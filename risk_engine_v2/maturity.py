from datetime import date

from risk_engine_v2.types import DataProvenance, DimensionResult, MaturityInput


def calculate_maturity_score(inputs: MaturityInput) -> DimensionResult:
    """
    Score protocol maturity from 0-20.

    Boundaries use >= on the lower side of each bucket:
    >=1095 days = 20, >=365 days = 14, >=180 days = 8, <180 days = 4.
    Missing or invalid dates receive the fixed insufficient-data floor of 4/20.
    """
    max_score = 20
    try:
        launch_date = date.fromisoformat(inputs.launch_date or "")
        as_of_date = date.fromisoformat(inputs.as_of_date)
        age_days = (as_of_date - launch_date).days
    except ValueError:
        return DimensionResult(
            score=4,
            max_score=max_score,
            provenance=DataProvenance.INSUFFICIENT,
            details={"reason": "missing_or_invalid_launch_date"},
        )

    if age_days < 0:
        return DimensionResult(
            score=4,
            max_score=max_score,
            provenance=DataProvenance.INSUFFICIENT,
            details={"age_days": age_days, "reason": "future_launch_date"},
        )

    if age_days >= 1095:
        score = 20
    elif age_days >= 365:
        score = 14
    elif age_days >= 180:
        score = 8
    else:
        score = 4

    return DimensionResult(
        score=score,
        max_score=max_score,
        provenance=inputs.provenance,
        details={"age_days": age_days, "launch_date": inputs.launch_date},
    )
