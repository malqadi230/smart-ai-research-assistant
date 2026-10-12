"""Document summaries and cross-document insight generation (map-reduce over chunks)."""

from __future__ import annotations

from openai import OpenAI

from .openai_client import chat

SECTION_CHARS = 12_000

SECTION_PROMPT = "Summarize this section of a research document in 5-8 concise bullet points, keeping key facts, numbers and conclusions."

FINAL_SUMMARY_PROMPT = """Combine these section summaries into one research summary with the headings:
## Overview
## Key Findings
## Methodology (if applicable)
## Conclusions
Keep it factual and concise."""

INSIGHTS_PROMPT = """You are given summaries of several research documents.
Produce:
## Common Themes
## Points of Agreement
## Contradictions or Differences
## Gaps & Open Questions
## Suggested Next Steps
Reference documents by name."""


def _group(chunks: list[str], limit: int) -> list[str]:
    sections, current = [], ""
    for chunk in chunks:
        if current and len(current) + len(chunk) > limit:
            sections.append(current)
            current = ""
        current += chunk + "\n\n"
    if current:
        sections.append(current)
    return sections


def summarize_document(client: OpenAI, model: str, chunks: list[str]) -> str:
    sections = _group(chunks, SECTION_CHARS)
    partials = [
        chat(client, model, [{"role": "system", "content": SECTION_PROMPT}, {"role": "user", "content": s}])
        for s in sections
    ]
    return chat(
        client,
        model,
        [{"role": "system", "content": FINAL_SUMMARY_PROMPT}, {"role": "user", "content": "\n\n".join(partials)}],
    )


def generate_insights(client: OpenAI, model: str, summaries: dict[str, str]) -> str:
    body = "\n\n".join(f"### {name}\n{summary}" for name, summary in summaries.items())
    return chat(client, model, [{"role": "system", "content": INSIGHTS_PROMPT}, {"role": "user", "content": body}])
