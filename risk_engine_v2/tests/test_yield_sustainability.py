import unittest

from risk_engine_v2.types import DataProvenance, YieldSustainabilityInput
from risk_engine_v2.yield_sustainability import calculate_yield_sustainability_score


class YieldSustainabilityScoreTest(unittest.TestCase):
    def test_spread_buckets_include_negative_spread(self):
        cases = [(-1, 15), (2, 15), (2.01, 12), (5, 12), (5.01, 8), (8, 8), (8.01, 4)]
        for spread, expected in cases:
            with self.subTest(spread=spread):
                result = calculate_yield_sustainability_score(
                    YieldSustainabilityInput(
                        rwa_yield=4 + spread,
                        treasury_yield=4,
                        provenance=DataProvenance.LIVE,
                    )
                )
                self.assertEqual(result.score, expected)

    def test_missing_input_is_insufficient(self):
        result = calculate_yield_sustainability_score(
            YieldSustainabilityInput(None, 4, DataProvenance.LIVE)
        )
        self.assertEqual(result.score, 4)
        self.assertEqual(result.provenance, DataProvenance.INSUFFICIENT)


if __name__ == "__main__":
    unittest.main()
