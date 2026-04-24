# BOUNDED ACCEPTANCE OPERATOR CHEAT SHEET

## Purpose
Ultra-compact operator reference for bounded / acceptance runs.

> **Authority and scope**  
> This file is a **bounded / acceptance operator cheat sheet** and **review / operator navigation** for quick local reference. Wording about *operator*, *go/no-go*, *checklist*, *pass*, *acceptance*, *bounded* scope, or similar **decision language** is **not** an automatic **operational authorization** — it does **not** grant real-money go, any **live** / first-live / `PRE_LIVE` release, **signoff**, **evidence**, or a **gate pass** in the current **Master V2** enablement sense. It confers **no** order, exchange, arming, routing, or enablement authority, and it does **not** create a **Master V2** or **Double Play** handoff. **Master V2 / Double Play** and the canonical **PRE_LIVE** / readiness / signoff contracts remain the governing authority.  
> Optional pointers: [`../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md`](../specs/MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md) · [`../specs/MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md`](../specs/MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md) · [`../BOUNDED_ACCEPTANCE_AUTHORITY_FRONTDOOR_INDEX_V0.md`](../BOUNDED_ACCEPTANCE_AUTHORITY_FRONTDOOR_INDEX_V0.md) · [`../AUTHORITY_RECOVERY_CONSOLIDATION_INDEX_V0.md`](../AUTHORITY_RECOVERY_CONSOLIDATION_INDEX_V0.md)

## Bounded Acceptance Index
- `docs&#47;ops&#47;reviews&#47;bounded_acceptance_index_page&#47;INDEX.md`

## Canonical Path
- runbook: `docs&#47;ops&#47;runbooks&#47;ACCEPTANCE_ORIENTED_BOUNDED_RUN_OPERATOR_RUNBOOK.md`
- launcher: `scripts&#47;ops&#47;run_bounded_pilot_with_local_secrets.py`
- standard: `docs&#47;ops&#47;specs&#47;ACCEPTANCE_EVIDENCE_STANDARD.md`
- canonical example: `docs&#47;ops&#47;evidence&#47;CANONICAL_ACCEPTANCE_RUN_20260319_CLOSEOUT.md`

## Before Run
- `main` clean + synced
- no active bounded-pilot processes
- supervisor stopped
- Entry Contract confirmed
- Go/No-Go confirmed
- Dry Validation confirmed
- Ops Cockpit reviewed
- `.bounded_pilot.env` present
- `python3 scripts/ops/run_bounded_pilot_with_local_secrets.py --dry-check`

## Canonical Start
```bash
cd ~/Peak_Trade
python3 scripts/ops/run_bounded_pilot_with_local_secrets.py --dry-check
python3 scripts/ops/run_bounded_pilot_with_local_secrets.py --steps 25 --position-fraction 0.0005
```

## After Run
1. **Execution events** — `out&#47;ops&#47;execution_events&#47;sessions&#47;&lt;session_id&gt;&#47;execution_events.jsonl`
2. **Live-session report** — `reports&#47;experiments&#47;live_sessions&#47;&lt;timestamp&gt;_live_session_bounded_pilot_&lt;session_id&gt;.json`
3. **Closeout** — create under `docs&#47;ops&#47;evidence/` using `docs&#47;ops&#47;templates/ACCEPTED_AND_FILLED_CLOSEOUT_TEMPLATE.md` or `REJECTED_ORDER_CLOSEOUT_TEMPLATE.md`
4. **Handoff** — if evidence position changes, add under `docs&#47;ops&#47;reviews/`

## Allowed
- Bounded runs via local secret launcher
- Conservative sizing (e.g. `position_fraction` 0.0005)
- Evidence capture mandatory

## Not Allowed
- Blanket live authorization
- Weakening gates
- Live secrets in paper/shadow/testnet
- Skipping evidence capture

## References
- Go/No-Go: `docs&#47;ops&#47;reviews/bounded_acceptance_go_no_go_snapshot/GO_NO_GO_SNAPSHOT.md`
- Runbook: `docs&#47;ops&#47;runbooks/ACCEPTANCE_ORIENTED_BOUNDED_RUN_OPERATOR_RUNBOOK.md`
- Canonical: `docs&#47;ops&#47;evidence/CANONICAL_ACCEPTANCE_RUN_20260319_CLOSEOUT.md`
