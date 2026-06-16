from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


# ── Enums ────────────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class RiskTolerance(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class PolicyAction(str, Enum):
    INVEST = "invest"
    ALLOCATE = "allocate"
    REBALANCE = "rebalance"


# ── Core Asset Model ─────────────────────────────────────────────────────────
# Rich data per protocol — this is our competitive advantage

class Asset(BaseModel):
    protocol_key: str
    name: str
    primary_asset: str
    asset_class: str
    chain: str
    tvl: float
    tvl_change_30d: float               # % change over 30 days
    apy: float
    audit_status: str
    issuer_concentration: str           # Low / Medium / High
    age_days: int
    apy_vs_treasury: Optional[float] = None   # spread vs US 10Y
    apy_vs_rwa_avg: Optional[float] = None    # spread vs RWA average
    risk_score: Optional[int] = None          # 0-100
    risk_level: Optional[RiskLevel] = None
    summary: Optional[str] = None


# ── Policy Skill ─────────────────────────────────────────────────────────────

class PolicyRequest(BaseModel):
    action: PolicyAction
    amount: float = Field(..., gt=0)
    asset: str
    risk_tolerance: RiskTolerance = RiskTolerance.MEDIUM
    max_single_allocation: float = Field(default=0.6, ge=0, le=1)  # max 60% in one asset
    min_risk_score: int = Field(default=50, ge=0, le=100)

class PolicyResponse(BaseModel):
    allowed: bool
    action: str
    asset: str
    amount: float
    reason: Optional[str] = None
    warnings: List[str] = []


# ── Opportunity Skill ─────────────────────────────────────────────────────────

class OpportunityRequest(BaseModel):
    risk_level: RiskTolerance = RiskTolerance.MEDIUM
    min_apy: Optional[float] = None
    min_tvl: Optional[float] = None

class OpportunityResponse(BaseModel):
    assets: List[Asset]
    treasury_rate: float
    rwa_avg_apy: float
    data_source: str                    # "live" or "mock"
    count: int


# ── Risk Skill ───────────────────────────────────────────────────────────────

class RiskRequest(BaseModel):
    protocol: str                       # protocol key e.g. "ondo"

class RiskResponse(BaseModel):
    protocol: str
    protocol_name: str
    risk_score: int                     # 0-100, higher = safer
    risk_level: RiskLevel
    factors: dict                       # breakdown of what affected score
    recommendation: str
    rating: Optional[str] = None
    overall_confidence: Optional[str] = None
    breakdown: Optional[Dict[str, Any]] = None
    scored_at: Optional[str] = None
    schema_version: Optional[str] = None


# ── Allocation Skill ─────────────────────────────────────────────────────────

class AllocationRequest(BaseModel):
    capital: float = Field(..., gt=0)
    risk: RiskTolerance = RiskTolerance.MEDIUM
    min_apy_spread: float = 0.0        # min spread above treasury

class AllocationItem(BaseModel):
    protocol_key: str
    name: str
    asset_class: str
    apy: float
    risk_score: int
    risk_level: RiskLevel
    allocation_pct: float               # % of total capital
    allocation_amount: float            # actual $ amount
    apy_vs_treasury: float
    summary: Optional[str] = None

class AllocationResponse(BaseModel):
    capital: float
    risk_preference: str
    allocations: List[AllocationItem]
    portfolio_avg_apy: float
    portfolio_avg_risk_score: float
    treasury_benchmark: float
    portfolio_spread: float             # portfolio APY - treasury rate
    data_source: str
    narrative: Optional[str] = None     # Claude summary
    onchain_status: Optional[str] = None
    onchain_tx_hash: Optional[str] = None
    onchain_error: Optional[str] = None


# ── Agent Skill ──────────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    query: str
    capital: Optional[float] = None
    risk_tolerance: Optional[RiskTolerance] = None

class AgentStep(BaseModel):
    step: str
    status: str
    result: Optional[str] = None

class AgentResponse(BaseModel):
    query: str
    steps: List[AgentStep]
    recommendation: Optional[AllocationResponse] = None
    answer: str
