# MASTER_V2 Canonical Volatility Numeric Max-Age Productive Evidence Campaign Authorization v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_EVIDENCE_CAMPAIGN_AUTHORIZATION_V1
STATUS: CAPABILITY_AVAILABLE
scope: campaign authorization capability only; no productive issuance; no session start; no network; no evidence write
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
HARD_STOP: true
---

> **Capability only.**
> Defines schema, deterministic writer, parser &#47; verifier, expiry policy,
> append-only revocation, atomic per-session single-use consumption, CLI modes,
> and an accumulation gatekeeper integration point.
> This PR does **not** issue a productive authorization and does **not** start
> a productive evidence session.

## Machine summary

```
REVIEW_MODE=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_EVIDENCE_CAMPAIGN_AUTHORIZATION_CAPABILITY_V1
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_EVIDENCE_CAMPAIGN_AUTHORIZATION_V1
SCHEMA=canonical_volatility_numeric_max_age_productive_evidence_campaign_authorization/v1
AUTHORIZATION_SCOPE=canonical_volatility_numeric_max_age_productive_evidence_campaign_execution_v1
CAMPAIGN_AUTHORIZATION_TTL_SECONDS=86400
AUTHORIZATION_SINGLE_USE_PER_SESSION=true
AUTHORIZATION_MAXIMUM_TOTAL_CONSUMPTIONS=2
MAXIMUM_SESSION_COUNT=2
PRODUCTIVE_AUTHORIZATION_ISSUED=false
HARD_STOP=true
```

## Schema and scope

Schema version:

`canonical_volatility_numeric_max_age_productive_evidence_campaign_authorization&#47;v1`

Scope:

`canonical_volatility_numeric_max_age_productive_evidence_campaign_execution_v1`

Unknown fields are rejected (`REJECT_UNKNOWN_FIELDS`).

## Bindings

The authorization artifact deterministically binds at least:

- `schema_version`, `authorization_id`, `authorization_scope`
- `issued_at`, `earliest_start`, `expires_at`, `single_use`
- `repository_sha`, `campaign_id`, `session_ids`, `maximum_session_count`
- `preregistration_artifact_path`, `preregistration_digest`
- `productive_design_id`, `productive_accumulation_contract_version`
- `public_md_venue`, `public_md_host`, `public_md_endpoint_allowlist`,
  `public_md_method_allowlist`, `instrument_allowlist`
- `durable_ledger_path`, `join_path`, `quarantine_path`
- `revocation_ledger_path`, `consumption_ledger_path`
- `artifact_digest`

For the preregistered campaign, authorized session IDs must be exactly the two
preregistered sessions. Wildcards, prefix matches, dynamic third sessions, and
session-id reuse are forbidden.

## TTL &#47; expiry semantics

Defined in the productive contract (`expiry_v1.py`), not only in tests:

- `CAMPAIGN_AUTHORIZATION_TTL_SECONDS=86400`
- `expires_at = issued_at + 86400`
- `issued_at`, `earliest_start`, `expires_at` are timezone-aware UTC
- `earliest_start >= issued_at` and `earliest_start <= expires_at`
- naive datetimes are invalid
- verification &#47; consumption use an injectable clock
- `now < earliest_start` fail-closed
- `now >= expires_at` fail-closed
- no grace period, no auto-extension, no implicit re-issuance

## Per-session single-use and maximum consumptions

- `AUTHORIZATION_SINGLE_USE_PER_SESSION=true`
- `AUTHORIZATION_MAXIMUM_TOTAL_CONSUMPTIONS=2`
- each authorized session may be consumed at most once
- after two successful consumptions, further consumption fails closed
- unknown session IDs fail closed
- duplicate consumption of the same session fails closed

## Revocation

Append-only revocation ledger records:

`authorization_id`, `authorization_digest`, `revoked_at`, `reason`,
`operator_reference`, `revocation_record_digest`

Rules:

- irreversible; no unrevoke
- revocation before or after first consumption blocks remaining sessions
- already completed evidence is not rewritten
- corrupt &#47; ambiguous revocation ledger fails closed
- revocation never mutates source, config, or the authorization artifact file

## Consume-before-side-effects

Consumption must:

1. load the artifact
2. verify digest
3. verify schema and bindings
4. check earliest-start &#47; expiry
5. check revocation
6. check session id and consumption counters
7. persist an append-only consumption record under exclusive lock
8. re-read and verify the persisted record
9. only then return a runtime release

No network, evidence, join, quarantine, session-directory, or accumulation
side-effect may occur before step 8 succeeds. Temporary files have no authority.

## CLI usage (illustrative, non-existent paths)

Owner CLI:

`scripts&#47;ops&#47;run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py`

Modes:

- `render-campaign-authorization`
- `verify-campaign-authorization`
- `revoke-campaign-authorization`
- `consume-campaign-authorization`

Illustrative only (paths below are not real issuance artifacts):

```bash
python3 scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py \
  --mode render-campaign-authorization \
  --repository-sha <explicit-sha> \
  --campaign-id <explicit-campaign-id> \
  --session-ids <s01>,<s02> \
  --preregistration-digest <explicit-digest> \
  --issued-at 2026-08-01T12:00:00Z \
  --earliest-start 2026-08-01T12:00:00Z \
  --campaign-authorization-output /tmp/example_campaign_authorization.json
```

Render requires every operator binding argument explicitly. There are no
productive defaults for repository SHA, campaign id, session ids,
preregistration digest, earliest-start, or output path.

## Capability versus issuance

| Surface | This capability PR |
|---|---|
| Schema &#47; writer &#47; verifier | implemented |
| Expiry &#47; revocation &#47; consumption | implemented |
| Accumulation gate integration point | implemented |
| Productive authorization issued | **false** |
| Authorization consumed in production | **false** |
| Productive session started | **false** |
| Market-data request | **false** |
| Evidence &#47; ledger materialization | **false** outside tmp fixtures |

A later separate explicit operator order is required before any productive
campaign authorization issuance or evidence execution.

## Owners

| Artifact | Path |
|---|---|
| Authorization package | `src&#47;research&#47;canonical_volatility_numeric_max_age_campaign_authorization_v1&#47;` |
| CLI owner | `scripts&#47;ops&#47;run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py` |
| Focused tests | `tests&#47;research&#47;test_canonical_volatility_numeric_max_age_campaign_authorization_v1.py` |
| Spec | this document |

## Planned durable authorization ledger paths

Derived under the existing campaign evidence root (typed &#47; bound here; not
materialized by this capability):

- revocation ledger:
  `docs&#47;evidence&#47;canonical_volatility_max_age_productive_research_evidence_ledger_v1&#47;campaigns&#47;cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe&#47;authorization&#47;revocation_ledger.jsonl` <!-- pt:ref-target-ignore -->
- consumption ledger:
  `docs&#47;evidence&#47;canonical_volatility_max_age_productive_research_evidence_ledger_v1&#47;campaigns&#47;cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe&#47;authorization&#47;consumption_ledger.jsonl` <!-- pt:ref-target-ignore -->

Productive ledger &#47; join &#47; quarantine paths remain those already defined by the
preregistration and accumulation contracts.
