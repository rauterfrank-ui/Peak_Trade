# WORKBOOK — Ops Loop A→Z (Cursor Multi-Agent Orchestrator) v1

**Scope:** Shadow/Paper only. **No live trading. No record mode. No secrets.**  
**Goal:** A single A→Z plan with explicit checkpoints, evidence, pins, hygiene, and failure triage so nothing gets left behind.

---

## Roles (5–7 Agents)

### Agent 0 — Planner / Conductor
- Owns the end-to-end plan and sequencing.
- Ensures every step has: **inputs, commands, outputs, pass/fail criteria, evidence, pins**.
- Maintains "Open Items" and closes them or parks them.

### Agent 1 — Safety / Governance
- Enforces deny-by-default, mode gates (paper/shadow), secret bans.
- Validates guardrails scripts and launchd/systemd templates.
- Ensures "hard stop" procedures exist (stop-playbooks).

### Agent 2 — Implementer
- Implements features and scripts.
- Keeps changes minimal, testable, deterministic.
- Uses out/ops evidence packs and pinned bundles.

### Agent 3 — Test / CI / Repro
- Writes smoke tests and deterministic unit tests.
- Validates bash compatibility (macOS bash 3.2), no fragile xargs assumptions.
- Ensures CI gates pass (docs-token-policy, etc).

### Agent 4 — Ops / Release / Orchestrator
- Launchd installation, reload, status, log inspection.
- Runs ops-loop orchestrator (P98/P99) and validates steady-state.
- Maintains service runbooks and safe templates.

### Agent 5 — Auditor / Evidence
- Ensures evidence manifests, SHA256SUMS, bundles, pin files.
- Validates `shasum -a 256 -c` in-place.
- Maintains retention and index rollups.

### Agent 6 — Docs / UX (optional, can be merged with Agent 0/4)
- Runbooks, quickstarts, troubleshooting tables.
- Fixes docs-token-policy-gate encoding (`&#47;` → `&#47;` in inline code).

---

## Global invariants (Non-negotiable)
- **MODE:** only `shadow` or `paper`.
- **DRY_RUN default:** `YES` for anything launchd/CI-facing unless explicitly doing local "real kickstart".
- **Secrets forbidden:** any env vars matching API keys/secrets.
- **OUT_DIR constraint:** must be under `out&#47;ops&#47;*`.
- **Deny-by-default execution:** no trade placement, no withdrawals, no record mode.

---

## System components (current)
- Supervisor: P78 + P80 + P81 + P82 + P84 + P87
- Health: P79
- Metrics: P90 (+ watcher)
- Audit: P91 (+ runner + launchd)
- Retention: P92 (P91), P94 (P93)
- Dashboard snapshot: P93 (+ launchd)
- Meta gate: P95
- Guard kickstart: P96 (+ DRY_RUN P97)
- Ops loop orchestrator: P98
- Ops loop CLI + launchd template: P99
- Guarded P99 launchd: P99 guarded + WorkingDirectory fix

---

# A→Z Plan

## A) Baseline sanity (always first)
**Commands**
- `git status -sb`
- `git log -1 --oneline`
- `scripts&#47;ops&#47;repo_clean_baseline_pin_v1.sh`
- `scripts&#47;ops&#47;final_done_pin_v1.sh`

**Pass**
- `main...origin&#47;main (clean)`
- baseline + final_done pins created and sha256 verified

---

## B) Supervisor steady-state (Shadow)
**Objective:** Supervisor produces ticks consistently.

**Start**
- `MODE=shadow INTERVAL=300 bash scripts&#47;ops&#47;launchd_online_readiness_supervisor_smoke_v1.sh start`

**Status**
- `bash scripts&#47;ops&#47;launchd_online_readiness_supervisor_smoke_v1.sh status`

**Pass**
- state=running
- tick dirs appear under OUT_DIR

**Stop**
- `bash scripts&#47;ops&#47;launchd_online_readiness_supervisor_smoke_v1.sh stop`

---

## C) Health gates (P79 + P90)
**Objective:** confirm freshness, tick count, P76 ready.

**P79**
- `MODE=shadow MAX_AGE_SEC=900 bash scripts&#47;ops&#47;p79_supervisor_health_gate_v1.sh`

**P90**
- `MIN_TICKS=2 MAX_AGE_SEC=900 bash scripts&#47;ops&#47;p90_supervisor_metrics_v1.sh | python3 -m json.tool`

**Pass**
- P79_GATE_OK
- P90 alerts == []

---

## D) Audit snapshots (P91) + kickstart guard (P96/P97)
**Objective:** periodic audited bundle/pin with deterministic verification.

**One-shot snapshot**
- `bash scripts&#47;ops&#47;p91_audit_snapshot_runner_v1.sh`

**Launchd periodic (optional)**
- com.peaktrade.p91-audit-snapshot-runner

**Kickstart when ready**
- `DRY_RUN=YES bash scripts&#47;ops&#47;p91_kickstart_when_ready_v1.sh`
- (local real) `DRY_RUN=NO bash ...` (only outside sandbox)

