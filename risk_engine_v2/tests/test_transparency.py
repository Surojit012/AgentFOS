import unittest

from risk_engine_v2.transparency import calculate_transparency_score
from risk_engine_v2.types import DataProvenance, TransparencyInput


class TransparencyScoreTest(unittest.TestCase):
    def test_audit_age_buckets(self):
        fresh = calculate_transparency_score(
            TransparencyInput("Audited", "2026-01-01", "2026-06-16", True, True, DataProvenance.LIVE)
        )
        stale = calculate_transparency_score(
            TransparencyInput("Audited", "2024-12-01", "2026-06-16", True, True, DataProvenance.LIVE)
        )
        expired = calculate_transparency_score(
            TransparencyInput("Audited", "2023-01-01", "2026-06-16", True, True, DataProvenance.LIVE)
        )
        self.assertEqual(fresh.score, 20)
        self.assertEqual(stale.score, 16)
        self.assertEqual(expired.score, 10)

    def test_no_evidence_gets_floor_and_insufficient(self):
        result = calculate_transparency_score(
            TransparencyInput("Unaudited", None, "2026-06-16", False, False, DataProvenance.LIVE)
        )
        self.assertEqual(result.score, 1)
        self.assertEqual(result.provenance, DataProvenance.INSUFFICIENT)


if __name__ == "__main__":
    unittest.main()
