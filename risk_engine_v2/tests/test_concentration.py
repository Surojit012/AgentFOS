import unittest

from risk_engine_v2.concentration import calculate_concentration_score
from risk_engine_v2.types import ConcentrationInput, DataProvenance


class ConcentrationScoreTest(unittest.TestCase):
    def test_top_five_buckets(self):
        cases = [(39.9, 20), (40, 15), (60, 15), (60.1, 10), (80, 10), (80.1, 5)]
        for concentration, expected in cases:
            with self.subTest(concentration=concentration):
                result = calculate_concentration_score(
                    ConcentrationInput(concentration, None, DataProvenance.LIVE)
                )
                self.assertEqual(result.score, expected)

    def test_invalid_over_100_is_insufficient_not_clamped(self):
        result = calculate_concentration_score(
            ConcentrationInput(120, "Low", DataProvenance.LIVE)
        )
        self.assertEqual(result.score, 5)
        self.assertEqual(result.provenance, DataProvenance.INSUFFICIENT)

    def test_issuer_fallback_is_degraded(self):
        result = calculate_concentration_score(
            ConcentrationInput(None, "Medium", DataProvenance.LIVE)
        )
        self.assertEqual(result.score, 15)
        self.assertEqual(result.provenance, DataProvenance.DEGRADED)


if __name__ == "__main__":
    unittest.main()
