from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints


class GenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_context: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1),
    ]
    data_as_of: date

    question: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
    ]


class ClarificationOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["clarification"]
    clarification_question: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1),
    ]
    reason: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1),
    ]
