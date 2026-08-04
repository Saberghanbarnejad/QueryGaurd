# Phase 0 — Finalized MVP specification and foundation

Specification date: 2026-07-17

## 1. Product outcome

QueryGuard will accept an English business question about one synthetic ERP-style
PostgreSQL database and produce either:

1. a structured clarification request;
2. a safely rejected request with reasons; or
3. a visible, explained, validated SQL proposal that the user may explicitly confirm.

Confirmation authorizes only the stored proposal identified by its QueryGuard query ID.
The server must retrieve its canonical SQL, revalidate it immediately before execution,
and run it through the read-only query connection. The browser or Streamlit client cannot
submit replacement SQL through the confirmation action.

## 2. Supported MVP behavior

- PostgreSQL is the only SQL dialect and data source.
- Questions and clarification messages are English only.
- Version 1 schema retrieval sends the complete small ERP schema context to the model.
- Generated SQL is restricted to one `SELECT`, or `WITH`/CTEs whose final operation is a
  `SELECT`.
- Set operations and every statement class not explicitly permitted are rejected in the
  MVP. Support can be reconsidered only after benchmark evidence justifies it.
- Generated SQL, the schema context used, explanation, assumptions, confidence,
  validation result, and rejection reasons are visible to the user.
- Ambiguous or unsupported questions return no SQL and a focused clarification or
  unsupported-request response.
- Results include columns, rows, returned-row count, truncation state, and execution time.
- Streamlit supports CSV download, feedback, and audit-history viewing through FastAPI.
- All endpoint request and response bodies use Pydantic models and a consistent error
  envelope: `error.code`, `error.message`, optional safe `error.details`, and `request_id`.

## 3. Confirmation workflow

1. `POST /queries/ask` performs schema retrieval, generation, parsing, validation, limit
   enforcement, and audit creation. It never executes generated SQL.
2. The response contains a server-generated query ID and a pending proposal or a
   clarification/rejection outcome.
3. `POST /queries/{query_id}/execute` requires an explicit `confirmed: true` value.
4. The server loads the immutable canonical SQL associated with the query ID, verifies
   that the proposal is still pending and unexpired, and re-runs validation.
5. The server checks the estimated query-plan cost, opens a read-only transaction, applies
   a local statement timeout, executes through the read-only role, and records metadata.
6. A proposal can be executed once in the MVP. Regeneration produces a new query ID.

Lower-level generation and validation endpoints remain available for testing and API
demonstration, but the Streamlit client uses the orchestrated ask/confirm workflow.

## 4. Database and security boundaries

Three database roles resolve the different privilege needs:

- `queryguard_owner`: creates roles/schemas, applies schema changes, and runs deterministic
  seeding. Its credential is unavailable to the runtime API service.
- `queryguard_reader`: has connection, usage, metadata-inspection access needed by
  QueryGuard and `SELECT` on the approved `erp` schema only. It has no write or DDL
  privileges.
- `queryguard_audit_writer`: can read, insert, and update only the narrowly defined tables
  in `queryguard_audit`; it has no access to ERP table data.

Generated queries must pass all of these controls:

- Parse successfully with SQLGlot using the PostgreSQL dialect.
- Contain exactly one statement.
- Have an allowed root query form and a final `SELECT`.
- Contain no DML, DDL, `COPY`, procedural code, calls, grants, revocations, transaction
  control, session changes, or `EXPLAIN` supplied by the model.
- Contain no locking clause, including `SELECT ... FOR UPDATE`.
- Reference only approved ERP relations; generated references to `pg_catalog`,
  `information_schema`, temporary schemas, or unqualified unapproved relations fail.
- Use only the MVP function allowlist. File, network, sleep, lock, large-object, server
  configuration, and other side-effecting or exfiltration-capable functions are rejected.
- Have an outer result limit no greater than 500. The service produces and displays the
  canonical limited SQL; it does not silently execute a different hidden query.
- Pass an application-generated `EXPLAIN (FORMAT JSON)` estimated-plan-cost check. The
  threshold is configurable and will be calibrated against the seeded database in Phase 4.
- Execute with a 5-second transaction-local statement timeout and a read-only transaction.

AST approval is not treated as proof of complete safety. Database permissions, read-only
transactions, timeouts, row limits, plan-cost checks, schema isolation, and audit records
remain independent controls.

The LLM never receives passwords, connection strings, actual ERP rows, query results, or
raw database exceptions. Application logs must not contain secrets. Rejected SQL and safe
rejection reasons are retained in the audit schema.

## 5. Synthetic ERP dataset

The approved business schema is `erp`. It contains:

- `customers`
- `suppliers`
- `product_categories`
- `products`
- `warehouses`
- `inventory`
- `employees`
- `sales_orders`
- `sales_order_items`
- `purchase_orders`
- `purchase_order_items`
- `product_returns`

The Phase 1 seed target is deterministic with random seed `42` and these asserted row
counts:

- 1,000 customers
- 100 suppliers
- 12 product categories
- 500 products
- 5 warehouses
- 2,500 inventory records
- 150 employees
- 20,000 sales orders
- 60,000 sales-order items
- 5,000 purchase orders
- 15,000 purchase-order items
- 2,000 product returns

The synthetic dataset snapshot date is `2026-06-30`. Relative-date interpretation in the
demo and benchmark uses this configured date instead of the machine clock so results remain
reproducible. Prompts expose the snapshot date and require the model to state material date
assumptions.

