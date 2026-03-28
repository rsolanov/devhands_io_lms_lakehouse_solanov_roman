{{
    config(
        materialized='table',
        schema='dm',
        alias='products',
        unique_key='product_id'
    )
}}

-- DM: производительность продуктов
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.current_price,
    COUNT(DISTINCT o.order_id)          AS order_count,
    COALESCE(SUM(o.quantity), 0)        AS units_sold,
    COALESCE(SUM(o.total_amount), 0)    AS total_revenue,
    COALESCE(AVG(o.total_amount), 0)    AS avg_sale_amount,
    COUNT(DISTINCT o.customer_id)       AS unique_customers,
    CURRENT_TIMESTAMP                   AS updated_dttm
FROM {{ ref('dds_products') }} p
LEFT JOIN {{ ref('dds_orders') }} o
    ON p.product_id = o.product_id
GROUP BY
    p.product_id,
    p.product_name,
    p.category,
    p.current_price