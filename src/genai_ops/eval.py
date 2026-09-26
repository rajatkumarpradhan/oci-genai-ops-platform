"""Golden-set evaluation harness.

Scores a pipeline against a fixed Q/A set on retrieval recall@k,
citation coverage, and answer faithfulness (token overlap between the
answer and the cited source chunks). Runs offline and deterministically,
so CI can gate on quality regressions.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


@dataclass
class EvalCaseResult:
    question: str
    recall_hit: bool
    citation_coverage: float
    faithfulness: float
    passed: bool
    detail: dict = field(default_factory=dict)


@dataclass
class EvalReport:
    total: int
    passed: int
    recall_at_k: float
    mean_citation_coverage: float
    mean_faithfulness: float
    cases: list = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return self.passed / max(self.total, 1)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "passed": self.passed,
            "pass_rate": round(self.pass_rate, 3),
            "recall_at_k": round(self.recall_at_k, 3),
            "mean_citation_coverage": round(self.mean_citation_coverage, 3),
            "mean_faithfulness": round(self.mean_faithfulness, 3),
            "cases": [c.__dict__ for c in self.cases],
        }


def run_eval(pipeline, golden_path: str | Path, faithfulness_floor: float = 0.35) -> EvalReport:
    cases = json.loads(Path(golden_path).read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError("golden set must be a non-empty list")
    results: list[EvalCaseResult] = []
    for case in cases:
        question = case["question"]
        expected_doc = case["expected_doc"]
        result = pipeline.query(question)
        retrieved_docs = {hit["metadata"].get("doc_id") for hit in result.retrieved}
        recall_hit = expected_doc in retrieved_docs
        cited_chunks = [pipeline.store.get(cid) for cid in result.citations]
        cited_chunks = [c for c in cited_chunks if c]
        cited_docs = {c.metadata.get("doc_id") for c in cited_chunks}
        citation_coverage = 1.0 if expected_doc in cited_docs else 0.0
        answer_tokens = _tokens(result.answer)
        source_tokens = set().union(*(_tokens(c.text) for c in cited_chunks)) if cited_chunks else set()
        faithfulness = (len(answer_tokens & source_tokens) / max(len(answer_tokens), 1)) if source_tokens else 0.0
        passed = recall_hit and citation_coverage > 0 and faithfulness >= faithfulness_floor
        results.append(EvalCaseResult(
            question=question,
            recall_hit=recall_hit,
            citation_coverage=citation_coverage,
            faithfulness=round(faithfulness, 3),
            passed=passed,
            detail={"citations": result.citations, "trace_id": result.trace_id},
        ))
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    return EvalReport(
        total=total,
        passed=passed,
        recall_at_k=sum(1 for r in results if r.recall_hit) / total,
        mean_citation_coverage=sum(r.citation_coverage for r in results) / total,
        mean_faithfulness=sum(r.faithfulness for r in results) / total,
        cases=results,
    )
