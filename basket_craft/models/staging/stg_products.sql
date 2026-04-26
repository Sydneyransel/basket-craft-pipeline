with source as (
    select * from {{ source('raw', 'products') }}
),

renamed as (
    select
        product_id,
        cast(created_at as timestamp) as created_at,
        product_name,
        description
    from source
)

select * from renamed
