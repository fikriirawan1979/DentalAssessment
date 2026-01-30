-- Create dental assessment database schema
-- Initial database setup for PostgreSQL

-- Create database if not exists (commented out as we assume database exists)
-- CREATE DATABASE IF NOT EXISTS dental_db;

-- Create extensions for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create user with limited permissions for the application
-- (uncomment if you want to create user)
-- DO $$
-- BEGIN
--   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'dental_user') THEN
--     CREATE ROLE dental_user LOGIN PASSWORD 'dental_password';
--   END IF;
-- END
-- $$;

-- Grant permissions to user
-- GRANT ALL PRIVILEGES ON DATABASE dental_db TO dental_user;
-- GRANT ALL ON SCHEMA public TO dental_user;

-- Set timezone
SET timezone = 'UTC';

-- Create indexes for better performance
-- These will be created by SQLAlchemy models, but here for reference
-- CREATE INDEX IF NOT EXISTS idx_assessments_created_at ON assessments(created_at);
-- CREATE INDEX IF NOT EXISTS idx_assessments_model_type ON assessments(model_type);
-- CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);
-- CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
-- CREATE INDEX IF NOT EXISTS idx_uploaded_files_created_at ON uploaded_files(created_at);
-- CREATE INDEX IF NOT EXISTS idx_prediction_cache_file_hash ON prediction_cache(file_hash);
-- CREATE INDEX IF NOT EXISTS idx_prediction_cache_expires_at ON prediction_cache(expires_at);

-- Comments for tables
COMMENT ON DATABASE dental_db IS 'Dental Assessment Application Database';