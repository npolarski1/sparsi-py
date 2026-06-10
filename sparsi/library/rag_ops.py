import asyncio
import re
import contextvars
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol
from pydantic import BaseModel
from dagor import Operator, register_operator, Input, Output

@dataclass
class Document:
    id: str
    content: str
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

# Metadata keys
METADATA_SOURCE = "source"
METADATA_SOURCE_URL = "source_url"
METADATA_HIGHLIGHTS = "highlights"
METADATA_UPDATED_AT = "updated_at"

class Retriever(Protocol):
    async def retrieve(self, ctx: Any, query: str, k: int) -> List[Document]:
        ...

_retriever_registry: Dict[str, Retriever] = {}
_default_retriever: Optional[Retriever] = None

def register_retriever(id: str, r: Retriever):
    _retriever_registry[id] = r

def set_default_retriever(r: Retriever):
    global _default_retriever
    _default_retriever = r

# contextvars for filters, mirroring WithRetrievalFilters in Go
_filters_var = contextvars.ContextVar("retrieval_filters", default=None)

def get_retrieval_filters() -> Optional[Dict[str, str]]:
    return _filters_var.get()

@register_operator("RetrieveOp")
class RetrieveOp(Operator, BaseModel):
    query: Input = ""
    k: int = 5
    retriever_id: str = ""
    results: Output = [] # List[Document]

    _retriever: Optional[Retriever] = None

    def setup(self, params: Dict[str, Any]) -> None:
        self.k = int(params.get("k", 5))
        self.retriever_id = params.get("retriever_id", "")
        
        # Resolve retriever at setup time
        rid = self.retriever_id
        if rid in _retriever_registry:
            self._retriever = _retriever_registry[rid]
        elif _default_retriever:
            self._retriever = _default_retriever
        else:
            # Don't raise yet, maybe it's registered later or we mock in run
            pass

    async def run(self, ctx: Any) -> None:
        if not self._retriever:
            # Fallback mock if no retriever registered (for examples)
            self.results = [
                Document(id="1", content=f"Information about {self.query}", metadata={METADATA_SOURCE: "doc1.md"}),
                Document(id="2", content=f"More details on {self.query}", metadata={METADATA_SOURCE: "doc2.md"})
            ]
            return

        self.results = await self._retriever.retrieve(ctx, self.query or "", self.k)

@register_operator("RetrieveWithFiltersOp")
class RetrieveWithFiltersOp(RetrieveOp):
    filters: Input = {} # Dict[str, str]

    async def run(self, ctx: Any) -> None:
        token = _filters_var.set(self.filters or {})
        try:
            await super().run(ctx)
        finally:
            _filters_var.reset(token)

@register_operator("ValidateCitationsOp")
class ValidateCitationsOp(Operator, BaseModel):
    answer: Input = ""
    documents: Input = [] # List[Document] or List[Dict]
    validated_answer: Output = ""
    is_valid: Output = True

    async def run(self, ctx: Any) -> None:
        if not self.answer or not self.documents:
            self.validated_answer = self.answer or ""
            return

        # Simple citation validation logic: 
        # Check if sources mentioned in [docX.md] actually exist in documents
        citations = re.findall(r'\[([^\]]+)\]', self.answer)
        
        valid_sources = set()
        for d in self.documents:
            if isinstance(d, Document):
                valid_sources.add(d.metadata.get(METADATA_SOURCE, ""))
            elif isinstance(d, dict):
                valid_sources.add(d.get("source") or d.get("metadata", {}).get("source", ""))
        
        invalid = [c for c in citations if c not in valid_sources and c != ""]
        if invalid:
            self.is_valid = False
            # Strip invalid citations or mark them
            self.validated_answer = self.answer + f"\n\n[Warning: Invalid citations: {', '.join(invalid)}]"
        else:
            self.validated_answer = self.answer
