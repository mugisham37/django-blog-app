-- Database initialization script for development environment
-- This script sets up the initial database structure and users

-- Create additional databases for testing
CREATE DATABASE fullstack_blog_test;

-- Create read-only user for analytics
CREATE USER analytics_user WITH PASSWORD 'analytics_password';
GRANT CONNECT ON DATABASE fullstack_blog TO analytics_user;
GRANT USAGE ON SCHEMA public TO analytics_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO analytics_user;

-- Create backup user
CREATE USER backup_user WITH PASSWORD 'backup_password';
GRANT CONNECT ON DATABASE fullstack_blog TO backup_user;
GRANT USAGE ON SCHEMA public TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO backup_user;

-- Enable required extensions
\c fullstack_blog;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Create indexes for common search patterns
-- These will be created by Django migrations, but we can prepare the extensions

-- Set up full-text search configuration
CREATE TEXT SEARCH CONFIGURATION blog_search (COPY = english);

-- Performance optimizations
-- Increase shared_buffers and other settings are in postgresql.conf

-- Create a function for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Grant permissions to main user
GRANT ALL PRIVILEGES ON DATABASE fullstack_blog TO postgres;
GRANT ALL PRIVILEGES ON DATABASE fullstack_blog_test TO postgres;