# Peak_Trade – Evidence Index (v0.1)

**Scope:** Living operational artifact for tracking evidence items related to CI runs, drills, tests, incidents, and process artifacts.  
**Purpose:** Centralized index for nachvollziehbarkeit (traceability) of operational evidence—NOT a compliance claim.  
**Owner:** ops  
**Status:** v0.1 (Operational - 9 entries)

---

## How to Add Evidence

**What is Evidence?**
Evidence items are operational artifacts that document system behavior, process execution, or decision-making. Examples:
- CI workflow run (GitHub Actions URL)
- PR merge + merge-log doc
- Test output (pytest result, coverage report)
- Drill session log (NO-LIVE drill, smoke test)
- Incident postmortem or RCA doc
- Config snapshot (e.g., required checks snapshot)

**Minimal Fields per Entry:**
- **Evidence ID:** Unique identifier (e.g., `EV-001`, `EV-YYYYMMDD-<name>`)
- **Date:** ISO 8601 format (`YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ`)
- **Owner:** Responsible party (username, team, or role)
- **Source Link:** URL (GitHub PR/run/commit) or repo path (`docs/ops/...`)
- **Claim:** What this evidence demonstrates (brief, factual)
- **Verification:** How to verify authenticity (hash, CI status, reproducible command)
- **Notes:** Optional context or caveats

**Format:** Prefer table format (below) for consistency. Fehlende Details als `[TBD]` markieren, NICHT als freies TODO.

---

## Evidence Registry

