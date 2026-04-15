# Basket Craft Pipeline — Design Spec
**Date:** 2026-04-15
**Author:** Sydney
**Status:** Approved

---

## Business Question

The Basket Craft team wants a monthly sales dashboard showing:
- Total revenue
- Order count
- Average order value (AOV)

…grouped by **product category** and **month**.

---

## Architecture

```
MySQL (db.isba.co:3306)
  database: basket_craft
  └─[extract.py]─► PostgreSQL raw schema (Docker localhost:5433)
                      raw.orders
                      raw.order_items
                      raw.products
                      └─[transform.py]─► analytics.monthly_sales_summary
                                          columns: product_category, month,
                                                   total_revenue, order_count,
                                                   avg_order_value
```

**Pattern:** ELT — raw data lands in PostgreSQL first, transformation happens inside the database using SQL.

---

## File Structure

```
basket-craft-pipeline/
├── .env                            # credentials (gitignored)
├── .gitignore
├── CLAUDE.md                       # project instructions for Claude Code
├── docker-compose.yml              # PostgreSQL container
├── requirements.txt                # Python dependencies
├── extract.py                      # Stage 1: MySQL → PostgreSQL raw schema
├── transform.py                    # Stage 2: raw → analytics.monthly_sales_summary
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-04-15-pipeline-design.md
```

---

## Components

### `docker-compose.yml`
Runs a PostgreSQL 15 container:
- Container name: `basket_craft_db`
- Host port: `5433` (avoids conflict with MP01 which uses `5432`)
- Database: `basket_craft`
- User: `student` / Password: `go_lions`

### `.env`
```
MYSQL_HOST=db.isba.co
MYSQL_PORT=3306
MYSQL_USER=analyst
MYSQL_PASSWORD=go_lions
MYSQL_DATABASE=basket_craft

PG_HOST=localhost
PG_PORT=5433
PG_USER=student
PG_PASSWORD=go_lions
PG_DATABASE=basket_craft
```

### `extract.py`
- Reads MySQL credentials from `.env` via `python-dotenv`
- Connects to MySQL using SQLAlchemy + pymysql
- Loads the following tables into the `raw` schema in PostgreSQL:
  - `orders`
  - `order_items`
  - `products`
  - (exact column names discovered at runtime; all columns loaded as-is)
- Prints row count per table after each load
- Wraps operations in try/except; exits with error message on failure

### `transform.py`
- Reads PostgreSQL credentials from `.env`
- Creates `analytics` schema if it does not exist
- Drops and recreates `analytics.monthly_sales_summary`
- Runs the following aggregation SQL:

```sql
CREATE TABLE analytics.monthly_sales_summary AS
SELECT
    p.category                              AS product_category,
    DATE_TRUNC('month', o.order_date)       AS month,
    SUM(oi.quantity * oi.unit_price)        AS total_revenue,
    COUNT(DISTINCT o.order_id)              AS order_count,
    SUM(oi.quantity * oi.unit_price)
      / COUNT(DISTINCT o.order_id)          AS avg_order_value
FROM raw.orders o
JOIN raw.order_items oi ON o.order_id = oi.order_id
JOIN raw.products p     ON oi.product_id = p.product_id
GROUP BY p.category, DATE_TRUNC('month', o.order_date)
ORDER BY month, product_category;
```

- Prints row count of `monthly_sales_summary` after creation
- Exact column names (`order_date`, `unit_price`, `category`) adjusted to match actual source schema if needed

### `requirements.txt`
```
sqlalchemy
pymysql
psycopg2-binary
python-dotenv
pandas
```

---

## Output Table

`analytics.monthly_sales_summary` — one row per product category per month:

| Column | Type | Description |
|---|---|---|
| `product_category` | text | Product category name from `products` table |
| `month` | timestamp | First day of the month (via `DATE_TRUNC`) |
| `total_revenue` | numeric | Sum of `quantity × unit_price` for all orders in that month/category |
| `order_count` | integer | Count of distinct orders |
| `avg_order_value` | numeric | `total_revenue / order_count` |

---

## Error Handling

- Both scripts use `try/except` blocks around all database operations
- On failure: print descriptive error message and exit with non-zero code
- On success: print row counts to confirm data landed correctly

---

## Verification Plan

After the pipeline runs, verify with three methods:

1. **psql via Claude Code** — check table names and row counts in both schemas
2. **DBeaver** — browse `analytics.monthly_sales_summary` visually
3. **Claude Code natural language** — ask "what category had the highest total revenue?" and sanity-check the answer against expectations

---

## Out of Scope

- Unit tests / pytest (verification steps above serve this purpose)
- Incremental loads (full refresh on each run)
- Data quality checks beyond row count confirmation
- Filtering by order status (all orders included)
