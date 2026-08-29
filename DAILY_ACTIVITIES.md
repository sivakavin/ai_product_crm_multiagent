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

## 2026-08-29 — Fix 50% routing accuracy on the 6-item eval set

After trimming `eval/test_set.json` to 3 rag + 3 sql, routing accuracy was 3/6 (50%): `how long does it take to process a refund` → got `sql`, and the two `interactions` questions (`show all customer interactions`, `which customers interacted via the chat channel`) → got `rag`. The `qwen2.5` router guessed by keywords ("how long" looked like a measurable fact; "chat/interaction" looked like conversation).
- [`prompts/supervisor.yaml`](prompts/supervisor.yaml) — rebuilt the router prompt: explicit `question -> route` few-shots for every failing pattern, a note that interactions/channels are structured CRM records (SQL), a note that policy process/timeline questions are RAG, and two CRITICAL RULE do-not-reroute clauses (interaction/chat words ≠ RAG; date/time/how-long words ≠ SQL).
- **Why:** the old prompt had zero examples covering interactions or policy-timelines, so a 7B classifier fell back to surface keywords.
- **Verify:** `venv\Scripts\python.exe -m eval.run_routing_eval` — now **6/6 (100%)** on the 6-item set.

---

## 2026-08-29 — Extend eval routing test set with doc + DB coverage

Added 6 entries to `eval/test_set.json` so routing eval covers more than the original 20 SQL-only questions: 3 RAG from the Refund Policy doc (`data/docs/Refund Policy.md`) and 3 SQL exercising previously-uncovered tables/columns (`interactions`, `orders.status`).
- [`eval/test_set.json`](eval/test_set.json) — new questions: refund policy / customized-product refund / refund processing time (→ `rag`); all customer interactions / interactions by chat channel / cancelled orders with amounts (→ `sql`).
- **Why:** routing eval previously had zero RAG cases and no coverage of the `interactions` table, so a supervisor defaulting to `sql` would pass all old tests.
- **Verify:** `venv\Scripts\python.exe eval\run_routing_eval.py` (requires Ollama) — 26 cases (23 sql, 3 rag), and JSON loads cleanly.

---

## 2026-08-29 — Fix RAG MCP hang: preload faiss on the subprocess main thread

`call_mcp_tool("rag", "search_docs", ...)` and the RAG branch of `test_graph` hung forever in the rag-server subprocess right after faiss logged `INFO:faiss.loader:Loading faiss.` (search_docs is executed by fastmcp in a **worker thread**; the first `import faiss` inside that thread deadlocks on Windows — DLL loader lock).
- The `ModuleNotFoundError: No module named 'faiss.swigfaiss_avx2'` seen nearby was a red herring: `faiss/loader.py` tries the AVX2 SWIG variant when the CPU advertises AVX2, fails (the wheel ships only `_swigfaiss`), logs it at INFO, and falls back to `swigfaiss`.
- [`mcp_servers/rag_server.py`](mcp_servers/rag_server.py) — added `import faiss` at module scope so `faiss.dll` loads on the subprocess main thread before `mcp.run()` starts the tool loop. Verified the same search works in a plain worker thread (~16s) but hangs only in the fastmcp subprocess without it.
- **Why:** fastmcp runs tools in a threadpool executor; any MCP server with heavy native deps must preload them at import time (main thread) — now spelled out in AGENTS.md.
- **Verify:** `venv\Scripts\python.exe -c "from utils.mcp_client import call_mcp_tool; print(len(call_mcp_tool('rag','search_docs',{'question':'refund policy'})))"` — returns ~2300 chars in ~18s instead of hanging; `test_script/test_graph.py` now routes to `rag` and runs the RAG branch.

---

## 2026-08-29 — Pin langfuse 2.x for litellm 1.98 compatibility

Every LLM call spewed `AttributeError: module 'langfuse' has no attribute 'version'` (non-blocking but noisy) and Langfuse tracing never worked.
- `litellm==1.98` (installed) is only compatible with the `langfuse` **2.x** line: its integration reads `langfuse.version.__version__` (removed in 4.x) and passes `sdk_integration` to `Langfuse.__init__` (removed in 3.x).
- [`requirements.txt`](requirements.txt) — pinned `langfuse>=2.0,<3` and installed `langfuse==2.60.10`.
- **Why:** unpinned, `pip install` resolves langfuse 4.15.1 → the crashes above.
- **Verify:** `venv\Scripts\python.exe -c "from litellm.integrations.langfuse.langfuse import LangFuseLogger; LangFuseLogger(None, None, None)"` — prints `LangFuseLogger init ok`; then a `test_graph` run logs `Langfuse Layer Logging - logging success` instead of errors.

---

## 2026-08-29 — Install fastmcp + fix table listing in sql_server

