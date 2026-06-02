# CI Scheduled Workflow Variable Gates

**Canonical reference** for repository variables that gate scheduled GitHub Actions workflows.

---

## Overview

Several scheduled workflows run only when specific repository variables are set to `true`. When unset or not `true`, the corresponding jobs are **skipped** on schedule triggers. Manual `workflow_dispatch` typically bypasses these gates.

| Variable | Workflow | Job(s) | Default when unset |
|----------|----------|--------|---------------------|
| `PT_PRJ_FEATURES_SMOKE_ENABLED` | prj-scheduled-shadow-paper-features-smoke | prj-features-smoke | Job skipped on schedule |
| `PT_SCHEDULED_PAPER_TESTS_ENABLED` | ci-scheduled-paper-and-export-smoke | paper_tests_audit_evidence | Job skipped |
| `PT_SCHEDULED_EXPORT_VERIFY_ENABLED` | ci-scheduled-paper-and-export-smoke | export_pack_verify | Job skipped |
| `PT_EXPORT_CI_ENABLED` | ci-export-pack-download-verify | export-pack-verify | Job skipped on PR |

---

## PT_PRJ_FEATURES_SMOKE_ENABLED

| Field | Value |
|-------|-------|
| **Purpose** | Enable scheduled PR-J shadow/paper features smoke runs |
| **Workflow** | `.github/workflows/prj-scheduled-shadow-paper-features-smoke.yml` |
| **Job** | prj-features-smoke |
| **When unset** | Job skipped on `schedule`; runs on `workflow_dispatch` |
| **Where to set** | GitHub repo: Settings → Secrets and variables → Actions → Variables |
| **Verification** | `gh variable list` (if permitted); or trigger workflow_dispatch and inspect run |

**Workflow condition:**
```yaml
if: ${{ vars.PT_PRJ_FEATURES_SMOKE_ENABLED == 'true' || github.event_name == 'workflow_dispatch' }}
```

**Related runbook:** `docs/ops/runbooks/prj_scheduled_shadow_paper_features_smoke.md`

---

## PT_SCHEDULED_PAPER_TESTS_ENABLED

| Field | Value |
|-------|-------|
| **Purpose** | Enable scheduled paper-tests-audit-evidence trigger (hourly) |
| **Workflow** | `.github/workflows/ci-scheduled-paper-and-export-smoke.yml` |
| **Job** | paper_tests_audit_evidence |
| **When unset** | Job skipped |
| **Where to set** | GitHub repo: Settings → Secrets and variables → Actions → Variables |
| **Verification** | `gh run list --workflow="CI / Scheduled Paper + Export Smoke" --limit 5` |

**Workflow condition:**
```yaml
if: vars.PT_SCHEDULED_PAPER_TESTS_ENABLED == 'true'
```

**Note:** Job also requires `scripts/ci/scheduled_guardrails.sh` to pass (vars + secrets for export channel).

---

## PT_SCHEDULED_EXPORT_VERIFY_ENABLED

| Field | Value |
|-------|-------|
| **Purpose** | Enable scheduled export-pack verify trigger (hourly) |
| **Workflow** | `.github/workflows/ci-scheduled-paper-and-export-smoke.yml` |
| **Job** | export_pack_verify |
| **When unset** | Job skipped |
| **Where to set** | GitHub repo: Settings → Secrets and variables → Actions → Variables |
| **Verification** | Same as above; when enabled, also requires `PT_RCLONE_CONF_B64`, `PT_EXPORT_REMOTE`, `PT_EXPORT_PREFIX` secrets |

**Workflow condition:**
```yaml
if: vars.PT_SCHEDULED_EXPORT_VERIFY_ENABLED == 'true'
```

---

## PT_EXPORT_CI_ENABLED

| Field | Value |
|-------|-------|
| **Purpose** | Enable export-pack download+verify job on pull_request (otherwise workflow_dispatch only) |
| **Workflow** | `.github/workflows/ci-export-pack-download-verify.yml` |
| **Job** | export-pack-verify |
| **When unset** | Job skipped on PR; runs on `workflow_dispatch` |
| **Where to set** | GitHub repo: Settings → Secrets and variables → Actions → Variables |
| **Verification** | Open a PR; job appears only if var is `true` |

**Workflow condition:**
```yaml
if: github.event_name == 'workflow_dispatch' || vars.PT_EXPORT_CI_ENABLED == 'true'
```

**Related runbook:** `docs/ops/runbooks/PHASE_W_EXPORT_PACK_GH_CONSUMER.md`

---

## Operator Verification Commands

```bash
# List repo variables (requires gh auth)
gh variable list

# Recent runs for scheduled workflows
gh run list --workflow="prj-scheduled-shadow-paper-features-smoke.yml" --limit 5
gh run list --workflow="ci-scheduled-paper-and-export-smoke.yml" --limit 5
gh run list --workflow="ci-export-pack-download-verify.yml" --limit 5
```

---

## Manual-only workflow recommender after PR #3896

Fourteen ops/schedule workflows remain **active** on GitHub with **`workflow_dispatch` retained**; their **`schedule` / cron triggers were removed** in PR #3896 to reduce recurring Actions cost. Cron is not restored by merging or running this recommender.

