# Basket Craft Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an ELT pipeline that extracts Basket Craft tables from MySQL into a local PostgreSQL Docker container, then transforms them into a monthly sales summary table.

**Architecture:** `extract.py` loads three raw MySQL tables (orders, order_items, products) into a `raw` schema in PostgreSQL as-is. `transform.py` runs a SQL GROUP BY aggregation inside PostgreSQL to produce `analytics.monthly_sales_summary` with revenue, order count, and average order value by product category and month.

**Tech Stack:** Python 3, SQLAlchemy, pymysql, psycopg2-binary, pandas, python-dotenv, pytest, Docker / PostgreSQL 15.

**Credentials:** All credentials live exclusively in `.env` (gitignored). No passwords or usernames appear in any committed file. `docker-compose.yml` reads from `.env` via `${VAR}` substitution. Python scripts read from `.env` via `python-dotenv`.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `docker-compose.yml` | Create | Runs PostgreSQL 15 container on host port 5433; reads credentials from `.env` |
| `requirements.txt` | Create | Python dependencies including pandas and pytest |
| `extract.py` | Create | Connects to MySQL, loads orders/order_items/products into raw schema |
| `transform.py` | Create | Runs aggregation SQL to build analytics.monthly_sales_summary |
| `tests/test_extract.py` | Create | Integration tests: DB connections + raw table row counts |
| `tests/test_transform.py` | Create | Integration tests: summary table existence, columns, positive values |

---

## Task 1: Docker and Python Environment

**Files:**
- Create: `docker-compose.yml`
- Create: `requirements.txt`

- [ ] **Step 1: Create docker-compose.yml**

Docker Compose automatically reads `.env` from the project root. The `${VAR}` syntax injects values at runtime — no credentials in this file.

```yaml
services:
  postgres:
    image: postgres:15
    container_name: basket_craft_db
    ports:
      - "${PG_PORT}:5432"
    environment:
      POSTGRES_DB: ${PG_DATABASE}
      POSTGRES_USER: ${PG_USER}
      POSTGRES_PASSWORD: ${PG_PASSWORD}
    volumes:
      - basket_craft_data:/var/lib/postgresql/data

volumes:
  basket_craft_data:
```

- [ ] **Step 2: Create requirements.txt**

Note: `pandas` is added here because `extract.py` uses `pd.read_sql` + `df.to_sql` to move data between databases — the cleanest cross-database copy approach in Python.

```
sqlalchemy
pymysql
psycopg2-binary
python-dotenv
pandas
pytest
```

- [ ] **Step 3: Create virtual environment and install dependencies**

```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows Git Bash
pip install -r requirements.txt
```

Expected: All packages install without error. `pip list` shows sqlalchemy, pymysql, psycopg2-binary, python-dotenv, pandas, pytest.

- [ ] **Step 4: Start the PostgreSQL container**

```bash
docker compose up -d
```

Expected output:
```
[+] Running 2/2
 ✔ Volume "basket-craft-pipeline_basket_craft_data"  Created
 ✔ Container basket_craft_db                          Started
```

- [ ] **Step 5: Verify the container is running**

```bash
docker ps --filter name=basket_craft_db
```

Expected: One row showing `basket_craft_db` with status `Up`.

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml requirements.txt
git commit -m "Add Docker and Python environment setup"
```

---

## Task 2: Write Failing Extract Tests

**Files:**
- Create: `tests/test_extract.py`

Write the tests first, before any implementation. They must fail right now.

- [ ] **Step 1: Create tests/test_extract.py**

```python
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
```

- [ ] **Step 2: Run the tests — verify they fail**

```bash
pytest tests/test_extract.py -v
```

Expected: `test_mysql_connection` and `test_pg_connection` PASS (connections work). The three `test_raw_table_has_rows` tests FAIL with `UndefinedTable` — the `raw` schema does not exist yet.

If `test_mysql_connection` also fails, confirm `.env` has correct `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE` values.

---

## Task 3: Implement extract.py

**Files:**
- Create: `extract.py`

- [ ] **Step 1: Create extract.py**

```python
import os
import sys
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

TABLES = ["orders", "order_items", "products"]


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


def main():
    try:
        mysql_engine = get_mysql_engine()
        pg_engine = get_pg_engine()

        with pg_engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))
            conn.commit()
        print("Raw schema ready.")

        for table in TABLES:
            df = pd.read_sql(f"SELECT * FROM {table}", mysql_engine)
            df.to_sql(table, pg_engine, schema="raw", if_exists="replace", index=False)
            print(f"  {table}: {len(df)} rows loaded")

        print("Extraction complete.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run extract.py**

```bash
python extract.py
```

Expected output (row counts will vary):
```
Raw schema ready.
  orders: 830 rows loaded
  order_items: 2491 rows loaded
  products: 42 rows loaded
Extraction complete.
```

If you see `Table 'basket_craft.order_items' doesn't exist`, the actual table name differs. Discover the real names:

```bash
python -c "
import os; from dotenv import load_dotenv; load_dotenv()
from sqlalchemy import create_engine, inspect
engine = create_engine(
    f\"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}\"
    f\"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DATABASE')}\"
)
print(inspect(engine).get_table_names())
"
```

Update `TABLES` in `extract.py` to match and re-run.

- [ ] **Step 3: Run extract tests — verify they now pass**

```bash
pytest tests/test_extract.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 4: Inspect actual column names for the transform step**

The transform SQL uses specific column names. Verify them now before writing transform.py:

```bash
python -c "
import os; from dotenv import load_dotenv; load_dotenv()
from sqlalchemy import create_engine, inspect
engine = create_engine(
    f\"postgresql+psycopg2://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}\"
    f\"@{os.getenv('PG_HOST')}:{os.getenv('PG_PORT')}/{os.getenv('PG_DATABASE')}\"
)
insp = inspect(engine)
for table in ['orders', 'order_items', 'products']:
    cols = [c['name'] for c in insp.get_columns(table, schema='raw')]
    print(f'raw.{table}: {cols}')
"
```

Note the actual names for:
- The date column in `raw.orders` (plan assumes `order_date`)
- The price column in `raw.order_items` (plan assumes `unit_price`)
- The category column in `raw.products` (plan assumes `category`)

If any differ, update the `TRANSFORM_SQL` in Task 5 Step 1 accordingly.

- [ ] **Step 5: Commit**

```bash
git add extract.py tests/test_extract.py
git commit -m "Add extract.py and integration tests for raw schema"
```

---

## Task 4: Write Failing Transform Tests

**Files:**
- Create: `tests/test_transform.py`

- [ ] **Step 1: Create tests/test_transform.py**

```python
import os
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

load_dotenv()


def get_pg_engine():
    url = (
        f"postgresql+psycopg2://{os.getenv('PG_USER')}:{os.getenv('PG_PASSWORD')}"
        f"@{os.getenv('PG_HOST', 'localhost')}:{os.getenv('PG_PORT', '5433')}"
        f"/{os.getenv('PG_DATABASE')}"
    )
    return create_engine(url)


def test_summary_table_has_rows():
    engine = get_pg_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM analytics.monthly_sales_summary")
        )
        count = result.scalar()
    assert count > 0, "monthly_sales_summary has no rows — did transform.py run?"


