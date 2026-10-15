# GHOSV Bounded Context V1

Package: `src/ops/ghosv_bounded_context_v1`

| Slice | Module | Role |
| --- | --- | --- |
| S01 | `s01_evidence_ingest_v1` | Read-only typed evidence ingest |
| S02 | `s02_identity_correlation_v1` | Explicit-ID correlation only |
| S03 | `s03_semantic_integrity_v1` | Contract integrity checks |
| S04 | `s04_traffic_light_v1` | GREEN/YELLOW/RED aggregation |
| S05 | `s05_critical_incident_v1` | Typed critical incidents |
| S06 | `s06_safety_authority_adapter_v1` | **DISABLED** safety handoff contract |
| S07 | `s07_safety_response_witness_v1` | Read-only response witness |

Entry: `run_ghosv_bounded_context_v1` in `pipeline_v1.py`.

**AUTHORITY:** GHOSV_TRADING_AUTHORITY=NONE, GHOSV_EXECUTION_AUTHORITY=NONE.
