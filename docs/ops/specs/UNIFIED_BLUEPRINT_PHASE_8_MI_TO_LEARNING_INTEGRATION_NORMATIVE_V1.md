---
docs_token: DOCS_TOKEN_UNIFIED_BLUEPRINT_PHASE_8_MI_TO_LEARNING_INTEGRATION_NORMATIVE_V1
status: active
scope: Unified Blueprint Phase 8 typed MI forecast/outcome/calibration export into learning evidence path
capability: UNIFIED_BLUEPRINT_PHASE_8_MI_TO_LEARNING_INTEGRATION_V1
last_updated: 2026-09-26
---

# Unified Blueprint Phase 8 — MI→Learning Integration Normative V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=UNIFIED_BLUEPRINT_PHASE_8_MI_TO_LEARNING_INTEGRATION_V1
BLUEPRINT_AUTHORITY=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

Machine-readable closure:
`config/governance/unified_blueprint_phase_8_mi_to_learning_integration_v1.json`

Code owner:
`src/governance/unified_blueprint_phase_8_mi_to_learning_integration_v1.py`

## Purpose

Close inter-loop edge `d02_mi_to_learning` by composing governed MI
`ForecastEvidence`, normative N_BARS realized outcomes, and
`CalibrationEvidence` into typed MI learning evidence exported onto the
existing offline learning evidence path without mutating productive DDO
reducers, MV2/Double-Play, Cap 2.3, or promotion authority.

## Verification

- `tests/learning/test_unified_blueprint_phase_8_mi_to_learning_integration_v1.py`
- `tests/governance/test_unified_blueprint_phase_8_mi_to_learning_integration_v1.py`
- `tests/governance/test_unified_blueprint_d01_d02_topology_adjudication_v1.py`

## Original MI content and optional DDO reference — 2026-11-21

The existing MI record validator now recomputes the original canonical
reproducibility digest before Store append, cold read or export. An unchanged
MI ID cannot retain changed outcome, horizon, price specification, instrument
or conditioned behavior bindings. The existing digest formula and record IDs
are unchanged; historical records are not rewritten.

If an MI export declares a legacy DDO record reference and supplies that
record, the two identities must agree. Reference-only, payload-only and
MI-only exports retain their existing meanings. A reference alone does not
set legacy DDO compatibility. MI evidence and DDO evidence remain different
record types; this does not turn forecast calibration into a PnL/quality label
or a productive DDO state update.
