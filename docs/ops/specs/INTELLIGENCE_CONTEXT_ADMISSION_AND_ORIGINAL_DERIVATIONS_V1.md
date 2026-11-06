---
docs_token: DOCS_TOKEN_INTELLIGENCE_CONTEXT_ADMISSION_AND_ORIGINAL_DERIVATIONS_V1
status: active
scope: Explicit offline MI context admission; no productive activation
---

# Intelligence context admission and original derivations

This is an additive implementation contract subordinate to the existing Track D
owners. It grants no runtime, trading, selection, capital or promotion authority.

The existing Phase18/19 materializer now optionally exposes a copied derivation
sidecar keyed by its original state references. Native records, IDs, decimal text
and equations remain unchanged. Price, flow, OHLCV proxy, volatility, derivatives
and cross-market calculations are still performed by their original functions.
The sidecar resolves numbers already computed there; it is not a second fact SSOT.

The local Attach bridge accepts only the existing boolean-false offline pins.
Boolean true, integer zero, None and strings fail closed. No global pin is changed.

## Explicit consumer

`compose_admitted_intelligence_context_v1` composes the existing materializer after
checking original payload bytes, original digest, source reference, generation,
canonical/native instrument and venue, actual capture, declared knowledge and
availability time, final interval availability, quality, finite numbers and units.
The source receipts are caller-provided evidence, not venue authentication.
Missing original capture or source metadata rejects rather than inventing history.

Every used fact requires exactly one receipt; unused receipts reject. A receipt
may be shared when the same original fact is used in multiple named roles.
Freshness limits and required families are explicit caller policy with no defaults.
Series must be contiguous PT1M and duplicate-free; selected/anchor grids must match.
OI levels must have compatible units and distinct timestamps. Trade notional and
OHLCV proxy inputs require base quantities; contract quantities are not silently
converted. Funding requires an explicit rate-period unit. There is no annualization.

All original source JSON bytes, hashes, times and units are retained as evidence
with the native context and copied derivation bodies. Hash binding proves integrity,
not natural provenance. An immutable full identity binds source generation, venue,
instrument, native mapping, lane, epoch and decision. Lane IDs identify exactly the
five existing slots and confer no position capacity.

## Equations and limits

Cross-market keeps the original formula `(selected-anchor)-beta*anchor`; it is not
renamed or changed into `selected-beta*anchor`. The native derived payload and
version make that meaning inspectable. Volatility, Scope and their parameters are
unchanged. Proxy microstructure remains PROXY_OHLCV, not L2.

Without an explicitly admitted provider the output is ABSTAIN with
NO_ADMITTED_FORECAST_PROVIDER. Missing required context gives INSUFFICIENT and
ABSTAIN/MISSING_REQUIRED_FAMILIES, without numeric zero substitution or a dummy
ForecastEvidence. This callable offline composition does not register a service,
schedule a job, touch productive financial owners or supply a model by inference.

Forecast execution/quality, measured research feature influence, GVEF quality and
the explicit Governance receiver remain separate interfaces and proofs. A new
integration function is not evidence that the productive host calls it.

Tests: [context admission](../../../tests/learning/test_intelligence_context_admission_v1.py),
[original materializer](../../../tests/learning/test_market_context_existing_fact_materialization_v1.py),
[Phase19](../../../tests/learning/test_market_context_phase_19_orthogonal_materialization_v1.py).
