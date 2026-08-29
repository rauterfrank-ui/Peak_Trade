# MASTER V2 — A06 Capital → Risk → Sizing → Position Intent restore v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Bounded current-system composition of STEP-29P and STEP-29Q after A01–A05 evidence. Not canonical authority. Not a new semantic owner.
docs_token: DOCS_TOKEN_MASTER_V2_A06_CAPITAL_RISK_SIZING_INTENT_RESTORE_V1

```text
HISTORICAL_REFERENCE_AUTHORITY=NONE
FORENSIC_REFERENCE_AUTHORITY_NONE=true
REFERENCE_MODEL=MASTER_V2_DOUBLE_PLAY_CONSERVED_REFERENCE_V1
A06_ONLY=true
NO_TRADING=true
NO_LIVE_AUTHORITY=true
NO_EXECUTION_AUTHORITY=true
SAFETY_RESTORED=false
A08_STARTED=false
A06_ADAPTER_COMPUTE_OWNER=false
A06_ADAPTER_RISK_OWNER=false
A06_ADAPTER_SIZING_OWNER=false
A06_ADAPTER_INTENT_OWNER=false
CRS_INTENT_RESTORE_V1_PRODUCTIVE_PATH=false
CRS_INTENT_RESTORE_PRODUCTIVE_REACHABLE=false
PRODUCTIVE_REPLAY_ORCHESTRATOR=false
```

## 1) Epistemic classes

| Class | Meaning |
|---|---|
| HISTORICALLY_PROVEN | Supported by forensic Master V2 / Double Play structure plus existing STEP-29P / 29Q owners |
| IMPLEMENTATION_DETAIL | Adapter mapping with no new business/authority semantics |
| OUT_OF_SCOPE | Not this slice |
| DEFERRED_TO_A08 | Historical E2E includes Safety before executable downstream; not implemented here |
| FORENSIC_REFERENCE_AUTHORITY_NONE | Forensic package is evidence/reference only |

This spec is not Restoration SSOT. Restoration admission authority remains the
merged class `HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_V1`.

## 2) Bounded restoration target

```text
A01–A05 authoritative CanonicalTradingDecisionEvidenceV1
  → STEP-29P evaluate_quantity_chain_v1
       envelope → pre-sizing risk → sizing → post-sizing risk → provenance
  → STEP-29Q build_canonical_order_intent_v1
       PLAN_ONLY / submission_authorized=false
```

Replay remains compute owner. Decision Packet remains derived handoff.
Double Play / SideState writer remains unchanged. A06 does not rewrite them.

Historical full E2E ordering includes Safety before executable downstream
progression. A06 does **not** restore Safety and does **not** claim full E2E.

## 3) Obligation matrix (readjudicated)

| ID | Obligation | Status | Class |
|---|---|---|---|
| O01 | Capital Envelope is a distinct functional stage | PROVEN | HISTORICALLY_PROVEN via STEP-29P `ScopeCapitalEnvelopeV1` |
| O02 | Envelope consumes authoritative replay evidence | PROVEN | HISTORICALLY_PROVEN |
| O03 | Risk consumes Envelope inside the 29P quantity chain | PROVEN | HISTORICALLY_PROVEN in `evaluate_quantity_chain_v1`; not a parallel A06 layer |
| O04 | Sizing consumes risk-approved/bounded 29P output | PROVEN | HISTORICALLY_PROVEN |
| O05 | Position Intent is downstream of Sizing | PROVEN | HISTORICALLY_PROVEN via STEP-29Q; Safety remains deferred |
| O06 | Decision Packet is derived handoff, not compute owner | PROVEN | HISTORICALLY_PROVEN in A01–A05; not an A06 gate |
| O07 | Integrated Replay remains compute owner | PROVEN | HISTORICALLY_PROVEN |
| O08 | No A06 rewrite of SideState / Double Play authority | PROVEN | HISTORICALLY_PROVEN as non-mutation; A06-owned override-reject gate is not historical |
| O09 | 29P rejection remains fail-closed | PROVEN | HISTORICALLY_PROVEN owner behavior; extra A06 gates are not restoration obligations |
| O10 | Position Intent remains non-executing PLAN_ONLY | PROVEN | HISTORICALLY_PROVEN |
| O11 | No order submission or live authority | PROVEN | HISTORICALLY_PROVEN |
| O12 | 29P stages remain independently observable | PROVEN | HISTORICALLY_PROVEN via chain fields, not A06 stage objects |

Downgraded relative to the first A06 attestation: O03/O08/O09 no longer treat
A06-facade mechanics as proven restoration.

## 4) Not restoration obligations

OUT_OF_SCOPE / not historically required:

- A06 facade architecture / stage-object protocol / stage digests
- A06-specific semantic IDs (`a06-intent::`)
- duplicate independent envelope evaluation
- A06-owned Risk/Sizing orchestration
- Packet-as-compute-owner rejection as a novel A06 semantic gate
- SideState-override rejection as a novel A06 semantic gate
- legacy-replay rejection as an A06 restoration invariant
- accidental-execution assertion framework as historical restoration
- extra provenance constraints beyond the proven owner chain

DEFERRED_TO_A08:

- Safety kernel / Safety stage between Risk and executable Intent progression
- any claim that execution admission is restored

## 5) Current-system composition

```text
FUNCTIONAL_STAGE_SEPARATION_REQUIRED=true
MANDATORY_MODULE_SEPARATION=false
A06_IS_COMPOSITION_ADAPTER=true
```

Owners:

| Role | Owner |
|---|---|
| Decision / replay compute | `trading.master_v2.integrated_offline_trading_logic_replay_v1` |
| SideState writer | `trading.master_v2.double_play_state.transition_state` |
| Capital / Risk / Sizing | `src.governance.capital_risk_sizing_v1` |
| Position Intent | `src.governance.canonical_order_intent_v1` |
| Composition adapter | `trading.master_v2.capital_risk_sizing_intent_restore_v1` (not an owner; `CRS_INTENT_RESTORE_V1_PRODUCTIVE_PATH=false`) |

The adapter calls `evaluate_quantity_chain_v1` once. It does not independently
re-evaluate the envelope. Mapping chain fields onto the existing 29Q decision
contract is IMPLEMENTATION_DETAIL, not a second Risk/Sizing computation.

## 6) Non-execution boundary

```text
EXECUTION_MODE=PLAN_ONLY
ORDER_SUBMIT_AUTHORIZED=false
LIVE_AUTHORIZED=false
CanonicalOrderIntentV1.submission_authorized=false
CanonicalOrderIntentV1.execution_eligible=false
SAFETY_RESTORED=false
A08_STARTED=false
```

PLAN_ONLY intent before A08 is not execution admission.

## 7) Remaining unresolved work (not this slice)

```text
A07_PARITY_RESTORE=false
A08_SAFETY_INVARIANT_RESTORE=false
A09_KILL_SWITCH_RESTORE=false
A10_SINGLE_WRITER_RESTORE=false
A11_EV_RESTORE=false
A12_LIVE_GATE_RESTORE=false
```
