# Caller Graph — Before

```text
live_gates → evaluate_double_play → step_switch_gate  [COMPETING]
scenario loop → tick.scope_event → transition_state   [BYPASS generator]
backtest loop → capture feedback(LONG_*) → apply overwrite side_state [BYPASS]
integrated → RuntimeScopeState → generator → transition_state [CANONICAL]
```

Source audit: `read_only_double_play_authority_and_chop_binding_forensic_audit_v1_20260718T150045Z/caller_graph.md`
EOF