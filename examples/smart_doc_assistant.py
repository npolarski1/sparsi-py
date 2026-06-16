import asyncio
import os
import sys
import json
import argparse
import structlog
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from dagor import Builder, Engine, Operator, register_operator, Input, Output, Reporter
import dagor.builtin
import sparsi.library
from sparsi.library.rag_ops import Document

# --- Custom Operators ---

@register_operator("RetrievedDocsToContextOp")
class RetrievedDocsToContextOp(Operator, BaseModel):
    documents: Input = [] # List[Document]
    indices: Input = []   # List[int] from AIRerankOp
    context: Output = ""

    async def run(self, ctx: Any) -> None:
        docs = self.documents or []
        idxs = self.indices or list(range(len(docs)))
        
        parts = []
        for i in idxs:
            if 0 <= i < len(docs):
                d = docs[i]
                source_id = d.metadata.get("source", f"doc_{i}")
                parts.append(f"<document id=\"{source_id}\">\n{d.content}\n</document>")
        
        self.context = "\n\n".join(parts)

# --- Graph ---

def build_graph(verbose: bool):
    b = Builder("smart_doc_assistant")
    
    # 1. Inject query
    b.vertex("query_src").op("ContextValOp").params({"key": "query"}).output("result", "query_wire")
    
    # 2. Define categories
    b.vertex("categories_src").op("ConstOp").params({
        "value": ["api", "auth", "deployment", "troubleshooting"]
    }).output("result", "allowed_categories")
    
    # 3. Classify Query
    b.vertex("classify").op("AIClassifyMultiLabelOp").params({
        "model": "gemini-3.5-flash",
    }).input("input", "query_wire").input("categories", "allowed_categories").output("result", "detected_categories")
    
    # 4. Retrieve Documents with Filter
    b.vertex("retrieve").op("RetrieveWithFiltersOp").params({
        "k": 5
    }).input("query", "query_wire").input("filters", "detected_categories").output("results", "raw_docs")
    
    # 5. Rerank Documents
    b.vertex("rerank").op("AIRerankOp").params({
        "model": "gemini-3.5-flash"
    }).input("query", "query_wire").input("candidates", "raw_docs").output("result", "reranked_indices")
    
    # 6. Prepare Context
    b.vertex("prepare_context").op("RetrievedDocsToContextOp")\
        .input("documents", "raw_docs")\
        .input("indices", "reranked_indices")\
        .output("context", "formatted_context")
    
    # 7. Generate Answer
    b.vertex("answer").op("AIComputeOp").params({
        "model": "gemini-3.5-flash",
        "system": "You are a technical support assistant. Use the provided context to answer the user's question. Cite your sources using [id]."
    }).input("prompt", "query_wire").input("system", "formatted_context").output("result", "raw_answer")
    
    # 8. Validate Citations
    b.vertex("validate").op("ValidateCitationsOp")\
        .input("answer", "raw_answer")\
        .input("documents", "raw_docs")\
        .output("validated_answer", "final_answer")\
        .output("is_valid", "citations_valid")
    
    return b.build()

# --- Execution ---

async def main():
    parser = argparse.ArgumentParser(description="Smart Documentation Assistant.")
    parser.add_argument("--query", default="How do I configure authentication?", help="The user query.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    # Native support for GEMINI_API_KEY is handled in the library ops.
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        print("Error: Neither GEMINI_API_KEY nor GOOGLE_API_KEY found. This example requires Gemini.")
        sys.exit(1)

    if args.verbose:
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(),
            ]
        )

    graph = build_graph(args.verbose)
    engine = Engine(graph, reporter=Reporter() if args.verbose else None)

    print(f"Query: {args.query}")
    print("Running Documentation Assistant...")
    
    try:
        await engine.run({"query": args.query})
        
        answer, _ = engine.get_output("final_answer")
        valid, _ = engine.get_output("citations_valid")
        
        print("\n--- Answer ---")
        print(answer)
        print(f"\nCitations Valid: {valid}")
        
    except Exception as e:
        print(f"\nAssistant Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
