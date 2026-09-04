# QueryGuard Mission Control

Last updated: 2026-09-04

QueryGuard is an Applied AI / LLM Engineering portfolio project. The roadmap is
organized around demonstrable AI-system capabilities rather than infrastructure
layers. Keep exactly one mission in `NOW`, no more than two detailed missions in
`NEXT`, and update this file only when a mission is completed, blocked, or
materially changed.

## NOW

### QG-M01 — Define structured generation outcomes

**Why it matters:** Provider-neutral structured outputs are the boundary
between nondeterministic models and deterministic application code.

- **Timebox:** 90 minutes.
- **First five minutes:** In the LLM package, create the module that will
  contain `GenerationRequest` and the three outcome variants.
- **Prerequisites:** Pydantic; no database, API key, or FastAPI application is
  required.
- **Learner-owned artifact:** Pydantic models, discriminated union, async
  provider protocol, and unit tests. Structured-output design is the learning
  objective.
- **Tutor-provided incidental work:** Import/package wiring or unrelated test
  configuration when explicitly requested.
- **Done:** Every valid variant parses; invalid discriminator, missing fields,
  extra fields, empty strings, and out-of-range confidence fail validation;
  strict mypy passes.
- **Stopping point:** Stop when the interface and focused tests are green. Do
  not create the FastAPI route or OpenAI adapter.
- **Resume sentence:** “Open the generation-contract tests, review the three
  valid examples, then implement `FakeGenerationProvider` in QG-M02.”
- **Suggested commit:** `feat(llm): define structured generation outcomes`
- **Unlock:** Explain in an interview how a discriminated provider-neutral
  contract isolates nondeterministic model output.

The internal interface is:

- `GenerationRequest`
  - `question`: stripped, nonempty, at most 2,000 characters.
  - `schema_context`: nonempty string.
  - `data_as_of`: date.
- `ProposalOutcome`
  - `status: Literal["proposal"]`
  - nonempty `sql` and `explanation`
  - `tables_used: list[str]`
  - `assumptions: list[str]`
  - `confidence`: 0 through 1
- `ClarificationOutcome`
  - `status: Literal["clarification"]`
  - nonempty `clarification_question` and `reason`
- `RejectionOutcome`
  - `status: Literal["rejection"]`
  - `code`: `unsupported_request`, `unsafe_request`, or
    `insufficient_context`
  - nonempty safe `message`
- `GenerationOutcome`: Pydantic discriminated union using `status`.
- `GenerationProvider.generate(request)`: async protocol returning
  `GenerationOutcome`.

All models forbid unexpected fields. Only proposal outcomes may contain SQL;
nullable fields are not used to represent different outcomes.

Verification:

```bash
pytest tests/unit -v
ruff check .
ruff format --check .
mypy
```

Avoid one nullable “everything model,” provider-specific SDK types in the
interface, execution methods on the provider, or SQL on clarification and
rejection outcomes.

## NEXT

### QG-M02 — Build a deterministic fake provider

**Why it matters:** A fake provider enables orchestration and evaluation work
without cost, flaky tests, or premature prompt tuning.

- **Timebox:** 90 minutes.
- **First five minutes:** Write a failing test in which a configured question
  must return a `ProposalOutcome`.
- **Prerequisites:** QG-M01 committed.
- **Learner-owned artifact:** Fake-provider behavior and tests.
- **Done:** The provider returns all three variants deterministically,
  normalizes harmless casing and whitespace, raises a dedicated error for an
  unknown input, and satisfies `GenerationProvider`.
- **Stopping point:** Stop when focused tests are green. Do not add a live
  model call.
- **Resume sentence:** “Use the fake provider as an injected dependency in the
  Safe Proposal service; do not import OpenAI.”
- **Suggested commit:** `test(llm): add deterministic fake generation provider`
- **Unlock:** A deterministic AI boundary suitable for the first API slice and
  evaluation runner.

The interface and scenarios are:

- Constructor accepts an immutable mapping of normalized questions to
  `GenerationOutcome`.
- Normalization is `strip().casefold()`.
- `generate()` returns the configured outcome asynchronously.
- An unknown question raises `UnknownFakeQuestionError`; it does not invent a
  fallback.
- “Show the top five customers by revenue” returns a proposal.
- “Show recent orders” returns a clarification.
- “Delete all customers” returns a rejection.

Verification:

```bash
pytest tests/unit -v
ruff check .
ruff format --check .
mypy
```

Do not encode production business logic in the fake, return dictionaries
instead of typed outcomes, silently default unknown questions, or couple the
fake to FastAPI.

## Demo roadmap

### 0. Fixture Runway — maintenance gate

Live-test and commit the existing ERP schema as a replaceable fixture. Fix only
acceptance blockers and configuration inconsistencies. Do not extend the
schema or build the former 106,267-row seed generator.

### 1. Safe Proposal Demo

`POST /queries/ask` accepts an English question. A deterministic fake provider
returns a typed proposal, clarification, or rejection. Proposal SQL passes an
independent SQLGlot policy before it is returned as validated; invalid SQL
becomes a safe rejection. Nothing is executed or persisted.

