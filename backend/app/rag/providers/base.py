from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class GenerationResult:
    text: str
    raw: Any = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class RAGProvider(ABC):
    name = "base"
    embedding_model = ""
    llm_model = ""

    @property
    def supports_embeddings(self) -> bool:
        return True

    @property
    def supports_generation(self) -> bool:
        return True

    @abstractmethod
    def embed(self, texts: list[str], task: str = "document") -> list[list[float]]:
        raise NotImplementedError

    @abstractmethod
    def generate(self, prompt: str) -> GenerationResult:
        raise NotImplementedError
