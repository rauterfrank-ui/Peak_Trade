# Final CURRENT Authority Closure — Limit/Equity N=1 Bind + Layered Safety (v1)

Navigation-only derived spec. Machine contract:
`config/governance/final_current_authority_closure_limit_equity_and_layered_safety_ratification_v1.json`.

Owner-GO `OWNER_GO_FINAL_CURRENT_AUTHORITY_CLOSURE_V1` (one-shot; **CONSUMED**)
ratifies existing productive semantics only. No runtime behavior change.

## Limit / equity

Four CRS input dimensions remain **semantically and mathematically distinct**
in `src/governance/capital_risk_sizing_v1.py`. This ratification does **not**
merge field names or collapse CRS math.

Ratified productive N=1 binding (enter-live-29p path only):

- `scope_capital_limit` := typed 29P available-for-sizing account equity
- `per_trade_risk_limit` := typed 29P available-for-sizing account equity
- `total_capital_limit` := typed 29P available-for-sizing account equity
- `daily_loss_remaining_budget` := typed 29P available-for-sizing account equity

Source authority: `ops.governed_productive_account_equity_authority_producer_v1`
via `current_productive_mv2_capital_context_rebind_v1`.

Historical isolated fixture literals (25/500/10000 family) remain
non-CURRENT and must not be reactivated as productive fallbacks.

## Layered safety

Ratified CURRENT separation (no umbrella runtime owner):

| Domain | Authority |
| --- | --- |
| Decision | MASTER_V2_PLUS_DOUBLE_PLAY |
| Replay safety veto | `safety_kernel_offline_replay_binding_adapter_v0` |
| Durable kill switch | `risk_gate` / `durable_filegate_join_v1` |
| KILL_ALL | Double Play SideState/composition |
| Flatten | `current_productive_exact_object_flatten_plan_v1` |

Cap 11.5 is not productive safety SSOT and is not activated by this slice.
