# Trend Following v2 — Canonical Wiring Map

**Rolle:** Repo-abgeleitete technische Implementierungsmap für den Recovery-Pfad `TREND_FOLLOWING_V2_MANDATORY_BOUNDARY_STATE_FILE_BINDING_REWIRE`.  
**Keine zweite Trading-SSOT.** Normative Parent-SSOT: [`PEAK_TRADE_IMPLEMENTATION_CONTRACT.md`](../governance/PEAK_TRADE_IMPLEMENTATION_CONTRACT.md) → Vollautonomie-Runbook v4.4.11.

Maschinenlesbare Map: [`trend_following_v2_canonical_wiring_v0.json`](trend_following_v2_canonical_wiring_v0.json)

## A. Zielzustand der vollständigen Kette

```text
Canonical Market Context
→ Scope Initialization
→ Deterministic Scope Event Generator
→ Bull Assessment
→ Bear Assessment
→ Directional State Switch
→ Survival
→ Suitability
→ Double Play
→ Entry / Position Management / Exit / Reversal
→ Capital Envelope
→ Pre-Sizing Risk
→ Canonical Position Sizing
→ Post-Sizing Risk
→ Canonical Order Intent Boundary
→ Safety Kernel Boundary
→ KillSwitch Boundary
→ Reconciliation / Unknown Outcome Boundary
→ Economic Validation
→ Promotion-Admissibility Boundary
→ Observability / AI / Feedback Boundary
```

## B. Produktive Trend-Following-v2-Kette (offline)

```text
config/ops/trend_following_v2_economic_evaluation_v1.json
→ build_sparse_signal_runtime_step31f_config_v0
→ build_runtime_step31f_config_v0 (+ mandatory binding overlay)
→ _run_candidate_with_runtime_config_v0
→ build_economic_viability_evidence_v1
→ run_mv2_research_backtest_wiring_v1
→ integrated_offline_trading_logic_replay_v1
→ mandatory boundary gates (capital/risk/sizing → order intent → safety → killswitch → reconciliation)
→ economic evidence materialization
```

## C. Mandatory Boundary Binding

Section key: `mv2_research_backtest_mandatory_boundary_state_file_binding_v0`

Referenz-Contract (Parität, keine Strategy-/Universe-Übernahme):

`config/ops/cross_sectional_futures_lead_lag_information_diffusion_v0_economic_evaluation_v1.json`

State-File-Root: `config/research/mv2_backtest_mandatory_boundary_state_files_v0/`

| Subdomain | State file | Digest ref |
|-----------|------------|------------|
| capital_risk_sizing | capital_risk_sizing.json | 82a8b8ae…728a7 |
| canonical_order_intent | canonical_order_intent.json | 3fc5a99c…06b5 |
| safety_kernel | safety_kernel.json | 21e11676…d30b |
| killswitch | killswitch.json | e8acdea6…9aeb |
| reconciliation | reconciliation.json | 3475daed…0caf |

Resolver-Owner: `src/research/cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0.py`

## D. Bestätigte Root Cause (pre-rewire)

Binding fehlte in `trend_following_v2_economic_evaluation_v1.json` und wurde nicht durch die Materializer-/Evidence-Kette propagiert. Produktive Boundary-Aufrufzahlen waren 0 (Audit Evidence 20260715T135331Z).

## E. Post-Rewire Nachweis

Bounded Single-Member E2E (RVN, 240 bars): `tests/research/test_trend_following_v2_mandatory_boundary_state_file_binding_rewire_v0.py`

Alle fünf mandatory Gates müssen `call_count > 0` haben. Fail-Closed bei fehlender Binding-Section oder ungültigem State-File.

## F. Definition of Done

Siehe `definition_of_done` in der JSON-Map. Post-Merge-Reaudit und Post-Repair-Baseline-Economic-Reevaluation sind abgeschlossen (`PASS` bzw. terminal `FAIL`). Recovery-Pfad: `COMPLETE_WITH_ECONOMIC_FAIL`; `CURRENT_PHASE=TERMINAL_ECONOMIC_FAIL_CLOSEOUT`; `NEXT_ADMISSIBLE_SCOPE=NONE_WITHOUT_NEW_OPERATOR_RATIFICATION`.

## G. Verbote

Keine Strategy-Parameter-, Signal-, Dataset-, Kosten-, Risk-/Sizing- oder Safety-Semantikänderung. Kein neuer Backtest- oder Boundary-Gate-Owner. Keine Runtime- oder Authority-Wirkung.
