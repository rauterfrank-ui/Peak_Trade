# HARDENING_V2_REQUIRED_WINDOW_COMPLETE_DECOUPLE_FROM_FEATURES_OK_V1

## Root cause (forensic predecessor)

Hardening-v2 wired:

`required_window_complete = features.warmup_complete and features.ok`

When the feature window was complete but regime stayed `unclassified`
(`REGIME_UNCLASSIFIED_FAIL_CLOSED`), Master V2 emitted
`required_window_incomplete` as a false positive.

## Repair (this capability)

Hardening-v2 now matches Bridge-v1:

`required_window_complete = features.warmup_complete`

via `derive_required_window_complete_v2(warmup_complete=..., features_ok=...)`
where `features_ok` is intentionally unused.

## Preserved separately

- `features.ok`
- `regime_id=unclassified`
- `REGIME_UNCLASSIFIED_FAIL_CLOSED`
- typed-volatility presence gate
- safety / risk / sizing / intent semantics
- `FEATURE_WINDOW_MIN` / `PRICE_PATH_MAX_LEN` / regime thresholds

## Diagnostic telemetry (non-authoritative)

Cycle traces may include:

- `mid_prices_len`
- `feature_window_min`
- `required_window_complete`
- `required_window_complete_inputs.warmup_complete`
- `required_window_complete_inputs.features_ok`
- `regime_id`
- `feature_blockers`

These fields have no decision, config, persistence, or timing effect.
