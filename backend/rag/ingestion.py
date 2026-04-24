"""
Ingestion pipeline — loads knowledge base into Pinecone.
Run this once to seed the vector store, and re-run whenever you update the knowledge base.
"""

import hashlib
from pathlib import Path

from backend.rag.vector_store import (
    KNOWLEDGE_COLLECTION,
    USER_POSTS_COLLECTION,
    add_documents,
    get_document_count,
)

KNOWLEDGE_BASE_PATH = Path(__file__).parent / "knowledge" / "linkedin_best_practices.md"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end].strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if len(c) > 50]


def make_chunk_id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def ingest_knowledge_base(force: bool = False):
    """
    Load linkedin_best_practices.md into the linkedin_knowledge namespace.
    Skips if already populated unless force=True.
    """
    if not force and get_document_count(KNOWLEDGE_COLLECTION) > 0:
        print(f"[RAG] Knowledge base already loaded. Skipping.")
        return

    print("[RAG] Loading LinkedIn best practices knowledge base...")

    text = KNOWLEDGE_BASE_PATH.read_text(encoding="utf-8")
    chunks = chunk_text(text)

    documents = chunks
    metadatas = [{"source": "linkedin_best_practices", "chunk_index": i} for i, _ in enumerate(chunks)]
    ids = [make_chunk_id(chunk) for chunk in chunks]

    add_documents(KNOWLEDGE_COLLECTION, documents, metadatas, ids)
    print(f"[RAG] Loaded {len(chunks)} chunks into '{KNOWLEDGE_COLLECTION}'.")


def ingest_user_post(post_content: str, post_id: str, metadata: dict):
    """
    Called whenever a post is published. Adds it to the user_posts namespace
    so the agent can learn from your posting history over time.
    """
    add_documents(
        USER_POSTS_COLLECTION,
        documents=[post_content],
        metadatas=[metadata],
        ids=[post_id],
    )
    print(f"[RAG] Added post {post_id} to user_posts namespace.")


if __name__ == "__main__":
    ingest_knowledge_base(force=True)
    print("[RAG] Ingestion complete.")
