# Cross-Sectional MA-Crossover Panel Rank Rotation v0 — Phase 3 Dataset Materialization v1

---
docs_token: DOCS_TOKEN_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_PHASE3_DATASET_MATERIALIZATION_V1
STATUS: PHASE3_DATASET_MATERIALIZED_NOT_EVALUATED_NOT_BINDING_RATIFIED
scope: governance, bounded-network-ingest, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Bounded Phase-3-Dataset-Materialization für `cross_sectional_ma_crossover_panel_rank_rotation&#47;v0`. Registriert OKX Production Lifecycle Source und PIT-fähiges PT1H-Panel-OHLCV. Keine Versioned-Binding-Ratifikation. Keine Economic Evaluation. Keine Runtime-Authority.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_PHASE3_DATASET_MATERIALIZATION_PASS` |
| `PROCESS_CLASSIFICATION` | `BOUNDED_OKX_PRODUCTION_LIFECYCLE_AND_PT1H_PANEL_DATASET_MATERIALIZATION_NO_EVAL_NO_RUNTIME_AUTHORITY_V1` |
| `GO_TOKEN` | `GO_BOUNDED_OKX_PRODUCTION_LIFECYCLE_SOURCE_REGISTRATION_AND_PT1H_PANEL_OHLCV_INGEST_V0` |
| `GO_TOKEN_CONSUMED` | `true` |
| `RESEARCH_SCOPE_RATIFIED` | `true` |
| `BINDING_RATIFIED` | `false` |
| `DATASET_MATERIALIZED` | `true` |
| `ECONOMIC_EVALUATION_AUTHORIZED` | `false` |
| `ECONOMIC_EVALUATION_EXECUTED` | `false` |
| `SINGLE_INSTRUMENT_EVIDENCE` | `TERMINAL_NEGATIVE` |
| `PANEL_ARCHETYPE_EVIDENCE` | `NOT_PREVIOUSLY_EXECUTED` |
| `RUNTIME_EFFECT` | `NONE` |
| `AUTHORITY_EFFECT` | `NONE` |
| `NEXT_ACTION` | `VERSIONED_BINDING_RATIFICATION_REQUIRES_SEPARATE_OPERATOR_GO` |

## B. Dataset Contract

| Feld | Wert |
|---|---|
| `DATASET_ID` | `pit_okx_linear_usdt_non_bitcoin_pt1h_panel` |
| `DATASET_VERSION` | `v2` |
| `DATASET_SCHEMA` | `pit_okx_pt1h_panel_ohlcv_dataset_manifest_v1` |
| `BAR_INTERVAL` | `PT1H` |
| `LIFECYCLE_POLICY` | `okx_production_instrument_lifecycle_historical_as_of_fail_closed.v1` |
| `STAGING_WINDOW_DAYS` | `14` |
| `NETWORK_SURFACE` | `okx_public_rest_api_v5_public_get_only` |
| `BITCOIN_PRESENT` | `false` |
| `FUTURES_ONLY` | `true` |

## C. Config References

| Artifact | Path |
|---|---|
| Phase 3 closeout | `config/research/cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_dataset_materialization_v1.json` |
| Canonical ingest owner | `scripts/ops/materialize_okx_production_lifecycle_and_pt1h_panel_v1.py` |
| Closeout owner | `scripts/ops/materialize_cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_dataset_materialization_v1.py` |
| Implementation owner | `src/research/cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_dataset_materialization_v1.py` |

## D. Explicit Non-Claims

| Claim | Status |
|---|---|
| Economic evaluation executed | **false** |
| Versioned binding ratified | **false** |
| Runtime authority touched | **false** |
| Promotion granted | **false** |
| Signal logic changed | **false** |
