# Evidence Entry: Bounded Live Phase 1 Config - Governance Limits Snapshot

**Evidence ID:** EV-20260107-BOUNDED-LIVE-V2
**Date:** 2026-01-07
**Category:** Config Snapshot
**Owner:** ops
**Status:** DRAFT

---

## Scope
Bounded-Live Phase 1 configuration snapshot: Governance-enforced risk limits for initial live trading rollout. Covers per-order limits, total exposure caps, daily loss limits, enforcement settings, safety gates, and phase progression criteria.

---

## Claims
- Strict risk limits: $50 max per order, $500 total exposure, $100 max daily loss, 2 max open positions
- Enforcement: `enforce_limits=true`, `allow_override=false`, `require_operator_confirmation=true`
- Safety gates: Kill switch required active, risk limits required enabled, manual bypass disallowed
- Session limits: 4-hour max duration, 1-hour cooldown between sessions, review required after each session
- Phase progression criteria: 7-day minimum, zero kill switch triggers, zero risk breaches, formal review + sign-offs required

---

## Evidence / Source Links
- [Config File: config/bounded_live.toml](../../config/bounded_live.toml)
- [PR #441: Bounded-live Phase 1 config](https://github.com/rauterfrank-ui/Peak_Trade/pull/441)
- [Commit: 6e568152](https://github.com/rauterfrank-ui/Peak_Trade/commit/6e568152)
- Related: Kill Switch Runbook, Risk Layer documentation

---

## Verification Steps
1. Inspect config: `cat config/bounded_live.toml | grep -A 5 '\[bounded_live.limits\]'`
2. Verify enforcement: `grep 'enforce_limits\|allow_override' config/bounded_live.toml`
3. Check safety gates: `grep 'require_kill_switch_active\|require_risk_limits_enabled' config/bounded_live.toml`
4. Validate phase progression: `grep -A 6 '\[bounded_live.phase_progression\]' config/bounded_live.toml`
5. Expected: All limits present, enforcement strict, no override allowed, kill switch required

---

## Risk Notes
- **Governance-critical config**: DO NOT MODIFY without Risk Owner approval + documented justification
- Phase 1→2 progression requires: 7+ days successful operation, zero breaches, formal review + sign-offs
- Config enforces **real money** limits (not paper/shadow) — violations block orders
- Session limits (4h max, 1h cooldown) may impact trading strategies requiring longer sessions
- Phase 2 preview included in config (for reference only, not active in Phase 1)

---

## Related PRs / Commits
- PR #441: Bounded-live Phase 1 config initial deployment
- Commit 6e568152: Config snapshot (2026-01-07)
- Related docs: Kill Switch Runbook, Risk Layer metrics, Live Readiness Phase Tracker

---

## Owner / Responsibility
**Owner:** ops
**Contact:** [TBD]

---

**Entry Created:** 2026-01-07
**Last Updated:** 2026-01-07
**Template Version:** v0.2
