"""Evaluate already-produced diagnostics against separately stored planted labels."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def evaluate():
    report = json.loads((ROOT / "outputs/report.json").read_text())
    truth = json.loads((ROOT / "validation/ground_truth.json").read_text())
    checks = {}
    detections = []
    for issue in truth["mechanisms"]:
        name = issue["issue"]
        if name in ("discount", "cost"):
            predicted = {a["product_id"] for a in report["actions"] if a["reason"] == name}
            actual = set(issue["product_ids"])
            tp = len(predicted & actual)
            detections.append({"issue": name, "true_products": len(actual), "flagged_products": len(predicted),
                               "true_positives": tp, "precision": tp / len(predicted) if predicted else 0,
                               "recall": tp / len(actual), "recovered_pattern": tp > 0})
        elif name == "mix":
            row = next(r for r in report["diagnostics"]["product_mix"] if r["category"] == issue["category"])
            effect = report["slices"][f"{issue['category']}|All|All"]["bridge"]["effects"]["mix"]
            detections.append({"issue": name, "category": issue["category"], "observed_change_pp": row["change_pp"],
                               "category_local_mix_effect_eur": effect, "recovered_pattern": row["change_pp"] < -5 and effect < 0})
        elif name == "availability":
            row = next(r for r in report["diagnostics"]["availability"] if r["category"] == issue["category"] and r["region"] == issue["region"] and r["tier"] == "Premium")
            detections.append({"issue": name, "observed_change_pp": row["change_pp"], "recovered_pattern": row["change_pp"] < -5})
        elif name == "customer_mix":
            row = next(r for r in report["diagnostics"]["customer_mix"] if r["channel"] == issue["channel"] and r["segment"] == issue["segment"])
            detections.append({"issue": name, "observed_change_pp": row["change_pp"], "recovered_pattern": row["change_pp"] > 5})
    checks["five_planted_patterns_detected"] = all(d["recovered_pattern"] for d in detections)
    checks["all_slice_bridges_reconcile"] = all(abs(s["bridge"]["residual"]) < .01 for s in report["slices"].values())
    checks["one_action_per_cell"] = len(report["actions"]) == len({(a["product_id"], a["region"], a["channel"]) for a in report["actions"]})
    company = report["slices"]["All|All|All"]
    checks["revenue_up_margin_down"] = company["revenue_change"] > 0 and company["margin_change_pp"] < 0
    checks["gross_profit_down"] = company["gp_change"] < 0
    controls = set(truth["positive_control"]["product_ids"])
    control_rows = [a for a in report["actions"] if a["product_id"] in controls]
    checks["some_discounted_positive_controls_protected"] = any(a["action"] in ("PROTECT", "SCALE") for a in control_rows)
    result = {"data_type": "synthetic", "checks": checks, "all_passed": all(checks.values()),
              "detections": detections, "scope": "Planted-pattern recovery, not causal attribution validation.",
              "note": "Precision/recall use unique SKU IDs across cells. Non-planted flags are not automatically false economic concerns."}
    (ROOT / "validation/evaluation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not result["all_passed"]:
        raise AssertionError("Synthetic scenario acceptance failed; see evaluation.json")
    return result


if __name__ == "__main__":
    evaluate()

