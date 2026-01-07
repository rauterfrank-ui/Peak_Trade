# Peak_Trade – Evidence Index (v0.1)

**Scope:** Living operational artifact for tracking evidence items related to CI runs, drills, tests, incidents, and process artifacts.  
**Purpose:** Centralized index for nachvollziehbarkeit (traceability) of operational evidence—NOT a compliance claim.  
**Owner:** ops  
**Status:** v0.1 (Operational - 16 entries)

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

### Drill / Operator Evidence
- **EV-20260107-P0-BASELINE** — Phase 0 Multi-Agent Roleplay baseline verification (5/5 gate criteria, 6079 tests, 73/73 config smoke tests)
- **EV-20260107-WP5A-DRILL** — Phase 5 NO-LIVE Drill Pack (5-step procedure, 8 templates, operator readiness, PR #504)
- **EV-20260103-CI-RULESETS-RUNBOOK** — GitHub Rulesets operator troubleshooting runbook (mergeable UNKNOWN quickflow)

### Incident / RCA Evidence
- **EV-20260107-EXEC-TELEM-RUNBOOK** — Execution telemetry incident runbook (Phase 16D, PR #370)

### Config Snapshot Evidence
- **EV-20260107-BOUNDED-LIVE-CONFIG** — Bounded-live Phase 1 config (PR #441, commit 6e568152, governance limits, phase progression criteria)

### Test / Refactor Evidence
- **EV-20251228-PHASE8A** — Phase 8A: Kupiec POF deduplication (138/138 tests, single canonical engine)
- **EV-20251228-PHASE8B** — Phase 8B: Christoffersen stdlib-only refactoring (112/112 tests, CLI demo, numpy/scipy removed)
- **EV-20251228-PHASE8D** — Phase 8D: Traffic Light deduplication (93/93 tests, binomial thresholds)

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

---

**Version:** v0.1  
**Maintained by:** ops  
**Last Updated:** 2026-01-07  
**Total Entries:** 16 (1 seed + 15 operational)  
**Next Review:** [TBD] (recommend quarterly or pre-phase-gate)
