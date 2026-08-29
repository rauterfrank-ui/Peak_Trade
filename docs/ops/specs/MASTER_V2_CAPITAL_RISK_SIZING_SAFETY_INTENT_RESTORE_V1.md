# MASTER V2 — Capital → Risk → Sizing → Safety → PLAN_ONLY Intent restore v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Bounded current-system composition of STEP-29P, existing Safety, and STEP-29Q after A01–A05 evidence. Not canonical authority. Not a new semantic owner.
docs_token: DOCS_TOKEN_MASTER_V2_CAPITAL_RISK_SIZING_SAFETY_INTENT_RESTORE_V1

```text
HISTORICAL_REFERENCE_AUTHORITY=NONE
FORENSIC_REFERENCE_AUTHORITY_NONE=true
REFERENCE_MODEL=MASTER_V2_DOUBLE_PLAY_CONSERVED_REFERENCE_V1
HISTORICAL_STAGE=Safety
A07_HISTORICAL_STAGE_IDENTITY=UNPROVEN
A07_IDENTITY_STATUS=UNPROVEN
A07_LABEL_DISPOSITION=RETIRE_AS_HISTORICAL_STAGE_LABEL
RESTORED_CHAIN=29P → Safety → 29Q PLAN_ONLY
A06_REWRITTEN=false
REPLAY_REORDERED=false
REPLAY_ORDERING_DIVERGENCE_STATUS=PROVEN
REPLAY_ORDERING_REMEDIATED_THIS_SLICE=false
EV_RESTORED=false
EV_REQUIRED_FOR_THIS_SLICE=false
EXECUTION_RESTORED=false
LIVE_RESTORED=false
SAFETY_OWNER_CHANGED=false
SAFETY_AUTHORITY_CHANGED=false
SAFETY_WIRING_CHANGED=true
CURRENT_SYSTEM_SEMANTIC_DELTA=true
NO_TRADING=true
NO_LIVE_AUTHORITY=true
NO_EXECUTION_AUTHORITY=true
ADAPTER_COMPUTE_OWNER=false
ADAPTER_RISK_OWNER=false
ADAPTER_SIZING_OWNER=false
ADAPTER_SAFETY_OWNER=false
ADAPTER_INTENT_OWNER=false
```

This document is bounded slice attestation, implementation notes, evidence
mapping, and negative contract. It is not historical authority, not class
SSOT, not new Safety policy, and not a full Master V2 / Double Play E2E
restoration claim.

A08, if used in restoration-program bookkeeping, is a restoration-program
label only. It is not historical authority for the stage name.
`MASTER_V2_HISTORICAL_STAGE_NAME` is Safety, not A08.

## 1) Epistemic classes

| Class | Meaning |
|---|---|
| HISTORICALLY_PROVEN | Supported by forensic Master V2 / Double Play structure plus existing STEP-29P / Safety / 29Q owners |
| IMPLEMENTATION_DETAIL | Adapter mapping with no new business/authority semantics |
| OUT_OF_SCOPE | Not this slice |
| FORENSIC_REFERENCE_AUTHORITY_NONE | Forensic package is evidence/reference only |

This spec is not Restoration SSOT. Restoration admission authority remains the
merged class `HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_V1`.

## 2) Bounded restoration target

```text
A01–A05 authoritative CanonicalTradingDecisionEvidenceV1
  → STEP-29P evaluate_quantity_chain_v1
  → existing Safety owner bind_safety_kernel_offline_replay_evidence_v0
  → STEP-29Q build_canonical_order_intent_v1
       PLAN_ONLY / submission_authorized=false
       only if Safety hard_block_reasons is empty
```

Invariant: Risk/Sizing → Safety → Intent.

Not Risk/Sizing → Intent → Safety.
Not Risk/Sizing → Intent → Safety → Intent.

29Q is not called before Safety. 29Q is invoked at most once per flow.
This adapter does not build an Intent and then discard or rebuild it around
Safety.

Replay remains compute owner and is not mutated. Decision Packet remains
derived handoff. Double Play / SideState writer remains unchanged.

## 3) Existing owners reused unchanged

| Role | Owner |
|---|---|
| Decision / replay compute | `trading.master_v2.integrated_offline_trading_logic_replay_v1` (unchanged this slice) |
| SideState writer | `trading.master_v2.double_play_state.transition_state` (unchanged) |
| Capital / Risk / Sizing | `src.governance.capital_risk_sizing_v1.evaluate_quantity_chain_v1` |
| Safety | `trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0.bind_safety_kernel_offline_replay_evidence_v0` |
| Position Intent | `src.governance.canonical_order_intent_v1.build_canonical_order_intent_v1` |
| Composition adapter | `trading.master_v2.capital_risk_sizing_safety_intent_restore_v1` (not an owner) |

Safety role on this path: boundary/block evidence only. No sizing, quantity
ownership, direction selection, SideState write, Intent construction,
submission permission, execution, or live authority.

Established Safety outputs consumed (not invented): `hard_block_reasons`,
`reason_codes`, `safety_boundary_ref`, `BOUND_OFFLINE`,
`no_permission_issued=true`.

## 4) Evidence mapping

Safety context is taken from existing `IntegratedOfflineReplayInputV1` /
A01–A05-compatible fields:

- `safety_mode`
- `safety_exit_signal`
- `reconciliation_state`
- `position_state`
- `trading_gate`
- killswitch / `safety_decision_allowed` mapping already used by the compute
  owner when binding Safety

The adapter does not invent implicit permissive defaults that erase a block.
Missing Safety context fails closed (`TypeError`). The existing Safety owner
condition table is not reproduced.

A06 is not called. A06 output is not the semantic implementation of this
chain. A06 remains evidence of the prior bounded restoration slice.

## 5) Replay ordering divergence (deferred)

```text
REPLAY_ORDERING_DIVERGENCE_STATUS=PROVEN
REPLAY_ORDERING_REMEDIATED_THIS_SLICE=false
```

Integrated replay currently still invokes CRS → Intent → Safety. This slice
restores only the bounded sibling composition CRS → Safety → Intent. It does
not create a second Compute Owner and does not claim full E2E restoration.

## 6) A07 / A08 labels

```text
A07_IDENTITY_STATUS=UNPROVEN
A07_LABEL_DISPOSITION=RETIRE_AS_HISTORICAL_STAGE_LABEL
HISTORICAL_STAGE=Safety
```

A07 is not implemented and is not treated as a historical Master V2 /
Double Play stage identity. Do not rename historical Safety to A07 to
preserve numbering.

## 7) Non-execution / negative contract

```text
EXECUTION_MODE=PLAN_ONLY
ORDER_SUBMIT_AUTHORIZED=false
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
CANARY_AUTHORIZED=false
CanonicalOrderIntentV1.submission_authorized=false
CanonicalOrderIntentV1.execution_eligible=false
EV_RESTORED=false
XP03_ACTIVATED=false
A06_MUTATED=false
REPLAY_MUTATED=false
```

No order submit, exchange/client/network submission path, execution
admission, live/testnet/canary authority, enabled/armed change, new Compute /
Risk / Sizing / Safety / Intent owner, SideState writer, EV binding, XP-03
activation, or Recovery mutation.

## 8) Remaining unresolved work (not this slice)

```text
REPLAY_SAFETY_BEFORE_INTENT_REORDER=false
EV_RESTORE=false
EXECUTION_RESTORE=false
LIVE_GATE_RESTORE=false
FULL_MASTER_V2_DOUBLE_PLAY_E2E=false
```
