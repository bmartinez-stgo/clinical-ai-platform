from __future__ import annotations

import logging

import chromadb

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "clinical_cases"


def _collection() -> chromadb.Collection:
    s = get_settings()
    client = chromadb.HttpClient(host=s.chromadb_host, port=s.chromadb_port)
    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def upsert(case_id: str, embedding: list[float], metadata: dict, document: str) -> None:
    _collection().upsert(
        ids=[case_id],
        embeddings=[embedding],
        metadatas=[metadata],
        documents=[document],
    )


def query(embedding: list[float], top_k: int) -> tuple[dict | None, int]:
    col = _collection()
    n = col.count()
    if n == 0:
        return None, 0
    results = col.query(
        query_embeddings=[embedding],
        n_results=min(top_k, n),
        include=["metadatas", "distances"],
    )
    return results, n


def delete(case_id: str) -> None:
    _collection().delete(ids=[case_id])


def count() -> int:
    return _collection().count()
