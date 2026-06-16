import logging

from risk_engine_v2.types import DataProvenance, DimensionResult, ConcentrationInput

logger = logging.getLogger(__name__)


def calculate_concentration_score(inputs: ConcentrationInput) -> DimensionResult:
    """
    Score concentration risk from 0-20.

    Top-5 holder concentration buckets are <40% = 20, 40-60% = 15,
    >60-80% = 10, and >80% = 5. Values below 0 or above 100 are rejected
    as insufficient data. If top-5 data is unavailable, issuer concentration
    is used as degraded fallback: Low = 20, Medium = 15, High = 5.
    """
    max_score = 20
    concentration = inputs.top_5_holder_concentration

    if concentration is not None:
        if concentration < 0 or concentration > 100:
            logger.warning(
                "Rejected invalid top-5 holder concentration in risk scoring: %s",
                concentration,
            )
            return DimensionResult(
                score=5,
                max_score=max_score,
                provenance=DataProvenance.INSUFFICIENT,
                details={"reason": "invalid_concentration", "value": concentration},
            )
        if concentration < 40:
            score = 20
        elif concentration <= 60:
            score = 15
        elif concentration <= 80:
            score = 10
        else:
            score = 5
        return DimensionResult(
            score=score,
            max_score=max_score,
            provenance=inputs.provenance,
            details={"top_5_holder_concentration": concentration},
        )

    fallback = (inputs.issuer_concentration or "").lower()
    fallback_scores = {"low": 20, "medium": 15, "high": 5}
    if fallback in fallback_scores:
        return DimensionResult(
            score=fallback_scores[fallback],
            max_score=max_score,
            provenance=DataProvenance.DEGRADED,
            details={"issuer_concentration": inputs.issuer_concentration},
        )

    return DimensionResult(
        score=5,
        max_score=max_score,
        provenance=DataProvenance.INSUFFICIENT,
        details={"reason": "missing_concentration"},
    )