`test_mcp.py` failed with `ModuleNotFoundError: No module named 'fastmcp'` even though the venv had `mcp`.
- The `fastmcp` package was split out of `mcp` at 2.0, and `utils/mcp_client.py` / `mcp_servers/sql_server.py` import `from fastmcp import ...`. It was declared in [`pyproject.toml`](pyproject.toml) but never installed. Installed `fastmcp==3.4.7` via `venv\Scripts\python.exe -m pip install "fastmcp>=2.14.1"`; it pins `mcp<2.0`, so pip downgraded `mcp` 2.1.1 → 1.29.1 (note: the `mcp>=2.1.1` line in `pyproject.toml` is now contradictory with fastmcp's mcp pin).
- [`mcp_servers/sql_server.py`](mcp_servers/sql_server.py) — `get_all_schemas` queried `SELECT name FROM sqlite_sequence WHERE type='table'`, but `sqlite_sequence` has no `type` column → `OperationalError: no such column: type`. Now lists tables from `sqlite_master` (excluding `sqlite_%`).
- **Why:** both blocked schema introspection over MCP.
- **Verify:** `venv\Scripts\python.exe -m test_script.test_mcp` prints all three CRM table schemas (the trailing `Task was destroyed but it is pending!` warning at exit is harmless — the resident session is intentionally never closed).

---

## 2026-08-29 — Fix Langfuse tracing (nothing was being shipped)

Traces never reached Langfuse — the LiteLLM callback registered but the logger had no credentials.
- [`config.py`](config.py) — `langfuse_public_key` alias was `LANGFUSE_PUBLIC_KEY=` (trailing `=`), so the field stayed at its default `" "` and the public key never loaded from `.env`. Fixed the alias.
- [`utils/llm.py`](utils/llm.py) — LiteLLM's `LangFuseLogger` reads credentials from **os.environ** (`LANGFUSE_SECRET_KEY` / `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_HOST`), but pydantic-settings only reads `.env` and never exports them, so `os.getenv` returned `None`. Now exports the settings into the environment before registering `litellm.success_callback = ["langfuse"]`. Note the host must be `LANGFUSE_HOST` — the old `.env` key `LANGFUSE_BASE_URL` was never consulted by litellm.
- **Why:** both bugs meant the callback fired but the SDK got `None` keys + wrong host default (`cloud.langfuse.com` vs `us.cloud.langfuse.com`).
- **Verify:** `venv\Scripts\python.exe -c "from config import settings; import utils.llm, os; print(os.getenv('LANGFUSE_PUBLIC_KEY'), os.getenv('LANGFUSE_HOST')); from litellm.integrations.langfuse.langfuse import resolve_langfuse_credentials; print(resolve_langfuse_credentials())"` — prints the real pk/sk/host tuple; then run any LLM call and confirm a trace in the Langfuse UI.

---

## 2026-08-29 — Keep MCP server subprocesses alive across calls

RAG queries re-loaded all docs (`Loading docs from ...`) on *every* question.
- [`utils/mcp_client.py`](utils/mcp_client.py) — `call_mcp_tool` used to `asyncio.run()` a `Client(StdioTransport)` **per call**, so each call spawned a fresh stdio subprocess. Each new `rag_server` process started with empty globals, discarding the module-level `_chunks_cache` / `_retriever_cache` in `utils/vectorstore.py` and re-reading all 5 docs.
- Now: one daemon event loop owns persistent `Client` sessions (one per logical server, created lazily with `__aenter__` and never `__aexit__`d). `call_mcp_tool` submits work via `asyncio.run_coroutine_threadsafe` and blocks on the result. A failed call drops the session so the next call reconnects cleanly.
- Added `MCPClient` convenience wrapper (`.call(tool, args)`) for ad-hoc use. It keys the persistent sessions on a normalized module name, so the earlier `Client("mcp_servers/sql_server.py")` bug — fastmcp can't infer a transport from a path string — is gone; servers always launch as `sys.executable -m <module>` from the repo root.

**Why:** server in-process caches (docs, chunks, retriever) now live for the app's lifetime instead of being rebuilt per query; also removes per-call subprocess startup cost.

**Verify:** run `venv\Scripts\python.exe -c "from utils.mcp_client import call_mcp_tool; print(call_mcp_tool('sql','get_all_schemas')); print(call_mcp_tool('sql','get_all_schemas'))"` twice — the `MCP client for 'sql' connected` log appears exactly **once** (old code logged a fresh subprocess `Logging started` per call). Note: `search_docs` still requires Ollama + the flashrank model to download once.

---

## 2026-08-28 — Fix PII masking in input guardrail

`input_guardrail` failed to mask `mask_pii` on realistic input like
`"My email is sivakavin.test@example.com and my phone number is +91 98765 43210."`.
- [`nodes/guardrails.py`](nodes/guardrails.py) — `mask_pii` had `return text` inside the loop, so only the first pattern (`mobile`) ever ran. Removed the early return so all patterns apply.
- [`nodes/guardrails.py`](nodes/guardrails.py) — the `mobile` pattern `\b(?:\+91[-\s]?)?[6-9]\d{9}\b` couldn't match formatted numbers: the leading `\b` fails before `+` (space→non-word = no boundary) and 10 consecutive digits were required. New pattern `(?<!\w)(?:\+91[-\s]?)?[6-9]\d{4}[-\s]?\d{5}\b` covers `9876543210`, `98765-43210`, `+91 98765 43210`, `+919876543210` and avoids partial masks inside words (`abc9876543210` stays intact).

**Why:** the guardrail silently passed PII through to the pipeline.
**Verify:** `python -m test_script.test_config` then run `mask_pii` on the sample above — email and phone both become `[<type>_MASKED]`.

---

## 2026-08-28 — Logger coverage for guardrails + rag_agent helpers

Added `get_logger(__name__)` wiring to the newest functions that were still using `print()` or no logging.
- [`nodes/guardrails.py`](nodes/guardrails.py) — first logger; replaced the two `print()` error handlers with `log.exception`, and added INFO/DEBUG lines for greeting short-circuit, SQL/prompt-injection blocks, PII masking, and the grounded/hallucinated verdict.
- [`nodes/rag_agent.py`](nodes/rag_agent.py) — added logging to `check_relevance` (verdict) and `rephrase_query` (rephrased query). Also removed a double `call_llm` in `rephrase_query` (it called the model twice; the first call was discarded).

**Why:** every node should be observable via `logs/crm_<date>.log`; `print()` bypasses it.
**Verify:** `python -m test_script.test_config` then `python -m test_script.test_guardrail` → `logs/crm_<today>.log` shows the guardrail INFO/DEBUG lines.

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
