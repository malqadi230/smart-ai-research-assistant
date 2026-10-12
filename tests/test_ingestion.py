import pytest

from research_assistant.ingestion import chunk_document, clean_text, split_text


def test_split_respects_chunk_size_and_covers_text():
    text = " ".join(f"Sentence number {i}." for i in range(500))
    chunks = split_text(text, chunk_size=300, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 300 for c in chunks)
    assert chunks[0].startswith("Sentence number 0.")
    assert chunks[-1].endswith("Sentence number 499.")


def test_split_overlaps_consecutive_chunks():
    text = " ".join(f"word{i}" for i in range(400))
    a, b = split_text(text, chunk_size=200, overlap=60)[:2]
    assert a[-30:].split()[-1] in b


def test_split_short_text_is_single_chunk():
    assert split_text("hello world", 1000, 200) == ["hello world"]


def test_split_rejects_overlap_ge_size():
    with pytest.raises(ValueError):
        split_text("abc", 100, 100)


def test_clean_text_collapses_whitespace():
    assert clean_text("a   b\n\n\n\nc\x00") == "a b\n\nc"


def test_chunk_document_text_file_metadata():
    data = ("Paragraph. " * 300).encode()
    chunks = chunk_document("notes.txt", data, chunk_size=500, overlap=100)
    assert chunks and all(c.source == "notes.txt" and c.page == 1 for c in chunks)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    assert len({c.id for c in chunks}) == len(chunks)


def test_unsupported_type():
    with pytest.raises(ValueError):
        chunk_document("image.png", b"", 500, 100)


def _image_only_pdf() -> bytes:
    """A one-page PDF that is just a picture of text, like a scanned page."""
    import io

    from PIL import Image, ImageDraw

    img = Image.new("RGB", (600, 200), "white")
    ImageDraw.Draw(img).text((20, 80), "Scanned page text", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PDF")
    return buf.getvalue()


def test_scanned_page_without_ocr_has_no_text():
    assert chunk_document("scan.pdf", _image_only_pdf(), 500, 100) == []


def test_scanned_page_is_sent_to_ocr_as_png():
    seen = []

    def fake_ocr(png: bytes) -> str:
        seen.append(png)
        return "Text recovered by OCR"

    chunks = chunk_document("scan.pdf", _image_only_pdf(), 500, 100, ocr=fake_ocr)
    assert len(seen) == 1 and seen[0].startswith(b"\x89PNG")
    assert [(c.text, c.page) for c in chunks] == [("Text recovered by OCR", 1)]
