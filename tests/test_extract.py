import os
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


def get_mysql_engine():
    url = (
        f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
        f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT', '3306')}"
        f"/{os.getenv('MYSQL_DATABASE')}"
    )
    return create_engine(url)


def get_pg_engine():
    url = (
        f"postgresql+psycopg2://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}"
        f"@{os.getenv('PG_HOST', 'localhost')}:{os.getenv('PG_PORT', '5433')}"
        f"/{os.getenv('PG_DATABASE')}"
    )
    return create_engine(url)


def test_mysql_connection():
    engine = get_mysql_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_pg_connection():
    engine = get_pg_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.parametrize("table", ["orders", "order_items", "products"])
def test_raw_table_has_rows(table):
    engine = get_pg_engine()
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM raw.{table}"))
        count = result.scalar()
    assert count > 0, f"raw.{table} has no rows — did extract.py run?"
