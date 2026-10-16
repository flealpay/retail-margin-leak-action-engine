# 02 · Data model

All source records are generated. Currency is EUR; monetary source columns use integer **cents**. Rates are fractions unless a field explicitly ends in `pp` or `pct` in a report. Output GP / revenue / COGS and unit values are in euros.

| Table | Grain and key | Default size | Main relationships / content |
| --- | --- | ---: | --- |
| `dim_product` | One SKU, `product_id` | 500 | Five categories; Budget / Core / Premium; reference list price and initial cost |
| `dim_customer` | One supplied customer, `customer_id` | 20,000 | Segment, home region, acquisition channel, loyalty flag, join date |
| `dim_promotion` | One percentage campaign, `promotion_id` | 35 | Date range, target category / segment / channel and percentage depth |
| `fact_sales` | One order line, `sales_line_id` | 180,000 | `transaction_id` groups three lines; date, customer, SKU, region, channel, quantity and observed prices |
| `fact_cost_history` | SKU × effective date | 1,000 | January and July product cost records; supplier and change |
| `fact_inventory_daily` | Date × SKU × region | 547,500 | Opening stock and binary snapshot in-stock flag |

Foreign keys and constraints are declared in [schema.sql](../sql/schema.sql). A transaction has a consistent customer, date, region and channel. A customer can appear in multiple orders. Each sale joins exactly one product, one customer and the most recent cost effective on its date. Its optional campaign must satisfy the date/category/segment/channel eligibility rules.

`regular_price_cents` is the observed transaction-time list price, which can differ from the product master reference price. `selling_price_cents` is the observed unit price after modeled discounts. `unit_cost_cents`, revenue, COGS, discounts and GP are calculated in the SQL view, rather than supplied as source financial results.

Inventory is region-level across both channels. It does not have a channel dimension or simulate a warehouse ledger. The generator samples sales only from SKUs whose daily snapshot is in stock. A validation also checks sold units do not exceed opening snapshot stock in this constructed environment. That is a consistency check, not a production inventory-balance model.

The source has no return, refund, tax, currency conversion or fulfilment-cost records. VAT is treated as excluded from the modeled sales values.

## Controlled generation

The default seed is 42. The metadata manifest records the six source checksums, dimensions and monthly order weights. Demand sampling includes category seasonality, product tiers, channel and customer composition, eligible promotions and daily stock. Changes are intentionally planted in the synthetic environment; their quantities are not real-world estimates.

The generator separately writes the planted product IDs and patterns to `validation/ground_truth.json`. This file is used only by evaluation. The data-analysis code neither imports it nor receives its path.

CSV source tables are generated locally and excluded from Git to keep the repository lightweight. Rebuild them with `generate.py`. `outputs/retail.sqlite` is also a generated cache. All six source CSVs can be loaded into BI tools; use the documented keys and effective-dated cost rule rather than a many-to-many cost join.

