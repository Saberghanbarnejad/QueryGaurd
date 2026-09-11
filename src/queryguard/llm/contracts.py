from datetime import date
from typing import Annotated

from pydantic import BaseModel, StringConstraints


class GenerationRequest(BaseModel):
    schema_context: str
    data_as_of: date

    question: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
    ]
