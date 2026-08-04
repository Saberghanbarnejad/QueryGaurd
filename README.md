# QueryGuard

QueryGuard is a safe, explainable natural-language SQL explorer for a synthetic
PostgreSQL enterprise database. It will convert English business questions into
validated, read-only SQL, require confirmation before execution, and evaluate the
quality and safety of the generated queries.

> **Current status:** Phase 0 foundation only. QueryGuard does not yet connect to a
> database, call an LLM, validate SQL, or provide a user interface.

## Problem statement

General-purpose chat interfaces can propose SQL, but they do not by themselves provide
database permissions, independent AST validation, resource limits, execution approval,
audit history, or repeatable evaluation. QueryGuard adds those application-level controls
around model-generated SQL.

## MVP boundaries

The MVP targets PostgreSQL, one deterministic synthetic ERP dataset, English questions,
and read-only `SELECT` queries, including CTEs whose final operation is a `SELECT`.

The model may propose SQL but may never execute it. The backend will independently parse,
validate, limit, and execute approved SQL through a database role that cannot write to the
ERP schema. Ambiguous questions will produce clarification requests instead of guessed SQL.

See [the Phase 0 specification](docs/phase-0.md) for the finalized requirements and
security boundaries.

## Non-goals for the MVP

- Arbitrary production databases or SQL dialects
- React, Next.js, or a mobile client
- LangChain, LlamaIndex, vector databases, fine-tuning, or autonomous agents
- Multiple LLM providers implemented at once
- User accounts, OAuth, complex RBAC, microservices, Kubernetes, or cloud deployment
- Local model hosting, voice features, or automatic dashboard generation

## Planned architecture

- **FastAPI backend:** owns orchestration and all business logic.
- **PostgreSQL:** contains the synthetic ERP schema and a separate audit schema.
- **Read-only query connection:** inspects and queries only the approved ERP schema.
- **Audit connection:** writes only QueryGuard audit and feedback records.
- **LLM provider interface:** keeps the OpenAI Responses API implementation replaceable.
- **SQLGlot security layer:** parses PostgreSQL SQL and enforces query policies.
- **Streamlit client:** calls FastAPI and contains presentation logic only.
- **Evaluation runner:** compares normalized results and measures quality, safety, latency,
  token usage, and cost when available.

## Technology stack

- Python 3.12
- FastAPI and Pydantic 2
- PostgreSQL 18 and SQLAlchemy 2
- Psycopg 3 and SQLGlot
- OpenAI Python SDK with the Responses API and Structured Outputs
- Streamlit and HTTPX
- pytest, Ruff, and mypy
- Docker Compose (beginning in Phase 1)

## Repository layout

```text
queryguard/
├── src/queryguard/
│   ├── api/routes/          # FastAPI routers and boundary models
│   ├── core/                # Configuration, errors, and logging
│   ├── db/                  # Connections, inspection, execution, and audit
│   ├── llm/                 # Provider interface, prompts, and structured output
│   ├── security/            # AST validation, policies, and limits
│   └── services/            # End-to-end query orchestration
├── ui/                      # Streamlit presentation layer
├── database/                # Schema, roles, and deterministic seed generation
├── evaluation/              # Benchmark questions, gold queries, and metrics
├── tests/
│   ├── unit/
│   ├── integration/
│   └── security/
├── docs/
├── .env.example
├── pyproject.toml
└── README.md
```

## Prerequisites

- Git 2.40 or newer
- Python 3.12.x
- Docker Desktop or Docker Engine with Docker Compose v2 (needed in Phase 1)
- An OpenAI API key (not needed until Phase 3; never commit it)

PostgreSQL does not need to be installed directly because Phase 1 will run it in Docker.

## Phase 0 setup

Run these commands from the repository root.

### macOS or Linux

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

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
ruff check .
ruff format --check .
mypy
pytest
```

Do not add a real API key yet. The placeholder database passwords are for the future local
Docker environment and must be replaced before any non-local deployment.

## Development roadmap

1. PostgreSQL Compose service, ERP schema, roles, deterministic seed data, and permission tests
2. FastAPI foundation, configuration, schema inspection, read-only execution, and audit storage
3. OpenAI provider abstraction, Responses API Structured Outputs, prompts, and mocked tests
4. SQLGlot AST validation, query policies, limits, read-only transactions, and security tests
5. End-to-end generate, clarify, validate, confirm, execute, and audit workflow
6. Streamlit API client, result display, feedback, history, and CSV export
7. Evaluation benchmark, gold results, metrics, error analysis, and prompt iteration
8. Documentation, screenshots, demo plan, Dockerized setup, CI, review, and resume bullets

## Main features

_To be completed and documented as the implementation progresses._

## Setup and environment variables

_The Phase 0 local setup is above. Dockerized setup and a full variable reference will be
completed after the relevant configuration exists._

## Example questions

_To be added after the deterministic ERP dataset and business definitions are verified._

## API documentation

_To be added with the FastAPI implementation in Phase 2 and finalized in Phase 8._

## Security model

_The initial boundaries are recorded in `docs/phase-0.md`. A full threat model and tested
controls will be documented in `docs/security.md` during later phases._

## Evaluation approach and results

_The benchmark methodology will be implemented in Phase 7. No accuracy, latency, or cost
claims will be made before measured results exist._

## Screenshots

_To be added after the Streamlit workflow is complete._

## Known limitations

- This repository currently contains only the Phase 0 foundation.
- All planned security controls remain unimplemented until their named phases are complete.

## Future improvements

_Post-MVP improvements will be chosen only after the MVP is complete and evaluated._

## License

MIT

