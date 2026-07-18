# Order Reachability

| Question | Answer |
|----------|--------|
| Can bypass set canonical `ENTRY_SIDE` LONG&#47;SHORT? | **false** |
| Can bypass feed `resolve_agreement_bound_directional_cycle_v1`? | **false** |
| Can bypass call `build_canonical_order_intent_v1`? | **false** |
| Can bypass reach live execution? | **false** (`LIVE_AUTHORIZED=false`) |
| Can classic path simulate paper fills locally? | yes (research `ExecutionPipeline`&#47;Paper) — **not** canonical order-intent authority |

Under OPTION_D, Bollinger Integrated Entry with `entry_side=NONE` remains non-executable on the agreement-bound path.
