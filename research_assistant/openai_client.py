"""Thin wrappers around the OpenAI API for embeddings and chat."""

from __future__ import annotations

import base64
from collections.abc import Iterator

from openai import OpenAI

from .config import Settings

OCR_PROMPT = (
    "Transcribe all text on this scanned document page exactly as written, preserving paragraph "
    "breaks. Output only the transcribed text, with no commentary. If the page has no text, output nothing."
)


def get_client(settings: Settings) -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your .env file (local) "
            "or to the app secrets (Streamlit Cloud)."
        )
    return OpenAI(api_key=settings.openai_api_key)


def embed_texts(client: OpenAI, model: str, texts: list[str], batch_size: int = 100) -> list[list[float]]:
    vectors: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        response = client.embeddings.create(model=model, input=texts[i : i + batch_size])
        vectors.extend(item.embedding for item in response.data)
    return vectors


def chat(client: OpenAI, model: str, messages: list[dict]) -> str:
    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content or ""


def ocr_image(client: OpenAI, model: str, png: bytes) -> str:
    """Read the text in a page image using the vision capability of the chat model."""
    url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    content = [{"type": "text", "text": OCR_PROMPT}, {"type": "image_url", "image_url": {"url": url}}]
    return chat(client, model, [{"role": "user", "content": content}])


def chat_stream(client: OpenAI, model: str, messages: list[dict]) -> Iterator[str]:
    stream = client.chat.completions.create(model=model, messages=messages, stream=True)
    for event in stream:
        if event.choices and event.choices[0].delta.content:
            yield event.choices[0].delta.content
