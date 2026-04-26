import pytest


def test_snowflake_connection(sf_conn):
    cur = sf_conn.cursor()
    cur.execute("SELECT 1")
    assert cur.fetchone()[0] == 1


@pytest.mark.parametrize("table", ["ORDERS", "ORDER_ITEMS", "PRODUCTS"])
def test_snowflake_table_has_rows(table, sf_conn):
    cur = sf_conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    assert count > 0, f"{table} has no rows — did load_snowflake.py run?"
