# LinkedIn AI Agent — Architecture

## What This Is

A personal AI agent that manages your LinkedIn presence end-to-end.
It reads your profile, learns your goals, tracks what works, and helps you
decide what to post, when to post it, and how to grow your career on LinkedIn.

Not a chatbot. Not a form. A stateful agent with tools, RAG-powered memory,
and multi-step reasoning built on LangGraph.

---

## Why LangGraph (not raw Claude tool use)

LangGraph is the industry standard for stateful agents. It handles:
- The agent loop cleanly (nodes, edges, conditional routing)
- Tool calling with proper error handling and retries
- State management across multi-step reasoning
- Conditional routing — agent decides whether to call tools or respond

Raw Claude tool use means rebuilding what LangGraph already does well.
For a project shown to recruiters, LangGraph is the more recognizable choice.

---

## Why RAG (not just PostgreSQL memory)

PostgreSQL stores structured facts (career goals, post history, analytics).
RAG stores *semantic knowledge* — what the agent retrieves based on meaning.

Two ChromaDB collections:
1. **`linkedin_knowledge`** — curated best practices for tech/AI engineers on LinkedIn (15 chunks, ingested at startup)
2. **`user_posts`** — your published posts embedded over time so the agent learns your voice and what works for your audience

---

## System Architecture (as built)

```
Next.js Frontend (localhost:3000)
    │
    │  HTTP via axios
    ▼
FastAPI Backend (localhost:8000)
    │
    ├── /auth/login          → LinkedIn OAuth redirect
    ├── /auth/callback       → exchange code, store user, redirect to frontend
    ├── /agent/chat          → runs the LangGraph agent
    ├── /posts/drafts        → list saved drafts
    ├── /posts/publish/{id}  → user-triggered publish to LinkedIn
    ├── /posts/schedule      → user-triggered schedule
    └── /profile/me          → live LinkedIn profile data
    │
    ▼
LangGraph Agent Graph
    │
    ├── [retrieve] node  → searches ChromaDB (linkedin_knowledge + user_posts)
    │                      injects top-k chunks into state
    ├── [agent] node     → Claude sonnet-4-6 reasons over messages + RAG context
    │                      + PostgreSQL memory (career goals, preferences)
    │                      decides: call tools OR respond
    ├── [tools] node     → executes tool calls, results appended to state
    └── loops back to [agent] until no more tool calls → END
    │
    ▼
Agent Tools (what Claude can call)
    ├── get_memory()              → loads user goals/prefs from PostgreSQL
    ├── save_memory(key, value)   → persists new context to PostgreSQL
    ├── get_linkedin_profile()    → fetches live profile via LinkedIn API
    ├── draft_post(topic, format) → RAG-informed post draft, saved as DB draft
    └── search_trends(query)      → Tavily web search [Phase 6]

User-controlled endpoints (NOT agent tools — user decides)
    ├── POST /posts/publish/{id}  → publishes a saved draft to LinkedIn
    └── POST /posts/schedule      → schedules a draft for future publishing
    │
    ▼
External Services
    ├── LinkedIn API    → profile read + post publishing
    ├── ChromaDB        → local vector store (./chroma_db on disk)
    ├── PostgreSQL      → structured data (Docker container)
    ├── OpenAI API      → text-embedding-3-small for embeddings
    ├── Anthropic API   → Claude sonnet-4-6 as agent brain
    └── Tavily API      → web search for trends [Phase 6]
```

---

## LangGraph State (as implemented)

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  # appends, never overwrites
    user_id: str        # authenticated user's UUID
    memory: dict        # loaded from PostgreSQL at start of every request
    retrieved_context: list[str]   # RAG chunks for current turn
```

**Key design decision:** `user_id` is injected into tools via `InjectedState` — Claude never sees or guesses it. This prevents the agent from hallucinating user IDs.

**Conversation history:** Last 10 turns loaded from `conversations` table on every request so the agent has full context without needing LangGraph checkpointing.

---

## RAG Pipeline (as implemented)

```
Startup:
  linkedin_best_practices.md
        ↓ chunk (500 chars, 50 overlap)
        ↓ embed (OpenAI text-embedding-3-small)
        ↓ store → ChromaDB "linkedin_knowledge" (15 chunks)

On every /agent/chat request:
  user message → embed → cosine similarity search
        ↓
  top 3 from "linkedin_knowledge" + top 2 from "user_posts"
        ↓
  injected into Claude's context before reasoning

On post publish:
  post content → embed → store in "user_posts"
  (agent learns your voice over time)
```

---

## Frontend (as built)

```
Next.js 16 + TypeScript + Tailwind CSS
Node.js 22 (via nvm)

Pages:
  /                   → Login page (LinkedIn OAuth button)
  /auth/callback      → Stores JWT token, redirects to /chat
  /chat               → Chat interface with the agent
  /drafts             → Review drafts, publish now or schedule
  /profile            → LinkedIn profile + AI audit

Auth flow:
  Frontend → /auth/login (backend) → LinkedIn → /auth/callback (backend)
  → redirect to frontend/auth/callback?token=JWT
  → token stored in localStorage
  → all API calls send token as query param

