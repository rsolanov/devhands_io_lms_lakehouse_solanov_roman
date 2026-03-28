{{
    config(
        materialized='table',
        schema='ods',
        alias='orders',
        unique_key='order_id'
    )
}}

SELECT
    order_id,
    customer_id,
    product_id,
    quantity,
    order_date,
    CURRENT_TIMESTAMP as updated_dttm
FROM {{ source('product', 'orders') }}