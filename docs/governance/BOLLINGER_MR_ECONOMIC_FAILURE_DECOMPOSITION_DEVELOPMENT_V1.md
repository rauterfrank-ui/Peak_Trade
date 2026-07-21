# Bollinger/MR Economic Failure Decomposition (DEVELOPMENT_ONLY) v1

---
docs_token: DOCS_TOKEN_BOLLINGER_MR_ECONOMIC_FAILURE_DECOMPOSITION_DEVELOPMENT_V1
STATUS: FAILURE_DECOMPOSITION_EXECUTION_COMPLETE
scope: research, offline-only, non-authorizing, diagnostic-only
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Read-only economic failure decomposition of the immutable Bollinger/MR baseline on the sealed `DEVELOPMENT_ONLY` panel. No new trading hypothesis, no holdout access, no parameter tuning, no Economic/Promotion gate open, no Master-V2 / Double-Play / risk / sizing / execution mutation.

## A. Verdict fields

| Feld | Wert |
|---|---|
| `SCOPE_ID` | `bollinger_mr_economic_failure_decomposition_development_v1` |
| `EXECUTION_ID` | `BOLLINGER_MR_ECONOMIC_FAILURE_DECOMPOSITION_DEVELOPMENT_EXECUTION_V1` |
| `EVIDENCE_CLASS_ID` | `BOLLINGER_MR_ECONOMIC_FAILURE_DECOMPOSITION_DEVELOPMENT_EVIDENCE_V1` |
| `DIAGNOSTIC_CLASS` | `COSTS_DESTROY_MARGINAL_EDGE` |
| `DATASET_ID` | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1` |
| `DATASET_CLASS` | `DEVELOPMENT_ONLY` |
| `BASELINE_CONFIG_ID` | `bollinger_bands_v2_full_canonical_system_economic_binding_v1` |
| `AUTHORITY_EFFECT` | `NONE` |
| `RUNTIME_EFFECT` | `NONE` |
| `ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` | `false` |
| `PROMOTION_ELIGIBLE` | `false` |
| `HOLDOUT_ACCESS_AUTHORIZED` | `false` |
| `NEW_HYPOTHESIS_AUTHORIZED` | `false` |

## B. Purpose

Diagnose *why* the existing Bollinger/MR economic evaluation fails on the sealed development panel by decomposing already-canonical signals, decisions, fills, and trade-ledger economics into:

- trade_count, gross/net pnl, fees, slippage
- gross/net profit factor
- per-trade MFE/MAE, capture ratio, MFE-to-exit leakage, holding period
- LONG/SHORT and instrument attribution
- cost stress at 0.5x / 1.0x / 1.5x / 2.0x canonical costs

Classification is exclusive to one of:

- `ENTRY_HAS_NO_GROSS_EDGE`
- `ENTRY_EDGE_LOST_AT_EXIT`
- `SHORT_SIDE_STRUCTURAL_DRAG`
- `COSTS_DESTROY_MARGINAL_EDGE`
- `INSTRUMENT_CONCENTRATION_ONLY`
- `MIXED_OR_INCONCLUSIVE`

No action recommendation and no new hypothesis are authorized in this scope. At most one `NEXT_RESEARCH_QUESTION` may be recorded in the open backlog without preregistration.

## C. Canonical owners (reuse-before-new)

- Config: `config/research/bollinger_mr_economic_failure_decomposition_development_v1.json`
- Package: `src/research/bollinger_mr_economic_failure_decomposition_development_v1/`
- Runner: `scripts/research/run_bollinger_mr_economic_failure_decomposition_development_v1.py`
- Evidence: `docs/evidence/bollinger_mr_economic_failure_decomposition_development_v1/`
- Dev panel loader: `src/research/entry_effective_mr_eligibility_development_evaluation_v1/dev_panel_bars_v1.py`
- Portfolio equity helper (import-only): `src/research/regime_gated_standaside_mr_development_evaluation_v1/shared_portfolio_equity_research_v1.py`
- Parent baseline evidence: `docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_development_v1/`
- Immutable baseline binding: `config/research/bollinger_bands_v2_full_canonical_system_economic_binding_v1.json`

## D. Explicit non-actions

- No holdout access or holdout rerun
- No new entry-eligibility filter
- No parameter tuning / instrument cherry-picking
- No Economic or Promotion gate open
- No runtime / shadow / paper / testnet / scheduler / orders
- No Master V2, Double-Play, risk, sizing, or execution semantic change
