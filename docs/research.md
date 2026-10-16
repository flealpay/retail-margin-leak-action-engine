# Research note: retail margin attribution and action limits

Research date: 2026-10-16. Scope: bounded primary-source review for a synthetic Retail Margin Leak & Action Engine MVP. All commercial figures must come from the generated dataset and executable analysis; these sources establish methodological foundations, not the project's business results.

## Accounting scope

IAS 2 describes inventory cost as purchase, conversion and other costs required to bring inventory to its present location and condition. On sale, the inventory carrying amount becomes an expense. Its paragraph 16 excludes selling costs from inventory costs. These principles do not make every online fulfilment expense a product cost: classification requires an explicit policy. The MVP should call its measure **gross profit = net sales − modeled product COGS**, and disclose exclusions. Do not subtract fulfilment in only one channel while labeling the result gross margin. A separate, explicitly defined contribution measure can include modeled variable selling or delivery costs if introduced later. [IFRS Foundation: IAS 2 overview](https://www.ifrs.org/issued-standards/list-of-standards/ias-2-inventories/), [IAS 2, paragraphs 15–16, indexed official publication; full access may require subscription](https://www.ifrs.org/content/dam/ifrs/publications/pdf-standards/english/2021/issued/part-a/ias-2-inventories.pdf).

## Exact change attribution

Shapley's original work derives a value for allocating a game's outcome among participants. The project's use of this allocation method for accounting factors is an implementation choice. Average marginal contributions over all factor replacement orders, rather than choosing an arbitrary replacement sequence. [Lloyd S. Shapley, *Notes on the N-Person Game — II: The Value of an N-Person Game*, RAND, 1951](https://www.rand.org/pubs/research_memoranda/RM0670.html).

For each half-year t, define cells i as SKU × region × channel and quantities:

- Q(t): total units.
- s(i,t): cell units divided by Q(t); shares sum to one.
- p(i,t): quantity-weighted regular/list price per unit.
- d(i,t): quantity-weighted discount **amount per unit**, not mean discount percentage.
- c(i,t): quantity-weighted product cost per unit, using the cost effective on each sale date.

Then the modeled identity is:

`GP(t) = Q(t) × sum_i s(i,t) × [p(i,t) − d(i,t) − c(i,t)]`

Define five factor groups N = {Q, s, p, d, c}. For a subset S, F(S) evaluates the formula with H2 values for factors in S and H1 values for all others. Evaluate all 2^5 = 32 states. For each factor k:

`effect(k) = sum over S⊆N\{k} [|S|! × (4−|S|)! / 5!] × [F(S∪{k})−F(S)]`

The effects sum to H2 GP minus H1 GP, up to floating-point tolerance. This is equivalent to averaging over 120 orders; it removes dependence on one chosen order and shares interactions. It does not remove dependence on the chosen formula, grouping, cell grain or baseline. Treat s as **joint product/channel/region mix**. A channel or customer breakdown is a diagnostic view, not an additional additive driver. The bridge uses gross profit in currency; a gross-margin percentage-point bridge needs a separately specified ratio function.

Require both-period coverage for every cell or document and test an explicit missing-cell policy. Substituting an unobserved price or cost silently changes the attribution. Publish raw reconciliation tolerance and use unrounded effects for totals.

## Attribution is different from incrementality

In a large experimental comparison, Gordon and colleagues found that observational methods often failed to recover the advertising effects measured by random assignment, even with rich covariates. This is evidence from advertising, not a direct retail-discount estimate. The relevant inference for this MVP is that observed commercial differences should not automatically be described as causal uplift. [Gordon, Zettelmeyer, Bhargava and Chapsky, author-hosted working paper, April 2018; subsequently published 2019](https://www.kellogg.northwestern.edu/faculty/gordon_b/files/fb_comparison.pdf).

Our bridge allocates an observed accounting change. Higher promotion-period volume does not establish incremental demand, profitable promotion lift or cannibalization. H1/H2 comparisons also retain seasonality and changing composition. Label recommendations as rule-based priorities for investigation or testing. A discounted-price recovery calculation that holds units constant is a **fixed-volume scenario**, not a forecast, promise, causal effect or additive recoverable-profit total.

## Inventory signal limits

Conlon and Mortimer study demand estimation with changing product availability and substitution. They report that ignoring availability can bias demand estimates and develop a model that handles periodically observed availability. This supports modeling availability explicitly rather than equating observed sales with unrestricted demand. [Conlon and Mortimer, *Demand Estimation Under Incomplete Product Availability*, NBER Working Paper 14315](https://www.nber.org/papers/w14315).

For this MVP, a daily on-hand snapshot supports a snapshot in-stock flag and the proportion of observed snapshots with stock. It does not establish intraday availability, unmet demand or a euro amount of lost sales. Flag an availability issue for investigation; do not add an invented stockout-loss bar to the exact bridge. Planted synthetic inventory patterns validate pattern detection, not real-world causal identification.

## Synthetic scenario and acceptance choices

Use January–December 2025, H1/H2 comparison, 500 SKUs, 20,000 customers, 180,000 sales lines and the agreed supporting tables. Label all tables, charts and public posts synthetic. Keep a planted-issue manifest separate from analysis input, and evaluate detection separately after producing results.

The pasted brief's illustrative targets are inconsistent: revenue +6% and margin 28% → 25% imply GP change `1.06 × 25/28 − 1 = −5.36%`, not −4%. Do not force those three claims together. Generate a coherent scenario and publish its computed results. The inventory table has exactly `500 × 3 × 365 = 547,500` daily SKU-region rows if coverage is complete.

This note is methodological guidance. The project README is the final reproduction contract and must document any implementation departures.
