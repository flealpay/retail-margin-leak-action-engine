"""SQL financial metrics, exact accounting attribution and explainable action rules."""

import csv
import hashlib
import itertools
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

from bridge import decompose

ROOT = Path(__file__).resolve().parent
TABLES = ("dim_product", "dim_customer", "dim_promotion", "fact_cost_history", "fact_inventory_daily", "fact_sales")


def query(connection, sql, args=()):
    cursor = connection.execute(sql, args)
    return [dict(zip([item[0] for item in cursor.description], row)) for row in cursor]


def build_database(data_dir, output_dir):
    manifest = json.loads((data_dir / "manifest.json").read_text())
    if manifest["data_type"] != "synthetic":
        raise ValueError("This project's reports require explicit synthetic provenance")
    for filename, digest in manifest["sha256"].items():
        if hashlib.sha256((data_dir / filename).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Input checksum mismatch: {filename}")
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "retail.sqlite"
    if db_path.exists():
        db_path.unlink()  # Rebuildable project output only.
    connection = sqlite3.connect(db_path)
    connection.executescript((ROOT / "sql/schema.sql").read_text())
    for table in TABLES:
        with (data_dir / f"{table}.csv").open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            fields = next(reader)
            expected = [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]
            if fields != expected:
                raise ValueError(f"Unexpected column order for {table}")
            marks = ",".join("?" for _ in fields)
            connection.executemany(f"INSERT INTO {table} VALUES ({marks})",
                                   ([None if cell == "" else cell for cell in row] for row in reader))
        connection.commit()
    # Compute line-level finances in SQL once; all reports use this materialization.
    connection.execute("CREATE TABLE sales_metrics AS SELECT * FROM v_sales")
    connection.execute("CREATE INDEX metrics_slice ON sales_metrics(category,region,channel,period)")
    connection.commit()
    return connection, manifest


def validate_data(connection, manifest):
    counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in TABLES}
    checks = {}
    checks["expected_row_counts"] = counts == dict(zip(TABLES, (500, 20000, 35, 1000, 547500, manifest["sales_lines"])))
    checks["foreign_keys"] = not list(connection.execute("PRAGMA foreign_key_check"))
    checks["asof_cost_join_preserves_rows"] = connection.execute("SELECT COUNT(*) FROM sales_metrics").fetchone()[0] == counts["fact_sales"]
    checks["all_months_covered"] = connection.execute("SELECT COUNT(DISTINCT substr(date,1,7)) FROM fact_sales").fetchone()[0] == 12
    checks["sales_follow_customer_join"] = connection.execute("SELECT COUNT(*) FROM fact_sales s JOIN dim_customer c USING(customer_id) WHERE s.date<c.join_date").fetchone()[0] == 0
    checks["promotion_eligibility"] = connection.execute("""
        SELECT COUNT(*) FROM sales_metrics s JOIN dim_promotion p USING(promotion_id)
        WHERE s.date<p.start_date OR s.date>p.end_date OR s.category<>p.target_category
        OR (p.channel<>'All' AND p.channel<>s.channel)
        OR (p.target_segment<>'All' AND p.target_segment<>s.customer_segment)
        OR abs(s.selling_price_cents-round(s.regular_price_cents*(1-p.discount_depth)))>1
    """).fetchone()[0] == 0
    checks["sales_match_available_stock"] = connection.execute("""
        SELECT COUNT(*) FROM fact_sales s LEFT JOIN fact_inventory_daily i
        ON i.date=s.date AND i.product_id=s.product_id AND i.region=s.region
        WHERE i.in_stock_flag IS NULL OR i.in_stock_flag<>1
    """).fetchone()[0] == 0
    checks["daily_units_within_opening_stock"] = connection.execute("""
        SELECT COUNT(*) FROM (
          SELECT s.date,s.product_id,s.region,SUM(s.quantity) AS sold,MAX(i.stock_on_hand) AS opening
          FROM fact_sales s JOIN fact_inventory_daily i
          ON s.date=i.date AND s.product_id=i.product_id AND s.region=i.region
          GROUP BY s.date,s.product_id,s.region HAVING sold>opening
        )
    """).fetchone()[0] == 0
    checks["profit_identity"] = connection.execute("SELECT SUM(revenue_cents)-SUM(cogs_cents)-SUM(gross_profit_cents) FROM sales_metrics").fetchone()[0] == 0
    checks["order_header_consistency"] = connection.execute("""
        SELECT COUNT(*) FROM (SELECT transaction_id FROM fact_sales GROUP BY transaction_id
        HAVING COUNT(DISTINCT date)>1 OR COUNT(DISTINCT customer_id)>1 OR COUNT(DISTINCT channel)>1 OR COUNT(DISTINCT region)>1)
    """).fetchone()[0] == 0
    if not all(checks.values()):
        raise AssertionError(f"Data validation failed: {checks}")
    return {"checks": checks, "row_counts": counts, "all_passed": True}


