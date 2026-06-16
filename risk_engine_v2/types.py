from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class DataProvenance(str, Enum):
    LIVE = "live"
    DEGRADED = "degraded"
    INSUFFICIENT = "insufficient"


@dataclass(frozen=True)
class DimensionResult:
    score: int
    max_score: int
    provenance: DataProvenance
    details: Dict[str, Any] = field(default_factory=dict)

    def to_api_dict(self) -> Dict[str, Any]:
        payload = {
            "score": self.score,
            "max": self.max_score,
            "provenance": self.provenance.value,
        }
        if self.details:
            payload["details"] = self.details
        return payload


@dataclass(frozen=True)
class LiquidityInput:
    tvl: Optional[float]
    provenance: DataProvenance
    active_addresses: Optional[int] = None
    transfer_count_30d: Optional[int] = None
    source_note: Optional[str] = None


@dataclass(frozen=True)
class MaturityInput:
    launch_date: Optional[str]
    as_of_date: str
    provenance: DataProvenance


@dataclass(frozen=True)
class TransparencyInput:
    audit_status: str
    audit_date: Optional[str]
    as_of_date: str
    reserve_reports: bool
    public_legal_docs: bool
    provenance: DataProvenance


@dataclass(frozen=True)
class ConcentrationInput:
    top_5_holder_concentration: Optional[float]
    issuer_concentration: Optional[str]
    provenance: DataProvenance


@dataclass(frozen=True)
class YieldSustainabilityInput:
    rwa_yield: Optional[float]
    treasury_yield: Optional[float]
    provenance: DataProvenance


@dataclass(frozen=True)
class CompositeRiskInput:
    protocol: str
    protocol_name: str
    liquidity: LiquidityInput
    maturity: MaturityInput
    transparency: TransparencyInput
    concentration: ConcentrationInput
    yield_sustainability: YieldSustainabilityInput
    scored_at: str


@dataclass(frozen=True)
class CompositeRiskResult:
    risk_score: int
    rating: str
    overall_confidence: str
    breakdown: Dict[str, DimensionResult]
    scored_at: str
    schema_version: str = "2.0"

    def to_api_dict(self) -> Dict[str, Any]:
        return {
            "risk_score": self.risk_score,
            "rating": self.rating,
            "overall_confidence": self.overall_confidence,
            "breakdown": {
                key: result.to_api_dict()
                for key, result in self.breakdown.items()
            },
            "scored_at": self.scored_at,
            "schema_version": self.schema_version,
        }
