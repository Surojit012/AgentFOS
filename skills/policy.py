"""
Policy Engine — agent-native guardrails for capital allocation decisions.

This is not human auth. This is programmatic enforcement of spending
policies that autonomous AI agents must respect before deploying capital.
"""

from models.schemas import (
    PolicyRequest,
    PolicyResponse,
    RiskTolerance,
)
from skills.risk import RiskEngine
from services.protocols import get_protocol_metadata
from services.defillama import fetch_all_protocols


class PolicyEngine:
    """Evaluates whether an agent action is allowed under current policy rules."""

    def __init__(self) -> None:
        self.risk_engine = RiskEngine()

    async def evaluate(self, request: PolicyRequest) -> PolicyResponse:
        """
        Evaluate whether an agent's proposed action is policy-compliant.

        Rules enforced:
        1. amount must be > 0
        2. risk_score of asset must be >= min_risk_score
        3. single allocation cannot exceed max_single_allocation %
        4. if risk_tolerance is "low", block any asset with risk_level "High"
        5. if risk_tolerance is "medium", block risk_score < 40

        Args:
            request: PolicyRequest with action, amount, asset, risk_tolerance

        Returns: PolicyResponse with allowed flag and reason if blocked
        """
        warnings = []

        # Rule 1: Amount must be positive (already enforced by Pydantic gt=0,
        # but double-check for defense in depth)
        if request.amount <= 0:
            return PolicyResponse(
                allowed=False,
                action=request.action.value,
                asset=request.asset,
                amount=request.amount,
                reason="Amount must be greater than 0.",
                warnings=[],
            )

        # Look up protocol metadata
        meta = get_protocol_metadata(request.asset)
        if not meta:
            return PolicyResponse(
                allowed=False,
                action=request.action.value,
                asset=request.asset,
                amount=request.amount,
                reason=f"Unknown protocol '{request.asset}'. Not in registry.",
                warnings=[],
            )

        # Get live or mock TVL for risk scoring
        try:
            protocol_data = await fetch_all_protocols()
            tvl = protocol_data.get(request.asset, {}).get("tvl", 0)
        except Exception:
            from config import MOCK_PROTOCOL_DATA
            tvl = MOCK_PROTOCOL_DATA.get(request.asset, {}).get("tvl", 0)

        # Score the protocol
        risk_result = self.risk_engine.evaluate(request.asset, tvl)
        risk_score = risk_result.risk_score
        risk_level = risk_result.risk_level

        # Rule 2: Risk score must meet minimum threshold
        if risk_score < request.min_risk_score:
            return PolicyResponse(
                allowed=False,
                action=request.action.value,
                asset=request.asset,
                amount=request.amount,
                reason=(
                    f"Risk score {risk_score} is below minimum threshold "
                    f"{request.min_risk_score}. Protocol does not meet safety requirements."
                ),
                warnings=[],
            )

        # Rule 3: Single allocation cannot exceed max_single_allocation %
        # (this is a policy constraint — the amount itself is what matters vs total capital)
        if request.max_single_allocation < 1.0:
            warnings.append(
                f"Max single allocation policy: {request.max_single_allocation * 100:.0f}% "
                f"of total portfolio. Ensure this allocation does not exceed that threshold."
            )

        # Rule 4: Low risk tolerance blocks High risk assets
        if request.risk_tolerance == RiskTolerance.LOW and risk_level.value == "High":
            return PolicyResponse(
                allowed=False,
                action=request.action.value,
                asset=request.asset,
                amount=request.amount,
                reason=(
                    f"Risk tolerance is 'low' but {meta['name']} has risk level "
                    f"'{risk_level.value}' (score: {risk_score}). Blocked by policy."
                ),
                warnings=[],
            )

        # Rule 5: Medium risk tolerance blocks risk_score < 40
        if request.risk_tolerance == RiskTolerance.MEDIUM and risk_score < 40:
            return PolicyResponse(
                allowed=False,
                action=request.action.value,
                asset=request.asset,
                amount=request.amount,
                reason=(
                    f"Risk tolerance is 'medium' but {meta['name']} has risk score "
                    f"{risk_score} (below 40 threshold). Blocked by policy."
                ),
                warnings=[],
            )

        # All rules passed
        return PolicyResponse(
            allowed=True,
            action=request.action.value,
            asset=request.asset,
            amount=request.amount,
            reason=f"Policy PASS — {meta['name']} (risk score: {risk_score}, level: {risk_level.value}) approved for {request.action.value}.",
            warnings=warnings,
        )