def load_cells(connection):
    return query(connection, """
      SELECT period,product_id,product_name,category,tier,region,channel,
        SUM(quantity) AS units,SUM(quantity*regular_price_cents)/100.0 AS list_value,
        SUM(discount_cents)/100.0 AS discount_value,SUM(cogs_cents)/100.0 AS cogs,
        SUM(revenue_cents)/100.0 AS revenue,SUM(gross_profit_cents)/100.0 AS gp
      FROM sales_metrics GROUP BY period,product_id,region,channel
    """)


def make_slice(rows):
    states, summaries = [], []
    for period in ("H1", "H2"):
        selected = [r for r in rows if r["period"] == period]
        units = sum(r["units"] for r in selected)
        revenue, cogs, gp = (sum(r[column] for r in selected) for column in ("revenue", "cogs", "gp"))
        cells = {f"{r['product_id']}|{r['region']}|{r['channel']}": {
            "share": r["units"] / units, "price": r["list_value"] / r["units"],
            "discount": r["discount_value"] / r["units"], "cost": r["cogs"] / r["units"],
        } for r in selected}
        states.append({"units": units, "cells": cells})
        summaries.append({"period": period, "units": units, "revenue": revenue, "cogs": cogs, "gp": gp,
                          "margin": gp / revenue if revenue else None,
                          "discount_rate": sum(r["discount_value"] for r in selected) / sum(r["list_value"] for r in selected)})
    bridge = decompose(*states)
    for expected, actual in zip(summaries, (bridge["baseline_gp"], bridge["current_gp"])):
        if abs(expected["gp"] - actual) > .01:
            raise AssertionError("Bridge endpoints do not match SQL gross profit")
    h1, h2 = summaries
    return {"periods": summaries, "bridge": bridge,
            "revenue_change": h2["revenue"] / h1["revenue"] - 1,
            "gp_change": h2["gp"] / h1["gp"] - 1,
            "margin_change_pp": (h2["margin"] - h1["margin"]) * 100,
            "adverse_contributions": -sum(min(0, v) for v in bridge["effects"].values())}


def action_for_pair(before, after):
    """One primary action per SKU/region/channel: scenarios have disjoint scope."""
    b, a = before, after
    p0, p1 = b["list_value"] / b["units"], a["list_value"] / a["units"]
    d0, d1 = b["discount_value"] / b["units"], a["discount_value"] / a["units"]
    c0, c1 = b["cogs"] / b["units"], a["cogs"] / a["units"]
    margin0, margin1 = b["gp"] / b["revenue"], a["gp"] / a["revenue"]
    depth_change = d1 / p1 - d0 / p0
    cost_change = c1 / c0 - 1
    uncovered_cost = max(0, c1 - c0 - (p1 - p0))
    scenario, assumption = 0.0, "No recovery estimate; diagnostic action only."
    if a["gp"] < 0:
        action, reason, instruction = "STOP", "negative_profit", "Pause and review the loss-making offer before further investment."
        scenario = -a["gp"]
        assumption = "Avoided gross loss if this entire offer stops; revenue and demand displacement excluded."
    elif a["units"] >= 20 and depth_change >= .045 and a["gp"] < .98 * b["gp"]:
        action, reason = "MODIFY", "discount"
        reduction = min(.02, d1 / p1)
        instruction = f"Test a {reduction * 100:.1f} pp reduction in discount depth; monitor units and gross profit."
        scenario = a["units"] * p1 * reduction
        assumption = "Fixed H2 units, list price, cost and mix; no demand response. Two-point discount scenario, not a forecast."
    elif a["units"] >= 20 and cost_change >= .06 and uncovered_cost > .10:
        action, reason = "MODIFY", "cost"
        instruction = f"Review EUR {uncovered_cost:.2f}/unit of cost increase not covered by list-price change; test repricing."
        scenario = a["units"] * uncovered_cost
        assumption = "Fixed H2 units, discounts, cost and mix; selling price increases by uncovered cost. Demand response excluded."
    elif a["gp"] >= b["gp"] * 1.2 and margin1 >= margin0 and a["units"] >= b["units"] * 1.2:
        action, reason, instruction = "SCALE", "positive_trend", "Consider a controlled expansion test; verify capacity and incremental profit first."
    elif a["gp"] >= b["gp"] and a["gp"] > 0:
        action, reason, instruction = "PROTECT", "positive_profit", "Protect current economics; assess promotion incrementality separately."
    else:
        action, reason, instruction = "INVESTIGATE", "margin_or_volume", "Review demand, availability and segment mix before selecting a commercial change."
    return {"product_id": a["product_id"], "product_name": a["product_name"], "category": a["category"],
            "tier": a["tier"], "region": a["region"], "channel": a["channel"], "action": action,
            "reason": reason, "instruction": instruction, "scenario_gp_eur": scenario, "assumption": assumption,
            "h1_units": b["units"], "h2_units": a["units"], "h1_gp": b["gp"], "h2_gp": a["gp"],
            "gp_delta": a["gp"] - b["gp"], "h2_margin": margin1,
            "h2_list_price": p1, "h2_discount_per_unit": d1, "h2_cost_per_unit": c1,
            "discount_change_pp": depth_change * 100, "cost_change_pct": cost_change * 100,
            "list_price_change_pct": (p1 / p0 - 1) * 100,
            "break_even_volume_change": ((p0 - d0 - c0) / (p1 - d1 - c1) - 1) if p1 - d1 - c1 > 0 else None}


