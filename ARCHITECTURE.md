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

Four Pinecone namespaces:
1. **`linkedin_knowledge`** — curated LinkedIn best practices for tech/AI engineers (15 chunks)
2. **`user_posts`** — your published posts embedded over time (agent learns your voice)
3. **`user_profile`** — your stored profile sections (headline, about, experience, skills)
4. **`linkedin_examples`** — 119 real high-performing LinkedIn posts with engagement metrics (NeuML dataset)

---

## System Architecture (as built)

```
Next.js Frontend (Vercel — linkedin-agent-blue.vercel.app)
    │
    │  HTTPS via axios
    ▼
FastAPI Backend (AWS EC2 — https://3.80.255.79.nip.io)
    │  nginx reverse proxy + Let's Encrypt SSL
    │  systemd service (linkedin-agent.service)
    │
    ├── /auth/login          → LinkedIn OAuth redirect
    ├── /auth/callback       → exchange code, store user, redirect to frontend
    ├── /agent/chat          → runs the LangGraph agent
    ├── /agent/conversations → DELETE to clear conversation history
    ├── /posts/drafts        → list saved drafts
    ├── /posts/publish/{id}  → user-triggered publish to LinkedIn
    ├── /posts/schedule      → user-triggered schedule
    ├── /profile/me          → live LinkedIn profile data
    ├── /profile/data        → GET/POST stored profile sections
    └── /profile/import      → POST LinkedIn ZIP export (Profile.csv + Positions.csv + Skills.csv)
    │
    ▼
LangGraph Agent Graph
    │
    ├── [retrieve] node  → searches Pinecone (4 namespaces: kb + user_posts + user_profile + examples)
    │                      injects top-k chunks into state
    ├── [agent] node     → Claude sonnet-4-6 reasons over messages + RAG context
    │                      + PostgreSQL memory (career goals, preferences)
    │                      decides: call tools OR respond
    ├── [tools] node     → executes tool calls, results appended to state
    └── loops back to [agent] until no more tool calls → END
    │
    ▼
Agent Tools (what Claude can call)
    ├── get_memory()                   → loads user goals/prefs from PostgreSQL
    ├── save_memory(key, value)        → persists new context to PostgreSQL
    ├── get_my_linkedin_profile()      → fetches live profile via LinkedIn API
    ├── get_my_posts()                 → fetches post history + analytics from DB
    ├── draft_post(topic, format)      → RAG-informed post draft, saved as DB draft
    ├── publish_post(post_id)          → posts to LinkedIn via Share API
    ├── schedule_post(post_id, time)   → queues post for future publishing
    ├── search_trends(query)           → Tavily web search for trending topics
    └── analyze_profile()              → auto-fetches stored profile, full audit + rewrite suggestions

User-controlled endpoints (NOT agent tools — user decides)
    ├── POST /posts/publish/{id}  → publishes a saved draft to LinkedIn
    └── POST /posts/schedule      → schedules a draft for future publishing
    │
    ▼
External Services
    ├── LinkedIn API    → profile read + post publishing
    ├── Pinecone        → serverless vector store (4 namespaces, cloud-hosted)
    ├── AWS RDS         → PostgreSQL (db.t3.micro, us-east-1)
    ├── OpenAI API      → text-embedding-3-small for embeddings
    ├── Anthropic API   → Claude sonnet-4-6 as agent brain
    └── Tavily API      → web search for trends
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

**New Conversation:** `DELETE /agent/conversations` clears DB history so the agent starts fresh (avoids stale cached audit results in context).

---

## RAG Pipeline (as implemented)

```
Startup:
  linkedin_best_practices.md
        ↓ chunk (500 chars, 50 overlap)
        ↓ embed (OpenAI text-embedding-3-small)
        ↓ store → Pinecone "linkedin_knowledge" (15 chunks)

One-time seed:
  NeuML/neuml-linkedin-202501 (HuggingFace dataset)
        ↓ filter: >=5 likes, >=400 impressions, >=4% engagement rate
        ↓ sort by engagement rate descending, top 150
        ↓ format with engagement tier label [VIRAL / HIGH / SOLID]
        ↓ embed + store → Pinecone "linkedin_examples" (119 posts)

On every /agent/chat request:
  user message → embed → cosine similarity search across all 4 namespaces
        ↓
  top 3 from "linkedin_knowledge"
  + top 2 from "user_posts"
  + top 2 from "user_profile"
  + top 3 from "linkedin_examples"
        ↓
  injected into Claude's context before reasoning

On /profile/data POST:
  profile sections (headline, about, experience, skills)
        ↓ save to RDS linkedin_profiles table
        ↓ embed → store in Pinecone "user_profile"

On post publish:
  post content → embed → store in "user_posts"
  (agent learns your voice over time)
```

---

## Frontend (as built)

```
Next.js 16 + TypeScript + Tailwind CSS
Node.js 22 (nvm alias default 22)
Deployed on Vercel

Pages:
  /                   → Login page (LinkedIn OAuth button)
  /auth/callback      → Stores JWT token, redirects to /chat
  /chat               → Chat interface with agent + "New conversation" button
  /drafts             → Review drafts, publish now or schedule
  /profile            → Profile form (headline/about/experience/skills) + ZIP import + AI audit

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
linkedin_profiles   → stored profile sections (headline, about, experience, skills)
```

---

## Infrastructure (as deployed)

```
AWS EC2 (t2.micro, Ubuntu 24.04 LTS, us-east-1)
  - IP: 3.80.255.79
  - DNS: 3.80.255.79.nip.io (free wildcard DNS)
  - SSL: Let's Encrypt via certbot
  - Reverse proxy: nginx (proxy_read_timeout 300s for long AI calls)
  - Process manager: systemd (linkedin-agent.service)
  - Python: uv + venv

