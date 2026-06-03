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

**`residual_all` intent:** lists all **13** entries in `RESIDUAL_SCHEDULE_WORKFLOW_FILES` — **8** with active `schedule:` plus **5** manual-only (GH-001..004 + GH-CI); not “13 active schedules”.

**Examples:**

```bash
python scripts/ops/recommend_manual_only_workflows.py --list-intents
python scripts/ops/recommend_manual_only_workflows.py --intent paper_shadow_evidence --include-commands
python scripts/ops/recommend_manual_only_workflows.py --intent market_info_daily --include-commands --json
```

AI-adjacent workflows (`infostream-automation`, `market_outlook_automation`) may incur model/API cost; prefer safe dispatch inputs (e.g. `skip_ai=true`) unless cost is explicitly approved.

---

## GH Schedule Governance Minimal RC v0 — SLICE-GH-0 / SLICE-GH-001

**Release:** `GH_SCHEDULE_GOVERNANCE_MINIMAL_RC_V0` · **Status:** **CORE COMPLETE** · **Status index:** `docs/ops/CI_AUDIT_KNOWN_ISSUES.md` — **§ GH Schedule Governance Minimal RC v0 — index v0** (reuse — no parallel hub).

**Slice separation (historical reference + status):**

| Slice | Scope | Status |
|-------|-------|--------|
| **SLICE-GH-0** | Docs-only governance start | **complete** (#3910) |
| **SLICE-GH-001** | Single-workflow manual-only: `.github&#47;workflows&#47;pro-prk-nightly-selfcheck.yml` | **complete** (#3911) |
| **SLICE-GH-CI** | Single-workflow manual-only: `.github&#47;workflows&#47;ci.yml` | **pending PR** (GH-CI slice) |

**Post GH-001..004 + GH-CI schedule posture:** **5** residual inventory workflows are manual-only (`ci.yml`, `pro-prk-nightly-selfcheck.yml`, `real-market-forward-evidence-smoke.yml`, `audit.yml`, `pru-required-checks-drift-detector.yml`); **`workflow_dispatch`** and other non-schedule triggers retained per workflow. Among `RESIDUAL_SCHEDULE_WORKFLOW_FILES`, **8** retain active `schedule:`. **No batch YAML wave.**

**Governance boundaries:**

- **Further YAML change** — requires **per-workflow Sub-GO**; not part of this completed release line; **`workflow_dispatch` must not be executed** from agent/CI automation.
- **Manual-only recommender** — `scripts/ops/recommend_manual_only_workflows.py` remains **read-only**; printed `gh workflow run` lines are **text only**; recommendation **≠** schedule deactivation or workflow disablement.
- **Schedule reactivation** — restoring `schedule:` on PR #3896 manual-only workflows or batch-editing residual schedules requires a **separate PR** and explicit operator-GO — not this release line.
- **Variable gates above** — unchanged; this section does not add new repository variables or new workflow surfaces.
- **Authority** — no runtime, paper/shadow/testnet/live, Notion writes, trading/execution/risk/governance/live-gate changes, or Master V2 / Double Play logic changes.

**Recommender + test owners:**

| Owner | Path |
|-------|------|
| Read-only CLI | `scripts/ops/recommend_manual_only_workflows.py` |
| Static tests | `tests/ops/test_recommend_manual_only_workflows.py` (GH-001 manual-only contract merged #3911) |

**Planning bundle (archive — not repo-ingested):** `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/closeout/gh_schedule_governance_minimal_rc_v0_final_closeout_handoff_20260602T204000Z/`

```text
GH_SCHEDULE_GOVERNANCE_MINIMAL_RC_V0=true
GH_SCHEDULE_GOVERNANCE_MINIMAL_RC_V0_CORE_DONE=true
SLICE_GH0_DOCS_ONLY=true
SLICE_GH001_COMPLETE=true
GH001_MANUAL_ONLY=true
RESIDUAL_ACTIVE_SCHEDULE_COUNT=7
RESIDUAL_MANUAL_ONLY_RESIDUAL_COUNT=6
RESIDUAL_SCHEDULE_INVENTORY_COUNT=13
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
