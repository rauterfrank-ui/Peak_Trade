# Measured split values at the actual robustness consumer — 2026-11-04

Source pin `401421f72`. No production code or policy change. Actual previously
computed native-grid split measurements from Blueprint 80 are read back, joined
to all three exact result refs and their final EVALUATED point. The existing
canonical robustness owner and existing Failure Memory producer are invoked.
No simulator rerun, new metric engine, natural study or complete experiment claim.

## Unit boundary first

The split supplier computes zero-risk-free hourly Sharpe with sqrt(8760).
The target policy explicitly declares MEAN_OVER_SAMPLE_STD_NO_ANNUALIZATION.
The probe explicitly divides known source Sharpe by sqrt(8760), preserving the
raw source artifact and refs. This dimensional conversion is specific to the
inspected source/default zero risk-free contract, not a general implicit adapter
or a ratified production observation binding. Ratios within each three-split test
are unchanged by the common scaling. Computational sample counts are the existing
simulator's per-bar counts; no statistical independence claim.

The identity container still uses explicitly synthetic fixture scaffolding for
other dimensions. Native parameter names and actual dataset digest are supplied,
but the probe does not certify all feature/cost/risk/core identity dimensions or
reinterpret sensitivity point IDs as canonical experiment IDs. It demonstrates
numerical consumer behavior, not authenticated end-to-end experiment identity.

## Actual gate effects, including negative controls

Both measured cases have positive train/holdout and negative validation Sharpe.
TRAIN_VALIDATION_HOLDOUT returns PASS for this particular gate. The overall suite
is BLOCKED because other required evidence is absent. No overall robustness PASS
is claimed or inferred.

The existing _oos_gate checks sample size for all three splits and tests the
holdout/train Sharpe collapse ratio. Validation Sharpe is required, finite,
serialized and integrity-bound, but is not used in its collapse decision. Two
counterfactuals with validation +100 versus -100 both keep this gate PASS while
full evidence digests differ. Thus preservation, numerical use in a decision and
completeness are distinct claims. Existing implementation/policy is unchanged;
the initial request's intended validation decision role has not been established
by this scoped inspection, so this is not automatically classified as a bug.

Changing holdout to zero instead produces FAIL and actual REJECTED_OVERFIT Failure
Memory. Omitting validation yields BLOCKED_MISSING_CAPABILITY; nonfinite validation
is rejected. Missing/invalid fields are therefore not silently passed. These are
explicit counterfactual consumer controls, not additional market observations.

[Probe](probe.py), [summary and source artifact hashes](summary.json),
[receipt/checks](receipt.json). Actual complete records and counterfactuals are
stored for each slow window: [slow50 measured](slow50_actual.json),
[slow100 measured](slow100_actual.json),
[slow50 positive validation](slow50_positive_validation_control.json),
[slow50 negative validation](slow50_negative_validation_control.json),
[slow100 positive validation](slow100_positive_validation_control.json),
[slow100 negative validation](slow100_negative_validation_control.json),
[slow50 collapsed holdout](slow50_collapsed_holdout_control.json),
[slow100 collapsed holdout](slow100_collapsed_holdout_control.json),
[slow50 missing validation](slow50_missing_validation_control.json),
[slow100 missing validation](slow100_missing_validation_control.json),
[slow50 failure memory](slow50_collapsed_failure_records.json),
[slow100 failure memory](slow100_collapsed_failure_records.json).

Twelve bounded actual suite calls (ten finite cases and two rejected nonfinite
cases) and two failure-memory projections checked. Ruff/format checked; no new
pytest or whole-suite claim. Existing numerical-feedback adapter and split port
remain explicit offline capabilities, not an installed research loop. Original
source intent, full identity binding, natural usefulness, funding/CRS/economic
validity and next executed canonical candidate remain separate proof obligations.
U04/GAP-0370 and original ledger unchanged; no live/account/order/service activation.
