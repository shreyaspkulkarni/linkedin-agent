from pinecone import Pinecone

from backend.config import settings
from backend.rag.embeddings import embed_text, embed_texts

KNOWLEDGE_COLLECTION = "linkedin_knowledge"
USER_POSTS_COLLECTION = "user_posts"
USER_PROFILE_COLLECTION = "user_profile"


def _get_index():
    pc = Pinecone(api_key=settings.pinecone_api_key)
    return pc.Index(settings.pinecone_index_name)


def add_documents(namespace: str, documents: list[str], metadatas: list[dict], ids: list[str]):
    """Embed documents and upsert into Pinecone under the given namespace."""
    index = _get_index()
    vectors_list = embed_texts(documents)
    vectors = [
        {"id": id_, "values": vec, "metadata": {**meta, "text": doc}}
        for id_, vec, meta, doc in zip(ids, vectors_list, metadatas, documents)
    ]
    index.upsert(vectors=vectors, namespace=namespace)


def query_documents(namespace: str, query_text: str, n_results: int = 5) -> list[str]:
    """Find the n most semantically similar chunks to query_text."""
    index = _get_index()
    query_vector = embed_text(query_text)
    results = index.query(
        vector=query_vector,
        top_k=n_results,
        namespace=namespace,
        include_metadata=True,
    )
    return [
        match.metadata.get("text", "")
        for match in results.matches
        if match.metadata
    ]


def get_document_count(namespace: str) -> int:
    """Return how many vectors exist in a namespace."""
    index = _get_index()
    stats = index.describe_index_stats()
    namespace_info = stats.namespaces.get(namespace)
    return namespace_info.vector_count if namespace_info else 0
