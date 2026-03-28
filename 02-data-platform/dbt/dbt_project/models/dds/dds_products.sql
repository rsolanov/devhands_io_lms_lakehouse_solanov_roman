{{
    config(
        materialized='table',
        schema='dds',
        alias='products',
        unique_key='product_id'
    )
}}

SELECT
    product_id,
    product_name,
    category,
    price AS current_price,
    CURRENT_TIMESTAMP as updated_dttm
FROM {{ ref('ods_products') }}