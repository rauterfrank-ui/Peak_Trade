# OBL_B07 Bollinger EVENT_ONLY Semantic Contract v1

---
docs_token: DOCS_TOKEN_OBL_B07_BOLLINGER_EVENT_ONLY_SEMANTIC_CONTRACT_V1
STATUS: BOLLINGER_EVENT_ONLY_RATIFIED
OPERATOR_OPTION: OPTION_EVENT_ONLY
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
BOLLINGER_EVENT_ONLY_RATIFIED: true
LONG_ONLY_AUTHORIZED: false
SHORT_ENTRY_AUTHORIZED: false
SYMMETRIC_SHORT_GEOMETRY_AUTHORIZED: false
STRATEGY_DIRECTION: NONE
ENTRY_SIDE: NONE
CLASSIC_LONG_IS_CANONICAL: false
PRODUCTIVE_SIDE_ACTIVATED: false
---

> Operator-GO ``OPTION_EVENT_ONLY``. Bollinger remains a direction-neutral
> Entry&#47;Exit event producer. No LONG&#47;SHORT side emission.

## A. Decision

| Field | Value |
|---|---|
| `OPERATOR_OPTION` | `OPTION_EVENT_ONLY` |
| `LONG_ONLY` | not authorized |
| `SYMMETRIC_SHORT_GEOMETRY` | not authorized |
| `STRATEGY_DIRECTION` | `NONE` (unratified) |
| `ENTRY_SIDE` | `NONE` |
| Later direction ratification | separate Operator-GO + Strategy-Design slice |

## B. Canonical mapping

| Raw Signal | Bollinger Event | Direction | Entry Side |
|---|---|---|---|
| `+1` | `ENTRY_EVENT` | `NONE` | `NONE` |
| `-1` | `EXIT_EVENT` | `NONE` | `NONE` |
| `0` | `FLAT_NO_EVENT` | `NONE` | `NONE` |
| missing&#47;invalid | `UNKNOWN_FAIL_CLOSED` | `NONE` | `NONE` |

## C. Owners

| Surface | Owner |
|---|---|
| Event contract | `src&#47;strategies&#47;bollinger_event_semantic_contract_v1.py` |
| Adapter binding | `src&#47;backtest&#47;strategy_signal_suitability_agreement_adapter_v1.py` |
| Raw producer | `src&#47;strategies&#47;bollinger.py` |
| SSOT JSON | `config&#47;governance&#47;obl_b07_bollinger_event_only_semantic_contract_v1.json` |
| System state | Master V2 &#47; Double Play (unchanged) |

## D. Classic boundary

Classic `BacktestEngine` may treat `+1` as LONG exposure historically.
That behavior is **not** the canonical Bollinger Strategy-Intent contract and
must not propagate into Integrated&#47;MV2 as entry-side authority.

## E. Safety

- `LIVE_AUTHORIZED=false`
- `ORDERS_ENABLED=false`
- No generic sign heuristic
- No cycle &#47; Bull-Bear &#47; position direction inference
