from datetime import date
import pytest
from queryguard.llm.contracts import ClarificationOutcome, GenerationRequest
from queryguard.llm.fake import fake_generation_provider

async def test_generate_returns_configured_response() -> None:
    expected = ClarificationOutcome(
        status="clarification",
        clarification_question="Which year?",
        reason="The date range is unclear.",
        )
    provider = fake_generation_provider({"show recent orders":expected})
    request = GenerationRequest(
        question=" Show recent orders ",
        schema_context="Table: erp.sales_orders",
        data_as_of=date(2026, 6, 30),
    )
    actual = await provider.generate(request)
    assert actual == expected
    