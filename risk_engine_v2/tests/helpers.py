from risk_engine_v2.types import (
    CompositeRiskInput,
    ConcentrationInput,
    DataProvenance,
    LiquidityInput,
    MaturityInput,
    TransparencyInput,
    YieldSustainabilityInput,
)


def frozen_snapshot(**overrides) -> CompositeRiskInput:
    payload = {
        "protocol": "ondo",
        "protocol_name": "Ondo Finance",
        "liquidity": LiquidityInput(tvl=600_000_000, provenance=DataProvenance.LIVE),
        "maturity": MaturityInput(
            launch_date="2020-01-01",
            as_of_date="2026-06-16",
            provenance=DataProvenance.LIVE,
        ),
        "transparency": TransparencyInput(
            audit_status="Audited",
            audit_date="2026-01-01",
            as_of_date="2026-06-16",
            reserve_reports=True,
            public_legal_docs=True,
            provenance=DataProvenance.LIVE,
        ),
        "concentration": ConcentrationInput(
            top_5_holder_concentration=35,
            issuer_concentration="Low",
            provenance=DataProvenance.LIVE,
        ),
        "yield_sustainability": YieldSustainabilityInput(
            rwa_yield=5,
            treasury_yield=4,
            provenance=DataProvenance.LIVE,
        ),
        "scored_at": "2026-06-16T10:00:00Z",
    }
    payload.update(overrides)
    return CompositeRiskInput(**payload)
