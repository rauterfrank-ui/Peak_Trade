# MV2 Zero-Trade Per-Bar Decision Outcome Diagnostic v1

- diagnostic_id: `MV2_ZERO_TRADE_PER_BAR_DECISION_OUTCOME_DIAGNOSTIC_V1`
- go_token: `GO_MV2_ZERO_TRADE_PER_BAR_DECISION_OUTCOME_DIAGNOSTIC_V1`
- owner: `research.mv2_zero_trade_per_bar_decision_outcome_diagnostic_v1`
- authority_effect: `NONE`
- runtime_effect: `NONE`
- offline_only: `True`
- base_sha: `147f0bee154e5a2452553d51c9b254350ea10142`
- binding_id: `bollinger_bands_v2_full_canonical_system_economic_binding_v1`

## Eval instrument

- entry_bar_count: `1`
- dominant_first_failed_stage: `suitability`
- dominant_taxonomy_outcome: `BLOCKED_SUITABILITY`
- unobservable_entry_bar_count: `0`
- outcome_counts: `{"BLOCKED_COMPOSITION": 0, "BLOCKED_DIRECTIONAL_AGREEMENT": 0, "BLOCKED_ENTRY_EXIT": 0, "BLOCKED_OTHER": 0, "BLOCKED_SUITABILITY": 1, "BLOCKED_SURVIVAL": 0, "BLOCKED_WARMUP": 0, "ENTER_LONG": 0, "ENTER_SHORT": 0, "EXIT_OR_DEMOTION": 0, "HOLD": 0, "UNOBSERVABLE_FAIL_CLOSED": 0}`
- first_failed_stage_counts: `{"suitability": 1}`

## Panel (118 instruments)

- entry_bar_count: `185`
- dominant_first_failed_stage: `suitability`
- dominant_taxonomy_outcome: `BLOCKED_SUITABILITY`
- unobservable_entry_bar_count: `0`
- outcome_counts: `{"BLOCKED_COMPOSITION": 0, "BLOCKED_DIRECTIONAL_AGREEMENT": 1, "BLOCKED_ENTRY_EXIT": 0, "BLOCKED_OTHER": 0, "BLOCKED_SUITABILITY": 184, "BLOCKED_SURVIVAL": 0, "BLOCKED_WARMUP": 0, "ENTER_LONG": 0, "ENTER_SHORT": 0, "EXIT_OR_DEMOTION": 0, "HOLD": 0, "UNOBSERVABLE_FAIL_CLOSED": 0}`
- first_failed_stage_counts: `{"directional_agreement": 1, "suitability": 184}`

## Suspicion status (observational only)

- price_path_suspicion_status: `OBSERVED_SYNTHETIC_MARK_PLUS_5_ON_ALL_ENTRY_BARS`
- regime_id_suspicion_status: `OBSERVED_HARDCODED_TRENDING_ON_ALL_ENTRY_BARS`

## Semantics guards

- DECISION_SEMANTICS_CHANGED=false
- STRATEGY_SEMANTICS_CHANGED=false
- SIZING_SEMANTICS_CHANGED=false
- RUNTIME_CHANGED=false
