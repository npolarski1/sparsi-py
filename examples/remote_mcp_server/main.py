import asyncio
import os
import sys
import json
import argparse
import structlog
from typing import Any, List, Dict, Optional
from pydantic import BaseModel
from dagor import Builder, Engine, Operator, register_operator, Input, Output, Reporter
from dagor.builtin import ContextValOp
import sparsi.library # Registers standard ops

logger = structlog.get_logger(__name__)

# --- Custom Ops ---

@register_operator("MCPCloudflareDocsSearchOp")
class MCPCloudflareDocsSearchOp(Operator, BaseModel):
    input: Input = "" # Should be a dict or a SearchInput object
    result: Output = ""

    async def run(self, ctx: Any) -> None:
        # In a real implementation, this would use the MCP client to call the tool.
        # For the example, we'll wrap the library.MCPCallOp or implement similar logic.
        # Since we are using sparsi.library, we can use its MCP ops.
        pass

# --- Graph ---

def build_graph():
    b = Builder("mcp_cloudflare_docs_search")
    
    b.vertex("search_input").op("ContextValOp").params({"key": "query"}).output("result", "q")
    
    # We use the generic MCPCallOp from sparsi.library
    b.vertex("cf_search").op("MCPCallOp").params({
        "transport": "http",
        "url": "https://docs.mcp.cloudflare.com/mcp",
        "tool_name": "search_cloudflare_documentation",
        "init_timeout_ms": 30000,
        "call_timeout_ms": 60000,
    }).input("input", "q").output("result", "search_results")
    
    return b.build()

# --- Execution ---

async def run_workflow(query: str, verbose: bool):
    graph = build_graph()
    engine = Engine(graph, reporter=Reporter() if verbose else None)
    
    # Cloudflare tool expects {"query": "..."}
    await engine.run({"query": {"query": query}})
    
    results, _ = engine.get_output("search_results")
    return {
        "query": query,
        "results": results
    }

# --- Main ---

async def main():
    parser = argparse.ArgumentParser(description="Remote MCP Server Search (Cloudflare Docs).")
    parser.add_argument("--query", required=True, help="Search query for Cloudflare documentation")
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

    print(f"Searching Cloudflare docs for: {args.query}...")
    try:
        result = await run_workflow(args.query, args.verbose)
        print("\n--- Results ---")
        print(result["results"])
    except Exception as e:
        if args.verbose:
            logger.exception("workflow_failed")
        else:
            print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
