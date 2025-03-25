AUDIT (
  name latency_threshold 
);
SELECT * FROM @this_model
WHERE @column >= @threshold;