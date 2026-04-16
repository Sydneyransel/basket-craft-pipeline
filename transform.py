import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Column names confirmed from actual raw schema:
# - o.created_at      → date column in raw.orders
# - oi.price_usd      → price column in raw.order_items
# - p.product_name    → grouping dimension (no category column exists; aliased as product_category)
TRANSFORM_SQL = """
CREATE TABLE analytics.monthly_sales_summary AS
SELECT
    p.product_name                               AS product_category,
    DATE_TRUNC('month', o.created_at)            AS month,
    SUM(oi.price_usd)                            AS total_revenue,
    COUNT(DISTINCT o.order_id)                   AS order_count,
    SUM(oi.price_usd) / COUNT(DISTINCT o.order_id) AS avg_order_value
FROM raw.orders o
JOIN raw.order_items oi ON o.order_id = oi.order_id
JOIN raw.products p     ON oi.product_id = p.product_id
GROUP BY p.product_name, DATE_TRUNC('month', o.created_at)
ORDER BY month, product_category
"""


def get_pg_engine():
    url = (
        f"postgresql+psycopg2://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}"
        f"@{os.getenv('PG_HOST', 'localhost')}:{os.getenv('PG_PORT', '5433')}"
        f"/{os.getenv('PG_DATABASE')}"
    )
    return create_engine(url)


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
