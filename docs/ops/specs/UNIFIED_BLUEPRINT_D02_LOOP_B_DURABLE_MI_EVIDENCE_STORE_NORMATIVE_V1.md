---
docs_token: DOCS_TOKEN_UNIFIED_BLUEPRINT_D02_LOOP_B_DURABLE_MI_EVIDENCE_STORE_NORMATIVE_V1
status: active
scope: Unified Blueprint D02 Loop-B durable MI offline evidence store (forecast/calibration/research)
capability: UNIFIED_BLUEPRINT_D02_LOOP_B_DURABLE_MI_EVIDENCE_STORE_V1
last_updated: 2026-09-26
---

# Unified Blueprint D02 Loop-B — Durable MI Evidence Store Normative V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=UNIFIED_BLUEPRINT_D02_LOOP_B_DURABLE_MI_EVIDENCE_STORE_V1
BLUEPRINT_AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

Machine-readable closure:
`config/governance/unified_blueprint_d02_loop_b_durable_mi_evidence_store_v1.json`

Code owner:
`src/governance/unified_blueprint_d02_loop_b_durable_mi_evidence_store_v1.py`

Store owner:
`src/learning/market_intelligence_forecast_calibration_offline_stack_v1/mi_offline_durable_evidence_store_v1.py`

## Purpose

Close inter-loop edge `d02_loop_b_market_intelligence_offline` durable MI
evidence persistence by storing typed ForecastEvidence + CalibrationEvidence +
MARKET_INTELLIGENCE_RESEARCH_EVIDENCE envelopes with deterministic identity,
append-only idempotent write, restart-safe read, and Phase-10 multi-cycle
replay binding. Market-state refs remain caller-supplied opaque refs; this
workpackage does not acquire market-fact ownership or invent a Materialized
Market State/Behavior producer.

## Verification

- `tests/learning/test_mi_offline_durable_evidence_store_v1.py`
- `tests/learning/test_unified_blueprint_d02_loop_b_durable_mi_evidence_store_v1.py`
- `tests/governance/test_unified_blueprint_d02_loop_b_durable_mi_evidence_store_v1.py`
- `tests/governance/test_unified_blueprint_d01_d02_topology_adjudication_v1.py`
