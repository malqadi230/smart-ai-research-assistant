import streamlit as st

from research_assistant.ingestion import SUPPORTED_TYPES
from research_assistant.ui import forget_summaries, get_assistant

st.title("📚 Knowledge Base")
assistant = get_assistant()

st.subheader("Add documents")
files = st.file_uploader("Upload PDF, TXT or MD files", type=list(SUPPORTED_TYPES), accept_multiple_files=True)
use_ocr = st.toggle(
    "Read scanned pages with OCR",
    value=True,
    help="Pages with no selectable text (scans, photos) are read by the AI vision model. Slower, and uses extra API calls.",
)

if files and st.button("Add to knowledge base", type="primary"):
    progress = st.progress(0.0)
    for i, f in enumerate(files, 1):
        with st.spinner(f"Processing {f.name}…"):
            try:
                result = assistant.ingest(f.name, f.getvalue(), use_ocr=use_ocr)
                forget_summaries(f.name)
                ocr_note = f" ({result.ocr_pages} scanned pages read with OCR)" if result.ocr_pages else ""
                st.success(f"{f.name}: indexed {result.chunks} chunks{ocr_note}")
            except Exception as e:
                st.error(f"{f.name}: {e}")
        progress.progress(i / len(files))

st.subheader("Indexed documents")
docs = assistant.store.list_documents()
if not docs:
    st.caption("No documents yet.")
for name, n_chunks in docs.items():
    col1, col2, col3 = st.columns([6, 2, 1])
    col1.write(f"📄 {name}")
    col2.caption(f"{n_chunks} chunks")
    if col3.button("Delete", key=f"del-{name}"):
        assistant.store.delete_document(name)
        forget_summaries(name)
        st.rerun()
