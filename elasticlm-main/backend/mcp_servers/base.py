import asyncio, sys
from contextlib import AsyncExitStack
from typing import Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from utils.logger import logger

class MCPServerProcess:
    """
    Spins up ANY stdio MCP server once and exposes a dynamic `.call()`.
    """
    def __init__(self, params: StdioServerParameters, tag: str = "mcp") -> None:
        self._params = params
        self._tag = tag
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None
        self._lock = asyncio.Lock()

    # ── lifecycle ────────────────────────────────────────────────
    async def start(self) -> None:
        if self._session:
            return
        self._stack = AsyncExitStack()
        r, w = await self._stack.enter_async_context(stdio_client(self._params))
        self._session = await self._stack.enter_async_context(ClientSession(r, w))
        await self._session.initialize()
        logger.info("🟢 %s ready", self._tag)

    async def stop(self) -> None:
        if self._stack:
            await self._stack.aclose()
            self._stack = self._session = None
            logger.info("🔴 %s stopped", self._tag)

    # ── dynamic dispatcher ───────────────────────────────────────
    async def call(self, tool: str, *, arguments: dict | None = None, **kwargs: Any):
        """
        Either
            await server.call("search", index="idx", queryBody=q)
        or
            await server.call("search", arguments={"index": "...", "queryBody": q})
        """
        if arguments is None:
            arguments = kwargs
        else:
            arguments |= kwargs                # merge; explicit kwargs win

        await self.start()
        async with self._lock:
            resp = await self._session.call_tool(tool, arguments=arguments)
        return resp.content
