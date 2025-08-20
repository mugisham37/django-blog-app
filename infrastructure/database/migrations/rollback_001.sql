-- Rollback script for migration 001
-- This script reverses the initial schema migration

BEGIN;

-- Drop triggers first
DROP TRIGGER IF EXISTS audit_roles ON roles;
DROP TRIGGER IF EXISTS audit_users ON users;
DROP TRIGGER IF EXISTS update_roles_updated_at ON roles;
DROP TRIGGER IF EXISTS update_users_updated_at ON users;

-- Drop functions
DROP FUNCTION IF EXISTS audit.audit_trigger();
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS audit.audit_log;
DROP TABLE IF EXISTS user_roles;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;
DROP TABLE IF EXISTS schema_migrations;

-- Drop schema
DROP SCHEMA IF EXISTS audit CASCADE;

-- Drop extensions (be careful with this in production)
-- DROP EXTENSION IF EXISTS "pg_trgm";
-- DROP EXTENSION IF EXISTS "pg_stat_statements";
-- DROP EXTENSION IF EXISTS "uuid-ossp";

-- Remove migration record (if schema_migrations table still exists)
-- DELETE FROM schema_migrations WHERE version = '001';

COMMIT;