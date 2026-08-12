# Phase 1, checkpoint 1 — PostgreSQL security foundation

## Goal

Run PostgreSQL 18.4 locally and prove the application roles are separated
before any ERP tables or seed data are introduced.

## Role boundaries

| Role | Login | Purpose | Allowed schema privileges |
| --- | --- | --- | --- |
| `queryguard_bootstrap` | Yes | Docker initialization only | Local superuser; never used by the API |
| `queryguard_owner` | Yes | Migrations and deterministic seeding | Owns `erp` and `audit` |
| `queryguard_runtime` | Yes | Generated business queries | `USAGE` on `erp`; future `SELECT` on ERP tables |
| `queryguard_audit` | Yes | Audit/history persistence | `USAGE` plus future `SELECT`, `INSERT`, `UPDATE` in `audit` |

The two runtime roles cannot create objects in `erp`, `audit`, or `public` and
cannot create temporary tables. Neither is a superuser, database creator, role
creator, replication role, or RLS-bypass role.

`default_transaction_read_only=on` is a defensive default for
`queryguard_runtime`, not the main security boundary. A client can change that
session setting, so the security test deliberately turns it off and proves that
PostgreSQL object permissions still reject `CREATE`.

## Start and verify

Run from the repository root with the Python virtual environment active.

1. Update `.env` with four unique local passwords. To generate each one on
   macOS, run `openssl rand -hex 24`.
2. Keep the passwords inside the three database URLs synchronized with the role
   password values.
3. Validate and start PostgreSQL:

   ```bash
   docker compose config --quiet
   docker compose up -d postgres
   docker compose ps
   ```

4. Export `.env` for the Python security test, then run it:

   ```bash
   set -a
   source .env
   set +a
   QUERYGUARD_RUN_DB_TESTS=1 pytest tests/security -v
   ```

5. Run all checks:

   ```bash
   ruff check .
   ruff format --check .
   mypy
   pytest
   ```

Expected database-test result: `10 passed`. The ordinary `pytest` command skips
the database-dependent file unless `QUERYGUARD_RUN_DB_TESTS=1` is explicitly
set.

## Important initialization behavior

Files in `/docker-entrypoint-initdb.d` run only when the PostgreSQL data volume
is empty. Editing `roles.sql` after the first successful startup does not
automatically reapply it.

During these early disposable-data checkpoints only, reset with:

```bash
docker compose down --volumes
docker compose up -d postgres
```

`--volumes` permanently deletes the local database volume. Do not use that
command after creating data you need to keep.

## Common errors

- `Set ... in .env`: a required password is missing or empty.
- Port `5432` already allocated: set `POSTGRES_PORT=5433` and update all three
  URLs to port `5433`.
- Security test cannot connect: wait for `docker compose ps` to show `healthy`.
- Password authentication failed after editing `.env`: the initialized volume
  still contains the old passwords; reset the disposable volume as shown above.
- `docker: command not found`: install and start Docker Desktop.

## Acceptance checklist

- [ ] `docker compose config --quiet` passes.
- [ ] PostgreSQL reports `healthy`.
- [ ] All 10 database security tests pass.
- [ ] Ruff, formatting, mypy, and ordinary pytest pass.
- [ ] You understand why the query and audit connections are separate.
- [ ] You understand that only the owner must create future schema objects.
- [ ] No real password or `.env` file is committed.
- [ ] `git status` shows only the intended checkpoint files before commit.

Suggested commit:

```text
feat(db): establish PostgreSQL role and schema boundaries
```

Next checkpoint: create the 12 ERP tables, constraints, and indexes as
`queryguard_owner`; do not seed them yet.
