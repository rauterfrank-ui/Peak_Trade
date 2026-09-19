---
docs_token: DOCS_TOKEN_LEARNING_CURRENT_DECISION_CONTRACT_REALIGNMENT_V1
status: active
scope: Normative Learning-only record roles and Double-Play decision bundle join; no trading authority; no outcome horizon
capability: LEARNING_CURRENT_DECISION_CONTRACT_REALIGNMENT_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
---

# Learning Current Decision Contract Realignment V1

```text
DOCUMENT_CLASS=SUBORDINATE_GOVERNANCE_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=OWNER_GO_LEARNING_CURRENT_DECISION_CONTRACT_REALIGNMENT_V1_SLICE_1
BOUND_ORIGIN_MAIN_SHA=26492d4fb4acb3184630ff78bb7285eb9ee0fc3f
SLICE_ID=SLICE_1_LEARNING_CURRENT_DECISION_NORMATIVE_BINDING_AND_JOIN_RESOLVER_V1
LEARNING_CURRENT_DECISION_CONTRACT_REALIGNMENT_V1=BOUND
RUNTIME_AUTHORIZATION_EFFECT=NONE
TRADING_AUTHORITY=NONE
EXECUTION_AUTHORITY=NONE
PROMOTION_AUTHORITY_EFFECT=NONE
LEARNING_PRODUCTIVE_AUTHORITY=NONE
ATLAS_AUTHORITY=NONE
```

Navigation-only. Master Runbook remains SSOT. This contract does **not**
authorize Live, Testnet, orders, credentials, producer mutation,
DecisionEvent enum expansion, outcome-horizon engines, optimizers,
productive host capture-session join, or promotion activation.

## 1. Normative record roles

```text
PRODUCER_SEMANTICS_AUTHORITATIVE=true
DOUBLE_PLAY_OBSERVATION_IS_PROJECTION_NOT_OWNER=true
DECISION_EVENT_IS_ENVELOPE_ONLY=true
NO_DECISION_EVENT_ENUM_EXPANSION=true
```

| Record | Role |
|--------|------|
| `decision_event_v0` | Generic observation / lineage envelope per capture seam |
| `double_play_entry_exit_observation_v1` | Typed learning projection of producer decision semantics |
| `double_play_entry_exit_policy_input_evidence_v1` | Pre-decision input evidence (not outcome authority) |

Authoritative actionable token for Double-Play learning:
`OBS.producer_canonical_payload.decision_outcome` only.

## 2. Join identity (fail-closed)

Primary: `decision_event_ref` from observation and optional input evidence to
DecisionEvent. Resolve observation uniquely (0 → `SIBLING_OBSERVATION_ABSENT`,
>1 → `SIBLING_OBSERVATION_AMBIGUOUS`). Bind typed input evidence via
`typed_output_observation_ref` when present. Verify digest/ref integrity.
Do not infer `decision_outcome` from DecisionEvent envelope fields.
Do not invent `cycle_id` semantics.

Implementation owner:
`src/learning/deterministic_decision_outcome_v0/current_decision_learning_binding_v1.py`

```text
RESOLVER_ID=peak_trade.learning.ddo.resolve_current_double_play_decision_bundle_v1
JOIN_USES_EXISTING_REFS_AND_DIGESTS_ONLY=true
MISSING_SIBLING_FAIL_CLOSED=true
```

## 3. Explicit non-goals (Slice 1)

```text
NO_CAPTURE_BEHAVIOR_CHANGE=true
NO_EVALUATION_ENGINE_CHANGE=true
NO_CHALLENGER_CHANGE=true
NO_OUTCOME_HORIZON=true
NO_PRODUCTIVE_HOST_JOIN=true
EXTERNAL_EFFECT_AUTHORIZED=false
```

Slice 2 (consumer rebind) requires separate Owner-GO.
