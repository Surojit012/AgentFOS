"""
TradFi benchmark data — Treasury yields from FRED, RWA market average APY.

Uses fredapi for FRED Treasury data (not fedfred).
Falls back silently to MOCK constants from config.py if APIs fail.
"""

from config import (
    settings,
    FRED_SERIES,
    MOCK_TREASURY_RATE,
    MOCK_RWA_AVG_APY,
    MOCK_PROTOCOL_DATA,
)
from services.defillama import fetch_all_protocols


def fetch_treasury_rate() -> float:
    """
    Fetch 10Y US Treasury rate from FRED using fredapi.

    Returns: float — current 10Y Treasury yield (e.g. 4.25)
    Falls back to MOCK_TREASURY_RATE if API key missing or request fails.
    """
    try:
        if not settings.FRED_API_KEY:
            return MOCK_TREASURY_RATE

        from fredapi import Fred
        fred = Fred(api_key=settings.FRED_API_KEY)
        series = fred.get_series(FRED_SERIES["treasury_10y"])

        # Get latest non-NaN value
        series = series.dropna()
        if series.empty:
            return MOCK_TREASURY_RATE

        return round(float(series.iloc[-1]), 2)
    except Exception:
        # Silent fallback — demo must never crash
        return MOCK_TREASURY_RATE


async def fetch_rwa_avg_apy() -> float:
    """
    Calculate average APY across our 6 RWA protocols.

    Tries live DefiLlama data first, falls back to mock averages.
    Returns: float — average APY across all 6 protocols.
    """
    try:
        protocol_data = await fetch_all_protocols()

        apys = [
            data.get("apy", 0)
            for data in protocol_data.values()
            if data.get("apy", 0) > 0
        ]

        if not apys:
            return MOCK_RWA_AVG_APY

        return round(sum(apys) / len(apys), 2)
    except Exception:
        # Silent fallback — demo must never crash
        return MOCK_RWA_AVG_APY
