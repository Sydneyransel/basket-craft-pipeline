# Snowflake Loader Design

**Date:** 2026-04-20
**Status:** Approved

## Overview

A new standalone script `load_snowflake.py` reads the three Basket Craft raw tables from AWS RDS PostgreSQL and loads them into the Snowflake `raw` schema using the official `snowflake-connector-python` package. This extends the pipeline with a cloud-to-cloud path while leaving the existing local Docker pipeline intact.

## Pipeline Position

```
MySQL (db.isba.co)
  └─[extract.py]─► PostgreSQL public schema (Docker localhost:5433)
                      orders, order_items, products
                      └─[transform.py]─► analytics.monthly_sales_summary

AWS RDS PostgreSQL (public schema)
  orders, order_items, products
    └─[load_snowflake.py]─► Snowflake raw schema
                              orders, order_items, products
```

The two paths are independent and do not share state.

## Components

### `db.py` — new factory

Add `get_snowflake_connection()` alongside the existing engine factories:

```python
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

### `load_snowflake.py` — new script

Mirrors the structure of `extract.py`:

1. Import `get_pg_engine` and `get_snowflake_connection` from `db.py`
2. Define `TABLES = ["orders", "order_items", "products"]`
3. For each table:
   - Read the full table into a pandas DataFrame in-memory via `pd.read_sql()` using `get_pg_engine()` (dataset is small enough; no chunking needed)
   - Uppercase the DataFrame column names (`df.columns = df.columns.str.upper()`)
   - Write to Snowflake passing the table name in uppercase (e.g. `"ORDERS"`), with `overwrite=True, auto_create_table=True, quote_identifiers=False`
4. Print row counts per table; print completion message
5. Wrap in try/except — errors go to stderr, exit code 1

### `requirements.txt`

Add `snowflake-connector-python`.

### `.env`

Six new required variables:

```
SNOWFLAKE_ACCOUNT=<account-identifier>
SNOWFLAKE_USER=<username>
SNOWFLAKE_PASSWORD=<password>
SNOWFLAKE_WAREHOUSE=<warehouse-name>
SNOWFLAKE_DATABASE=<database-name>
SNOWFLAKE_SCHEMA=raw
```

## Data Flow

- **Source:** `public.orders`, `public.order_items`, `public.products` on AWS RDS PostgreSQL
- **Destination:** `raw.ORDERS`, `raw.ORDER_ITEMS`, `raw.PRODUCTS` on Snowflake (all identifiers uppercase, unquoted)
- **Chunking:** full table loaded into memory as a single DataFrame — appropriate for this dataset size
- **Write mode:** truncate-and-reload (`overwrite=True`) — tables are fully replaced on every run
- **Schema creation:** `auto_create_table=True` — Snowflake tables are created on first run; column types are inferred from the DataFrame

## Error Handling

Same pattern as `extract.py`: a single try/except wraps the full loop. Any exception prints to stderr and exits with code 1. No partial-load recovery — if one table fails, the script stops.

## Testing

No automated tests are added in this spec. Manual verification: compare row counts in Snowflake against the RDS source after running the script.
