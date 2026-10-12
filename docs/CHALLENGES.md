# Challenges & Solutions Log

Real issues hit during development. Used for the "Challenges Faced and Solutions" section of the
demo video and the final report.

| # | Challenge | Solution |
|---|---|---|
| 1 | PyPDF2 (listed in the brief) is deprecated and no longer maintained. | Used `pypdf`, its official maintained successor, which has the same API style. |
| 2 | Chunks cut in the middle of sentences lost meaning and hurt retrieval. | Built a splitter that prefers paragraph → sentence → line → word boundaries, with a 200-char overlap. |
| 3 | Answers need verifiable sources, not just text. | Stored page numbers as chunk metadata and numbered the retrieved chunks in the prompt so the model cites `[n]`, shown with file + page in the UI. |
| 4 | Re-uploading the same file created duplicate chunks. | Deterministic chunk IDs (file hash + index) and delete-before-insert on re-upload. |
| 5 | Long documents exceed the model's context window when summarising. | Map-reduce summarisation: summarise sections, then combine. |
| 6 | Keeping the API key out of the code for both local and cloud runs. | `.env` locally (git-ignored) and Streamlit Secrets in the cloud, read through one config function. |
| 7 | Follow-up questions like "what are its limitations?" retrieved irrelevant chunks because the search had no subject. | Added a query-rewriting step that turns follow-ups into standalone queries using the conversation history. |
| 8 | Scanned PDFs have no text layer, so nothing could be indexed. | Detect pages without text, render them to images with pypdfium2, and transcribe them with the OpenAI vision model. |
| 9 | Tesseract OCR needs a system install that Streamlit Cloud doesn't provide by default. | Used the vision capability of the existing OpenAI model instead: no extra install, one API. |
