import asyncio
import os
import sys
import json
import argparse
import structlog
from typing import Any, Dict, Optional
from pydantic import BaseModel
from dagor import Builder, Engine, Operator, register_operator, Input, Output, Reporter
from dagor.builtin import ContextValOp
import sparsi.library # Registers standard ops

logger = structlog.get_logger(__name__)

# --- Custom Ops ---

@register_operator("FormatFaithfulnessCheckOp")
class FormatFaithfulnessCheckOp(Operator, BaseModel):
    source: Input = ""
    summary: Input = ""
    query: Output = ""

    async def run(self, ctx: Any) -> None:
        self.query = f"Source document:\n{self.source}\n\nSummary to verify:\n{self.summary}"

# --- Graph ---

def build_graph():
    b = Builder("faithful_summary")
    
    # 1. Inject source
    b.vertex("source_const").op("ContextValOp").params({"key": "source"}).output("result", "source")
    
    # 2. Summarize with Gemini
    b.vertex("summarize").op("AIComputeStringToStringOp").params({
        "operation": "summarize this article in 3–5 concise sentences; include only information explicitly stated in the text, do not add context or draw inferences",
        "model": "gemini-3.5-flash",
    }).input("prompt", "source").output("result", "summary")
    
    # 3. Format for check
    b.vertex("format_check").op("FormatFaithfulnessCheckOp") \
        .input("source", "source") \
        .input("summary", "summary") \
        .output("query", "query")
    
    # 4. Verify with Gemini
    b.vertex("verify").op("AIBoolOp").params({
        "predicate": "does every factual claim in the summary appear in or follow directly from the source document, with no information added or invented?",
        "model": "gemini-3.5-flash",
    }).input("input", "query").output("result", "faithful")
    
    return b.build()

# --- Shared Execution ---

async def run_workflow(source_text: str, verbose: bool):
    graph = build_graph()
    engine = Engine(graph, reporter=Reporter() if verbose else None)
    
    await engine.run({"source": source_text})
    
    summary, _ = engine.get_output("summary")
    faithful, _ = engine.get_output("faithful")
    
    return {
        "source_length": len(source_text),
        "summary": summary,
        "faithful": faithful
    }

# --- Main ---

async def main():
    parser = argparse.ArgumentParser(description="Summarize and fact-check a document.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="path to a text file to summarize")
    group.add_argument("--text", help="inline source text to summarize")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(),
            ]
        )

    source = args.text
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            source = f.read()

    print(f"Running faithful-summary workflow...")
    try:
        result = await run_workflow(source, args.verbose)
        print("\n--- Workflow Result ---")
        print(json.dumps(result, indent=2))
    except Exception as e:
        if args.verbose:
            logger.error("workflow_failed", error=str(e))
        else:
            print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
