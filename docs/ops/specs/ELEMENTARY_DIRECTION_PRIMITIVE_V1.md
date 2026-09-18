---
docs_token: DOCS_TOKEN_ELEMENTARY_DIRECTION_PRIMITIVE_V1
status: active
scope: additive pure C1 mark-to-mark identity; non-authorizing; no runtime activation
last_updated: 2026-09-18
---

# Elementary Direction Primitive V1

## 1. Purpose

Add the smallest typed identity for consecutive C1 mark movement of the bound
selected Future:

`previous DISTINCT accepted C1 mark` → `current bound markPx` → `{BULL, BEAR, NEUTRAL}`.

This slice does **not** activate Dynamic Scope, Double Play, Entry/Exit, C3,
Survival, Suitability, risk, intent, venue POST, Testnet, or Live.

```text
AUTHORITY_EFFECT=NONE
RUNTIME_EFFECT=NONE
ORDER_EFFECT=NONE
DOUBLE_PLAY_REWIRED=false
SWITCH_POLICY_TOUCHED=false
```

## 2. Owner

| Role | Surface |
| --- | --- |
| Pure evaluator | `src&#47;trading&#47;market_state&#47;elementary_direction_v1.py` |
| C1 predecessor | `ObservationAcceptanceResultV1.state_before.last_accepted_observation_identity.mark_price` |
| Current mark | bound selected-Future OKX `markPx` / C1 candidate `mark_price` |
| Passive cycle join | `src&#47;ops&#47;full_core_live_path_composition_root_v1&#47;current_productive_master_v2_runtime_cycle_v1.py` evidence field only |

## 3. Semantics

Strict signum. No tick, percent, deadband, distance, confirmation epoch,
candle return, trailing anchor, or volatility.

| previous | current | identity |
| --- | --- | --- |
| `None` (first accepted observation) | valid mark | `NEUTRAL` |
| valid mark | `current > previous` | `BULL` |
| valid mark | `current < previous` | `BEAR` |
| valid mark | `current == previous` | `NEUTRAL` |

Invalid numerics follow C1 mark conventions (`is_finite_number`, strictly `> 0`,
bools rejected) and are **rejected**, not normalized to `NEUTRAL`.

Instrument mismatch against the bound selected Future is **rejected**, not
normalized.

C1 fail-closed classifications (`OUT_OF_ORDER`, `IDENTITY_CONFLICT`,
`INVALID_MARK`, `INVALID_EVENT_TIME`) are **not comparable** and reject.

Predecessor is always `state_before`, never `state_after`, never candle close,
never trailing anchor, never volatility mark history.

## 4. Non-authority

The primitive is identity only. It must not be consumed by:

- ScopeEvent / SideState
- C3 DirectionalAssessment
- Double Play composition
- EntryExitPolicy
- capital risk sizing
- order intent
- venue plan / POST

Numeric `+1` / `-1` units are not encoded. `BULL` / `BEAR` / `NEUTRAL` are the
identity.

## 5. Tests

- `tests&#47;trading&#47;market_state&#47;test_elementary_direction_v1.py`
- `tests&#47;ops&#47;test_elementary_direction_passive_cycle_join_v1.py`
