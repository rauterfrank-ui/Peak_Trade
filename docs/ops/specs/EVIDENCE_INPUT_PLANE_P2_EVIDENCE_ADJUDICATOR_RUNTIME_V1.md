---
docs_token: DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_EVIDENCE_INPUT_PLANE_P2_EVIDENCE_ADJUDICATOR_RUNTIME_V1
status: active
scope: P2 Component A bounded evidence adjudicator runtime only; no Component B; no productive binding
workpackage: P2_MASTER_V2_EVIDENCE_ADJUDICATOR_RUNTIME_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-26
---

# Master V2 / Double Play — Evidence & Input Plane P2 Component A Adjudicator Runtime V1

Bounded **Component A** runtime: deterministic evidence intake, validation, normalization, and
adjudication to the P1 `CanonicalMasterV2EvidenceEnvelopeV1` contract only.

```text
A_RUNTIME_IMPLEMENTED=true
A_RUNTIME_IMPLEMENTATION_AUTHORIZED=false
A_RUNTIME_REACHABLE=false
B_RUNTIME_IMPLEMENTED=false
PRODUCTIVE_ACTIVATION_AUTHORIZED=false
PRODUCTIVE_L6_BINDING_AUTHORIZED=false
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

## Authority

| Field | Value |
| --- | --- |
| Component | A (Evidence Adjudicator) |
| Authority | `BOUNDED_EVIDENCE_ADJUDICATION_ONLY` |
| Trading authority | `NONE` |
| DP state mutation | `NONE` |
| Input binding / L6 productive seam | `NONE` (B not implemented) |
| Code | `src/governance/master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1/` |

## Inputs / outputs

- **Intake:** `EvidenceIntakeRecordV1` (registered producer/type/version only)
- **Output:** `MasterV2EvidenceAdjudicationResultV1` with optional P1 envelope on `ADMIT`
- **Registry:** `config/governance/master_v2_double_play_evidence_input_plane_p2_producer_registry_v1.json`

## Verification

```bash
./scripts/pt -m pytest tests/governance/test_master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.py -q
./scripts/pt -m pytest tests/governance/test_master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.py -q
```
