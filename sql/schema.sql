PRAGMA foreign_keys = ON;
CREATE TABLE dim_product (
 product_id TEXT PRIMARY KEY, product_name TEXT NOT NULL, category TEXT NOT NULL,
 subcategory TEXT, brand TEXT, tier TEXT NOT NULL, base_price_cents INTEGER NOT NULL,
 initial_cost_cents INTEGER NOT NULL, base_margin_pct REAL, launch_date TEXT
);
CREATE TABLE dim_customer (
 customer_id TEXT PRIMARY KEY, customer_segment TEXT NOT NULL, region TEXT NOT NULL,
 acquisition_channel TEXT, join_date TEXT, loyalty_member INTEGER CHECK(loyalty_member IN (0,1))
);
CREATE TABLE dim_promotion (
 promotion_id TEXT PRIMARY KEY, promo_name TEXT, promo_type TEXT, start_date TEXT, end_date TEXT,
 target_category TEXT, target_segment TEXT, discount_depth REAL, channel TEXT
);
CREATE TABLE fact_cost_history (
 product_id TEXT REFERENCES dim_product, effective_date TEXT, unit_cost_cents INTEGER NOT NULL,
 cost_change_pct REAL, supplier_id TEXT, PRIMARY KEY(product_id,effective_date)
);
CREATE TABLE fact_inventory_daily (
 date TEXT, product_id TEXT REFERENCES dim_product, region TEXT, stock_on_hand INTEGER,
 in_stock_flag INTEGER CHECK(in_stock_flag IN (0,1)), PRIMARY KEY(date,product_id,region)
);
CREATE TABLE fact_sales (
 sales_line_id TEXT PRIMARY KEY, transaction_id TEXT NOT NULL, date TEXT NOT NULL,
 customer_id TEXT REFERENCES dim_customer, product_id TEXT REFERENCES dim_product,
 quantity INTEGER CHECK(quantity>0), regular_price_cents INTEGER CHECK(regular_price_cents>0),
 selling_price_cents INTEGER CHECK(selling_price_cents>=0 AND selling_price_cents<=regular_price_cents),
 promotion_id TEXT REFERENCES dim_promotion, channel TEXT, region TEXT
);
CREATE INDEX sales_cell ON fact_sales(product_id,region,channel,date);
CREATE INDEX sales_date ON fact_sales(date);
CREATE VIEW v_sales AS
SELECT s.*, p.category, p.tier, p.product_name, c.customer_segment,
 CASE WHEN s.date < '2025-07-01' THEN 'H1' ELSE 'H2' END AS period,
 h.unit_cost_cents,
 s.quantity * s.selling_price_cents AS revenue_cents,
 s.quantity * h.unit_cost_cents AS cogs_cents,
 s.quantity * (s.selling_price_cents-h.unit_cost_cents) AS gross_profit_cents,
 s.quantity * (s.regular_price_cents-s.selling_price_cents) AS discount_cents
FROM fact_sales s
JOIN dim_product p USING(product_id)
JOIN dim_customer c USING(customer_id)
JOIN fact_cost_history h ON h.product_id=s.product_id AND h.effective_date=(
 SELECT MAX(h2.effective_date) FROM fact_cost_history h2
 WHERE h2.product_id=s.product_id AND h2.effective_date<=s.date
);

