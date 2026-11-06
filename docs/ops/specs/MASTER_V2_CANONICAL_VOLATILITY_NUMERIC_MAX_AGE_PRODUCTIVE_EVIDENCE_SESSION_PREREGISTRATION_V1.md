# MASTER_V2 Canonical Volatility Numeric Max-Age Productive Evidence Session Preregistration v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_EVIDENCE_SESSION_PREREGISTRATION_V1
STATUS: CAPABILITY_AVAILABLE
scope: campaign and session preregistration only; no runtime; no network; no evidence write
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
NETWORK_AUTHORIZED: false
EXECUTION_AUTHORIZED: false
EVIDENCE_WRITE_AUTHORIZED: false
PARAMETER_DECISION_AUTHORIZED: false
ENFORCEMENT_AUTHORIZED: false
COUNTERFACTUAL_ONLY: true
MAX_AGE_THRESHOLD_SELECTED: false
MAX_AGE_ENFORCEMENT_ENABLED: false
AUTO_PROMOTION_ALLOWED: false
HARD_STOP: true
---

> **Campaign &#47; session preregistration only.**
> Creates a versioned, digestsable plan for a later separately authorized
> public-read-only market-data campaign. Does **not** start a session, open
> network, fetch market data, write evidence, materialize ledger parent dirs,
> select a threshold, enable enforcement, or mutate Alpha &#47; State &#47;
> Composition &#47; Risk &#47; Exit.

## Machine summary

```
REVIEW_MODE=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_EVIDENCE_SESSION_PREREGISTRATION_V1
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_EVIDENCE_SESSION_PREREGISTRATION_V1
SCHEMA=canonical_volatility_numeric_max_age_productive_evidence_session_preregistration/v1
REPOSITORY_SHA=e9c1871ea7b493cde9f49eb517910b1a7134fb5b
PRODUCTIVE_PREREGISTRATION_DIGEST=777e3dd8aa3458f8687cabbadf63016ac478b5385568ee3d54d22c119880a62e
DESIGN_PREREGISTRATION_DIGEST=965f6e09e50e434e363d380c2d62e43041a37ad7d87956e590609a16f011b537
RESEARCH_AGE_GRID_SECONDS=[60,120,300,600,900,1800,3600,7200]
EXECUTION_AUTHORIZED=false
NETWORK_AUTHORIZED=false
EVIDENCE_WRITE_AUTHORIZED=false
HARD_STOP=true
```

## Campaign purpose

Preregister a productive Canonical-Volatility numeric max-age research evidence
accumulation campaign and at least two independent sessions. The campaign may
later accumulate counterfactual age-grid observations under a **separate**
authorization. This step never authorizes execution.

## Session lifecycle

```
PREREGISTERED
  → separately AUTHORIZED
  → ACTIVE
  → COMPLETED | ABORTED
```

All sessions in this artifact start as `PREREGISTERED` with
`planned_start_not_authorized=true` and `no_runtime_side_effects=true`.

Process restart continues the **same** `session_id` with an explicit
`resume_token` and `restart_generation + 1`. A restart is not a new independent
session and must not fabricate coverage.

## Public read-only market-data plan (still unauthorized)

| Field | Value |
|---|---|
| venue | OKX |
| venue_scope | OKX_EEA_FUTURES_PUBLIC_MARKET_DATA |
| host | `https:&#47;&#47;eea.okx.com` |
| transport | HTTPS_REST_GET_ONLY |
| method | GET only |
| credentials_required | false |
| websocket_allowed | false |
| private &#47; order &#47; mutation | excluded |
| canonical_instrument_id | ETH-USD_UM_XPERP-310404 |
| venue_native_instrument_id | resolved only via existing venue-binding authority |
| network_authorized | false |
| feed_activation_requires_separate_authorization | true |

Allowed endpoints only:

- `&#47;api&#47;v5&#47;public&#47;time`
- `&#47;api&#47;v5&#47;public&#47;instruments`
- `&#47;api&#47;v5&#47;public&#47;mark-price`
- `&#47;api&#47;v5&#47;market&#47;ticker`
- `&#47;api&#47;v5&#47;market&#47;tickers`

## Sample &#47; event-time semantics

- `CANONICAL_TIME_DOMAIN=MARKET_EVENT_TIME`
- runtime cycle is not a market sample
- decision epoch is not a market sample
- repeated poll results cannot fabricate market time
- duplicate samples cannot create a new age observation
- out-of-order and distinct-observation policies must reuse existing typed policies

Every later productive observation must bind at least:
`market_sample_id`, `venue`, `canonical_instrument_id`,
`venue_native_instrument_id`, `event_time`, `receive_time`,
`source_sequence_or_equivalent`, `mark_price`, `sample_digest`,
`volatility_estimate_id`, `volatility_as_of_event_time`, `computed_age_seconds`,
`session_id`, `restart_generation`, `market_regime_label`,
`volatility_regime_label`.

