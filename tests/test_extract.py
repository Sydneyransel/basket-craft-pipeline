import pytest
from sqlalchemy import text


def test_mysql_connection(mysql_engine):
    with mysql_engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_pg_connection(pg_engine):
    with pg_engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.parametrize("table", ["orders", "order_items", "products"])
def test_raw_table_has_rows(table, pg_engine):
    with pg_engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.scalar()
    assert count > 0, f"{table} has no rows — did extract.py run?"