AWS RDS (db.t3.micro, PostgreSQL 16, us-east-1)
  - Private VPC, security group allows EC2 inbound on 5432

Pinecone (serverless, us-east-1-aws)
  - Index: linkedin-agent
  - Namespaces: linkedin_knowledge, user_posts, user_profile, linkedin_examples

Vercel (frontend)
  - Auto-deploys from GitHub main branch
  - NEXT_PUBLIC_API_URL=https://3.80.255.79.nip.io
```

---

## Project Structure (as built)

```
linkedin-agent/
├── backend/
│   ├── main.py                          # FastAPI app + router registration
│   ├── config.py                        # Pydantic settings from .env
│   ├── agent/
│   │   ├── graph.py                     # LangGraph graph (retrieve→agent→tools)
│   │   ├── state.py                     # AgentState TypedDict
│   │   ├── prompts.py                   # System prompt defining agent personality
│   │   ├── nodes/
│   │   │   ├── retrieve.py              # RAG retrieval node (4 Pinecone namespaces)
│   │   │   ├── agent.py                 # Claude reasoning node + tool binding
│   │   │   └── tools.py                 # ToolNode (LangGraph prebuilt)
│   │   └── tools/
│   │       ├── memory_tools.py          # save_memory, get_memory
│   │       ├── linkedin_tools.py        # get_my_linkedin_profile, get_my_posts, analyze_profile
│   │       ├── content_tools.py         # draft_post, publish_post, schedule_post
│   │       └── search_tools.py          # search_trends (Tavily)
│   ├── rag/
│   │   ├── vector_store.py              # Pinecone client + query/upsert helpers (4 namespaces)
│   │   ├── embeddings.py                # OpenAI text-embedding-3-small
│   │   ├── ingestion.py                 # KB loader + ingest_user_post() + ingest_user_profile()
│   │   ├── seed_linkedin_examples.py    # One-time seed: NeuML dataset → linkedin_examples
│   │   └── knowledge/
│   │       └── linkedin_best_practices.md
│   ├── api/routes/
│   │   ├── auth.py                      # OAuth login + callback
│   │   ├── agent.py                     # POST /agent/chat, DELETE /agent/conversations
│   │   ├── posts.py                     # drafts, publish, schedule, published
│   │   └── profile.py                   # /profile/me, /profile/data, /profile/import
│   ├── linkedin/
│   │   ├── auth.py                      # OAuth URL generation + token exchange
│   │   └── client.py                    # LinkedIn API wrapper
│   └── db/
│       ├── database.py                  # SQLAlchemy engine + session
│       ├── models.py                    # All DB models (incl. LinkedInProfile)
│       └── crud.py                      # DB operations
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                   # Root layout (dark theme)
│   │   ├── page.tsx                     # Login page
│   │   ├── auth/callback/page.tsx       # Token handler
│   │   ├── chat/page.tsx                # Agent chat UI + New conversation button
│   │   ├── drafts/page.tsx              # Draft review + publish/schedule
│   │   └── profile/page.tsx             # Profile form + ZIP import + AI audit
│   ├── lib/
│   │   └── api.ts                       # All backend API calls
│   └── .env.local                       # NEXT_PUBLIC_API_URL
│
├── pyproject.toml                       # Python deps managed by uv (incl. datasets)
├── .env                                 # All backend secrets
├── requests.http                        # Quick API testing (REST Client)
├── CLAUDE.md                            # Project context for Claude Code
└── ARCHITECTURE.md                      # This file
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
LINKEDIN_REDIRECT_URI=https://3.80.255.79.nip.io/auth/callback

# Tavily
TAVILY_API_KEY=

# PostgreSQL (AWS RDS)
DATABASE_URL=postgresql://user:password@rds-endpoint:5432/linkedin_agent

# Pinecone
PINECONE_API_KEY=
PINECONE_INDEX_NAME=linkedin-agent

# App
SECRET_KEY=
FRONTEND_URL=https://linkedin-agent-blue.vercel.app
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

# Seed LinkedIn examples into Pinecone (first time only — skips if already populated)
uv run python -m backend.rag.seed_linkedin_examples
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
- ✅ Phase 6 — Intelligence: Tavily search_trends, analyze_profile (profile coach), analytics tracking
- ✅ Phase 7 — Deployment: AWS EC2 + RDS + Pinecone migration + Vercel + SSL via nip.io
- ✅ Phase 8 — RAG Enrichment: Profile storage system, New Conversation feature, 119 LinkedIn example posts in Pinecone

---

## What This Demonstrates to Recruiters

| Skill | Where it shows |
|---|---|
| LangGraph stateful agents | Graph nodes, conditional routing, InjectedState |
| RAG pipeline | Chunk → embed → store → retrieve → generate |
| Vector databases | Pinecone serverless with 4 namespaces |
| LangChain + Claude tool use | 9 agent tools with @tool decorator |
| OAuth 2.0 | Full LinkedIn auth flow end-to-end |
| Full-stack (FastAPI + Next.js) | REST API + React frontend |
| PostgreSQL + SQLAlchemy | Relational DB with proper models |
| AWS (EC2 + RDS) | Production cloud deployment |
| Vercel | Frontend hosting with auto-deploy |
| nginx + SSL | Reverse proxy + Let's Encrypt |
| GenAI in production | Prompt engineering, context management, RAG |
| HuggingFace datasets | Real-world data ingestion pipeline |

This is not a tutorial app. This is a production-grade agent you actually use.
