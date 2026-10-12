# RAG Pipeline Documentation

Retrieval-Augmented Generation (RAG) grounds a language model's answer in your own documents:
instead of relying on what the model memorised during training, relevant passages are retrieved
first and handed to the model as context.

## 1. Ingestion (`research_assistant/ingestion.py`)

1. **Text extraction:** PDFs are read page by page with `pypdf`, so every chunk remembers its page
   number for citations. TXT/MD files are treated as a single page.
   **Scanned pages:** if a PDF page has (almost) no extractable text, it is rendered to an image with
   `pypdfium2` and transcribed by the OpenAI vision model. Only image-only pages are sent, so normal
   PDFs incur no extra cost. OCR can be switched off on the Knowledge Base page.
2. **Cleaning:** null bytes are removed, runs of spaces are collapsed, and excessive blank lines
   are reduced.
3. **Chunking:** text is split into ~1000-character chunks with a 200-character overlap. The splitter
   prefers to cut at a paragraph break, then a sentence end, then a line break, then a space, so
   chunks rarely end mid-sentence. The overlap keeps ideas that cross a boundary retrievable.

## 2. Embedding (`research_assistant/openai_client.py`)

Each chunk is converted into a vector with OpenAI `text-embedding-3-small` (1536 dimensions).
Requests are batched (100 chunks per call) to reduce latency and the number of API round trips.

## 3. Storage (`research_assistant/vector_store.py`)

Vectors, chunk text and metadata (`source`, `page`, `chunk_index`) are stored in a persistent
ChromaDB collection configured for **cosine similarity**. Chunk IDs are derived from a hash of the
file name plus the chunk index; re-uploading a file deletes its old chunks first, so there are no
duplicates.

## 4. Retrieval (`research_assistant/rag.py → condense_question, search`)

**Follow-up rewriting:** a follow-up such as *"how long did they take to recover?"* has no
searchable subject on its own. When there is conversation history, the model first rewrites it as a
standalone query (*"How long did corals take to recover from bleaching?"*). The rewritten query is
used for retrieval and shown under the answer's sources for transparency; the model still answers
the user's original question.

The query is embedded with the same model, and the top-k (default 5) most similar chunks are
returned. An optional metadata filter (`source $in [...]`) limits the search to the documents the
user selected. Relevance is reported as `1 - cosine distance`.

## 5. Generation (`research_assistant/rag.py → stream_answer`)

The prompt sent to the chat model contains:

- a **system prompt** instructing it to answer only from the sources, cite them as `[n]`, and say so
  when the answer is not in the sources;
- the last 6 conversation messages, for follow-up questions;
- the retrieved chunks, numbered `[1]…[k]` with their file name and page.

The answer is streamed token by token to the UI, and the numbered sources are shown beneath it so
every citation can be checked.

## 6. Summaries & insights (`research_assistant/summarizer.py`)

Long documents do not fit in one prompt, so summarisation uses **map-reduce**: chunks are grouped
into ~12k-character sections, each section is summarised, and the partial summaries are merged into a
structured summary (Overview, Key Findings, Methodology, Conclusions). Cross-document insights are
generated from the per-document summaries (themes, agreements, contradictions, gaps, next steps).

## Design decisions

| Decision | Reason |
|---|---|
| ChromaDB over Pinecone | Runs locally with no account and no extra cost; easy to swap later |
| Character-based chunking with boundary search | Simple, dependency-free, and keeps sentences intact |
| Page-level metadata | Enables precise citations (file + page) |
| Cosine similarity | The standard metric for OpenAI embeddings |
| Streaming responses | Better perceived latency in the chat UI |
| Query rewriting only when history exists | Saves an API call on first questions |
| Vision-model OCR instead of Tesseract | No system install needed locally or on Streamlit Cloud |
