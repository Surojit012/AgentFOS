import unittest

from risk_engine_v2.maturity import calculate_maturity_score
from risk_engine_v2.types import DataProvenance, MaturityInput


class MaturityScoreTest(unittest.TestCase):
    def test_boundaries_use_lower_bound_inclusive(self):
        cases = [
            ("2023-06-17", 1095, 20),
            ("2025-06-16", 365, 14),
            ("2025-12-18", 180, 8),
            ("2026-01-01", 166, 4),
        ]
        for launch_date, age_days, expected in cases:
            with self.subTest(age_days=age_days):
                result = calculate_maturity_score(
                    MaturityInput(
                        launch_date=launch_date,
                        as_of_date="2026-06-16",
                        provenance=DataProvenance.LIVE,
                    )
                )
                self.assertEqual(result.score, expected)
                self.assertEqual(result.details["age_days"], age_days)

    def test_invalid_date_is_insufficient(self):
        result = calculate_maturity_score(
            MaturityInput(
                launch_date=None,
                as_of_date="2026-06-16",
                provenance=DataProvenance.LIVE,
            )
        )
        self.assertEqual(result.score, 4)
        self.assertEqual(result.provenance, DataProvenance.INSUFFICIENT)


if __name__ == "__main__":
    unittest.main()
