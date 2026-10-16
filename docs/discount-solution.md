# Targeted solution to the main gross-profit bottleneck

The five-factor accounting bridge identifies discount changes as the largest negative component, −€563,258.63. This is a mechanical allocation of the H1/H2 difference, not a claim that every discounted sale is wasteful or that the full amount is recoverable.

## Policy replay

Use the analysis's discount flags, not the planted labels: 245 SKU-region-channel offer scopes, spanning 125 SKUs and 9,079 H2 sales lines. Reduce each observed line's discount by **up to six percentage points of its list price**. Cap the revised selling price at its list price, and calculate the change to whole cents. The actual line-level cap matters when a line already has less than a six-point discount.

Hold observed quantities, SKU/location/channel mix, list prices and product costs fixed. This is a replay of a candidate policy, not an observed intervention or an estimated response to higher prices.

| Quantity | EUR |
| --- | ---: |
| Original H1 gross profit | 3,912,985.57 |
| Original H2 gross profit | 3,806,896.21 |
| Original GP gap | 106,089.36 |
| Added GP in the fixed-volume replay | 112,241.30 |
| Revised H2 GP | 3,919,137.51 |
| Revised H2 GP above H1 | 6,151.94 |

The model closes the baseline GP gap at unchanged volume. It does not recover the entire allocated discount effect. Six percentage points means, for example, changing a 20% discount to 14%; it is not a 6% relative reduction in the discount.

## Demand sensitivity

Only the affected offers receive a uniform volume decline in this simple sensitivity calculation. Other sales remain unchanged. Fractional volume is a mathematical sensitivity assumption, not simulated individual customer behavior.

| Affected-offer unit decline | Revised company GP | Above / below H1 GP |
| --- | ---: | ---: |
| 0% | €3,919,137.51 | +€6,151.94 |
| 1% | €3,913,763.37 | +€777.80 |
| 2% | €3,908,389.24 | −€4,596.33 |
| 5% | €3,892,266.83 | −€20,718.74 |
| 10% | €3,865,396.16 | −€47,589.41 |

The affected-offer unit decline can be no greater than approximately **1.14%** if the specific goal is to preserve H1 company GP in this model. This is a break-even guardrail, not evidence that demand will remain within it. The practical next action is a controlled test of targeted discount caps, monitoring units and total gross profit.

## Reproduce

After the project's analysis has produced the SQLite cache:

```sh
python3 discount_solution.py
```

This writes `outputs/discount-solution.json`, including assumptions and sensitivity. A full project `run.py` also runs the replay. The generated illustration is a separate ImageGen asset; [its prompt and number sources](visual-generation.md) are retained for review.
