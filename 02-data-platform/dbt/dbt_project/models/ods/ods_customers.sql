{{
    config(
        materialized='table',
        schema='ods',
        alias='customers',
        unique_key='customer_id'
    )
}}

SELECT
    customer_id,
    first_name,
    last_name,
    email,
    registration_date,
    CURRENT_TIMESTAMP as updated_dttm
FROM {{ source('product', 'customers') }}