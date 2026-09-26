"""Generation clients.

`LLMClient` is the seam where a real OCI Generative AI client would
plug in (cohere / llama on dedicated AI clusters). This portfolio ships
an offline extractive client: it answers strictly from retrieved
context and must cite the chunks it used, which keeps the whole RAG
loop testable without a tenancy.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol

_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass
class GenerationResult:
    answer: str
    citations: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


class LLMClient(Protocol):
    def generate(self, question: str, contexts: list[dict], max_tokens: int) -> GenerationResult:
        ...


class MissingCitationError(Exception):
    pass


class OfflineExtractiveClient:
    """Answer by extracting the most question-relevant sentences from the
    retrieved contexts, with mandatory [n] citations."""

    def __init__(self, require_citations: bool = True) -> None:
        self.require_citations = require_citations

    def generate(self, question: str, contexts: list[dict], max_tokens: int) -> GenerationResult:
        if not question.strip():
            raise ValueError("question must not be empty")
        if not contexts:
            return GenerationResult(answer="No supporting context was retrieved; I cannot answer from the available documents.")
        q_terms = set(_TOKEN_RE.findall(question.lower())) - _STOPWORDS
        scored: list[tuple[float, str, int]] = []
        for idx, ctx in enumerate(contexts, start=1):
            for sent in re.split(r"(?<=[.!?])\s+", ctx["text"]):
                sent = sent.strip()
                if len(sent) < 20:
                    continue
                terms = set(_TOKEN_RE.findall(sent.lower()))
                overlap = len(q_terms & terms) / max(len(q_terms), 1)
                if overlap > 0:
                    scored.append((overlap, sent, idx))
        if not scored:
            return GenerationResult(answer="The retrieved documents do not contain an answer to this question.")
        scored.sort(key=lambda item: item[0], reverse=True)
        picked: list[str] = []
        used: set[int] = set()
        budget_chars = max_tokens * 4
        total = 0
        for _, sent, idx in scored:
            if idx in used or total + len(sent) > budget_chars:
                continue
            picked.append(f"{sent} [{idx}]")
            used.add(idx)
            total += len(sent)
            if len(picked) >= 3:
                break
        if not picked:
            return GenerationResult(answer="The retrieved documents do not contain an answer to this question.")
        citations = [contexts[i - 1]["record_id"] for i in sorted(used)]
        answer = " ".join(picked)
        if self.require_citations and not citations:
            raise MissingCitationError("answer produced without citations")
        return GenerationResult(
            answer=answer,
            citations=citations,
            input_tokens=(len(question) + sum(len(c["text"]) for c in contexts)) // 4,
            output_tokens=len(answer) // 4,
        )


class MockOCIClient:
    """Canned-response client for tests and demos of the OCI call path."""

    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self.responses = responses or {}
        self.calls: list[dict] = []

    def generate(self, question: str, contexts: list[dict], max_tokens: int) -> GenerationResult:
        self.calls.append({"question": question, "contexts": len(contexts), "max_tokens": max_tokens})
        body = self.responses.get(question, f"Mock OCI GenAI answer grounded in {len(contexts)} context(s). [1]")
        return GenerationResult(
            answer=body,
            citations=[contexts[0]["record_id"]] if contexts else [],
            input_tokens=(len(question) + sum(len(c["text"]) for c in contexts)) // 4,
            output_tokens=len(body) // 4,
        )


_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "of", "to", "in", "on", "for",
    "and", "or", "how", "what", "which", "when", "where", "why", "does", "do",
    "did", "can", "could", "should", "would", "with", "from", "by", "at", "as",
    "it", "this", "that", "these", "those", "be", "been", "being",
}
