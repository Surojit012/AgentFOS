# Changelog

## 2026-06-16

- Added AgentFOS Risk Engine v2 with deterministic five-dimension scoring.
- Added score provenance per dimension: `live`, `degraded`, and `insufficient`.
- Added additive `/risk` response fields: `rating`, `overall_confidence`, `breakdown`, `scored_at`, and `schema_version`.
- Preserved backward compatibility for existing consumers that only read top-level `risk_score`.
