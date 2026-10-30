from queryguard.llm.contracts import GenerationOutcome, GenerationRequest


class UnknownFakeQuestionError(Exception):
    """Raised when no response is configured for a question."""


class FakeGenerationProvider:
    def __init__(self, responses: dict[str, GenerationOutcome]):
        self._generate = None
        self._responses = responses.copy()

    async def generate(self, request: GenerationRequest) -> GenerationOutcome:
        question = request.question.strip().casefold()
        try:
            return self._responses[question]
        except KeyError as error:
            raise UnknownFakeQuestionError(
                "No response is configured for this question."
            ) from error
