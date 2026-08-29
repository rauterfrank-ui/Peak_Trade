# MASTER V2 — Integrated Replay Safety before Intent restore v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Bounded current-system rewire of Integrated Replay call order to Risk/Sizing → Safety → Intent. Not canonical authority. Not a new semantic owner.
docs_token: DOCS_TOKEN_MASTER_V2_INTEGRATED_REPLAY_SAFETY_BEFORE_INTENT_RESTORE_V1

```text
HISTORICAL_REFERENCE_AUTHORITY=NONE
FORENSIC_REFERENCE_AUTHORITY_NONE=true
RESTORATION_TARGET_ID=MASTER_V2_DOUBLE_PLAY_CONSERVED_REFERENCE_V1
SLICE_ID=INTEGRATED_REPLAY_SAFETY_BEFORE_INTENT_COMPUTE_OWNER_REWIRE_V1
HISTORICAL_STAGE=Safety
A07_HISTORICAL_STAGE_IDENTITY=UNPROVEN
A07_IDENTITY_STATUS=UNPROVEN
A07_LABEL_DISPOSITION=RETIRE_AS_HISTORICAL_STAGE_LABEL
PROGRAM_LABEL=A08_REMAINDER
HISTORICAL_ORDER=Risk/Sizing → Safety → Intent
PREVIOUS_CURRENT_ORDER=Risk/Sizing → Intent → Safety
RESTORED_REPLAY_ORDER=Risk/Sizing → Safety → Intent
COMPUTE_OWNER_IDENTITY_CHANGED=false
COMPUTE_OWNER_AUTHORITY_CHANGED=false
COMPUTE_OWNER_WIRING_CHANGED=true
RISK_OWNER_CHANGED=false
SAFETY_OWNER_CHANGED=false
INTENT_OWNER_CHANGED=false
SIDESTATE_OWNER_CHANGED=false
RECON_OWNER_CHANGED=false
KILLSWITCH_OWNER_CHANGED=false
CURRENT_SYSTEM_SEMANTIC_DELTA=true
NEW_SEMANTIC_POLICY=false
UNATTESTED_FORMULA_CHANGE=false
EV_RESTORED=false
EV_REQUIRED_FOR_THIS_SLICE=false
XP03_ACTIVATED=false
EXECUTION_RESTORED=false
LIVE_RESTORED=false
A06_MUTATED=false
SIBLING_SLICE_MUTATED=false
REPLAY_ROUTED_THROUGH_SIBLING_ADAPTER=false
NO_TRADING=true
NO_LIVE_AUTHORITY=true
NO_EXECUTION_AUTHORITY=true
```

This document is bounded slice attestation, implementation notes, evidence
mapping, and negative contract. It is not historical authority, not class
SSOT, and not a full Master V2 / Double Play E2E restoration claim.

A08 is restoration-program bookkeeping only. It is not historical authority
for the stage name. `MASTER_V2_HISTORICAL_STAGE_NAME` is Safety, not A08.

## 1) Epistemic classes

| Class | Meaning |
|---|---|
| HISTORICALLY_PROVEN | Supported by Master Runbook §1 / §5.3 and existing STEP-29P / Safety / 29Q owners |
| IMPLEMENTATION_DETAIL | Compute-owner wiring with no new business/authority semantics |
| OUT_OF_SCOPE | Not this slice |
| FORENSIC_REFERENCE_AUTHORITY_NONE | Forensic package is evidence/reference only |

This spec is not Restoration SSOT. Restoration admission authority remains the
merged class `HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_V1`.

## 2) Bounded restoration target

```text
existing upstream decision / SideState / EntryExit
  → STEP-29P bind_capital_risk_sizing_offline_replay_evidence_v0
  → existing Safety bind_safety_kernel_offline_replay_evidence_v0
  → STEP-29Q bind_canonical_order_intent_offline_replay_evidence_v0
       PLAN_ONLY / submission_authorized=false
       skipped for ENTER_LONG / ENTER_SHORT when Safety hard_block_reasons is nonempty
  → existing reconciliation unknown-outcome evidence binder
  → existing killswitch boundary evidence binder
  → existing result / evidence packaging
```

Invariant: Risk/Sizing → Safety → Intent.

Not Risk/Sizing → Intent → Safety.
Not Safety → Recon → KillSwitch → Intent as a historical chain.

29Q is not called before Safety. 29Q is invoked at most once per Replay path.
Safety-blocked ENTER progression must not create an ENTER CanonicalOrderIntent,
while downstream evidence binders remain active.

Replay remains the Compute Owner. Identity and authority do not change.
Wiring changes. Decision Packet remains derived handoff. Double Play /
SideState writer remains unchanged and is not re-run because Safety blocks
entry.

## 3) Existing owners reused unchanged

| Role | Owner |
|---|---|
| Decision / replay compute | `trading.master_v2.integrated_offline_trading_logic_replay_v1` |
| SideState writer | `trading.master_v2.double_play_state.transition_state` |
| Capital / Risk / Sizing | `src.governance.capital_risk_sizing_v1` via existing CRS replay binder |
| Safety | `trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0.bind_safety_kernel_offline_replay_evidence_v0` |
| Position Intent | `src.governance.canonical_order_intent_v1` via existing 29Q replay binder |
| Recon evidence binder | `trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0` |
| KillSwitch evidence binder | `trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0` |

ENTER suppression consumes `hard_block_reasons` from the existing Safety
result. Replay does not reproduce the Safety condition table. Outcome
classification uses existing `decision_outcome` evidence.

The later reconciliation binder is not the same concept as Safety's
`reconciliation_state` input. The later killswitch binder is not the same
concept as Safety's killswitch input.

## 4) Sibling / A06 relation

The merged sibling adapter
`capital_risk_sizing_safety_intent_restore_v1.py` remains
`INDEPENDENT_REFERENCE_COMPOSITION` /
`PROOF_OR_RESTORE_COMPOSER_ONLY`. Replay does not import or route
through it. `PRODUCTIVE_OWNER=false`.

A06 `capital_risk_sizing_intent_restore_v1.py` remains closed and is not
the historical orchestration SSOT.
`CRS_INTENT_RESTORE_V1_PRODUCTIVE_PATH=false`.

## 5) Non-execution / negative contract

```text
EXECUTION_MODE=PLAN_ONLY
ORDER_SUBMIT_AUTHORIZED=false
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
CANARY_AUTHORIZED=false
EV_RESTORED=false
XP03_ACTIVATED=false
A06_MUTATED=false
SIBLING_SLICE_MUTATED=false
REPLAY_ROUTED_THROUGH_SIBLING_ADAPTER=false
29Q_MAX_INVOCATIONS_PER_REPLAY=1
29Q_CALLED_BEFORE_SAFETY=false
SAFETY_HARD_BLOCK_CAN_CREATE_ENTER_INTENT=false
```

No order submit, exchange/client/network submission path, execution
admission, live/testnet/canary authority, enabled/armed change, new Compute /
Risk / Sizing / Safety / Intent / SideState / Recon / KillSwitch owner,
EV binding, XP-03 activation, or Recovery mutation.

## 6) Remaining unresolved work (not this slice)

```text
A09_KILL_SWITCH_RESTORE=false
EV_RESTORE=false
EXECUTION_RESTORE=false
LIVE_GATE_RESTORE=false
FULL_MASTER_V2_DOUBLE_PLAY_E2E=false
```
