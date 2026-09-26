import unittest

from genai_ops.generation import MockOCIClient, OfflineExtractiveClient


class OfflineExtractiveTests(unittest.TestCase):
    def setUp(self):
        self.client = OfflineExtractiveClient()
        self.ctx = [
            {"record_id": "a#0", "text": "OCI budgets send alert emails when spend crosses thresholds. Tags drive showback."},
            {"record_id": "b#0", "text": "Bananas are berries but strawberries are not."},
        ]

    def test_answers_from_relevant_context(self):
        result = self.client.generate("How do OCI budgets alert?", self.ctx, 256)
        self.assertIn("budget", result.answer.lower())
        self.assertEqual(result.citations, ["a#0"])
        self.assertIn("[1]", result.answer)

    def test_refuses_without_context(self):
        result = self.client.generate("anything?", [], 256)
        self.assertIn("cannot answer", result.answer)

    def test_refuses_when_no_overlap(self):
        result = self.client.generate("zz qqq unrelated", self.ctx, 256)
        self.assertIn("do not contain", result.answer)

    def test_empty_question_rejected(self):
        with self.assertRaises(ValueError):
            self.client.generate(" ", self.ctx, 256)

    def test_mock_client_records_calls(self):
        mock = MockOCIClient()
        out = mock.generate("q", self.ctx, 100)
        self.assertEqual(len(mock.calls), 1)
        self.assertTrue(out.answer)


if __name__ == "__main__":
    unittest.main()
