"""Smart AI Research Assistant — Streamlit entry point."""

import streamlit as st

st.set_page_config(page_title="Smart AI Research Assistant", page_icon="🔬", layout="wide")

pages = [
    st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("views/knowledge_base.py", title="Knowledge Base", icon=":material/library_books:"),
    st.Page("views/chat.py", title="Chat with Documents", icon=":material/forum:"),
    st.Page("views/search.py", title="Semantic Search", icon=":material/search:"),
    st.Page("views/insights.py", title="Summaries & Insights", icon=":material/insights:"),
]

st.navigation(pages).run()
