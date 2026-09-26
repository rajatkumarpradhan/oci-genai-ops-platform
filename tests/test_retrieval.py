import unittest

from genai_ops.embeddings import HashingEmbedder
from genai_ops.retrieval import HybridRetriever, bm25_scores, reciprocal_rank_fusion
from genai_ops.vectorstore import VectorStore, VectorRecord


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.e = HashingEmbedder()
        self.store = VectorStore()
        docs = {
            "a": "OCI budgets send alert emails when spend crosses thresholds.",
            "b": "Protein folding uses deep learning models.",
            "c": "Budget alerts integrate with notification topics in OCI.",
        }
        for rid, text in docs.items():
            self.store.upsert(VectorRecord(rid, self.e.embed(text), text, {"doc_id": rid}))
        self.retriever = HybridRetriever(self.store, self.e)

    def test_bm25_prefers_matching_doc(self):
        scores = bm25_scores("budget alerts", {r.record_id: r.text for r in self.store._records.values()})
        best = max(scores, key=scores.get)
        self.assertIn(best, {"a", "c"})

    def test_rrf_fuses_rankings(self):
        fused = reciprocal_rank_fusion([["a", "b"], ["b", "a"]])
        self.assertAlmostEqual(fused["a"], fused["b"])

    def test_hybrid_returns_top_k(self):
        hits = self.retriever.retrieve("budget alerts in OCI", top_k=2)
        self.assertEqual(len(hits), 2)
        self.assertGreaterEqual(hits[0]["score"], hits[1]["score"])

    def test_empty_query_rejected(self):
        with self.assertRaises(ValueError):
            self.retriever.retrieve("   ")

    def test_empty_store_returns_nothing(self):
        empty = HybridRetriever(VectorStore(), self.e)
        self.assertEqual(empty.retrieve("anything"), [])


if __name__ == "__main__":
    unittest.main()
