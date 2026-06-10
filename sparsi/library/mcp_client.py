import asyncio
import structlog
from typing import Any, Dict, List, Optional, Set
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = structlog.get_logger(__name__)

class MCPClient:
    def __init__(self, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        self.command = command
        self.args = args
        self.env = env or {}
        self.session: Optional[ClientSession] = None
        self._exit_stack = None
        self._client_context = None

    async def connect(self):
        params = StdioServerParameters(
            command=self.command,
            args=self.args,
            env=self.env
        )
        self._client_context = stdio_client(params)
        read, write = await self._client_context.__aenter__()
        self.session = ClientSession(read, write)
        await self.session.__aenter__()
        await self.session.initialize()
        logger.debug("mcp_connected", command=self.command)

    async def disconnect(self):
        if self.session:
            await self.session.__aexit__(None, None, None)
        if self._client_context:
            await self._client_context.__aexit__(None, None, None)
        logger.debug("mcp_disconnected", command=self.command)

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        if not self.session:
            await self.connect()
        
        response = await self.session.call_tool(name, arguments)
        return response.content
