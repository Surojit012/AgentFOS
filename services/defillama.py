"""
DefiLlama API client — fetches TVL + APY data for RWA protocols.

Real async httpx calls to DefiLlama's public API.
Falls back silently to MOCK_PROTOCOL_DATA from config.py if API fails.
"""

import httpx
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from config import PROTOCOLS, MOCK_PROTOCOL_DATA


DEFILLAMA_TVL_BASE = "https://api.llama.fi/protocol"
DEFILLAMA_YIELDS_URL = "https://yields.llama.fi/pools"
DEFILLAMA_TVL_HISTORICAL = "https://api.llama.fi/v2/historicalChainTvl"

# Map our protocol slugs to known DefiLlama pool project identifiers
_SLUG_TO_PROJECT = {
    "ondo": "ondo-finance",
    "zoth": "zoth",
    "maple-finance": "maple-finance",
    "centrifuge": "centrifuge",
    "backed-finance": "backed-finance",
    "opentrade": "opentrade",
}


def _calculate_age_days(launch_year: int) -> int:
    """Calculate days since protocol launch (Jan 1 of launch_year)."""
    launch_date = datetime(launch_year, 1, 1, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return (now - launch_date).days


async def _fetch_tvl_for_protocol(client: httpx.AsyncClient, slug: str) -> Optional[float]:
    """Fetch current TVL from DefiLlama protocol endpoint."""
    url = f"{DEFILLAMA_TVL_BASE}/{slug}"
    resp = await client.get(url, timeout=10.0)
    resp.raise_for_status()
    data = resp.json()
    # currentChainTvls contains chain-level TVL; total is in "tvl" field
    if "currentChainTvls" in data:
        return sum(v for v in data["currentChainTvls"].values() if isinstance(v, (int, float)))
    # Fallback: use last entry in tvl timeseries
    if "tvl" in data and isinstance(data["tvl"], list) and len(data["tvl"]) > 0:
        return float(data["tvl"][-1].get("totalLiquidityUSD", 0))
    return None


async def _fetch_tvl_change_30d(client: httpx.AsyncClient, slug: str) -> Optional[float]:
    """Fetch TVL change over 30 days from DefiLlama protocol endpoint."""
    url = f"{DEFILLAMA_TVL_BASE}/{slug}"
    resp = await client.get(url, timeout=10.0)
    resp.raise_for_status()
    data = resp.json()
    tvl_series = data.get("tvl", [])
    if not isinstance(tvl_series, list) or len(tvl_series) < 2:
        return None
    current_tvl = float(tvl_series[-1].get("totalLiquidityUSD", 0))
    # Find entry ~30 days ago
    target_ts = datetime.now(timezone.utc).timestamp() - (30 * 86400)
    closest_entry = min(tvl_series, key=lambda e: abs(e.get("date", 0) - target_ts))
    old_tvl = float(closest_entry.get("totalLiquidityUSD", 0))
    if old_tvl == 0:
        return None
    return round(((current_tvl - old_tvl) / old_tvl) * 100, 2)


async def _fetch_apy_for_slug(client: httpx.AsyncClient, slug: str) -> Optional[float]:
    """Fetch APY from DefiLlama yields endpoint by matching project name."""
    resp = await client.get(DEFILLAMA_YIELDS_URL, timeout=15.0)
    resp.raise_for_status()
    data = resp.json()
    pools = data.get("data", [])
    project_name = _SLUG_TO_PROJECT.get(slug, slug)
    # Find best matching pool for this project
    matching_pools = [
        p for p in pools
        if p.get("project", "").lower() == project_name.lower()
    ]
    if not matching_pools:
        return None
    # Return highest APY pool for this project
    best = max(matching_pools, key=lambda p: p.get("apy", 0))
    return round(float(best.get("apy", 0)), 2)


async def fetch_protocol_data(protocol_key: str) -> Dict[str, Any]:
    """
    Fetch TVL + APY for a single protocol from DefiLlama.
    Falls back silently to MOCK_PROTOCOL_DATA if API fails.

    Returns: {"tvl": float, "apy": float, "tvl_change_30d": float}
    """
    protocol_meta = PROTOCOLS.get(protocol_key)
    if not protocol_meta:
        return MOCK_PROTOCOL_DATA.get(protocol_key, {"tvl": 0, "apy": 0, "tvl_change_30d": 0})

    slug = protocol_meta["slug"]
    data_source = "live"

    try:
        async with httpx.AsyncClient() as client:
            tvl = await _fetch_tvl_for_protocol(client, slug)
            apy = await _fetch_apy_for_slug(client, slug)
            tvl_change = await _fetch_tvl_change_30d(client, slug)

            # If we got at least TVL or APY, build result with mock filling gaps
            mock = MOCK_PROTOCOL_DATA.get(protocol_key, {})
            result = {
                "tvl": tvl if tvl is not None else mock.get("tvl", 0),
                "apy": apy if apy is not None else mock.get("apy", 0),
                "tvl_change_30d": tvl_change if tvl_change is not None else mock.get("tvl_change_30d", 0),
                "data_source": data_source if (tvl is not None or apy is not None) else "mock",
            }
            return result
    except Exception:
        # Silent fallback to mock data — demo must never crash
        mock = MOCK_PROTOCOL_DATA.get(protocol_key, {"tvl": 0, "apy": 0, "tvl_change_30d": 0})
        return {**mock, "data_source": "mock"}


async def fetch_all_protocols() -> Dict[str, Dict[str, Any]]:
    """
    Fetch TVL + APY data for all 6 protocols.
    Returns dict keyed by protocol_key with tvl, apy, tvl_change_30d, data_source.
    """
    results = {}
    for key in PROTOCOLS:
        results[key] = await fetch_protocol_data(key)
    return results
