with source as (
    select * from {{ source('raw', 'orders') }}
),

renamed as (
    select
        order_id,
        cast(created_at as timestamp) as created_at,
        website_session_id,
        user_id as customer_id,
        primary_product_id,
        items_purchased,
        price_usd,
        cogs_usd
    from source
)

select * from renamed
