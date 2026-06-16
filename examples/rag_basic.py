import asyncio
import os
import sys
import argparse
import structlog
from dagor import Builder, Engine, Reporter
from dagor.builtin import ContextValOp
import sparsi.library

async def run_workflow(query: str, verbose: bool):
    b = Builder("rag_workflow")
    
    # 1. Inject query
    b.vertex("input").op("ContextValOp").params({"key": "query"}).output("result", "q")
    
    # 2. Retrieve Documents
    b.vertex("retrieve").op("RetrieveOp").input("query", "q").output("results", "docs")
    
    # 3. Generate Answer
    b.vertex("answer").op("AIComputeOp").params({
        "model": "gemini-3.5-flash",
        "system": "You are a helpful assistant. Answer the user's question using the provided context. Cite your sources using [filename.md]."
    }).input("prompt", "q").output("result", "raw_answer")
    
    # 4. Validate Citations
    b.vertex("validate").op("ValidateCitationsOp").input("answer", "raw_answer").input("documents", "docs").output("validated_answer", "final_answer")
    
    graph = b.build()
    engine = Engine(graph, reporter=Reporter() if verbose else None)
    
    await engine.run({"query": query})
    return engine.get_output("final_answer")[0]

async def main():
    parser = argparse.ArgumentParser(description="Basic RAG example.")
    parser.add_argument("--query", default="What is the capital of France?", help="The query to ask.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    if not os.environ.get("GOOGLE_API_KEY"):
        print("Warning: GOOGLE_API_KEY not found. This example uses Gemini.")

    if args.verbose:
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(),
            ]
        )

    print(f"Running RAG for: {args.query}")
    try:
        ans = await run_workflow(args.query, args.verbose)
        print(f"\n--- Results ---")
        print(ans)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
