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

## Probability admission at the existing owner — 2026-11-22

At baseline `01008238316f0742dca0363070f373e8dae74aa5`, forecast minting and
consumer revalidation already use the same probabilistic payload grammar.
Directional admission only checked the total; threshold-event admission used
two comparisons. Negative components could cancel values above one; NaN could
pass both gates. Boolean values were converted to numbers. Original decimal
text just outside a bound could round onto zero or one during float conversion.
These are admission gaps in existing connections, not missing new producers.

The shared grammar now requires each p_up/p_down/p_flat and p_event value to be
a finite numeric int, float or decimal string in the inclusive interval [0, 1].
Booleans are not probabilities. Decimal comparison checks the original numeric
text before conversion; the existing left-to-right float sum and absolute
directional sum tolerance of 1e-9 remain. Original payload values, types, digest
canonicalization and forecast IDs are retained for admitted inputs. Validation
does not clamp, renormalize, rewrite historical records or invent missing data.
Existing field-presence and unsupported-kind checks remain in their owners.

Native minting, cold forecast validation, calibration, the attribution query,
MI learning composition and ingest inherit this gate. Invalid inputs raise
DdoValidationError before a successful consumer result or new learning write.
The corrected original-source test baseline has 44 unblocked contradictions
and 21 already-passing controls. Four fully native original-source probes
reached synthetic learning-store readback; directional calibration included
scores 1.1 and NaN. No mocked validator was needed to establish those paths.
The earlier diagnostic test attempt had fixture/call-signature faults and is
retained separately; it is not the corrected baseline or a passing proof.

Verification: `tests/learning/test_forecast_probability_semantic_admission_v1.py`.
Twelve complete native valid packets and nine serialized synthetic learning
records captured before the source change remain byte-identical afterward,
including JSON cold validation, absent outcomes, insufficient support, zero
and one, decimal strings, signed zero and the original sum tolerance.
All verification uses synthetic data, temporary stores and denied networking.

This checks dimensionless probability admission, not forecast accuracy or
calibration quality. Threshold units, mean/std-return and behavior-label
semantics are not established by this gate. The existing directional owner
computes 1 minus the realized-class probability under its BRIER_SCORE_V1 label;
its mathematical interpretation remains a separate open issue, without a
silent numerical or historical-schema change here. Existing downstream float
precision, identity scope, missing-reference limits and evidence-only authority
remain. No account PnL, model update, productive apply or operational readiness
is inferred. Local construction history remains limited to the frozen import.

## Resolved legacy directional score semantics — 2026-11-22

The open method-interpretation question above is resolved for the existing V1
contract: **BRIER_SCORE_V1 is a historical wire identifier for the linear
per-event loss 1 - p(realized_class), not a quadratic Brier score.** Retain the
token, calculation and sealed identities; do not silently redefine old or new
V1 records as a different numerical method. The source constant and scoring
function now state this explicitly. No missing numerical handoff was found at
the examined consumers and no new route or metric is introduced.

The retained D03 owner request of 26 September, sections D and G, requires
forecast-kind-appropriate evaluation, backward compatibility and separation
from the opaque productive economic label. It specifies no Brier formula or
normalization. The original implementation at PR #6847, merge
`32171b35e631cab767dca4f5fcd99b8a837caf23`, already uses the same token and 1-p
formula. Its retained full source has Git blob
`b13929af6f2fd78154d58cab8b61e27459ed2c62` and SHA256
`1fa265f3b5fe1eaea00f2f8ea4dd1c460017e822c26380959c1c480a22812ca3`.
The retained original request, source and revision metadata are linked in the
[D03 origin investigation](../evidence/mi_independent_market_observation_history_2026_11_06/README.md).
The attached blueprint PDF is absent at its recorded local path; its complete
contents are not independently reconstructed here. The later November
[consumer assessment](../evidence/self_learning_loop_a_causal_consumer_assessment_v1_2026_11_04/README.md)
reported the same mismatch without changing it. Its historical results are not
substituted for the current native tests at baseline
`83287d84c94ddbf413eeed1d81334e3954d88ab9`.

The V1 value is dimensionless in [0, 1] for admitted probabilities: zero when
the supplied realized class had probability one, one when it had probability
zero. Lower means more probability assigned to that supplied class. The caller
supplies UP/DOWN/FLAT; a joined outcome reference alone does not derive or
authenticate that label. The scalar ignores how probability is split between
the other two classes, although the full forecast identity still binds them.

For contrast only, the unscaled multiclass quadratic expression is the sum of
(p_class - one_hot_outcome_class) squared over all three classes. Forecasts
(0.5, 0.3, 0.2) and (0.5, 0.4, 0.1) with supplied UP both return V1 loss 0.5;
that quadratic expression gives 0.38 and 0.42. More importantly, on an exact
ten-case synthetic population with six UP, three DOWN and one FLAT, truthful
(0.6, 0.3, 0.1) has mean V1 loss 0.54, whereas always reporting (1, 0, 0) lowers
it to 0.40. Thus minimizing this linear loss does not elicit truthful
probabilities: it is not a proper probability-scoring objective. Calling its
average calibration quality would be incorrect. This comparison does not
install a particular quadratic normalization or a new scoring method.

Current consumer meaning is bounded and verified:

- CalibrationEvidence and the existing full triad store retain the numeric
  result, method token, forecast/outcome references, IDs and digests. Cold read
  and repeated append preserve the original bytes.
- The MI learning record and research projection carry references, method
  metadata where present and evidence disposition. Their reference transport
  does not erase the full triad's numeric result or train a model.
- With a fixed original M4 request, controlled supplied UP/DOWN/FLAT labels
  produce 0.5/0.7/0.8 and distinct lineage. The complete M4 chain after removal
  of its two explicit MI attachments is identical. This is a local consumer
  intervention, not a claim about every possible external or dynamic reader.
- The actual measured-return numeric reader rejects these directional triads
  with DURABLE_RETURN_ERROR_REQUIRED. The OLS label/error path uses
  RETURN_ERROR_V1, not the misleading directional token. Existing GVEF MI
  evaluation checks bundle digests/invariants; it does not calculate a Brier
  score, probabilistic calibration quality or model improvement.

Verification: `tests/learning/test_legacy_directional_score_semantics_v1.py`.
All 28 new semantic probes already pass on the unchanged original numerical
owner: this is a clarified historical contract and stronger regression proof,
not a repaired numerical runtime defect. Three complete native
calibration/triad/learning/export/M4 packets and six serialized store files are
captured before the source comments and compared afterward. Three separately
retained historical calibration records remain natively valid and unchanged.
Tests use synthetic inputs, temporary stores and denied networking. Existing
probability admission, missing-outcome/insufficient-support behavior,
financial/Core boundaries and authority remain unchanged. No operational or
research session is started. A future true quadratic metric requires its own
explicit method definition, normalization and compatibility decision; it must
not reuse BRIER_SCORE_V1 to give existing evidence a different meaning.
