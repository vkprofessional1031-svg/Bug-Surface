"""Persistent vector store of past fixes and review feedback."""
import chromadb
from sentence_transformers import SentenceTransformer

PERSIST_DIR = "memory/chroma_db"
COLLECTION_NAME = "past_fixes"

_model = SentenceTransformer("all-MiniLM-L6-v2")


def _get_collection():
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    return client.get_or_create_collection(COLLECTION_NAME)


def store_fix(issue_text: str, diff_text: str, review_reasoning: str, issue_name: str, derived_from: str = ""):
    """Embed and store a resolved, approved fix. `derived_from` records which
    past fix (if any) was retrieved and influenced this one, for provenance."""
    collection = _get_collection()
    embedding = _model.encode(issue_text).tolist()
    collection.add(
        ids=[issue_name],
        embeddings=[embedding],
        documents=[diff_text],
        metadatas=[{
            "issue_text": issue_text,
            "review_reasoning": review_reasoning,
            "derived_from": derived_from,
        }],
    )


def retrieve_similar(issue_text: str, k: int = 2) -> list[dict]:
    """Find the k most similar past resolved issues, if any exist."""
    collection = _get_collection()
    if collection.count() == 0:
        return []
    embedding = _model.encode(issue_text).tolist()
    results = collection.query(query_embeddings=[embedding], n_results=min(k, collection.count()))

    lessons = []
    for doc_id, doc, meta in zip(results["ids"][0], results["documents"][0], results["metadatas"][0]):
        lessons.append({
            "id": doc_id,
            "past_issue": meta["issue_text"],
            "past_diff": doc,
            "past_review_notes": meta["review_reasoning"],
        })
    return lessons
