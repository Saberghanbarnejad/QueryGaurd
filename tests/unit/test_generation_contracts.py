from datetime import date

import pytest
from pydantic import ValidationError

from queryguard.llm.contracts import GenerationRequest


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
