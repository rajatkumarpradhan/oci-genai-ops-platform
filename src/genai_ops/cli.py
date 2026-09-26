"""Command line interface: ingest, query, eval, status, report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import Settings
from .eval import run_eval
from .pipeline import InjectionBlocked, RAGPipeline


def _load_settings(args) -> Settings:
    if getattr(args, "config", None):
        return Settings.load(args.config)
    return Settings()


def cmd_ingest(args) -> int:
    pipeline = RAGPipeline(_load_settings(args))
    docs_dir = Path(args.docs)
    if not docs_dir.is_dir():
        print(f"docs dir not found: {docs_dir}", file=sys.stderr)
        return 2
    total = 0
    for path in sorted(docs_dir.glob("*.md")) + sorted(docs_dir.glob("*.txt")):
        count = pipeline.ingest(path.stem, path.read_text(encoding="utf-8"))
        print(f"ingested {path.name}: {count} chunks")
        total += count
    if args.store:
        pipeline.store.save(args.store)
        print(f"saved {total} chunks to {args.store}")
    return 0


def cmd_query(args) -> int:
    pipeline = RAGPipeline(_load_settings(args))
    if args.store:
        from .vectorstore import VectorStore
        from .retrieval import HybridRetriever
        pipeline.store = VectorStore.load(args.store)
        pipeline.retriever = HybridRetriever(pipeline.store, pipeline.embedder)
    try:
        result = pipeline.query(args.question)
    except InjectionBlocked as exc:
        print(f"blocked: {exc}", file=sys.stderr)
        return 3
    print(result.answer)
    print("\ncitations:")
    for cid in result.citations:
        print(f"  - {cid}")
    print(f"\ntrace: {result.trace_id} | cost: {json.dumps(result.cost)}")
    return 0


def cmd_eval(args) -> int:
    pipeline = RAGPipeline(_load_settings(args))
    docs_dir = Path(args.docs)
    for path in sorted(docs_dir.glob("*.md")) + sorted(docs_dir.glob("*.txt")):
        pipeline.ingest(path.stem, path.read_text(encoding="utf-8"))
    report = run_eval(pipeline, args.golden)
    print(json.dumps(report.to_dict(), indent=2))
    return 0 if report.pass_rate >= args.min_pass else 1


def cmd_status(args) -> int:
    pipeline = RAGPipeline(_load_settings(args))
    if args.store:
        from .vectorstore import VectorStore
        pipeline.store = VectorStore.load(args.store)
    print(json.dumps(pipeline.status(), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="genai-ops", description=__doc__)
    parser.add_argument("--config", help="settings JSON path")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="chunk + embed a docs directory")
    p_ingest.add_argument("docs")
    p_ingest.add_argument("--store", help="persist vector store JSON here")
    p_ingest.set_defaults(func=cmd_ingest)

    p_query = sub.add_parser("query", help="ask a question against ingested docs")
    p_query.add_argument("question")
    p_query.add_argument("--store", help="load a persisted vector store")
    p_query.set_defaults(func=cmd_query)

    p_eval = sub.add_parser("eval", help="run the golden-set evaluation")
    p_eval.add_argument("docs")
    p_eval.add_argument("golden")
    p_eval.add_argument("--min-pass", type=float, default=0.8)
    p_eval.set_defaults(func=cmd_eval)

    p_status = sub.add_parser("status", help="print pipeline status/metrics")
    p_status.add_argument("--store")
    p_status.set_defaults(func=cmd_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
