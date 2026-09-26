---
docs_token: DOCS_TOKEN_PEAK_TRADE_RANKING_FEATURE_CONTRACT_V1
status: active
scope: B04 typed ranking feature contract/DTO seam; B03 policy binding only; no runtime activation
capability: CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-26
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
SELECTION_AUTHORITY: false
ECONOMIC_RANK_ACTIVATED: false
PRODUCTIVE_ECONOMIC_RANK_ACTIVATION: false
HARD_STOP: true
---

# Peak Trade Ranking Feature Contract V1 (B04)

Owner-GO `PEAK_TRADE_B04_RANKING_FEATURE_CONTRACT_V1` materializes the
B03-ratified Cap 2.2 ranking policy into versioned, deterministic
contract/DTO types for raw inputs, normalized values, candidate bundles,
score contributions, explainability witnesses, and provenance — without
productive economic rank activation (B06), Cap 2.3 selection changes, or
external effects. B05 Cap-2.1 feature production is a separate slice that
consumes this contract for raw DTO population only.

Subordinate to
`docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md` and
`docs/ops/specs/PEAK_TRADE_RANKING_MATRIX_POLICY_V1.md`.

Typed owner: `src/ops/peak_trade_ranking_feature_contract_v1.py`.

```text
DOCUMENT_CLASS=DOCS_AND_TYPED_CONTRACT_PEAK_TRADE_RANKING_FEATURE
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=PEAK_TRADE_B04_RANKING_FEATURE_CONTRACT_V1
BOUND_ORIGIN_MAIN_SHA=9117b02e6c1ba93732c3efa17d1bba47f77294ae
CONTRACT_ID=PEAK_TRADE_RANKING_FEATURE_CONTRACT_V1
CONTRACT_VERSION=peak_trade_ranking_feature_contract/v1
SCHEMA_VERSION=peak_trade_ranking_feature_witness.v1
B04_IMPLEMENTED=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
AUTHORITY_EFFECT=NONE
PRODUCTIVE_ECONOMIC_RANK_ACTIVATION=false
ECONOMIC_RANK_ACTIVATED=false
INPUT2_MAX_AGE_SECONDS_RATIFIED=false
INPUT2_MAX_AGE_SECONDS=UNRATIFIED
CAP23_SOLE_SELECTION_OWNER=true
CROSS_UNIVERSE_AUTHORITY=NONE
```

## Ratified economic features (B03 only)

| Feature policy ID | Role |
| --- | --- |
| `CAP22_PT1M_MARK_LOG_RETURN_POPULATION_SIGMA_V1` | Volatility raw input |
| `CAP22_PT1M_MARK_MID_RELATIVE_RANGE_V1` | Amplitude raw input |

Structural Cap 2.1 score components and profile-only fields are carried
in separate witness types with `economic_ranking_authority=false`.

## Witness layers

1. **Policy identity** — ranking policy id/version/digest plus feature
   contract id/version/digest and score construction id.
2. **Input-2 provenance** — neutral age/timestamp transport;
   `input2_max_age_seconds` remains `UNRATIFIED`.
3. **Raw / normalized feature values** — explicit `READY`, `MISSING`,
   `INVALID`, `INCOMPLETE_WARMUP`, `NOT_READY` states; no silent defaults.
4. **Explainability** — per-candidate contributions, tie-break stages,
   optional pairwise order witness; deterministic canonical JSON digest.

## Explicit non-claims

- Contract present ≠ productive economic rank activated.
- B04 does not wire Cap 2.2 producer runtime or Cap 2.3 selection.
- Map of Truth and System Atlas remain navigation-only (`AUTHORITY=NONE`).
