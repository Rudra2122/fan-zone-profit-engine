"""Bridge to MongoDB's official MCP server (the partner integration).

All of the agent's data access goes through the Model Context Protocol: this
module spawns MongoDB's `mongodb-mcp-server` as a child process and talks to it
over stdio using the MCP Python SDK. The agent never touches the driver
directly at request time — it calls MCP tools (`find`, `insert-many`), which is
the "agent uses a partner's tools to accomplish a task" story the rubric wants.

Because Flask/agent code is synchronous, the async MCP session is hosted on a
dedicated event-loop thread for the lifetime of the process and reused across
requests (one node subprocess per worker). Sync callers get blocking
`find()` / `insert_many()` methods.

Env:
  MONGODB_URI        connection string (passed to the MCP server)
  MONGODB_MCP_CMD    command that launches the server (default: mongodb-mcp-server)
"""

import asyncio
import json
import os
import re
import threading
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

DB_NAME = "fanzone"

# MongoDB's MCP server wraps query results in these safety boundary tags; the
# JSON payload (an EJSON array) sits between them.
_BOUNDARY = re.compile(
    r"<untrusted-user-data-[0-9a-fA-F-]+>(.*?)</untrusted-user-data-[0-9a-fA-F-]+>",
    re.DOTALL,
)


class MCPUnavailableError(RuntimeError):
    """The MCP data layer is unavailable — server failed to start, or a tool
    call returned an error (e.g. MongoDB unreachable). Distinct from a genuine
    empty query result, so callers can return an honest 5xx instead of a 404."""


def _raise_on_error(result, op):
    """Raise if the MCP tool reported an error, so an infra failure isn't
    silently read as an empty result (which would masquerade as 'no match')."""
    if getattr(result, "isError", False):
        text = "\n".join((getattr(c, "text", "") or "") for c in result.content)
        raise MCPUnavailableError(f"MongoDB MCP '{op}' failed: {text[:400]}")


def _parse_docs(result):
    """Extract the document array from an MCP `find` tool result.

    The server emits the tag names inside its own warning prose (e.g.
    "...between the <tag> and </tag> boundaries..."), so a single non-greedy
    match can land on that filler. Scan every boundary block and return the
    first one that actually parses as a JSON array.
    """
    text = "\n".join((getattr(c, "text", "") or "") for c in result.content)
    for match in _BOUNDARY.finditer(text):
        payload = match.group(1).strip()
        if not payload.startswith("["):
            continue
        try:
            docs = json.loads(payload)
        except (ValueError, TypeError):
            continue
        if isinstance(docs, list):
            for d in docs:
                if isinstance(d, dict):
                    d.pop("_id", None)
            return docs
    return []


class _MCPBridge:
    def __init__(self):
        self._loop = None
        self._session = None
        self._stack = None
        self._lock = None  # asyncio.Lock, created on the loop thread
        self._ready = threading.Event()
        self._startup_lock = threading.Lock()
        self._start_error = None

    # -- lifecycle ---------------------------------------------------------
    def _ensure(self):
        if self._session is not None:
            return
        with self._startup_lock:
            if self._session is not None:
                return
            thread = threading.Thread(target=self._run, daemon=True)
            thread.start()
            self._ready.wait(timeout=90)
            if self._session is None:
                raise MCPUnavailableError(
                    f"MongoDB MCP bridge failed to start: {self._start_error}"
                )

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect())
        except Exception as exc:  # noqa: BLE001 — surface startup failure to caller
            self._start_error = repr(exc)
            self._ready.set()
            return
        self._loop.run_forever()

    async def _connect(self):
        uri = os.environ.get("MONGODB_URI")
        if not uri:
            raise RuntimeError("MONGODB_URI is not set")
        cmd = os.environ.get("MONGODB_MCP_CMD", "mongodb-mcp-server")
        # Pass the connection string as an explicit CLI arg (not only via
        # MDB_MCP_CONNECTION_STRING): on Cloud Run the env-var path did not
        # reach the server ("configured connection string is not valid"),
        # whereas the CLI arg is unambiguous. Keep the env var too as a fallback.
        params = StdioServerParameters(
            command=cmd,
            args=["--connectionString", uri],
            env={**os.environ, "MDB_MCP_CONNECTION_STRING": uri},
        )
        self._stack = AsyncExitStack()
        read, write = await self._stack.enter_async_context(stdio_client(params))
        session = await self._stack.enter_async_context(ClientSession(read, write))
        # Bound the handshake so a dead/broken server fails fast instead of
        # hanging startup. Publish self._session only after a successful
        # handshake — otherwise a failed init would look "started" to _ensure
        # and later calls would hang into a 500 instead of a clean 503.
        await asyncio.wait_for(session.initialize(), timeout=30)
        self._lock = asyncio.Lock()
        self._session = session
        self._ready.set()

    def _call(self, coro):
        self._ensure()
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=60)

    # -- async tool calls (run on the loop thread) -------------------------
    async def _afind(self, collection, filter, sort, limit, projection):
        args = {"database": DB_NAME, "collection": collection, "filter": filter or {}}
        if sort:
            args["sort"] = sort
        if limit is not None:
            args["limit"] = limit
        if projection:
            args["projection"] = projection
        async with self._lock:
            result = await self._session.call_tool("find", args)
        _raise_on_error(result, "find")
        return _parse_docs(result)

    async def _ainsert(self, collection, documents):
        async with self._lock:
            result = await self._session.call_tool(
                "insert-many",
                {"database": DB_NAME, "collection": collection, "documents": documents},
            )
        _raise_on_error(result, "insert-many")

    # -- sync public API ---------------------------------------------------
    def find(self, collection, filter=None, sort=None, limit=None, projection=None):
        return self._call(self._afind(collection, filter, sort, limit, projection))

    def insert_many(self, collection, documents):
        self._call(self._ainsert(collection, documents))


# Process-wide singleton.
bridge = _MCPBridge()
