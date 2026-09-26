"""In-memory vector store with JSON persistence.

Stands in for Oracle Database 23ai AI Vector Search in this portfolio:
the same upsert/search/persist lifecycle, at laptop scale.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

from .embeddings import cosine


@dataclass
class VectorRecord:
    record_id: str
    vector: list[float]
    text: str
    metadata: dict


class VectorStore:
    def __init__(self) -> None:
        self._records: dict[str, VectorRecord] = {}

    def __len__(self) -> int:
        return len(self._records)

    def upsert(self, record: VectorRecord) -> None:
        if not record.record_id:
            raise ValueError("record_id required")
        self._records[record.record_id] = record

    def upsert_many(self, records: list[VectorRecord]) -> int:
        for rec in records:
            self.upsert(rec)
        return len(records)

    def get(self, record_id: str) -> VectorRecord | None:
        return self._records.get(record_id)

    def search(self, query_vector: list[float], top_k: int = 4) -> list[tuple[VectorRecord, float]]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        scored = [(rec, cosine(query_vector, rec.vector)) for rec in self._records.values()]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]

    def save(self, path: str | Path) -> None:
        payload = [asdict(rec) for rec in self._records.values()]
        Path(path).write_text(json.dumps(payload, indent=1), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "VectorStore":
        store = cls()
        for raw in json.loads(Path(path).read_text(encoding="utf-8")):
            store.upsert(VectorRecord(**raw))
        return store
