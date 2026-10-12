"""Document loading, text extraction and chunking."""

from __future__ import annotations

import hashlib
import io
import re
from collections.abc import Callable
from dataclasses import dataclass

from pypdf import PdfReader

SUPPORTED_TYPES = ("pdf", "txt", "md")

# A page with less extractable text than this is treated as scanned (image-only)
OCR_MIN_CHARS = 20
OCR_RENDER_SCALE = 2  # ~144 DPI, enough for reliable OCR

OcrFn = Callable[[bytes], str]  # PNG bytes -> text


@dataclass
class Chunk:
    text: str
    source: str
    page: int
    chunk_index: int

    @property
    def id(self) -> str:
        return f"{doc_id(self.source)}-{self.chunk_index}"


def doc_id(source: str) -> str:
    return hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]


def render_page_png(pdf, index: int) -> bytes:
    image = pdf[index].render(scale=OCR_RENDER_SCALE).to_pil()
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def extract_pages(filename: str, data: bytes, ocr: OcrFn | None = None) -> list[tuple[int, str]]:
    """Return (page_number, text) pairs. Text files are treated as a single page.

    If `ocr` is given, PDF pages without a text layer (scans) are rendered to images and passed to it.
    """
    suffix = filename.lower().rsplit(".", 1)[-1]
    if suffix == "pdf":
        reader = PdfReader(io.BytesIO(data))
        pages: list[tuple[int, str]] = []
        rendered = None
        try:
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if ocr and len(text.strip()) < OCR_MIN_CHARS:
                    if rendered is None:
                        import pypdfium2 as pdfium

                        rendered = pdfium.PdfDocument(data)
                    text = ocr(render_page_png(rendered, i))
                pages.append((i + 1, text))
        finally:
            if rendered is not None:
                rendered.close()
        return pages
    if suffix in ("txt", "md"):
        return [(1, data.decode("utf-8", errors="ignore"))]
    raise ValueError(f"Unsupported file type: {filename}")


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks, preferring paragraph/sentence boundaries."""
    if overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            window = text[start:end]
            for sep in ("\n\n", ". ", "\n", " "):
                cut = window.rfind(sep)
                if cut > chunk_size // 2:
                    end = start + cut + len(sep)
                    break
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def chunk_document(
    filename: str, data: bytes, chunk_size: int, overlap: int, ocr: OcrFn | None = None
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for page, text in extract_pages(filename, data, ocr):
        for piece in split_text(clean_text(text), chunk_size, overlap):
            chunks.append(Chunk(text=piece, source=filename, page=page, chunk_index=len(chunks)))
    return chunks
