from typing import Any, Dict

from config import MOCK_PROTOCOL_DATA, MOCK_TREASURY_RATE


def get_mock_market_inputs(protocol_key: str) -> Dict[str, Any]:
    """Return clearly marked mock market inputs for a protocol snapshot."""
    mock = MOCK_PROTOCOL_DATA.get(protocol_key, {})
    return {
        "tvl": mock.get("tvl"),
        "apy": mock.get("apy"),
        "treasury_yield": MOCK_TREASURY_RATE,
        "data_source": "mock",
    }
