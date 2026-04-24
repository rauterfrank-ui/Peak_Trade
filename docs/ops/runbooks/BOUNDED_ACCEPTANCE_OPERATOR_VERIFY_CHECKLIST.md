# BOUNDED ACCEPTANCE OPERATOR VERIFY CHECKLIST

## Purpose
Short pass/fail verification checklist for bounded / acceptance runs.

> **Authority and scope**  
> This file is a **bounded / acceptance operator verify checklist** and **review / operator navigation** for local pass/fail checks around a bounded/acceptance run. Wording about *pass* / *fail*, *go/no-go*, *checklist*, *evidence*, *closeout*, *acceptance*, *bounded* scope, or similar **decision language** is **not** an automatic **operational authorization** — it does **not** grant real-money go, any **live** / first-live / `PRE_LIVE` release, **signoff**, **evidence**, or a **gate pass** in the current **Master V2** enablement sense. It confers **no** order, exchange, arming, routing, or enablement authority, and it does **not** create a **Master V2** or **Double Play** handoff. **Master V2 / Double Play** and the canonical **PRE_LIVE** / readiness / signoff contracts remain the governing authority.  
> Optional pointers: [`../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md`](../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md) · [`../specs/MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md`](../specs/MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md) · [`../BOUNDED_ACCEPTANCE_AUTHORITY_FRONTDOOR_INDEX_V0.md`](../BOUNDED_ACCEPTANCE_AUTHORITY_FRONTDOOR_INDEX_V0.md) · [`../AUTHORITY_RECOVERY_CONSOLIDATION_INDEX_V0.md`](../AUTHORITY_RECOVERY_CONSOLIDATION_INDEX_V0.md)

## Usage
Use this checklist:
- immediately before a bounded / acceptance run
- during the run for quick evidence confirmation
- immediately after completion before writing the closeout

## Pre-Run Verify
Mark each item PASS / FAIL.

1. Repo state
- `main` clean and synced
- no uncommitted changes relevant to bounded / acceptance flow

2. Runtime state
- no active bounded-pilot processes
- supervisor stopped unless explicitly required

3. Launch path
- canonical path selected:
  `scripts&#47;ops&#47;run_bounded_pilot_with_local_secrets.py`
- `.bounded_pilot.env` present
- `--dry-check` passes

4. Governance / Ops gates
- Entry Contract confirmed
- Go / No-Go confirmed
- Dry Validation confirmed
- Ops Cockpit reviewed

5. Safety / scope
- bounded / acceptance intent explicit
- no paper / shadow / testnet secret bleed
- no blanket live authorization assumed

## In-Run Verify
Mark each item PASS / FAIL.

1. Process chain present
- launcher / bounded-pilot / execution process chain visible if expected

2. Evidence path present
- newest session-scoped execution-event file exists
- newest live-session report exists

3. Outcome visibility
- can identify one of:
  - no-order
  - rejected-order
  - accepted-and-filled

## Post-Run Verify
Mark each item PASS / FAIL.

1. Completion state
- no active bounded-pilot processes remain
- final report status captured

2. Required artifacts
- session-scoped execution-event file present
- live-session report present

3. Required closeout fields available
- `session_id`
- `run_id`
- `mode`
- `strategy`
- `started_at`
- `finished_at`
- `steps`
- `position_fraction` where relevant
- `status`
- execution-event path
- live-session report path
- outcome class
- operator interpretation
- next-step recommendation

4. Outcome-specific checks

### Rejected-Order
- `order_submit` present
- `order_reject` present
- exchange-side rejection reason captured

### Accepted-and-Filled
- `order_submit` present
- `fill` present
- `num_orders`, `num_trades`, `fill_rate` captured
- txid captured if available

## Pass / Fail Rule
A bounded / acceptance run is ready for closeout only if:
- Pre-Run Verify = PASS
- In-Run Verify = PASS where applicable
- Post-Run Verify = PASS

If any critical item fails:
- do not treat the run as canonical evidence
- document the failure or gap explicitly

## References
- start here:
  `docs&#47;ops&#47;reviews&#47;bounded_acceptance_start_here_page&#47;START_HERE.md`
- operator runbook:
  `docs&#47;ops&#47;runbooks&#47;ACCEPTANCE_ORIENTED_BOUNDED_RUN_OPERATOR_RUNBOOK.md`
- evidence standard:
  `docs&#47;ops&#47;specs&#47;ACCEPTANCE_EVIDENCE_STANDARD.md`
- go / no-go snapshot:
  `docs&#47;ops&#47;reviews&#47;bounded_acceptance_go_no_go_snapshot&#47;GO_NO_GO_SNAPSHOT.md`
