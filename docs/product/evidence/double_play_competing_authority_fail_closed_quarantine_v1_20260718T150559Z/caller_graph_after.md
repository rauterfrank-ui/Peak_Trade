# Caller Graph — After

```text
live_gates → evaluate_double_play  [PROJECTION_DIAGNOSTIC_ONLY; no step_switch_gate]
scenario loop → require allow_test_scope_event_injection + TEST_INJECTION provenance
              → tick.scope_event → transition_state   [TEST_ONLY]
backtest loop → capture feedback(NEUTRAL placeholders + position facts)
              → apply position/venue fields only       [OBSERVATION_ONLY]
integrated → RuntimeScopeState → generator → transition_state [CANONICAL SOLE]
```

Canonical Switch / Bull-Bear owner: `transition_state`.
EOF