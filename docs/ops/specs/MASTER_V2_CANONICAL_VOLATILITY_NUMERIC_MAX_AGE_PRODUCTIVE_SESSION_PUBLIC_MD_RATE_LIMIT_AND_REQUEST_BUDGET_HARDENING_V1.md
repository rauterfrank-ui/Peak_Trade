# MASTER_V2 Canonical Volatility Numeric Max-Age Productive Session Public-MD Rate-Limit and Request-Budget Hardening v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_SESSION_PUBLIC_MD_RATE_LIMIT_AND_REQUEST_BUDGET_HARDENING_V1
STATUS: CAPABILITY_AVAILABLE
scope: productive preregistered session public-MD pacing, request budget, HTTP 429 contract, attempt evidence, venue instrument binding
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
NETWORK_AUTHORIZED: false
EXECUTION_AUTHORIZED: false
EVIDENCE_WRITE_AUTHORIZED: false
PARAMETER_DECISION_AUTHORIZED: false
ENFORCEMENT_AUTHORIZED: false
COUNTERFACTUAL_ONLY: true
HARD_STOP: true
---

> **Capability only.**
> Hardens the preregistered productive session runner against zero-interval
> request bursts and weak HTTP-429 retries.
> This PR does **not** execute Session 02, does **not** consume authorization,
> and does **not** perform real market-data requests.

## Machine summary

```
REVIEW_MODE=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_SESSION_PUBLIC_MD_RATE_LIMIT_AND_REQUEST_BUDGET_HARDENING_V1
PACING_MONOTONIC_CLOCK_BASED=true
SESSION_REQUEST_BUDGET_COUNTS_PHYSICAL_ATTEMPTS=true
RETRY_ATTEMPTS_COUNT_AGAINST_BUDGET=true
RETRY_AFTER_SUPPORTED=true
NESTED_OUTER_CYCLE_RETRY_FORBIDDEN=true
NOT_OFFICIAL_OKX_LIMIT_CLAIM=true
NOT_STRATEGY_OR_ALPHA_PARAMETER=true
HARD_STOP=true
```

## Why this capability exists

Session 01 terminated after authorization consumption with
`FETCH_FAILED:RATE_LIMIT_HTTP_429` after 43 identical mark-price GETs.
Root cause: `collect_public_mark_samples_v1(cycle_count=128, poll_interval_seconds=0.0)`
plus millisecond-scale 429 backoff without Retry-After, request budget, or
per-attempt evidence.

## Rate-limit / pacing contract

Owner type: `PublicMdRequestPacingPolicyV1`

| Field | Default | Origin |
|---|---|---|
| `minimum_interval_seconds` | `2.0` | wallclock observation `poll_interval_seconds` |
| `maximum_requests_per_cycle` | `3` | `per_request_max_retries + 1` |
| `maximum_consecutive_rate_limits` | `3` | same |
| `maximum_requests_per_session` | `160` | conservative ops safety cap |
| `retry_after_max_seconds` | `60.0` | conservative ops safety cap |
| `backoff_initial_seconds` | `1.0` | conservative ops safety default |
| `backoff_multiplier` | `2.0` | exponential |
| `backoff_max_seconds` | `30.0` | capped backoff |
| `jitter_fraction` | `0.1` | deterministic jitter contract |

These values are **ops/transport safety defaults**. They are **not** strategy or
alpha parameters and are **not** claimed to be official OKX rate limits unless a
repository-side venue contract proves otherwise.

Pacing:

- monotonic-clock based
- applied before every physical HTTP attempt (including retries)
- no busy-wait
- no sleep after the final successful sample
- `poll_interval_seconds=0.0` with `cycle_count>1` cannot create a zero-interval burst

## Request-budget contract

```
SESSION_REQUEST_BUDGET_COUNTS_PHYSICAL_ATTEMPTS=true
RETRY_ATTEMPTS_COUNT_AGAINST_BUDGET=true
BUDGET_CHECK_BEFORE_NETWORK_SIDE_EFFECT=true
BUDGET_CANNOT_BE_EXCEEDED=true
BUDGET_EXHAUSTION_IS_DETERMINISTIC=true
```

Effective budget:

```
effective = min(
  policy.maximum_requests_per_session,
  max_cycles * policy.maximum_requests_per_cycle
)
```

Clamp reason is written into evidence. Exhaustion terminal class:

`REQUEST_BUDGET_EXHAUSTED`

## HTTP-429 contract

Transport remains the sole per-request retry authority.

| Condition | Behavior |
|---|---|
| `Retry-After` delta-seconds valid | wait parsed seconds (capped) |
| `Retry-After` HTTP-date valid | wait until date (capped) |
| `Retry-After` invalid/negative | evidence `RATE_LIMIT_RETRY_AFTER_INVALID`, fall back to capped exponential backoff |
| `Retry-After` absent | capped exponential backoff + deterministic jitter |
| consecutive 429s exhausted | `RATE_LIMIT_RETRY_EXHAUSTED` — outer cycle loop does not start a new request |
| session 429 budget exceeded | `RATE_LIMIT_SESSION_BUDGET_EXCEEDED` |

Jitter is deterministic from `(session_id, global_request_index)` unless a test
injects another unit source. No millisecond retry storm.

## Telemetry counters

| Counter | Meaning |
|---|---|
| `physical_request_attempt_count` | every physical GET |
| `successful_response_count` | HTTP 2xx with usable provider payload path |
| `rate_limited_response_count` | HTTP 429 |
| `terminal_transport_failure_count` | terminal transport failures |
| `completed_market_sample_count` | parsed mark samples |
| `completed_accumulation_cycle_count` | productive accumulation cycles |

`market_data_request_occurred=true` as soon as the first physical GET begins,
even if collection later fails.

`NETWORK_FAILURES` must not be used as a physical-request count.

## Attempt evidence schema

`canonical_volatility_numeric_max_age_public_md_physical_attempt_evidence/v1`

One structured row per physical attempt with timing, status, Retry-After,
backoff source/delay, budget before/after, and terminal/error codes.
No secrets, full headers, or sensitive bodies.

## Instrument binding

Call graph:

```
run_preregistered_productive_session_v1
→ resolve_preregistered_session_venue_instrument_v1
→ resolve_okx_venue_instrument_mapping_v1
→ default_okx_europe_xperp_production_binding + sealed offline inventory validation
```

No second mapping authority. No network instruments call in offline tests.
Fail-closed on missing/ambiguous/contradictory binding. Evidence includes
canonical ID, venue ID, and mapping digest.

## Lifecycle order (unchanged safety order)

1. static preflight
2. atomic authorization consumption
3. session lock
4. venue instrument resolution
5. pacing/budget init
6. transport open
7. paced sample collection
8. accumulation
9. terminal evidence
10. lock release

## Non-goals

- No Session-02 execution
- No authorization issuance/consumption/revocation in this capability PR
- No Master-V2 / Double-Play alpha or numeric-max-age strategy changes
- No real OKX smoke test in CI
