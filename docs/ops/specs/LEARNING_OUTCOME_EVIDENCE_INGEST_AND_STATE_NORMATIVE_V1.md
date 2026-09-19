---
docs_token: DOCS_TOKEN_LEARNING_OUTCOME_EVIDENCE_INGEST_AND_STATE_NORMATIVE_V1
status: active
scope: Normative fail-closed productive learning outcome ingest and learning_state_record transitions; no trading/promotion authority
capability: LEARNING_OUTCOME_EVIDENCE_INGEST_AND_STATE_NORMATIVE_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
---

# Learning Outcome Evidence Ingest and State Normative V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
WORKPACKAGE_ID=SELF_LEARNING_PRODUCTIVE_CLOSED_LOOP_V1
SLICE_ID=S2A_NORMATIVE_FOUNDATION
OWNER_GO=OWNER_GO_SELF_LEARNING_CLOSED_LOOP_SEMANTIC_FOUNDATION_A+C
BOUND_ORIGIN_MAIN_SHA=d2bb81c340fe30b48139746058512e1cc357c20c
LEARNING_PRODUCTIVE_AUTHORITY=NONE
TRADING_AUTHORITY=NONE
EXECUTION_AUTHORITY=NONE
PROMOTION_AUTHORITY_EFFECT=NONE
PROMOTION_AUTHORITY_ACTIVATION=false
EXTERNAL_EFFECT_AUTHORIZED=false
IMPLEMENTATION_AUTHORIZED=true
OWNER_ADJUDICATION_BOUND=true
ARCHITECTURE_CHOICE=A+C
```

Machine-readable decision:
`config/governance/learning_outcome_evidence_ingest_and_state_decision_v1.json`

Predecessor productive chain:

- `docs/ops/specs/DDO_OUTCOME_TO_PROMOTION_PRODUCTIVE_BINDING_NORMATIVE_V1.md` (evaluation terminus; no promotion join)
- `docs/ops/specs/DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1.md` (`AppendOnlyDdoLedgerV0`)

## 1. Flow (binding)

```text
EvaluationBundle (outcome_record + attribution_record + counterfactual_record)
  → LEARNING_OUTCOME_EVIDENCE_INGEST_V1 (fail-closed)
  → learning_state_record_v0 (append-only)
  → deterministic state transition (reduce)
  → next-cycle feedback seam (opaque economic_score label only)
```

## 2. State identity / version / provenance

| Rule | Semantics |
| --- | --- |
| `state_scope_id` | Deterministic scope from session + account identity (`derive_learning_state_scope_id_v1`) |
| `state_version` | Monotonic +1 per non-idempotent ingest within scope |
| `ingest_sequence` | Count of successful non-idempotent ingests |
| `evaluation_bundle_fingerprint` | SHA-256 over canonical JSON of three evaluation `content_hash` values |
| `prior_state_record_ref` | Previous `learning_state_record` in scope chain |
| Causal parents | Outcome + attribution + counterfactual record ids (+ prior state when present) |

## 3. Ordering / idempotency / replay

| Condition | Behavior |
| --- | --- |
| Same fingerprint as prior state in scope | **Idempotent** — return prior state, no version bump |
| Same fingerprint re-append to ledger | Ledger `IDEMPOTENT_REPLAY` |
| `outcome.event_time_utc` strictly before prior `last_event_time_utc` | **Fail-closed** `LEARNING_INGEST_OUT_OF_ORDER_EVENT_TIME` |
| Missing / invalid bundle cross-refs | **Fail-closed** |
| Restart | Reconstruct latest state per `state_scope_id` by max `state_version` from ledger |

## 4. S2B field adjudication

| Field / concern | Class | Productive reducer |
| --- | --- | --- |
| `state_scope_id`, `state_version`, `ingest_sequence` | RATIFIED_UPDATE_SEMANTICS | Yes |
| `evaluation_bundle_fingerprint`, record refs, causal parents | RATIFIED_UPDATE_SEMANTICS | Yes |
| `last_event_time_utc` (ordering anchor) | RATIFIED_UPDATE_SEMANTICS | Yes |
| `next_cycle_economic_score_label` | RATIFIED_UPDATE_SEMANTICS | Opaque copy for feedback seam only |
| `last_evaluation_horizon`, `last_actual_outcome_ref` | OBSERVATION_ONLY | Stored, not interpreted |
| `last_decision_score`, `last_safety_score`, `last_economic_score` | OBSERVATION_ONLY | Opaque token copy only |
| regime | UNKNOWN | No productive reducer |
| calibration (numeric) | SCHEMA_ONLY | No numeric calibration in v1 |
| performance / error analytics | OBSERVATION_ONLY | No derived metrics |
| drift (`drift_*` records) | SCHEMA_ONLY / OFFLINE_ONLY | No auto projection from outcomes in v1 |
| model-quality | UNKNOWN | No productive reducer |

## 5. Feedback seam (cycle N → N+1)

```text
CONSUMER=real_outcome_horizon_productive_host_v1 (via bridge ddo_n_bars_economic_score)
CONSUMED_STATE_FIELDS=next_cycle_economic_score_label
SEMANTIC_EFFECT=opaque evaluation_observation economic_score label only
AUTHORITY_OWNER=peak_trade.learning.ddo.real_outcome_horizon_productive_host_v1
TRADING_DECISION_AUTHORITY=UNCHANGED (Master V2 + Double Play)
```

## 6. Forbidden

- Promotion, optimization universe, trading/risk/execution mutation from learning state
- Candidate/hypothesis lineage invention from outcomes
- Drift assessment auto-generation without separate Owner-GO
- Numeric calibration / ML thresholds / regime classification not ratified in v1
