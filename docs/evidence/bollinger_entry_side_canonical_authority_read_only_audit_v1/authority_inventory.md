# Authority Inventory

Classification key: `CANONICAL_STATE_AUTHORITY` | `STRATEGY_SIGNAL_PRODUCER` | `SIDE_PROJECTION` | `ORDER_INTENT_CONSUMER` | `TEST_FIXTURE` | `SCENARIO_ONLY` | `LEGACY_OR_COMPATIBILITY` | `COMPETING_AUTHORITY` | `UNREACHABLE_OR_DEAD` | `UNKNOWN`

| File | Symbol | Class | Productive | Invents Direction? | Fail-closed | Second-truth risk |
|------|--------|-------|------------|--------------------|-------------|-------------------|
| `src&#47;strategies&#47;bollinger_event_semantic_contract_v1.py` | `classify_bollinger_raw_signal_event_v1` | STRATEGY_SIGNAL_PRODUCER | yes | no (`NONE`) | yes | none |
| `src&#47;strategies&#47;bollinger.py` | `BollingerBandsStrategy.generate_signals` | STRATEGY_SIGNAL_PRODUCER | yes | no side; raw `{+1,-1,0}` | partial | low if misread as LONG |
| `src&#47;backtest&#47;strategy_signal_suitability_agreement_adapter_v1.py` | `_bollinger_event_only_side_agreement_and_aux` | SIDE_PROJECTION | yes | no | yes | none |
| same | `_resolve_entry_side_carrier_v1` | SIDE_PROJECTION | yes | Bollinger always `NONE`; TF may LONG | yes | low if generic +1→LONG assumed |
| same | `normalize_strategy_signal_to_suitability_agreement_material_v1` | SIDE_PROJECTION | yes | Bollinger guard `entry_side` must be NONE | yes | none |
| `config&#47;governance&#47;obl_b07_bollinger_event_only_semantic_contract_v1.json` | SSOT | CANONICAL_STATE_AUTHORITY (policy) | config | n&#47;a | n&#47;a | none |
| `src&#47;trading&#47;master_v2&#47;strategy_suitability_agreement_material_v1.py` | `StrategyEntrySideCarrierV1` | SIDE_PROJECTION (type) | yes | no | yes | low if forged deserialize |
| `src&#47;backtest&#47;mv2_research_wiring_v1.py` | `resolve_agreement_bound_directional_cycle_v1` | SIDE_PROJECTION | yes | no invent; needs carrier | yes (`None` flat) | none for Bollinger |
| `src&#47;trading&#47;master_v2&#47;double_play_state.py` | `transition_state` | CANONICAL_STATE_AUTHORITY | yes | yes — sole Bull&#47;Bear SideState | yes | none if sole held |
| same | `RuntimeScopeState` | CANONICAL_STATE_AUTHORITY | yes | scope policy only | yes | none |
| `src&#47;trading&#47;master_v2&#47;canonical_scope_initialization_v1.py` | `CanonicalScopeSnapshotV1` | CANONICAL_STATE_AUTHORITY | yes | no SideState invent | yes | none |
| `src&#47;trading&#47;master_v2&#47;canonical_market_context_v1.py` | `CanonicalMarketContextV1` | CANONICAL_STATE_AUTHORITY | yes | no trading side | yes | none |
| `src&#47;trading&#47;master_v2&#47;double_play_composition_matrix_v1.py` | `evaluate_double_play_composition_matrix_v1` | CANONICAL_STATE_AUTHORITY | yes | selects composition side; conflict→NONE | yes | none (not strategy-side SSOT) |
| `src&#47;trading&#47;master_v2&#47;double_play_composition.py` | `compose_double_play_decision` | LEGACY_OR_COMPATIBILITY | residual | eligibility; not SideState SSOT | yes (live false) | low if misread as switch |
| `src&#47;trading&#47;master_v2&#47;suitability_binding_v1.py` | `derive_effective_strategy_side_agreement_v1` | ORDER_INTENT_CONSUMER adjacent | yes | ENTRY agrees only vs LONG DA; ignores `entry_side` | partial | MEDIUM asymmetry (not carrier) |
| `src&#47;trading&#47;master_v2&#47;integrated_offline_trading_logic_replay_v1.py` | `run_integrated_offline_trading_logic_replay_v1` | ORDER_INTENT_CONSUMER &#47; orchestrator | yes offline | no invent | yes | none |
| `src&#47;trading&#47;master_v2&#47;canonical_core_runtime_integration_bridge_v0.py` | bridge | BOUND_NOT_ACTIVATED | bound, not live | `authority_effect=NONE` | yes | none |
| `src&#47;governance&#47;canonical_order_intent_v1.py` | `build_canonical_order_intent_v1` | ORDER_INTENT_CONSUMER | gated offline | consumes selected side | yes | none |
| `src&#47;backtest&#47;strategy_signal_binding_v1.py` | binding owner | STRATEGY_SIGNAL_PRODUCER binding | yes | no side invent | yes | none |
| `src&#47;backtest&#47;engine.py` | `BacktestEngine.run_realistic` | LEGACY_OR_COMPATIBILITY | yes classic | **yes** `signal==1`→LONG | n&#47;a | HIGH if treated as Integrated |
| `src&#47;trading&#47;master_v2&#47;double_play_sole_authority_quarantine_v1.py` | quarantine | CANONICAL_STATE_AUTHORITY | policy | documents sole owners | yes | none |
| OBL_B05&#47;B07 tests &#47; fixtures | — | TEST_FIXTURE | tests | no | — | none |

## Counts

```text
COMPETING_AUTHORITY_COUNT=0
CONFIRMED_BYPASS_COUNT=1
RESIDUAL_ASYMMETRY_NOT_COUNTED_AS_COMPETING=1
```

Residual asymmetry: Suitability ENTRY_EXIT ENTRY agrees only with LONG DA without checking `entry_side` — demotion bias, not SideState&#47;carrier emission.
