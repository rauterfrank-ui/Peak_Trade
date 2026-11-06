# Independent Market OLS Next Forecast V1

```text
DOCUMENT_CLASS=SUBORDINATE_IMPLEMENTATION_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
CAPABILITY=INDEPENDENT_MARKET_OLS_NEXT_FORECAST_V1
RUNTIME_AUTHORIZATION_EFFECT=NONE
TRADING_AUTHORITY=NONE
EXTERNAL_EFFECT_AUTHORIZED=false
MODEL_SCOPE=CALLER_INVOKED_OFFLINE_BASELINE
```

This additive baseline closes the bounded original-market-evidence → numerical model → next computed offline forecast seam. It does not replace the original measurement, calibration, DDO state, ranking, Scope or Double-Play owners.

The system goal is continuous Double-Play operation on each enabled instrument slot, eventually five enabled Futures slots, with relative movement-based replacement and learning/optimization supporting data quality, stability and the existing trading logic. The current N1/MaxPos=1 limit is an implementation/authorization stage, not this final target. This baseline neither activates five lanes nor changes position/rotation policy. Per-instrument models have market identity, not invented Decision/Lane identities. A model cannot silently cross to a replacement instrument.

## Evidence and feature contract

Training takes explicit original market-job locators. Each job must cold-read through the existing independent-market API. The existing owner then revalidates the original receipts/measurement and reproduces the original calibration; the full original triad must agree. Labels are the original realized LOG_RETURN, never a supplied label, simple return, PnL or opaque economic score. The original forecast error is retained for an explicitly described historical comparison.

Feature selectors explicitly name a source role, ordinal, fact kind, numeric field and unit. Values come only from original point-in-time-admitted context facts; no filling, scaling, derived feature invention or implicit ordinal selection is performed. Missing/ambiguous fields, bool/nonfinite values and unit changes reject. Feature order and names are part of model identity.

V1 is deliberately one market identity/source generation and one complete target-semantics signature: hourly MARK_PRICE, explicit N≥2, price unit/family, original endpoint price basis, source kind and freshness policy. Absolute horizon dates change per observation. N closes retain N−1 return intervals. There is no automatic pooling or migration across instruments, horizons or corrected source generations.

Every label's actual measurement evaluation and receipt availability must be at or before the explicit training cutoff. Rows are sorted by forecast creation and must be sequential and nonoverlapping: a row's label is available before the next row's context time. Duplicate original outcome IDs or duplicate samples reject, including the same outcome attached to multiple forecasts.

## Numerical baseline

An explicit policy supplies validation fraction, minimum training/validation counts, context age and training-evidence age. Validation requires at least two samples; training must support an intercept and all selected features. No hidden policy defaults are supplied.

The unchanged `fit_ols_lstsq` owner fits an intercept and coefficients on its chronological training prefix. The adapter requires full rank and its admissible numerical status. Existing diagnostic statuses do not become economic or promotion acceptance. The target is the original canonical logreturn; the old Bouchaud simple-return/bps wrapper is not reused.

The model predicts a conditional mean by intercept plus the weighted selected feature values. `std_return` is the population standard deviation of the held-out residuals, retained as a bounded empirical error-spread summary. No Gaussian assumption, calibrated probability, interval coverage or distribution-quality claim is introduced. Held-out RMSE/MAE, residual mean/std and the old supplied forecasts' errors remain explicit; the latter may come from different historical providers and are not a fixed independent economic baseline.

## Versioned model state and retries

The complete numeric state, policy, feature/target semantics, exact sample manifest, runtime/source bindings and parent identity are stored in an immutable, content-addressed model artifact. Its reference binds the actual coefficient bytes as well as the request. Parent updates require a strict cumulative prefix extension with new original evidence, identical feature/target policy and increasing versions. Batch refitting includes each original outcome once; no repeated-evidence weight update is performed.

Publication reuses the existing atomic complete-byte append primitive, with a cooperative per-request lease. The model is published before its request receipt. An identical retry uses the original artifact without fitting; a prepared artifact left before the receipt is recovered without refitting. Conflicting or multiple artifacts for one request block. This is local filesystem coordination, not distributed transaction or physical power-loss certification.

Cold model reading verifies immutable numeric bytes and lineage without a fitter, original data source or calibration computation. Evidence freshness is measured from the last actual label availability, so a later publication timestamp does not rejuvenate old training data.

## Actual next forecast

The provider loads that stored model, replays the existing admitted future context, enforces exact market/target/feature identity and time/freshness, numerically computes the payload, and mints the existing ForecastEvidence. It passes the complete stored model bytes and the actually computed payload to the unchanged market forecast freeze.

The generic freeze's own `model_inference_performed=false` remains accurate for that function. A separate immutable provider receipt records this caller's actual inference, exact feature values, model digest and frozen forecast binding. It is not a positive quality admission or a trading decision. Its cold read verifies saved artifacts without refitting or rerunning inference.

The provider derives its freeze attempt identity from the requested attempt and the exact computation body (model, context, features, target, forecast time and computed numbers). The returned original job key therefore binds the actual computation. Re-sealing changed receipt/freeze numbers cannot retain that job identity. The original generic freeze API and other callers' attempt identities are unchanged.

The resulting original freeze can reach the existing later measurement/calibration/triad path and subsequently become an input to another explicit training invocation. This supplies a numerical next-cycle mechanism, not a continuous training scheduler, automatic promotion, natural-source validation or demonstrated Double-Play benefit. Phase20/21 and other research/representation paths retain their separate contracts.
