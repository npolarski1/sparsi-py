import asyncio
import json
import argparse
from typing import Any, Callable, Dict, Optional, List
from mcp.server.stdio import stdio_server
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as types
from dagor import Builder, Engine

class MCPServer:
    def __init__(self, name: str, version: str = "0.1.0"):
        self.name = name
        self.version = version
        self.server = Server(name)
        self._tool_configs = {}

    def add_workflow_tool(self, name: str, description: str, builder_func: Callable[[], Builder], input_mapping: Dict[str, str], output_wire: str = "final_result"):
        """
        Maps an MCP tool call to a Sparsi DAG execution.
        
        Args:
            name: MCP tool name.
            description: Description shown to the client.
            builder_func: Factory function to create a fresh Builder instance.
            input_mapping: Map of {mcp_arg_name: context_val_key}.
            output_wire: The wire to return as the tool result.
        """
        self._tool_configs[name] = {
            "description": description,
            "builder_func": builder_func,
            "input_mapping": input_mapping,
            "output_wire": output_wire
        }

        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name=tool_name,
                    description=cfg["description"],
                    inputSchema={
                        "type": "object",
                        "properties": {
                            arg: {"type": "string"} for arg in cfg["input_mapping"].keys()
                        },
                        "required": list(cfg["input_mapping"].keys())
                    }
                )
                for tool_name, cfg in self._tool_configs.items()
            ]

        @self.server.call_tool()
        async def call_tool(tool_name: str, arguments: Dict[str, Any]) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            if tool_name not in self._tool_configs:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            cfg = self._tool_configs[tool_name]
            
            # Map arguments to context keys
            inputs = {}
            for arg_name, ctx_key in cfg["input_mapping"].items():
                inputs[ctx_key] = arguments.get(arg_name)
            
            # Run workflow
            builder = cfg["builder_func"]()
            graph = builder.build()
            engine = Engine(graph)
            
            await engine.run(inputs)
            
            res, ok = engine.get_output(cfg["output_wire"])
            if not ok:
                # If final_result not found, maybe try to find any output?
                # For now just return a warning
                return [types.TextContent(type="text", text=f"Error: Output wire '{cfg['output_wire']}' not found in graph.")]

            # Format result
            text_res = res if isinstance(res, str) else json.dumps(res, indent=2)
            return [types.TextContent(type="text", text=text_res)]

    async def run(self):
        async with stdio_server() as (read, write):
            await self.server.run(
                read,
                write,
                InitializationOptions(
                    server_name=self.name,
                    server_version=self.version,
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

def run_dual_mode(name: str, builder_func: Callable[[], Builder], input_mapping: Dict[str, str], output_wire: str = "final_result"):
    """
    Helper to run a workflow either as a CLI tool or as an MCP server.
    Usage:
        if __name__ == "__main__":
            run_dual_mode("my_tool", build_graph, {"query": "input_key"})
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--mcp", action="store_true", help="Run as MCP server")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    # Add CLI arguments dynamically based on input_mapping
    for arg in input_mapping.keys():
        parser.add_argument(f"--{arg}", required=False)
    
    args = parser.parse_args()

    if args.verbose:
        import structlog
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(),
            ]
        )

    if args.mcp:
        server = MCPServer(name)
        server.add_workflow_tool(name, f"Executes the {name} workflow", builder_func, input_mapping, output_wire)
        asyncio.run(server.run())
    else:
        # CLI Mode
        inputs = {}
        for arg, ctx_key in input_mapping.items():
            val = getattr(args, arg, None)
            if val is None:
                print(f"Error: --{arg} is required in CLI mode.")
                return
            inputs[ctx_key] = val
        
        async def run_cli():
            b = builder_func()
            g = b.build()
            
            from dagor import Reporter
            engine = Engine(g, reporter=Reporter() if args.verbose else None)
            await engine.run(inputs)
            res, _ = engine.get_output(output_wire)
            print(res)
            
        asyncio.run(run_cli())
