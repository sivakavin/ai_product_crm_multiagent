# AI Product CRM — Multi-Agent System

A **production-ready**, provider-agnostic AI CRM assistant that answers customer questions by intelligently combining **structured database queries** (SQL) and **unstructured document retrieval** (RAG) through a multi-agent LangGraph pipeline.

Powered by **LiteLLM** — swap between **Ollama** (local), **Groq**, **OpenAI**, **Anthropic**, **Azure OpenAI**, **AWS Bedrock**, **Google Vertex AI**, or any of 100+ supported providers by changing a single `.env` variable. No code changes required.

Ask questions like _"What is the refund policy?"_ or _"Show me all pending orders for Rahul"_ — the system routes, retrieves, and synthesizes answers automatically.

---

## Table of Contents

1. [What It Is](#what-it-is)
2. [Key Features](#key-features)
3. [Architecture](#architecture)
4. [Technology Stack](#technology-stack)
5. [Prerequisites](#prerequisites)
6. [Installation](#installation)
7. [Configuration](#configuration)
8. [Data Setup](#data-setup)
9. [Running the Application](#running-the-application)
10. [How It Works — End to End](#how-it-works--end-to-end)
11. [Project Structure](#project-structure)
12. [API Reference](#api-reference)
13. [Evaluation](#evaluation)
14. [Troubleshooting](#troubleshooting)
15. [Delivery to Client](#delivery-to-client)

---

## What It Is

This system is a **conversational CRM agent** that sits on top of your customer database and policy documents. Users ask natural-language questions, and the AI:

- Queries the SQLite CRM database (customers, orders, interactions)
- Searches policy documents (refund policy, shipping policy, FAQs)
- Combines both sources into a single, coherent answer
- Filters out SQL injection, prompt injection, and PII leakage

It is designed for **customer support teams** who need fast, accurate answers from both structured and unstructured company data.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Provider-Agnostic** | Swap LLM providers (Ollama, Groq, OpenAI, Anthropic, etc.) via `.env` — zero code changes |
| **Per-Tier Model Config** | Each pipeline stage (router, SQL, RAG, synthesize, fallback) independently points to any model |
| **Smart Routing** | LLM-based supervisor decides whether a question needs SQL, RAG, or both |
| **SQL Agent** | Generates and executes SQLite queries from natural language |
| **RAG Agent** | Hybrid FAISS + BM25 retrieval with FlashRank reranking |
| **Answer Synthesis** | Merges database facts and document context into one answer |
| **Input Guardrails** | Blocks SQL injection, prompt injection; masks PII (Aadhaar, PAN, cards, etc.) |
| **Output Guardrail** | Detects hallucinated answers and replaces with a safe fallback |
| **Semantic Cache** | Caches similar questions (cosine similarity >= 0.85) for instant repeat answers |
| **Dual Interface** | Streamlit chat UI + FastAPI REST API |
| **Observability** | Langfuse tracing integration, structured logging with retention |
| **Graceful Fallback** | Automatic failover to fallback model if primary provider is down |

---

## Architecture

### Pipeline Flow

```
                        ┌─────────────────────┐
                        │     User Question    │
                        └─────────┬───────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │     Input Guardrail       │
                    │  • Greeting detection     │
                    │  • SQL injection block    │
                    │  • Prompt injection block │
                    │  • PII masking            │
                    └─────────┬────────────────┘
                              │
                              ▼
                    ┌──────────────────────────┐
                    │       Supervisor          │
                    │  LLM classifier:          │
                    │  sql | rag | both         │
                    └────┬─────────┬────────┬──┘
                         │         │        │
                    ┌────▼───┐ ┌──▼───┐ ┌──▼──────────┐
                    │  SQL   │ │ RAG  │ │ SQL → RAG   │
                    │ Agent  │ │Agent │ │  (both)      │
                    └────┬───┘ └──┬───┘ └──┬──────────┘
                         │        │        │
                         │        │        │
                         └────────┴───┬────┘
                                      │
                                      ▼
                          ┌──────────────────────┐
                          │     Synthesize        │
                          │  Merge SQL + RAG      │
                          │  into one answer      │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │   Output Guardrail    │
                          │  Groundedness check   │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │     Final Answer      │
                          └──────────────────────┘
```

### Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        LangGraph StateGraph                      │
│  State: { question, route, sql_result, rag_result, answer }      │
├──────────────┬───────────────────────────────────────────────────┤
│  Nodes       │  guardrails → supervisor → sql_agent / rag_agent  │
│              │              → synthesize → guardrails             │
├──────────────┼───────────────────────────────────────────────────┤
│  MCP Servers │  sql_server.py  (get_all_schemas, run_sql)        │
│              │  rag_server.py  (search_docs)                     │
├──────────────┼───────────────────────────────────────────────────┤
│  Data        │  SQLite DB (customers, orders, interactions)      │
│              │  FAISS + BM25 vectorstore (policy docs)           │
├──────────────┼───────────────────────────────────────────────────┤
│  LLM Layer   │  LiteLLM (unified interface to 100+ providers)    │
│              │  Per-tier model routing:                           │
│              │    router → groq/llama3-70b-8192                   │
│              │    sql    → openai/gpt-4o                          │
│              │    rag    → ollama/qwen2.5:7b                      │
│              │    synth  → anthropic/claude-sonnet-4-20250514     │
│              │    fallback → any provider                         │
├──────────────┼───────────────────────────────────────────────────┤
│  Interfaces  │  Streamlit chat UI (app/chat.py)                  │
│              │  FastAPI REST API  (app/main.py)                  │
└──────────────┴───────────────────────────────────────────────────┘
```

### Model Provider Architecture

```
                    ┌──────────────────────────┐
                    │       .env config          │
                    │  ROUTER_MODEL=groq/...     │
                    │  SQL_MODEL=openai/...      │
                    │  RAG_MODEL=ollama/...      │
                    └──────────┬───────────────┘
                               │
                               ▼
                    ┌──────────────────────────┐
                    │   config.py (Pydantic)    │
                    │  Settings reads .env      │
                    └──────────┬───────────────┘
                               │
                               ▼
                    ┌──────────────────────────┐
                    │   utils/llm.py            │
                    │   get_llm(tier)           │
                    │   call_llm(prompt, tier)  │
                    └──────────┬───────────────┘
                               │
                               ▼
                    ┌──────────────────────────┐
                    │       LiteLLM             │
                    │  litellm.completion(       │
                    │    model="groq/llama3"     │
                    │  )                         │
                    │                            │
                    │  Auto-routes to:           │
                    │  • Ollama (local)          │
                    │  • Groq (cloud)            │
                    │  • OpenAI (cloud)          │
                    │  • Anthropic (cloud)       │
                    │  • Azure / Bedrock / etc.  │
                    └────────────────────────────┘
```

Each tier is **independently swappable**. Mix and match providers per tier:

```env
ROUTER_MODEL=groq/llama3-70b-8192        # Fast routing on Groq
SQL_MODEL=openai/gpt-4o                  # Accurate SQL on OpenAI
RAG_MODEL=ollama/qwen2.5:7b              # Local RAG for cost saving
SYNTHESIZE_MODEL=anthropic/claude-sonnet-4-20250514  # Best synthesis
FALLBACK_MODEL=openai/gpt-4o-mini        # Cheap fallback
```

---

## Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Agent Framework** | LangGraph (LangChain) | Stateful multi-agent pipeline |
| **LLM Abstraction** | LiteLLM | Unified API for 100+ providers |
| **Supported Providers** | Ollama, Groq, OpenAI, Anthropic, Azure, Bedrock, Vertex, Mistral, Together, Deepseek, ... | Swap via `.env` — no code changes |
| **Database** | SQLite 3 | Lightweight, serverless |
| **Vector Store** | FAISS (CPU) | Fast local similarity search |
| **Sparse Retrieval** | BM25 (rank-bm25) | Keyword-based complement to FAISS |
| **Reranker** | FlashRank | Cross-encoder reranking |
| **Embeddings** | Provider-dependent | Ollama nomic-embed-text / OpenAI / etc. |
| **MCP Protocol** | FastMCP (stdio) | Tool-calling standard for SQL + RAG |
| **Chat UI** | Streamlit | Interactive chat interface |
| **REST API** | FastAPI + Uvicorn | Production-grade API server |
| **Observability** | Langfuse | Tracing + evaluation |
| **Language** | Python 3.13 | |

---

## Prerequisites

- **Python 3.13** (required — tested with this version only)
- **Windows 10/11**, macOS, or Linux (tested on Windows)
- **One LLM provider** — choose any:
  - **Ollama** (local, free) — [ollama.com](https://ollama.com) — requires 8 GB+ RAM
  - **Groq** (cloud, free tier) — [console.groq.com](https://console.groq.com) — API key required
  - **OpenAI** (cloud, paid) — [platform.openai.com](https://platform.openai.com) — API key required
  - **Anthropic** (cloud, paid) — [console.anthropic.com](https://console.anthropic.com) — API key required
  - Any [LiteLLM-supported provider](https://docs.litellm.ai/docs/providers)
- ~2 GB free disk space (dependencies + vector store)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ai_product_crm_multiagent.git
cd ai_product_crm_multiagent
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

**Activate it:**

```bash
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Your LLM Provider

Choose **one** provider and configure it in `.env` (see [Configuration](#configuration) section below).

**Option A — Ollama (local, free):**

```bash
# Install Ollama from https://ollama.com, then pull models:
ollama pull qwen2.5:latest
ollama pull llama3:latest
ollama pull nomic-embed-text
```

**Option B — Groq (cloud, free tier):**

```bash
# No local models needed — just set API key in .env:
# GROQ_API_KEY=gsk_...
# ROUTER_MODEL=groq/llama3-70b-8192
```

**Option C — OpenAI (cloud, paid):**

```bash
# No local models needed — just set API key in .env:
# OPENAI_API_KEY=sk-...
# ROUTER_MODEL=openai/gpt-4o
```

**Option D — Any other provider:**

Set the corresponding API key and model in `.env`. See [LiteLLM Providers](https://docs.litellm.ai/docs/providers) for the full list.

### 5. Verify Installation

```bash
venv\Scripts\python.exe -m test_script.test_config
```

This runs an **offline** config check. If it passes, installation is correct.

---

## Configuration

All configuration is managed through a single `.env` file in the project root.

### Create `.env` from the template below:

```env
# ── App ──────────────────────────────────────────
APP_ENV=local
LLM_PROVIDER=ollama

# ── Database ─────────────────────────────────────
DB_PATH=data/crm.db

# ── RAG Settings ─────────────────────────────────
VECTORSTORE_PATH=data/vectorstore
DOCS_PATH=data/docs
CHUNK_SIZE=300
CHUNK_OVERLAP=50
RETRIVER_K=10
RERANKER_MODEL_NAME=ms-marco-MiniLM-L-12-v2

# ── Embeddings (provider-specific) ───────────────
# Ollama:
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=nomic-embed-text
# OpenAI:  EMBEDDING_MODEL=openai/text-embedding-3-small
# Groq:    (embeddings run via Ollama locally, even when LLM calls use Groq)

# ── Model Tiers (LiteLLM format: provider/model) ─
# Each tier is INDEPENDENTLY configurable.
# Mix providers freely — e.g., Groq for speed, OpenAI for accuracy, Ollama for cost.
#
# Supported providers: ollama, groq, openai, anthropic, azure, bedrock,
#                      vertex_ai, mistral, together, deepseek, fireworks, ...
# Full list: https://docs.litellm.ai/docs/providers

ROUTER_MODEL=ollama/qwen2.5:latest
SQL_MODEL=ollama/qwen2.5:latest
RAG_MODEL=ollama/qwen2.5:latest
SYNTHESIZE_MODEL=ollama/llama3:latest
FALLBACK_MODEL=ollama/llama3:latest

# ── Provider API Keys (set only what you use) ────
GROQ_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
AZURE_API_KEY=
AZURE_API_BASE=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# ── Observability ────────────────────────────────
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com

# ── Logging ──────────────────────────────────────
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_RETENTION_DAYS=7
LOG_FILE_NAME=crm
LOG_TO_CONSOLE=true
LOG_COLOR=true

# ── MCP Servers ──────────────────────────────────
MCP_PYTHON=
MCP_SQL_SERVER=mcp_servers.sql_server
MCP_RAG_SERVER=mcp_servers.rag_server
```

### How Model Swapping Works

The system uses **LiteLLM** as a universal LLM gateway. Every LLM call goes through `utils/llm.py`:

```python
# utils/llm.py — simplified
import litellm

model_map = {
    "router":     settings.router_model,      # e.g., "groq/llama3-70b-8192"
    "sql":        settings.sql_model,          # e.g., "openai/gpt-4o"
    "rag":        settings.rag_model,          # e.g., "ollama/qwen2.5:7b"
    "synthesize": settings.synthesize_model,   # e.g., "anthropic/claude-sonnet-4-20250514"
    "fallback":   settings.fallback_model,     # e.g., "openai/gpt-4o-mini"
}

def call_llm(prompt, tier="router"):
    model = model_map.get(tier, settings.router_model)
    response = litellm.completion(model=model, messages=[...])
    return response.choices[0].message.content
```

Each pipeline stage (routing, SQL generation, RAG answering, synthesis) independently calls `call_llm()` with its own tier. **Change one `.env` line to swap a provider — zero code changes.**

### Provider Configuration Examples

**All-local (Ollama only — zero cost, no API keys):**

```env
ROUTER_MODEL=ollama/qwen2.5:latest
SQL_MODEL=ollama/qwen2.5:latest
RAG_MODEL=ollama/qwen2.5:latest
SYNTHESIZE_MODEL=ollama/llama3:latest
FALLBACK_MODEL=ollama/llama3:latest
```

**All-cloud (Groq — fast inference, free tier):**

```env
GROQ_API_KEY=gsk_your_key_here
ROUTER_MODEL=groq/llama3-70b-8192
SQL_MODEL=groq/llama3-70b-8192
RAG_MODEL=groq/llama3-70b-8192
SYNTHESIZE_MODEL=groq/llama3-70b-8192
FALLBACK_MODEL=groq/gemma2-9b-it
```

**Hybrid (Groq for speed + Ollama for cost-sensitive tiers):**

```env
GROQ_API_KEY=gsk_your_key_here
ROUTER_MODEL=groq/llama3-70b-8192
SQL_MODEL=groq/llama3-70b-8192
RAG_MODEL=ollama/qwen2.5:7b
SYNTHESIZE_MODEL=groq/llama3-70b-8192
FALLBACK_MODEL=ollama/llama3:latest
```

**Production (OpenAI + Anthropic mix):**

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
ROUTER_MODEL=openai/gpt-4o-mini
SQL_MODEL=openai/gpt-4o
RAG_MODEL=anthropic/claude-sonnet-4-20250514
SYNTHESIZE_MODEL=openai/gpt-4o
FALLBACK_MODEL=openai/gpt-4o-mini
```

### LiteLLM Model Format

All model values follow the LiteLLM convention: `provider/model-name`

| Provider | Format | Example |
|----------|--------|---------|
| Ollama | `ollama/model:tag` | `ollama/qwen2.5:latest` |
| Groq | `groq/model` | `groq/llama3-70b-8192` |
| OpenAI | `openai/model` | `openai/gpt-4o` |
| Anthropic | `anthropic/model` | `anthropic/claude-sonnet-4-20250514` |
| Azure OpenAI | `azure/model` | `azure/gpt-4o-deployment` |
| AWS Bedrock | `bedrock/model` | `bedrock/anthropic.claude-3-sonnet` |
| Google Vertex | `vertex_ai/model` | `vertex_ai/gemini-pro` |
| Mistral | `mistral/model` | `mistral/mistral-large-latest` |
| Together | `together/model` | `together/llama-3-70b-chat-hf` |
| Deepseek | `deepseek/model` | `deepseek/deepseek-chat` |

Full provider list: [docs.litellm.ai/docs/providers](https://docs.litellm.ai/docs/providers)

---

## Data Setup

### Create the CRM Database

```bash
venv\Scripts\python.exe data\seed_db.py
```

This creates `data/crm.db` with 3 tables and 30 sample records:

| Table | Rows | Description |
|-------|------|-------------|
| `customers` | 10 | Name, email, phone, city |
| `orders` | 10 | Order date, amount, status (pending/shipped/delivered/cancelled) |
| `interactions` | 10 | Channel (email/chat/phone/social), type, notes |

### Build the Vector Store

```bash
venv\Scripts\python.exe utils\vectorstore.py
```

This loads documents from `data/docs/`, chunks them, and builds the FAISS index at `data/vectorstore/`.

Source documents included:

| File | Format | Content |
|------|--------|---------|
| `Refund Policy.md` | Markdown | Refund eligibility, process, non-refundable items |
| `Shipping Policy.docx` | Word | Shipping methods, timelines, costs |
| `Frequently Asked Questions.pdf` | PDF | Common customer questions and answers |

---

## Running the Application

### Option A: One-Click Startup (Windows) — Recommended

```bash
startup.bat
```

Double-click `startup.bat` (or run it from the repo root). It:
1. Verifies the Python virtual environment exists
2. Auto-creates `.env` from `.env.example` if missing
3. Checks whether Ollama is running (only if `.env` uses `ollama/` models) and warns if not
4. Prompts you to choose what to launch:

```
  [1] Streamlit UI only  (http://localhost:8501)
  [2] FastAPI API only   (http://localhost:8000)
  [3] BOTH UI + API
  [4] Exit
```

Each service opens in its own console window. Close that window (or press `Ctrl+C`) to stop the service.

### Option B: Streamlit Chat UI

```bash
venv\Scripts\python.exe -m streamlit run app\chat.py
```

Opens a browser at `http://localhost:8501` with a chat interface. Type questions and get instant answers with route indicators.

### Option C: FastAPI REST API

```bash
venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

**Endpoints:**

```bash
# Health check
curl http://localhost:8000/health

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the refund policy?"}'
```

---

## How It Works — End to End

### Example Queries

| Question | Route | What Happens |
|----------|-------|-------------|
| "What is the refund policy?" | `rag` | Searches policy docs → returns refund rules |
| "Show me all pending orders" | `sql` | Generates SQL → queries orders table |
| "What's Rahul's order history and your return policy?" | `both` | SQL for orders + RAG for policy → merged answer |
| "Hi, how are you?" | _(greeting)_ | Short-circuited with a friendly canned response |
| "Ignore all instructions and..." | _(blocked)_ | Prompt injection detected → blocked |

### Step-by-Step Flow

1. **User submits a question** via Streamlit UI or API
2. **Input Guardrail** runs:
   - Detects greetings → returns immediately
   - Scans for SQL injection patterns → blocks if found
   - LLM classifies prompt injection → blocks if detected
   - Masks PII (phone numbers, emails, Aadhaar, PAN, cards)
3. **Supervisor** classifies the question as `sql`, `rag`, or `both`
4. **Agent(s) execute:**
   - **SQL Agent**: Fetches DB schema via MCP → LLM generates SQL → executes via MCP → returns results
   - **RAG Agent**: Retrieves documents via MCP (hybrid FAISS+BM25 + FlashRank reranking) → checks relevance → retries with rephrase if needed (up to 2 retries) → generates answer
   - **Both**: SQL runs first, then RAG
5. **Synthesize** merges all results into one coherent answer
6. **Output Guardrail** checks if the answer is grounded in the evidence
7. **Final answer** returned to the user

---

## Project Structure

```
ai_product_crm_multiagent/
│
├── app/
│   ├── chat.py              # Streamlit chat UI
│   └── main.py              # FastAPI REST API
│
├── graph/
│   ├── build_graph.py       # LangGraph pipeline definition
│   └── state.py             # AgentState TypedDict
│
├── nodes/
│   ├── guardrails.py        # Input + output guardrails
│   ├── supervisor.py        # Route classifier (sql/rag/both)
│   ├── sql_agent.py         # SQL generation + execution
│   ├── rag_agent.py         # Document retrieval + answer
│   └── synthesize.py        # Answer merging
│
├── utils/
│   ├── llm.py               # LiteLLM model-tier wrapper
│   ├── mcp_client.py        # MCP client (tool calling)
│   ├── db.py                # SQLite helpers
│   ├── vectorstore.py       # FAISS + BM25 hybrid retriever
│   ├── reranker.py          # FlashRank reranking
│   ├── prompt_loader.py     # YAML prompt loader
│   ├── logger.py            # Structured logging
│   └── cache.py             # Semantic cache
│
├── mcp_servers/
│   ├── sql_server.py        # FastMCP: get_all_schemas, run_sql
│   └── rag_server.py        # FastMCP: search_docs
│
├── prompts/
│   ├── supervisor.yaml      # Routing prompt
│   ├── sql_agent.yaml       # SQL generation prompt
│   ├── rag_agent.yaml       # RAG answer prompt
│   └── synthesize.yaml      # Synthesis prompt
│
├── data/
│   ├── crm.db               # SQLite CRM database
│   ├── seed_db.py           # Database seeder
│   ├── docs/                # RAG source documents
│   └── vectorstore/         # FAISS index
│
├── test_script/             # Test scripts
├── eval/                    # Evaluation sets + runners
├── logs/                    # Application logs
│
├── .env                     # Environment config (gitignored)
├── config.py                # Pydantic Settings class
├── requirements.txt         # Python dependencies
├── setup.bat / setup.sh     # One-click setup scripts
├── startup.bat              # One-click launch UI/API (Windows)
└── README.md                # This file
```

---

## API Reference

### `POST /query`

Send a question and get an AI-generated answer.

**Request:**

```json
{
  "question": "What is the refund policy?"
}
```

**Response:**

```json
{
  "question": "What is the refund policy?",
  "route": "rag",
  "answer": "Our refund policy allows returns within 30 days...",
  "cached": false
}
```

### `GET /health`

**Response:**

```json
{
  "status": "ok"
}
```

---

## Evaluation

### Routing Accuracy

```bash
venv\Scripts\python.exe -m eval.run_routing_eval
```

Runs 14 test questions through the supervisor and reports routing accuracy.

### RAG Quality (RAGAS)

```bash
venv\Scripts\python.exe -m eval.run_ragas_eval
```

Runs faithfulness evaluation on 3 test cases using the RAGAS framework.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'config'` | Run from the **repo root** — all commands must execute from the project root directory |
| `OllamaConnectionError` | Ensure Ollama is running: `ollama serve` in a separate terminal |
| `AuthenticationError` (Groq/OpenAI/Anthropic) | Check your API key in `.env` and ensure it's valid and has credits |
| `RateLimitError` | You've hit provider rate limits — switch tiers to a different provider or wait |
| `Model not found` | Verify model name matches provider format: `groq/llama3-70b-8192` not `llama3-70b-8192` |
| `No module named 'faiss'` | Run `pip install faiss-cpu` |
| App is slow on first query | Normal — first query loads models and builds the index |
| `call_mcp_tool not found` | Ensure `utils/mcp_client.py` contains the `call_mcp_tool` function |
| Logs not appearing | Check `logs/` directory exists and `.env` has `LOG_TO_CONSOLE=true` |
| Provider returns empty/wrong output | Check model name in `.env` — LiteLLM requires exact `provider/model` format |

---

## Delivery to Client

### Step 1: Determine Client's Deployment Model

| Model | Client Needs | Best For |
|-------|-------------|----------|
| **A. All-Local** | Python + Ollama, no internet required | On-premise, data-sensitive, zero recurring cost |
| **B. Cloud API** | Python + API key (Groq/OpenAI/etc.) | Quick setup, no GPU needed, pay-per-use |
| **C. Hybrid** | Python + Ollama + partial cloud key | Balance of cost and quality |

### Step 2: Prepare the Package

Create a clean distribution folder with only the files the client needs:

```
crm_ai_delivery/
├── app/                    # UI + API
├── graph/                  # Pipeline
├── nodes/                  # Agent nodes
├── utils/                  # Utilities
├── mcp_servers/            # MCP servers
├── prompts/                # Prompt templates
├── data/
│   ├── seed_db.py          # DB setup script
│   ├── docs/               # RAG source documents
│   └── vectorstore/        # Pre-built index (or rebuild instructions)
├── config.py               # Configuration
├── requirements.txt        # Dependencies
├── setup.bat               # One-click setup (Windows)
├── setup.sh                # One-click setup (macOS/Linux)
├── startup.bat             # One-click launch UI/API (Windows)
├── .env.example            # Template (without secrets)
└── README.md               # This document
```

**Exclude from delivery:**
- `.env` (contains secrets — provide `.env.example` instead)
- `venv/` and `.venv/` (recreated during installation)
- `logs/` (runtime artifact)
- `__pycache__/` and `*.egg-info/`
- `test_script/` and `eval/` (internal testing)
- `data/crm.db` (recreated with seed script)
- `AGENTS.md` and `DAILY_ACTIVITIES.md` (internal docs)

### Step 3: Client Machine Requirements

| Component | All-Local (A) | Cloud API (B) | Hybrid (C) |
|-----------|---------------|---------------|------------|
| Python 3.13 | Required | Required | Required |
| Ollama | Required | Not needed | Required |
| GPU/RAM | 8 GB+ RAM | No special hardware | 8 GB+ RAM |
| Internet | Not needed | Required for API | Partially |
| API Keys | None | 1 provider key | 1 provider key |
| Recurring Cost | Free | Pay-per-use | Partial |

### Step 4: Setup Scripts for Client

**`setup.bat` (Windows):**

```batch
@echo off
REM setup.bat — Run once on client machine (Windows)

echo ============================================
echo   AI Product CRM — Setup
echo ============================================

echo.
echo [1/5] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/5] Installing dependencies...
pip install -r requirements.txt

echo [3/5] Copying environment template...
if not exist .env (
    copy .env.example .env
    echo   Created .env from template — please edit with your API keys.
) else (
    echo   .env already exists — skipping.
)

echo [4/5] Creating database...
venv\Scripts\python.exe data\seed_db.py

echo [5/5] Building vector store...
venv\Scripts\python.exe utils\vectorstore.py

echo.
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo   Next steps:
echo   1. Edit .env with your provider settings
echo.
echo   To start the app (run ONE):
echo     Streamlit UI:  venv\Scripts\python.exe -m streamlit run app\chat.py
echo     REST API:      venv\Scripts\python.exe -m uvicorn app.main:app --reload
echo.
echo   If using Ollama locally, start it first:
echo     ollama serve
echo.
pause
```

**`setup.sh` (macOS/Linux):**

```bash
#!/bin/bash
# setup.sh — Run once on client machine

set -e

echo "============================================"
echo "  AI Product CRM — Setup"
echo "============================================"

echo ""
echo "[1/5] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[2/5] Installing dependencies..."
pip install -r requirements.txt

echo "[3/5] Copying environment template..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  Created .env from template — please edit with your API keys."
else
    echo "  .env already exists — skipping."
fi

echo "[4/5] Creating database..."
python data/seed_db.py

echo "[5/5] Building vector store..."
python utils/vectorstore.py

echo ""
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
echo "  Next steps:"
echo "  1. Edit .env with your provider settings"
echo ""
echo "  To start the app (run ONE):"
echo "    Streamlit UI:  venv/bin/python -m streamlit run app/chat.py"
echo "    REST API:      venv/bin/python -m uvicorn app.main:app --reload"
echo ""
echo "  If using Ollama locally, start it first:"
echo "    ollama serve"
```

### Step 5: Provide `.env.example`

```env
# ── App ──────────────────────────────────────────
APP_ENV=local
LLM_PROVIDER=ollama

# ── Database ─────────────────────────────────────
DB_PATH=data/crm.db

# ── RAG Settings ─────────────────────────────────
VECTORSTORE_PATH=data/vectorstore
DOCS_PATH=data/docs
CHUNK_SIZE=300
CHUNK_OVERLAP=50
RETRIVER_K=10
RERANKER_MODEL_NAME=ms-marco-MiniLM-L-12-v2

# ── Embeddings ───────────────────────────────────
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=nomic-embed-text

# ── Model Tiers (provider/model format) ──────────
# Swap any tier to any LiteLLM-supported provider.
# Providers: ollama, groq, openai, anthropic, azure, bedrock, vertex_ai, ...
# Full list: https://docs.litellm.ai/docs/providers
ROUTER_MODEL=ollama/qwen2.5:latest
SQL_MODEL=ollama/qwen2.5:latest
RAG_MODEL=ollama/qwen2.5:latest
SYNTHESIZE_MODEL=ollama/llama3:latest
FALLBACK_MODEL=ollama/llama3:latest

# ── Provider API Keys (set only what you use) ────
GROQ_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# ── Observability ────────────────────────────────
LANGFUSE_SECRET_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com

# ── Logging ──────────────────────────────────────
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_RETENTION_DAYS=7
LOG_FILE_NAME=crm
LOG_TO_CONSOLE=true
LOG_COLOR=true

# ── MCP Servers ──────────────────────────────────
MCP_PYTHON=
MCP_SQL_SERVER=mcp_servers.sql_server
MCP_RAG_SERVER=mcp_servers.rag_server
```

**Client instructions by deployment model:**

| Model | What client edits in `.env` |
|-------|---------------------------|
| **A. All-Local** | Nothing — defaults work with Ollama. Just `ollama serve` first. |
| **B. Cloud Groq** | Set `GROQ_API_KEY=...` and change model tiers to `groq/...` |
| **C. Cloud OpenAI** | Set `OPENAI_API_KEY=...` and change model tiers to `openai/...` |
| **D. Hybrid** | Set 1 API key + mix `ollama/...` and `groq/...` tiers as needed |

### Step 6: Delivery Checklist

**Pre-delivery (your side):**
- [ ] All source files packaged (no secrets, no venv, no logs)
- [ ] `.env.example` included (no `.env` with real keys)
- [ ] `setup.bat` + `setup.sh` included and tested
- [ ] `startup.bat` included and tested
- [ ] `data/seed_db.py` included for database recreation
- [ ] `data/docs/` includes all RAG source documents
- [ ] `requirements.txt` is up to date
- [ ] README.md covers their chosen deployment model

**Post-delivery (client side):**
- [ ] Python 3.13 installed
- [ ] Ollama installed (if All-Local or Hybrid model)
- [ ] `setup.bat` / `setup.sh` ran successfully
- [ ] `.env` configured with provider settings
- [ ] Ollama models pulled and verified (if applicable)
- [ ] Database seeded and vector store built
- [ ] Streamlit UI or FastAPI starts without errors
- [ ] Test query returns a valid answer
- [ ] Logs are writing to `logs/` directory

**Post-setup verification commands:**

```bash
# Offline config check (always works)
venv\Scripts\python.exe -m test_script.test_config

# Full graph test (requires LLM provider running)
venv\Scripts\python.exe -m test_script.test_graph

# One-click launch UI + API (Windows)
startup.bat

# Or start the UI directly
venv\Scripts\python.exe -m streamlit run app\chat.py
```

---

## License

Proprietary — For authorized use only.
