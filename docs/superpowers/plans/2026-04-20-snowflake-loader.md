# Snowflake Loader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `load_snowflake.py` that reads the three raw Basket Craft tables from AWS RDS PostgreSQL and loads them into the Snowflake `raw` schema, with all identifiers uppercased and tables replaced on every run.

**Architecture:** A new script mirrors the structure of `extract.py` — loop over `TABLES`, read each into a DataFrame with `pd.read_sql()`, uppercase column names, then bulk-load via `write_pandas()`. `get_snowflake_connection()` is added to `db.py` alongside the existing engine factories. Tests follow the existing pattern: session-scoped fixture in `conftest.py`, connection + row-count assertions in a new test file.

**Tech Stack:** `snowflake-connector-python`, `snowflake.connector.pandas_tools.write_pandas`, `pandas`, `python-dotenv`, `pytest`

---

## Prerequisites

`.env` must contain these six Snowflake variables before running any task:

```
SNOWFLAKE_ACCOUNT=<account-identifier>
SNOWFLAKE_USER=<username>
SNOWFLAKE_PASSWORD=<password>
SNOWFLAKE_WAREHOUSE=<warehouse-name>
SNOWFLAKE_DATABASE=<database-name>
SNOWFLAKE_SCHEMA=raw
```

---

## File Map

| Action | File | Purpose |
|---|---|---|
| Modify | `requirements.txt` | Add `snowflake-connector-python` |
| Modify | `db.py` | Add `get_snowflake_connection()` factory |
| Modify | `tests/conftest.py` | Add `sf_conn` session-scoped fixture |
| Create | `tests/test_snowflake_load.py` | Connection + row-count tests |
| Create | `load_snowflake.py` | Main loader script |

---

## Task 1: Add the Snowflake dependency

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add the package**

Open `requirements.txt`. It currently reads:
```
sqlalchemy
pymysql
psycopg2-binary
python-dotenv
pandas
pytest
```

Add one line so it reads:
```
sqlalchemy
pymysql
psycopg2-binary
python-dotenv
pandas
pytest
snowflake-connector-python
```

- [ ] **Step 2: Install**

```bash
pip install -r requirements.txt
```

Expected: pip resolves and installs `snowflake-connector-python` and its dependencies with no errors.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat: add snowflake-connector-python dependency"
```

---

## Task 2: Add `get_snowflake_connection()` to `db.py`

**Files:**
- Modify: `tests/conftest.py`
- Create: `tests/test_snowflake_load.py`
- Modify: `db.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_snowflake_load.py`:

```python
def test_snowflake_connection(sf_conn):
    cur = sf_conn.cursor()
    cur.execute("SELECT 1")
    assert cur.fetchone()[0] == 1
```

- [ ] **Step 2: Add the `sf_conn` fixture to `conftest.py`**

The current `conftest.py` is:
```python
import pytest

from db import get_mysql_engine, get_pg_engine


@pytest.fixture(scope="session")
def mysql_engine():
    return get_mysql_engine()


@pytest.fixture(scope="session")
def pg_engine():
    return get_pg_engine()
```

Replace it with:
```python
import pytest

from db import get_mysql_engine, get_pg_engine, get_snowflake_connection


@pytest.fixture(scope="session")
def mysql_engine():
    return get_mysql_engine()


@pytest.fixture(scope="session")
def pg_engine():
    return get_pg_engine()


@pytest.fixture(scope="session")
def sf_conn():
    conn = get_snowflake_connection()
    yield conn
    conn.close()
```

- [ ] **Step 3: Run to confirm it fails**

```bash
pytest tests/test_snowflake_load.py::test_snowflake_connection -v
```

Expected: `ImportError` — `cannot import name 'get_snowflake_connection' from 'db'`

- [ ] **Step 4: Implement `get_snowflake_connection()` in `db.py`**

The current `db.py` is:
```python
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

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
```

Replace it with:
```python
import os
import snowflake.connector
from dotenv import load_dotenv
from sqlalchemy import create_engine

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


def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )
```

- [ ] **Step 5: Run to confirm it passes**

```bash
pytest tests/test_snowflake_load.py::test_snowflake_connection -v
```

Expected:
```
tests/test_snowflake_load.py::test_snowflake_connection PASSED
```

- [ ] **Step 6: Commit**

```bash
git add db.py tests/conftest.py tests/test_snowflake_load.py
git commit -m "feat: add get_snowflake_connection factory and connection test"
```

---

## Task 3: Implement `load_snowflake.py` and verify row counts

**Files:**
- Modify: `tests/test_snowflake_load.py`
- Create: `load_snowflake.py`

- [ ] **Step 1: Write the failing row-count tests**

Replace the contents of `tests/test_snowflake_load.py` with:

```python
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
```

- [ ] **Step 2: Run to confirm they fail**

```bash
pytest tests/test_snowflake_load.py -v
```

Expected: `test_snowflake_connection` PASSED, all three `test_snowflake_table_has_rows` FAILED with something like `ProgrammingError: Table 'ORDERS' does not exist`.

- [ ] **Step 3: Create `load_snowflake.py`**

```python
import sys
import pandas as pd
from snowflake.connector.pandas_tools import write_pandas

from db import get_pg_engine, get_snowflake_connection

TABLES = ["orders", "order_items", "products"]


def main():
    try:
        pg_engine = get_pg_engine()
        conn = get_snowflake_connection()

        for table in TABLES:
            with pg_engine.connect() as pg_conn:
                df = pd.read_sql(f"SELECT * FROM {table}", pg_conn)
            df.columns = df.columns.str.upper()
            write_pandas(
                conn,
                df,
                table_name=table.upper(),
                overwrite=True,
                auto_create_table=True,
                quote_identifiers=False,
            )
            print(f"  {table}: {len(df)} rows loaded")

        conn.close()
        print("Snowflake load complete.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the script**

```bash
python load_snowflake.py
```

Expected output (row counts will vary):
```
  orders: 1000 rows loaded
  order_items: 3000 rows loaded
  products: 50 rows loaded
Snowflake load complete.
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
pytest tests/test_snowflake_load.py -v
```

Expected:
```
tests/test_snowflake_load.py::test_snowflake_connection PASSED
tests/test_snowflake_load.py::test_snowflake_table_has_rows[ORDERS] PASSED
tests/test_snowflake_load.py::test_snowflake_table_has_rows[ORDER_ITEMS] PASSED
tests/test_snowflake_load.py::test_snowflake_table_has_rows[PRODUCTS] PASSED
```

- [ ] **Step 6: Run full test suite to check for regressions**

```bash
pytest
```

Expected: all tests pass (existing extract/transform tests plus new Snowflake tests).

- [ ] **Step 7: Commit**

```bash
git add load_snowflake.py tests/test_snowflake_load.py
git commit -m "feat: add load_snowflake.py with RDS PostgreSQL to Snowflake raw loader"
```
