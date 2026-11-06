---
docs_token: DOCS_TOKEN_INTELLIGENCE_EXACT_FORECAST_MEASUREMENT_HANDOFF_V1
status: active
scope: Explicit offline forecast binding, original measurement and typed handoffs
---

# Exact forecast, original measurement and separate SL/OPT handoffs

This additive composition preserves the original ForecastEvidence, N_BARS,
CalibrationEvidence, MI durable store and typed Learning/Optimization owners.
It does not execute or select a forecasting model and does not activate a host.

## Before a forecast can be frozen

Replay the admitted context from its exact original source JSON, original source
order, metadata and original derivation functions. A resealed inconsistent sidecar
is rejected. Preserve optional materialization parameters and original fact kind,
including facts whose payload lacks a redundant fact-kind field.

Validate individual finite probabilities and their domains, finite return means,
nonnegative standard deviations, and an explicit measurement-adapter kind. This
composition currently admits only RETURN_DISTRIBUTION_SUMMARY with the original
first-finalized-close to last-finalized-close LOG_RETURN target. Directional
component validation is available separately; no directional-to-return conversion
is invented. The old directional method and its historical name remain unchanged.

Require a supplied provider-admission manifest and exact model artifact digest,
model/training/validation/schema/admission references, training availability,
context binding and explicit context-age policy at forecast creation time. These
are caller-supplied evidence, not an independently authenticated model admission or
proof of actual inference. Missing provider remains explicit abstention in the
context entry. No default model, training dataset or scientific metric is chosen.

Freeze the native forecast with its complete optional decision/instrument/drift
references and the original probabilistic JSON bytes. The additive byte digest
retains complete float representations and original formatting; no .12g digest
migration occurs. The full job key includes source generation, instrument, venue,
native mapping, lane, epoch, decision, information set, target digest, N, bar spec,
model and attempt generation. N alone cannot address the job.

## Original measurement and persistence

Before any measurement attachment or original-store write, call the original
side-effect-free measured-return preparation. It performs the unchanged target,
entity, temporal, original measurement-artifact and numeric validation and computes
the unchanged calibration and research projection. The existing calibration API
then delegates to that preparation and its existing persistence owner.

N closes still mean N-1 close-return intervals. Return error remains realized
log return minus forecast mean. It is neither money PnL nor a research score;
standard-deviation admission does not establish distribution calibration.

Freeze-before-measurement and source-generation/availability checks precede the
handoff. Evidence attachments under the caller-supplied original MI store root
retain forecast, exact measurement inputs and numeric readback ACK. They are not
an outcome scheduler, an independent Pending queue or a second fact/Learning SSOT.
Publication uses complete fsynced temporary bytes and exclusive atomic creation;
per-full-job process leases serialize participating wrapper calls. No guarantee
is inferred about unrelated legacy writers, host crash or power loss.

Cold readback compares the complete original MI triad, exact input parents and
numeric values without executing a provider, backtest, evaluator or calibration.
An interruption after native persistence but before ACK resumes the original
idempotent calibration/store path. A divergent same-key retry rejects. A simulated
exception boundary and a separate fresh-process cold read are tested; these are
not claimed as a complete physical crash matrix.

## Separate typed consumers

The additive optional original-calibration argument to the existing MI-to-Learning
bridge reproduces the exact calibration, including its provenance, before using
its identity. Existing calls without that argument retain their original behavior.
Original typed Learning storage/readback and MI_TYPED_ONLY export are separate
from the original Optimization intake ACK. A changed Learning recipient rejects
before writing to that foreign store. The original opaque DDO score label is not
reinterpreted. Original facts, ledgers, Scope and five-slot semantics are preserved.

OPT admission is not numerical feature consumption by a Research provider.
A supplied forecast is not proof of model inference or quality. Actual feature
use, model/scientific admission and a Governance receiver remain explicit open
integration requirements; no productive apply or automatic promotion follows.

Tests: [exact integration](../../../tests/learning/test_intelligence_forecast_measurement_integration_v1.py),
[original measured return](../../../tests/learning/test_measured_return_calibration_v1.py).
