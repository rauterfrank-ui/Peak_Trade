# OBL_B05 ENTRY_EXIT Optional Side-Carrier Contract v1

---
docs_token: DOCS_TOKEN_OBL_B05_ENTRY_EXIT_OPTIONAL_SIDE_CARRIER_CONTRACT_V1
STATUS: CONTRACT_EXTENSION_AVAILABLE
scope: technical contract extension, research/MV2 wiring transport, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
BOLLINGER_SIDE_ACTIVATED: false
SEMANTIC_PRODUCER_DECISION_STILL_REQUIRED: true
---

> **Non-authorizing:** Defines an optional explicit `entry_side` carrier for
> `ENTRY_EXIT_EVENT_V1` and transports it through agreement material / resolve /
> price_path projection. Does **not** activate Bollinger (or any producer) to
> emit LONG/SHORT. Does **not** authorize ENTER, promotion, runtime, testnet,
> orders, capital, or live.

## A. Verdict

| Feld | Wert |
|---|---|
| `SLICE_ID` | `OBL_B05_ENTRY_EXIT_OPTIONAL_SIDE_CARRIER_CONTRACT_V1` |
| `BASE_SHA` | `0473c8bad1b0b82840ec038fc0f84ec92a396cff` |
| `CONTRACT_EXTENSION_AVAILABLE` | `true` |
| `LEGACY_BEHAVIOR_UNCHANGED` | `true` |
| `BOLLINGER_SIDE_ACTIVATED` | `false` |
| `SEMANTIC_PRODUCER_DECISION_STILL_REQUIRED` | `true` |
| `LIVE_AUTHORIZED` | `false` |
| `ORDERS_ENABLED` | `false` |
| `FIRST_FALSE_PREDICATE_ID` | `FF_DA_FLAT_PATH_ENTRY_EXIT_NO_SIDE_CARRIER_V1` |
| `PANEL_ENTRY_BASELINE` | `185` ENTRY bars remain flat-path fail-closed while producers emit `NONE` |

## B. Semantics

- `ENTRY` remains an **event**; it does **not** mean LONG.
- `cycle_signal_value=+1` under `ENTRY_EXIT_EVENT_V1` remains ENTRY only.
- New carrier: `entry_side ∈ {LONG, SHORT, NONE}` on
  `StrategySuitabilityAgreementMaterialV1`.
- Default for all existing producers (adapter): `NONE`.
- `NONE` / missing:
  - `resolve_agreement_bound_directional_cycle_v1` → `None`
  - `price_path` → `(mark, mark)`
  - DA remains blocked as today (`FF_DA_FLAT_PATH_ENTRY_EXIT_NO_SIDE_CARRIER_V1`)
- Explicit `LONG` → direction `+1` → relative positive impulse.
- Explicit `SHORT` → direction `-1` → relative negative impulse.
- `EXIT` never invents a side (no exit-side contract in this slice).
- Forbidden derivations: band-cross, strategy name, `supported_sides`,
  Suitability `ENTRY→AGREE(LONG)`, signal sign as side authority.

## C. Owners (reuse-before-new)

| Surface | Owner |
|---|---|
| Material / schema / serialize | `src&#47;trading&#47;master_v2&#47;strategy_suitability_agreement_material_v1.py` |
| Adapter default `NONE` | `src&#47;backtest&#47;strategy_signal_suitability_agreement_adapter_v1.py` |
| Resolve + price_path | `src&#47;backtest&#47;mv2_research_wiring_v1.py` |
| Contract tests | `tests&#47;backtest&#47;test_entry_exit_optional_side_carrier_contract_v1.py` |
| Parent Decision D | `docs&#47;governance&#47;STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_DECISION_D_V1.md` |

## D. Producer matrix (current)

| producer | encoding | explicit `entry_side`? | resolved direction | fail-closed behavior |
|---|---|---|---|---|
| `bollinger_bands` | `ENTRY_EXIT_EVENT_V1` | no (`NONE`) | `None` | flat `price_path`; DA block |
| `macd` | `ENTRY_EXIT_EVENT_V1` | no (`NONE`) | `None` | flat `price_path`; DA block |
| `momentum_1h` | `ENTRY_EXIT_EVENT_V1` | no (`NONE`) | `None` | flat `price_path`; DA block |
| `trend_following` | `ENTRY_EXIT_EVENT_V1` | no (`NONE`) | `None` | flat `price_path`; DA block |
| `mean_reversion` | `ENTRY_EXIT_EVENT_V1` | no (`NONE`) | `None` | flat `price_path`; DA block |
| `my_strategy` | `ENTRY_EXIT_EVENT_V1` | no (`NONE`) | `None` | flat `price_path`; DA block |
| `ecm_cycle` | `ENTRY_EXIT_EVENT_V1` | no (`NONE`) | `None` | flat `price_path`; DA block |
| `rsi_reversion` (ref) | `POSITIONAL_LS_STATE_V1` | n/a (`NONE`) | from `cycle_signal_value` | unchanged |
| `ma_crossover` (ref) | `POSITIONAL_LONG01_STATE_V1` | n/a (`NONE`) | from `cycle_signal_value` | unchanged |

## E. Before / after

| Aspect | Before (`0473c8ba`) | After (this slice) |
|---|---|---|
| Material field `entry_side` | absent | present; default `NONE` |
| Adapter Bollinger ENTRY | NEUTRAL / ENTRY | NEUTRAL / ENTRY / `entry_side=NONE` |
| `resolve` ENTRY_EXIT | always `None` | `None` unless explicit LONG/SHORT |
| `price_path` legacy ENTRY | `(mark, mark)` | `(mark, mark)` unchanged |
| Bollinger panel first-false | `FF_DA_FLAT_PATH_ENTRY_EXIT_NO_SIDE_CARRIER_V1` ×185 | unchanged (producer still `NONE`) |
| ENTER / live / orders | forbidden | still forbidden |

## F. Forbidden / next GO

- Bollinger auto-LONG assignment
- Suitability ENTRY→LONG as DA authority
- Signal-sign as side
- `supported_sides` as signal authority
- mark+5 / absolute impulses
- Confirmation / composition / strategy reclassification changes
- Runtime / scheduler / testnet / orders / capital / live

Next semantic producer decision (separate Operator-GO) is required before any
ENTRY_EXIT producer may emit `entry_side=LONG|SHORT`.
