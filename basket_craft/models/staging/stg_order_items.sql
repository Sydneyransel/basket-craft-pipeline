with source as (
    select * from {{ source('raw', 'order_items') }}
),

renamed as (
    select
        order_item_id,
        cast(created_at as timestamp) as created_at,
        order_id,
        product_id,
        cast(is_primary_item as boolean) as is_primary_item,
        price_usd,
        cogs_usd
    from source
)

select * from renamed
