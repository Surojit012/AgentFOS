import json
import unittest

from risk_engine_v2.composite import calculate_composite_risk
from risk_engine_v2.tests.helpers import frozen_snapshot


class DeterminismTest(unittest.TestCase):
    def test_same_snapshot_replays_byte_identical_json(self):
        snapshot = frozen_snapshot()
        first = json.dumps(calculate_composite_risk(snapshot).to_api_dict(), sort_keys=True)
        second = json.dumps(calculate_composite_risk(snapshot).to_api_dict(), sort_keys=True)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
