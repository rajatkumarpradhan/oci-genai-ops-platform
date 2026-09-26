"""Document chunking strategies for retrieval pipelines.

Chunking is pure and deterministic: the same document always produces
the same chunk list, which keeps eval runs reproducible.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    doc_id: str
    index: int
    text: str
    metadata: dict = field(default_factory=dict)

    @property
    def chunk_id(self) -> str:
        return f"{self.doc_id}#{self.index}"


def fixed_chunks(text: str, size: int, overlap: int, doc_id: str) -> list[Chunk]:
    """Split text into overlapping fixed-size windows."""
    if size <= 0:
        raise ValueError("size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be >= 0 and < size")
    text = text.strip()
    if not text:
        return []
    chunks: list[Chunk] = []
    step = size - overlap
    pos = 0
    idx = 0
    while pos < len(text):
        window = text[pos:pos + size]
        chunks.append(Chunk(doc_id=doc_id, index=idx, text=window))
        idx += 1
        pos += step
    return chunks


def sentence_chunks(text: str, max_chars: int, doc_id: str) -> list[Chunk]:
    """Split text on sentence boundaries, packing sentences up to max_chars.

    A sentence longer than max_chars falls back to fixed-size splitting so
    no content is ever dropped.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    sentences = [s.strip() for s in _SENTENCE_RE.split(text.strip()) if s.strip()]
    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_len = 0
    idx = 0

    def flush() -> None:
        nonlocal buf, buf_len, idx
        if buf:
            chunks.append(Chunk(doc_id=doc_id, index=idx, text=" ".join(buf)))
            idx += 1
            buf, buf_len = [], 0

    for sent in sentences:
        if len(sent) > max_chars:
            flush()
            for piece in fixed_chunks(sent, max_chars, 0, doc_id):
                chunks.append(Chunk(doc_id=doc_id, index=idx, text=piece.text))
                idx += 1
            continue
        if buf_len + len(sent) + (1 if buf else 0) > max_chars:
            flush()
        buf.append(sent)
        buf_len += len(sent) + (1 if buf_len else 0)
    flush()
    return chunks
