# Trade Ledger and Equity Curve Evidence Class Scope v0

---
docs_token: DOCS_TOKEN_TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_SCOPE_V0
STATUS: SCOPE_DEFINED_NOT_EXECUTED
scope: governance, documentation-only, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
---

> **Non-authorizing:** Definiert ausschließlich den Governance-/Evidence-Class-Scope für persistierte Trade-Ledger- und Equity-Curve-Artefakte bei zukünftigen Evaluationen. Keine Evaluation, keine Execution, keine Runtime, keine Promotion, kein Same-Binding-Retry, kein Ergebnis-Rescue.

## A. Verdict

| Feld | Wert |
|---|---|
| `VERDICT` | `SCOPE_DEFINED_NOT_EXECUTED` |
| `PROCESS_CLASSIFICATION` | `TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_SCOPE_V0` |
| `SCOPE_CLASSIFICATION` | `GOVERNANCE_ONLY_TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_SCOPE_DEFINITION_NO_EXECUTION` |
| `GO_TOKEN` | `GO_TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_SCOPE_DEFINITION_PR_V0` |
| `EVIDENCE_CLASS_ID` | `TRADE_LEDGER_AND_EQUITY_CURVE_PERSISTENCE_V0` |
| `PARENT_PRIMARY_FAILURE_CLASS` | `NEGATIVE_RAW_EDGE` |
| `PRIMARY_FAILURE_CLASS_UNCHANGED` | `true` |
| `PARENT_TERMINAL_NEGATIVE_EVIDENCE_VERDICT` | `ROBUSTNESS_FAILED` |
| `TERMINAL_NEGATIVE_EVIDENCE_UNCHANGED` | `true` |
| `EVALUATION_AUTHORIZED` | `false` |
| `ECONOMIC_EVALUATION_EXECUTED` | `false` |
| `PERSISTENCE_EXECUTION_AUTHORIZED` | `false` |
| `PERSISTENCE_EXECUTED` | `false` |
| `PROMOTION_AUTHORIZED` | `false` |
| `RUNTIME_AUTHORITY` | `false` |
| `RETRY_ALLOWED` | `false` |
| `SAME_BINDING_RETRY_ALLOWED` | `false` |
| `PARAMETER_OPTIMIZATION_ALLOWED` | `false` |
| `THRESHOLD_LOWERING_ALLOWED` | `false` |
| `RESULT_RESCUE_ALLOWED` | `false` |
| `REQUIRED_FUTURE_OPERATOR_GO` | `true` |
| `REPO_MUTATION_SCOPE` | `GOVERNANCE_ONLY` |
| `FUTURE_EXECUTION_SCOPE` | `PERSISTENCE_AT_EVALUATION_TIME_OR_SEPARATE_RATIFIED_SCOPE_ONLY` |
| `runtime_effect` | `NONE` |
| `authority_effect` | `NONE` |

**Authoritative owners (reuse, nicht ersetzen):**

- Scope config: `config/research/trade_ledger_equity_curve_evidence_class_scope_v0.json`
- Parent materialization execution: `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/okx_full_panel_cross_sectional_ranking_trade_level_artifact_materialization_evidence_execution_read_only_v0_20260705T072422Z`
- Progress registry: `docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md`

## B. Zweck

Diese Evidence-Klasse definiert **welche Trade-Level- und Equity-Curve-Artefakte und Felder zukünftige Evaluationen persistieren müssen**, damit spätere read-only/offline Diagnostik ohne Rerun, Recalculation oder Same-Binding-Retry belastbar möglich ist.

Die Scope-Definition schließt die Lücke, die die Trade-Level Artifact Materialization (20260705T072422Z) offengelegt hat: Aggregatmetriken allein reichen nicht für Tail-, Side-, Regime-, Funding-, Drawdown-Cluster- oder Turnover-Diagnose.

## C. Hintergrund — Materialization 20260705T072422Z

| Befund | Wert |
|---|---|
| Materialization VERDICT | `TRADE_LEVEL_MATERIALIZATION_COMPLETE — INCONCLUSIVE_FIELDS_PERSIST — PRIMARY_FAILURE_UNCHANGED` |
| Primary Failure Class | `NEGATIVE_RAW_EDGE` (unchanged, terminal) |
| gross≈net | -97.53% |
| profit_factor | 0.805 |
| net_expectancy | -5.64 |
| trade_count | 812 |
| TRADE_LEDGER_V1 in source | **absent** |
| EQUITY_CURVE_V1 in source | **absent** |

**Weiterhin INCONCLUSIVE wegen fehlender Persistierung:**

