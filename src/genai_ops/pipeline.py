"""RAG pipeline orchestration.

Stages: guard(in) -> retrieve -> generate -> guard(out) -> cost track,
each wrapped in a trace span and a metrics timer. The pipeline is the
unit under test for the whole toolkit.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .chunking import sentence_chunks
from .config import Settings
from .costguard import CostGuard, UsageRecord
from .embeddings import HashingEmbedder
from .generation import GenerationResult, OfflineExtractiveClient
from .guardrails import redact_pii, screen_injection
from .observability import MetricsRegistry, StructuredLogger, Trace
from .retrieval import HybridRetriever
from .vectorstore import VectorStore, VectorRecord


class InjectionBlocked(Exception):
    pass


@dataclass
class QueryResult:
    answer: str
    citations: list[str]
    retrieved: list[dict]
    trace_id: str
    cost: dict
    guardrail_events: list[str] = field(default_factory=list)


class RAGPipeline:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.embedder = HashingEmbedder()
        self.store = VectorStore()
        self.retriever = HybridRetriever(self.store, self.embedder)
        self.client = OfflineExtractiveClient(require_citations=self.settings.generation.require_citations)
        self.cost_guard = CostGuard(
            monthly_budget_units=self.settings.cost.monthly_budget_units,
            warn_fraction=self.settings.cost.warn_fraction,
            input_price=self.settings.cost.input_token_price,
            output_price=self.settings.cost.output_token_price,
        )
        self.metrics = MetricsRegistry(namespace=self.settings.observability.metrics_namespace)
        self.logger = StructuredLogger(level=self.settings.observability.log_level)

    def ingest(self, doc_id: str, text: str) -> int:
        """Chunk, embed and upsert one document. Returns chunk count."""
        if not doc_id:
            raise ValueError("doc_id required")
        with self.metrics.timed("ingest_ms"):
            chunks = sentence_chunks(text, self.settings.pipeline.chunk_size, doc_id)
            records = [
                VectorRecord(
                    record_id=chunk.chunk_id,
                    vector=self.embedder.embed(chunk.text),
                    text=chunk.text,
                    metadata={"doc_id": doc_id, "chunk_index": chunk.index},
                )
                for chunk in chunks
            ]
            self.store.upsert_many(records)
        self.metrics.increment("documents_ingested")
        self.metrics.increment("chunks_ingested", len(records))
        self.logger.info("document ingested", doc_id=doc_id, chunks=len(records))
        return len(records)

    def query(self, question: str) -> QueryResult:
        trace = Trace()
        guardrail_events: list[str] = []
        with trace.span("guard_in"):
            safe_question = question
            if self.settings.guardrails.block_injection:
                report = screen_injection(question)
                if report.blocked:
                    self.metrics.increment("injection_blocked")
                    self.logger.warning("prompt injection blocked", matched=",".join(report.matched), trace_id=trace.trace_id)
                    raise InjectionBlocked(f"prompt-injection pattern matched: {report.matched}")
            if self.settings.guardrails.redact_pii:
                redaction = redact_pii(question)
                if redaction.redacted:
                    guardrail_events.append(f"input_pii_redacted:{sorted(redaction.redactions)}")
                    safe_question = redaction.text
            if len(safe_question) > self.settings.guardrails.max_input_chars:
                raise ValueError("question exceeds max_input_chars")
        with trace.span("retrieve"):
            hits = self.retriever.retrieve(
                safe_question,
                top_k=self.settings.retrieval.top_k,
                min_score=self.settings.retrieval.min_score,
            )
            self.metrics.increment("queries")
            self.metrics.observe_ms("retrieval_candidates", len(hits))
        with trace.span("generate"):
            result: GenerationResult = self.client.generate(
                safe_question, hits, self.settings.pipeline.max_answer_tokens)
        with trace.span("guard_out"):
            answer = result.answer
            if self.settings.guardrails.redact_pii:
                redaction = redact_pii(answer)
                if redaction.redacted:
                    guardrail_events.append(f"output_pii_redacted:{sorted(redaction.redactions)}")
                    answer = redaction.text
        with trace.span("cost"):
            cost = self.cost_guard.track(UsageRecord(result.input_tokens, result.output_tokens))
            if cost["warning"]:
                self.metrics.increment("budget_warnings")
                self.logger.warning("budget warning threshold crossed", spent=cost["spent"], trace_id=trace.trace_id)
        self.logger.info("query answered", citations=len(result.citations), trace_id=trace.trace_id)
        return QueryResult(
            answer=answer,
            citations=result.citations,
            retrieved=hits,
            trace_id=trace.trace_id,
            cost=cost,
            guardrail_events=guardrail_events,
        )

    def status(self) -> dict:
        return {
            "documents": self.metrics.snapshot()["counters"].get("documents_ingested", 0),
            "chunks": len(self.store),
            "cost": self.cost_guard.summary(),
            "metrics": self.metrics.snapshot(),
        }
