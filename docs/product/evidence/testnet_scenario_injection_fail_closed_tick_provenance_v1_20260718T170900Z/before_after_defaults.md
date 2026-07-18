# Before / After Defaults

| Surface | Before | After |
|---------|--------|-------|
| `OfflineDoublePlayScenarioReplayInputV0.allow_test_scope_event_injection` | `False` (already fail-closed) | `False` (unchanged) |
| `TestnetCompletionPathMarketInputV0.allow_test_scope_event_injection` | field absent (implicit via builder True) | `False` explicit field default |
| `build_replay_input_from_testnet_market_input` | hardcoded `True` | resolves market_input / exact-True kwarg; default False; requires validated tick provenance when True |
| Missing field / None / `"true"` / `"1"` | N/A or truthy risk | `resolve_allow_test_scope_event_injection` → False unless exact `True` |
| Typed tick provenance | string mark only (`TEST_INJECTION`) | `OfflineScenarioTickProvenanceV1` required when injection enabled |
