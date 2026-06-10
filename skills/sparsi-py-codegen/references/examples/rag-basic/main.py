import asyncio
import os
import sys
from dagor import Builder, Engine
import sparsi.library

async def main():
    if not os.environ.get("GOOGLE_API_KEY"):
        print("Warning: GOOGLE_API_KEY not found. This example uses Gemini.")

    query = "What is the capital of France?"
    
    b = Builder("rag_workflow")
    
    # 1. Inject query
    b.vertex("input").op("ContextValOp").params({"key": "query"}).output("result", "q")
    
    # 2. Retrieve Documents
    b.vertex("retrieve").op("RetrieveOp").input("query", "q").output("results", "docs")
    
    # 3. Generate Answer
    # We'll use a simple prompt that asks the LLM to use citations
    b.vertex("answer").op("AIComputeOp").params({
        "model": "gemini-3.5-flash",
        "system": "You are a helpful assistant. Answer the user's question using the provided context. Cite your sources using [filename.md]."
    }).input("prompt", "q").output("result", "raw_answer")
    
    # 4. Validate Citations
    b.vertex("validate").op("ValidateCitationsOp").input("answer", "raw_answer").input("documents", "docs").output("validated_answer", "final_answer")
    
    graph = b.build()
    engine = Engine(graph)
    
    print(f"Running RAG for: {query}")
    await engine.run({"query": query})
    
    ans, _ = engine.get_output("final_answer")
    print(f"--- Results ---")
    print(ans)

if __name__ == "__main__":
    asyncio.run(main())
