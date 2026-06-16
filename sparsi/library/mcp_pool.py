import asyncio
import structlog
from typing import Any, Dict, List, Optional, Tuple
from .mcp_client import MCPClient

logger = structlog.get_logger(__name__)

class MCPPoolEntry:
    def __init__(self, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        self.command = command
        self.args = args
        self.env = env or {}
        self.ready: List[MCPClient] = []
        self.lock = asyncio.Lock()
        self.target_n = 0
        self.inflight = 0

    async def replenish(self):
        async with self.lock:
            if len(self.ready) + self.inflight >= self.target_n:
                return
            self.inflight += 1
        
        try:
            client = MCPClient(self.command, self.args, self.env)
            await client.connect()
            async with self.lock:
                self.ready.append(client)
        except Exception as e:
            logger.warn("mcp_pool_replenish_failed", command=self.command, error=str(e))
        finally:
            async with self.lock:
                self.inflight -= 1

    async def pop(self) -> Optional[MCPClient]:
        async with self.lock:
            if not self.ready:
                return None
            return self.ready.pop()

class MCPPool:
    def __init__(self):
        self.entries: Dict[Tuple[str, str], MCPPoolEntry] = {}
        self.lock = asyncio.Lock()

    def _make_key(self, command: str, args: List[str]) -> Tuple[str, str]:
        return (command, " ".join(args))

    async def acquire(self, command: str, args: List[str], env: Optional[Dict[str, str]], pool_size: int) -> MCPClient:
        if pool_size <= 0:
            client = MCPClient(command, args, env)
            await client.connect()
            return client

        key = self._make_key(command, args)
        async with self.lock:
            if key not in self.entries:
                self.entries[key] = MCPPoolEntry(command, args, env)
            entry = self.entries[key]
            if pool_size > entry.target_n:
                entry.target_n = pool_size

        client = await entry.pop()
        # Top up in background
        asyncio.create_task(entry.replenish())
        
        if client:
            logger.debug("mcp_pool_hit", command=command)
            return client
        
        logger.debug("mcp_pool_miss", command=command)
        client = MCPClient(command, args, env)
        await client.connect()
        return client

    async def shutdown(self):
        async with self.lock:
            for entry in self.entries.values():
                async with entry.lock:
                    while entry.ready:
                        client = entry.ready.pop()
                        await client.disconnect()
            self.entries.clear()

global_mcp_pool = MCPPool()
