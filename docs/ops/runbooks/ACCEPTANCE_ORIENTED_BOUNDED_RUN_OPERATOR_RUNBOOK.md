# ACCEPTANCE ORIENTED BOUNDED RUN OPERATOR RUNBOOK

## Purpose
Operator workflow for a conservative acceptance-oriented bounded-pilot run aligned to the acceptance evidence standard.

> **Authority and scope**  
> This file is an **acceptance- / bounded-run operator runbook** and **review / operator navigation** for a bounded-pilot path. Wording about operators, runs, launches, acceptance, bounded scope, or credentials is **not** an automatic **operational authorization**: it does **not** grant real-money go, any **live** / first-live / `PRE_LIVE` release, **signoff**, **evidence**, or a **gate pass** in the current **Master V2** enablement sense. It confers **no** order, exchange, arming, routing, or enablement authority, and it does **not** create a **Master V2** or **Double Play** handoff. **Master V2 / Double Play** and the canonical **PRE_LIVE** / readiness / signoff contracts remain the governing authority.  
> Optional pointers: [`../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md`](../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md) · [`../specs/MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md`](../specs/MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md) · [`../BOUNDED_ACCEPTANCE_AUTHORITY_FRONTDOOR_INDEX_V0.md`](../BOUNDED_ACCEPTANCE_AUTHORITY_FRONTDOOR_INDEX_V0.md) · [`../AUTHORITY_RECOVERY_CONSOLIDATION_INDEX_V0.md`](../AUTHORITY_RECOVERY_CONSOLIDATION_INDEX_V0.md)

## Bounded Acceptance Index
- `docs&#47;ops&#47;reviews&#47;bounded_acceptance_index_page&#47;INDEX.md`

## Scope
Applies to explicit bounded/acceptance-oriented runs only.

Does not apply to:
- paper
- shadow
- testnet
- generic live-adjacent experimentation outside the bounded path

## Required Inputs
- `main` clean and synchronized
- no active bounded-pilot processes
- supervisor stopped unless explicitly required
- valid Kraken credentials available through the approved launcher path
- `PT_EXEC_EVENTS_ENABLED=true`
- preflight checklist reviewed
- Entry Contract confirmed
- Go/No-Go confirmed
- Dry Validation confirmed
- Ops Cockpit reviewed

## Approved Launch Paths

### A. Primary: Local Secret Launcher
Use this path by default. No shell export of secrets required.

```bash
cd ~/Peak_Trade
python3 scripts/ops/run_bounded_pilot_with_local_secrets.py --dry-check
python3 scripts/ops/run_bounded_pilot_with_local_secrets.py --steps 25 --position-fraction 0.0005
```

The local secret launcher sets `PT_EXEC_EVENTS_ENABLED=true` automatically and reads credentials from `.bounded_pilot.env`.

Reference:
- `docs&#47;ops&#47;runbooks&#47;LOCAL_BOUNDED_SECRET_LAUNCHER_RUNBOOK.md`

### B. Fallback: Shell Export + Direct Bounded Pilot Session
Use only when the local secret launcher is unavailable. Requires manual export of credentials; avoid if possible (secrets may end up in shell history).

```bash
cd ~/Peak_Trade
export KRAKEN_API_KEY='...'
export KRAKEN_API_SECRET='...'
export PT_EXEC_EVENTS_ENABLED=true
python3 scripts/ops/run_bounded_pilot_session.py --steps 25 --position-fraction 0.0005
```

Reference:
- `scripts&#47;ops&#47;run_bounded_pilot_session.py`

## Post-Run Evidence Capture

After the run completes, verify:

1. **Session-scoped execution-event file**
   - Path: `out&#47;ops&#47;execution_events&#47;sessions&#47;&lt;session_id&gt;&#47;execution_events.jsonl`
   - Expected events for accepted-and-filled: `order_submit`, `fill`
   - Expected events for rejected-order: `order_submit`, `order_reject`

2. **Live-session report**
   - Path: `reports&#47;experiments&#47;live_sessions&#47;&lt;timestamp&gt;_live_session_bounded_pilot_&lt;session_id&gt;.json`
   - Verify `status`, `num_orders`, `num_trades`, `fill_rate`

3. **Closeout document**
   - Create under `docs&#47;ops&#47;evidence&#47;`
   - Include all required closeout fields per `docs&#47;ops&#47;specs&#47;ACCEPTANCE_EVIDENCE_STANDARD.md`
   - Canonical accepted-and-filled example: `docs&#47;ops&#47;evidence&#47;CANONICAL_ACCEPTANCE_RUN_20260319_CLOSEOUT.md`

4. **Handoff**
   - If the run changes the evidence position, add a handoff under `docs&#47;ops&#47;reviews&#47;`

## Required Closeout Fields (per Acceptance Evidence Standard)

- `session_id`
- `run_id`
- `mode`
- `strategy`
- `started_at`
- `finished_at`
- `steps`
- `position_fraction`
- `status`
- execution-event path
- live-session report path
- outcome class: no-order | rejected-order | accepted-and-filled
- operator interpretation
- next-step recommendation

## Accepted-and-Filled Evidence
- `docs&#47;ops&#47;evidence&#47;ACCEPTANCE_ORIENTED_BOUNDED_RUN_20260318_CLOSEOUT.md`
- `docs&#47;ops&#47;evidence&#47;LOCAL_SECRET_LAUNCHER_BOUNDED_RUN_20260319_CLOSEOUT.md`
- `docs&#47;ops&#47;evidence&#47;CANONICAL_ACCEPTANCE_RUN_20260319_CLOSEOUT.md`

## Canonical Accepted-and-Filled Reference
Preferred accepted-and-filled example:
- `docs&#47;ops&#47;evidence&#47;CANONICAL_ACCEPTANCE_RUN_20260319_CLOSEOUT.md`

Use this canonical example when:
- operators need one concrete accepted-and-filled reference
- future acceptance closeouts need a model document
- governance / ops packaging needs a canonical bounded accepted-and-filled anchor

## Guardrails

- no weakening of gates
- no replacement of Entry Contract / Go-No-Go
- no secret-handling policy changes
- acceptance-oriented run requires valid exchange credentials
- evidence mode must be enabled for evidence capture

## References

- `docs&#47;ops&#47;specs&#47;ACCEPTANCE_EVIDENCE_STANDARD.md`
- `docs&#47;ops&#47;evidence&#47;CANONICAL_ACCEPTANCE_RUN_20260319_CLOSEOUT.md` (canonical accepted-and-filled example)
- `docs&#47;ops&#47;runbooks&#47;NEXT_BOUNDED_TRIAL_PREFLIGHT_CHECKLIST.md`
- `docs&#47;ops&#47;runbooks&#47;LOCAL_BOUNDED_SECRET_LAUNCHER_RUNBOOK.md`
- `docs&#47;ops&#47;specs&#47;BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md`
- `docs&#47;ops&#47;specs&#47;FIRST_BOUNDED_LIVE_ORDER_CONTRACT.md`
