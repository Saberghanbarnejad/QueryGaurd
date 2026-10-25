from queryguard.llm.contracts import GenerationOutcome, GenerationRequest


class fake_generation_provider:
    def __init__(self, responses: dict[str, GenerationOutcome]):
        self._generate = None
        self._responses = responses.copy()
    
    async def generate(self, request: GenerationRequest) -> GenerationOutcome:
        question = request.question.strip().casefold()
        return self._responses[question]