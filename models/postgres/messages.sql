MODEL (
  name pg.messages,
  kind VIEW,
  dialect duckdb,
  audits (
    latency_threshold(column := latency, threshold := 1000)
  )
);

WITH source AS (
  SELECT
    event_id,
    message,
    created_at,
    inserted_at,
    updated_at,
    date_diff('ms', created_at, inserted_at) as latency
  FROM postgres.public.messages
)
SELECT
  event_id,
  message,
  created_at,
  inserted_at,
  latency
FROM source