lib/api.ts — all backend calls in one place
```

---

## Database Schema (as implemented)

```sql
users               → LinkedIn identity + access token + profile picture
user_memory         → key/value store for agent's persistent memory
posts               → drafts / scheduled / published posts
analytics           → likes, comments, shares, impressions per post
conversations       → full chat history (role + content + tool_calls)
```

---

## Project Structure (as built)

```
linkedin-agent/
├── backend/
│   ├── main.py                     # FastAPI app + router registration
│   ├── config.py                   # Pydantic settings from .env
│   ├── agent/
│   │   ├── graph.py                # LangGraph graph (retrieve→agent→tools)
│   │   ├── state.py                # AgentState TypedDict
│   │   ├── prompts.py              # System prompt defining agent personality
│   │   ├── nodes/
│   │   │   ├── retrieve.py         # RAG retrieval node
│   │   │   ├── agent.py            # Claude reasoning node + tool binding
│   │   │   └── tools.py            # ToolNode (LangGraph prebuilt)
│   │   └── tools/
│   │       ├── memory_tools.py     # save_memory, get_memory
│   │       ├── linkedin_tools.py   # get_linkedin_profile
│   │       ├── content_tools.py    # draft_post
│   │       └── search_tools.py     # search_trends [Phase 6]
│   ├── rag/
│   │   ├── vector_store.py         # ChromaDB client + query helpers
│   │   ├── embeddings.py           # OpenAI embedding function
│   │   ├── ingestion.py            # Knowledge base loader + ingest_user_post()
│   │   └── knowledge/
│   │       └── linkedin_best_practices.md
│   ├── api/routes/
│   │   ├── auth.py                 # OAuth login + callback
│   │   ├── agent.py                # POST /agent/chat
│   │   ├── posts.py                # drafts, publish, schedule, published
│   │   └── profile.py              # GET /profile/me
│   ├── linkedin/
│   │   ├── auth.py                 # OAuth URL generation + token exchange
│   │   └── client.py               # LinkedIn API wrapper
│   └── db/
│       ├── database.py             # SQLAlchemy engine + session
│       ├── models.py               # All DB models
│       └── crud.py                 # DB operations
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx              # Root layout (dark theme)
│   │   ├── page.tsx                # Login page
│   │   ├── auth/callback/page.tsx  # Token handler
│   │   ├── chat/page.tsx           # Agent chat UI
│   │   ├── drafts/page.tsx         # Draft review + publish/schedule
│   │   └── profile/page.tsx        # Profile + AI audit
│   ├── lib/
│   │   └── api.ts                  # All backend API calls
│   └── .env.local                  # NEXT_PUBLIC_API_URL
│
├── docker-compose.yml              # PostgreSQL only (backend runs locally)
├── pyproject.toml                  # Python deps managed by uv
├── .env                            # All backend secrets
├── requests.http                   # Quick API testing (REST Client)
├── CLAUDE.md                       # Project context for Claude Code
└── ARCHITECTURE.md                 # This file
```

---

## Environment Variables

```
# Anthropic
ANTHROPIC_API_KEY=

# OpenAI (embeddings only)
OPENAI_API_KEY=

# LinkedIn
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=
LINKEDIN_REDIRECT_URI=http://localhost:8000/auth/callback

# Tavily (Phase 6)
TAVILY_API_KEY=

# PostgreSQL (Docker)
DATABASE_URL=postgresql://linkedin_agent:password@localhost:5432/linkedin_agent
POSTGRES_USER=linkedin_agent
POSTGRES_PASSWORD=password
POSTGRES_DB=linkedin_agent

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db

# App
SECRET_KEY=
FRONTEND_URL=http://localhost:3000
```

---

## Running Locally

```bash
# Terminal 1 — database
docker compose up -d

# Terminal 2 — backend (from project root)
uv run uvicorn backend.main:app --reload

# Terminal 3 — frontend
cd frontend && npm run dev

# Seed knowledge base (first time only)
uv run python -m backend.rag.ingestion
```

Backend: http://localhost:8000
Frontend: http://localhost:3000
API docs: http://localhost:8000/docs

---

## Checkpoints

- ✅ Phase 1 — Foundation: Docker + PostgreSQL + FastAPI + LinkedIn OAuth
- ✅ Phase 2 — RAG Pipeline: ChromaDB + OpenAI embeddings + 15-chunk knowledge base
- ✅ Phase 3 — LangGraph Agent: retrieve → agent → tools loop, InjectedState, conversation history
- ✅ Phase 4 — Content Tools: draft_post with clarifying questions, user-controlled publish/schedule
- ✅ Phase 5 — Frontend: Next.js 16, 4 pages, full OAuth flow, chat UI, drafts dashboard
- 🔄 Phase 6 — Intelligence: Tavily trend search, profile coach mode, analytics

---

## Phase 6 — What's Next

### search_trends tool (Tavily)
Agent searches what's trending in GenAI/tech right now and incorporates
that into post suggestions. Makes the Content Strategist mode genuinely useful.

### Profile Coach mode
Systematic profile audit: fetches live LinkedIn profile, compares against
your target role from memory, returns prioritized rewrite suggestions.

### Analytics tracking
Fetch engagement data for published posts, store in analytics table,
agent learns what topics/formats perform best for your audience over time.

---

## What This Demonstrates to Recruiters

| Skill | Where it shows |
|---|---|
| LangGraph stateful agents | Graph nodes, conditional routing, InjectedState |
| RAG pipeline | Chunk → embed → store → retrieve → generate |
| Vector databases | ChromaDB with cosine similarity search |
| LangChain + Claude tool use | All agent tools with @tool decorator |
| OAuth 2.0 | Full LinkedIn auth flow end-to-end |
| Full-stack (FastAPI + Next.js) | REST API + React frontend |
| PostgreSQL + SQLAlchemy | Relational DB with proper models |
| Docker | Containerized infrastructure |
| GenAI in production | Prompt engineering, context management, RAG |
| Node.js 22 + Next.js 16 | Latest frontend stack |

This is not a tutorial app. This is a production-grade agent you actually use.
