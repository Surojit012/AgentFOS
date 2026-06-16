import unittest

from skills.risk import RiskEngine


class BackwardCompatibilityTest(unittest.TestCase):
    def test_risk_response_keeps_top_level_int_score(self):
        response = RiskEngine().evaluate("ondo", 1_000_000_000, apy=4.7, data_source="mock")
        self.assertIsInstance(response.risk_score, int)
        self.assertGreaterEqual(response.risk_score, 0)
        self.assertLessEqual(response.risk_score, 100)
        self.assertEqual(response.schema_version, "2.0")
        self.assertIn("breakdown", response.factors)


if __name__ == "__main__":
    unittest.main()
