# Phase 0 — Project foundation

Phase 0 fixes the MVP scope, Python 3.12 baseline, package boundaries, tooling,
and security workflow. It intentionally contains no database, API, LLM, SQL
validator, or UI implementation.

The execution lifecycle is:

1. Generate structured SQL without executing it.
2. Validate independently.
3. Store the proposal server-side.
4. Ask the user to confirm.
5. Retrieve and revalidate the stored proposal.
6. Execute with the read-only database role.
7. Record metadata and feedback with a separate audit role.

The synthetic dataset uses random seed `42` and snapshot date `2026-06-30`.
