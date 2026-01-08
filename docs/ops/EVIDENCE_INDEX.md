# Peak_Trade – Evidence Index (v0.2)

**Scope:** Living operational artifact for tracking evidence items related to CI runs, drills, tests, incidents, and process artifacts.  
**Purpose:** Centralized index for nachvollziehbarkeit (traceability) of operational evidence—NOT a compliance claim.  
**Owner:** ops  
**Status:** v0.2 (Operational - 20 entries)

---

## Fast Path (Quick Commands)

**Generate new entry:**
```bash
python scripts/ops/generate_evidence_entry.py --tag <TAG> --category "<CATEGORY>" --title "<TITLE>"
```

**Validate Index:**
```bash
python scripts/ops/validate_evidence_index.py
```

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
| EV-20260107-PR605 | 2026-01-07 | ops | [PR #605 Merge Log](PR_605_MERGE_LOG.md) | PR #605: Audit dependency remediation (urllib3, wheel CVEs) + Makefile fix + docs-reference-targets-gate unblocked, 19/19 CI checks passed | Commit 59fa5eb4 (squash merge), all gates green (Audit 1m11s, Policy Critic 1m17s, tests 3.9/3.10/3.11 all pass), docs stale path reference removed | Security remediation + build tooling fix, zero regressions |
| EV-20260103-CI-RULESETS-RUNBOOK | 2026-01-03 | ops | [docs/ops/runbooks/github_rulesets_pr_reviews_policy.md](runbooks/github_rulesets_pr_reviews_policy.md) | GitHub Rulesets & Mergeable UNKNOWN operator quickflow (PR #514): 6-step diagnostic procedure, CLI-based verification, Source-of-Truth merge attempt protocol | Deployed as part of CI hardening session (commits 25f9686→bced46a), referenced in 3 locations (runbook, ops README, ci.yml workflow), operator-facing documentation | PR-merge blocker troubleshooting guide, deterministic decision tree for UNKNOWN mergeable states |
| EV-20251228-PHASE8B | 2025-12-28 | ops | [PHASE8B_MERGE_LOG.md](../../PHASE8B_MERGE_LOG.md) | Phase 8B: Christoffersen Independence + Conditional Coverage VaR backtests - stdlib-only refactoring (numpy/scipy removed), 112/112 tests passed (31 new tests) | Branch: refactor/christoffersen-stdlib, Phase 8B API + legacy API preserved, CLI demo validates clustering detection, Chi²(1) via erfc, Chi²(2) via exp(-x/2) | Zero breaking changes, backward compatible, comprehensive edge case coverage (transition matrix, LR decomposition, monotonic sanity) |
| EV-20260107-WP5A-DRILL | 2026-01-07 | ops | [docs/ops/WP5A_PHASE5_NO_LIVE_DRILL_PACK.md](WP5A_PHASE5_NO_LIVE_DRILL_PACK.md) + [templates/phase5_no_live/](templates/phase5_no_live/) | Phase 5 NO-LIVE Drill Pack: 5-step operator procedure (Environment Setup, Systems Check, Strategy Dry-Run, Evidence Assembly, Go/No-Go), 8 templates (checklists, evidence, postmortem) | PR #504 (merged), NO-LIVE banner in all templates, hard prohibitions (no API keys, no real orders), GO = drill passed (NOT live authorization), two-person rule enforced | Operator readiness framework, risk: LOW (docs-only, no runtime code), 100 min estimated drill duration |
| EV-20260107-CI-MATRIX-CONTRACT | 2026-01-07 | ops | [.github/workflows/ci.yml](../../.github/workflows/ci.yml#L40-L89) | CI Required Checks Matrix Naming Contract: Deterministic test discovery via `tests (${{ matrix.python-version }})` format, Python 3.11 guaranteed, job-level `if:` prohibited on required jobs | Guard job `ci-required-contexts-contract` blocks drift, checks: explicit names, matrix variables in names, Python 3.11 in matrix, PR-isolated concurrency | Ensures `tests (3.11)` and `strategy-smoke` materialize on every PR (docs-only or code-changes), fail-open safe |
| EV-20260107-DOCS-REF-GATE | 2026-01-07 | ops | [scripts/ops/collect_docs_reference_targets_fullscan.py](../../scripts/ops/collect_docs_reference_targets_fullscan.py) | Docs Reference Targets Gate: Link validation (3229 links, 3079 valid), baseline tracking (3229_valid_links.txt), triage workflow for new stale links | Scans `docs/`, `templates/`, `*.md` files; detects dead paths, broken references; CI integration via `make docs-reference-targets-check`; triage protocol: accept, fix, or defer stale links | Prevents documentation drift, evidence: baseline commit, gate pass/fail status in CI logs |
| EV-20260107-EXEC-PIPELINE-RUNBOOK | 2026-01-07 | ops | [docs/runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md](../runbooks/EXECUTION_PIPELINE_GOVERNANCE_RISK_RUNBOOK_V1.md) | ExecutionPipeline Governance & Risk Runbook v1.1 (Phase 16A V2): Live-order-execution permanently locked via `_FEATURE_STATUS_MAP["live_order_execution"] = "locked"`, NO executor dispatch to live env until governance sign-off, operator diagnostic procedures for BLOCKED_BY_GOVERNANCE/BLOCKED_BY_RISK/KILLED/INVALID statuses | Runbook references governance feature lock (src/governance/go_no_go.py), ExecutionStatus enum (BLOCKED_BY_GOVERNANCE), pipeline safety principles (no executor call if governance-locked), verification: `grep "live_order_execution" src/governance/go_no_go.py` should show "locked" | Governance-critical: Hard lock prevents live orders until multi-stakeholder approval; runbook version v1.1 (2026-ready), scope: Paper/Shadow/Testnet only, NO live routing |
| EV-20251230-KILL-SWITCH-DRILL | 2025-12-30 | ops | [docs/runbooks/KILL_SWITCH_DRILL_PROCEDURE.md](../runbooks/KILL_SWITCH_DRILL_PROCEDURE.md) | Kill Switch Drill Procedure v1.0: Monthly operator drill protocol (Scenario 1: Manual Trigger, Scenario 2: Recovery, Scenario 3: Multiple Systems), pre-drill checklist (test env ready, no real trading), drill documentation template, post-drill review requirements | Drill commands: `python -m src.risk_layer.kill_switch.cli status/trigger/reset`, success criteria: kill switch triggers within 5 seconds, all systems stop within 30 seconds, recovery completes within 5 minutes, drill log stored per run | NO-LIVE drill (shadow/testnet only), monthly frequency recommended, operator readiness evidence, audit trail: drill session logs + signed off by drill lead |
| EV-20251230-LIVE-TRANSITION-RUNBOOK | 2025-12-30 | ops | [docs/runbooks/LIVE_MODE_TRANSITION_RUNBOOK.md](../runbooks/LIVE_MODE_TRANSITION_RUNBOOK.md) | Live Mode Transition Runbook v1.0 (One-Way-Gate): Phase 1 Bounded-Live procedure, 4 required approvals (Risk/Security/Operations/System Owner), pre-transition checklist (kill switch tested, risk limits configured, operators trained), 3-gate activation protocol (enable_live_trading/live_mode_state/live_dry_run_mode), rollback procedure (limited window), post-transition monitoring (first 24h critical) | Bounded-live config reference: `config/bounded_live.toml`, verification: pre-transition health check (kill switch drill completion, risk limits configured, operators trained), NO go-live without 4/4 sign-offs | Governance-critical: One-way-gate requires multi-stakeholder approval; Phase 1 limits: $50/order, $500 total exposure, $100 daily loss; Phase 1→2 progression criteria: 7 days zero breaches + formal review |
| EV-20260103-CI-CONTRACT-GUARD | 2026-01-03 | ops | [scripts/ops/check_required_ci_contexts_present.sh](../../scripts/ops/check_required_ci_contexts_present.sh) + [.github/workflows/ci.yml#L40-L89](../../.github/workflows/ci.yml#L40-L89) | CI Required Contexts Contract Guard (PR #515, commit 5a93f19): Blocks CI-workflow drift, enforces deterministic job naming (`tests (${{ matrix.python-version }})`), guarantees Python 3.11 in matrix, prohibits job-level `if:` on required jobs (`tests`, `strategy-smoke`), ensures PR-isolated concurrency (no cross-PR cancels) | Guard script: `scripts/ops/check_required_ci_contexts_present.sh`, runs on every PR as `ci-required-contexts-contract` job, exit code 1 if drift detected, fail-open safe (conservative: if changes-job fails, tests run anyway), contract enforces: explicit names, matrix vars in names, Python 3.11 present, PR-isolated concurrency | CI/Workflow Governance: Part of 2026-01-03 CI Hardening Session (PRs #512/#514/#515), ensures required checks materialize on every PR (docs-only or code-changes), prevents GitHub Ruleset blocking due to missing contexts |
| EV-20251228-PHASE8-STDLIB-REFACTOR | 2025-12-28 | ops | [PHASE8A_MERGE_LOG.md](../../PHASE8A_MERGE_LOG.md) + [PHASE8B_MERGE_LOG.md](../../PHASE8B_MERGE_LOG.md) + [PHASE8D_MERGE_LOG.md](../../PHASE8D_MERGE_LOG.md) | Phase 8 (A/B/D) VaR Backtest Stdlib-Only Refactoring: Kupiec POF (138/138 tests), Christoffersen IND/CC (112/112 tests, numpy/scipy removed, Chi²(1) via erfc, Chi²(2) via exp(-x/2)), Traffic Light (93/93 tests, binomial thresholds), single canonical engines established, zero breaking changes, comprehensive delegation tests, backward-compatible legacy APIs preserved | Test evidence: `pytest tests/risk_layer/var_backtest/ -q` (all pass), `pytest tests/risk/validation/ -q` (delegation + legacy), CLI demos: `scripts/risk/run_christoffersen_demo.py`, linting clean (`ruff check . --quiet`), refactor-only (no new features), risk: VERY LOW (100% test coverage, reversible) | Stdlib-only claim: no numpy/scipy dependencies in Phase 8B Christoffersen (pure math.erfc/exp), canonical engines in src/risk_layer/var_backtest/, legacy wrappers in src/risk/validation/ delegate to canonical |

---

## Evidence by Category

### CI / Workflow Evidence
- **EV-20260107-SEED** — Placeholder standards PR (example seed entry)
- **EV-20260103-CI-HARDENING** — CI required checks hardening session (PRs #512, #514, #515)
- **EV-20260103-CI-RULESETS-RUNBOOK** — GitHub Rulesets & Mergeable UNKNOWN operator quickflow (PR #514)
- **EV-20260107-PR518** — CI Health Panel v0.2 - Persistent snapshots
- **EV-20260107-PR519** — CI Health Panel v0.2 - Run-Now buttons
- **EV-20260107-PR605** — Audit dependency remediation + Makefile fix + docs-reference-targets-gate (PR #605)
- **EV-20260107-DOCS-REF-GATE** — Docs Reference Targets Gate (link validation, baseline tracking, triage)
- **EV-20260107-CI-MATRIX-CONTRACT** — CI Required Checks Matrix Naming Contract (deterministic test discovery)
- **EV-20260103-CI-CONTRACT-GUARD** — CI Required Contexts Contract Guard (PR #515, deterministic job naming, Python 3.11 guarantee)

### Drill / Operator Evidence
- **EV-20260107-P0-BASELINE** — Phase 0 Multi-Agent Roleplay baseline verification (5/5 gate criteria, 6079 tests, 73/73 config smoke tests)
- **EV-20260107-WP5A-DRILL** — Phase 5 NO-LIVE Drill Pack (5-step procedure, 8 templates, operator readiness, PR #504)
- **EV-20260103-CI-RULESETS-RUNBOOK** — GitHub Rulesets operator troubleshooting runbook (mergeable UNKNOWN quickflow)
- **EV-20251230-KILL-SWITCH-DRILL** — Kill Switch Drill Procedure v1.0 (monthly operator drills, 3 scenarios, SLAs)

### Governance / Runbook Evidence
- **EV-20260107-EXEC-PIPELINE-RUNBOOK** — ExecutionPipeline Governance & Risk Runbook v1.1 (live-execution locked, NO-LIVE enforcement)
- **EV-20251230-LIVE-TRANSITION-RUNBOOK** — Live Mode Transition Runbook v1.0 (One-Way-Gate, 4 sign-offs, Phase 1 Bounded-Live)

### Incident / RCA Evidence
- **EV-20260107-EXEC-TELEM-RUNBOOK** — Execution telemetry incident runbook (Phase 16D, PR #370)

### Config Snapshot Evidence
- **EV-20260107-BOUNDED-LIVE-CONFIG** — Bounded-live Phase 1 config (PR #441, commit 6e568152, governance limits, phase progression criteria)

### Test / Refactor Evidence
- **EV-20251228-PHASE8A** — Phase 8A: Kupiec POF deduplication (138/138 tests, single canonical engine)
- **EV-20251228-PHASE8B** — Phase 8B: Christoffersen stdlib-only refactoring (112/112 tests, CLI demo, numpy/scipy removed)
- **EV-20251228-PHASE8D** — Phase 8D: Traffic Light deduplication (93/93 tests, binomial thresholds)
- **EV-20251228-PHASE8-STDLIB-REFACTOR** — Phase 8 (A/B/D) VaR Backtest Stdlib-Only Refactoring (343 tests total, numpy/scipy removed)

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-07 | v0 Initial — 1 seed entry (PR #596 example) | ops |
| 2026-01-07 | Added EV-20260107-P0-BASELINE (Phase 0 Multi-Agent Roleplay complete) | ops |
| 2026-01-07 | Added 5 Priority 1 evidence entries (CI Hardening, Phase 8A/8D, PR 518/519) | ops |
| 2026-01-07 | Added EV-20260107-BOUNDED-LIVE-CONFIG (Priority 2: Config Snapshot) | ops |
| 2026-01-07 | Added EV-20260107-EXEC-TELEM-RUNBOOK (Priority 3: Incident/Runbook) | ops |
| 2026-01-07 | v0.1 Expansion: Added 6 high-value entries (CI-RULESETS-RUNBOOK, PHASE8B, WP5A-DRILL, CI-MATRIX-CONTRACT, DOCS-REF-GATE, PR605), total: 16 entries | ops |
| 2026-01-07 | v0.2 Tier-B Expansion: Added 5 high-value entries (Exec Pipeline Runbook, Kill Switch Drill, Live Transition Runbook, CI Contract Guard, Phase 8 Stdlib Refactor), total: 20 entries | ops |

---

**Version:** v0.2  
**Maintained by:** ops  
**Last Updated:** 2026-01-07  
**Total Entries:** 20 (1 seed + 19 operational)  
**Next Review:** [TBD] (recommend quarterly or pre-phase-gate)
