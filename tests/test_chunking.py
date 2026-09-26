import unittest

from genai_ops.chunking import fixed_chunks, sentence_chunks


class ChunkingTests(unittest.TestCase):
    def test_fixed_chunks_cover_text(self):
        text = "x" * 1000
        chunks = fixed_chunks(text, 300, 50, "d")
        self.assertEqual(chunks[0].chunk_id, "d#0")
        self.assertEqual(len(chunks), 4)
        self.assertEqual(chunks[0].text, text[:300])
        self.assertEqual(chunks[-1].text, text[750:])
        # every position covered: step = size - overlap
        for i, c in enumerate(chunks):
            self.assertEqual(c.text, text[i * 250:i * 250 + 300])

    def test_fixed_chunks_rejects_bad_overlap(self):
        with self.assertRaises(ValueError):
            fixed_chunks("abc", 10, 10, "d")

    def test_sentence_chunks_respect_boundaries(self):
        text = "First sentence here. Second sentence follows. Third one ends it."
        chunks = sentence_chunks(text, 40, "d")
        self.assertGreaterEqual(len(chunks), 2)
        self.assertTrue(all(len(c.text) <= 40 for c in chunks))
        self.assertEqual(" ".join(c.text for c in chunks), text)

    def test_sentence_chunks_fallback_for_long_sentence(self):
        text = "y" * 500
        chunks = sentence_chunks(text, 100, "d")
        self.assertEqual(len(chunks), 5)

    def test_empty_text_no_chunks(self):
        self.assertEqual(sentence_chunks("   ", 100, "d"), [])


if __name__ == "__main__":
    unittest.main()
