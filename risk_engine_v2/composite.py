from risk_engine_v2.concentration import calculate_concentration_score
from risk_engine_v2.liquidity import calculate_liquidity_score
from risk_engine_v2.maturity import calculate_maturity_score
from risk_engine_v2.transparency import calculate_transparency_score
from risk_engine_v2.types import CompositeRiskInput, CompositeRiskResult, DataProvenance
from risk_engine_v2.yield_sustainability import calculate_yield_sustainability_score


def _rating(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Low Risk"
    if score >= 60:
        return "Moderate Risk"
    if score >= 40:
        return "High Risk"
    return "Very High Risk"


def _confidence(provenances: list[DataProvenance]) -> str:
    insufficient_count = provenances.count(DataProvenance.INSUFFICIENT)
    degraded_count = provenances.count(DataProvenance.DEGRADED)
    if insufficient_count >= 2:
        return "low"
    if insufficient_count == 1 or degraded_count >= 2:
        return "medium"
    return "high"


def calculate_composite_risk(inputs: CompositeRiskInput) -> CompositeRiskResult:
    """
    Aggregate five integer dimension scores into one deterministic 0-100 score.

    Determinism rule: each dimension floors or buckets its own value to an int
    inside its allotted range. The composite never rounds floats; it only sums
    the five already-final integer dimension scores. This intentionally chooses
    "round/floor at dimension boundary, then sum" over "sum raw floats, then
    round once" so stored input snapshots replay byte-for-byte.
    """
    breakdown = {
        "liquidity": calculate_liquidity_score(inputs.liquidity),
        "maturity": calculate_maturity_score(inputs.maturity),
        "transparency": calculate_transparency_score(inputs.transparency),
        "concentration": calculate_concentration_score(inputs.concentration),
        "yield_sustainability": calculate_yield_sustainability_score(
            inputs.yield_sustainability
        ),
    }
    risk_score = sum(result.score for result in breakdown.values())
    provenances = [result.provenance for result in breakdown.values()]

    return CompositeRiskResult(
        risk_score=risk_score,
        rating=_rating(risk_score),
        overall_confidence=_confidence(provenances),
        breakdown=breakdown,
        scored_at=inputs.scored_at,
    )
