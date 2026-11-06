# MASTER_V2 Canonical Volatility Numeric Max-Age Productive Research Evidence Accumulation v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_RESEARCH_EVIDENCE_ACCUMULATION_V1
STATUS: CAPABILITY_AVAILABLE
scope: productive research evidence accumulation, counterfactual age-grid diagnostics, and evaluability without parameter decision
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
NUMERIC_MAX_AGE_DECIDED: false
NUMERIC_MAX_AGE_SECONDS: null
THRESHOLD_STATUS: UNRESOLVED_MAX_AGE
ENFORCEMENT_ENABLED: false
ENFORCEMENT_APPLIED: false
COUNTERFACTUAL_ONLY: true
THRESHOLD_SELECTED: false
BLOCKED_FOR_PARAMETER_DECISION: true
HARD_STOP: true
---

> **Productive research-evidence accumulation and evaluability only.**
> Accumulates typed join-compatible evidence, evaluates a preregistered research
> age grid counterfactually, and reports coverage &#47; robustness readiness.
> Does **not** select a numeric threshold, recommend a productive value, mutate
> Alpha &#47; State &#47; Composition &#47; Risk &#47; Exit, enable enforcement, or authorize
> orders. Insufficient coverage is a valid outcome and remains
> `BLOCKED_FOR_PARAMETER_DECISION`.

## Machine summary

```
REVIEW_MODE=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_RESEARCH_EVIDENCE_ACCUMULATION_V1
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_MAX_AGE_PRODUCTIVE_RESEARCH_EVIDENCE_ACCUMULATION_CAPABILITY_V1
PRODUCTIVE_PREREGISTRATION_CONTRACT_VERSION=canonical_volatility_numeric_max_age_productive_research_evidence_preregistration/v1
AGE_REFERENCE_CLOCK=MARKET_EVENT_TIME
COUNTERFACTUAL_ONLY=true
ENFORCEMENT_APPLIED=false
THRESHOLD_SELECTED=false
BLOCKED_FOR_PARAMETER_DECISION=true
RUNTIME_CYCLE_IS_NOT_MARKET_SAMPLE=true
HARD_STOP=true
```

## Research question

Which, if any, robust event-time `maximum_observation_age` region for canonical
`VolatilityEstimateV1` can later be considered — using only productive research
evidence accumulated under the preregistration — without selecting,
recommending, or enforcing a numeric threshold in this step?

## Producer &#47; Consumer &#47; Evidence Graph

```
Productive bridge runner
  → ProductiveNaturalAgeLifecycleCmcBindingHostV1
       (NaturalAgeProgressionLifecycleHostV1 = sole produce&#47;reuse&#47;recompute authority)
  → Typed VolatilityEstimateV1 with immutable as_of during reuse
  → Presence &#47; Trust Gate (unknown entry fail-closed; exit&#47;reduce&#47;risk&#47;safety preserved)
  → Non-enforcing max-age telemetry (threshold unresolved; natural age from event time)
  → Productive evidence producer (preregistration bound first; lifecycle age fail-closed)
  → Validation &#47; quarantine (fail-closed)
  → Append-only productive ledger (chained digests)
  → Research join projection (existing join contract)
  → Counterfactual age-grid diagnostics (no decision mutation)
  → Actionable strata &#47; safety&#47;risk&#47;exit observability (consumers only)
  → Evaluability &#47; robustness report (no winner selection)
  → Later separate Parameter-Decision step (explicit GO required)
```

Natural-age lifecycle wiring owner:

`docs&#47;ops&#47;specs&#47;MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_BRIDGE_NATURAL_AGE_LIFECYCLE_WIRING_V1.md`

No node in this graph is Alpha, State, Composition, Risk, Safety, TradingGate,
order, or threshold-selection authority.

## Preregistration

Machine-readable owner:

`src&#47;research&#47;canonical_volatility_max_age_productive_research_evidence_accumulation_v1&#47;preregistration_v1.py`

Bound before every productive evidence write via
`assert_preregistration_before_evidence_v1()`.

Includes:

- research age candidate grid (research arguments only; not a recommendation)
- event-time age semantics and estimate_age definition
- fresh &#47; stale &#47; missing &#47; untrusted definitions
- distinct-observation, duplicate, out-of-order, stale, warm-up policies
- regime stratification minima
- leakage &#47; purge &#47; embargo controls (inherited; not executed here)
- abort criteria, metrics, stress &#47; robustness controls
- explicit non-promotion invariant

Design-contract digest remains the join-facing `preregistration_digest`.
This step adds `productive_preregistration_digest`.

## Age semantics

