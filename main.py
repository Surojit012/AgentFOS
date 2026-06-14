"""
AgentFOS — Bloomberg Terminal for RWAs, callable by AI agents.

FastAPI application exposing 6 endpoints:
- POST /policy      — check if agent action is allowed
- POST /opportunity — fetch RWA yield opportunities
- POST /risk        — score a protocol deterministically
- POST /allocate    — generate capital allocation
- POST /agent       — natural language orchestration
- GET  /health      — health check
"""

import re
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models.schemas import (
    RiskTolerance,
    PolicyAction,
    PolicyRequest,
    PolicyResponse,
    OpportunityRequest,
    OpportunityResponse,
    RiskRequest,
    RiskResponse,
    AllocationRequest,
    AllocationResponse,
    AgentRequest,
    AgentResponse,
    AgentStep,
)
from skills.policy import PolicyEngine
from skills.opportunity import OpportunityEngine
from skills.risk import RiskEngine
from skills.allocation import AllocationEngine
from services.defillama import fetch_all_protocols

# ── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AgentFOS",
    description=(
        "RealFi Yield Intelligence Network — Bloomberg Terminal for RWAs, "
        "callable by AI agents. Discover RWA opportunities, evaluate risk, "
        "enforce spending policies, and generate capital allocation decisions."
    ),
    version=settings.APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Engine Instances ─────────────────────────────────────────────────────────

policy_engine = PolicyEngine()
opportunity_engine = OpportunityEngine()
risk_engine = RiskEngine()
allocation_engine = AllocationEngine()

# ── Root & Health ────────────────────────────────────────────────────────────


