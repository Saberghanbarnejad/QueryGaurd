# QueryGuard

QueryGuard is a safe, explainable natural-language SQL explorer for a synthetic
PostgreSQL ERP database. It is being built as a production-quality portfolio
project in controlled, verified checkpoints.

## Current status

Phase 1, checkpoint 1: PostgreSQL 18.4, isolated database roles, schema
boundaries, and executable permission tests. No ERP tables, API, LLM
integration, SQL validator, or UI exists yet.

## Why a dedicated application?

A general chatbot can propose SQL, but it does not by itself provide database
least privilege, AST validation, execution limits, confirmation, audit history,
or reproducible evaluation. QueryGuard will combine those controls around the
model rather than treating model instructions as a security boundary.

## Architecture

The planned application has an independent FastAPI backend and Streamlit
presentation layer. Generated SQL follows this lifecycle:

`generate → validate → confirm → revalidate → execute read-only → audit`

Database access is split across an owner/migration role, a strict ERP query
role, and a narrowly scoped audit writer. See
[`docs/phase-1-checkpoint-1.md`](docs/phase-1-checkpoint-1.md).

## Technology stack

- Python 3.12
- FastAPI and Pydantic 2
- PostgreSQL 18.4 and SQLAlchemy 2
- SQLGlot
- OpenAI Responses API with Structured Outputs (Phase 3)
- Streamlit (Phase 6)
- pytest, Ruff, and mypy
- Docker Compose

## Prerequisites

- Python 3.12.x
- Git 2.40+
- Docker Desktop or Docker Engine with Compose v2
- OpenAI API key beginning in Phase 3 only

## Setup

Run from the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example .env
```

Replace every `change-me` password in `.env`, then follow the
[Phase 1 checkpoint guide](docs/phase-1-checkpoint-1.md).

## Development checks

```bash
ruff check .
ruff format --check .
mypy
pytest
```

## Planned sections

The following sections will be completed as their implementation phases land:

- Main features and example questions
- API documentation
- Detailed security model and threat model
- Evaluation methodology and measured results
- Screenshots and demonstration
- Known limitations
- Future improvements

## License

MIT
