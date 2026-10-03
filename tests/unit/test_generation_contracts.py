from datetime import date

import pytest
from pydantic import ValidationError

from queryguard.llm.contracts import (
    ClarificationOutcome,
    GenerationRequest,
    ProposalOutcome,
    RejectionOutcome,
)


def test_generation_request_rejects_whitespace_only_question() -> None:
    with pytest.raises(ValidationError):
        GenerationRequest(
            question="   ",
            schema_context="Table: erp.customers",
            data_as_of=date(2026, 6, 30),
        )


def test_generation_request_trims_question() -> None:
    request = GenerationRequest(
        question=" Show customers ",
        schema_context="Table: erp.customers",
        data_as_of=date(2026, 6, 30),
    )
    assert request.question == "Show customers"


def test_generation_request_rejects_question_over_limit() -> None:
    with pytest.raises(ValidationError):
        GenerationRequest(
            question="a" * 2001,
            schema_context="Table: erp.customers",
            data_as_of=date(2026, 6, 30),
        )


def test_generation_request_accepts_question_at_limit() -> None:
    request = GenerationRequest(
        question="a" * 2000,
        schema_context="Table: erp.customers",
        data_as_of=date(2026, 6, 30),
    )
    assert request.question == "a" * 2000


def test_generation_request_rejects_blank_schema_context() -> None:
    with pytest.raises(ValidationError):
        GenerationRequest(
            question="Show customers",
            schema_context="  ",
            data_as_of=date(2026, 6, 30),
        )


def test_generation_request_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        GenerationRequest.model_validate(
            {
                "question": "Show customers",
                "schema_context": "Table: erp.customers",
                "data_as_of": date(2026, 6, 30),
                "debug_mode": True,
            }
        )


def test_clarification_outcome_trims_question() -> None:
    outcome = ClarificationOutcome(
        status="clarification",
        clarification_question=" Which Year? ",
        reason="the requested date range is ambiguous",
    )

    assert outcome.clarification_question == "Which Year?"


def test_clarification_outcome_rejects_blank_question() -> None:
    with pytest.raises(ValidationError):
        ClarificationOutcome(
            status="clarification",
            clarification_question="   ",
            reason="the requested date range is ambiguous",
        )


def test_clarification_outcome_rejects_wrong_status() -> None:
    with pytest.raises(ValidationError):
        ClarificationOutcome.model_validate(
            {
                "status": "proposal",
                "clarification_question": "Which Year?",
                "reason": "the requested date range is ambiguous",
            }
        )


def test_clarification_outcome_rejects_blank_reason() -> None:
    with pytest.raises(ValidationError):
        ClarificationOutcome(
            status="clarification",
            clarification_question="Which Year?",
            reason="   ",
        )


def test_clarification_outcome_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ClarificationOutcome.model_validate(
            {
                "status": "clarification",
                "clarification_question": "Which Year?",
                "reason": "the requested date range is ambiguous",
                "sql": "SELECT * FROM erp.customers",
            }
        )


def test_rejection_outcome_trims_message() -> None:
    outcome = RejectionOutcome(
        status="rejection",
        code="unsafe_request",
        message="  Requests that modify data are not supported.   ",
    )
    assert outcome.message == "Requests that modify data are not supported."


def test_rejection_outcome_rejects_blank_message() -> None:
    with pytest.raises(ValidationError):
        RejectionOutcome(status="rejection", code="unsafe_request", message=" ")


def test_rejection_outcome_rejects_unknown_code() -> None:
    with pytest.raises(ValidationError):
        RejectionOutcome.model_validate(
            {
                "status": "rejection",
                "code": "random_code",
                "message": "This request cannot be fulfilled",
            }
        )


def test_proposal_outcome_accepts_valid_input() -> None:
    outcome = ProposalOutcome(
        status="proposal",
        sql="  SELECT customer_id FROM erp.customers LIMIT 5  ",
        explanation=" Return 5 customer IDs.   ",
        tables_used=["erp.customers"],
        assumptions=[],
        confidence=0.8,
    )
    assert outcome.sql == "SELECT customer_id FROM erp.customers LIMIT 5"
    assert outcome.explanation == "Return 5 customer IDs."
    assert outcome.tables_used == ["erp.customers"]
    assert outcome.confidence == 0.8
