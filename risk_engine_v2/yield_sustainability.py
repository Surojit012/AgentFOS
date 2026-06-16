from decimal import Decimal

from risk_engine_v2.types import DataProvenance, DimensionResult, YieldSustainabilityInput


def calculate_yield_sustainability_score(inputs: YieldSustainabilityInput) -> DimensionResult:
    """
    Score yield sustainability from 0-15.

    Spread = RWA yield - Treasury yield. Negative spreads and 0-2% score 15,
    >2-5% scores 12, >5-8% scores 8, and >8% scores 4. Missing yield inputs
    receive the fixed insufficient-data floor score of 4/15.
    """
    max_score = 15
    if inputs.rwa_yield is None or inputs.treasury_yield is None:
        return DimensionResult(
            score=4,
            max_score=max_score,
            provenance=DataProvenance.INSUFFICIENT,
            details={"reason": "missing_yield_input"},
        )

    spread = Decimal(str(inputs.rwa_yield)) - Decimal(str(inputs.treasury_yield))
    if spread <= Decimal("2"):
        score = 15
    elif spread <= Decimal("5"):
        score = 12
    elif spread <= Decimal("8"):
        score = 8
    else:
        score = 4

    return DimensionResult(
        score=score,
        max_score=max_score,
        provenance=inputs.provenance,
        details={
            "rwa_yield": inputs.rwa_yield,
            "treasury_yield": inputs.treasury_yield,
            "spread": float(spread),
        },
    )