def diagnostics(connection, cells):
    mix = []
    for category in sorted({r["category"] for r in cells}):
        shares = []
        for period in ("H1", "H2"):
            selected = [r for r in cells if r["period"] == period and r["category"] == category]
            shares.append(sum(r["units"] for r in selected if r["tier"] == "Premium") / sum(r["units"] for r in selected))
        mix.append({"category": category, "h1_premium_unit_share": shares[0], "h2_premium_unit_share": shares[1],
                    "change_pp": (shares[1] - shares[0]) * 100})
    availability = query(connection, """
       SELECT p.category,p.tier,i.region,
       AVG(CASE WHEN i.date<'2025-09-01' THEN i.in_stock_flag END) AS baseline,
       AVG(CASE WHEN i.date>='2025-09-01' AND i.date<'2025-11-01' THEN i.in_stock_flag END) AS autumn
       FROM fact_inventory_daily i JOIN dim_product p USING(product_id)
       GROUP BY p.category,p.tier,i.region
    """)
    for row in availability:
        row["change_pp"] = (row["autumn"] - row["baseline"]) * 100
    customer = query(connection, """
      SELECT period,channel,customer_segment,SUM(quantity) AS units,
       SUM(gross_profit_cents)*1.0/SUM(revenue_cents) AS margin
      FROM sales_metrics GROUP BY period,channel,customer_segment
    """)
    customer_changes = []
    for channel in ("Online", "Store"):
        for segment in sorted({r["customer_segment"] for r in customer}):
            shares = []
            for period in ("H1", "H2"):
                rows = [r for r in customer if r["period"] == period and r["channel"] == channel]
                shares.append(next(r["units"] for r in rows if r["customer_segment"] == segment) / sum(r["units"] for r in rows))
            customer_changes.append({"channel": channel, "segment": segment, "h1_unit_share": shares[0],
                                     "h2_unit_share": shares[1], "change_pp": (shares[1] - shares[0]) * 100})
    return {"product_mix": sorted(mix, key=lambda r: r["change_pp"]),
            "availability": sorted(availability, key=lambda r: r["change_pp"]),
            "customer_mix": sorted(customer_changes, key=lambda r: -r["change_pp"])}


def export_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def analyze(data_dir=ROOT / "data", output_dir=ROOT / "outputs"):
    connection, manifest = build_database(data_dir, output_dir)
    try:
        audit = validate_data(connection, manifest)
        cells = load_cells(connection)
        categories = sorted({r["category"] for r in cells})
        slices = {}
        for category, region, channel in itertools.product(["All"] + categories, ["All", "North", "Central", "South"], ["All", "Online", "Store"]):
            selected = [r for r in cells if (category == "All" or r["category"] == category)
                        and (region == "All" or r["region"] == region) and (channel == "All" or r["channel"] == channel)]
            slices[f"{category}|{region}|{channel}"] = make_slice(selected)
        pairs = defaultdict(dict)
        for row in cells:
            pairs[(row["product_id"], row["region"], row["channel"])][row["period"]] = row
        actions = [action_for_pair(pair["H1"], pair["H2"]) for pair in pairs.values()]
        actions.sort(key=lambda r: (-r["scenario_gp_eur"], r["gp_delta"], r["product_id"], r["region"], r["channel"]))
        monthly = query(connection, """
          SELECT substr(date,1,7) AS month,category,region,channel,SUM(revenue_cents)/100.0 AS revenue,
            SUM(gross_profit_cents)/100.0 AS gp,SUM(quantity) AS units
          FROM sales_metrics GROUP BY substr(date,1,7),category,region,channel
        """)
        report = {"data_type": "synthetic", "currency": "EUR", "seed": manifest["seed"], "comparison": "H1 2025 vs H2 2025",
                  "mix_definition": "Joint SKU × region × channel unit-share mix", "categories": categories,
                  "slices": slices, "actions": actions, "monthly": monthly,
                  "diagnostics": diagnostics(connection, cells), "audit": audit,
                  "scenario_total": sum(r["scenario_gp_eur"] for r in actions),
                  "limitations": ["Accounting attribution is not causal identification.",
                    "Fixed-volume scenarios exclude demand response and are not forecasts.",
                    "Stock snapshots cannot establish lost demand or its value.",
                    "H1/H2 comparison includes seasonality; no YoY control is available."]}
        (output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        export_csv(output_dir / "actions.csv", actions)
        export_csv(output_dir / "monthly.csv", monthly)
        export_csv(output_dir / "bridge.csv", [{"factor": k, "gp_effect_eur": v} for k, v in slices["All|All|All"]["bridge"]["effects"].items()])
        for name, rows in report["diagnostics"].items():
            export_csv(output_dir / f"{name}.csv", rows)
        print(json.dumps({"company": slices["All|All|All"], "scenario_total": report["scenario_total"], "audit": audit}, indent=2))
        return report
    finally:
        connection.close()


if __name__ == "__main__":
    analyze()
