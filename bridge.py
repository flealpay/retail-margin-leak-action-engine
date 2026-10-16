"""Exact five-factor Shapley accounting bridge, not a causal effect estimator."""

import math

FACTORS = ("volume", "mix", "list_price", "discount", "cost")


def value(baseline, current, mask):
    q = (current if mask & 1 else baseline)["units"]
    states = [current if mask & (1 << i) else baseline for i in range(1, 5)]
    return q * sum(
        states[0]["cells"][cell]["share"] * (
            states[1]["cells"][cell]["price"] - states[2]["cells"][cell]["discount"] - states[3]["cells"][cell]["cost"]
        ) for cell in baseline["cells"]
    )


def decompose(baseline, current):
    if set(baseline["cells"]) != set(current["cells"]):
        raise ValueError("Bridge requires a common cell universe")
    for state in (baseline, current):
        if state["units"] <= 0 or abs(sum(c["share"] for c in state["cells"].values()) - 1) > 1e-8:
            raise ValueError("Positive units and shares summing to one are required")
    values = {mask: value(baseline, current, mask) for mask in range(32)}
    effects = {}
    for i, factor in enumerate(FACTORS):
        result = 0.0
        for mask in range(32):
            if mask & (1 << i):
                continue
            size = bin(mask).count("1")
            weight = math.factorial(size) * math.factorial(4 - size) / math.factorial(5)
            result += weight * (values[mask | (1 << i)] - values[mask])
        effects[factor] = result
    residual = values[31] - values[0] - sum(effects.values())
    if abs(residual) > 0.01:
        raise AssertionError(f"Unreconciled bridge residual: EUR {residual}")
    return {"baseline_gp": values[0], "current_gp": values[31], "effects": effects, "residual": residual}