All data is generated from local synthetic vocabularies. No employer, customer, or other
confidential data is permitted.

## 6. LLM boundary

The provider interface accepts the user question plus schema and business context and
returns a provider-neutral Pydantic model with:

- `sql: str | None`
- `explanation: str`
- `tables_used: list[str]`
- `assumptions: list[str]`
- `needs_clarification: bool`
- `clarification_question: str | None`
- `confidence: float` constrained to 0 through 1

The first provider uses the official OpenAI Python SDK, the Responses API, and native
Pydantic Structured Outputs. The model is configuration, not a constant spread through the
code. The initial local example uses `gpt-5.6-terra` as a cost/quality baseline; evaluation
will determine whether a different configured model or reasoning effort is justified.

The application validates provider output with Pydantic even when the SDK parses Structured
Outputs. Refusals, incomplete responses, timeouts, invalid provider payloads, and rate limits
map to safe application errors. The model has no SQL-execution tool.

## 7. Schema context

Version 1 includes every ERP table because the synthetic schema is bounded. Each table
entry contains its name, description, columns, PostgreSQL types, nullability, primary key,
foreign keys, and short reviewed business definitions.

The application inspector may query controlled metadata from PostgreSQL catalogs. This does
not grant generated SQL permission to query catalog schemas.

Version 2 will add deterministic keyword and foreign-key-neighborhood selection. Semantic
retrieval and vector databases remain post-MVP unless evaluation proves they are necessary.

## 8. Audit data

Audit records retain:

- query ID and timestamps;
- natural-language question;
- schema context identifiers;
- provider and configured model;
- proposed and canonical limited SQL;
- structured model explanation, assumptions, tables, clarification state, and confidence;
- validation outcome and safe reason codes;
- plan estimate, execution outcome, row count, truncation state, and latency;
- token usage and reported cost inputs when available; and
- user feedback.

Passwords, API keys, connection URLs, stack traces, and raw secret-bearing exception text are
never audit fields.

## 9. Evaluation standard

The target benchmark contains 50 manually reviewed cases spanning selection, filters,
sorting, aggregates, joins, dates, grouping, CTEs, comparisons, nulls, ambiguity,
unsupported requests, and unsafe requests.

Metrics include structured-output validity, SQL syntax validity, execution success,
normalized-result correctness, safety-rejection accuracy, clarification appropriateness,
latency, token usage, and cost when available. Correctness is not based on SQL-string
identity. Result comparison accounts for ordering requirements, column semantics, numeric
tolerances, and nulls.

Live-model tests require an explicit environment flag and are excluded from the default test
run. No portfolio or resume metric is reported until produced by the committed evaluation
runner against the committed benchmark.

## 10. Explicit MVP non-goals

React, Next.js, LangChain, LlamaIndex, multiple or autonomous agents, vector databases,
fine-tuning, Kubernetes, microservices, accounts, OAuth, cloud infrastructure, arbitrary
production databases, multiple dialects, local LLMs, voice, mobile apps, automatic
dashboards, and complex RBAC are excluded.

## 11. Verified dependency baseline

Direct dependencies are pinned in `pyproject.toml` to versions checked against official
documentation or maintainer-owned package metadata on 2026-07-17. Python 3.12 is pinned as
the project runtime even though newer supported Python releases exist, because it is the
requested baseline and is supported by all selected packages. PostgreSQL 18.4 is the Phase 1
container target; PostgreSQL 19 is still a beta and is excluded.

## 12. Phase 0 commands

Run all commands from the `queryguard` repository root.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example .env
ruff check .
ruff format --check .
mypy
pytest
```

On Windows PowerShell, use the equivalent commands in `README.md`.

Expected verification output includes successful Ruff and mypy checks and one passing unit
test. No database or LLM call occurs in Phase 0.

## 13. Common setup errors

- `python3.12: command not found`: install Python 3.12 or use `py -3.12` on Windows.
- PowerShell blocks activation: use `Set-ExecutionPolicy -Scope Process Bypass`, then activate
  the environment again.
- `pip` cannot build Psycopg: confirm Python is 64-bit and current, then retry; the selected
  binary extra normally avoids local compiler requirements.
- `docker: command not found`: install and start Docker Desktop before Phase 1.
- OpenAI authentication errors are not relevant yet; Phase 0 and the default tests make no
  OpenAI request.

## 14. Phase 0 acceptance checklist

- [ ] Repository exists on the `main` branch.
- [ ] Python reports version 3.12.x.
- [ ] `.venv` is active and direct dependencies install from `pyproject.toml`.
- [ ] `.env` was copied locally and remains ignored by Git.
- [ ] `ruff check .` passes.
- [ ] `ruff format --check .` passes.
- [ ] `mypy` passes.
- [ ] `pytest` reports one passed test.
- [ ] `git status --short` lists no `.env`, `.venv`, cache, or secret files.
- [ ] The reader/audit role split and confirmation workflow are understood.
- [ ] No database, LLM integration, validator, executor, or UI has been implemented early.

Recommended commit message:

```text
chore: initialize QueryGuard project foundation
```

## 15. Exact next step

Phase 1, checkpoint 1: add Docker Compose with PostgreSQL 18.4, implement only the database
roles and schema boundaries, and add permission smoke tests before creating ERP tables or
seed data.

