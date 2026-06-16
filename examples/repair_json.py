import asyncio
import os
import sys
import json
import argparse
import structlog
from typing import Any, Dict
from pydantic import BaseModel
from dagor import Builder, Engine, Operator, register_operator, Input, Output, Reporter
import dagor.builtin
import sparsi.library

# --- Custom Operator ---

@register_operator("CountKeysOp")
class CountKeysOp(Operator, BaseModel):
    data: Input = None
    count: Output = 0

    async def run(self, ctx: Any) -> None:
        if isinstance(self.data, dict):
            self.count = len(self.data)
        elif isinstance(self.data, list):
            self.count = len(self.data)
        else:
            self.count = 0

# --- Graph ---

def build_graph(verbose: bool):
    b = Builder("repair_json_workflow")
    
    # 1. Inject input
    b.vertex("raw_input").op("ContextValOp").params({"key": "json_str"}).output("result", "raw_wire")
    
    # 2. Parse with Repair
    # Note: We pass all params for the inner op directly to WithRepair
    b.vertex("parse_json").op("WithRepair").params({
        "inner_op_name": "JsonParseOp",
        "input_field": "json_str",
        "max_attempts": 3,
        "model": "gemini-3.5-flash",
        "prompt_prefix": "The following JSON is malformed. Please fix it and return ONLY the corrected JSON: "
    }).input("json_str", "raw_wire").output("result", "parsed_wire")
    
    # 3. Count keys
    b.vertex("count_keys").op("CountKeysOp").input("data", "parsed_wire").output("count", "count_wire")
    
    return b.build()

# --- Execution ---

async def main():
    parser = argparse.ArgumentParser(description="Repair broken JSON using AI.")
    parser.add_argument("--json", default='{"name": "sparsi", "broken": ', help="The (possibly broken) JSON string.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    if not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found. This example requires Gemini.")
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

    print(f"Input JSON: {args.json}")
    print("Running workflow...")
    
    try:
        await engine.run({"json_str": args.json})
        
        fixed, _ = engine.get_output("parsed_wire")
        count, _ = engine.get_output("count_wire")
        
        print("\n--- Results ---")
        print(f"Repaired JSON: {json.dumps(fixed)}")
        print(f"Top-level Key/Item Count: {count}")
    except Exception as e:
        print(f"\nWorkflow Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
