---
docs_token: DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_EVIDENCE_INPUT_PLANE_P1_AUTHORITY_CONTRACTS_AND_SCHEMAS_V1
status: active
scope: P1 authority contracts and canonical A/B/L6 typed schemas only; no runtime activation
workpackage: P1_MASTER_V2_DOUBLE_PLAY_EVIDENCE_INPUT_PLANE_AUTHORITY_CONTRACTS_AND_SCHEMAS_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-26
---

# Master V2 / Double Play — Evidence & Input Plane P1 Authority Contracts & Schemas V1

Owner-ratified **contract and schema materialization only** for Component A, Component B,
and the bounded typed L6 external-evidence input seam (Option B). O-002 is **RATIFIED**.

```text
RUNTIME_AUTHORIZATION_EFFECT=NONE
A_RUNTIME_IMPLEMENTATION_AUTHORIZED=false
B_RUNTIME_IMPLEMENTATION_AUTHORIZED=false
PRODUCTIVE_L6_BINDING_AUTHORIZED=false
FINAL_D_T_FORMULA_SELECTED=false
L6_INTERPRETATION_AUTHORITY=L6_ONLY
PROPOSED_D_T_MUST_NOT_BECOME_A_B_INFORMATION_CARRIER=true
```

## Topology (contract plane)

```text
Producer → Component A (adjudicate CanonicalMasterV2EvidenceEnvelopeV1)
         → Component B (CanonicalDpLayerInputBindingV1 → L6 target only)
         → L6BoundedTypedExternalEvidenceInputV1 (P2+ runtime consumer; not P1)
Parallel preserved: P4 ExplicitDtProposalV1 → proposed_d_t → DynamicScopeGeneratorInputV1
```

## Component A

| Field | Value |
| --- | --- |
| Authority | `BOUNDED_EVIDENCE_ADJUDICATION_ONLY` |
| Trading authority | `NONE` |
| Schema | `CanonicalMasterV2EvidenceEnvelopeV1` / `canonical_master_v2_evidence_envelope.v1` |
| Code | `src/governance/master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1/` |

## Component B

| Field | Value |
| --- | --- |
| Authority | `BOUNDED_DP_INPUT_CREATION_AND_BINDING_ONLY` |
| Trading authority | `NONE` |
| DP state mutation | `NONE` |
| Allowed B targets (P1) | `L6_DYNAMIC_SCOPE_GENERATOR` only |
| Forbidden | `proposed_d_t`, `d_t`, `final_d_t`, formula selection, heterogeneous collapse |
| Schema | `CanonicalDpLayerInputBindingV1` / `canonical_dp_layer_input_binding.v1` |

## L6 typed seam

| Field | Value |
| --- | --- |
| Admissibility | `YES_BOUNDED_TYPED_ONLY` (O-002 RATIFIED) |
| Contract | `L6BoundedTypedExternalEvidenceInputV1` |
| L6 semantic authority | **UNCHANGED**; interpretation **L6_ONLY** (future P2 wiring) |
| Existing `proposed_d_t` | **Preserved** (P4/O-R2 unchanged) |

## Owner decision snapshot

`config/governance/master_v2_double_play_evidence_input_plane_p1_owner_decision_v1.json`

## Evidence

`docs/evidence/master_v2_double_play_evidence_input_plane_p1/p1_proof_bundle_v1.json`

## Verification

```bash
./scripts/pt -m pytest tests/governance/test_master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.py -q
./scripts/pt -m pytest tests/governance/test_master_v2_double_play_evidence_input_plane_p0_evidence_seam_census_v1.py -q
```
