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

## Optional decision-attribution query binding — 2026-11-22

At baseline `9b6c06d00da43d988e1c76d8b72dc9395eabef07`, the reference query
already receives forecasts, attribution records and calibration receipts from
the offline orchestrator and Phase-14 composer. It validates forecast and
attribution independently, but copied calibration fields without native
revalidation or cross-reference checks. These connections are reused.

The query now reuses the original CalibrationEvidence validator. Contradictory
declared decision references and selected-instrument references reject instead
of one overriding the other. Calibration must belong to this MI domain; when a
forecast is supplied, its ID, n_bars, bar specification and forecast kind must
match. Native validation alone does not establish that cross-object join.

Phase 14 now passes its already available original outcome reference through
the optional `expected_actual_outcome_ref` argument. A calibration that declares
a different original measurement rejects, even for the same forecast and
horizon. The query does not acquire, recalculate or write an outcome. Missing
or UNKNOWN original outcomes do not invent a reference. A valid earlier
NOT_EVALUABLE calibration receipt with no outcome remains unbound, even if a
later Phase-14 evaluation has an actual measurement. Its missing field is not
backfilled. All three principal inputs remain optional.

The corrected original-source counterexample set has 35 cases: 21 incorrect
projections, including five through the actual Phase-14 caller, and 14 controls
that already pass. Seven probes use invalid native calibration records; other
probes use valid native records, controlled resealed declarations, original
opposite-return measurements or different source provenance. Recomputed IDs
and digests do not establish the join. Validation errors stop the query before
Phase-14 result publication; they are exceptions, not fabricated REJECTED result
objects. No learning or research writer is called by this query.

Verification: `tests/learning/test_mi_attribution_query_reference_binding_v1.py`.
Thirteen complete original query/Phase-14/ingest/readback packets and two full
synthetic ledger files remain byte-identical. Real JSON roundtrips, original
LearningState labels, cold read and idempotency remain supported. Verification
uses synthetic ETH decisions and original O4, measurement, forecast,
calibration, evaluation and ledger owners with network access denied.

Only explicitly supplied references are compared. Forecast IDs/digests retain
their existing scope, which does not bind their optional decision/instrument
reference fields; the new comparisons establish declared consistency, not
independent source authenticity or actual historical forecast consumption.
Without the optional expected outcome, the query has no independent original
measurement against which to compare a calibration. Instrument selection
receipts are not equated with canonical market instrument IDs. State/regime
references remain annotations. No additional time ordering is inferred from
the reference-only query. Existing numerical scoring, method labels, units,
horizons, ID/digest algorithms, evidence-only authority and storage owners stay
unchanged; this does not certify numerical calibration quality, account PnL,
decision quality, model learning, causal effects, automatic apply or productive
operation. Available local Git history starts with the frozen November import;
earlier construction history is not independently recovered here.