@app.get("/")
async def root():
    return {
        "name": "AgentFOS",
        "tagline": "Every other agent knows what to buy. AgentFOS decides if it should.",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


# ── POST /policy ─────────────────────────────────────────────────────────────


@app.post("/policy", response_model=PolicyResponse)
async def evaluate_policy(request: PolicyRequest) -> PolicyResponse:
    """Check if an agent action is allowed under current policy rules."""
    return await policy_engine.evaluate(request)


# ── POST /opportunity ────────────────────────────────────────────────────────


@app.post("/opportunity", response_model=OpportunityResponse)
async def discover_opportunities(request: OpportunityRequest) -> OpportunityResponse:
    """Fetch RWA yield opportunities with benchmark enrichment."""
    return await opportunity_engine.discover(request)


# ── POST /risk ───────────────────────────────────────────────────────────────


@app.post("/risk", response_model=RiskResponse)
async def score_risk(request: RiskRequest) -> RiskResponse:
    """Score a protocol deterministically using risk weights."""
    # Fetch live TVL for the protocol
    try:
        protocol_data = await fetch_all_protocols()
        tvl = protocol_data.get(request.protocol, {}).get("tvl", 0)
    except Exception:
        from config import MOCK_PROTOCOL_DATA
        tvl = MOCK_PROTOCOL_DATA.get(request.protocol, {}).get("tvl", 0)

    return risk_engine.evaluate(request.protocol, tvl)


# ── POST /allocate ───────────────────────────────────────────────────────────


@app.post("/allocate", response_model=AllocationResponse)
async def generate_allocation(request: AllocationRequest) -> AllocationResponse:
    """Generate capital allocation with risk-adjusted scoring and AI narrative."""
    return await allocation_engine.allocate(request)


# ── POST /agent ──────────────────────────────────────────────────────────────


def _parse_agent_query(query: str, capital: float = None, risk_tolerance: str = None):
    """
    Parse natural language query to extract capital and risk tolerance.

    Handles queries like:
    - "Find low risk RWAs above treasury yields"
    - "Allocate $100k to medium risk protocols"
    - "What are the safest RWA yields?"
    """
    parsed_capital = capital
    parsed_risk = risk_tolerance

    # Extract capital from query if not explicitly provided
    if parsed_capital is None:
        # Match patterns like $100k, $100,000, 100000, $1M, etc.
        money_patterns = [
            (r'\$(\d+(?:\.\d+)?)\s*[mM]', lambda m: float(m.group(1)) * 1_000_000),
            (r'\$(\d+(?:\.\d+)?)\s*[kK]', lambda m: float(m.group(1)) * 1_000),
            (r'\$(\d[\d,]*(?:\.\d+)?)', lambda m: float(m.group(1).replace(',', ''))),
            (r'(\d[\d,]+)\s*(?:dollars|usd)', lambda m: float(m.group(1).replace(',', ''))),
        ]
        for pattern, extractor in money_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                parsed_capital = extractor(match)
                break

        if parsed_capital is None:
            parsed_capital = 100_000  # Default capital

    # Extract risk tolerance from query if not explicitly provided
    if parsed_risk is None:
        query_lower = query.lower()
        if any(w in query_lower for w in ["low risk", "safe", "conservative", "safest"]):
            parsed_risk = "low"
        elif any(w in query_lower for w in ["high risk", "aggressive", "risky"]):
            parsed_risk = "high"
        else:
            parsed_risk = "medium"

    return parsed_capital, parsed_risk


@app.post("/agent", response_model=AgentResponse)
async def agent_orchestrate(request: AgentRequest) -> AgentResponse:
    """
    Natural language orchestration — runs all skills in sequence:
    1. Parse query for capital + risk tolerance
    2. Run OpportunityEngine
    3. Run RiskEngine on each result
    4. Run PolicyEngine check
    5. Run AllocationEngine
    6. Return AgentResponse with steps + recommendation
    """
    steps = []

    # Step 0: Parse query
    capital, risk_str = _parse_agent_query(
        request.query,
        capital=request.capital,
        risk_tolerance=request.risk_tolerance.value if request.risk_tolerance else None,
    )
    risk_tolerance = RiskTolerance(risk_str)

    steps.append(AgentStep(
        step="Parse Query",
        status="complete",
        result=f"Capital: ${capital:,.0f}, Risk tolerance: {risk_str}",
    ))

    # Step 1: Discover opportunities
    opp_request = OpportunityRequest(risk_level=risk_tolerance)
    opportunities = await opportunity_engine.discover(opp_request)

    steps.append(AgentStep(
        step="Opportunity Discovery",
        status="complete",
        result=f"{opportunities.count} opportunities found (treasury benchmark: {opportunities.treasury_rate}%)",
    ))

    # Step 2: Risk score each protocol
    risk_results = {}
    for asset in opportunities.assets:
        risk_result = risk_engine.evaluate(asset.protocol_key, asset.tvl)
        risk_results[asset.protocol_key] = risk_result

    risk_summary = ", ".join(
        f"{r.protocol_name}: {r.risk_score}/100 ({r.risk_level.value})"
        for r in risk_results.values()
    )
    steps.append(AgentStep(
        step="Risk Scoring",
        status="complete",
        result=risk_summary if risk_summary else "No protocols to score",
    ))

    # Step 3: Policy check — verify that at least one allocation would pass
    policy_pass = True
    policy_reasons = []
    for asset in opportunities.assets:
        policy_req = PolicyRequest(
            action=PolicyAction.INVEST,
            amount=capital / max(len(opportunities.assets), 1),
            asset=asset.protocol_key,
            risk_tolerance=risk_tolerance,
        )
        policy_result = await policy_engine.evaluate(policy_req)
        if not policy_result.allowed:
            policy_reasons.append(f"{asset.name}: {policy_result.reason}")

    passed_count = len(opportunities.assets) - len(policy_reasons)
    steps.append(AgentStep(
        step="Policy Check",
        status="complete",
        result=f"Policy PASS for {passed_count}/{len(opportunities.assets)} protocols"
        + (f". Blocked: {'; '.join(policy_reasons)}" if policy_reasons else ""),
    ))

    # Step 4: Generate allocation
    alloc_request = AllocationRequest(
        capital=capital,
        risk=risk_tolerance,
    )
    allocation = await allocation_engine.allocate(alloc_request)

    if allocation.allocations:
        top = allocation.allocations[0]
        alloc_summary = (
            f"Top allocation: {top.name} ({top.allocation_pct}% / "
            f"${top.allocation_amount:,.0f}) — APY {top.apy}%, "
            f"risk score {top.risk_score}, spread +{top.apy_vs_treasury}% vs treasury"
        )
    else:
        alloc_summary = "No allocations generated (filters too restrictive)"

    steps.append(AgentStep(
        step="Capital Allocation",
        status="complete",
        result=alloc_summary,
    ))

    # Build final answer
    if allocation.allocations:
        answer = (
            f"Analyzed {opportunities.count} RWA protocols for ${capital:,.0f} at "
            f"{risk_str} risk tolerance. Portfolio yields {allocation.portfolio_avg_apy}% "
            f"average APY with +{allocation.portfolio_spread}% spread over "
            f"{allocation.treasury_benchmark}% Treasury benchmark. "
            f"{allocation.narrative or ''}"
        )
    else:
        answer = (
            f"No suitable RWA protocols found for ${capital:,.0f} at {risk_str} "
            f"risk tolerance. Consider adjusting risk parameters or capital amount."
        )

    return AgentResponse(
        query=request.query,
        steps=steps,
        recommendation=allocation if allocation.allocations else None,
        answer=answer,
    )
