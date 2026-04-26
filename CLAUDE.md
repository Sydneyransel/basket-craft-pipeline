# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Instructions

Use a Python virtual environment to manage dependencies.

## Commands

All commands assume the `.venv` is activated (`source .venv/Scripts/activate` on Windows Git Bash, or `.venv\Scripts\Activate.ps1` in PowerShell).

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Start PostgreSQL container:**
```bash
docker compose up -d
```

**Run the full pipeline:**
```bash
python extract.py   # MySQL → PostgreSQL public schema
python transform.py # public tables → analytics.monthly_sales_summary
```

**Load raw tables into Snowflake:**
```bash
python load_snowflake.py  # AWS RDS PostgreSQL raw schema → Snowflake raw schema
```

**Run all tests:**
```bash
pytest
```

**Run a single test:**
```bash
pytest tests/test_transform.py::test_summary_has_expected_columns -v
```

Tests require both the pipeline scripts to have run first — they verify the database state, not the scripts themselves.

## Architecture

This is an ELT pipeline (Extract → Load → Transform):

```
MySQL (db.isba.co:3306)
  └─[extract.py]─► PostgreSQL public schema (Docker localhost:5433)
                      orders, order_items, products
                      └─[transform.py]─► analytics.monthly_sales_summary

AWS RDS PostgreSQL raw schema
  orders, order_items, products
    └─[load_snowflake.py]─► Snowflake raw schema
                              ORDERS, ORDER_ITEMS, PRODUCTS
```

**`db.py`** — shared SQLAlchemy engine factories (`get_mysql_engine()`, `get_pg_engine()`). Both `extract.py` and `transform.py` import from here. Credentials come from `.env` via `python-dotenv`.

**`extract.py`** — reads all three tables from MySQL with pandas `read_sql`, writes them to the `public` schema in PostgreSQL using `df.to_sql(..., if_exists="replace")`. No schema transformation happens here.

**`transform.py`** — runs a single `CREATE TABLE AS SELECT` inside PostgreSQL that joins the three raw tables and aggregates by `product_name` and truncated month. Writes to `analytics.monthly_sales_summary`. The `analytics` schema is created if it doesn't exist; the table is dropped and recreated on each run.

**`load_snowflake.py`** — reads all three tables from AWS RDS PostgreSQL (`raw` schema) into pandas DataFrames, uppercases column names, and bulk-loads into Snowflake `raw` schema using `write_pandas`. Tables are truncated and replaced on every run (`overwrite=True`). Requires six `SNOWFLAKE_*` env vars in `.env`.

**`tests/conftest.py`** — provides session-scoped `mysql_engine` and `pg_engine` fixtures via `db.py`. `pytest.ini` sets `pythonpath = .` so test files can import project modules.

## Schema Layout

- `public.orders`, `public.order_items`, `public.products` — raw source tables (easy DBeaver browsing)
- `analytics.monthly_sales_summary` — derived output (product_category, month, total_revenue, order_count, avg_order_value)

## Key Column Notes

The actual MySQL source schema differs from generic naming conventions:
- `orders.created_at` (not `order_date`)
- `order_items.price_usd` (line total; no `quantity` or `unit_price` columns)
- `products.product_name` (no `category` column — used as `product_category` in the summary)

## Environment

`.env` is gitignored and must be created locally. Required variables:
```
MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE
SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_WAREHOUSE, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA
```

PostgreSQL runs on port `5433` (not the default `5432`) to avoid conflicts with other local PostgreSQL instances.
