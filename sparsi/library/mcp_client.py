import asyncio
import structlog
from typing import Any, Dict, List, Optional, Set
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = structlog.get_logger(__name__)

class MCPClient:
    def __init__(
        self, 
        command: str = "", 
        args: List[str] = [], 
        env: Optional[Dict[str, str]] = None,
        url: str = "",
        headers: Optional[Dict[str, str]] = None
    ):
        self.command = command
        self.args = args
        self.env = env or {}
        self.url = url
        self.headers = headers or {}
        self.session: Optional[ClientSession] = None
        self._exit_stack = None
        self._client_context = None

    async def connect(self):
        if self.url:
            import logging
            # Silence the "Unknown SSE event: ping" noise from the mcp library
            class PingFilter(logging.Filter):
                def filter(self, record):
                    return "Unknown SSE event: ping" not in record.getMessage()
            
            logging.getLogger("mcp.client.sse").addFilter(PingFilter())
            logging.getLogger("mcp.client.streamable_http").addFilter(PingFilter())

            from mcp.client.sse import sse_client
            logger.debug("mcp_connecting_sse", url=self.url)
            self._client_context = sse_client(self.url, headers=self.headers)
        else:
            params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env
            )
            logger.debug("mcp_connecting_stdio", command=self.command)
            self._client_context = stdio_client(params)
        
        read, write = await self._client_context.__aenter__()
        self.session = ClientSession(read, write)
        await self.session.__aenter__()
        await self.session.initialize()
        logger.debug("mcp_connected", command=self.command if not self.url else self.url)

    async def disconnect(self):
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
            if self._client_context:
                await self._client_context.__aexit__(None, None, None)
        except RuntimeError as e:
            if "Attempted to exit cancel scope in a different task" in str(e):
                logger.debug("mcp_disconnect_task_mismatch", error=str(e))
            else:
                raise
        except Exception as e:
            logger.debug("mcp_disconnect_error", error=str(e))
            
        logger.debug("mcp_disconnected", command=self.command)

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        if not self.session:
            await self.connect()
        
        response = await self.session.call_tool(name, arguments)
        return response.content
