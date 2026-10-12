import streamlit as st

from research_assistant.ui import get_assistant

st.title("🔬 Smart AI Research Assistant")
st.write(
    "Upload research documents, search them by meaning, and ask questions answered "
    "with citations — powered by Retrieval-Augmented Generation (RAG)."
)

assistant = get_assistant()
docs = assistant.store.list_documents()

c1, c2, c3 = st.columns(3)
c1.metric("Documents", len(docs))
c2.metric("Indexed chunks", assistant.store.count())
c3.metric("Results per query", assistant.settings.top_k)
st.caption(f"Models: {assistant.settings.chat_model} · {assistant.settings.embedding_model}")

st.subheader("How it works")
st.markdown(
    """
1. **Upload** PDFs or text files in the *Knowledge Base* page.
2. Text is **extracted and split into chunks**, each converted to an **embedding** vector.
3. Embeddings are stored in a **ChromaDB vector database**.
4. When you ask a question, the most relevant chunks are **retrieved** by semantic similarity.
5. The model **generates an answer grounded in those chunks**, citing its sources.
"""
)

if not docs:
    st.info("Your knowledge base is empty. Start by uploading documents.")
    st.page_link("views/knowledge_base.py", label="Go to Knowledge Base", icon=":material/upload:")
