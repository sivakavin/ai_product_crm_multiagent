# AGENTS.md

AI Product CRM Multi-Agent: a LangGraph pipeline (`input_guardrail -> supervisor -> (sql_agent | rag_agent) -> synthesize -> output_guardrail`, with `both` running sql then rag) over a SQLite CRM DB + hybrid FAISS/BM25 RAG, driven by LiteLLM model tiers (Ollama/Groq). SQL and RAG capabilities are exposed as FastMCP stdio servers. UI is a Streamlit chat app.

## Commands

Everything is run from the **repo root** with the venv interpreter:

```
venv\Scripts\python.exe -m test_script.test_config    # offline, fastest sanity check
venv\Scripts\python.exe -m test_script.test_graph     # end-to-end; requires Ollama
venv\Scripts\python.exe -m test_script.test_sql       # requires Ollama
venv\Scripts\python.exe -m test_script.test_rag       # requires Ollama
venv\Scripts\python.exe -m test_script.test_supervisor
venv\Scripts\python.exe -m test_script.test_synthesize
venv\Scripts\python.exe -m test_script.test_guardrail
venv\Scripts\python.exe -m test_script.test_langsmith
venv\Scripts\python.exe data\seed_db.py               # (re)create data/crm.db
venv\Scripts\python.exe utils\vectorstore.py          # rebuild FAISS index (slow)
venv\Scripts\python.exe -m streamlit run app\chat.py  # UI
```

- There is **no pytest and no linter/formatter** configured. `test_script/*` are plain scripts; import them as modules so repo-root imports resolve. Only `test_config` works without Ollama running.
- Default models: `qwen2.5:7b` (router) and `nomic-embed-text` (embeddings) must be pulled in Ollama.

## Architecture

- **Graph**: `graph/build_graph.py` (entry: `graph.build_graph.graph`), state typed in `graph/state.py` (`question`, `route`, `sql_result`, `rag_result`, `answer`).
- **Nodes**: `nodes/` — `supervisor.py` (routes sql/rag/both), `sql_agent.py`, `rag_agent.py`, `synthesize.py`, `guardrails.py`.
- **Utils**: `utils/llm.py` (LiteLLM tier + fallback), `utils/mcp_client.py`, `utils/db.py`, `utils/vectorstore.py`, `utils/reranker.py`, `utils/prompt_loader.py`, `utils/logger.py`.
- **MCP servers**: `mcp_servers/sql_server.py` (`get_all_schemas`, `run_sql`), `mcp_servers/rag_server.py` (`search_docs`). Agents call them only through `utils.mcp_client.call_mcp_tool(server, tool, args)`.
- **Prompts**: `prompts/*.yaml`, loaded by `prompt_loader.py` via a **relative path** — one more reason commands must run from repo root.
- **Config**: `config.py` is Pydantic `Settings` backed by `.env` (gitignored). `data/crm.db` and `data/vectorstore/` are also gitignored build artifacts; regenerate with the commands above.

## Gotchas

- **CWD matters.** Running any module from another directory breaks `from config import settings` (DB path, `.env`), prompt loading, and MCP subprocess launches.
- **MCP subprocesses** are spawned as `sys.executable -m <module>` with `cwd=project root` (`utils/mcp_client.py`). Never launch servers with bare `"python"` (system Python lacks `fastmcp` deps) and never `print()` to stdout in a server — stdout is the JSON-RPC channel; the logger deliberately writes to stderr only. Add new servers by registering the logical name in `_SERVERS` and setting `MCP_*_SERVER` in config.
- **Model tiers**: `utils/llm.py` maps `router / sql_writter / rag / synthesize / fallback`; an unknown tier silently uses the router model (no error). Note `nodes/sql_agent.py` passes `tier="sql_model"`, so it currently routes to the router model, not the intended SQL tier.
- **LangSmith tracing is half-wired**: `config.py` sets `LANGSMITH_*` env vars when tracing is on, but the `litellm.success_callback = ["langsmith"]` wiring in `utils/llm.py` compares `settings.langchain_tracing_v2 == "true"` (bool vs str → always falsy). Don't "simplify" this without fixing both sides.
- Graph node names are misspelled on purpose (`input_guardril`, `output_guardril`) and must match the edge-map keys in `build_graph.py`.
- **`import faiss` must not happen inside an MCP tool.** fastmcp runs tools in a worker thread; loading `faiss.dll` there deadlocks on Windows (loader-lock). `mcp_servers/rag_server.py` preloads `import faiss` at module scope (main thread). Any new MCP server with heavy native deps must do the same. Note faiss logs `No module named 'faiss.swigfaiss_avx2'` at INFO on AVX2 CPUs — that is normal fallback logging, not an error.
- Logs go to `logs/crm_<date>.log` via `utils/logger.py` (retention sweep, stderr console).

## Conventions

- **Keep `DAILY_ACTIVITIES.md` current**: append a new `## YYYY-MM-DD` section at the top, newest-first, with what changed, key files, why, and how to verify. Python 3.13 (`venv`).