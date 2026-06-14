# AgentFOS — Build Rules

## What We Are Building

AgentFOS is the financial decision layer for autonomous agents.

It is not a chatbot, not a trading bot, and not a dashboard. It is deterministic infrastructure that lets agents:

- discover RWA opportunities
- evaluate risk with transparent math
- enforce capital allocation policy
- produce allocation recommendations
- write a verifiable on-chain proof on Pharos

## Non-Negotiable Rules

- NO database of any kind: no Postgres, no SQLAlchemy, no Redis
- NO LangChain, NO CrewAI, NO vector DB
- NO placeholder functions
- NO TODO comments
- NO stubs: every function must have real working logic
- Mock fallback on every external API call so the demo never crashes
- Pydantic validates every input and every output
- One responsibility per file
- Use `fredapi` for FRED Treasury data, not `fedfred`

## Stack

`fastapi`, `uvicorn[standard]`, `httpx`, `pandas`, `numpy`, `pydantic`, `pydantic-settings`, `fredapi`, `yfinance`, `beautifulsoup4`, `lxml`, `anthropic`, `python-dotenv`, `aiohttp`

## Project Structure

Do not introduce new top-level architecture.

```text
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
```

## Product Identity

Every document and every product surface should reinforce the same flow:

`Agent → Policy Skill → Opportunity Skill → Risk Skill → Allocation Skill → Pharos On-Chain Proof`

That is the product.

## Current Domain Baseline

The working baseline is the six curated RWA protocols:

`ondo`, `zoth`, `maple`, `centrifuge`, `backed`, `opentrade`

This baseline is intentional. It keeps the product focused, understandable, and demo-safe.

## Risk Scoring

Risk scoring is deterministic math, not AI.

```text
score = 100
if tvl < 1_000_000: score -= 30
if tvl < 10_000_000: score -= 15
if age_days < 180: score -= 25
if age_days < 365: score -= 10
if audit_status == "unaudited": score -= 30
if issuer_concentration == "high": score -= 20
if issuer_concentration == "medium": score -= 10
```

## API Surface

- `POST /policy` — check whether an action is allowed
- `POST /opportunity` — fetch RWA yield opportunities
- `POST /risk` — score one protocol deterministically
- `POST /allocate` — generate a capital allocation and write the top result on-chain
- `POST /agent` — natural-language orchestration without the paid write path
- `GET /health` — app health check

## Mock Fallbacks

These external dependencies must always degrade safely:

- DefiLlama API
- FRED Treasury rates
- yfinance benchmarks

All mock values live in `config.py` as `MOCK_*` constants.

## Documentation Rule

If a doc, README, skill reference, or submission page describes the product, it must say the same thing:

- deterministic
- auditable
- verifiable
- on-chain proof
- financial decision layer for autonomous agents
