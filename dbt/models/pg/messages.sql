{{ config(
    materialized='table',
    database=target.database,
) }}

WITH source AS (
  SELECT
    event_id,
    message,
    created_at,
    inserted_at,
    updated_at,
    date_diff('ms', created_at, inserted_at) as latency
  FROM {{ source('postgres', 'messages') }}
)
SELECT
  event_id,
  message,
  created_at,
  inserted_at,
  latency
FROM source