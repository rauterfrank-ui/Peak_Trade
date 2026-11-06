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

## Evidence envelope consistency (2026-11-04)

The outer Learning-Evidence outcome class must equal the embedded provenance class,
and its single-record pool must match that class. The record owner binds class
and digest; Optimization also checks the declared class/pool and a repeated digest
when supplied. A contradiction is rejected, not silently replaced by a derived
value. Existing minimal direct pool comparison may omit the repeated digest; the
full Learning-Evidence record still requires it. These are consistency checks,
not independent source-truth verification or authority to reinterpret G2 review
labels as realized outcomes.
[Bound before/after checks](../evidence/semantic_target_and_provenance_consistency_v1_2026_11_04/README.md).
