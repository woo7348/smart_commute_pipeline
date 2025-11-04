-- db/init.sql
CREATE ROLE airflow WITH LOGIN PASSWORD 'airflow';
CREATE DATABASE airflow OWNER airflow;
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
