"""
Risk Engine — deterministic risk scoring for RWA protocols.

Pure math. No AI. Judges trust math.
Score starts at 100 and deductions apply based on protocol characteristics.
"""

from config import RISK_WEIGHTS, PROTOCOLS
from models.schemas import RiskLevel, RiskResponse
from services.protocols import get_protocol_metadata, calculate_age_days


class RiskEngine:
    """Deterministic risk scoring engine using RISK_WEIGHTS from config.py."""

    def score_protocol(
        self,
        protocol_key: str,
        tvl: float,
        age_days: int,
        audit_status: str,
        issuer_concentration: str,
    ) -> int:
        """
        Score a protocol 0-100 using deterministic rules.
        Higher score = safer protocol.

        Args:
            protocol_key: Protocol identifier (e.g. "ondo")
            tvl: Total value locked in USD
            age_days: Number of days since protocol launch
            audit_status: "Audited" or "unaudited"
            issuer_concentration: "Low", "Medium", or "High"

        Returns: Risk score as int 0-100
        """
        score = 100

        # TVL deductions
        if tvl < 1_000_000:
            score -= RISK_WEIGHTS["tvl_very_low"]
        elif tvl < 10_000_000:
            score -= RISK_WEIGHTS["tvl_low"]

        # Age deductions
        if age_days < 180:
            score -= RISK_WEIGHTS["age_very_new"]
        elif age_days < 365:
            score -= RISK_WEIGHTS["age_new"]

        # Audit deduction
        if audit_status.lower() == "unaudited":
            score -= RISK_WEIGHTS["unaudited"]

        # Issuer concentration deductions
        if issuer_concentration.lower() == "high":
            score -= RISK_WEIGHTS["concentration_high"]
        elif issuer_concentration.lower() == "medium":
            score -= RISK_WEIGHTS["concentration_medium"]

        return max(0, min(100, score))

    def get_risk_level(self, score: int) -> RiskLevel:
        """
        Map numeric risk score to RiskLevel enum.

        70-100 → Low risk (safe)
        40-69  → Medium risk
        0-39   → High risk
        """
        if score >= 70:
            return RiskLevel.LOW
        elif score >= 40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def evaluate(self, protocol_key: str, tvl: float) -> RiskResponse:
        """
        Full risk evaluation for a protocol.
        Pulls static metadata from config, scores, and returns full breakdown.

        Args:
            protocol_key: Protocol identifier
            tvl: Current TVL in USD

        Returns: RiskResponse with score, level, factors, and recommendation
        """
        meta = get_protocol_metadata(protocol_key)
        if not meta:
            return RiskResponse(
                protocol=protocol_key,
                protocol_name=protocol_key,
                risk_score=0,
                risk_level=RiskLevel.HIGH,
                factors={"error": "Unknown protocol"},
                recommendation="Protocol not found in registry. Do not invest.",
            )

        age_days = calculate_age_days(meta["launch_year"])
        audit_status = meta["audit_status"]
        issuer_concentration = meta["issuer_concentration"]

        score = self.score_protocol(
            protocol_key=protocol_key,
            tvl=tvl,
            age_days=age_days,
            audit_status=audit_status,
            issuer_concentration=issuer_concentration,
        )
        risk_level = self.get_risk_level(score)

        # Build factor breakdown
        factors = {
            "base_score": 100,
            "tvl": tvl,
            "tvl_deduction": 0,
            "age_days": age_days,
            "age_deduction": 0,
            "audit_status": audit_status,
            "audit_deduction": 0,
            "issuer_concentration": issuer_concentration,
            "concentration_deduction": 0,
            "final_score": score,
        }

        if tvl < 1_000_000:
            factors["tvl_deduction"] = -RISK_WEIGHTS["tvl_very_low"]
        elif tvl < 10_000_000:
            factors["tvl_deduction"] = -RISK_WEIGHTS["tvl_low"]

        if age_days < 180:
            factors["age_deduction"] = -RISK_WEIGHTS["age_very_new"]
        elif age_days < 365:
            factors["age_deduction"] = -RISK_WEIGHTS["age_new"]

        if audit_status.lower() == "unaudited":
            factors["audit_deduction"] = -RISK_WEIGHTS["unaudited"]

        if issuer_concentration.lower() == "high":
            factors["concentration_deduction"] = -RISK_WEIGHTS["concentration_high"]
        elif issuer_concentration.lower() == "medium":
            factors["concentration_deduction"] = -RISK_WEIGHTS["concentration_medium"]

        # Generate recommendation
        if risk_level == RiskLevel.LOW:
            recommendation = (
                f"{meta['name']} scores {score}/100 — low risk. "
                f"Strong fundamentals with ${tvl:,.0f} TVL and {age_days} days of operation. "
                f"Suitable for conservative allocation."
            )
        elif risk_level == RiskLevel.MEDIUM:
            recommendation = (
                f"{meta['name']} scores {score}/100 — medium risk. "
                f"Acceptable for diversified portfolios but monitor "
                f"{'TVL closely' if tvl < 10_000_000 else 'issuer concentration'}."
            )
        else:
            recommendation = (
                f"{meta['name']} scores {score}/100 — high risk. "
                f"Significant concerns detected. Not recommended for conservative agents."
            )

        return RiskResponse(
            protocol=protocol_key,
            protocol_name=meta["name"],
            risk_score=score,
            risk_level=risk_level,
            factors=factors,
            recommendation=recommendation,
        )
