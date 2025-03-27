{{ config(
    materialized='table',
    database=target.database,
) }}

SELECT 
    DATE_TRUNC('hour', tpep_dropoff_datetime) AS hour,
    SUM(passenger_count) AS total_passengers
FROM 
    {{ source('motherduck', 'taxi') }}
GROUP BY
    DATE_TRUNC('hour', tpep_dropoff_datetime)
ORDER BY 
    hour
