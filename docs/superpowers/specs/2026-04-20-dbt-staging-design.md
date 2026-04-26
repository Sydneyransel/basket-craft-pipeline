# dbt Staging Layer Design

**Date:** 2026-04-20
**Status:** Approved

## Overview

Four dbt staging models under `models/staging/`, each materialised as a view. Staging models do exactly three things: select from a source, rename columns for consistency, and cast data types. No JOINs, no WHERE filters, no aggregations — ever.

## File Structure

```
basket_craft/models/
  staging/
    stg_customers.sql
    stg_orders.sql
    stg_order_items.sql
    stg_products.sql
    _stg_sources.yml        ← column docs + not_null/unique tests
```

The `models/example/` directory (dbt scaffold) is deleted. `dbt_project.yml` gets a `staging` config block:

```yaml
models:
  basket_craft:
    staging:
      +materialized: view
```

## Model Definitions

### `stg_customers`

Source: `{{ source('raw', 'customers') }}`

| Source column | Staging column | Notes |
|---|---|---|
| `customer_id` | `customer_id` | PK |
| `first_name` | `first_name` | |
| `last_name` | `last_name` | |
| `email` | `email` | |
| `password_salt` | — | Dropped — no analytical value |
| `password_hash` | — | Dropped — no analytical value |
| `billing_street_address` | `billing_street_address` | |
| `billing_city` | `billing_city` | |
| `billing_state` | `billing_state` | |
| `billing_postal_code` | `billing_postal_code` | |
| `billing_country` | `billing_country` | |
| `shipping_street_ddress` | `shipping_street_address` | Fix source typo (double `d`) |
| `shipping_city` | `shipping_city` | |
| `shipping_state` | `shipping_state` | |
| `shipping_postal_code` | `shipping_postal_code` | |
| `shipping_country` | `shipping_country` | |
| `created_at` | `created_at` | Cast to `timestamp` |

### `stg_orders`

Source: `{{ source('raw', 'orders') }}`

| Source column | Staging column | Notes |
|---|---|---|
| `order_id` | `order_id` | PK |
| `created_at` | `created_at` | Cast to `timestamp` |
| `website_session_id` | `website_session_id` | |
| `user_id` | `customer_id` | Rename FK to match entity name |
| `primary_product_id` | `primary_product_id` | |
| `items_purchased` | `items_purchased` | |
| `price_usd` | `price_usd` | |
| `cogs_usd` | `cogs_usd` | |

### `stg_order_items`

Source: `{{ source('raw', 'order_items') }}`

| Source column | Staging column | Notes |
|---|---|---|
| `order_item_id` | `order_item_id` | PK |
| `created_at` | `created_at` | Cast to `timestamp` |
| `order_id` | `order_id` | FK |
| `product_id` | `product_id` | FK |
| `is_primary_item` | `is_primary_item` | Cast to `boolean` |
| `price_usd` | `price_usd` | |
| `cogs_usd` | `cogs_usd` | |

### `stg_products`

Source: `{{ source('raw', 'products') }}`

| Source column | Staging column | Notes |
|---|---|---|
| `product_id` | `product_id` | PK |
| `created_at` | `created_at` | Cast to `timestamp` |
| `product_name` | `product_name` | |
| `description` | `description` | |

## Tests (`_stg_sources.yml`)

| Model | Column | Tests |
|---|---|---|
| `stg_customers` | `customer_id` | `not_null`, `unique` |
| `stg_orders` | `order_id` | `not_null`, `unique` |
| `stg_orders` | `customer_id` | `not_null` |
| `stg_order_items` | `order_item_id` | `not_null`, `unique` |
| `stg_order_items` | `order_id` | `not_null` |
| `stg_order_items` | `product_id` | `not_null` |
| `stg_products` | `product_id` | `not_null`, `unique` |

Run with: `dbt test --select staging`

## Staging Discipline

Staging models must never contain:
- `JOIN` of any kind
- `WHERE` clauses
- `GROUP BY` / aggregations (`COUNT`, `SUM`, `AVG`, etc.)

Any logic beyond renaming and casting belongs in a downstream marts model.
