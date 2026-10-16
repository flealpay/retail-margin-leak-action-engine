# Generated synthetic data

Run `python generate.py` or `python run.py` from the repository root. The six source CSVs are intentionally excluded from Git; generation uses a fixed seed and requires no downloads. `manifest.json` records expected dimensions and source checksums for the default scenario.

| Source | Default rows |
| --- | ---: |
| `dim_product.csv` | 500 |
| `dim_customer.csv` | 20,000 |
| `dim_promotion.csv` | 35 |
| `fact_sales.csv` | 180,000 |
| `fact_cost_history.csv` | 1,000 |
| `fact_inventory_daily.csv` | 547,500 |

Monetary source fields are integer EUR cents. Each sales line belongs to an order. Costs join by SKU and the most recent effective date before or on the sale date. See [the full data model](../docs/data-model.md).

The [50-line sample](../examples/sales-sample.csv) is for inspecting the sales schema only. It is not a complete dataset and cannot replace the generated source tables for analysis.

