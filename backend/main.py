from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.db.database import create_tables
from backend.api.routes import auth, profile, agent, posts

app = FastAPI(title="LinkedIn AI Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    create_tables()


app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(agent.router)
app.include_router(posts.router)


@app.get("/health")
def health():
    return {"status": "ok"}
