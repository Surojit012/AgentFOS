import unittest

from risk_engine_v2.composite import calculate_composite_risk
from risk_engine_v2.tests.helpers import frozen_snapshot
from risk_engine_v2.types import DataProvenance, LiquidityInput, YieldSustainabilityInput


class CompositeRiskTest(unittest.TestCase):
    def test_composite_equals_sum_of_dimension_scores(self):
        result = calculate_composite_risk(frozen_snapshot())
        self.assertEqual(
            result.risk_score,
            sum(dimension.score for dimension in result.breakdown.values()),
        )
        self.assertIsInstance(result.risk_score, int)

    def test_confidence_downgrades_with_two_insufficient_dimensions(self):
        result = calculate_composite_risk(
            frozen_snapshot(
                liquidity=LiquidityInput(tvl=None, provenance=DataProvenance.LIVE),
                yield_sustainability=YieldSustainabilityInput(
                    rwa_yield=None,
                    treasury_yield=4,
                    provenance=DataProvenance.LIVE,
                ),
            )
        )
        self.assertEqual(result.overall_confidence, "low")


if __name__ == "__main__":
    unittest.main()