- Side / Long-Short-Asymmetrie
- Regime / Bucket-Konzentration
- Instrument-Konzentration
- Tail-Loss / Outlier-Cluster
- Turnover-Verteilung
- Funding-Attribution
- Intraperiod / Cluster / Trade-Level Drawdown-Pfad

**Source-Bundle-Referenz:**

`/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/okx_full_panel_cross_sectional_ranking_trade_level_artifact_materialization_evidence_execution_read_only_v0_20260705T072422Z` (MANIFEST_VERIFY_RC=0)

## D. Problemstatement

Aggregatmetriken (`net_return`, `profit_factor`, `net_expectancy`, `trade_count`, Portfolio-`max_drawdown`) erlauben keine belastbare Attribution auf:

- breite kleine Verluste vs. wenige Tail-Losses
- Long/Short-Asymmetrie
- Regime-/Bucket-Konzentration
- per-Instrument-Konzentration
- Funding-Drag pro Trade
- Turnover-Verteilung und Overtrading
- intraperiod / cluster / trade-level Drawdown-Pfade

Ohne persistierte `TRADE_LEDGER_V1` und `EQUITY_CURVE_V1` bleiben diese Dimensionen **INCONCLUSIVE**, auch bei read-only Materialisierung aus vorhandenen Bundles.

## E. Verbotene Interpretationen

| Interpretation | Status |
|---|---|
| Scope definition = Evaluation authorization | **FORBIDDEN** |
| Ledger persistence = Result rescue | **FORBIDDEN** |
| Equity curve persistence = Economic pass | **FORBIDDEN** |
| Diagnostics completeness = Promotion eligibility | **FORBIDDEN** |
| Evidence readiness = Runtime authority | **FORBIDDEN** |

Primary Failure Class `NEGATIVE_RAW_EDGE` bleibt terminale negative Evidence unabhängig von späterer Ledger-Persistierung.

## F. Pflichtartefakte (bei zukünftiger Evaluation-Persistierung)

| Artefakt | Zweck |
|---|---|
| `TRADE_LEDGER_V1.jsonl` | Vollständiges per-Trade-Ledger |
| `TRADE_LEDGER_V1.schema.json` | Maschinenlesbares Schema für Trade-Ledger |
| `EQUITY_CURVE_V1.jsonl` | Equity-/Drawdown-Pfad über Zeit |
| `EQUITY_CURVE_V1.schema.json` | Maschinenlesbares Schema für Equity-Curve |
| `TRADE_LEDGER_SUMMARY_V1.json` | Aggregate Summary über Ledger |
| `EQUITY_CURVE_SUMMARY_V1.json` | Aggregate Summary über Equity-Pfad |
| `FIELD_COMPLETENESS_REPORT_V1.json` | Fail-closed Feld-Vollständigkeitsbericht |
| `MANIFEST.sha256` | Bundle-Integrität |

## G. Mindestfelder TRADE_LEDGER_V1

| Feld | Beschreibung |
|---|---|
| `trade_id` | Eindeutige Trade-Identifikation |
| `evaluation_id` | Evaluation-Run-Identifikation |
| `candidate_id` | Kandidaten-Identifikation |
| `strategy_id` | Strategie-Identifikation |
| `strategy_version` | Strategie-Version |
| `instrument_id` | Instrument |
| `venue` | Handelsplatz |
| `market_type` | `futures` (Pflichtwert) |
| `side` | Long/Short |
| `entry_time` | Entry-Zeitpunkt |
| `exit_time` | Exit-Zeitpunkt |
| `entry_price` | Entry-Preis |
| `exit_price` | Exit-Preis |
| `quantity` | Positionsgröße |
| `notional` | Notional |
| `gross_pnl` | Brutto-PnL |
| `fees` | Gebühren |
| `slippage` | Slippage |
| `funding` | Funding |
| `net_pnl` | Netto-PnL |
| `return_bps` | Return in Basispunkten |
| `holding_period_seconds` | Haltedauer |
| `entry_reason_codes` | Entry-Begründung |
| `exit_reason_codes` | Exit-Begründung |
| `signal_bucket` | Signal-Bucket |
| `ranking_score` | Ranking-Score |
| `regime_label` | Regime-Label |
| `walk_forward_split_id` | Walk-Forward-Split |
| `data_period_id` | Datenperiode |
| `parameter_binding_id` | Parameter-Binding |
| `fee_model_binding_id` | Fee-Model-Binding |
| `slippage_model_binding_id` | Slippage-Model-Binding |
| `funding_model_binding_id` | Funding-Model-Binding |
| `execution_model_binding_id` | Execution-Model-Binding |
| `equity_before` | Equity vor Trade |
| `equity_after` | Equity nach Trade |
| `drawdown_after_trade` | Drawdown nach Trade |
| `input_digest` | Input-Digest |
| `config_digest` | Config-Digest |
| `implementation_digest` | Implementation-Digest |

