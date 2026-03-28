{{
    config(
        materialized='table',
        schema='ods',
        alias='products',
        unique_key='product_id'
    )
}}

SELECT
    product_id,
    product_name,
    category,
    price,
    CURRENT_TIMESTAMP as updated_dttm
FROM {{ source('product', 'products') }}