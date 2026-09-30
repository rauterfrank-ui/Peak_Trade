# CURRENT Outcome/Evidence Provenance Contract V1

```
CONTRACT_ID=CURRENT_OUTCOME_EVIDENCE_PROVENANCE_CONTRACT_V1
OWNER=src/learning/deterministic_decision_outcome_v0/outcome_evidence_provenance_v1.py
RUNTIME_AUTHORIZATION_EFFECT=NONE
UNIVERSAL_REALM_ENUM=false
```

Orthogonal provenance dimensions (no fabricated `realm_id` enum). Embedded on `outcome_record_v0.outcome_evidence_provenance`, copied through learning state/export.

Eligibility gates:

- `self_learning_provenance_eligibility_v1.py`
- `optimization_provenance_eligibility_v1.py` (via `canonical_optimization_universe_learning_input_v1`)

Legacy records without provenance fail closed at ingest/export/optimization boundaries.
