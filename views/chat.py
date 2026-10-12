import streamlit as st

from research_assistant.ui import chat_to_markdown, get_assistant, render_sources, source_filter

EXAMPLE_QUESTIONS = [
    "Summarize the main findings",
    "What methodology was used?",
    "What limitations are mentioned?",
    "What future work is suggested?",
]

st.title("💬 Chat with Documents")
assistant = get_assistant()
sources = source_filter(assistant, key="chat_sources")

if "chat" not in st.session_state:
    st.session_state.chat = []  # list of {"role", "content", "sources"?, "search_query"?}

st.sidebar.download_button(
    "Export conversation (.md)",
    chat_to_markdown(st.session_state.chat),
    file_name="research-chat.md",
    disabled=not st.session_state.chat,
    width="stretch",
)
if st.sidebar.button("Clear conversation", width="stretch"):
    st.session_state.chat = []
    st.rerun()

for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            render_sources(msg["sources"], msg.get("search_query"))

pending = st.session_state.pop("pending_question", None)
if not st.session_state.chat and not pending:
    st.caption("Try one of these to get started:")
    cols = st.columns(len(EXAMPLE_QUESTIONS))
    for col, example in zip(cols, EXAMPLE_QUESTIONS):
        if col.button(example, width="stretch"):
            st.session_state.pending_question = example
            st.rerun()

question = st.chat_input("Ask a question about your documents") or pending

if question:
    if assistant.store.count() == 0:
        st.warning("Upload documents in the Knowledge Base page first.")
        st.stop()

    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat]
    st.session_state.chat.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching documents…"):
            search_query = assistant.condense_question(question, history)
            results = assistant.search(search_query, sources=sources)
        answer = st.write_stream(assistant.stream_answer(question, results, history))
        shown_query = search_query if search_query != question else None
        render_sources(results, shown_query)

    st.session_state.chat.append(
        {"role": "assistant", "content": answer, "sources": results, "search_query": shown_query}
    )
    st.rerun()  # refresh the sidebar export with the new message
