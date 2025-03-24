MODEL (
  name md.taxi_passengers_by_hour,
  kind  VIEW,
);

SELECT 
    DATE_TRUNC('hour', tpep_pickup_datetime
  ) AS hour,
    SUM(passenger_count) AS total_passengers
FROM 
    sample_data.nyc.taxi
GROUP BY
    DATE_TRUNC('hour', tpep_pickup_datetime)
ORDER BY 
    hour;