from sqlalchemy import inspect, text


def test_summary_table_has_rows(pg_engine):
    with pg_engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM monthly_sales_summary")
        )
        count = result.scalar()
    assert count > 0, "monthly_sales_summary has no rows — did transform.py run?"


def test_summary_has_expected_columns(pg_engine):
    insp = inspect(pg_engine)
    columns = {
        col["name"]
        for col in insp.get_columns("monthly_sales_summary", schema="public")
    }
    expected = {"product_category", "month", "total_revenue", "order_count", "avg_order_value"}
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_avg_order_value_is_positive(pg_engine):
    with pg_engine.connect() as conn:
        result = conn.execute(
            text("SELECT MIN(avg_order_value) FROM monthly_sales_summary")
        )
        min_aov = result.scalar()
    assert min_aov is not None and min_aov > 0, "avg_order_value should always be positive"
