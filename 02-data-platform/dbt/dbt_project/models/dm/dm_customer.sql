{{
    config(
        materialized='table',
        schema='dm',
        alias='customers',
        unique_key='customer_id'
    )
}}

-- DM: метрики клиентов
SELECT
    c.customer_id,
    c.full_name,
    c.email,
    c.registration_date,
    COUNT(DISTINCT o.order_id)                              AS total_orders,
    COALESCE(SUM(o.total_amount), 0)                        AS lifetime_value,
    COALESCE(AVG(o.total_amount), 0)                        AS avg_order_value,
    MIN(o.order_date)                                       AS first_order_date,
    MAX(o.order_date)                                       AS last_order_date,
    date_diff('day', MAX(o.order_date), CURRENT_DATE)       AS days_since_last_order,
    CURRENT_TIMESTAMP                                       AS updated_dttm
FROM {{ ref('dds_customers') }} c
LEFT JOIN {{ ref('dds_orders') }} o
    ON c.customer_id = o.customer_id
GROUP BY
    c.customer_id,
    c.full_name,
    c.email,
    c.registration_date