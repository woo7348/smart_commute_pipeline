CREATE TABLE weather (
  id SERIAL PRIMARY KEY,
  base_time TIMESTAMP,
  temperature FLOAT,
  rainfall FLOAT,
  wind_speed FLOAT
);

CREATE TABLE bus_delay (
  id SERIAL PRIMARY KEY,
  route_id VARCHAR(20),
  station_id VARCHAR(20),
  arrival_time TIMESTAMP,
  delay_seconds INT
);

CREATE TABLE joined_analysis (
  id SERIAL PRIMARY KEY,
  route_id VARCHAR(20),
  station_id VARCHAR(20),
  temperature FLOAT,
  rainfall FLOAT,
  delay_rate FLOAT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
