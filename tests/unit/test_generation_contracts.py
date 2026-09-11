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
