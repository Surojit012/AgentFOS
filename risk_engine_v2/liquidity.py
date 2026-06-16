from decimal import Decimal, ROUND_FLOOR
import logging

from risk_engine_v2.types import DataProvenance, DimensionResult, LiquidityInput

logger = logging.getLogger(__name__)


def calculate_liquidity_score(inputs: LiquidityInput) -> DimensionResult:
    """
    Score liquidity from 0-25.

    TVL uses strict upper buckets: >500M = 10, >=100M = 7, >=10M = 4,
    >0 and <10M = 1. Missing, zero, or negative TVL receives the fixed
    insufficient-data floor score of 1/25. Optional activity can add up to
    15 points, floored at the dimension boundary and capped at 25.
    """
    max_score = 25
    tvl = inputs.tvl
    details = {"tvl": tvl}

    if tvl is not None and tvl < 0:
        logger.warning("Rejected negative TVL in risk scoring: %s", tvl)

    if tvl is None or tvl <= 0:
        return DimensionResult(
            score=1,
            max_score=max_score,
            provenance=DataProvenance.INSUFFICIENT,
            details={**details, "reason": "missing_or_invalid_tvl"},
        )

    tvl_dec = Decimal(str(tvl))
    if tvl_dec > Decimal("500000000"):
        tvl_score = 10
    elif tvl_dec >= Decimal("100000000"):
        tvl_score = 7
    elif tvl_dec >= Decimal("10000000"):
        tvl_score = 4
    else:
        tvl_score = 1

    activity_score = 0
    if inputs.active_addresses is not None and inputs.active_addresses > 0:
        activity_score += int(
            min(Decimal(inputs.active_addresses) / Decimal("10000"), Decimal("8"))
            .to_integral_value(rounding=ROUND_FLOOR)
        )
    if inputs.transfer_count_30d is not None and inputs.transfer_count_30d > 0:
        activity_score += int(
            min(Decimal(inputs.transfer_count_30d) / Decimal("100000"), Decimal("7"))
            .to_integral_value(rounding=ROUND_FLOOR)
        )

    score = min(max_score, tvl_score + min(activity_score, 15))
    provenance = inputs.provenance
    if provenance == DataProvenance.LIVE and inputs.source_note in {"empty_payload", "stale"}:
        provenance = DataProvenance.DEGRADED

    return DimensionResult(
        score=score,
        max_score=max_score,
        provenance=provenance,
        details={
            **details,
            "tvl_bucket_score": tvl_score,
            "activity_score": min(activity_score, 15),
            "source_note": inputs.source_note,
        },
    )
