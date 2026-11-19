-- Standalone inspection queries for data/telemetry.db
SELECT COUNT(*) AS total_readings FROM readings;
SELECT COUNT(*) AS missing_readings FROM readings WHERE reading IS NULL;
SELECT COUNT(*) AS out_of_range FROM readings WHERE reading < 0 OR reading > 120;
SELECT COUNT(*) AS unknown_sensor FROM readings r LEFT JOIN sensors s ON r.sensor_id=s.sensor_id WHERE s.sensor_id IS NULL;
SELECT event_id, COUNT(*) AS occurrences FROM readings GROUP BY event_id HAVING COUNT(*) > 1;
-- Window function: ranked readings per sensor
SELECT sensor_id, recorded_at, reading, ROW_NUMBER() OVER (PARTITION BY sensor_id ORDER BY recorded_at DESC) AS recency_rank FROM readings LIMIT 50;
-- CTE: per-plant counts
WITH per_plant AS (SELECT s.plant, COUNT(*) AS records FROM readings r JOIN sensors s ON r.sensor_id=s.sensor_id GROUP BY s.plant) SELECT * FROM per_plant ORDER BY records DESC;
