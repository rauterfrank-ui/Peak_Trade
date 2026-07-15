# Cross-Sectional Futures Pairwise Lead-Lag Spillover V1 Score-and-Ranking Contract V0

> **Non-authorizing:** Implementiert den kanonischen Score- und Ranking-Contract für `cross_sectional_futures_pairwise_lead_lag_spillover&#47;v1` als Ergänzung zum ratifizierten Hypothesis Binding. Keine Economic Evaluation, keine Selection-/Aggregation-Policy-Bindung, keine Runtime, keine Promotion.

## Scope

| Feld | Wert |
|------|------|
| `research_scope` | `cross_sectional_futures_pairwise_lead_lag_spillover&#47;v1` |
| `score_family` | `pairwise_spillover_graph_v1` |
| `hypothesis_binding_digest` | `a531051eb8a4f414fea42aef9bed3afbbbb93e455092a4bc43be2e9b820a1ae8` |
| `pre_portfolio_hypothesis_binding_digest` | `6b2a74392eda2bf1a672682aa27da3873bc25666c5d9bb34d269f785afc2b438` |
| `GO_TOKEN` | `GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_SCORE_AND_RANKING_CONTRACT_IMPLEMENTATION_V0` |

## Score Contract

| Feld | Wert |
|------|------|
| `score_formula_version` | `pairwise_spillover_graph_v1` |
| `leader_feature` | lagged log return (`L=8`, `signal_lag=1`) |
| `follower_target` | strictly future log return (`forward_lag=1`) |
| `pair_score` | `leader_lagged_return_i * follower_future_return_j` |
| `self_pairs` | forbidden |
| `panel_median_benchmark` | forbidden |

## Ranking Contract

| Feld | Wert |
|------|------|
| `primary_ranking_entity` | `directed_pair` |
| `secondary_ranking_entity` | `instrument_net_inbound_spillover` |
| `pair_ranking_formula` | `rank_directed_pairwise_spillover_by_strength_desc_v1` |
| `instrument_ranking_formula` | `rank_instruments_by_net_inbound_spillover_desc_v1` |
| `pair_tie_break` | `score_desc_then_leader_id_asc_then_follower_id_asc` |
| `instrument_tie_break` | `score_desc_then_instrument_id_asc` |
| `tie_break_score_source` | `unrounded_internal_score` |

## Portfolio Binding Status

Alle fünf Portfolio-Policy-Felder sind `BOUND` via
`CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_PORTFOLIO_BINDING_IMPLEMENTATION_V0`.

## Next Admissible Scope

## Canonical Owners

| Surface | Owner |
|---------|-------|
| Score computation | `src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_v0.py` |
| Contract validator/binder | `src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0.py` |
| Portfolio binding | `src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_v0.py` |
| Materializer | `scripts/research/materialize_cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0.py` |
| Config | `config/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0.json` |
| Tests | `tests/research/test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0_contract.py` |
| Hypothesis binding | `src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0.py` |

## Next Admissible Scope

`GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0`
