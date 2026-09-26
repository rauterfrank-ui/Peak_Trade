---
docs_token: DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_EVIDENCE_INPUT_PLANE_P4_L6_PRODUCTIVE_SEAM_BINDING_V1
status: active
scope: P4 first approved L6 typed evidence productive seam binding only; no blanket productive activation
workpackage: P4_MASTER_V2_DOUBLE_PLAY_FIRST_APPROVED_LAYER_SEAM_BINDING_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-26
---

# Master V2 / Double Play — Evidence & Input Plane P4 L6 Productive Seam Binding V1

Productive **A → B → L6 typed admission** orchestration for the census-approved Option B L6 seam.
Preserves existing L6 semantic ownership and the parallel mechanical `proposed_d_t` path.

```text
P4_FIRST_APPROVED_SEAM=L6
L6_EXTERNAL_EVIDENCE_ADMISSIBILITY=YES_BOUNDED_TYPED_ONLY
A_RUNTIME_REACHABLE=true
B_RUNTIME_REACHABLE=true
L6_PRODUCTIVE_BINDING=true
PRODUCTIVE_DP_SEAM_BOUND=true
PRODUCTIVE_ACTIVATION_AUTHORIZED=false
PRODUCTIVE_L6_BINDING_AUTHORIZED=true
FINAL_D_T_FORMULA_SELECTED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
EXTERNAL_EFFECT_AUTHORIZED=false
```

## Runtime cut (P4)

| Edge | Class |
| --- | --- |
| Registered producer intake → P2 adjudicator | `CURRENT_EXISTING` (P2) |
| P2 ADMIT → P3 binder | `CURRENT_EXISTING` (P3) |
| P3 BIND → P4 L6 admission gate | `P4_TO_IMPLEMENT` |
| Mechanical `proposed_d_t` + nullline → L6 passthrough owner | `P4_TO_IMPLEMENT` (optional consumption; not sourced from evidence) |
| Full productive Master V2 cycle / P5 producer integration | `OUT_OF_SCOPE` |

## Authority

| Field | Value |
| --- | --- |
| Seam | `L6_DYNAMIC_SCOPE_GENERATOR` typed external evidence only |
| A/B trading authority | `NONE` |
| L6 semantic authority | `UNCHANGED` (`L6_ONLY` interpretation on contract) |
| Code | `src/governance/master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1/` |
| Owner decision | `config/governance/master_v2_double_play_evidence_input_plane_p4_owner_decision_v1.json` |

## Verification

```bash
./scripts/pt -m pytest tests/governance/test_master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1.py -q
./scripts/pt -m pytest tests/governance/test_master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1.py -q
./scripts/pt -m pytest tests/governance/test_master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.py -q
```