**Pass**
- `P91_AUDIT_SNAPSHOT_OK`
- pin + bundle + sha256 OK

---

## E) Dashboard snapshots (P93) + retention (P94)
**Objective:** periodic "status dashboard" evidence and keep only last N.

**One-shot**
- `OUT_DIR="<run_dir>" MODE=shadow MAX_AGE_SEC=900 MIN_TICKS=2 bash scripts&#47;ops&#47;p93_online_readiness_status_dashboard_v1.sh`

**Retention**
- `KEEP_N=48 bash scripts&#47;ops&#47;p94_p93_status_dashboard_retention_v1.sh`

**Pass**
- pin/evi/bundle created
- retention NOOP or OK with correct remaining

---

## F) Retention for P91 snapshots (P92)
**Objective:** keep last N P91 snapshot artifacts.

- `KEEP_N=48 bash scripts&#47;ops&#47;p92_p91_audit_snapshot_retention_v1.sh`

---

## G) Ops meta gate (P95)
**Objective:** single "green light" check for ops loop.

- `MODE=shadow MAX_AGE_SEC=900 MIN_TICKS=2 bash scripts&#47;ops&#47;p95_ops_health_meta_gate_v1.sh`

**Pass**
- `P95_GATE_OK`
- P90_OK and latest_p76_status=ready

---

## H) Ops loop orchestrator (P98) + CLI (P99)
**Objective:** drive the full ops loop in one command.

**CLI dry run**
- `OUT_DIR="<run_dir>" DRY_RUN=YES python3 -m src.ops.p99.ops_loop_cli_v1 --mode shadow`

**Pass**
- P99_OK
- EVI + pin + bundle + sha256 OK

---

## I) Guarded launchd for ops loop (P99 guarded)
**Objective:** schedule ops loop safely with hard guardrails.

**Install**
- copy guarded plist into `~/Library&#47;LaunchAgents&#47;`
- ensure `WorkingDirectory` is set to repo root
- bootstrap + kickstart

**Pass**
- last exit code 0
- P99 pins appear periodically
- guard one-shot returns `P99_OK`

---

## J) Long shadow soak (2–6h) + periodic snapshots
**Objective:** stability under time.

- Supervisor: INTERVAL=300
- P91 runner: 300
- P92 retention: 900
- P93 dashboard: 300
- P94 retention: 900
- Optional P90 watcher: 300

**Checkpoint (manual heartbeat)**
- P79 / P90 / P95 all green

---

## K) Stop playbooks (must exist)

## Checklists (copy/paste)

### Preflight (must be true)
- [ ] `git status -sb` shows clean or only excluded scratch
- [ ] `REPO_CLEAN_BASELINE_PIN_OK` present
- [ ] `FINAL_DONE_PIN_OK` present
- [ ] `MODE=shadow` and `DRY_RUN=YES` for any automated ops loop

### Long shadow soak (2–6h)
- [ ] Supervisor running (`INTERVAL=300`, `MODE=shadow`)
- [ ] P79 gate OK (`age_sec <= 900`)
- [ ] P90 metrics OK (no alerts, latest_p76_status=ready)
- [ ] P95 meta gate OK
- [ ] Periodic P93 snapshots appear (pins + bundles)
- [ ] Retention jobs (P92/P94) are NOOP or OK

### Stop playbook (must exist + tested)
- [ ] Run `bash scripts&#47;ops&#47;p101_stop_playbook_v1.sh` (creates pinned evidence)
- [ ] Verify bundle + pin SHA256
- [ ] Confirm supervisor stopped (no new ticks), and launchd jobs booted out as expected

**Objective:** quick & safe shutdown.

1) Stop ops-loop launchd
2) Stop dashboard/retention launchd
3) Stop P91/P92 launchd
4) Stop supervisor
5) Final snapshot (P93 one-shot + P91 one-shot) + pins

---

## L) Hygiene + parking
**Rule:** no untracked leftovers. Park under `out&#47;ops&#47;_scratch&#47;...` and add `.git&#47;info&#47;exclude`.

---

## M) Finish criteria ("DONE")
- Supervisor stable
- P79/P90/P95 consistently green
- P91 snapshots producing pinned bundles
- P93 dashboard producing pinned bundles
- Retentions working (P92/P94)
- Ops loop (P99 guarded) runs periodically and produces pinned bundles
- Stop-playbook verified
- `REPO_CLEAN_BASELINE_PIN_OK` + `FINAL_DONE_PIN_OK` after each change set

---

# Failure triage quick table

## No ticks / stale ticks
- Check supervisor launchd status
- Check OUT_DIR path and permissions
- Ensure MODE=shadow
- Increase wait window for first 2 ticks

## P76 missing
- Look under `tick_*&#47;p76&#47;P76_RESULT.txt` (not tick root)

## launchd EX_CONFIG / bad paths
- Set `WorkingDirectory` to repo root
- Use absolute log paths or redirect stderr to /dev/null (if desired)

## docs-token-policy-gate
- Inline code must escape `&#47;` as `&#47;`
