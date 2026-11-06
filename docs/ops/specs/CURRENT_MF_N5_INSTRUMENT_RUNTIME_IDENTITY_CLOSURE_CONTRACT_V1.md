---
docs_token: DOCS_TOKEN_CURRENT_MF_N5_INSTRUMENT_RUNTIME_IDENTITY_CLOSURE_CONTRACT_V1
---

# CURRENT MF N≤5 Instrument Runtime Identity Closure Contract V1

OWNER=ops.current_mf_n5_instrument_runtime_identity_closure_v1  
CONTRACT_ID=CURRENT_MF_N5_INSTRUMENT_RUNTIME_IDENTITY_CLOSURE_CONTRACT_V1  
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK  
RUNTIME_AUTHORIZATION_EFFECT=NONE  
N_GT_1_ACTIVATION=OUT_OF_SCOPE  

## Purpose

Close DD-06 D1–D6 capability gaps for instrument-correct MF_N5 lane isolation without
granting Cap23 selection, Cap24 bind-only inversion, MF_N5 trading authority, or POST.

## Derived identity (carry-only)

`OccupiedLaneRuntimeInstrumentIdentityV1` reuses `BoundInstrumentLaneIdentityV1` from
hard-facts closure; selection lineage fields are copied from `BoundInstrumentV1` for audit only.

## Surfaces

| Delta | Owner module |
|-------|----------------|
| D1 per-lane C1 | `c1_fanout_v1` + N1 consumer wiring |
| D2 per-lane position | `position_truth_v1` + `extract_position_truth_v1` |
| D3 ownership | `ownership_v1` |
| D4 lane generation | `lane_generation_v1` |
| D5 lifecycle pins | `lifecycle_v1` + orchestrator membership pin |
| D6 reconciliation admission | `reconciliation_admission_v1` |

## Evidence

`evidence/ops/n5_instrument_runtime_identity_closure_v1/IMPLEMENTATION_EVIDENCE_V1.md`

Local position-feedback correction, 2026-11-02: a supplied positions response
takes precedence over global position kwargs even for N1. Malformed/error responses
are rejected rather than converted to FLAT. N1 global fallback is retained only
when no positions response is supplied. Order completion does not release the
Future/slot or stop Double Play. Bounded filled-order/open-position/scope tests
do not prove automatic feedback through the outer OCCUPANCY_PRESENT host gate.

Subsequent local repair on 2026-11-02 wires a separate management callback
through that gate for one validated bound open position with no pending orders.
Full lane-consumer offline tests now reach the existing durable Double Play
cycle while retaining the scope. Entry sizing/envelopes and live execution
remain outside this management evaluation path.

Local quantity handoff, 2026-11-03: one matching open position row also carries
its exact Decimal quantity, source-snapshot digest and lane/instrument-generation
identity. Quantity observation alone does not establish contract units or execution
authority. The management join binds the existing instrument-metadata producer
and any existing canonical reducing intent, preserving explicit missing-input
statuses. No inferred size/fraction or automatic slot release is introduced.

Owner clarification, 2026-11-03: after a confirmed reconciled full close, Ranking
reviews the assignment and may retain or replace the Future. A partial reduction
retains custody. The local full-close builder adds no automatic slot-release or
ranking invocation; these downstream runtime feedback connections remain open.

Subsequent local execution handoff, 2026-11-03: a full-close receipt now carries
the close assessment into the existing execution composer and venue translator.
The governed host admits only an exact snapshot-matched net-mode reducing EXIT
envelope to PRE_EXTERNAL_EFFECT; ordinary management cannot introduce an entry
envelope. Permit/send admission is unchanged. Offline simulated lifecycle and
observed-position feedback do not establish automatic productive reconciliation,
capital-budget updates or Ranking invocation. Hedge-mode closing remains pending.