**Read-only CLI:** `scripts/ops/recommend_manual_only_workflows.py`

| Behavior | Detail |
|----------|--------|
| Purpose | Map an operator **intent** (e.g. paper/shadow evidence, health suite) to relevant manual-only workflows |
| Output | Workflow file, display name, rationale, cost/risk notes, optional `gh workflow run "…"` **text only** |
| Does **not** | Run `gh`, mutate repo files, re-enable `schedule`, or change GitHub settings |
| Operator-GO | Every manual run needs an explicit operator decision; runs can incur runner and provider (e.g. AI) costs |

**Re-enabling cron** requires a **separate PR** that restores `schedule:` in workflow YAML plus explicit **operator-GO** — not this recommender.

**Examples:**

```bash
python scripts/ops/recommend_manual_only_workflows.py --list-intents
python scripts/ops/recommend_manual_only_workflows.py --intent paper_shadow_evidence --include-commands
python scripts/ops/recommend_manual_only_workflows.py --intent market_info_daily --include-commands --json
```

AI-adjacent workflows (`infostream-automation`, `market_outlook_automation`) may incur model/API cost; prefer safe dispatch inputs (e.g. `skip_ai=true`) unless cost is explicitly approved.

---

## GH Schedule Governance Minimal RC v0 — SLICE-GH-0 / SLICE-GH-001

**Release:** `GH_SCHEDULE_GOVERNANCE_MINIMAL_RC_V0` · **Status index:** `docs/ops/CI_AUDIT_KNOWN_ISSUES.md` — **§ GH Schedule Governance Minimal RC v0 — index v0** (reuse — no parallel hub).

**Slice separation:**

| Slice | Scope | This document |
|-------|-------|---------------|
| **SLICE-GH-0** | Docs-only governance start | This section documents boundaries only — **no** YAML change |
| **SLICE-GH-001** | Possible later single-workflow manual-only | **Not** authorized from SLICE-GH-0; requires **separate explicit Sub-GO** |

**SLICE-GH-001 candidate (only):** `.github&#47;workflows&#47;pro-prk-nightly-selfcheck.yml` — currently retains active `schedule:` (daily cron) among **13 residual scheduled workflows** documented in `scripts&#47;ops&#47;recommend_manual_only_workflows.py` (`RESIDUAL_SCHEDULE_WORKFLOW_FILES`). **All other 12 residuals remain unchanged** in this release line; **no batch YAML wave.**

**Governance boundaries:**

- **YAML change** — forbidden in SLICE-GH-0; SLICE-GH-001 may remove `schedule:` on the candidate file only after explicit Sub-GO; **`workflow_dispatch` must not be executed** from agent/CI automation.
- **Manual-only recommender** — `scripts/ops/recommend_manual_only_workflows.py` remains **read-only**; printed `gh workflow run` lines are **text only**; recommendation **≠** schedule deactivation or workflow disablement.
- **Schedule reactivation** — restoring `schedule:` on PR #3896 manual-only workflows or batch-editing residual schedules requires a **separate PR** and explicit operator-GO — not this release line.
- **Variable gates above** — unchanged; this section does not add new repository variables or new workflow surfaces.
- **Authority** — no runtime, paper/shadow/testnet/live, Notion writes, trading/execution/risk/governance/live-gate changes, or Master V2 / Double Play logic changes.

**Recommender + test owners (reference only in SLICE-GH-0):**

| Owner | Path |
|-------|------|
| Read-only CLI | `scripts/ops/recommend_manual_only_workflows.py` |
| Static tests | `tests/ops/test_recommend_manual_only_workflows.py` |
| Optional post-GH-001 guard | `tests/ci/test_workflow_manual_dispatch_sensitive_surface_contract_v0.py` (SLICE-GH-2 only if needed) |

**Planning bundle (archive — not repo-ingested):** `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/next_larger_theme_ranking_after_ops_cockpit_status_index_rc_v0_20260602T201200Z/`

```text
GH_SCHEDULE_GOVERNANCE_MINIMAL_RC_V0=true
SLICE_GH0_DOCS_ONLY=true
SLICE_GH_001_SEPARATE_SUB_GO=true
GH001_CANDIDATE_WORKFLOW=pro-prk-nightly-selfcheck.yml
WORKFLOW_DISPATCH_EXECUTED=false
BATCH_SCHEDULE_CHANGES=false
SCHEDULE_REACTIVATION=false
RECOMMENDER_READ_ONLY=true
```

---

## Cross-References

- [CI_AUDIT_KNOWN_ISSUES.md](CI_AUDIT_KNOWN_ISSUES.md) — **§ GH Schedule Governance Minimal RC v0 — index v0**
- [CI.md](CI.md) — CI pipeline overview
- [runbooks/prj_scheduled_shadow_paper_features_smoke.md](runbooks/prj_scheduled_shadow_paper_features_smoke.md)
- [runbooks/PHASE_W_EXPORT_PACK_GH_CONSUMER.md](runbooks/PHASE_W_EXPORT_PACK_GH_CONSUMER.md)
- `scripts/ci/scheduled_guardrails.sh` — runtime guardrail script
