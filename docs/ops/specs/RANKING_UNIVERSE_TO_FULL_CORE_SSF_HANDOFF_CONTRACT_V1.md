---
docs_token: DOCS_TOKEN_RANKING_UNIVERSE_TO_FULL_CORE_SSF_HANDOFF_CONTRACT_V1
status: active
scope: CURRENT Ranking-universe to Full-Core Single-Selected-Future handoff contract; assertion/validation only; no second authority; no new runtime join
capability: NONE
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-16
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
SELECTION_AUTHORITY: false
ALPHA_ALLOWED: false
HARD_STOP: true
---

# Ranking Universe to Full-Core SSF Handoff Contract V1

```text
DOCUMENT_CLASS=DOCS_AND_TYPED_CONTRACT_NON_AUTHORIZING_HANDOFF_ASSERTION
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=OWNER_GO_RANKING_UNIVERSE_TO_FULL_CORE_SSF_HANDOFF_CONTRACT_V1
CONTRACT_ID=RANKING_UNIVERSE_TO_FULL_CORE_SSF_HANDOFF_CONTRACT_V1
AUTHORITY_EFFECT=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
VALIDATOR_AUTHORITY_EFFECT=NONE
SECOND_AUTHORITY_CREATED=false
NEW_RUNTIME_JOIN_CREATED=false
PRODUCTIVE_RUNTIME_SEMANTICS_CHANGED=false
LAST_RANKING_UNIVERSE_AUTHORITY=CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1
HANDOFF_INPUT_OBJECT=SingleSelectedFutureSelectionV1
FIRST_EXTERNAL_RUNTIME_CONSUMER=run_single_selected_future_runtime_binding_gate_v1
CAP24_ARCHITECTURAL_CLASSIFICATION=SHARED_BOUNDARY_SEAM
CAP24_IS_FULL_CORE_PACKAGE_MEMBER=false
FULL_CORE_INGEST_OBJECT=BoundInstrumentV1
FIRST_TRADING_DECISION_CONSUMER=run_current_productive_master_v2_runtime_cycle_v1
MF_EGRESS_NOT_THIS_HANDOFF=true
C1_GATE_NATIVE_ID_JOINED=false
```

Master Runbook SSOT pointer: §4.5.14.

Typed assertion/validator:
`src&#47;ops&#47;ranking_universe_to_full_core_ssf_handoff_contract_v1.py`.

This file does **not** replace Cap 2.1–2.4 producer specs, does **not**
activate those capabilities, does **not** join MF, and does **not**
rewrite historical Cap 2.4 wording (`CAP24_ROLE=RUNTIME_BINDING_CONSUMER`)
as if that standing producer-spec label had already been this CURRENT
handoff contract. Cap 2.4 remains a shared boundary seam, not a Full-Core
package member.

## 1. Purpose

Persist and assert the CURRENT productive handoff:

```text
ProductiveFuturesRankingSnapshotV1
→ Cap 2.3 SingleSelectedFutureSelectionV1
  [LAST_RANKING_UNIVERSE_AUTHORITY]
→ run_single_selected_future_runtime_binding_gate_v1
  [Cap 2.4; SHARED_BOUNDARY_SEAM; FIRST_EXTERNAL_RUNTIME_CONSUMER]
→ BoundInstrumentV1
  [FULL_CORE_INGEST_OBJECT]
→ run_current_productive_master_v2_runtime_cycle_v1
  [FIRST_TRADING_DECISION_CONSUMER]
→ run_integrated_offline_trading_logic_replay_v1
```

The typed module is an assertion/validation surface over existing DTOs. It
is not a producer and not an owner.

## 2. Authority split

```text
CAP22_ROLE=RANKING_CONTEXT_ONLY
CAP22_SELECTION_AUTHORITY=false
CAP22_TRADING_AUTHORITY=false
CAP22_WIRE_AUTHORITY=false
CAP23_ROLE=SOLE_PRODUCTIVE_SELECTION_AUTHORITY
CAP24_ROLE=VALIDATE_AND_BIND_EXISTING_SELECTED_IDENTITY
CAP24_MAY_RERANK=false
CAP24_MAY_RESELECT=false
CAP24_MAY_REPLACE_SELECTED_INSTRUMENT_IDENTITY=false
MASTER_V2_ROLE=TRADING_DECISION_AUTHORITY_ON_BOUND_INSTRUMENT
MASTER_V2_MAY_RESELECT_INSTRUMENT=false
```

Cap 2.2 may produce ranking context only. Cap 2.3 is the sole productive
selection authority. Cap 2.4 validates freshness/integrity, ranking and
universe references, and native identity, then binds the already-selected
identity. Master V2 consumes the bound identity and must not determine a
new instrument.

## 3. Boundary transform

```text
BOUNDARY_TRANSFORM=validate_selection_freshness_integrity
+validate_ranking_universe_references
+validate_native_identity
+bind_existing_selected_identity
+NO_rerank
+NO_reselect
```

## 4. Field lineage

No silent canonical/native-ID normalization. Exact string identity is
required. Mismatch or missing required provenance is fail-closed.

| Field | Cap 2.3 `SingleSelectedFutureSelectionV1` | Cap 2.4 `BoundInstrumentV1` | Master V2 / replay |
|---|---|---|---|
| `instrument_id` | derived by Cap 2.3 from ranked candidate; preserved | preserved and validated | consumed; not reselected |
| `venue_native_id` | derived by Cap 2.3 from ranked candidate; preserved | preserved and validated | consumed; not reselected |
| `selection_id` | derived in Cap 2.3 | preserved | dropped before replay |
| `ranking_snapshot_id` | carried from Cap 2.2 snapshot | preserved | dropped before replay |
| `universe_snapshot_id` | absent/dropped on the SSF DTO | re-derived/validated from matched ranking+universe | dropped before replay |

## 5. Non-goals

```text
C1_GATE_NATIVE_ID_UNCHANGED=true
MF_PRODUCTIVE_JOIN_CHANGED=false
ACTIVATED_FLAGS_CHANGED=false
SELECTION_POLICY_SEMANTICS_CHANGED=false
TRADING_LOGIC_CHANGED=false
EXECUTION_SURFACE_CHANGED=false
STEP_29P_CHANGED=false
STEP_29Q_CHANGED=false
FILEGATE_CHANGED=false
```

Isolated MF egress remains a separate unbound handoff and is not this
chain (`MF_EGRESS_NOT_THIS_HANDOFF=true`).
