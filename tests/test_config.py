import unittest

from genai_ops.config import Settings


class ConfigTests(unittest.TestCase):
    def test_defaults(self):
        s = Settings()
        self.assertEqual(s.retrieval.top_k, 4)
        self.assertTrue(s.guardrails.redact_pii)
        self.assertEqual(s.cost.monthly_budget_units, 100.0)

    def test_from_dict_applies_overrides(self):
        s = Settings.from_dict({"retrieval": {"top_k": 7}, "cost": {"monthly_budget_units": 5}})
        self.assertEqual(s.retrieval.top_k, 7)
        self.assertEqual(s.cost.monthly_budget_units, 5)

    def test_unknown_section_rejected(self):
        with self.assertRaises(ValueError):
            Settings.from_dict({"mystery": {}})

    def test_unknown_key_rejected(self):
        with self.assertRaises(ValueError):
            Settings.from_dict({"retrieval": {"nope": 1}})

    def test_round_trip(self):
        s = Settings.from_dict({"pipeline": {"name": "demo"}})
        self.assertEqual(s.to_dict()["pipeline"]["name"], "demo")


if __name__ == "__main__":
    unittest.main()
