# AgentFOS Risk Engine v2

Risk Engine v2 is a deterministic, auditable scoring system for RWA protocols.

It does not use machine learning, LLM reasoning, or hidden heuristics. Every score is
the sum of five integer dimension scores and can be replayed from a stored input
snapshot.

## Composite Score

The total score is 100 points:

| Dimension | Max |
|---|---:|
| Liquidity | 25 |
| Protocol Maturity | 20 |
| Transparency | 20 |
| Concentration Risk | 20 |
| Yield Sustainability | 15 |

The composite score is:

```text
risk_score = liquidity + maturity + transparency + concentration + yield_sustainability
```

## Determinism Rule

Each dimension returns an integer inside its own allotted range. Any flooring or
bucket selection happens inside the dimension function. The composite function never
rounds floats; it only sums already-final integer scores.

This means the engine intentionally uses:

```text
floor/bucket per dimension, then sum
```

not:

```text
sum raw floats, then round once
```

That rule makes stored snapshots replay byte-for-byte.

## Provenance

Every dimension reports one provenance value:

| Value | Meaning |
|---|---|
| `live` | Fresh primary-source data was used |
| `degraded` | Fallback, stale, partial, or static data was used |
| `insufficient` | No usable data existed; a documented floor score was applied |

Top-level confidence is derived from dimension provenance:

| Condition | Confidence |
|---|---|
| 2+ insufficient dimensions | `low` |
| 1 insufficient dimension or 2+ degraded dimensions | `medium` |
| Otherwise | `high` |

## Dimension Rules

### Liquidity, 25 Points

TVL bucket:

| TVL | Points |
|---|---:|
| `> $500M` | 10 |
| `>= $100M` and `<= $500M` | 7 |
| `>= $10M` and `< $100M` | 4 |
| `> $0` and `< $10M` | 1 |
| Missing, zero, or negative | 1 with `insufficient` provenance |

Optional activity metrics can add up to 15 points, capped at 25 total.

### Protocol Maturity, 20 Points

Protocol age is calculated from a stored `launch_date`.

| Age | Points |
|---|---:|
| `>= 1095 days` | 20 |
| `>= 365 days` and `< 1095 days` | 14 |
| `>= 180 days` and `< 365 days` | 8 |
| `< 180 days` | 4 |
| Missing or invalid date | 4 with `insufficient` provenance |

### Transparency, 20 Points

| Input | Points |
|---|---:|
| Audit within 365 days | 10 |
| Audit within 730 days | 6 |
| Audit older than 730 days or missing | 0 |
| Reserve reports | 5 |
| Public legal docs | 5 |
| No transparency evidence | 1 with `insufficient` provenance |

### Concentration Risk, 20 Points

| Top-5 Holder Concentration | Points |
|---|---:|
| `< 40%` | 20 |
| `40-60%` | 15 |
| `>60-80%` | 10 |
| `>80%` | 5 |
| Missing top-5 data | fallback to issuer concentration as `degraded` |
| `<0%` or `>100%` | 5 with `insufficient` provenance |

Issuer fallback:

| Issuer Concentration | Points |
|---|---:|
| Low | 20 |
| Medium | 15 |
| High | 5 |

### Yield Sustainability, 15 Points

Spread is `RWA yield - Treasury yield`.

| Spread | Points |
|---|---:|
| `<= 2%`, including negative spread | 15 |
| `>2%` and `<=5%` | 12 |
| `>5%` and `<=8%` | 8 |
| `>8%` | 4 |
| Missing yield data | 4 with `insufficient` provenance |

## API Compatibility

Existing consumers can continue to read:

```json
{ "risk_score": 82 }
```

Risk Engine v2 adds fields without removing the old shape:

```json
{
  "risk_score": 82,
  "rating": "Low",
  "overall_confidence": "medium",
  "breakdown": {
    "liquidity": { "score": 22, "max": 25, "provenance": "live" }
  },
  "scored_at": "2026-06-16T10:00:00Z",
  "schema_version": "2.0"
}
```