| Evidence ID | Date | Owner | Source Link | Claim / What It Demonstrates | Verification | Notes |
|-------------|------|-------|-------------|------------------------------|--------------|-------|
| EV-20260107-SEED | 2026-01-07 | ops | [PR #596 Merge Log](PR_596_MERGE_LOG.md) | Placeholder policy v0 merged with CI green | GitHub PR status: merged, checks passed | Seed entry (example); no live trading claim |
| EV-20260107-P0-BASELINE | 2026-01-07 | ops | [Inline: main@8a41315d] | Phase 0 Multi-Agent Roleplay complete: 5/5 gate criteria passed, 6079 tests discovered, 73/73 config smoke tests green (3.04s) | pytest 8.4.2, Python 3.9.6, workspace CLEAN, no active sessions | Phase 0→Phase 1 transition cleared |
| EV-20260103-CI-HARDENING | 2026-01-03 | ops | [docs/ops/CI_HARDENING_SESSION_20260103.md](CI_HARDENING_SESSION_20260103.md) | CI required checks hardening session: PRs #512, #514, #515 merged (9caf5eb→5a93f19), fail-open changes, PR-isolated concurrency, operator runbook | Required checks tests (3.11) deterministic, ci-required-contexts-contract guard active, mergeable UNKNOWN quickflow documented | Session included contract guard strengthening + runbook deployment |
| EV-20251228-PHASE8A | 2025-12-28 | ops | [PHASE8A_MERGE_LOG.md](../../PHASE8A_MERGE_LOG.md) | Phase 8A: Kupiec POF deduplication complete, single canonical engine established, 138/138 tests passed | Branch: refactor/kupiec-pof-single-engine, delegation tests verify wrapper correctness, zero breaking changes | Ready for merge, risk: VERY LOW (refactor-only) |
| EV-20251228-PHASE8D | 2025-12-28 | ops | [PHASE8D_MERGE_LOG.md](../../PHASE8D_MERGE_LOG.md) | Phase 8D: Traffic Light deduplication complete, binomial-based thresholds, 93/93 tests passed | Canonical engine unchanged, 12 delegation tests, backward compatibility maintained | Ready for merge, risk: VERY LOW, follows Phase 8A pattern |
| EV-20260107-PR518 | 2026-01-07 | ops | [docs/ops/PR_518_CI_HEALTH_PANEL_V0_2.md](PR_518_CI_HEALTH_PANEL_V0_2.md) | PR #518: CI Health Panel v0.2 - persistent snapshots (JSON + Markdown), 20/20 tests passed | Atomic writes via os.replace(), error handling tested, snapshot integrity verified | Ready for review, risk: LOW (read-only, local-only) |
| EV-20260107-PR519 | 2026-01-07 | ops | [docs/ops/PR_519_CI_HEALTH_BUTTONS_V0_2.md](PR_519_CI_HEALTH_BUTTONS_V0_2.md) | PR #519: CI Health Panel v0.2 - Run-Now buttons + auto-refresh, 27/27 tests passed | In-memory lock prevents parallel runs (HTTP 409), fetch-based updates, XSS-safe | Ready for review, risk: LOW (local-only, no destructive ops) |
| EV-20260107-BOUNDED-LIVE-CONFIG | 2026-01-07 | ops | [config/bounded_live.toml](../../config/bounded_live.toml) | Bounded-live Phase 1 config snapshot: $100 daily loss limit, $500 total exposure, strict enforcement (no overrides), kill switch required | Commit 6e568152 (PR #441), enforce_limits=true, allow_override=false, require_kill_switch_active=true, 7-day min phase duration | Governance-critical config, Phase 1→2 progression requires zero breaches + formal review |
| EV-20260107-EXEC-TELEM-RUNBOOK | 2026-01-07 | ops | [docs/ops/EXECUTION_TELEMETRY_INCIDENT_RUNBOOK.md](EXECUTION_TELEMETRY_INCIDENT_RUNBOOK.md) | Execution telemetry incident runbook (Phase 16D Ops Pack): 7 diagnostic commands, symptom→action mapping, read-only diagnostics | Commit b194a622 (PR #370), covers missing fills, latency spikes, parse errors, session log analysis | Operator reference for execution telemetry incidents, no system changes |

---

## Evidence by Category

### CI / Workflow Evidence
- **EV-20260107-SEED** — Placeholder standards PR (example seed entry)
- **EV-20260103-CI-HARDENING** — CI required checks hardening session (PRs #512, #514, #515)
- **EV-20260107-PR518** — CI Health Panel v0.2 - Persistent snapshots
- **EV-20260107-PR519** — CI Health Panel v0.2 - Run-Now buttons

### Drill / Operator Evidence
- **EV-20260107-P0-BASELINE** — Phase 0 Multi-Agent Roleplay baseline verification

### Incident / RCA Evidence
- **EV-20260107-EXEC-TELEM-RUNBOOK** — Execution telemetry incident runbook (Phase 16D, PR #370)

### Config Snapshot Evidence
- **EV-20260107-BOUNDED-LIVE-CONFIG** — Bounded-live Phase 1 config (PR #441, commit 6e568152)

### Test / Refactor Evidence
- **EV-20251228-PHASE8A** — Phase 8A: Kupiec POF deduplication (138/138 tests)
- **EV-20251228-PHASE8D** — Phase 8D: Traffic Light deduplication (93/93 tests)

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-07 | v0 Initial — 1 seed entry (PR #596 example) | ops |
| 2026-01-07 | Added EV-20260107-P0-BASELINE (Phase 0 Multi-Agent Roleplay complete) | ops |
| 2026-01-07 | Added 5 Priority 1 evidence entries (CI Hardening, Phase 8A/8D, PR 518/519) | ops |
| 2026-01-07 | Added EV-20260107-BOUNDED-LIVE-CONFIG (Priority 2: Config Snapshot) | ops |
| 2026-01-07 | Added EV-20260107-EXEC-TELEM-RUNBOOK (Priority 3: Incident/Runbook) | ops |

---

**Version:** v0.1  
**Maintained by:** ops  
**Last Updated:** 2026-01-07  
**Total Entries:** 9 (1 seed + 8 operational)  
**Next Review:** [TBD] (recommend quarterly or pre-phase-gate)
