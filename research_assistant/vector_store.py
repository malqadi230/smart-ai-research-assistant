"""ChromaDB-backed vector store for document chunks."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import chromadb

from .ingestion import Chunk


@dataclass
class SearchResult:
    text: str
    source: str
    page: int
    score: float


class VectorStore:
    def __init__(self, persist_dir: Path, collection_name: str):
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = self._client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    def count(self) -> int:
        return self._collection.count()

    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        self._collection.upsert(
            ids=[c.id for c in chunks],
            documents=[c.text for c in chunks],
            embeddings=embeddings,
            metadatas=[{"source": c.source, "page": c.page, "chunk_index": c.chunk_index} for c in chunks],
        )

    def query(self, embedding: list[float], k: int, sources: list[str] | None = None) -> list[SearchResult]:
        if self.count() == 0:
            return []
        where = {"source": {"$in": sources}} if sources else None
        res = self._collection.query(query_embeddings=[embedding], n_results=k, where=where)
        return [
            SearchResult(text=doc, source=meta["source"], page=int(meta["page"]), score=1 - dist)
            for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
        ]

    def list_documents(self) -> dict[str, int]:
        """Map of document name -> number of chunks."""
        metas = self._collection.get(include=["metadatas"])["metadatas"] or []
        return dict(sorted(Counter(m["source"] for m in metas).items()))

    def get_document_chunks(self, source: str) -> list[str]:
        res = self._collection.get(where={"source": source}, include=["documents", "metadatas"])
        pairs = sorted(zip(res["metadatas"], res["documents"]), key=lambda p: p[0]["chunk_index"])
        return [doc for _, doc in pairs]

    def delete_document(self, source: str) -> None:
        self._collection.delete(where={"source": source})
