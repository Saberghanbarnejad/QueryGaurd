\set ON_ERROR_STOP on

BEGIN;

-- Role names are fixed project identifiers. Only password values come from the
-- environment and psql quotes them as SQL literals via :'variable'.
SELECT 'CREATE ROLE queryguard_owner LOGIN'
WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'queryguard_owner')
\gexec

SELECT 'CREATE ROLE queryguard_runtime LOGIN'
WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'queryguard_runtime')
\gexec

SELECT 'CREATE ROLE queryguard_audit LOGIN'
WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'queryguard_audit')
\gexec

ALTER ROLE queryguard_owner
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS
    CONNECTION LIMIT 2;
ALTER ROLE queryguard_runtime
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS
    CONNECTION LIMIT 10;
ALTER ROLE queryguard_audit
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS
    CONNECTION LIMIT 5;

SELECT format('ALTER ROLE queryguard_owner PASSWORD %L', :'owner_password')
\gexec
SELECT format('ALTER ROLE queryguard_runtime PASSWORD %L', :'runtime_password')
\gexec
SELECT format('ALTER ROLE queryguard_audit PASSWORD %L', :'audit_password')
\gexec

-- PUBLIC receives CONNECT and TEMPORARY on new databases by default. Remove
-- both, then return CONNECT only to the three application roles.
REVOKE ALL ON DATABASE :"db_name" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"db_name"
    TO queryguard_owner, queryguard_runtime, queryguard_audit;

-- The public schema is excluded from every application search_path and no
-- application role may create objects there.
REVOKE ALL ON SCHEMA public FROM PUBLIC;

CREATE SCHEMA IF NOT EXISTS erp AUTHORIZATION queryguard_owner;
CREATE SCHEMA IF NOT EXISTS audit AUTHORIZATION queryguard_owner;
ALTER SCHEMA erp OWNER TO queryguard_owner;
ALTER SCHEMA audit OWNER TO queryguard_owner;

REVOKE ALL ON SCHEMA erp, audit FROM PUBLIC;
REVOKE ALL ON SCHEMA erp FROM queryguard_audit;
REVOKE ALL ON SCHEMA audit FROM queryguard_runtime;
GRANT USAGE ON SCHEMA erp TO queryguard_runtime;
GRANT USAGE ON SCHEMA audit TO queryguard_audit;

-- These grants are harmless while the schemas are empty and also make this
-- script safe to rerun after objects exist.
REVOKE ALL ON ALL TABLES IN SCHEMA erp FROM PUBLIC, queryguard_audit;
GRANT SELECT ON ALL TABLES IN SCHEMA erp TO queryguard_runtime;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA erp
    FROM PUBLIC, queryguard_runtime, queryguard_audit;

REVOKE ALL ON ALL TABLES IN SCHEMA audit FROM PUBLIC, queryguard_runtime;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA audit TO queryguard_audit;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA audit FROM PUBLIC, queryguard_runtime;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA audit TO queryguard_audit;

-- Future objects inherit the same boundary, but only when queryguard_owner
-- creates them. Phase 1 schema and seed commands must therefore use that role.
ALTER DEFAULT PRIVILEGES FOR ROLE queryguard_owner IN SCHEMA erp
    REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE queryguard_owner IN SCHEMA erp
    GRANT SELECT ON TABLES TO queryguard_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE queryguard_owner IN SCHEMA erp
    REVOKE ALL ON SEQUENCES FROM PUBLIC;

ALTER DEFAULT PRIVILEGES FOR ROLE queryguard_owner IN SCHEMA audit
    REVOKE ALL ON TABLES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE queryguard_owner IN SCHEMA audit
    GRANT SELECT, INSERT, UPDATE ON TABLES TO queryguard_audit;
ALTER DEFAULT PRIVILEGES FOR ROLE queryguard_owner IN SCHEMA audit
    REVOKE ALL ON SEQUENCES FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE queryguard_owner IN SCHEMA audit
    GRANT USAGE, SELECT ON SEQUENCES TO queryguard_audit;
ALTER DEFAULT PRIVILEGES FOR ROLE queryguard_owner
    REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

-- Session defaults reduce accidental misuse. Object privileges above remain
-- the real database-level security boundary because a client can change some
-- session settings.
ALTER ROLE queryguard_owner SET search_path = pg_catalog, erp, audit;
ALTER ROLE queryguard_runtime SET search_path = pg_catalog, erp;
ALTER ROLE queryguard_runtime SET default_transaction_read_only = on;
ALTER ROLE queryguard_runtime SET statement_timeout = '5s';
ALTER ROLE queryguard_runtime SET lock_timeout = '1s';
ALTER ROLE queryguard_runtime SET idle_in_transaction_session_timeout = '10s';
ALTER ROLE queryguard_runtime SET row_security = on;
ALTER ROLE queryguard_audit SET search_path = pg_catalog, audit;
ALTER ROLE queryguard_audit SET statement_timeout = '5s';
ALTER ROLE queryguard_audit SET lock_timeout = '1s';
ALTER ROLE queryguard_audit SET idle_in_transaction_session_timeout = '10s';

COMMIT;
