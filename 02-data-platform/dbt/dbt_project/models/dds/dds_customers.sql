{{
    config(
        materialized='table',
        schema='dds',
        alias='customers',
        unique_key='customer_id'
    )
}}

SELECT
    customer_id,
    first_name,
    last_name,
    CONCAT(first_name, ' ', last_name) AS full_name,
    email,
    registration_date,
    CURRENT_TIMESTAMP as updated_dttm
FROM {{ ref('ods_customers') }}