def test_summary_has_expected_columns():
    engine = get_pg_engine()
    insp = inspect(engine)
    columns = {
        col["name"]
        for col in insp.get_columns("monthly_sales_summary", schema="analytics")
    }
    expected = {"product_category", "month", "total_revenue", "order_count", "avg_order_value"}
    assert expected.issubset(columns), f"Missing columns: {expected - columns}"


def test_avg_order_value_is_positive():
    engine = get_pg_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT MIN(avg_order_value) FROM analytics.monthly_sales_summary")
        )
        min_aov = result.scalar()
    assert min_aov > 0, "avg_order_value should always be positive"
```

- [ ] **Step 2: Run the tests — verify they fail**

```bash
pytest tests/test_transform.py -v
```

Expected: All 3 tests FAIL — `analytics.monthly_sales_summary` does not exist yet.

---

## Task 5: Implement transform.py

**Files:**
- Create: `transform.py`

Before writing this file, confirm the actual column names from Task 3 Step 4. Update `TRANSFORM_SQL` if any column names differ from the defaults.

- [ ] **Step 1: Create transform.py**

```python
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Update column names in this SQL if Task 3 Step 4 revealed different names:
# - o.order_date       → date column in raw.orders
# - oi.unit_price      → price column in raw.order_items
# - p.category         → category column in raw.products
TRANSFORM_SQL = """
CREATE TABLE analytics.monthly_sales_summary AS
SELECT
    p.category                               AS product_category,
    DATE_TRUNC('month', o.order_date)        AS month,
    SUM(oi.quantity * oi.unit_price)         AS total_revenue,
    COUNT(DISTINCT o.order_id)               AS order_count,
    SUM(oi.quantity * oi.unit_price)
        / COUNT(DISTINCT o.order_id)         AS avg_order_value
FROM raw.orders o
JOIN raw.order_items oi ON o.order_id = oi.order_id
JOIN raw.products p     ON oi.product_id = p.product_id
GROUP BY p.category, DATE_TRUNC('month', o.order_date)
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
```

- [ ] **Step 2: Run transform.py**

```bash
python transform.py
```

Expected output (row count depends on data):
```
monthly_sales_summary: 48 rows created.
Transformation complete.
```

If you get `column "category" does not exist`, re-check Task 3 Step 4 output and update the column name in `TRANSFORM_SQL`.

- [ ] **Step 3: Run transform tests — verify they now pass**

```bash
pytest tests/test_transform.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 4: Run the full test suite**

```bash
pytest tests/ -v
```

Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add transform.py tests/test_transform.py
git commit -m "Add transform.py and integration tests for analytics schema"
```

---

## Task 6: End-to-End Verification and Final Push

Verify the pipeline output three ways, then push everything.

- [ ] **Step 1: Re-run the full pipeline from scratch**

```bash
python extract.py && python transform.py
```

Expected: Extract prints row counts for all three tables; transform prints summary row count. No errors.

- [ ] **Step 2: Verify with psql — check schemas and row counts**

```bash
docker exec -it basket_craft_db psql -U $PG_USER -d $PG_DATABASE -c "\dn"
docker exec -it basket_craft_db psql -U $PG_USER -d $PG_DATABASE \
  -c "SELECT 'orders' AS tbl, COUNT(*) FROM raw.orders
      UNION ALL SELECT 'order_items', COUNT(*) FROM raw.order_items
      UNION ALL SELECT 'products', COUNT(*) FROM raw.products
      UNION ALL SELECT 'monthly_sales_summary', COUNT(*) FROM analytics.monthly_sales_summary;"
```

Expected: Two schemas (`raw`, `analytics`). Row counts match what the scripts printed.

- [ ] **Step 3: Spot-check business logic**

```bash
docker exec -it basket_craft_db psql -U $PG_USER -d $PG_DATABASE \
  -c "SELECT product_category, ROUND(SUM(total_revenue)::numeric, 2) AS total
      FROM analytics.monthly_sales_summary
      GROUP BY product_category
      ORDER BY total DESC LIMIT 5;"
```

Expected: A ranked list of categories by revenue. Numbers should be plausible — not zero, not astronomically large.

- [ ] **Step 4: Push to GitHub**

```bash
git push
```

Expected: All commits pushed to `origin/main`.
