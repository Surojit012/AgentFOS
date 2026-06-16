from datetime import date

from risk_engine_v2.types import DataProvenance, DimensionResult, TransparencyInput


def calculate_transparency_score(inputs: TransparencyInput) -> DimensionResult:
    """
    Score transparency from 0-20.

    Audit contributes 10 points when <=365 days old, 6 points when <=730 days
    old, and 0 beyond that or if absent. Reserve reports add 5. Public legal
    docs add 5. Missing transparency data receives a non-zero floor of 1/20.
    """
    max_score = 20
    audit_points = 0
    audit_age_days = None

    if inputs.audit_status.lower() == "audited" and inputs.audit_date:
        try:
            audit_date = date.fromisoformat(inputs.audit_date)
            as_of_date = date.fromisoformat(inputs.as_of_date)
            audit_age_days = (as_of_date - audit_date).days
            if 0 <= audit_age_days <= 365:
                audit_points = 10
            elif 365 < audit_age_days <= 730:
                audit_points = 6
        except ValueError:
            audit_points = 0

    reserve_points = 5 if inputs.reserve_reports else 0
    legal_points = 5 if inputs.public_legal_docs else 0
    score = audit_points + reserve_points + legal_points

    provenance = inputs.provenance
    if score == 0:
        score = 1
        provenance = DataProvenance.INSUFFICIENT

    return DimensionResult(
        score=score,
        max_score=max_score,
        provenance=provenance,
        details={
            "audit_points": audit_points,
            "audit_age_days": audit_age_days,
            "reserve_points": reserve_points,
            "legal_points": legal_points,
        },
    )
