"""Hybrid retrieval: sparse BM25-style scoring fused with dense vector
search using reciprocal rank fusion (RRF).

OCI's production shape pairs AI Vector Search with a lexical index;
this module mirrors that shape offline so ranking logic is testable.
"""
from __future__ import annotations

import math
from collections import defaultdict

from .embeddings import HashingEmbedder, tokenize
from .vectorstore import VectorStore


def bm25_scores(query: str, docs: dict[str, str], k1: float = 1.5, b: float = 0.75) -> dict[str, float]:
    """Classic BM25 over a small in-memory corpus."""
    q_tokens = tokenize(query)
    if not q_tokens or not docs:
        return {}
    tokenized = {doc_id: tokenize(text) for doc_id, text in docs.items()}
    avg_len = sum(len(t) for t in tokenized.values()) / max(len(tokenized), 1)
    # document frequency per query term
    df: dict[str, int] = defaultdict(int)
    for tokens in tokenized.values():
        for term in set(q_tokens) & set(tokens):
            df[term] += 1
    n_docs = len(tokenized)
    scores: dict[str, float] = {}
    for doc_id, tokens in tokenized.items():
        score = 0.0
        doc_len = len(tokens) or 1
        for term in q_tokens:
            tf = tokens.count(term)
            if tf == 0:
                continue
            idf = math.log(1 + (n_docs - df.get(term, 0) + 0.5) / (df.get(term, 0) + 0.5))
            denom = tf + k1 * (1 - b + b * doc_len / (avg_len or 1))
            score += idf * (tf * (k1 + 1)) / denom
        scores[doc_id] = score
    return scores


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    """Fuse ranked id lists into a single score map."""
    fused: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            fused[doc_id] += 1.0 / (k + rank)
    return dict(fused)


class HybridRetriever:
    def __init__(self, store: VectorStore, embedder: HashingEmbedder):
        self.store = store
        self.embedder = embedder

    def retrieve(self, query: str, top_k: int = 4, min_score: float = 0.0) -> list[dict]:
        """Return ranked hits with fused scores and source text."""
        if not query.strip():
            raise ValueError("query must not be empty")
        if len(self.store) == 0:
            return []
        corpus = {rec.record_id: rec.text for rec in (self.store.get(rid) for rid in self._ids()) if rec}
        bm25 = bm25_scores(query, corpus)
        bm25_ranking = [doc_id for doc_id, _ in sorted(bm25.items(), key=lambda kv: kv[1], reverse=True)]
        vector_hits = self.store.search(self.embedder.embed(query), top_k=len(corpus))
        vector_ranking = [rec.record_id for rec, _ in vector_hits]
        fused = reciprocal_rank_fusion([vector_ranking, bm25_ranking])
        ordered = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)
        hits = []
        for record_id, score in ordered[:top_k]:
            if score < min_score:
                continue
            rec = self.store.get(record_id)
            if rec is None:
                continue
            hits.append({
                "record_id": record_id,
                "score": score,
                "text": rec.text,
                "metadata": rec.metadata,
                "vector_score": dict((r.record_id, s) for r, s in vector_hits).get(record_id, 0.0),
                "bm25_score": bm25.get(record_id, 0.0),
            })
        return hits

    def _ids(self) -> list[str]:
        return [rec.record_id for rec in self.store._records.values()]
