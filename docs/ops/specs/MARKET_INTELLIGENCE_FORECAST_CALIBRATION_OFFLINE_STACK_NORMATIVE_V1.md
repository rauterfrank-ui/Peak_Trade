# MARKET_INTELLIGENCE_FORECAST_CALIBRATION_OFFLINE_STACK_NORMATIVE_V1

```text
DOCUMENT_CLASS=IMPLEMENTATION_SPEC
AUTHORITY_EFFECT=NONE
RUNTIME_AUTHORIZATION_EFFECT=NONE
OWNER=learning.market_intelligence_forecast_calibration_offline_stack_v1
WORKPACKAGE_ID=MARKET_INTELLIGENCE_FORECAST_CALIBRATION_OFFLINE_STACK_V1
TRACK=TRACK_D_D03
```

Track D03 offline Market Intelligence evidence stack: governed `ForecastEvidence` and
`CalibrationEvidence` objects, explicit multi-horizon composition, deterministic offline
orchestrator, additive research projection, and optimization research intake.

Does not acquire market-fact ownership, alter N_BARS normative semantics, mutate productive
learning-state reducers, bind MV2/Double-Play, Cap 2.3, execution, or open promotion.

Policy ratification: `config/governance/market_intelligence_forecast_calibration_offline_stack_v1_policy_v1.json`.


## Explicit outcome end binding — 2026-11-04

Forecast/outcome JOINED requires matching n_bars/bar_spec and the explicit forecast
end to equal the last canonical N_BARS close as a UTC instant. Reuse the existing
forecast horizon derivation; do not substitute later evaluation knowledge time.
Mismatch raises FORECAST_OUTCOME_HORIZON_END_MISMATCH before calibration. This
preserves successful join objects and does not supply missing numeric label,
instrument/selection or measurement-start provenance.
[Tests and limits](../evidence/mi_forecast_outcome_end_binding_v1_2026_11_04/README.md).
