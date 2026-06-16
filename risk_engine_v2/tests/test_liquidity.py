import unittest

from risk_engine_v2.liquidity import calculate_liquidity_score
from risk_engine_v2.types import DataProvenance, LiquidityInput


class LiquidityScoreTest(unittest.TestCase):
    def test_tvl_buckets(self):
        cases = [
            (500_000_001, 10),
            (500_000_000, 7),
            (100_000_000, 7),
            (10_000_000, 4),
            (9_999_999, 1),
        ]
        for tvl, expected in cases:
            with self.subTest(tvl=tvl):
                result = calculate_liquidity_score(
                    LiquidityInput(tvl=tvl, provenance=DataProvenance.LIVE)
                )
                self.assertEqual(result.score, expected)

    def test_missing_zero_and_negative_are_insufficient(self):
        for tvl in (None, 0, -1):
            with self.subTest(tvl=tvl):
                result = calculate_liquidity_score(
                    LiquidityInput(tvl=tvl, provenance=DataProvenance.LIVE)
                )
                self.assertEqual(result.score, 1)
                self.assertEqual(result.provenance, DataProvenance.INSUFFICIENT)


if __name__ == "__main__":
    unittest.main()
