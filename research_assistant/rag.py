"""Retrieval-Augmented Generation pipeline tying ingestion, retrieval and generation together."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .config import Settings, get_settings
from .ingestion import chunk_document
from .openai_client import chat, chat_stream, embed_texts, get_client, ocr_image
from .vector_store import SearchResult, VectorStore

SYSTEM_PROMPT = """You are a careful research assistant.
Answer the user's question using ONLY the numbered sources provided in the context.
- Cite every claim inline with the source number in square brackets, e.g. [1] or [2][3].
- If the sources do not contain the answer, say so plainly instead of guessing.
- Be concise and well structured; use bullet points for lists of findings."""

REWRITE_PROMPT = """Rewrite the user's latest question as a standalone search query for a document database.
Use the conversation to resolve references such as "it", "they", "that method" or "the second point".
Return ONLY the rewritten query. If the question is already standalone, return it unchanged."""

MAX_HISTORY_MESSAGES = 6


@dataclass
class IngestResult:
    chunks: int
    ocr_pages: int


def build_context(results: list[SearchResult]) -> str:
    return "\n\n".join(
        f"[{i}] (source: {r.source}, page {r.page})\n{r.text}" for i, r in enumerate(results, 1)
    )


class ResearchAssistant:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.client = get_client(self.settings)
        self.store = VectorStore(self.settings.chroma_dir, self.settings.collection_name)

    # --- Ingestion -------------------------------------------------------

    def ingest(self, filename: str, data: bytes, use_ocr: bool = True) -> IngestResult:
        """Chunk, embed and store a document. Re-uploading a file replaces it."""
        ocr_pages = 0

        def ocr(png: bytes) -> str:
            nonlocal ocr_pages
            ocr_pages += 1
            return ocr_image(self.client, self.settings.chat_model, png)

        chunks = chunk_document(
            filename, data, self.settings.chunk_size, self.settings.chunk_overlap, ocr if use_ocr else None
        )
        if not chunks:
            hint = "" if use_ocr else " It may be a scanned PDF; enable OCR and try again."
            raise ValueError(f"No extractable text in {filename}.{hint}")
        vectors = embed_texts(self.client, self.settings.embedding_model, [c.text for c in chunks])
        self.store.delete_document(filename)
        self.store.add_chunks(chunks, vectors)
        return IngestResult(chunks=len(chunks), ocr_pages=ocr_pages)

    # --- Retrieval -------------------------------------------------------

    def search(self, query: str, k: int | None = None, sources: list[str] | None = None) -> list[SearchResult]:
        [vector] = embed_texts(self.client, self.settings.embedding_model, [query])
        return self.store.query(vector, k or self.settings.top_k, sources)

    def condense_question(self, question: str, history: list[dict] | None) -> str:
        """Turn a follow-up like "what are its limitations?" into a standalone search query."""
        if not history:
            return question
        convo = "\n".join(f"{m['role']}: {m['content'][:1000]}" for m in history[-MAX_HISTORY_MESSAGES:])
        rewritten = chat(
            self.client,
            self.settings.chat_model,
            [
                {"role": "system", "content": REWRITE_PROMPT},
                {"role": "user", "content": f"Conversation:\n{convo}\n\nLatest question: {question}"},
            ],
        )
        return rewritten.strip().strip('"') or question

    # --- Generation ------------------------------------------------------

    def _messages(self, question: str, results: list[SearchResult], history: list[dict] | None) -> list[dict]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += (history or [])[-MAX_HISTORY_MESSAGES:]
        messages.append(
            {"role": "user", "content": f"Context:\n{build_context(results)}\n\nQuestion: {question}"}
        )
        return messages

    def answer(self, question: str, results: list[SearchResult], history: list[dict] | None = None) -> str:
        return chat(self.client, self.settings.chat_model, self._messages(question, results, history))

    def stream_answer(
        self, question: str, results: list[SearchResult], history: list[dict] | None = None
    ) -> Iterator[str]:
        return chat_stream(self.client, self.settings.chat_model, self._messages(question, results, history))
