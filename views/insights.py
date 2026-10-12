import streamlit as st

from research_assistant.summarizer import generate_insights, summarize_document
from research_assistant.ui import get_assistant

st.title("📝 Summaries & Insights")
assistant = get_assistant()
docs = list(assistant.store.list_documents())

if not docs:
    st.info("Upload documents in the Knowledge Base page first.")
    st.stop()

if "summaries" not in st.session_state:
    st.session_state.summaries = {}
summaries: dict[str, str] = st.session_state.summaries


def ensure_summary(name: str) -> str:
    if name not in summaries:
        chunks = assistant.store.get_document_chunks(name)
        summaries[name] = summarize_document(assistant.client, assistant.settings.chat_model, chunks)
    return summaries[name]


tab_summary, tab_insights = st.tabs(["Research summary", "Cross-document insights"])

with tab_summary:
    doc = st.selectbox("Document", docs)
    if st.button("Generate summary", type="primary"):
        with st.spinner(f"Summarizing {doc}…"):
            ensure_summary(doc)
    if doc in summaries:
        st.markdown(summaries[doc])
        st.download_button("Download summary (.md)", summaries[doc], file_name=f"{doc}-summary.md")

with tab_insights:
    selected = st.multiselect("Documents to compare", docs, default=docs[:5])
    if st.button("Generate insights", type="primary", disabled=len(selected) < 1):
        with st.spinner("Reading documents and generating insights…"):
            picked = {name: ensure_summary(name) for name in selected}
            st.session_state.insights = generate_insights(assistant.client, assistant.settings.chat_model, picked)
    if "insights" in st.session_state:
        st.markdown(st.session_state.insights)
        st.download_button("Download insights (.md)", st.session_state.insights, file_name="insights.md")
