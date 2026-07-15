# Cross-Sectional Futures Pairwise Lead-Lag Spillover V1 Versioned Hypothesis Binding V0

> **Non-authorizing:** Ratifiziert die versionierte Binding-Identität für `cross_sectional_futures_pairwise_lead_lag_spillover&#47;v1` als pairwise directed spillover graph hypothesis auf dem kanonischen PIT-OHLCV-Panel. Keine Economic Evaluation, keine Score-Berechnung, keine Runtime, keine Promotion.

## Scope

| Feld | Wert |
|------|------|
| `research_scope` | `cross_sectional_futures_pairwise_lead_lag_spillover&#47;v1` |
| `hypothesis_family` | `pairwise_leader_follower_spillover_v1` |
| `score_family` | `pairwise_spillover_graph_v1` |
| `market_scope` | `OKX_LINEAR_USDT_NON_BITCOIN_FUTURES` |
| `bar_interval` | `PT1H` |
| `dataset_policy` | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1` |
| `universe_policy` | `pit_okx_linear_usdt_non_bitcoin_perpetual_universe_manifest_v1` |
| `timestamp_alignment` | `common_utc_hourly_close_intersection_no_forward_fill` |

## Pairwise Semantics

- Knoten sind einzelne zulässige Futures-Instrumente.
- Kanten sind gerichtete Leader→Follower-Beziehungen (`ordered_directed_pairs_i_to_j_with_i_not_equal_j`).
- Features: `feature_time < decision_time` (nur lagged return und optional lagged OHLCV).
- Targets: `decision_time < target_time` (strictly future return).
- Kein contemporaneous target leakage, kein Forward Fill, keine unfinalisierten Bars.
- Keine Panel-Median-Benchmark-Semantik aus Lead-Lag-v0.
- Kein unverändertes Reuse des terminalen Lead-Lag-v0-Bindings.

## Pending Implementation Fields

Folgende Felder sind explizit `PENDING_SEPARATE_IMPLEMENTATION_BINDING`:

- `aggregation_policy`
- `selection_policy`
- `holding_policy`
- `exit_policy`
- `portfolio_weighting_policy`

## Distinctness and Negative Evidence

| Feld | Wert |
|------|------|
| `prior_scope` | `cross_sectional_futures_lead_lag_information_diffusion&#47;v0` |
| `prior_scope_status` | `TERMINAL_INSUFFICIENT_SAMPLE` |
| `material_difference_class` | `PAIRWISE_DIRECTED_GRAPH_VS_PANEL_MEDIAN_DIFFUSION` |
| `negative_evidence_preserved` | `true` |
| `unchanged_retry` | `false` |
| `policy_rescue` | `false` |

## Dataset Reuse

| Feld | Wert |
|------|------|
| `DATASET_REMATERIALIZATION_REQUIRED` | `false` |
| `DATASET_REUSE` | `REUSE_AS_IS` |
| `UNIVERSE_REUSE` | `REUSE_AS_IS` |
| `PERIOD_SPLIT_REUSE` | `REUSE_AS_IS` |

## Canonical Owners

| Surface | Owner |
|---------|-------|
| Binding validator | `src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0.py` |
| Materializer | `scripts/research/materialize_cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0.py` |
| Config | `config/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0.json` |
| Tests | `tests/research/test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0_contract.py` |

## Next Admissible Scope

`GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_SCORE_AND_RANKING_CONTRACT_IMPLEMENTATION_V0`
