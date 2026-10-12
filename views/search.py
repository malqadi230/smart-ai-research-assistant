import streamlit as st

from research_assistant.ui import get_assistant, source_filter

st.title("🔎 Semantic Search")
st.caption("Finds passages by meaning, not just matching keywords.")
assistant = get_assistant()
sources = source_filter(assistant, key="search_sources")

query = st.text_input("Search query", placeholder="e.g. limitations of the proposed method")
k = st.slider("Number of results", 1, 20, assistant.settings.top_k)

if query:
    with st.spinner("Searching…"):
        results = assistant.search(query, k=k, sources=sources)
    if not results:
        st.info("No results. Is the knowledge base empty?")
    for i, r in enumerate(results, 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {r.source}** · page {r.page}")
            st.progress(max(0.0, min(1.0, r.score)), text=f"Relevance {r.score:.2f}")
            st.write(r.text)
