import json
import os
import tempfile
import unittest

from genai_ops.eval import run_eval
from genai_ops.observability import MetricsRegistry, StructuredLogger, Trace
from genai_ops.pipeline import RAGPipeline


class ObservabilityTests(unittest.TestCase):
    def test_counters_and_timers(self):
        reg = MetricsRegistry()
        reg.increment("requests")
        reg.increment("requests", 2)
        with reg.timed("op_ms"):
            pass
        snap = reg.snapshot()
        self.assertEqual(snap["counters"]["requests"], 3.0)
        self.assertEqual(snap["timers"]["op_ms"]["count"], 1)

    def test_tagged_metrics_separate(self):
        reg = MetricsRegistry()
        reg.increment("hits", route="a")
        reg.increment("hits", route="b")
        self.assertEqual(len(reg.snapshot()["counters"]), 2)

    def test_trace_records_error_spans(self):
        trace = Trace()
        with self.assertRaises(RuntimeError):
            with trace.span("boom"):
                raise RuntimeError("x")
        self.assertEqual(trace.spans[0]["error"], "RuntimeError")

    def test_structured_logger_json_lines(self):
        logger = StructuredLogger()
        logger.info("hello", trace_id="t1")
        line = logger.as_json_lines()
        self.assertEqual(json.loads(line)["message"], "hello")


class EvalHarnessTests(unittest.TestCase):
    def test_golden_eval_passes(self):
        pipeline = RAGPipeline()
        with tempfile.TemporaryDirectory() as tmp:
            golden = os.path.join(tmp, "golden.json")
            with open(golden, "w") as fh:
                json.dump([{"question": "What is OCI Generative AI?", "expected_doc": "genai"}], fh)
            pipeline.ingest("genai", "OCI Generative AI is a fully managed service. It hosts Cohere and Meta Llama models.")
            report = run_eval(pipeline, golden, faithfulness_floor=0.2)
        self.assertEqual(report.pass_rate, 1.0)
        self.assertEqual(report.recall_at_k, 1.0)

    def test_empty_golden_rejected(self):
        pipeline = RAGPipeline()
        with tempfile.TemporaryDirectory() as tmp:
            golden = os.path.join(tmp, "golden.json")
            with open(golden, "w") as fh:
                json.dump([], fh)
            with self.assertRaises(ValueError):
                run_eval(pipeline, golden)


if __name__ == "__main__":
    unittest.main()
