import asyncio
import json
import structlog
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
from dagor import Operator, register_operator, Input, Output, get_run_id
from .mcp_client import MCPClient
from .mcp_pool import global_mcp_pool

logger = structlog.get_logger(__name__)

@register_operator("MCPScriptOp")
class MCPScriptOp(Operator, BaseModel):
    command: str = ""
    args: List[str] = []
    url: str = ""
    headers: Dict[str, str] = {}
    tool_name: str = ""
    arguments: Input = {}
    pool_size: int = 0
    result: Output = None

    def setup(self, params: Dict[str, Any]) -> None:
        self.command = params.get("command", "")
        self.url = params.get("url", "")
        self.headers = params.get("headers", {})
        self.args = params.get("args", [])
        if isinstance(self.args, str):
            self.args = [a.strip() for s in self.args.split(",") for a in s.split() if a.strip()]
        
        self.tool_name = params.get("tool_name", "")
        self.pool_size = int(params.get("pool_size", 0))

    async def run(self, ctx: Any) -> None:
        if (not self.command and not self.url) or not self.tool_name:
            return

        client = await global_mcp_pool.acquire(
            command=self.command, 
            args=self.args, 
            env=None, 
            pool_size=self.pool_size,
            url=self.url,
            headers=self.headers
        )
        try:
            self.result = await client.call_tool(self.tool_name, self.arguments or {})
        finally:
            if self.pool_size <= 0:
                await client.disconnect()

@register_operator("MCPCallOp")
class MCPCallOp(Operator, BaseModel):
    """
    MCPCallOp: invoke a single MCP server tool as a DAG step.
    Similar to MCPScriptOp but follows the generic In/Out pattern of Go.
    """
    input: Input = None # Marshaled as arguments
    result: Output = None
    
    command: str = ""
    args: List[str] = []
    url: str = ""
    headers: Dict[str, str] = {}
    tool_name: str = ""
    pool_size: int = 0
    transport: str = "stdio"

    def setup(self, params: Dict[str, Any]) -> None:
        self.transport = params.get("transport", "stdio")
        self.command = params.get("command", "")
        self.url = params.get("url", "")
        self.headers = params.get("headers", {})
        self.args = params.get("args", [])
        if isinstance(self.args, str):
            self.args = [a.strip() for a in self.args.split(",") if a.strip()]
            
        self.tool_name = params.get("tool_name", "")
        self.pool_size = int(params.get("pool_size", 0))

    async def run(self, ctx: Any) -> None:
        if (not self.command and not self.url) or not self.tool_name:
            raise ValueError("MCPCallOp: command/url and tool_name are required")

        client = await global_mcp_pool.acquire(
            command=self.command, 
            args=self.args, 
            env=None, 
            pool_size=self.pool_size,
            url=self.url,
            headers=self.headers
        )
        try:
            # If input is a dict, use as-is, else wrap in a dict if needed or just pass
            args = self.input if isinstance(self.input, dict) else {"value": self.input}
            self.result = await client.call_tool(self.tool_name, args)
        finally:
            if self.pool_size <= 0:
                await client.disconnect()
