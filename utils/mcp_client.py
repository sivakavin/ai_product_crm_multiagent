"""Reusable MCP client — persistent stdio sessions, transport-decoupled.

Agents call `call_mcp_tool(server, tool, args)` (see AGENTS.md). `MCPClient` is
a convenience wrapper for ad-hoc use: construct with a server module
(`mcp_servers/sql_server.py` or `mcp_servers.sql_server`) and call `.call(...)`.

Each server runs as a single resident `sys.executable -m <module>` subprocess
per app lifetime, so its in-process caches (e.g. the RAG docs/retriever) survive
across calls instead of being rebuilt on every query. Spawning a fresh subprocess
per call (the old `async with Client(...)` per call) destroyed those caches.
"""

import os
import sys
import asyncio
import threading
from concurrent.futures import Future

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from config import settings
from utils.logger import get_logger

log = get_logger(__name__)

# Project root. Server subprocesses launch from here (cwd) so their
# `from config import settings` / `from utils... import ...` resolve.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Interpreter used to launch server subprocesses. Blank in config -> reuse the
# app's own interpreter (sys.executable), so servers run with identical deps.
# Never launch servers with bare "python" (see AGENTS.md).
_PYTHON = settings.mcp_python or sys.executable

# Server registry: logical name -> importable module (run via `python -m`).
# Unknown names are treated as module paths directly, so MCPClient can key on a
# module without registering it here.
_SERVERS = {
    "sql": settings.mcp_sql_server,
    "rag": settings.mcp_rag_server,
}


def _as_module(server_path: str) -> str:
    """Normalise 'mcp_servers/sql_server.py' -> 'mcp_servers.sql_server'."""
    module = server_path.strip()
    if module.endswith(".py"):
        module = module[:-3]
    return module.replace("/", ".").replace(os.sep, ".")


def _build_transport(server: str) -> StdioTransport:
    """The single seam for transport choice. To move a server to HTTP later,
    branch here (e.g. return a StreamableHttpTransport) — callers stay untouched."""
    module = _SERVERS.get(server, server)
    return StdioTransport(
        command=_PYTHON,
        args=["-m", module],
        cwd=PROJECT_ROOT,
    )


# --- Persistent sessions ----------------------------------------------------
# One daemon event loop owns one Client (and its subprocess) per server, kept
# alive across calls so the server's in-process caches persist.
_loop_lock = threading.Lock()
_loop: asyncio.AbstractEventLoop | None = None
_connect_lock = asyncio.Lock()
_clients: dict[str, Client] = {}


def _get_loop() -> asyncio.AbstractEventLoop:
    """Lazily start the single background event loop that owns all sessions."""
    global _loop
    if _loop is None:
        with _loop_lock:
            if _loop is None:
                loop = asyncio.new_event_loop()
                threading.Thread(
                    target=loop.run_forever,
                    name="mcp-client-loop",
                    daemon=True,
                ).start()
                _loop = loop
    return _loop


async def _ensure_client(server: str) -> Client:
    """Connect a server's session once and keep it connected indefinitely."""
    async with _connect_lock:
        client = _clients.get(server)
        if client is None:
            client = Client(_build_transport(server))
            await client.__aenter__()  # start session; never __aexit__ -> stays alive
            _clients[server] = client
            log.info("MCP client for %r connected (subprocess now resident)", server)
        return client


async def _drop_client(server: str) -> None:
    """Tear down a dead/poisoned session so the next call reconnects fresh."""
    async with _connect_lock:
        client = _clients.pop(server, None)
        if client is not None:
            try:
                await client.__aexit__(None, None, None)
            except Exception:
                log.debug("Ignoring error while closing MCP client for %r", server)


async def _acall(server: str, tool: str, args: dict) -> str:
    client = await _ensure_client(server)
    result = await client.call_tool(tool, args)
    if getattr(result, "is_error", False):
        raise RuntimeError(f"MCP tool {server}.{tool} failed: {result.data}")
    return result.data


def call_mcp_tool(server: str, tool: str, args: dict | None = None) -> str:
    """Run an MCP tool on a persistent server session and return its text output.

    Synchronous wrapper around the fastmcp client so LangGraph nodes can call it
    directly. The session (and its stdio subprocess) is created lazily on the
    first call and reused afterwards; a failed call invalidates the session so
    the next call reconnects.
    """
    args = args or {}
    log.debug("MCP -> %s.%s args=%s", server, tool, args)
    loop = _get_loop()
    future: Future = asyncio.run_coroutine_threadsafe(
        _acall(server, tool, args), loop
    )
    try:
        result = future.result()
    except BaseException:
        log.warning(
            "MCP %s.%s failed; dropping session so next call reconnects", server, tool
        )
        asyncio.run_coroutine_threadsafe(_drop_client(server), loop)
        raise
    log.debug("MCP <- %s.%s ok", server, tool)
    return result


class MCPClient:
    """Simple persistent MCP client: one server, call tools synchronously."""

    def __init__(self, server_path: str):
        self.server_module = _as_module(server_path)

    def call(self, tool_name: str, args: dict | None = None) -> str:
        """Sync wrapper. Any caller can use this."""
        return call_mcp_tool(self.server_module, tool_name, args)