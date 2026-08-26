# Daily Activities Log

A day-wise development journal for the **AI Product CRM Multi-Agent** project.
Its purpose is to let any developer see *what changed, when, and why* without
digging through git history.

> **How to maintain this file:** add a new `## YYYY-MM-DD` section at the top of
> the log whenever you finish a meaningful chunk of work. Keep entries short:
> what changed, the key files, why, and how to verify. Newest day first.

**Stack:** Python 3.13 · LangGraph · LiteLLM (Ollama / Groq) · FAISS + BM25 · FlashRank · FastMCP · Pydantic Settings · LangSmith

**Flow:** `supervisor → (sql_agent | rag_agent) → synthesize`

---

## 2026-08-22 — MCP servers + logging/observability

Two efforts landed together in commit `25d0c8e` ("MCP Server Updated").

### 1. Observability / logging system
Replaced scattered `print()` / emoji debugging with a single, config-driven logger.
- **New** [`utils/logger.py`](utils/logger.py) — one `get_logger(__name__)` helper. On first
  use it configures logging once and automatically:
  - writes to a **dated file** `logs/crm_<YYYY-MM-DD>.log`,
  - **deletes log files older than `LOG_RETENTION_DAYS`** (startup sweep),
  - prints a clean aligned format `time | LEVEL | module | message` (optional console color).
- [`config.py`](config.py) + `.env` — new keys, nothing hardcoded:
  `LOG_LEVEL`, `LOG_DIR`, `LOG_RETENTION_DAYS`, `LOG_FILE_NAME`, `LOG_TO_CONSOLE`, `LOG_COLOR`.
- Converted prints → leveled logs across `nodes/*.py` and `utils/*.py`
  (INFO for flow, DEBUG for verbose dumps, WARNING/ERROR for the LLM fallback path).
- [`.gitignore`](.gitignore) — added `logs/`.

**Why:** production-grade apps need observable, self-maintaining logs, not `print` noise.
**Verify:** `python -m test_script.test_graph` → a `logs/crm_<today>.log` appears with clean
lines; back-date a `logs/crm_2000-01-01.log` and re-run to confirm the retention sweep deletes it.

### 2. MCP servers (tools exposed over FastMCP)
- **New** [`mcp_servers/sql_server.py`](mcp_servers/sql_server.py) — FastMCP server exposing
  `get_all_schemas` and `run_sql` tools over stdio.
- **New** [`mcp_servers/rag_server.py`](mcp_servers/rag_server.py) — FastMCP server exposing
  `search_docs` (hybrid retrieve + rerank).
- [`nodes/sql_agent.py`](nodes/sql_agent.py) — wired to call the SQL MCP server via a
  `fastmcp` `Client` + `StdioTransport`.

**Why:** move DB/RAG capabilities behind the MCP protocol so tools are reusable and decoupled.

### 🐞 Known issue — SQL MCP client fails with `McpError: Connection closed` (under fix)
Diagnosed 3 independent bugs in the SQL MCP client path (each hides the next):
1. [`nodes/sql_agent.py`](nodes/sql_agent.py) — `StdioTransport(command="python", ...)` launches
   the **system** Python (no `fastmcp`) → server dies on import. Fix: `command=sys.executable`.
2. [`mcp_servers/sql_server.py`](mcp_servers/sql_server.py) — run as a script, the project root
   isn't on `sys.path`, so `from config import settings` fails. Fix: prepend project root to
   `sys.path` (and pass `cwd=<project root>` in the transport so `.env` / `data/crm.db` resolve).
3. [`nodes/sql_agent.py`](nodes/sql_agent.py) — `result[0].text`; in fastmcp 3.4.7 `call_tool`
   returns a non-subscriptable `CallToolResult`. Fix: `result.data`.

**Status:** diagnosed and documented; fixes not yet applied. Fastest/cleanest option discussed
is an **in-memory** MCP client (`Client(mcp)`, no subprocess) wrapped in a small sync helper.

---

## 2026-08-21 — RAG quality upgrade

Commit `9a4c924` ("Update RAG"). Made retrieval hybrid and self-correcting.
- [`utils/vectorstore.py`](utils/vectorstore.py) — **hybrid retrieval**: FAISS (semantic, MMR)
  + BM25 (keyword) combined via `EnsembleRetriever` (50/50); document chunk caching.
- **New** [`utils/reranker.py`](utils/reranker.py) — FlashRank cross-encoder reranking of
  retrieved passages (`RERANKER_MODEL_NAME` from config).
- [`nodes/rag_agent.py`](nodes/rag_agent.py) — **relevance check + query-rephrase retry loop**
  (up to `MAX_RETRIES`): if retrieved context isn't relevant, rephrase and retry.
- [`config.py`](config.py) — reranker model setting.

**Why:** pure vector search missed keyword-exact matches; reranking + retries improve answer grounding.
**Verify:** `python -m test_script.test_rag`.

---

## 2026-08-18 — Initial multi-agent build

Commit `b306434` — first working version.
- **Graph** [`graph/build_graph.py`](graph/build_graph.py), [`graph/state.py`](graph/state.py) —
  LangGraph state machine routing `supervisor → sql_agent | rag_agent → synthesize`.
- **Nodes** — [`supervisor.py`](nodes/supervisor.py) (routes sql/rag/both),
  [`sql_agent.py`](nodes/sql_agent.py), [`rag_agent.py`](nodes/rag_agent.py),
  [`synthesize.py`](nodes/synthesize.py).
- **Utils** — [`llm.py`](utils/llm.py) (LiteLLM model-tier switching + fallback),
  [`db.py`](utils/db.py) (SQLite schema/query), [`vectorstore.py`](utils/vectorstore.py)
  (FAISS + Ollama embeddings), [`prompt_loader.py`](utils/prompt_loader.py).
- **Config** [`config.py`](config.py) — Pydantic `Settings` (env-driven, no hardcoding),
  model tiers (router/sql/rag/synthesize/fallback), LangSmith tracing.
- **Prompts** `prompts/*.yaml`; **data** `data/seed_db.py`, RAG docs + prebuilt FAISS store.
- **Tests** `test_script/*` (config, graph, rag, sql, supervisor, synthesize, langsmith).

**Why:** establish the end-to-end multi-agent CRM baseline.
**Verify:** `python -m test_script.test_config` then `python -m test_script.test_graph`
(requires Ollama running locally).
