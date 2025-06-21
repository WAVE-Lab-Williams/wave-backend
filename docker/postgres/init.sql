-- PostgreSQL initialization script for WAVE development database
-- This script runs when the PostgreSQL container starts for the first time

-- Create additional database if needed
-- CREATE DATABASE wave_dev_backup;

-- Create some basic extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext";

-- You can add initial table schemas here in the future
-- For now, we're keeping it minimal as requested

GRANT ALL PRIVILEGES ON DATABASE wave_dev TO wave_user;
