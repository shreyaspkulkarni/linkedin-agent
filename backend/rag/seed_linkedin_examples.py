"""
Seed Pinecone with high-performing LinkedIn posts from NeuML/neuml-linkedin-202501.
Run once: uv run python -m backend.rag.seed_linkedin_examples
"""

import hashlib
import sys

from datasets import load_dataset

from backend.rag.vector_store import LINKEDIN_EXAMPLES_COLLECTION, add_documents, get_document_count

MIN_LIKES = 5
MIN_IMPRESSIONS = 400
MIN_ENGAGEMENT_RATE = 0.04  # top ~50% by engagement rate
MAX_POSTS = 150


def _engagement_tier(engagement_rate: float) -> str:
    if engagement_rate >= 0.10:
        return "viral"
    if engagement_rate >= 0.06:
        return "high"
    return "solid"


def _format_post(row: dict) -> str:
    likes = row.get("Likes") or 0
    comments = row.get("Comments") or 0
    impressions = row.get("Impressions") or 0
    reposts = row.get("Reposts") or 0
    eng_rate = row.get("Engagement rate") or 0.0
    tier = _engagement_tier(eng_rate)
    text = (row.get("Post title") or "").strip()
    return (
        f"[{tier.upper()} ENGAGEMENT — {likes} likes, {comments} comments, "
        f"{reposts} reposts, {impressions:,} impressions, {eng_rate:.1%} engagement rate]\n\n"
        f"{text}"
    )


def main():
    existing = get_document_count(LINKEDIN_EXAMPLES_COLLECTION)
    if existing > 0:
        print(f"linkedin_examples already has {existing} vectors. Skipping seed.")
        print("To re-seed, delete the namespace in Pinecone first.")
        sys.exit(0)

    print("Loading NeuML/neuml-linkedin-202501 dataset...")
    ds = load_dataset("NeuML/neuml-linkedin-202501", split="train")
    print(f"Total posts: {len(ds)}")

    rows = [
        r for r in ds
        if (r.get("Likes") or 0) >= MIN_LIKES
        and (r.get("Impressions") or 0) >= MIN_IMPRESSIONS
        and (r.get("Engagement rate") or 0.0) >= MIN_ENGAGEMENT_RATE
    ]
    print(f"After filtering (>={MIN_LIKES} likes, >={MIN_IMPRESSIONS} impressions, >={MIN_ENGAGEMENT_RATE:.0%} eng rate): {len(rows)} posts")

    # Sort by engagement rate descending and cap
    rows.sort(key=lambda r: r.get("Engagement rate") or 0.0, reverse=True)
    rows = rows[:MAX_POSTS]
    print(f"Using top {len(rows)} posts")

    documents = [_format_post(r) for r in rows]
    metadatas = [
        {
            "likes": r.get("Likes") or 0,
            "comments": r.get("Comments") or 0,
            "impressions": r.get("Impressions") or 0,
            "reposts": r.get("Reposts") or 0,
            "engagement_rate": r.get("Engagement rate") or 0.0,
            "tier": _engagement_tier(r.get("Engagement rate") or 0.0),
        }
        for r in rows
    ]
    ids = [hashlib.md5(doc.encode()).hexdigest() for doc in documents]

    print("Embedding and upserting to Pinecone (this takes ~1 min)...")
    # Upsert in batches of 50 to stay within request limits
    batch = 50
    for i in range(0, len(documents), batch):
        add_documents(
            LINKEDIN_EXAMPLES_COLLECTION,
            documents[i : i + batch],
            metadatas[i : i + batch],
            ids[i : i + batch],
        )
        print(f"  Upserted {min(i + batch, len(documents))}/{len(documents)}")

    print(f"\nDone. {len(documents)} LinkedIn example posts ingested into '{LINKEDIN_EXAMPLES_COLLECTION}'.")


if __name__ == "__main__":
    main()
