# 01 · Business problem and scope

## Decision question

Revenue is growing while gross profit is falling. Which accounting drivers explain the change, where is it concentrated, and which commercial actions should management investigate or test?

Decision users are a Commercial Director, Pricing Manager, Category Manager or Head of Analytics. A successful MVP provides a traceable path from company change to category / region / channel / SKU, a reconciled explanation, and an action with explicit assumptions.

## Scope

The controlled synthetic business is an omnichannel retailer with five categories, three regions, two channels and a full 2025 year. H1 is the baseline and H2 is the comparison. Data size and grains are defined in the [data model](data-model.md).

Three primary hypotheses:

1. **Discount:** increased discount depth can dilute unit economics even when units grow.
2. **Mix:** a shift toward lower-margin products can reduce the blended margin.
3. **Cost:** supplier cost increases may exceed list-price changes and compress unit profit.

Two related diagnostic patterns are included: Premium Apparel availability in South during September–October, and an increased Deal Seeker unit share in Online. These are analyzed separately from the additive accounting bridge.

The generator stores planted labels separately. The analysis only receives business tables, not those labels; evaluation reads them after results have been produced. Positive controls prevent the rule “every deep discount is bad.”

## Outputs

- Explainable action labels: SCALE / PROTECT / MODIFY / INVESTIGATE / STOP.
- Full financial and scenario assumptions per action.
- Offline dashboard, source CSVs for BI import, SQL calculations and reproducible Python.
- Business-first roadmap, one-page data graphic and concise English post.

Excluded: ML, forecasting, causal inference, demand elasticity, optimization, live APIs and cloud deployment. Promotion incrementality and stockout lost sales remain unmeasured.

## Interpretation of the supplied examples

The specification's example euro amounts and percentage changes are illustrative rather than acceptance values. Revenue +6%, GP −4% and margin 28% → 25% are not arithmetically consistent together. Results are calculated from the generated tables. Scenario parameters, including monthly order weights, are explicitly chosen to construct revenue growth with margin erosion; they are not estimates of market behavior.


