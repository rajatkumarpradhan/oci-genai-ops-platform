import unittest

from genai_ops.embeddings import HashingEmbedder, cosine, tokenize
from genai_ops.vectorstore import VectorStore, VectorRecord


class EmbeddingTests(unittest.TestCase):
    def test_deterministic_and_normalized(self):
        e = HashingEmbedder()
        v1 = e.embed("oracle cloud infrastructure")
        v2 = e.embed("oracle cloud infrastructure")
        self.assertEqual(v1, v2)
        self.assertAlmostEqual(sum(x * x for x in v1), 1.0, places=6)

    def test_similar_texts_score_higher(self):
        e = HashingEmbedder()
        a = e.embed("budget alerts for cloud spending")
        b = e.embed("cloud spending budget alerts")
        c = e.embed("protein folding research paper")
        self.assertGreater(cosine(a, b), cosine(a, c))

    def test_tokenize_lowercases(self):
        self.assertEqual(tokenize("OCI GenAI 2026"), ["oci", "genai", "2026"])

    def test_dimensions_floor(self):
        with self.assertRaises(ValueError):
            HashingEmbedder(dimensions=4)


class VectorStoreTests(unittest.TestCase):
    def setUp(self):
        self.e = HashingEmbedder()
        self.store = VectorStore()

    def test_upsert_and_search_order(self):
        self.store.upsert(VectorRecord("a", self.e.embed("apple pie recipe"), "apple pie recipe", {}))
        self.store.upsert(VectorRecord("b", self.e.embed("quantum computing"), "quantum computing", {}))
        hits = self.store.search(self.e.embed("apple pie"), 2)
        self.assertEqual(hits[0][0].record_id, "a")

    def test_persistence_round_trip(self):
        import tempfile, os
        self.store.upsert(VectorRecord("a", self.e.embed("hello"), "hello", {"k": 1}))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "store.json")
            self.store.save(path)
            loaded = VectorStore.load(path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded.get("a").metadata["k"], 1)

    def test_search_requires_positive_k(self):
        with self.assertRaises(ValueError):
            self.store.search([0.0] * 256, 0)


if __name__ == "__main__":
    unittest.main()
