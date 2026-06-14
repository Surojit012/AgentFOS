"""
Opportunity Engine — discovers and enriches RWA yield opportunities.

Pulls live protocol data from DefiLlama, enriches with benchmark spreads,
applies risk scoring, and filters/sorts by user criteria.
"""

from typing import Optional

from models.schemas import (
    Asset,
    RiskLevel,
    RiskTolerance,
    OpportunityRequest,
    OpportunityResponse,
)
from services.defillama import fetch_all_protocols
from services.benchmarks import fetch_treasury_rate, fetch_rwa_avg_apy
from services.protocols import get_protocol_metadata, calculate_age_days
from skills.risk import RiskEngine


class OpportunityEngine:
    """Discovers and enriches RWA yield opportunities across 6 protocols."""

    def __init__(self) -> None:
        self.risk_engine = RiskEngine()

    async def discover(self, request: OpportunityRequest) -> OpportunityResponse:
        """
        Discover RWA yield opportunities with full enrichment.

        Steps:
        1. Fetch live protocol data (TVL, APY) from DefiLlama
        2. Fetch treasury rate and RWA average APY benchmarks
        3. Enrich each asset with benchmark spreads and risk scores
        4. Filter by risk_level and min_apy if specified
        5. Sort by APY descending

        Args:
            request: OpportunityRequest with risk_level, min_apy, min_tvl filters

        Returns: OpportunityResponse with enriched assets + benchmark data
        """
        # Fetch live data
        protocol_data = await fetch_all_protocols()
        treasury_rate = fetch_treasury_rate()
        rwa_avg_apy = await fetch_rwa_avg_apy()

        # Determine data source (live vs mock)
        data_sources = [d.get("data_source", "mock") for d in protocol_data.values()]
        overall_source = "live" if any(s == "live" for s in data_sources) else "mock"

        # Build enriched asset list
        assets = []
        for key, live_data in protocol_data.items():
            meta = get_protocol_metadata(key)
            if not meta:
                continue

            tvl = live_data.get("tvl", 0)
            apy = live_data.get("apy", 0)
            tvl_change_30d = live_data.get("tvl_change_30d", 0)
            age_days = calculate_age_days(meta["launch_year"])

            # Risk scoring
            risk_score = self.risk_engine.score_protocol(
                protocol_key=key,
                tvl=tvl,
                age_days=age_days,
                audit_status=meta["audit_status"],
                issuer_concentration=meta["issuer_concentration"],
            )
            risk_level = self.risk_engine.get_risk_level(risk_score)

            # Benchmark spreads
            apy_vs_treasury = round(apy - treasury_rate, 2)
            apy_vs_rwa_avg = round(apy - rwa_avg_apy, 2)

            asset = Asset(
                protocol_key=key,
                name=meta["name"],
                primary_asset=meta["primary_asset"],
                asset_class=meta["asset_class"],
                chain=meta["chain"],
                tvl=tvl,
                tvl_change_30d=tvl_change_30d,
                apy=apy,
                audit_status=meta["audit_status"],
                issuer_concentration=meta["issuer_concentration"],
                age_days=age_days,
                apy_vs_treasury=apy_vs_treasury,
                apy_vs_rwa_avg=apy_vs_rwa_avg,
                risk_score=risk_score,
                risk_level=risk_level,
            )
            assets.append(asset)

        # Apply filters
        filtered = self._apply_filters(assets, request)

        # Sort by APY descending
        filtered.sort(key=lambda a: a.apy, reverse=True)

        return OpportunityResponse(
            assets=filtered,
            treasury_rate=treasury_rate,
            rwa_avg_apy=rwa_avg_apy,
            data_source=overall_source,
            count=len(filtered),
        )

    def _apply_filters(
        self,
        assets: list[Asset],
        request: OpportunityRequest,
    ) -> list[Asset]:
        """Apply risk_level, min_apy, and min_tvl filters."""
        filtered = assets

        # Filter by risk_level (maps RiskTolerance to allowed RiskLevels)
        if request.risk_level == RiskTolerance.LOW:
            # Low tolerance → only Low risk assets
            filtered = [a for a in filtered if a.risk_level == RiskLevel.LOW]
        elif request.risk_level == RiskTolerance.MEDIUM:
            # Medium tolerance → Low + Medium risk assets
            filtered = [
                a for a in filtered
                if a.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM)
            ]
        # High tolerance → all assets pass

        # Filter by minimum APY
        if request.min_apy is not None:
            filtered = [a for a in filtered if a.apy >= request.min_apy]

        # Filter by minimum TVL
        if request.min_tvl is not None:
            filtered = [a for a in filtered if a.tvl >= request.min_tvl]

        return filtered
