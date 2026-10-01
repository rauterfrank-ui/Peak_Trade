---
docs_token: DOCS_TOKEN_CURRENT_PRODUCTIVE_GOLDEN_HAPPY_VECTOR_FORENSIC_OBSERVABILITY_V1
status: active
scope: Forensic Golden Happy Vector observability for directional signal_strength and pre-observation entry state; default OFF; no trading authority
capability: CURRENT_PRODUCTIVE_GOLDEN_HAPPY_VECTOR_FORENSIC_OBSERVABILITY_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-10-01
---

# CURRENT Productive Golden Happy Vector Forensic Observability V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
RUNTIME_AUTHORIZATION_EFFECT=NONE
TRADING_AUTHORITY=NONE
EXECUTION_AUTHORITY=NONE
POST_ALLOWED=false
EXTERNAL_EFFECT_AUTHORIZED=false
OBSERVABILITY_DEFAULT_ENABLED=false
```

## 1. Purpose

Persist **already computed** productive directional assessment values and a
**single immutable entry-state snapshot** for bounded Golden Happy Vector runs,
without altering trading semantics, thresholds, selection, GET/cache behavior,
or product budgets.

## 2. Evidence products

| Product | Path (under `--evidence-root`) | When |
|---------|--------------------------------|------|
| Directional signal rows | `directional_signal_observability_v1.jsonl` | Per MV2 cycle with selected-lane assessment (session ON) |
| Entry state snapshot | `continuous_run_entry_state_snapshot_v1.json` | Once after rotation reconciliation, before first `poll()` |

## 3. Enablement

```text
CLI=--enable-golden-happy-vector-forensic-observability-v1
API=enable_golden_happy_vector_forensic_observability_v1
DEFAULT=false
INDEPENDENT_OF=--enable-natural-market-data-capture-v1
```

## 4. Signal capture semantics

- `signal_strength` is read from `IntegratedOfflineReplayIntermediateV1` bull/bear
  assessment (selected lane only); **no** second `compute_signal_strength` in the
  capture path.
- Threshold flags derive from the same persisted strength and CURRENT policy
  thresholds via `map_signal_strength_to_confirmation_assessment_signal_v1` mapping
  family (numeric compare only).
- Capture failure does not change cycle decisions (`OBSERVABILITY_CAPTURE_FAILURE_CHANGES_DECISION=false`).

## 5. Entry snapshot semantics

- Read-only cursor/carrier serialization at continuous-run entry boundary.
- Rotation fresh lane: `present=false`, `reason=MISSING_BY_DESIGN_AFTER_ROTATION`.
- Snapshot write failure before first observation: fail-closed (`ENTRY_STATE_SNAPSHOT_FAILURE_POLICY=FAIL_CLOSED_BEFORE_FIRST_OBSERVATION`).

## 6. Correlation keys

`run_id`, `continuous_run_id`, `cycle_index`, `cycle_instance_id`,
`c1_venue_event_time`, `market_observation_epoch`, `observation_identity_digest`,
`instrument_id` — joinable to existing natural GET capture and S5 cycle evidence.
