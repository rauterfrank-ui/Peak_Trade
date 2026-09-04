---
title: "MODEL_C up_distance Switch-Event vs Profit-Protection Authority Split v1"
status: "ACTIVE"
owner: "ops"
last_updated: "2026-09-04"
docs_token: "DOCS_TOKEN_MODEL_C_UP_DISTANCE_SWITCH_VS_PROFIT_PROTECTION_AUTHORITY_SPLIT_V1"
---

# MODEL_C up_distance Switch-Event vs Profit-Protection Authority Split v1

## 1. Purpose

Persist the Owner-authorized **identity split** of switch-event `up_distance`
vs profit-protection distance under:

```text
OWNER_GO=PEAK_TRADE_OWNER_GO_MODEL_C_DUAL_USE_SPLIT_V1
OWNER_GO_STATUS=GRANTED_CONFIRMED
AUTHORIZED_WORKPACKAGE=
  MODEL_C_UP_DISTANCE_SWITCH_EVENT_VS_PROFIT_PROTECTION_AUTHORITY_SPLIT
BOUND_ORIGIN_MAIN_SHA=e9bd94965a3f6e9bdc29b76b1e0c1cfbe3a4b594
```

```text
DOCUMENT_CLASS=DOCS_AND_WIRING_IDENTITY_SPLIT
PARALLEL_SSOT_CREATED=false
NUMERIC_BEHAVIOR_CHANGE=false
SWITCH_EVENT_UP_DISTANCE_EFFECTIVE_VALUE=200.0
PROFIT_PROTECTION_DISTANCE_EFFECTIVE_VALUE=200.0
MODEL_C_DERIVATION_RUNTIME_BINDING_AUTHORIZED=false
MODEL_C_FREEZE_EXCEPTION_AUTHORIZED=false
RESEARCH_DISTANCE_REWRITE_AUTHORIZED=false
HYSTERESIS_MULTIPLIER_RUNTIME_BINDING_AUTHORIZED=false
PR_6270_MODIFICATION_AUTHORIZED=false
LIVE_MUTATION_AUTHORIZED=false
LIVE_AUTHORIZED=false
CORE_LOGIC_CHANGE=false
MODEL_B_REMAINS_PRODUCTIVE_BASELINE=true
EFFECTIVE_NUMERIC_VALUES_UNCHANGED=true
```

This split is the mandatory blocker recorded by
[MODEL_C_DYNAMIC_SCOPE_DERIVED_SWITCH_EVENT_THRESHOLDS_CONTRACT_V1.md](MODEL_C_DYNAMIC_SCOPE_DERIVED_SWITCH_EVENT_THRESHOLDS_CONTRACT_V1.md)
and OQ-C5 in
[MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md](MODEL_C_FORMULA_AND_POLICY_ADJUDICATION_V1.md).

It does **not** bind MODEL_C derivation, grant a freeze exception, rewrite
research distances, or change Exit numerics.

## 2. Authority after this slice

| Role | Owner | Effective value |
|------|-------|-----------------|
| Switch-event `up_distance` | Cap 6.3 TOML / `CANONICAL_UP_DISTANCE` | `200.0` |
| Profit-protection distance | Cap 6.5 `FROZEN_PROFIT_PROTECTION_DISTANCE` | `200.0` |

```text
PROFIT_PROTECTION_DISTANCE_REUSES_SWITCH_EVENT_UP_DISTANCE=false
PRODUCTIVE_HOST_PASSES=FROZEN_PROFIT_PROTECTION_DISTANCE
PRODUCTIVE_HOST_MUST_NOT_PASS=decision_cfg.up_distance
```

```text
NUMERIC_VALUE != SEMANTIC_AUTHORITY
VALUE_PARITY_CURRENTLY_REQUIRED=true
SHARED_AUTHORITY_REQUIRED=false
SHARED_NUMERIC_AUTHORITY_ALLOWED=false
SWITCH_EVENT_DISTANCE_AUTHORITY=CAP_6_3_CANONICAL_UP_DISTANCE
PROFIT_PROTECTION_DISTANCE_AUTHORITY=CAP_6_5_FROZEN_PROFIT_PROTECTION_DISTANCE
SWITCH_EVENT_UP_DISTANCE=200.0
PROFIT_PROTECTION_DISTANCE=200.0
IDENTICAL_NUMERIC_VALUE_IS_MIGRATION_INVARIANT_NOT_PERMANENT_COUPLING=true
```

Same number does **not** mean same authority. The identical current value
`200.0` is a **migration invariant** of this identity split, not a durable
coupling requirement. Identity aliasing (`FROZEN_PROFIT_PROTECTION_DISTANCE =
float(CANONICAL_UP_DISTANCE)` or productive
`profit_protection_distance=decision_cfg.up_distance`) is **forbidden**.

## 3. Productive wiring

Hosts:

- [`src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/decision_economics_cycle_bridge_v1.py`](../../../src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/decision_economics_cycle_bridge_v1.py)
- [`src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2/hardening_cycle_bridge_v2.py`](../../../src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2/hardening_cycle_bridge_v2.py)

Owner constant:

- [`src/ops/exit_policy_producer_binding_v1/constants_v1.py`](../../../src/ops/exit_policy_producer_binding_v1/constants_v1.py)

Cap 6.3 TOML is **not** extended. Profit-protection follows the Cap 6.5
binding-constant pattern already used by `CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS`.

Historical Cap 6.5 evidence JSON may retain the prior reuse wording.

## 4. Not authorized here

- MODEL_C `derive_scope_event_distances_v1` runtime bind
- Cap 6.2 / 6.3 / 6.5 freeze exception
- Research BPS rewrite
- `hysteresis_multiplier` runtime
- PR `#6270`
- Live / orders / credentials

## 5. Next stop

```text
NEXT_STOP=AWAIT_OWNER_GO_MODEL_C_FREEZE_EXCEPTION
MARKER: MODEL_C_DUAL_USE_SPLIT_IMPLEMENTED=true
MARKER: NUMERIC_BEHAVIOR_CHANGE=false
MARKER: MODEL_B_REMAINS_PRODUCTIVE_BASELINE
MARKER: DERIVATION_SEAM_UNBOUND
MARKER: LIVE_AUTHORIZED=false
```