Regime labels must come from typed feature &#47; regime metadata authority — not
free text and not invented fixed name lists in this preregistration.

## Coverage minima

- `minimum_independent_sessions=2`
- `minimum_distinct_sessions=2`
- `minimum_distinct_evidence_records=8`
- `minimum_market_regimes=2`
- `minimum_volatility_regimes=1`
- `minimum_instruments=1`
- `minimum_computed_age_observations=1`
- at least one distinct observation planned per age bucket
  `[60,120,300,600,900,1800,3600,7200]`

## 7200-seconds reachability plan

Natural reachability only:

1. Campaign event-time &#47; wallclock span must exceed 7200 seconds.
2. An early independent session produces a valid VolatilityEstimate and retains
   its real `as_of_event_time`.
3. Later distinct market samples raise
   `computed_age_seconds = event_time - volatility_as_of_event_time` naturally.
4. Restarts may reload the same estimate history without counting a new estimate.
5. Missing natural reachability terminates fail-closed as coverage-incomplete.
6. Bounds remain `≤128` cycles per session, `≥2` independent sessions; coverage
   may accumulate across sessions and process starts. No exact polling cadence
   is defined as market time.

## Durable paths

Canonical non-`&#47;tmp` paths:

- productive ledger:
  `docs&#47;evidence&#47;canonical_volatility_max_age_productive_research_evidence_ledger_v1&#47;productive_research_evidence_ledger.jsonl` <!-- pt:ref-target-ignore -->
- quarantine ledger:
  `docs&#47;evidence&#47;canonical_volatility_max_age_productive_research_evidence_ledger_v1&#47;productive_research_evidence_quarantine.jsonl` <!-- pt:ref-target-ignore -->
- join projection:
  `docs&#47;evidence&#47;canonical_volatility_numeric_max_age_research_evidence_ledger_v1&#47;research_evidence_ledger.jsonl` <!-- pt:ref-target-ignore -->

Campaign-specific paths (not materialized here) cover typed volatility
persistence, campaign &#47; session manifests, terminal verdict, and evaluability
report under a campaign-scoped directory. Parent dirs are created only after a
separate campaign authorization.

## Separate authorization requirement

This capability issues **no** authorization. A later explicit operator step must
authorize:

- campaign execution
- network &#47; public MD feed activation
- evidence writes
- parent-dir materialization

Until then: `execution_authorized=false`, `network_authorized=false`,
`evidence_write_authorized=false`.

## Non-promotion invariants

```
COUNTERFACTUAL_ONLY=true
ENFORCEMENT_APPLIED=false
MAX_AGE_THRESHOLD_SELECTED=false
MAX_AGE_ENFORCEMENT_ENABLED=false
ALPHA_SEMANTICS_CHANGED=false
STATE_SEMANTICS_CHANGED=false
COMPOSITION_AUTHORITY_CHANGED=false
EXIT_PRECEDENCE_PRESERVED=true
REVERSAL_REDUCE_FIRST_PRESERVED=true
AUTO_PROMOTION_ALLOWED=false
```

Runbook guidance remains binding for event-time, sample identity,
poll-rate independence, state-domain separation, exit precedence, and the
separation of research, shadow, and promotion:
`Peak_Trade_Master_V2_Double_Play_Market_State_Decision_Cadence_Runbook_v3_revised_v4.md`.

## Owners

| Artifact | Path |
|---|---|
| Builder &#47; verifier | `src&#47;research&#47;canonical_volatility_max_age_productive_research_evidence_accumulation_v1&#47;session_campaign_preregistration_v1.py` |
| Frozen artifact | `config&#47;research&#47;canonical_volatility_numeric_max_age_productive_evidence_session_preregistration_v1.json` |
| CLI modes | `render-session-preregistration`, `verify-session-preregistration` |
| CLI owner | `scripts&#47;ops&#47;run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py` |
| Focused tests | `tests&#47;research&#47;test_canonical_volatility_numeric_max_age_productive_evidence_session_preregistration_v1.py` |
| Spec | this document |

## Operator process (read-only)

```
PYTHONPATH=src python3 scripts&#47;ops&#47;run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py \
  --mode verify-session-preregistration
```

```
PYTHONPATH=src python3 scripts&#47;ops&#47;run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py \
  --mode render-session-preregistration
```

## Exact next step after merge

After merge of this capability PR, the **only** next step is a **separate**
operator-authorized campaign-authorization capability that may activate the
preregistered public-read-only MD plan and allow durable path materialization &#47;
evidence writes. Until that separate GO:

- `READY_FOR_PRODUCTIVE_EVIDENCE_EXECUTION=false`
- `PARAMETER_DECISION_ALLOWED=false`
- `HARD_STOP=true`

## Non-goals

- runtime session start
- network &#47; market-data fetch
- evidence or ledger mutation
- threshold selection or enforcement
- Alpha &#47; State &#47; Composition &#47; Risk &#47; Exit mutation
- automatic promotion
- mutation of existing research preregistration digests
