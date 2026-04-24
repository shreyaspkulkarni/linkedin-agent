# LinkedIn AI Agent

## What This Project Is
A personal AI agent for managing LinkedIn presence. It reads your profile,
remembers your goals, tracks post performance, and helps decide what to post
to grow your career. Built with Claude API tool use, FastAPI, React/TypeScript,
and PostgreSQL.

## Stack
- **Agent:** Claude API with raw tool use (no LangChain)
- **Backend:** Python FastAPI
- **Frontend:** React + TypeScript
- **DB:** PostgreSQL via SQLAlchemy
- **Auth:** LinkedIn OAuth 2.0
- **Search:** Tavily API
- **Containers:** Docker + Docker Compose

## Key Files
- `ARCHITECTURE.md` — full system design, DB schema, build phases
- `backend/agent/agent.py` — main agent loop
- `backend/agent/tools/` — all agent tools
- `backend/db/models.py` — DB schema
- `backend/linkedin/client.py` — LinkedIn API wrapper

## Checkpoints
- ✅ Checkpoint 1 — Phase 1 complete: Docker + PostgreSQL + FastAPI + LinkedIn OAuth working. JWT auth confirmed.
- ✅ Checkpoint 2 — Phase 2 complete: ChromaDB + OpenAI embeddings + LinkedIn best practices KB ingested (15 chunks). RAG retrieval working.
- ✅ Checkpoint 3 — Phase 3 complete: LangGraph agent working. retrieve → agent → tools loop confirmed. InjectedState for user_id. Conversations saved to DB.
- ✅ Checkpoint 4 — Phase 4 complete: draft_post tool working. Agent asks clarifying Qs before drafting. Conversation history loaded from DB. publish/schedule are user-controlled endpoints.
- ✅ Checkpoint 5 — Phase 5 complete: Next.js 16 frontend working. Login → chat → drafts → profile flow complete. OAuth redirects to frontend. Grammarly hydration warning is harmless.

## Current Phase
Phase 6 — Intelligence (Tavily trend search, profile coach, analytics)

## Agent Tools
1. `get_my_linkedin_profile` — reads live LinkedIn profile
2. `get_my_posts` — fetches post history + analytics from DB
3. `search_trends` — Tavily web search for trending topics
4. `draft_post` — generates post draft in user's voice
5. `publish_post` — posts to LinkedIn via Share API
6. `schedule_post` — queues post for later publishing
7. `save_memory` — persists user context to DB
8. `get_memory` — retrieves stored context
9. `analyze_profile` — audits profile against career goals

## Environment Variables Needed
See `.env.example` for all required keys:
- ANTHROPIC_API_KEY
- LINKEDIN_CLIENT_ID + LINKEDIN_CLIENT_SECRET
- TAVILY_API_KEY
- DATABASE_URL
- SECRET_KEY

## Dev Setup
```bash
cp .env.example .env
# fill in .env values
docker-compose up
```
Backend: http://localhost:8000
Frontend: http://localhost:3000
API docs: http://localhost:8000/docs
