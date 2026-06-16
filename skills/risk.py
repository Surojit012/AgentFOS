"""Compatibility adapter for AgentFOS Risk Engine v2."""

from datetime import datetime, timezone
from typing import Optional

from config import MOCK_PROTOCOL_DATA, MOCK_TREASURY_RATE
from models.schemas import RiskLevel, RiskResponse
from services.protocols import get_protocol_metadata, calculate_age_days
from risk_engine_v2 import calculate_composite_risk
from risk_engine_v2.types import (
    CompositeRiskInput,
    ConcentrationInput,
    DataProvenance,
    LiquidityInput,
    MaturityInput,
    TransparencyInput,
    YieldSustainabilityInput,
)


class RiskEngine:
    """Deterministic v2 risk scoring engine with the legacy RiskResponse surface."""

    def score_protocol(
        self,
        protocol_key: str,
        tvl: float,
        age_days: int,
        audit_status: str,
        issuer_concentration: str,
        apy: Optional[float] = None,
        treasury_yield: Optional[float] = None,
        data_source: str = "degraded",
    ) -> int:
        """
        Score a protocol 0-100 using Risk Engine v2.
        Higher score = safer protocol.

        Args:
            protocol_key: Protocol identifier (e.g. "ondo")
            tvl: Total value locked in USD
            age_days: Number of days since protocol launch
            audit_status: "Audited" or "unaudited"
            issuer_concentration: "Low", "Medium", or "High"

        Returns: Risk score as int 0-100
        """
        meta = get_protocol_metadata(protocol_key) or {}
        result = self._evaluate_v2(
            protocol_key=protocol_key,
            tvl=tvl,
            apy=apy if apy is not None else MOCK_PROTOCOL_DATA.get(protocol_key, {}).get("apy"),
            treasury_yield=treasury_yield if treasury_yield is not None else MOCK_TREASURY_RATE,
            data_source=data_source,
            meta_override={
                **meta,
                "audit_status": audit_status,
                "issuer_concentration": issuer_concentration,
                "launch_date": self._launch_date_from_age(age_days),
            },
        )
        return result.risk_score

    def get_risk_level(self, score: int) -> RiskLevel:
        """
        Map numeric risk score to RiskLevel enum.

        75-100 → Low risk (safe)
        40-74  → Medium risk
        0-39   → High risk
        """
        if score >= 75:
            return RiskLevel.LOW
        elif score >= 40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def evaluate(
        self,
        protocol_key: str,
        tvl: float,
        apy: Optional[float] = None,
        treasury_yield: Optional[float] = None,
        data_source: str = "degraded",
    ) -> RiskResponse:
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
                rating="Very High",
                overall_confidence="low",
                breakdown={},
                scored_at=self._scored_at(),
                schema_version="2.0",
            )

        v2_result = self._evaluate_v2(
            protocol_key=protocol_key,
            tvl=tvl,
            apy=apy if apy is not None else MOCK_PROTOCOL_DATA.get(protocol_key, {}).get("apy"),
            treasury_yield=treasury_yield if treasury_yield is not None else MOCK_TREASURY_RATE,
            data_source=data_source,
        )
        score = v2_result.risk_score
        risk_level = self.get_risk_level(score)
        age_days = calculate_age_days(meta["launch_year"])
        api_result = v2_result.to_api_dict()

        factors = {
            "schema_version": "2.0",
            "tvl": tvl,
            "age_days": age_days,
            "audit_status": meta["audit_status"],
            "issuer_concentration": meta["issuer_concentration"],
            "overall_confidence": v2_result.overall_confidence,
            "breakdown": api_result["breakdown"],
            "final_score": score,
        }

        # Generate recommendation
        if risk_level == RiskLevel.LOW:
            recommendation = (
                f"{meta['name']} scores {score}/100 ({v2_result.rating}). "
                f"Strong fundamentals with {v2_result.overall_confidence} scoring confidence. "
                f"Suitable for conservative allocation."
            )
        elif risk_level == RiskLevel.MEDIUM:
            recommendation = (
                f"{meta['name']} scores {score}/100 ({v2_result.rating}). "
                f"Acceptable for diversified portfolios; monitor degraded or insufficient dimensions."
            )
        else:
            recommendation = (
                f"{meta['name']} scores {score}/100 ({v2_result.rating}). "
                f"Significant concerns detected. Not recommended for conservative agents."
            )

        return RiskResponse(
            protocol=protocol_key,
            protocol_name=meta["name"],
            risk_score=score,
            risk_level=risk_level,
            factors=factors,
            recommendation=recommendation,
            rating=v2_result.rating,
            overall_confidence=v2_result.overall_confidence,
            breakdown=api_result["breakdown"],
            scored_at=v2_result.scored_at,
            schema_version=v2_result.schema_version,
        )

    def _evaluate_v2(
        self,
        protocol_key: str,
        tvl: Optional[float],
        apy: Optional[float],
        treasury_yield: Optional[float],
        data_source: str,
        meta_override: Optional[dict] = None,
    ):
        meta = meta_override or get_protocol_metadata(protocol_key) or {}
        provenance = self._provenance_from_source(data_source)
        scored_at = self._scored_at()
        as_of_date = scored_at[:10]
        top_5 = meta.get("top_5_holder_concentration")
        concentration_provenance = provenance if top_5 is not None else DataProvenance.DEGRADED

        snapshot = CompositeRiskInput(
            protocol=protocol_key,
            protocol_name=meta.get("name", protocol_key),
            liquidity=LiquidityInput(
                tvl=tvl,
                provenance=provenance,
                source_note=data_source,
            ),
            maturity=MaturityInput(
                launch_date=meta.get("launch_date"),
                as_of_date=as_of_date,
                provenance=DataProvenance.DEGRADED if "launch_year" in meta else DataProvenance.INSUFFICIENT,
            ),
            transparency=TransparencyInput(
                audit_status=meta.get("audit_status", "Unaudited"),
                audit_date=meta.get("audit_date"),
                as_of_date=as_of_date,
                reserve_reports=bool(meta.get("reserve_reports", False)),
                public_legal_docs=bool(meta.get("public_legal_docs", False)),
                provenance=DataProvenance.DEGRADED,
            ),
            concentration=ConcentrationInput(
                top_5_holder_concentration=top_5,
                issuer_concentration=meta.get("issuer_concentration"),
                provenance=concentration_provenance,
            ),
            yield_sustainability=YieldSustainabilityInput(
                rwa_yield=apy,
                treasury_yield=treasury_yield,
                provenance=provenance,
            ),
            scored_at=scored_at,
        )
        return calculate_composite_risk(snapshot)

    @staticmethod
    def _provenance_from_source(data_source: str) -> DataProvenance:
        if data_source == "live":
            return DataProvenance.LIVE
        if data_source in {"mock", "degraded", "stale", "empty_payload", "source_unreachable"}:
            return DataProvenance.DEGRADED
        return DataProvenance.INSUFFICIENT

    @staticmethod
    def _scored_at() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _launch_date_from_age(age_days: int) -> str:
        launch = datetime.now(timezone.utc).date().toordinal() - max(age_days, 0)
        return datetime.fromordinal(launch).date().isoformat()
