from pydantic_settings import BaseSettings
from typing import Dict, Any


class Settings(BaseSettings):
    # API Keys
    STRAICO_API_KEY: str = ""
    FRED_API_KEY: str = ""

    # App
    APP_NAME: str = "AgentFOS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

# ── Protocol Registry ────────────────────────────────────────────────────────
# 6 deep protocols with static metadata
# Live data (TVL, APY) fetched at runtime from DefiLlama
# This is our competitive advantage — specificity over breadth

PROTOCOLS: Dict[str, Dict[str, Any]] = {
    "ondo": {
        "name": "Ondo Finance",
        "slug": "ondo",                        # DefiLlama slug
        "asset_class": "Tokenized Treasury",
        "primary_asset": "OUSG",
        "chain": "Ethereum",
        "website": "https://ondo.finance",
        "audit_status": "Audited",
        "issuer_concentration": "Low",
        "launch_year": 2023,
    },
    "zoth": {
        "name": "Zoth",
        "slug": "zoth",
        "asset_class": "Emerging Market Credit",
        "primary_asset": "zOPAL",
        "chain": "Ethereum",
        "website": "https://zoth.io",
        "audit_status": "Audited",
        "issuer_concentration": "Medium",
        "launch_year": 2023,
    },
    "maple": {
        "name": "Maple Finance",
        "slug": "maple-finance",
        "asset_class": "Institutional Private Credit",
        "primary_asset": "MPL",
        "chain": "Ethereum",
        "website": "https://maple.finance",
        "audit_status": "Audited",
        "issuer_concentration": "Medium",
        "launch_year": 2021,
    },
    "centrifuge": {
        "name": "Centrifuge",
        "slug": "centrifuge",
        "asset_class": "Real World Asset Loans",
        "primary_asset": "CFG",
        "chain": "Ethereum",
        "website": "https://centrifuge.io",
        "audit_status": "Audited",
        "issuer_concentration": "Low",
        "launch_year": 2021,
    },
    "backed": {
        "name": "Backed Finance",
        "slug": "backed-finance",
        "asset_class": "Tokenized ETFs & Bonds",
        "primary_asset": "bIB01",
        "chain": "Ethereum",
        "website": "https://backed.fi",
        "audit_status": "Audited",
        "issuer_concentration": "Low",
        "launch_year": 2022,
    },
    "opentrade": {
        "name": "OpenTrade",
        "slug": "opentrade",
        "asset_class": "Trade Finance",
        "primary_asset": "USDC Vault",
        "chain": "Ethereum",
        "website": "https://opentrade.io",
        "audit_status": "Audited",
        "issuer_concentration": "Medium",
        "launch_year": 2023,
    },
}

# ── Risk Scoring Weights ─────────────────────────────────────────────────────
# Deterministic. Not AI. Judges trust math.

RISK_WEIGHTS = {
    "tvl_very_low": 30,       # TVL < $1M
    "tvl_low": 15,            # TVL < $10M
    "age_very_new": 25,       # < 6 months old
    "age_new": 10,            # < 12 months old
    "unaudited": 30,          # no audit
    "concentration_high": 20, # single issuer dominates
    "concentration_medium": 10,
}

# ── TradFi Benchmark FRED Series ────────────────────────────────────────────
FRED_SERIES = {
    "treasury_10y": "GS10",   # 10-Year Treasury Constant Maturity Rate
    "treasury_2y": "GS2",     # 2-Year Treasury
    "treasury_3m": "TB3MS",   # 3-Month T-Bill
    "fed_funds": "FEDFUNDS",  # Federal Funds Rate
}

# ── Mock Data ────────────────────────────────────────────────────────────────
# Fallback when DefiLlama or FRED is down during demo
# Never let a dead API kill the demo

MOCK_PROTOCOL_DATA = {
    "ondo": {"tvl": 1_200_000_000, "apy": 4.7, "tvl_change_30d": 12.3},
    "zoth": {"tvl": 48_000_000,    "apy": 10.2, "tvl_change_30d": 8.1},
    "maple": {"tvl": 380_000_000,  "apy": 8.5, "tvl_change_30d": -2.4},
    "centrifuge": {"tvl": 220_000_000, "apy": 7.2, "tvl_change_30d": 5.6},
    "backed": {"tvl": 95_000_000,  "apy": 5.1, "tvl_change_30d": 15.2},
    "opentrade": {"tvl": 62_000_000, "apy": 6.8, "tvl_change_30d": 3.9},
}

MOCK_TREASURY_RATE = 4.2   # 10Y US Treasury fallback
MOCK_RWA_AVG_APY = 7.1    # RWA market average fallback
