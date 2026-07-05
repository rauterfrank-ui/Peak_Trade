# Trade Ledger and Equity Curve Persistence Offline Evaluation Execution v0

---
docs_token: DOCS_TOKEN_TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_EXECUTION_V0
STATUS: OFFLINE_EVALUATION_EXECUTION_COMPLETE
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Führt die bounded Offline-Evaluation mit gepinntem Binding aus PR #4859 aus und persistiert TRADE_LEDGER_V1.jsonl sowie EQUITY_CURVE_V1.jsonl ausschließlich im Durable Archive. Keine Runtime, keine Orders, keine Credentials, kein Arming, keine Promotion.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `PASS` |
| `PROCESS_CLASSIFICATION` | `TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_EXECUTION_V0` |
| `GO_TOKEN` | `GO_TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_EXECUTION_V0` |
| `GO_TOKEN_CONSUMED` | `true` |
| `EVIDENCE_CLASS_ID` | `TRADE_LEDGER_AND_EQUITY_CURVE_PERSISTENCE_V0` |
| `PRIMARY_FAILURE_CLASS` | `NEGATIVE_RAW_EDGE` |
| `PRIMARY_FAILURE_CLASS_UNCHANGED` | `true` |
| `CANDIDATE_EVIDENCE_STATUS` | `ROBUSTNESS_FAILED` |
| `OFFLINE_ONLY` | `true` |
| `AUTHORITY_EFFECT` | `NONE` |
| `RUNTIME_AUTHORIZED` | `false` |
| `ORDERS_ALLOWED` | `false` |
| `CREDENTIALS_REQUIRED` | `false` |
| `NO_OUTPUT_JSONL_MATERIALIZED_IN_REPO` | `true` |

## B. Binding

| Feld | Wert |
|---|---|
| `BINDING_CONFIG` | `config/research/trade_ledger_equity_curve_execution_binding_materialization_v0.json` |
| `strategy_binding_ref` | `trend_following&#47;v1` |
| `strategy_binding_digest` | `ea3bde558a2ffd903ed7b7f678cb0cf0a8a4b1f1bb7f5978f7b5bc8f69ab8478` |
| `ORIGIN_MAIN_SHA` | `5e86ed8e0ab21c42fbbd97c8510d58e74db263ec` |

## C. Durable Evidence Bundle

| Feld | Wert |
|---|---|
| `DURABLE_BUNDLE_PATH` | `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0_20260705T083113Z` |
| `MANIFEST_VERIFY_RC` | `0` |
| `TRADE_LEDGER_V1.jsonl` | Durable archive only (nicht im Repo) |
| `EQUITY_CURVE_V1.jsonl` | Durable archive only (nicht im Repo) |
| `TRADE_COUNT` | `219` |
| `EQUITY_POINT_COUNT` | `19809` |

## D. Metrics Summary

| Metrik | Wert |
|---|---|
| `gross_return` | `-0.002398` |
| `net_return` | `-0.002398` |
| `net_expectancy` | `-0.109486` |
| `profit_factor` | `0.950837` |
| `sharpe` | `-0.132181` |
| `max_drawdown` | `-0.009945` |
| `evidence_status` | `ROBUSTNESS_FAILED` |

## E. Boundary

- NO_RUNTIME / NO_SHADOW / NO_PAPER / NO_TESTNET / NO_SCHEDULER / NO_ORDERS / NO_CREDENTIALS / NO_ARMING
- NO_PROMOTION / NO_SAME_BINDING_RETRY / NO_PARAMETER_OPTIMIZATION
- Primary Failure Class `NEGATIVE_RAW_EDGE` bleibt unverändert
- Persistierte Ledger-Diagnostics erzeugen keine Trading Eligibility oder Promotion Authority

## F. Next Action Recommendation

`NO_RUNTIME_OR_PROMOTION_ACTION` — keine weiteren Schritte ohne separaten, explizit ratifizierten Scope und Operator-GO.
