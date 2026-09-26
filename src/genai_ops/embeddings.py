"""Deterministic local embeddings.

A portfolio stand-in for OCI GenAI embedding models: a hashed
bag-of-words vector with L2 normalisation. It is deterministic,
requires no network, and captures lexical similarity well enough to
exercise the retrieval stack end to end. Swap `HashingEmbedder` for a
real OCI client behind the same interface in production.
"""
from __future__ import annotations

import hashlib
import math
import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class HashingEmbedder:
    """Hashing-trick embedder: tokens map to fixed buckets."""

    def __init__(self, dimensions: int = 256):
        if dimensions < 8:
            raise ValueError("dimensions must be >= 8")
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dimensions
        for tok in tokenize(text):
            digest = hashlib.sha256(tok.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[bucket] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("vectors must have equal length")
    return sum(x * y for x, y in zip(a, b))