## H. Mindestfelder EQUITY_CURVE_V1

| Feld | Beschreibung |
|---|---|
| `timestamp` | Zeitstempel |
| `evaluation_id` | Evaluation-Run-Identifikation |
| `candidate_id` | Kandidaten-Identifikation |
| `instrument_id_or_universe` | Instrument oder Universum |
| `equity` | Equity |
| `cash` | Cash |
| `unrealized_pnl` | Unrealisierter PnL |
| `realized_pnl` | Realisierter PnL |
| `cumulative_fees` | Kumulierte Gebühren |
| `cumulative_slippage` | Kumulierte Slippage |
| `cumulative_funding` | Kumuliertes Funding |
| `drawdown` | Drawdown (absolut) |
| `drawdown_pct` | Drawdown (prozentual) |
| `exposure_notional` | Exposure Notional |
| `position_count` | Positionsanzahl |
| `active_side_count` | Aktive Seiten |
| `walk_forward_split_id` | Walk-Forward-Split |
| `regime_label` | Regime-Label |
| `data_quality_status` | Datenqualitätsstatus |
| `input_digest` | Input-Digest |

## I. Fail-closed-Regeln

| Fehlendes Feld | Fail-closed-Klassifikation |
|---|---|
| per-trade `net_pnl` | `TRADE_LEDGER_INVALID` |
| `side` | `LONG_SHORT_BREAKDOWN_INCONCLUSIVE` |
| `regime_label` | `REGIME_BREAKDOWN_INCONCLUSIVE` |
| `funding` | `FUNDING_ATTRIBUTION_INCONCLUSIVE` |
| equity path (EQUITY_CURVE_V1) | `DRAWDOWN_PATH_INCONCLUSIVE` |
| `instrument_id` | `INSTRUMENT_CONCENTRATION_INCONCLUSIVE` |
| `ranking_score` / `signal_bucket` | `SIGNAL_BUCKET_ATTRIBUTION_INCONCLUSIVE` |

Fehlende Felder dürfen nicht geschätzt oder interpoliert werden.

## J. Zulässige zukünftige Nutzung

- Persistierung bei separat ratifizierter Evaluation-Scope-Execution
- Read-only/offline Diagnostics aus persistierten Ledger-/Equity-Curve-Bundles
- Fail-closed Feld-Vollständigkeitsprüfung vor Diagnostics

## K. Nicht zulässige Nutzung

- Promotion oder Runtime-Authority
- Threshold-Absenkung oder Parameter-Optimierung
- Same-Binding-Retry der PR #4852 Economic Evaluation
- Result-Rescue oder Umdeutung terminal negativer Evidence
- Trading- oder Optimierungsempfehlungen aus Ledger-Daten

## L. Harte Boundaries

| Boundary | Status |
|---|---|
| NO_EVALUATION_IN_THIS_PR | `true` |
| NO_PERSISTENCE_EXECUTION_IN_THIS_PR | `true` |
| NO_BACKTEST_RERUN_IN_THIS_PR | `true` |
| NO_SIGNAL_RECALCULATION_IN_THIS_PR | `true` |
| NO_SAME_BINDING_RETRY | `true` |
| NO_PARAMETER_OPTIMIZATION | `true` |
| NO_THRESHOLD_LOWERING | `true` |
| NO_RESULT_RESCUE | `true` |
| NO_PROMOTION | `true` |
| NO_RUNTIME | `true` |
| NO_SHADOW / NO_PAPER / NO_TESTNET | `true` |
| NO_SCHEDULER / NO_ADAPTER_SUBMISSION | `true` |
| NO_ORDERS / NO_CREDENTIALS / NO_ARMING / NO_LIVE | `true` |
| NO_CORE_SYSTEM_CHANGE | `true` |
| NO_CANONICAL_TRADING_LOGIC_CHANGE | `true` |

## M. Safe Next Action

```text
NEXT_ACTION=NO_RUNTIME_OR_PROMOTION_ACTION
FUTURE_PERSISTENCE=REQUIRES_SEPARATE_OPERATOR_GO_AND_RATIFIED_EVALUATION_SCOPE_WITH_LEDGER_EQUITY_CURVE_PERSISTENCE
```

Keine Evaluation in diesem Scope. Keine Persistierung in diesem Scope. Separates explizites Operator-GO erforderlich für jede zukünftige Persistierungsausführung. Primary Failure Class `NEGATIVE_RAW_EDGE` bleibt unverändert terminal.
