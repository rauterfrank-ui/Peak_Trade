# Bounded Real-Money Pilot Entry Boundary Note

status: DRAFT
last_updated: 2026-03-14
owner: Peak_Trade
purpose: Clarify where the spec-defined flow ends and how the first real-money step is invoked
docs_token: DOCS_TOKEN_BOUNDED_REAL_MONEY_PILOT_ENTRY_BOUNDARY_NOTE

## 1. Intent

This note clarifies the **operational boundary** between the spec-defined flow and the first bounded real-money pilot attempt. It does not add execution authority or relax gates.

## 2. Where the Flow Ends Today

The canonical flow defined by Entry Contract, Candidate Flow, and Dry Validation **ends at Dry-Validation**:

| Step | Command / Action | Status |
|------|------------------|--------|
| A1 | `python3 scripts/run_live_dry_run_drills.py` | Implemented |
| A2 | `python3 scripts/ops/pilot_go_no_go_eval_v1.py` | Implemented |
| A3 | `python3 scripts/run_execution_session.py --dry_run` | Implemented |
| B | Ops Cockpit review, gates GREEN | Implemented |
| **C** | **First bounded real-money step** | **No defined CLI/invocation path** |

## 3. First Real-Money Step: Operator-Driven

The first bounded real-money step (§4 of BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT) is **operator-driven**:

- There is **no** `--mode bounded_pilot` or equivalent in `run_execution_session.py` today.
- `run_live_pilot_session.sh` enforces `PT_LIVE_DRY_RUN=YES` and invokes `orchestrate_testnet_runs.py` — i.e. **dry-run / testnet**, not real money.
- A real-money pilot session would require a **separate, explicitly gated path** (not yet implemented) or manual operator invocation under all gates.

**Rule:** Until a bounded-pilot entry path exists, the first real-money step is **manual / operator-driven**, with all Entry Contract prerequisites and abort criteria applied.

**Gate wrapper:** `scripts/ops/run_bounded_pilot_session.py` runs Pre-Entry-Checks (go/no-go, cockpit). Exit 0 when all gates GREEN; does not start a live session. See `RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION` Step 5.

## 4. run_live_pilot_session.sh

- **Current scope:** Dry-run and testnet validation only.
- **PT_LIVE_DRY_RUN=YES** is enforced; the script does not support real-money execution.
- For a future real-money pilot: a separate invocation path or controlled condition would be required, with all gates explicit.

## 5. Relationship

- Companion to: `BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT`
- Gap documentation: `BOUNDED_PILOT_LIVE_ENTRY_GAP_NOTE` (blockers B1–B6, dependency chain)
- Companion to: `RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW`
- Closes documentation gap from: first-bounded-real-money-pilot-execution-readiness-review

## 6. Non-Goals

- No execution authority
- No new gates or relaxation
- No replacement for operator judgment
