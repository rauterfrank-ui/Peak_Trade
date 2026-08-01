# MASTER_V2 Canonical Volatility Numeric Max-Age Preregistered Productive Session Runner v1

---
docs_token: DOCS_TOKEN_MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PREREGISTERED_PRODUCTIVE_SESSION_RUNNER_V1
STATUS: CAPABILITY_AVAILABLE
scope: preregistered productive session runner capability only; no productive session execution in this PR; no authorization consumption; no real market-data
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
> Adds the unique fail-closed CLI/runner path that can later execute one already
> preregistered campaign session with exact session-id binding, preregistered
> OKX-EEA public market data, and consume-before-side-effects.
> This PR does **not** start Session 01, does **not** consume the issued
> authorization, and does **not** perform real market-data requests.

## Machine summary

```
REVIEW_MODE=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PREREGISTERED_PRODUCTIVE_SESSION_RUNNER_CAPABILITY_V1
CAPABILITY_ID=MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PREREGISTERED_PRODUCTIVE_SESSION_RUNNER_V1
CLI_MODE=productive-preregistered-session-run
SESSION_ID_EXACT_MATCH_REQUIRED=true
DERIVED_SESSION_IDS_FORBIDDEN=true
AUTHORIZATION_CONSUME_BEFORE_SIDE_EFFECTS=true
PRODUCTIVE_BRIDGE_ACCUMULATE_IS_NOT_THIS_RUNNER=true
PRODUCTIVE_SESSION_EXECUTION_IN_THIS_CAPABILITY=false
HARD_STOP=true
```

## Why this capability exists

`productive-bridge-accumulate` remains valid for offline authoritative bridge
capability probes. It is **not** a lawful runner for a preregistered productive
campaign session because it:

1. does not bind `TARGET_SESSION_ID` exactly
2. fabricates `{session_id}-productive-N` identifiers
3. uses offline deterministic mark paths
4. does not consume the preregistered OKX public MD plan
5. does not validate campaign authorization + preregistration + session as one
   atomic execution context

## CLI contract

Owner CLI:

`scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py`

Mode:

`productive-preregistered-session-run`

Example for a later separately authorized Session 01 execution
(not executed by this capability PR):

```bash
PYTHONPATH=src python3 scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py \
  --mode productive-preregistered-session-run \
  --campaign-id cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe \
  --preregistration-id MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PRODUCTIVE_EVIDENCE_SESSION_PREREGISTRATION_V1 \
  --preregistration-digest 1cfc1698796b1b931077cd692c7b0e97bc401f626d7e7b17bba1a777b62a252f \
  --session-id cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe_s01_8a97f48c839c \
  --authorization-id <issued-authorization-id> \
  --authorization-digest <issued-authorization-digest> \
  --campaign-authorization-artifact docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/campaigns/cv_maxage_productive_evidence_campaign_v1_4b3bdcecab2c0bfe/authorization/campaign_authorization.json \
  --repository-sha <exact-main-sha> \
  --expected-branch main \
  --venue OKX \
  --instrument-id ETH-USD_UM_XPERP-310404 \
  --market-data-scope OKX_EEA_FUTURES_PUBLIC_MARKET_DATA \
  --evidence-scope canonical_volatility_max_age_productive_research_evidence_ledger_v1 \
  --enable-real-public-md-fetcher
```

Preflight-only (no consume / no network):

```bash
... --mode productive-preregistered-session-run ... --preflight-only
```

## Lifecycle

1. local git / baseline check
2. preregistration validation
3. authorization validation
4. session-id and campaign bindings
5. venue / instrument / scope bindings
6. output / ledger target check without mutation
7. public-MD readiness without session side effects
8. atomic authorization consumption for the exact session id
9. session start / lock
10. public MD fetch + evidence accumulation via existing productive bridge consumer
11. terminal completion or fail-closed terminal evidence

No evidence, ledger, lock, session, or consumption mutation before step 8.

## Bindings

Exact match required for:

- repository SHA / branch
- campaign id
- preregistration id + digest
- authorization id + digest
- session id (no derivation, no `{session_id}-productive-N`)
- venue `OKX`
- instrument `ETH-USD_UM_XPERP-310404`
- market-data scope `OKX_EEA_FUTURES_PUBLIC_MARKET_DATA`
- evidence scope `canonical_volatility_max_age_productive_research_evidence_ledger_v1`

## Market-data contract

- OKX EEA public REST (`https://eea.okx.com`)
- GET only
- allowlisted public endpoints from the preregistration / authorization
- no credentials, private endpoints, orders, testnet, or websocket
- no offline / synthetic / deterministic mark source in this mode
- markPx from `/api/v5/public/mark-price`
- runtime cycles do not invent market time

## Separation from productive-bridge-accumulate

| Mode | Role |
|---|---|
| `productive-bridge-accumulate` | Offline authoritative bridge probe / capability path |
| `productive-preregistered-session-run` | Sole lawful runner for a preregistered campaign session |

## Owners

| Artifact | Path |
|---|---|
| Runner package | `src/research/canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1/` |
| CLI owner | `scripts/ops/run_canonical_volatility_max_age_productive_research_evidence_accumulation_v1.py` |
| Focused tests | `tests/research/test_canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.py` |
| Spec | this document |

## Non-goals

- Session 01 execution in this PR
- authorization issuance / consumption / revocation in this PR
- real market-data requests during capability merge
- threshold selection or enforcement
- Master-V2 / Double-Play trading-logic mutation
- promotion / economic-validity claims
