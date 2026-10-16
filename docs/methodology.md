# 03 · KPI, attribution and action contract

## KPIs

For a sale line with quantity q, list price p, selling price a and date-effective unit cost c:

- Revenue after discounts = `q × a`.
- Discount amount = `q × (p − a)`.
- Product COGS = `q × c`.
- Gross profit = revenue − COGS.
- Gross margin = `sum(GP) / sum(revenue)`. Never average line or SKU margin percentages to obtain the company margin.
- Weighted discount depth = `sum(discount amount) / sum(q × p)`.
- Gross-margin change in percentage points = `100 × (H2 margin − H1 margin)`.
- Revenue or GP growth = `H2 / H1 − 1`, for a positive baseline.
- Snapshot availability = mean binary in-stock flag over the explicitly stated SKU-region-date scope.
- Premium / customer-segment unit share = units in that group / all units in its stated scope.

All monetary sums are initially computed in integer cents by SQL. The Python bridge uses floating-point euros and enforces a residual below €0.01.

## Exact five-factor GP bridge

Within each selected scope, use cells i = SKU × region × channel. Q is total units; s is the vector of unit shares; p, d and c are **quantity-weighted per-unit amounts** for list price, discount and cost. Discount d is not an average percentage.

`GP = Q × Σ_i s_i × (p_i − d_i − c_i)`

For the five factor groups (Q, s, p, d, c), evaluate all 32 combinations of H1 and H2 values. The Shapley contribution for factor k is:

`Σ_{S⊆N\{k}} |S|! (4−|S|)! / 5! × [F(S∪{k}) − F(S)]`

This equals averaging that factor's marginal change across all 120 replacement orders. Effects sum to H2 GP − H1 GP. Interaction contributions are shared; allocation depends on the chosen factor grouping and cell grain. It is an accounting allocation, not a causal demand model.

Every cell must be present in both periods. Missing common support raises an error rather than silently filling an unobserved price. The default dataset covers all 3,000 SKU-region-channel cells in each period. Each of the dashboard's 72 filtered scopes gets its own normalized shares and its own exact bridge. Category-local components do not sum to company components factor by factor.

**Adverse contributions** = sum of the absolute values of negative bridge components. Positive offsets and the net GP change are shown separately. This is not recoverable profit.

Primary foundations and their limits are documented in [the research note](research.md).

## One primary action per cell

Rules are applied in this order to a SKU-region-channel cell, using H1/H2 weighted unit economics:

| Condition | Action | Scenario / intended next step |
| --- | --- | --- |
| H2 GP < 0 | STOP | Pause and review the offer; avoided loss if stopped, with lost revenue and displacement excluded |
| H2 units ≥ 20; discount depth rises ≥ 4.5 pp; H2 GP < 98% of H1 GP | MODIFY / discount | Test a 2 pp discount reduction, capped at current depth |
| H2 units ≥ 20; cost rises ≥ 6%; cost increase not covered by list-price change exceeds €0.10/unit | MODIFY / cost | Review repricing by the uncovered cost amount |
| H2 GP and units both ≥ 120% of H1; margin does not decline | SCALE | Consider a controlled expansion test; no numeric demand forecast |
| H2 GP ≥ H1 GP and positive | PROTECT | Preserve economics while checking incrementality separately |
| Otherwise | INVESTIGATE | Review volume, availability and segment composition |

Thresholds are transparent MVP heuristics, not optimized business policies or statistical significance cutoffs. STOP is implemented and tested even if it is not needed for a particular generated seed. The engine executes no price or promotion changes.

Discount scenario: `H2 units × H2 list price × min(0.02, current discount depth)`.

Cost scenario: `H2 units × max(0, cost increase − list-price increase)`.

STOP scenario: `−H2 GP`, only when H2 GP is negative, and only as an avoided-loss arithmetic case.

All scenarios hold H2 units and other unit economics constant, excluding demand response, substitution and execution costs. They are conditional gross-profit amounts, not recovery forecasts. Each cell gets only one primary action, avoiding overlapping scenarios on the same sales scope. Even the sum over disjoint cells does not establish achievable combined recovery.

The export also gives the arithmetic break-even quantity change `H1 unit GP / H2 unit GP − 1` when H2 unit GP is positive. This is a conditional threshold for maintaining baseline gross profit at those unit values, not estimated elasticity or incremental demand.

## Separate diagnostic views

- Product-tier mix: premium **unit share**, H1 → H2, per category.
- Availability: Premium and other tiers per category-region, Jan–Aug snapshot mean versus Sep–Oct. This matches the observation window under investigation, not a euro amount of lost sales.
- Customer composition: segment unit share within channel, H1 → H2.

Availability and customer composition are not additional additive bars. The joint-mix bridge already accounts mechanically for changed sales composition, and the causal contribution of these patterns is unmeasured.

## Evaluation

After producing `report.json`, evaluation reads the separately stored planted patterns. It reports recall on planted SKU IDs, the fraction of flags that match planted IDs, the known mix/availability/customer-direction checks, and positive controls. The labels are not exhaustive negative/positive truth about every economic concern. At the default seed, discount recall is 100%, with 40 planted IDs among 125 flagged IDs (32% match fraction); cost flags match 50/50. Broader discount flags require review.

No test result establishes real-world generalization, causal identification or the financial benefit of acting.
