"""
Allocation Engine — generates risk-adjusted capital allocation across RWA protocols.

Combines OpportunityEngine discovery, RiskEngine scoring, and policy filtering
to produce optimal portfolio allocations with AI-generated narrative summaries.
"""

import json
from typing import Optional

from models.schemas import (
    RiskLevel,
    RiskTolerance,
    OpportunityRequest,
    AllocationRequest,
    AllocationResponse,
    AllocationItem,
)
from skills.opportunity import OpportunityEngine
from skills.risk import RiskEngine
from services.benchmarks import fetch_treasury_rate
from intelligence.summarizer import summarize_allocation


class AllocationEngine:
    """Generates capital allocation recommendations using risk-adjusted scoring."""

    def __init__(self) -> None:
        self.opportunity_engine = OpportunityEngine()
        self.risk_engine = RiskEngine()

    async def allocate(self, request: AllocationRequest) -> AllocationResponse:
        """
        Generate a full capital allocation recommendation.

        Steps:
        1. Discover opportunities via OpportunityEngine
        2. Score each protocol via RiskEngine
        3. Filter by risk tolerance
        4. Filter by min_apy_spread above treasury
        5. Rank by risk-adjusted composite score:
           (risk_score * 0.6) + (apy_spread_normalized * 0.4)
        6. Generate allocation percentages
        7. Get AI narrative summary

        Args:
            request: AllocationRequest with capital, risk tolerance, min_apy_spread

        Returns: AllocationResponse with full portfolio breakdown
        """
        # Step 1: Discover opportunities matching risk tolerance
        opp_request = OpportunityRequest(risk_level=request.risk)
        opportunities = await self.opportunity_engine.discover(opp_request)

        treasury_rate = opportunities.treasury_rate
        data_source = opportunities.data_source

        # Step 2 & 3: Assets already have risk scores from OpportunityEngine
        # Filter by risk tolerance
        eligible_assets = opportunities.assets

        # Step 4: Filter by min_apy_spread above treasury
        if request.min_apy_spread > 0:
            eligible_assets = [
                a for a in eligible_assets
                if (a.apy_vs_treasury or 0) >= request.min_apy_spread
            ]

        # Handle case where no assets pass filters
        if not eligible_assets:
            return AllocationResponse(
                capital=request.capital,
                risk_preference=request.risk.value,
                allocations=[],
                portfolio_avg_apy=0.0,
                portfolio_avg_risk_score=0,
                treasury_benchmark=treasury_rate,
                portfolio_spread=0.0,
                data_source=data_source,
                narrative="No eligible assets found matching your risk tolerance and yield requirements.",
            )

        # Step 5: Rank by risk-adjusted composite score
        # Composite = (risk_score * 0.6) + (apy_spread_normalized * 0.4)
        max_spread = max(
            (a.apy_vs_treasury or 0) for a in eligible_assets
        )
        # Avoid division by zero
        spread_normalizer = max_spread if max_spread > 0 else 1.0

        scored_assets = []
        for asset in eligible_assets:
            spread = asset.apy_vs_treasury or 0
            apy_spread_normalized = (spread / spread_normalizer) * 100
            composite_score = (asset.risk_score * 0.6) + (apy_spread_normalized * 0.4)
            scored_assets.append((asset, composite_score))

        # Sort by composite score descending (best first)
        scored_assets.sort(key=lambda x: x[1], reverse=True)

        # Step 6: Generate allocation percentages
        # Weighted by composite score
        total_composite = sum(cs for _, cs in scored_assets)
        if total_composite == 0:
            total_composite = 1.0

        allocations = []
        for asset, composite in scored_assets:
            pct = round((composite / total_composite) * 100, 2)
            amount = round(request.capital * (pct / 100), 2)

            allocations.append(
                AllocationItem(
                    protocol_key=asset.protocol_key,
                    name=asset.name,
                    asset_class=asset.asset_class,
                    apy=asset.apy,
                    risk_score=asset.risk_score,
                    risk_level=asset.risk_level,
                    allocation_pct=pct,
                    allocation_amount=amount,
                    apy_vs_treasury=asset.apy_vs_treasury or 0,
                )
            )

        # Portfolio-level metrics
        total_allocated_pct = sum(a.allocation_pct for a in allocations)
        if total_allocated_pct > 0:
            weighted_apy = sum(a.apy * (a.allocation_pct / 100) for a in allocations)
            portfolio_avg_apy = round(weighted_apy / (total_allocated_pct / 100), 2)
            weighted_risk = sum(a.risk_score * (a.allocation_pct / 100) for a in allocations)
            portfolio_avg_risk = round(weighted_risk / (total_allocated_pct / 100))
        else:
            portfolio_avg_apy = 0.0
            portfolio_avg_risk = 0
        portfolio_spread = round(portfolio_avg_apy - treasury_rate, 2)

        # Step 7: Get AI narrative summary
        allocation_response = AllocationResponse(
            capital=request.capital,
            risk_preference=request.risk.value,
            allocations=allocations,
            portfolio_avg_apy=portfolio_avg_apy,
            portfolio_avg_risk_score=portfolio_avg_risk,
            treasury_benchmark=treasury_rate,
            portfolio_spread=portfolio_spread,
            data_source=data_source,
            narrative=None,
        )

        # Generate narrative via Claude (with mock fallback)
        narrative = await summarize_allocation(
            allocation_data=allocation_response.model_dump(),
            treasury_rate=treasury_rate,
        )
        allocation_response.narrative = narrative

        return allocation_response
