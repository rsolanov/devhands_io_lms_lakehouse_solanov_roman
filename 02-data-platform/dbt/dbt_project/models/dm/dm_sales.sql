{{
    config(
        materialized='table',
        schema='dm',
        alias='sales'
    )
}}

-- DM: витрина продаж по месяцам
SELECT
    c.customer_id,
    c.full_name,
    p.product_id,
    p.product_name,
    p.category,
    DATE_TRUNC('month', o.order_date)   AS order_month,
    COUNT(DISTINCT o.order_id)          AS order_count,
    SUM(o.quantity)                     AS total_quantity,
    SUM(o.total_amount)                 AS total_revenue,
    AVG(o.total_amount)                 AS avg_order_value,
    CURRENT_TIMESTAMP                   AS updated_dttm
FROM {{ ref('dds_orders') }} o
INNER JOIN {{ ref('dds_customers') }} c ON o.customer_id = c.customer_id
INNER JOIN {{ ref('dds_products') }} p  ON o.product_id  = p.product_id
GROUP BY
    c.customer_id,
    c.full_name,
    p.product_id,
    p.product_name,
    p.category,
    DATE_TRUNC('month', o.order_date)