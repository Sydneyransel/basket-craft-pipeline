with source as (
    select * from {{ source('raw', 'customers') }}
),

renamed as (
    select
        customer_id,
        first_name,
        last_name,
        email,
        billing_street_address,
        billing_city,
        billing_state,
        billing_postal_code,
        billing_country,
        shipping_street_ddress as shipping_street_address,
        shipping_city,
        shipping_state,
        shipping_postal_code,
        shipping_country,
        cast(created_at as timestamp) as created_at
    from source
)

select * from renamed
