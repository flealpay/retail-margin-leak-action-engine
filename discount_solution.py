"""Replay a targeted discount policy on observed synthetic H2 sales lines."""

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def replay(reduction_pp=6):
    if not 0 <= reduction_pp <= 100:
        raise ValueError("Discount reduction must be between 0 and 100 percentage points")
    report = json.loads((ROOT / "outputs/report.json").read_text())
    if report["data_type"] != "synthetic":
        raise ValueError("This demonstration requires synthetic provenance")
    flagged = [a for a in report["actions"] if a["reason"] == "discount"]
    connection = sqlite3.connect(ROOT / "outputs/retail.sqlite")
    try:
        connection.execute("CREATE TEMP TABLE selected(product_id TEXT,region TEXT,channel TEXT,PRIMARY KEY(product_id,region,channel))")
        connection.executemany("INSERT INTO selected VALUES (?,?,?)", [(a["product_id"], a["region"], a["channel"]) for a in flagged])
        rows = connection.execute("""
          SELECT quantity,regular_price_cents,selling_price_cents,unit_cost_cents
          FROM sales_metrics JOIN selected USING(product_id,region,channel) WHERE period='H2'
        """).fetchall()
    finally:
        connection.close()
    gain_cents = sum(q * min(round(p * reduction_pp / 100), p - selling) for q, p, selling, cost in rows)
    old_gp_cents = sum(q * (selling-cost) for q, p, selling, cost in rows)
    before, current = report["slices"]["All|All|All"]["periods"]
    gain, affected_gp = gain_cents / 100, old_gp_cents / 100
    gap = before["gp"] - current["gp"]
    new_gp = current["gp"] + gain
    sensitivity = [{"affected_units_decline_pct": decline * 100,
                    "company_gp_eur": current["gp"] - affected_gp + (affected_gp + gain) * (1 - decline),
                    "vs_h1_gp_eur": current["gp"] - affected_gp + (affected_gp + gain) * (1 - decline) - before["gp"]}
                   for decline in (0, .01, .02, .05, .10)]
    result = {
        "data_type": "synthetic", "policy": f"Reduce discount depth by up to {reduction_pp:g} percentage points on discount-flagged SKU-region-channel offers; cap each price at its original list price.",
        "reduction_pp": reduction_pp, "flagged_cells": len(flagged), "flagged_skus": len({a["product_id"] for a in flagged}),
        "affected_sales_lines": len(rows), "affected_h2_gp_eur": affected_gp,
        "h1_gp_eur": before["gp"], "h2_gp_eur": current["gp"], "profit_gap_eur": gap,
        "modeled_gain_eur": gain, "modeled_h2_gp_eur": new_gp,
        "gap_coverage_pct": gain / gap * 100, "vs_h1_gp_eur": new_gp - before["gp"],
        "max_affected_unit_decline_to_preserve_h1_gp_pct": (gain - gap) / (affected_gp + gain) * 100,
        "sensitivity": sensitivity,
        "assumptions": ["H2 quantities and product/region/channel mix are unchanged in the main scenario.",
                        "Product cost and list prices are unchanged; discount reduction raises selling price.",
                        "Each line is capped at list price; rounding uses whole cents, ties to even.",
                        "Sensitivity applies a uniform quantity reduction only to affected offers.",
                        "No observed treatment, elasticity estimate, causal lift, or realized recovery is claimed."]}
    assert gain >= 0
    assert abs((new_gp - current["gp"]) - gain) < .005
    (ROOT / "outputs/discount-solution.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps(replay(), indent=2))
