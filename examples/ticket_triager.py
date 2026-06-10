import asyncio
import os
import sys
from dagor import Builder, Engine
from dagor.builtin import ContextValOp
import sparsi.library # Registers all ops

async def main():
    if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("Warning: No AI API keys found. This example will likely fail unless mocked.")

    ticket_text = "My screen is flickering and I can't finish my report! It's urgent."
    
    b = Builder("ticket_triager")
    
    # 1. Inject input
    b.vertex("input").op("ContextValOp").params({"key": "ticket"}).output("result", "raw_ticket")
    
    # 2. Classify Category
    b.vertex("classify").op("AIComputeOp").params({
        "model": "gemini-3.5-flash",
        "system": "You are a ticket classifier. Categorize the ticket into: Hardware, Software, Network, or Access."
    }).input("prompt", "raw_ticket").output("result", "category")
    
    # 3. Extract Priority
    b.vertex("priority").op("AIComputeOp").params({
        "model": "gemini-3.5-flash",
        "system": "You are a priority extractor. Respond with ONLY one word: High, Medium, or Low."
    }).input("prompt", "raw_ticket").output("result", "priority_val")
    
    # 4. Format Output
    b.vertex("format").op("StringConcatOp").input("a", "category").input("b", "priority_val").output("result", "summary")
    
    graph = b.build()
    engine = Engine(graph)
    
    print(f"Running triager for: {ticket_text}")
    await engine.run({"ticket": ticket_text})
    
    cat, _ = engine.get_output("category")
    pri, _ = engine.get_output("priority_val")
    
    print(f"--- Results ---")
    print(f"Category: {cat}")
    print(f"Priority: {pri}")

if __name__ == "__main__":
    asyncio.run(main())
