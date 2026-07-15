# Cross-Sectional Futures Pairwise Lead-Lag Spillover V1 Offline Economic Evaluation Authorization Ratification V0

> **Authorization-only:** Reratifiziert die offline-only Autorisierung für eine spätere separate Economic Evaluation von `cross_sectional_futures_pairwise_lead_lag_spillover/v1` auf die nach PR #5204 vollständig materialisierte Portfolio-Binding-Identität. Keine Evaluation-Ausführung, keine Hypothesis-/Score-/Ranking-Mutation, keine Runtime, keine Promotion.

## Scope

| Feld | Wert |
|------|------|
| `scope_id` | `cross_sectional_futures_pairwise_lead_lag_spillover/v1` |
| `authorization_scope` | `OFFLINE_ECONOMIC_EVALUATION` |
| `authorization_version` | `v0` |
| `operator_go` | `GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_UPDATED_AUTHORIZATION_RATIFICATION_V0` |
| `previous_operator_go` | `GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_RATIFICATION_V0` |
| `supersession_mode` | `PORTFOLIO_BINDING_COMPLETION_SUPERSESSION_V0` |
| `binding_classification` | `PORTFOLIO_BINDING_COMPLETION_V0` |

## Authorization Binding Identity

| Feld | Digest |
|------|--------|
| `authorization_binding_digest` (neu) | `a531051eb8a4f414fea42aef9bed3afbbbb93e455092a4bc43be2e9b820a1ae8` |
| `superseded_authorization_binding_digest` | `6b2a74392eda2bf1a672682aa27da3873bc25666c5d9bb34d269f785afc2b438` |

## Unveränderte kanonische Referenzen

| Referenz | Digest / Status |
|----------|-----------------|
| Score-and-Ranking Contract | `900410cfe2812b910c086942e123ff15ca8054a6069b0b39982ccdbec00e2ddd` |
| Dataset | `79b1c977960f4af7e1eb54580738d77b259b74f7f02bbf0e999afbb95f8f09f1` |
| Universe | `d57738dc7e80520c17e49c406a22f8de15216c2e48e56d91b3757359ebb552a1` |
| Portfolio Binding | vollständig gebunden (PR #5204) |

## Fail-Closed Grenzen

| Flag | Wert |
|------|------|
| `OFFLINE_ONLY` | `true` |
| `ECONOMIC_EVALUATION_AUTHORIZED_FOR_SEPARATE_EXECUTION` | `true` |
| `ECONOMIC_EVALUATION_EXECUTED` | `false` |
| `HYPOTHESIS_BINDING_UNCHANGED` | `true` |
| `SCORE_CONTRACT_UNCHANGED` | `true` |
| `RANKING_CONTRACT_UNCHANGED` | `true` |
| `PORTFOLIO_BINDING_UNCHANGED` | `true` |
| `PARAMETER_OPTIMIZATION_ALLOWED` | `false` |
| `THRESHOLD_REDUCTION_ALLOWED` | `false` |
| `POLICY_RESCUE_ALLOWED` | `false` |
| `RUNTIME_EFFECT` | `NONE` |
| `AUTHORITY_EFFECT` | `NONE` |
| `LIVE_AUTHORIZED` | `false` |
| `ORDERS_ALLOWED` | `false` |

## Canonical Owners

| Surface | Owner |
|---------|-------|
| Authorization ratification validator/binder | `src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0.py` |
| Materializer | `scripts/research/materialize_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0.py` |
| Config | `config/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0.json` |
| Tests | `tests/research/test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0_contract.py` |
| Portfolio binding (unchanged) | `src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_v0.py` |
| Hypothesis binding (unchanged) | `src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0.py` |
| Score/ranking contract (unchanged) | `src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0.py` |
| Offline evaluation entry point (deferred) | `scripts/ops/run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.py` (`PENDING_SEPARATE_EXECUTION_SCOPE`) <!-- pt:ref-target-ignore --> |

## Source Evidence

| Bundle | Pfad |
|--------|------|
| PR #5204 Merge Closeout | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/pr5204_merge_closeout_cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_implementation_v0_20260715T064015Z` |
| Hypothesis Binding Ratification | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_ratification_v0_20260715T040511Z` |
| Score-and-Ranking Contract | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0_20260715T041800Z` |
| PR #5200 Merge Closeout | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/pr5200_merge_closeout_cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_implementation_v0_20260715T044248Z` |

## Next Admissible Scope

`GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0`

Erfordert separates Operator-GO. Repair und Reevaluation bleiben getrennte Authority-Slices.
