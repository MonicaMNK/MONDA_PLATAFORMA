"""Interfaces del diseño PI7. La implementación corresponde a PI8–PI11."""
from typing import Protocol, Sequence

class EmbeddingClient(Protocol):
    async def embed(self, texts: Sequence[str], model: str, correlation_id: str) -> list[list[float]]: ...

class VectorStoreRepository(Protocol):
    async def search(self, vector: Sequence[float], course_id: str, active_content_ids: Sequence[str], k: int) -> list[dict]: ...

class LLMClient(Protocol):
    async def generate(self, prompt: str, source_ids: Sequence[str], correlation_id: str) -> dict: ...
