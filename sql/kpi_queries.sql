-- Read-only examples for outputs/retail.sqlite, created by analyze.py.
-- All financial calculations originate in v_sales and its materialization.

-- 1. Half-year financial performance. Margin is a ratio of sums.
SELECT period,
       SUM(quantity) AS units,
       ROUND(SUM(revenue_cents) / 100.0, 2) AS revenue_eur,
       ROUND(SUM(cogs_cents) / 100.0, 2) AS cogs_eur,
       ROUND(SUM(gross_profit_cents) / 100.0, 2) AS gross_profit_eur,
       ROUND(100.0 * SUM(gross_profit_cents) / NULLIF(SUM(revenue_cents), 0), 2) AS gross_margin_pct
FROM sales_metrics
GROUP BY period ORDER BY period;

-- 2. Locate changes in gross profit, without adding percentage-point changes.
SELECT category, region, channel,
       ROUND(SUM(CASE WHEN period='H2' THEN gross_profit_cents ELSE -gross_profit_cents END) / 100.0, 2) AS gp_change_eur
FROM sales_metrics
GROUP BY category, region, channel ORDER BY gp_change_eur;

-- 3. Quantity-weighted discount depth at product level.
SELECT period, product_id, category,
       SUM(quantity) AS units,
       ROUND(100.0 * SUM(discount_cents) / NULLIF(SUM(quantity * regular_price_cents), 0), 2) AS discount_depth_pct,
       ROUND(SUM(gross_profit_cents)/100.0, 2) AS gross_profit_eur
FROM sales_metrics
GROUP BY period, product_id, category ORDER BY product_id, period;

