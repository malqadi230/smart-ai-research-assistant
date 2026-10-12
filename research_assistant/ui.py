"""Streamlit helpers shared across pages."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from .rag import ResearchAssistant
from .vector_store import SearchResult


@st.cache_resource(show_spinner=False)
def _assistant() -> ResearchAssistant:
    return ResearchAssistant()


def get_assistant() -> ResearchAssistant:
    try:
        return _assistant()
    except RuntimeError as e:
        st.error(str(e))
        st.stop()


def source_filter(assistant: ResearchAssistant, key: str) -> list[str] | None:
    """Sidebar multiselect to restrict retrieval to specific documents. None means all."""
    docs = list(assistant.store.list_documents())
    selected = st.sidebar.multiselect("Limit to documents", docs, key=key, placeholder="All documents")
    return selected or None


def render_sources(results: list[SearchResult], search_query: str | None = None) -> None:
    with st.expander(f"Sources ({len(results)})"):
        if search_query:
            st.caption(f"🔁 Follow-up searched as: *{search_query}*")
        for i, r in enumerate(results, 1):
            st.markdown(f"**[{i}] {r.source}** · page {r.page} · relevance {r.score:.2f}")
            st.caption(r.text[:500] + ("…" if len(r.text) > 500 else ""))


def forget_summaries(*names: str) -> None:
    """Drop cached summaries/insights after documents change so stale results aren't shown."""
    summaries = st.session_state.get("summaries", {})
    for name in names:
        summaries.pop(name, None)
    st.session_state.pop("insights", None)


def chat_to_markdown(messages: list[dict]) -> str:
    lines = ["# Research Assistant — Conversation Export", f"_Exported {datetime.now():%d %b %Y, %H:%M}_", ""]
    for msg in messages:
        if msg["role"] == "user":
            lines += [f"## Q: {msg['content']}", ""]
        else:
            lines += [msg["content"], ""]
            if msg.get("sources"):
                lines.append("**Sources**")
                lines += [f"- [{i}] {r.source}, page {r.page}" for i, r in enumerate(msg["sources"], 1)]
                lines.append("")
    return "\n".join(lines)
