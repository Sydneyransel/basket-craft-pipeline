import sys
from sqlalchemy import text

from db import get_pg_engine

# Column names confirmed from actual source schema:
# - o.created_at   → date column in orders (no order_date column exists)
# - oi.price_usd   → per-item price in order_items (no quantity column; price_usd is the line total)
# - p.product_name → grouped as product_category (no category column exists in products)
TRANSFORM_SQL = """
CREATE TABLE analytics.monthly_sales_summary AS
SELECT
    p.product_name                                 AS product_category,
    DATE_TRUNC('month', o.created_at)              AS month,
    SUM(oi.price_usd)                              AS total_revenue,
    COUNT(DISTINCT o.order_id)                     AS order_count,
    SUM(oi.price_usd) / COUNT(DISTINCT o.order_id) AS avg_order_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p     ON oi.product_id = p.product_id
GROUP BY p.product_name, DATE_TRUNC('month', o.created_at)
ORDER BY month, product_category
"""


def main():
    try:
        pg_engine = get_pg_engine()

        with pg_engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))
            conn.execute(text("DROP TABLE IF EXISTS analytics.monthly_sales_summary"))
            conn.execute(text(TRANSFORM_SQL))
            result = conn.execute(
                text("SELECT COUNT(*) FROM analytics.monthly_sales_summary")
            )
            row_count = result.scalar()
            conn.commit()

        print(f"monthly_sales_summary: {row_count} rows created.")
        print("Transformation complete.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