- canonical clock: market event time
- `estimate_age_seconds = reference_market_event_time - volatility_as_of_event_time`
- receive time is transported but never replaces event time for age
- runtime cycles are not market samples
- duplicate identical estimate identities do not advance distinct observation coverage

## Counterfactual semantics

For each preregistered age candidate, diagnostically compute:

- would-be fresh &#47; stale
- entry eligibility counterfactual
- exit-path preservation (always required true for age diagnostics)

Flags:

`COUNTERFACTUAL_ONLY=true`, `ALPHA_MUTATION=false`, `STATE_MUTATION=false`,
`ENFORCEMENT_APPLIED=false`, `THRESHOLD_SELECTED=false`.

## Ledger schema

Productive records use
`canonical_volatility_max_age_productive_research_evidence_record&#47;v1` and remain
append-only with chain digests. Join projection reuses
`canonical_volatility_numeric_max_age_research_evidence_join&#47;v1`.

Enrichment fields include `estimate_age_seconds`, `volatility_regime`,
`config_digest`, `code_sha`, `exit_path_preservation`,
`productive_preregistration_digest`, and `estimator_observation_count`.

## Session &#47; regime stratification

Coverage and evaluability report:

- coverage by session
- coverage by market regime
- coverage by volatility regime
- coverage by age bucket
- restart &#47; reuse boundaries

## Robustness plan

Evaluability implements, without selection:

- polling-frequency sensitivity
- duplicate &#47; out-of-order &#47; missing-sample sensitivity
- session stability and stability plateaus
- session-blocked bootstrap confidence intervals
- data-gap &#47; recovery stress
- exit-path-preservation regression

No productive winner ranking is emitted.

## Known coverage gaps

Absence of authorized productive external evidence remains a valid blocked
state. Fixture &#47; probe cycles are diagnostic helpers and must not be treated as
authoritative productive evidence for parameter decision.

## Conditions for a later Parameter-Decision step

A later separately authorized step is required. Exact prerequisites are emitted
by `parameter_decision_prerequisites_v1()` and include minimum session &#47; regime &#47;
distinct-observation coverage, loadable join ledger, recorded robustness &#47;
plateau evidence, and an explicit operator GO. Until then:

`BLOCKED_FOR_PARAMETER_DECISION=true`
`EVIDENCE_SUFFICIENT_FOR_PARAMETER_DECISION=false`

## Operator process

```
PYTHONPATH=src python3 scripts&#47;ops&#47;run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py \
  --mode evaluability-report \
  --productive-ledger-path &#47;path&#47;to&#47;productive_research_evidence_ledger.jsonl
```

Productive accumulation continues to use `--mode productive-bridge-accumulate`
under a separately valid campaign authorization.

## Owners

| Artifact | Path |
|---|---|
| Package | `src&#47;research&#47;canonical_volatility_max_age_productive_research_evidence_accumulation_v1&#47;` |
| Preregistration | `...&#47;preregistration_v1.py` |
| Counterfactual grid | `...&#47;counterfactual_grid_v1.py` |
| Evaluability | `...&#47;evaluability_v1.py` |
| CLI | `scripts&#47;ops&#47;run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py` |
| Spec | this document |
| Focused tests | `tests&#47;research&#47;test_canonical_volatility_numeric_max_age_productive_research_evidence_accumulation_v1.py` |
| Prior capability spec | `docs&#47;ops&#47;specs&#47;MASTER_V2_CANONICAL_VOLATILITY_MAX_AGE_PRODUCTIVE_RESEARCH_EVIDENCE_ACCUMULATION_CAPABILITY_V1.md` |

## Session-02 gap and next evidence-plan capability

Productive Session 02 completed with ledger integrity, but all computed ages were
`0` because each distinct sample rematerialized a fresh estimate
(`as_of_event_time == market_event_time`). That evidence is insufficient for a
numeric max-age policy decision.

The follow-on research-only capability

`docs&#47;ops&#47;specs&#47;MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_NATURAL_AGE_PROGRESSION_AND_ACTIONABLE_STRATA_EVIDENCE_PLAN_V1.md`

defines an explicit natural estimate lifecycle, research recompute wiring (not a
max-age policy), actionable strata projection, and an additional coverage plan
for later separately authorized sessions. Session 02 must not be retried by that
plan. No threshold selection or enforcement is introduced there.

## Non-goals

- numeric max-age decision or recommendation
- enforcement enablement
- Alpha &#47; State &#47; Composition &#47; Risk &#47; Exit mutation
- parameter promotion
- testnet &#47; paper &#47; live trading
- order routing
- legacy fallbacks `0.02` &#47; `0.2` &#47; `1.0` as research truth
