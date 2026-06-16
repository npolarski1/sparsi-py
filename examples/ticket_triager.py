import asyncio
import os
import sys
import argparse
import structlog
from dagor import Builder, Engine, Reporter
from dagor.builtin import ContextValOp
import sparsi.library # Registers all ops

async def run_workflow(ticket_text: str, verbose: bool):
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
    engine = Engine(graph, reporter=Reporter() if verbose else None)
    
    await engine.run({"ticket": ticket_text})
    
    cat, _ = engine.get_output("category")
    pri, _ = engine.get_output("priority_val")
    
    return {
        "category": cat,
        "priority": pri
    }

async def main():
    parser = argparse.ArgumentParser(description="Ticket triager.")
    parser.add_argument("--ticket", default="My screen is flickering and I can't finish my report! It's urgent.", help="The ticket text.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("Warning: No AI API keys found. This example will likely fail unless mocked.")

    if args.verbose:
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(),
            ]
        )

    print(f"Running triager for: {args.ticket}")
    try:
        result = await run_workflow(args.ticket, args.verbose)
        print(f"\n--- Results ---")
        print(f"Category: {result['category']}")
        print(f"Priority: {result['priority']}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
