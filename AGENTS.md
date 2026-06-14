# AgentFOS — Build Rules

## What We Are Building
RealFi Yield Intelligence Network — "Bloomberg Terminal for RWAs, 
callable by AI agents." A Financial Operating System that lets 
autonomous agents discover RWA opportunities, evaluate risk, enforce 
spending policies, and generate capital allocation decisions on Pharos.

## Non-Negotiable Rules
- NO database (no Postgres, no SQLAlchemy, no Redis)
- NO LangChain, NO CrewAI, NO vector DB
- NO placeholder functions, NO TODO comments
- NO stubs — every function must have real working logic
- Mock fallback on EVERY external API call — demo must never crash
- Pydantic validates every input and output
- One responsibility per file
- fredapi for FRED Treasury data (not fedfred)

## Stack
fastapi, uvicorn[standard], httpx, pandas, numpy, pydantic,
pydantic-settings, fredapi, yfinance, beautifulsoup4, lxml,
anthropic, python-dotenv, aiohttp

## Project Structure (DO NOT DEVIATE)
AgentFOS/
├── main.py
├── config.py
├── requirements.txt
├── .env.example
├── AGENTS.md
├── skills/
│   ├── policy.py
│   ├── opportunity.py
│   ├── risk.py
│   └── allocation.py
├── services/
│   ├── defillama.py
│   ├── benchmarks.py
│   └── protocols.py
├── models/
│   └── schemas.py
├── intelligence/
│   └── summarizer.py
└── prompts/
    └── summarize.txt

## The 6 Protocols (deep data, not shallow)
ondo, zoth, maple, centrifuge, backed, opentrade

## Risk Scoring (deterministic math, not AI)
score = 100
if tvl < 1_000_000: score -= 30
if tvl < 10_000_000: score -= 15
if age_days < 180: score -= 25
if age_days < 365: score -= 10
if audit_status == "unaudited": score -= 30
if issuer_concentration == "high": score -= 20
if issuer_concentration == "medium": score -= 10

## API Endpoints
POST /policy      — check if agent action is allowed
POST /opportunity — fetch RWA yield opportunities
POST /risk        — score a protocol deterministically
POST /allocate    — generate capital allocation
POST /agent       — natural language orchestration

## Mock Fallbacks Required For
- DefiLlama API
- FRED Treasury rates
- yfinance benchmarks
All mocks live in config.py as MOCK_* constants.