"""Central configuration, read from Streamlit secrets or environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[1]


def _get(key: str, default: str | None = None) -> str | None:
    # Streamlit Cloud injects secrets via st.secrets; locally we fall back to .env
    try:
        import streamlit as st

        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    chat_model: str
    embedding_model: str
    chroma_dir: Path
    collection_name: str
    chunk_size: int
    chunk_overlap: int
    top_k: int


def get_settings() -> Settings:
    return Settings(
        openai_api_key=_get("OPENAI_API_KEY"),
        chat_model=_get("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        embedding_model=_get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        chroma_dir=Path(_get("CHROMA_DIR", str(ROOT_DIR / "data" / "chroma_db"))),
        collection_name=_get("CHROMA_COLLECTION", "research_docs"),
        chunk_size=int(_get("CHUNK_SIZE", "1000")),
        chunk_overlap=int(_get("CHUNK_OVERLAP", "200")),
        top_k=int(_get("TOP_K", "5")),
    )