The first vertical slice is:

`question → fake provider → typed outcome → independent SQL validation → FastAPI response`

After QG-M02, reveal missions that:

1. Add a pure proposal service that calls `GenerationProvider`.
2. Validate proposal SQL with SQLGlot: exactly one PostgreSQL statement, a
   final/root `SELECT`, no DML/DDL/transaction/session control/`COPY`/`EXPLAIN`
   or locking, approved ERP tables only, and an outer limit no greater than
   500.
3. Convert validation failure into
   `RejectionOutcome(code="unsafe_request")`.
4. Expose `POST /queries/ask` with the fake provider injected.
5. Test proposal, clarification, rejection, invalid request, and unsafe SQL.

No database query, persistence, confirmation, or OpenAI request belongs in
this demo. Mark it `DEMO UNLOCKED` only after all five API outcome-path tests
pass.

### 2. Evaluation Demo

Create a versioned 15-case benchmark: six valid proposal cases, three
clarification cases, three unsafe cases, and three unsupported cases. Measure
outcome-type accuracy, structured-output validity, SQL-policy decisions, and
error categories. Produce machine-readable JSON plus a concise terminal
report. Publish no metric until the committed runner produces it.

### 3. Live Model Demo

Add an OpenAI Responses adapter behind the provider protocol using strict
JSON-schema Structured Outputs. Capture latency and reported token usage; map
refusal, incomplete response, timeout, rate limit, and invalid output to safe
application errors. Require explicit opt-in for live tests and keep execution
disabled.

### 4. Safe Execution Demo

Replace fixed schema context with PostgreSQL metadata inspection. Add only a
tiny deterministic fixture. Store canonical validated proposals server-side;
require confirmation, TTL validation, revalidation, and one-time read-only
execution with row, timeout, and plan-cost limits. Preserve audit-role
separation.

### 5. Feedback and Improvement Demo

Persist audit metadata and feedback, compare prompt/provider versions against
the benchmark, cluster failures, and make changes only when evaluation
supports them.

### 6. Portfolio Production Demo

Add the Streamlit client, Dockerized setup, CI, structured logging,
observability, screenshots, threat model, demo script, limitations, and a
measured evaluation report.

### 7. Real Database Onboarding — post-MVP

Connect a real or more complex database through metadata normalization and
configurable policies. Run the same evaluation before and after onboarding.
Focus on schema-context quality, safety regression, and integration
reliability—not schema construction.

## Completed missions

- Phase 0 project foundation — commit `ff88190`.
- Phase 1.1 PostgreSQL role and schema isolation — commit `2f4ea57`.
- QG-M00 fixture runway — `DONE`, commit `6688875`; Docker Compose validation,
  24 live database tests, Ruff, formatting, strict mypy, ordinary pytest, and
  `git diff --check` passed. No demo milestone was unlocked.

No demo milestone is unlocked yet.

## Blockers

- None.

## Parking lot

- Former 106,267-row deterministic synthetic dataset: canceled from the main
  path.
- Tiny deterministic data fixture: deferred to Safe Execution.
- Keyword and foreign-key-neighborhood schema selection: evaluate after the
  fixed-context baseline.
- Concurrency and load testing: defer until an I/O-bound API or evaluation
  workload makes them meaningful.
- Fine-tuning, RAG, agents, multiple providers, and multiple SQL dialects:
  excluded unless evaluation demonstrates a product need.

## Fifteen-minute restart mission

Use this whenever starting feels difficult:

1. **Minutes 0–2:** Open this file and read only `NOW`.
2. **Minutes 2–5:** Run the last focused test command from the previous
   handoff.
3. **Minutes 5–10:** Inspect only the learner-owned file and its test.
4. **Minutes 10–15:** Perform the first five-minute action or write one failing
   test.
5. End with: “The next smallest action is ___.”

This mission succeeds even if no production code is completed.

## Tutoring, notes, and quiz protocol

At session start, state the learning objective, learner-owned artifact,
permitted incidental help, and exact acceptance evidence. Ask two recall
questions: one recent and one from a weak topic.

For learner-owned work, help escalates through:

`guiding question → conceptual hint → pseudocode → focused snippet → full solution only when explicitly requested`

At session end, provide a sub-five-minute copyable handoff containing:

- Session ID and goal
- Concepts learned
- Change made
- Verification evidence
- Debugging or misconception lesson
- Design trade-off
- Weak topic
- Exact resume sentence

The separate notes chat converts the handoff into an Obsidian note and runs a
larger cumulative quiz every three sessions or at a demo milestone.

## Test and acceptance policy

- Contract and fake-provider tests require no Docker, database, network, or
  API key.
- Live OpenAI tests remain explicit opt-in.
- Each mission passes focused tests, Ruff, formatting, and strict mypy before
  commit.
- Security decisions use explicit reason codes, not raw parser/provider/database
  exceptions.
- No performance, cost, or quality metric becomes a portfolio claim until the
  committed evaluator measures it.
- Existing database work is preserved; the roadmap includes no destructive
  Git or Docker operation.
