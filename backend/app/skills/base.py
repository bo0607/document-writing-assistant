from abc import ABC, abstractmethod
from typing import Any

from app.core.model_adapter import ModelAdapter
from app.core.result_assembler import ResultAssembler


class WritingSkill(ABC):
    name = "base"
    description = ""

    def __init__(self, model: ModelAdapter, assembler: ResultAssembler):
        self.model = model
        self.assembler = assembler

    @abstractmethod
    def execute(
        self, context: dict[str, Any], instruction: str | None = None
    ) -> dict[str, Any] | str:
        raise NotImplementedError

    def call_model(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str | None:
        response = self.model.complete(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if not response.success:
            return None
        return self.assembler.clean_text(response.content)

