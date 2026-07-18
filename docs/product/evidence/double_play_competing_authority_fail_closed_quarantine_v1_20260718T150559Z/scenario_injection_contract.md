# Scenario Scope Event Injection Contract

## Rules

1. `OfflineDoublePlayScenarioReplayInputV0.allow_test_scope_event_injection` defaults to **`false`**.
2. Without the flag, validation fails with
   `scenario_scope_event_injection_requires_explicit_test_harness_flag`.
3. With the flag, every tick must set `scope_event_provenance="TEST_INJECTION"`.
4. Unmarked provenance is fail-closed rejected.
5. Factory: `make_offline_scenario_replay_input_for_tests_v0` marks ticks and sets the flag.
6. Integrated / Backtest / Runtime wiring must not accept unmarked external ScopeEvents as SideState authority (they use the generator → mapper → `transition_state` chain).

## Status

`SCENARIO_SCOPE_EVENT_STATUS=TEST_ONLY_GUARDED`
EOF