"""Create a seeded retail environment. All records and mechanisms are synthetic."""

import argparse
import calendar
import csv
import hashlib
import json
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATEGORIES = ("Electronics", "Home", "Personal Care", "Apparel", "Accessories")
REGIONS = ("North", "Central", "South")
SEGMENTS = ("Premium", "Core", "Deal Seeker", "Occasional")


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def generate(output=ROOT / "data", lines=180000, seed=42):
    if lines < 120 or lines % 3:
        raise ValueError("sales lines must be at least 120 and divisible by three")
    output.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    products = []
    pools = defaultdict(list)
    for category_index, category in enumerate(CATEGORIES):
        for index in range(100):
            tier = "Budget" if index < 30 else "Core" if index < 75 else "Premium"
            factor = {"Budget": 0.6, "Core": 1.0, "Premium": 1.9}[tier]
            base = round((250, 95, 30, 75, 45)[category_index] * factor * rng.uniform(0.85, 1.15) * 100)
            cost = round(base * {"Budget": 0.78, "Core": 0.65, "Premium": 0.55}[tier])
            product = {
                "product_id": f"P{category_index * 100 + index + 1:04d}",
                "product_name": f"{category} {tier} {index + 1:03d}",
                "category": category, "subcategory": f"{category} {index % 4 + 1}",
                "brand": f"Brand {index % 8 + 1}", "tier": tier,
                "base_price_cents": base, "initial_cost_cents": cost,
                "base_margin_pct": (base - cost) / base, "launch_date": "2024-01-01",
            }
            products.append(product)
            pools[(category, tier)].append(product)
    write_csv(output / "dim_product.csv", list(products[0]), products)
    lookup = {p["product_id"]: p for p in products}
    discount_ids = set(rng.sample([p["product_id"] for p in products if p["category"] == "Electronics"], 40))
    cost_ids = set(rng.sample([p["product_id"] for p in products if p["category"] == "Personal Care"], 50))
    stock_ids = set(rng.sample([p["product_id"] for p in products if p["category"] == "Apparel" and p["tier"] == "Premium"], 15))
    healthy_ids = set(rng.sample([p["product_id"] for p in products if p["category"] == "Accessories" and p["tier"] == "Premium"], 8))

    customers = []
    customer_pools = defaultdict(list)
    for index in range(20000):
        customer = {
            "customer_id": f"C{index + 1:05d}", "customer_segment": SEGMENTS[index % 4],
            "region": REGIONS[(index // 4) % 3],
            "acquisition_channel": ("Organic", "Paid", "Referral")[index % 3],
            "join_date": "2024-01-01", "loyalty_member": int(index % 3 != 0),
        }
        customers.append(customer)
        customer_pools[(customer["region"], customer["customer_segment"])].append(customer)
    write_csv(output / "dim_customer.csv", list(customers[0]), customers)

    # Two effective-dated records per SKU; one value per product/date.
    costs = []
    second_cost = {}
    for product in products:
        pid, initial = product["product_id"], product["initial_cost_cents"]
        change = rng.uniform(0.10, 0.15) if pid in cost_ids else rng.uniform(0.00, 0.025)
        second_cost[pid] = round(initial * (1 + change))
        for when, amount in (("2025-01-01", initial), ("2025-07-01", second_cost[pid])):
            costs.append({"product_id": pid, "effective_date": when, "unit_cost_cents": amount,
                          "cost_change_pct": amount / initial - 1, "supplier_id": f"S{int(pid[1:]) % 20:02d}"})
    write_csv(output / "fact_cost_history.csv", list(costs[0]), costs)

    promotions = []
    periods = ((1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (9, 12))
    category_promos = defaultdict(list)
    for ci, category in enumerate(CATEGORIES):
        for slot, (first, last) in enumerate(periods):
            special = slot == 6
            promo = {
                "promotion_id": f"M{ci * 7 + slot + 1:03d}",
                "promo_name": f"{category} campaign {slot + 1}", "promo_type": "Percentage Discount",
                "start_date": f"2025-{first:02d}-01", "end_date": f"2025-{last:02d}-{calendar.monthrange(2025, last)[1]:02d}",
                "target_category": category, "target_segment": "All" if special or slot % 3 else "Deal Seeker",
                "discount_depth": 0.20 if special else (0.08, 0.12, 0.15)[slot % 3],
                "channel": "All" if special else ("Online", "Store", "All")[slot % 3],
            }
            promotions.append(promo)
            category_promos[category].append(promo)
    write_csv(output / "dim_promotion.csv", list(promotions[0]), promotions)

    # Daily opening-stock snapshots; not an intraday inventory ledger.
    available = {}
    inventory_fields = ("date", "product_id", "region", "stock_on_hand", "in_stock_flag")
    with (output / "fact_inventory_daily.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(inventory_fields)
        for day in range(365):
            when = date(2025, 1, 1) + timedelta(days=day)
            for product in products:
                for region in REGIONS:
                    probability = 0.72 if product["product_id"] in stock_ids and region == "South" and when.month in (9, 10) else 0.96
                    flag = int(rng.random() < probability)
                    available[(when.isoformat(), product["product_id"], region)] = flag
                    writer.writerow((when.isoformat(), product["product_id"], region, rng.randint(500, 1500) if flag else 0, flag))

    # Sampling weights encode mechanisms. The analyzer receives none of these labels.
    product_weights = {}
    for month in range(1, 13):
        for category in CATEGORIES:
            weights = {}
            for tier in ("Budget", "Core", "Premium"):
                shares = (0.35, 0.45, 0.20)
                if category == "Home":
                    shares = (0.28, 0.34, 0.38) if month <= 6 else (0.44, 0.34, 0.22)
                candidates = pools[(category, tier)]
                for product in candidates:
                    weight = shares[("Budget", "Core", "Premium").index(tier)] / len(candidates)
                    if month >= 9 and product["product_id"] in discount_ids:
                        weight *= 1.25
                    if month >= 9 and product["product_id"] in healthy_ids:
                        weight *= 1.8
                    weights[product["product_id"]] = weight
            product_weights[(month, category)] = (list(weights), list(weights.values()))

    month_weights = (.95, .95, 1, 1, 1.02, 1.03, .987, .987, 1.0152, 1.0152, 1.128, 1.1656)
    order_months = rng.choices(range(1, 13), weights=month_weights, k=lines // 3)
    fields = ("sales_line_id", "transaction_id", "date", "customer_id", "product_id", "quantity",
              "regular_price_cents", "selling_price_cents", "promotion_id", "channel", "region")
    with (output / "fact_sales.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        for order, month in enumerate(order_months):
            when = date(2025, month, rng.randint(1, calendar.monthrange(2025, month)[1])).isoformat()
            region = rng.choices(REGIONS, weights=(.34, .33, .33))[0]
            channel = "Online" if rng.random() < (0.40 if month <= 6 else 0.55) else "Store"
            segment_weights = (.18, .40, .24, .18) if channel != "Online" or month <= 6 else (.14, .32, .39, .15)
            segment = rng.choices(SEGMENTS, weights=segment_weights)[0]
            customer = rng.choice(customer_pools[(region, segment)])
            for line in range(3):
                category_weights = [1.15 * (1.65 if month >= 11 else 1), 1, 1.1, 0.9 * (1.3 if month in (3, 4, 9, 10) else 1), .8]
                category = rng.choices(CATEGORIES, weights=category_weights)[0]
                ids, weights = product_weights[(month, category)]
                for attempt in range(100):
                    pid = rng.choices(ids, weights=weights)[0]
                    if available[(when, pid, region)]:
                        break
                else:
                    raise RuntimeError("No available SKU found")
                product = lookup[pid]
                quantity = rng.choices((1, 2, 3), weights=(.78, .18, .04))[0]
                regular = round(product["base_price_cents"] * (1 if month <= 6 else 1.03))
                eligible = [p for p in category_promos[category] if p["start_date"] <= when <= p["end_date"]
                            and p["channel"] in ("All", channel) and p["target_segment"] in ("All", segment)]
                promotion = None
                if month >= 9 and (pid in discount_ids or pid in healthy_ids):
                    promotion = category_promos[category][-1]
                elif eligible and rng.random() < (.62 if segment == "Deal Seeker" else .26):
                    promotion = rng.choice(eligible)
                discount = promotion["discount_depth"] if promotion else rng.uniform(0.01, 0.05)
                selling = round(regular * (1 - discount))
                writer.writerow((f"L{order * 3 + line + 1:07d}", f"T{order + 1:06d}", when,
                                 customer["customer_id"], pid, quantity, regular, selling,
                                 promotion["promotion_id"] if promotion else "", channel, region))

    truth = {
        "data_type": "synthetic", "seed": seed,
        "mechanisms": [
            {"issue": "discount", "category": "Electronics", "product_ids": sorted(discount_ids), "starts": "2025-09-01"},
            {"issue": "mix", "category": "Home", "unit_share_premium_h1": .38, "unit_share_premium_h2": .22},
            {"issue": "cost", "category": "Personal Care", "product_ids": sorted(cost_ids), "starts": "2025-07-01"},
            {"issue": "availability", "category": "Apparel", "region": "South", "months": [9, 10], "product_ids": sorted(stock_ids)},
            {"issue": "customer_mix", "channel": "Online", "segment": "Deal Seeker", "selection_share_h1": .24, "selection_share_h2": .39},
        ],
        "positive_control": {"category": "Accessories", "product_ids": sorted(healthy_ids), "note": "High-discount, positive-unit-profit examples; no causal incrementality claim."},
    }
    validation = output.parent / "validation"
    validation.mkdir(exist_ok=True)
    (validation / "ground_truth.json").write_text(json.dumps(truth, indent=2) + "\n")
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.glob("*.csv"))}
    manifest = {"data_type": "synthetic", "seed": seed, "currency": "EUR", "period": ["2025-01-01", "2025-12-31"],
                "sales_lines": lines, "orders": lines // 3, "products": 500, "customers": 20000,
                "inventory_rows": 547500, "cost_events": 1000, "promotions": 35,
                "monthly_order_weights": month_weights, "sha256": files}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Generated {lines:,} synthetic sales lines, 500 SKUs and 547,500 inventory snapshots.")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lines", type=int, default=180000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate(lines=args.lines, seed=args.seed)

