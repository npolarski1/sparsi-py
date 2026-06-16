import os
import asyncio
import structlog
from typing import Any, Dict, List, Optional, Protocol, Union
from pydantic import BaseModel
from dagor import Operator, register_operator, Input, Output
from google import genai
from google.genai import types

logger = structlog.get_logger(__name__)

class EmbeddingClient(Protocol):
    async def embed(self, ctx: Any, texts: List[str]) -> List[List[float]]:
        ...

class EmbeddingClientFactory(Protocol):
    async def embedder(self, ctx: Any, provider: str, model: str, ref: str) -> EmbeddingClient:
        ...

class GeminiEmbeddingClient:
    def __init__(self, client: genai.Client, model: str):
        self.client = client
        self.model = model

    async def embed(self, ctx: Any, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        # Chunks of 100
        batch_size = 100
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.client.models.embed_content(
                model=self.model,
                contents=batch,
            )
            for emb in response.embeddings:
                results.append(emb.values)
        return results

class EnvEmbeddingClientFactory:
    def __init__(self):
        self._clients: Dict[str, genai.Client] = {}

    async def embedder(self, ctx: Any, provider: str, model: str, ref: str) -> EmbeddingClient:
        if provider != "gemini":
            raise ValueError(f"EnvEmbeddingClientFactory only supports gemini, got {provider}")
        
        if ref not in self._clients:
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            self._clients[ref] = genai.Client(api_key=api_key)
            
        return GeminiEmbeddingClient(self._clients[ref], model)

_embedding_factory_registry: Dict[str, EmbeddingClientFactory] = {}
_default_embedding_factory: EmbeddingClientFactory = EnvEmbeddingClientFactory()

def register_embedding_factory(id: str, f: EmbeddingClientFactory):
    _embedding_factory_registry[id] = f

def set_default_embedding_factory(f: EmbeddingClientFactory):
    global _default_embedding_factory
    _default_embedding_factory = f

@register_operator("EmbeddingOp")
class EmbeddingOp(Operator, BaseModel):
    input: Input = None # str or List[str]
    model: str = "text-embedding-004"
    provider: str = "gemini"
    embeddings: Output = []

    async def run(self, ctx: Any) -> None:
        if not self.input:
            self.embeddings = []
            return
            
        texts = [self.input] if isinstance(self.input, str) else self.input
        
        factory = _default_embedding_factory
        client = await factory.embedder(ctx, self.provider, self.model, "")
        self.embeddings = await client.embed(ctx, texts)
