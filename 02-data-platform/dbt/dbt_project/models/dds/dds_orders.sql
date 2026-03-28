{{
    config(
        materialized='table',
        schema='dds',
        alias='orders',
        unique_key='order_id'
    )
}}

SELECT
    o.order_id,
    o.customer_id,
    o.product_id,
    o.quantity,
    p.current_price                      as unit_price,
    o.quantity * p.current_price         as total_amount,
    o.order_date,
    CURRENT_TIMESTAMP                    as updated_dttm
FROM {{ ref('ods_orders') }} o
LEFT JOIN {{ ref('dds_products') }} p
    ON o.product_id = p.product_id