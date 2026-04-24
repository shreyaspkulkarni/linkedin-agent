from openai import OpenAI

from backend.config import settings

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536


def embed_text(text: str) -> list[float]:
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(input=text, model=EMBEDDING_MODEL)
    return response.data[0].embedding


def embed_texts(texts: list[str]) -> list[list[float]]:
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(input=texts, model=EMBEDDING_MODEL)
    return [item.embedding for item in response.data]
