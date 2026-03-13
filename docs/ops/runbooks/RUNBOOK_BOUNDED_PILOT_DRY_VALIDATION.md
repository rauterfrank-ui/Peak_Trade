# RUNBOOK — Bounded Pilot Dry Validation

status: DRAFT
last_updated: 2026-03-13
owner: Peak_Trade
purpose: Operator sequence for dry validation before any bounded real-money pilot; operationalizes existing dry-run stack without new runtime orchestration
docs_token: DOCS_TOKEN_RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION

## Intent

This runbook defines the **exact operator sequence** for dry validation before a bounded real-money pilot. It closes the gap identified in the bounded-real-money-pilot-dry-validation-flow review: no single contract that chains drills → go/no-go → session dry-run.

**Scope:** docs-only. No new runtime orchestration. Uses existing scripts and gates.

## Trigger

- Operator intends to run a bounded real-money pilot
- Dry validation must succeed before any pilot session with real funds
- `live_pilot_execution_plan` requires "Dry-run first must succeed" but did not define the sequence

## Prerequisites

- Repo on `main` (or approved branch)
- Config present: `config/config.toml` (or `CONFIG_PATH`)
- Ops Cockpit buildable: `build_ops_cockpit_payload()` succeeds

## Operator Sequence (in order)

### Step 1: Live Drills (Phase 73)

Run safety drills to validate gating and dry-run behavior.

```bash
python3 scripts/run_live_dry_run_drills.py
```

**Expected:** All scenarios pass. Exit 0. No config changes, no orders, no API calls.

**If any drill fails:** Stop. Do not proceed. Fix gates/config before retrying.

### Step 2: Pilot Go/No-Go Eval

Evaluate cockpit payload against PILOT_GO_NO_GO_CHECKLIST.

```bash
python3 scripts/ops/pilot_go_no_go_eval_v1.py
```

**Expected:** `verdict=GO_FOR_NEXT_PHASE_ONLY` or `verdict=CONDITIONAL` (no FAIL).

**If verdict=NO_GO:** Stop. Inspect `--json` output. Fix blockers (caps, treasury separation, human supervision, etc.) before retrying.

### Step 3: Execution Session Dry-Run

Validate session config and intended session parameters without starting a live session.

```bash
python3 scripts/run_execution_session.py --dry_run
```

(Adjust for your env: `--mode`, `--config`, etc. as needed.)

**Expected:** Config validated, intended session logged, exit 0. No LiveSessionRunner created, no registry write.

**If dry-run fails:** Stop. Fix config before retrying.

### Step 4: Pilot Session Wrapper (optional pre-check)

If using `run_live_pilot_session.sh`, verify gates are satisfied with dry-run enforced:

```bash
PT_LIVE_ENABLED=YES PT_LIVE_ARMED=YES PT_LIVE_ALLOW_FLAGS=pilot_only \
PT_LIVE_DRY_RUN=YES PT_CONFIRM_TOKEN_EXPECTED=TOKEN PT_CONFIRM_TOKEN=TOKEN \
scripts/ops/run_live_pilot_session.sh
```

**Note:** This wrapper invokes `orchestrate_testnet_runs.py`. For live session dry validation, Step 3 (`run_execution_session.py --dry_run`) is the primary check.

## Evidence

- Step 1: Drill output (text or JSON)
- Step 2: `pilot_go_no_go_eval_v1.py` verdict and optional `--json` output
- Step 3: `run_execution_session.py` dry-run log
- Capture: repo head, timestamp, operator identity (optional)

## Success Criteria

- All three steps (1–3) complete with exit 0
- No FAIL in go/no-go eval
- No config changes, no orders, no API calls

## Relationship

- **Companion to:** `live_pilot_execution_plan` (Step B: Dry-run first must succeed)
- **Companion to:** `live_pilot_session_wrapper` (PT_LIVE_DRY_RUN=YES gate)
- **Closes gap:** bounded-real-money-pilot-dry-validation-flow review (single dry validation contract)
- **References:** `PILOT_GO_NO_GO_CHECKLIST`, `PILOT_GO_NO_GO_OPERATIONAL_SLICE`

## Explicit Non-Goals

- no new runtime orchestration script
- no new gates
- no replacement for operator judgment
- no claim of pilot readiness beyond dry validation
