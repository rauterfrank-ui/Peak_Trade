# Peak Trade — Kanonisches Vollautonomie-Runbook v4.4
## Core-System-Konsistenz, Reuse-First-Integration & Economic Viability

**Status:** Kanonisches strategisches und operatives Implementierungsrunbook
**Version:** 4.4
**Stand:** 3. Juli 2026
**Operator:** Frank Rauter
**Systemziel:** Vollautonomes, futures-only Peak-Trade-System mit deterministischer, konsistenter und auditierbarer Handelslogik; realistischer Profitabilitätsvalidierung; unabhängiger Safety Authority; gefenceter Single-Writer-Runtime; vollständiger Reconciliation; sicherer Restart-/Recovery-Semantik und einer durchgängigen Research→Validation→Promotion→Runtime→Feedback-Kette.
**Keine Anlageberatung.**

---

# 0. Zweck dieser Version

Dieses Runbook konsolidiert:

1. die vollständige Zielsemantik aus Runbook v4.3,
2. den realen Repo-Ist-Zustand aus dem systemweiten Multi-Agent-Audit,
3. die bestätigte Reuse-First-Strategie,
4. die Notwendigkeit belastbarer Economic-Viability-Evidence,
5. die korrigierte Implementierungsreihenfolge,
6. die klare Trennung zwischen vorhandener Capability, tatsächlicher Verdrahtung und nachgewiesener Profitabilität.

Diese Version ersetzt nicht die vorhandene Master-V2-, Backtest-, Monte-Carlo-, Walk-Forward-, Portfolio-, Safety- oder Evidence-Infrastruktur.

Sie definiert, wie die vorhandenen Komponenten ohne parallele SSOTs in eine kanonische, wirtschaftlich prüfbare Gesamtkette überführt werden.

---

# 0.1 Zentrale Entscheidung

```text
PEAK_TRADE_REBUILD_REQUIRED=false
REUSE_FIRST=true
GREENFIELD_ECONOMIC_VALIDATION_STACK_ALLOWED=false
PARALLEL_TRADING_SSOT_ALLOWED=false
PARALLEL_PROFITABILITY_SSOT_ALLOWED=false
```

Der aktuelle Peak-Trade-Stack enthält bereits:

- Master-V2-/Double-Play-Pure-Stack,
- Backtest Engine,
- Walk-Forward,
- Monte Carlo,
- Stress-Tests,
- Portfolio-Backtests,
- Performance-Metriken,
- Strategy Profiles,
- SafetyGuard,
- KillSwitch,
- Reconciliation,
- Evidence- und Manifest-Infrastruktur.

Die bestätigten Lücken sind primär:

- semantische Completion,
- fehlende kanonische Wiring-Pfade,
- Research-/Runtime-Drift,
- parallele Owner,
- fehlende persistierte Netto-Performance-Evidence,
- fehlende technische Profitabilitäts-/Robustness-Gates in Promotion.

---

# 0.2 Normative Begriffe

```text
MUST
→ zwingend; Nichterfüllung blockiert den Schritt

MUST_NOT
→ verboten

SHOULD
→ Standard; Abweichung nur mit dokumentierter Begründung und Evidence

MAY
→ optionale Erweiterung ohne Authority- oder Semantikänderung
```

---

# 0.3 Runbook-Hierarchie

```text
PART_I_CONSTITUTION
PART_II_CANONICAL_TRADING_LOGIC
PART_III_ECONOMIC_VALIDITY_AND_RESEARCH_INTEGRATION
PART_IV_RUNTIME_SAFETY_AND_EXECUTION
PART_V_IMPLEMENTATION_AND_VALIDATION_LADDER
PART_VI_OPERATIONAL_AUTONOMY_AND_PRODUCTION
```

Konfliktrangfolge:

```text
CONSTITUTIONAL_SAFETY_INVARIANTS
> CANONICAL_TRADING_LOGIC_CONTRACTS
> ECONOMIC_VALIDITY_CONTRACTS
> RUNTIME_AUTHORITY_CONTRACTS
> IMPLEMENTATION_SEQUENCE
> NARRATIVE_GUIDANCE
```

---

# PART I — CONSTITUTION

# 1. Unveränderliche Systemgrenzen

```text
FUTURES_ONLY=true
BITCOIN_DIRECTION_ALLOWED=false
SPOT_ALLOWED=false
SYNTHETIC_SPOT_ALLOWED=false

PEAK_TRADE_CANONICAL_TRADING_SYSTEM=true
PEAK_TRADE_CANONICAL_TRADING_SYSTEM_SINGLE_SSOT=true
PEAK_TRADE_PARALLEL_TRADING_SYSTEM_ALLOWED=false

LIVE_AUTHORIZED=false
READY_FOR_OPERATOR_ARMING=false
ORDERS_ALLOWED=false
SCHEDULER_RUNTIME_ALLOWED=false

SHADOW_AUTHORIZED=false
PAPER_AUTHORIZED=false
TESTNET_AUTHORIZED=false
CANARY_AUTHORIZED=false
FULL_AUTONOMOUS_PRODUCTION_AUTHORIZED=false
```

Initiale spätere Canary-Limits:

```text
TOTAL_LIMIT_USD=500
ORDER_LIMIT_USD=25
DAILY_LOSS_LIMIT_USD=25
MAX_POSITIONS=1
MAX_ACTIVE_DIRECTIONAL_SIDE=1
SIMULTANEOUS_LONG_SHORT_EXPOSURE_ALLOWED=false
```

Kein autonomer Prozess darf diese Grenzen erhöhen.

---

# 2. Kanonische Authority-Domänen

```text
CANONICAL_PEAK_TRADE_SYSTEM
├── TRADING_DECISION_CORE
├── CAPITAL_RISK_AND_SIZING_CORE
├── ECONOMIC_VALIDATION_CORE
├── SAFETY_EXECUTION_RUNTIME_CORE
└── LEARNING_PROMOTION_CORE
```

## 2.1 Trading Decision Core

```text
Canonical Market Context
→ Scope Initialization
→ Scope Event Generation
→ Bull/Bear Assessment
→ State Switch
→ Survival
→ Suitability
→ Double Play
→ Canonical Trading Decision
```

## 2.2 Capital, Risk und Sizing Core

```text
Canonical Trading Decision
→ Scope Capital Envelope
→ Pre-Sizing Risk
→ Canonical Position Sizing
→ Post-Sizing Risk
→ Canonical Order Intent
```

## 2.3 Economic Validation Core

```text
Canonical Trading Decision Path
→ Backtest Execution Model
→ Costs
→ Walk-Forward
→ Monte Carlo
→ Stress
→ Portfolio/Regime Evaluation
→ Economic Viability Evidence
```

## 2.4 Safety, Execution und Runtime Core

```text
Canonical Order Intent
→ Safety Kernel
→ Runtime Eligibility
→ Authority Lease
→ Single-Use Permission
→ Submission
→ Venue
→ Reconciliation
→ Recovery
```

## 2.5 Learning und Promotion Core

```text
Admissible Economic Evidence
→ Candidate
→ Validation
→ Promotion Decision
→ Deploy Inactive
→ Runtime Eligibility
```

Keine Domain darf ihre eigene Kontrollinstanz überschreiben.

---

# 3. Grundsatz: technische Korrektheit und wirtschaftliche Gültigkeit

Peak Trade benötigt zwei unabhängige Gates:

```text
SYSTEM_CORRECTNESS_GATE
ECONOMIC_VALIDITY_GATE
```

## 3.1 System Correctness

Prüft:

- Determinismus,
- State- und Authority-Semantik,
- Safety,
- Reconciliation,
- Recovery,
- Runtime-Integrität.

## 3.2 Economic Validity

Prüft:

- Netto-Erwartungswert,
- Kostenrealismus,
- Out-of-Sample-Stabilität,
- Walk-Forward,
- Monte Carlo,
- Stress,
- Regime-Stabilität,
- Drawdown,
- Portfolio-Beitrag,
- Reproduzierbarkeit.

## 3.3 Zusammenführung

```text
SYSTEM_CORRECTNESS_PASS
AND ECONOMIC_VALIDITY_PASS
→ eligible_for_shadow_candidate
```

Weder ein grüner Backtest noch ein grüner Safety-Test genügt allein.

---

# PART II — CANONICAL TRADING LOGIC

# 4. Verbindliches Systemziel

Peak Trade bewertet einen ausgewählten Futures-Kontrakt mit zwei spezialisierten Richtungs-Layern:

```text
Bull-/Long-Layer
Bear-/Short-Layer
```

Beide gehören zu einem einzigen kanonischen Trading-System.

Master V2 und Double Play koordinieren die Seiten.

Nur eine Seite darf Directional Exposure besitzen.

---

# 5. Orthogonales Zustandsmodell

Jeder Runtime- und Decision-Snapshot führt mindestens:

```text
direction_state
trading_gate
position_state
execution_state
reconciliation_state
safety_mode
authority_state
data_integrity_state
economic_validation_state
```

Beispiel:

```text
direction_state=LONG_SELECTED
trading_gate=BLOCKED
position_state=OPEN_REDUCING
execution_state=PARTIALLY_FILLED
reconciliation_state=PARTIAL
safety_mode=NO_NEW_POSITIONS
authority_state=EXIT_ONLY
data_integrity_state=TRUSTED
economic_validation_state=NOT_APPLICABLE_RUNTIME
```

---

# 6. Kanonische Richtungszustände

```text
NEUTRAL_OBSERVE

LONG_ARMED
LONG_SELECTED

SHORT_ARMED
SHORT_SELECTED

SWITCH_LONG_TO_SHORT_PENDING
SWITCH_SHORT_TO_LONG_PENDING

CHOP_GUARD_BLOCK
```

`LONG_SELECTED` und `SHORT_SELECTED` bedeuten ausschließlich fachliche Richtungswahl.

Sie implizieren nicht:

- Order Submission,
- Fill,
- Position,
- Trading Authority,
- offenen Trading Gate.

---

# 7. Reversal- und Flat-Invariante

Verboten:

```text
LONG_SELECTED → SHORT_SELECTED
SHORT_SELECTED → LONG_SELECTED
```

Gegenseite erst nach:

```text
venue_position_quantity == 0
AND no_open_increase_orders
AND no_unresolved_reduce_orders
AND no_submission_unknown
AND order_snapshot_fresh
AND fill_snapshot_fresh
AND position_snapshot_fresh
AND intent_ledger_matches_venue
AND reconciliation_state == RECONCILED
```

```text
OPPOSITE_SIDE_REQUIRES_RECONCILED_FLAT=true
VENUE_FLAT_ALONE_SUFFICIENT=false
```

---

# 8. Canonical Market Context

Jeder Entscheidungszyklus beginnt mit genau einem immutable:

```text
CanonicalMarketContextV1
```

## 8.1 Pflichtfelder

```text
context_id
instrument_id
trading_epoch
market_event_time
decision_time
bar_interval
bar_finality_status
mark_price
index_price
best_bid
best_ask
spread
volume
open_interest
funding_rate
volatility_estimate
trend_feature_set
momentum_feature_set
liquidity_feature_set
market_structure_feature_set
data_integrity_status
clock_trust_status
warmup_status
feature_contract_version
input_digest
```

## 8.2 Preis- und Zeitregeln

```text
PRIMARY_DECISION_PRICE=VENUE_MARK_PRICE
EXECUTION_REFERENCE_PRICE=BEST_BID_ASK_OR_VENUE_MARKET_SNAPSHOT
LIQUIDATION_REFERENCE_PRICE=VENUE_DEFINED_MARK_OR_INDEX_PRICE

TRADING_DECISION_ON_UNFINALIZED_BAR_ALLOWED=false
SCOPE_CONFIRMATION_ON_UNFINALIZED_BAR_ALLOWED=false
OUT_OF_ORDER_MARKET_EVENT_ALLOWED=false
DUPLICATE_MARKET_EVENT_MUST_BE_IDEMPOTENT=true
```

Intrabar-Daten dürfen Risk, Integrity und Exit-Safety speisen, aber keine neue Entry- oder Reversal-Bestätigung erzeugen, solange keine separat ratifizierte Intrabar-Policy existiert.

## 8.3 Warmup

```text
WARMUP_REQUIRED
WARMUP_COMPLETE
WARMUP_INVALID
```

Solange Warmup nicht vollständig ist:

```text
NO_NEW_DIRECTIONAL_POSITION=true
NO_SCOPE_CONFIRMATION=true
OBSERVATION_AND_RECONCILIATION_ONLY=true
```

---

# 9. Canonical Scope Initialization

Scope-Zustände:

```text
SCOPE_UNINITIALIZED
SCOPE_WARMING_UP
SCOPE_VALID
SCOPE_STALE
SCOPE_INVALID
```

Initialisierung nur wenn:

```text
warmup_status == WARMUP_COMPLETE
AND data_integrity_status == TRUSTED
AND clock_trust_status == TRUSTED
AND required_window_complete
AND instrument_metadata_valid
```

Kanonische Initialisierung:

```text
reference_price = finalized_mark_price
initial_volatility_distance = volatility_estimate * reference_price
initial_scope_band = clamp(
    initial_volatility_distance,
    min_scope_band,
    max_scope_band
)

neutral_upper_boundary = reference_price + initial_scope_band
neutral_lower_boundary = reference_price - initial_scope_band
trailing_anchor = reference_price
```

Kein Codepfad darf implizite Default-Werte einsetzen.

---

# 10. Deterministic Scope Event Generator

Der Scope Event Generator ist ein eigener deterministischer Owner.

```text
SCOPE_EVENT_GENERATOR_ROLE=CANONICAL_SCOPE_EVENT_OWNER
```

## 10.1 Inputs

```text
CanonicalMarketContextV1
current_scope
current_direction_state
confirmation_state
cooldown_state
scope_policy
```

## 10.2 Outputs

```text
NOOP
UPSCOPE_CANDIDATE
UPSCOPE_CONFIRMED
DOWNSCOPE_CANDIDATE
DOWNSCOPE_CONFIRMED
ADVERSE_EXIT_CANDIDATE
CHOP_DETECTED
SCOPE_BLOCKED
```

## 10.3 Invarianten

```text
CURRENT_SCOPE_IS_IMMUTABLE_WITHIN_DECISION_CYCLE=true
NEXT_SCOPE_EFFECTIVE_NEXT_TRADING_EPOCH_ONLY=true
NO_SCOPE_EVENT_FROM_UNFINALIZED_DATA=true
NO_SCOPE_EVENT_FROM_UNTRUSTED_DATA=true
NO_SCOPE_EVENT_AUTHORITY_EFFECT=true
NO_SCOPE_EVENT_ORDER_EFFECT=true
```

## 10.4 Schwellen

```text
up_candidate_threshold = trailing_anchor + up_distance
adverse_exit_threshold = trailing_anchor - adverse_exit_distance
reversal_candidate_threshold = trailing_anchor - reversal_distance
```

Für Short gespiegelt.

Zwingend:

```text
0 < up_distance <= hard_max_scope_distance
0 < adverse_exit_distance <= hard_max_adverse_distance
0 < reversal_distance <= hard_max_reversal_distance
adverse_exit_distance <= reversal_distance
```

## 10.5 Confirmation

```text
confirmation_unit=FINALIZED_TRADING_EPOCH
candidate_count_requires_consecutive_epochs=true
candidate_reset_on_opposite_or_no_longer_true=true
candidate_count >= confirmation_epochs
→ CONFIRMED
```

---

# 11. Dynamic Scope

Dynamic Scope ist:

- Preis-/Strukturhülle,
- bounded,
- deterministisch,
- read-before-write.

Dynamic Scope ist nicht:

- Capital Allocation,
- Position Sizing,
- Trailing Stop,
- Exit Policy,
- Reversal Policy,
- KillSwitch,
- Runtime Authority.

Getrennt zu führen:

```text
trailing_anchor
scope_band
adverse_exit_threshold
reversal_candidate_threshold
reversal_confirmation_state
```

---

# 12. Bull- und Bear-Assessment

Beide Seiten erzeugen:

```text
DirectionalAssessmentV1
```

Pflichtfelder:

```text
assessment_id
side
instrument_id
trading_epoch
status
signal_strength
confidence
feature_refs
scope_event_ref
survival_preconditions
hard_block_reasons
reason_codes
valid_until_epoch
semantic_digest
```

Status:

```text
INVALID
BLOCKED
OBSERVE
CANDIDATE
CONFIRMED
```

Bull und Bear verwenden denselben Contract und dieselbe Auswertungsreihenfolge.

Pflichttest:

```text
price_path
→ mathematically mirrored price_path
→ structurally mirrored Bull/Bear outcome
```

---

# 13. Survival

Subchecks:

```text
DATA_COMPLETENESS_CHECK
COST_SURVIVAL_CHECK
VOLATILITY_SURVIVAL_CHECK
SEQUENCE_SURVIVAL_CHECK
DRAWDOWN_SURVIVAL_CHECK
LIQUIDATION_BUFFER_CHECK
```

Kostenmodell:

```text
expected_roundtrip_cost =
    entry_fee
  + expected_entry_slippage
  + exit_fee
  + expected_exit_slippage
  + expected_funding_cost

net_expected_edge = expected_gross_edge - expected_roundtrip_cost
```

Aggregation:

```text
ANY_HARD_FAIL → FAIL
ANY_REQUIRED_UNKNOWN → BLOCKED
ALL_REQUIRED_PASS → PASS
```

---

# 14. Suitability

Suitability bestimmt, welche bereits registrierte Strategie für Seite und Regime geeignet ist.

```text
NO_IMPLICIT_STRATEGY_SELECTION_BY_LIST_ORDER=true
NO_FALLBACK_STRATEGY=true
UNKNOWN_REGIME_BLOCKS_NEW_ENTRY=true
```

Mehrere passende Strategien benötigen eine versionierte Ranking Policy mit stabiler Tie-Break-Regel.

---

# 15. Double Play

Double Play:

- koordiniert Bull und Bear,
- löst Konflikte,
- konsumiert Survival und Suitability,
- erzeugt Canonical Trading Decision.

Double Play darf nicht:

- Orders senden,
- Risk duplizieren,
- Sizing duplizieren,
- KillSwitch resetten,
- Authority ausstellen,
- Reconciliation überschreiben.

Konfliktregel:

```text
BOTH_SIDES_CONFIRMED
→ CHOP_GUARD_BLOCK
→ NO_NEW_ENTRY
→ EXISTING_POSITION_MANAGEMENT_CONTINUES
```

---

# 16. Decision Precedence

```text
1. Safety / Authority Revocation
2. Hard Risk Reduction
3. Reconciliation Requirement
4. Mandatory Exit Policy
5. Existing Position Management
6. Reversal Processing
7. New Entry
8. Favorable Scope Trailing
9. Observation / No Action
```

Kanonische Outcomes:

```text
NO_ACTION
OBSERVE
HOLD
REDUCE
EXIT
ENTER_LONG
ENTER_SHORT
CANCEL_PENDING
RECONCILE_ONLY
BLOCKED
```

---

# 17. Entry-, Position-Management- und Exit-Policy

## 17.1 Entry Preconditions

```text
direction_state in {LONG_ARMED, SHORT_ARMED}
AND selected_assessment.status == CONFIRMED
AND survival.status == PASS
AND suitability.status == PASS
AND position_state == FLAT_RECONCILED
AND reconciliation_state == RECONCILED
AND trading_gate in {ENTRY_ALLOWED, INCREASE_ALLOWED}
AND safety_mode == NORMAL
AND data_integrity_state == TRUSTED
AND clock_trust_valid
AND cooldown_pass
```

## 17.2 Exit-Klassen

```text
SAFETY_EXIT
HARD_RISK_EXIT
ADVERSE_SCOPE_EXIT
PROFIT_PROTECTION_EXIT
TIME_EXIT
STRATEGY_INVALIDATION_EXIT
REVERSAL_PREPARATION_EXIT
```

## 17.3 Exit-Invariante

```text
reduce_only=true
quantity <= reconciled_open_position_quantity
position_flip_allowed=false
```

Ein Reversal erzeugt zuerst Exit und Reconciled-flat, niemals direkt eine Gegenorder.

---

# 18. Canonical Trading Decision

Output:

```text
CanonicalTradingDecisionEvidenceV1
```

Pflichtfelder:

```text
decision_id
instrument_id
trading_epoch
input_refs
current_scope_ref
next_scope_ref
scope_event
previous_side_state
next_side_state
bull_assessment
bear_assessment
survival_result
suitability_result
composition_result
decision_outcome
reason_codes
decision_precedence_trace
market_context_ref
selected_strategy_ref
entry_or_exit_policy_ref

execution_eligible=false
adapter_compatible=false
quantity_status=NOT_BOUND
authority_effect=NONE
runtime_effect=NONE
```

---

# PART III — ECONOMIC VALIDITY AND RESEARCH INTEGRATION

# 19. Audit-bestätigter Ist-Zustand

```text
PROFITABILITY_CAPABILITY_STATUS=TECHNICAL_CAPABILITY_PRESENT
ECONOMIC_VALIDITY_STATUS=ECONOMIC_VALIDITY_NOT_YET_PROVEN
RESEARCH_RUNTIME_DRIFT_STATUS=CANONICAL_RESEARCH_WIRING_COMPLETED
MONTE_CARLO_STATUS=TECHNICAL_CAPABILITY_PRESENT
WALK_FORWARD_STATUS=TECHNICAL_CAPABILITY_PRESENT
PORTFOLIO_BACKTEST_STATUS=TECHNICAL_CAPABILITY_PRESENT
PROMOTION_INTEGRATION_STATUS=ECONOMIC_GATE_BOUND_FAIL_CLOSED
DUPLICATE_OWNER_STATUS=CONSOLIDATION_GOVERNED
STEP29M_FLEET_STATUS=COMPLETE_NO_PASS
STEP30A_STATUS=COMPLETE_POLICY_FAIL
STEP29N_STATUS=COMPLETE_FAIL_CLOSED_BLOCKED
STEP29O_STATUS=COMPLETE_PASS
STEP29R_STATUS=PRECONDITION_ASSESSED_NOT_ADMISSIBLE
FINAL_RESEARCH_FLEET_BINDING_READY=true
FINAL_RESEARCH_FLEET_EVALUATION_COMPLETE=true
FINAL_RESEARCH_FLEET_STATUS=COMPLETE_NO_PASS
PASS_COUNT=0
FAIL_COUNT=3
PROMOTION_CANDIDATES=[]
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false
RUNTIME_REWIRE_ADMISSIBLE=false
```

Diese Werte bedeuten:

- Die technische Research- und Evidence-Capability ist vorhanden.
- Die bisher geprüften Bindings haben keine Economic Validity nachgewiesen.
- Runtime-Rewire und alle ausführungswirksamen Stufen bleiben blockiert.
- Negative Evidence ist terminal und darf nicht durch Governance- oder Policy-Änderung wegdefiniert werden.
- Weitere Research-Arbeit ist nur als versionierter, reproduzierbarer und offline-only Scope zulässig.
- Core-System und kanonische Handelslogik bleiben unverändert.

## 19.1 Terminale negative Economic Evidence

Manifest-verifizierte abgeschlossene Bindings:

| Binding | Net Return | Profit Factor | Trades | Primäre Failure-Klasse |
|---|---:|---:|---:|---|
| `macd&#47;v1-v3` | -2,33 % | 0,817 | 717 | `NEGATIVE_RAW_STRATEGY_EDGE` |
| `breakout_donchian&#47;v1` | -1,60 % | 0,845 | 328 | `NEGATIVE_RAW_STRATEGY_EDGE` |
| `ma_crossover&#47;v1` | -2,48 % | 0,161 | 6 | `NEGATIVE_RAW_STRATEGY_EDGE` |
| `rsi_reversion&#47;step30a` | -4,82 % | 0,836 | 465 | `SIGNAL_EDGE_PLUS_TURNOVER_PLUS_ROBUSTNESS` |
| `composite_breakout_confirmation_vol_gated_donchian_v1` | -2,34 % | 0,739 | 217 | `FEHLENDE_NETTO_EDGE_NEGATIVE_GROSS_EDGE` |
| `trend_following&#47;v1` | -0,24 % | 0,95 | 219 | `ROBUSTNESS_FAILED` (`MONTE_CARLO_FAILED`, `NET_EXPECTANCY_BELOW_THRESHOLD`, `PROFIT_FACTOR_BELOW_THRESHOLD`, `STRESS_FAILED`) |
| `bollinger_bands&#47;v1` | 0 % | 0,0 | 0 | `PROMISING_NOT_PASS` (`TRADE_COUNT_BELOW_THRESHOLD`, `PROFIT_FACTOR_BELOW_THRESHOLD`, `STRESS_FAILED`; 1307 Nonzero-Signals, 0 Trades) |
| `momentum_1h&#47;v1` | -0,19 % | 0,28 | 2 | `ROBUSTNESS_FAILED` (`TRADE_COUNT_BELOW_THRESHOLD`, `SINGLE_TRADE_DOMINANCE_EXCEEDED`, `MONTE_CARLO_FAILED`, `NET_EXPECTANCY_BELOW_THRESHOLD`, `PROFIT_FACTOR_BELOW_THRESHOLD`, `STRESS_FAILED`) |

```text
FAILED_BINDINGS_ARE_NEGATIVE_EVIDENCE=true
FAILED_BINDINGS_MAY_NOT_BE_RETRIED_UNCHANGED=true
POLICY_CHANGE_DOES_NOT_CHANGE_HISTORICAL_EVIDENCE=true
PROMISING_IS_NOT_PASS=true
PROMISING_IS_NOT_ECONOMICALLY_VIABLE_OFFLINE=true
PROMISING_IS_NOT_PROMOTION_CANDIDATE=true
PROMISING != PASS
PROMISING != ECONOMICALLY_VIABLE_OFFLINE
PROMISING != PROMOTION_CANDIDATE
```

## 19.2 Aktive Research-Governance

```text
OPERATOR_POLICY_DECISION=AUTHORIZE_BOUNDED_MULTI_CANDIDATE_FUTURES_RESEARCH_FLEET_V0
NO_NEW_CANDIDATE_HOLD=REVOKED
MULTI_CANDIDATE_RESEARCH_FLEET_ALLOWED=true
EXACTLY_ONE_CANDIDATE_LIMIT=false
FINAL_RESEARCH_FLEET_EVALUATION_COMPLETE=true
FINAL_RESEARCH_FLEET_STATUS=COMPLETE_NO_PASS
NO_ADMISSIBLE_NEXT_RESEARCH_SCOPE=true
OPERATOR_INPUT_REQUIRED_FOR_NEW_RESEARCH_SCOPE=true
```

Die Aufhebung des Holds verändert ausschließlich die Research-Governance.

Sie verändert nicht:

- Canonical Market Context,
- Scope Initialization oder Scope Event Generator,
- Bull-/Bear-Assessment,
- Survival oder Suitability,
- Double Play,
- Entry-/Position-/Exit-Policy,
- Capital/Risk/Sizing,
- Safety Kernel,
- Reconciliation,
- Runtime Authority.

```text
CORE_SYSTEM_MUTATION_ALLOWED=false
CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED=false
MASTER_V2_MUTATION_ALLOWED=false
DOUBLE_PLAY_MUTATION_ALLOWED=false
RISK_SIZING_MUTATION_ALLOWED=false
SAFETY_RUNTIME_MUTATION_ALLOWED=false
```

---

# 20. Reuse-First Economic Validation

Es wird kein neuer Economic-Validation-Stack aufgebaut.

Wiederzuverwenden:

```text
scripts/run_backtest.py
src/backtest/engine.py
src/backtest/walkforward.py
src/experiments/monte_carlo.py
src/experiments/stress_tests.py
src/experiments/portfolio_robustness.py
src/backtest/stats.py
src/experiments/evidence_chain.py
src/experiments/strategy_profiles.py
src/core/experiments.py
```

Neue Komponenten sind nur zulässig, wenn eine bestätigte Lücke nicht durch Adapter, Rewire oder Consolidation geschlossen werden kann.

---

# 21. Verbindlicher Research-/Runtime-Paritätsgrundsatz

```text
CANONICAL_TRADING_LOGIC_MUST_BE_SHARED=true
SEPARATE_BACKTEST_SIGNAL_LOGIC_ALLOWED=false
SEPARATE_RUNTIME_SIGNAL_LOGIC_ALLOWED=false
```

Die gleiche kanonische Decision-Semantik muss in:

- Offline Replay,
- Backtest,
- Walk-Forward,
- Monte Carlo,
- Stress,
- Shadow,
- Paper,
- Testnet,
- Runtime

verwendet werden.

Abweichungen dürfen nur in der Execution-Simulation oder Environment-Authority liegen, nicht in der Handelslogik.

---

# 22. Realistische Kostenbindung

Der Default-Backtest darf keine impliziten Nullkosten verwenden.

Aktuell bestätigter Drift:

```text
DEFAULT_BACKTEST_FEE_BPS=0
DEFAULT_BACKTEST_SLIPPAGE_BPS=0

CONFIG_FEE_BPS=10
CONFIG_SLIPPAGE_BPS=5
```

Kanonische Regel:

```text
NO_IMPLICIT_ZERO_COST_BACKTEST=true
NO_ECONOMIC_CLAIM_WITH_ZERO_COST_DEFAULT=true
```

Pflichtkomponenten:

- Maker-/Taker-Fees,
- Slippage,
- Spread,
- Funding,
- Tick-/Lot-Rounding,
- Mindestmenge,
- Mindestnotional,
- Partial Fills,
- Latenzannahmen,
- Mark-/Index-/Execution-Preis,
- Long-/Short-Symmetrie.

---

# 23. EconomicViabilityEvidenceV1

Pflichtartefakt:

```text
EconomicViabilityEvidenceV1
```

Pflichtfelder:

```text
strategy_id
strategy_version
instrument_id_or_universe
canonical_trading_logic_version
data_period
training_period
validation_period
out_of_sample_period
fee_model_version
slippage_model_version
funding_model_version
execution_model_version
config_digest
implementation_digest
data_digest

gross_return
net_return
net_expectancy
profit_factor
sharpe
sortino
max_drawdown
calmar
trade_count
turnover
fee_drag
funding_drag
slippage_impact
tail_loss
time_in_market
long_contribution
short_contribution
regime_breakdown
portfolio_contribution

walk_forward_results
monte_carlo_results
stress_results
parameter_sensitivity_results

status
reason_codes
manifest_digest
```

Status:

```text
RESEARCH_ONLY
PROMISING
ROBUSTNESS_FAILED
ECONOMICALLY_VIABLE_OFFLINE
SHADOW_VALIDATED
PAPER_VALIDATED
TESTNET_VALIDATED
```

---

# 24. Economic Validity Gate

```text
PROFITABLE_BACKTEST != ECONOMICALLY_VIABLE
```

Mindestbedingungen:

```text
net_expectancy_after_costs > 0
profit_factor_above_policy_threshold
max_drawdown_within_policy
walk_forward_stability_pass
out_of_sample_pass
parameter_robustness_pass
monte_carlo_pass
stress_test_pass
sufficient_trade_count
no_single_trade_or_regime_dominance
```

Konkrete Grenzwerte sind versionierte Policy und dürfen nicht nachträglich zur Ergebnisoptimierung verändert werden.

---

# 25. Walk-Forward, Monte Carlo und Stress

## 25.1 Walk-Forward

Vorhandenen Owner wiederverwenden:

```text
src/backtest/walkforward.py
```

Pflicht:

- explizite OOS-Fenster,
- stabile Rolling-Splits,
- keine nachträgliche Parameteranpassung im Testfenster,
- MV2-Bindung,
- realistische Kosten.

## 25.2 Monte Carlo

Research- und Risk-Monte-Carlo bleiben getrennte Domänen:

```text
src/experiments/monte_carlo.py
→ Strategy-/Return-Robustness

src/risk/monte_carlo.py
→ VaR/CVaR-Risk-Domain
```

Kein Zwang zur technischen Zusammenlegung, aber klare Owner-Dokumentation.

## 25.3 Stress

Bestehende Stress-Owner wiederverwenden.

Ergänzend erforderlich:

```text
fee_multiplier_stress
slippage_multiplier_stress
funding_stress
spread_expansion_stress
fill_quality_stress
latency_stress
trade_omission_stress
```

---

# 26. Portfolio und Single-Position-Semantik

Die vorhandene Multi-Strategy-/Multi-Asset-Infrastruktur bleibt Research-Capability.

Für die kanonische v4.3-Initialphase gilt:

```text
SINGLE_SELECTED_FUTURE=true
MAX_POSITIONS=1
MAX_ACTIVE_DIRECTIONAL_SIDE=1
```

Portfolio-Flächen dürfen:

- Strategien vergleichen,
- Robustness aggregieren,
- Kandidaten ranken.

Sie dürfen nicht die Double-Play-Authority oder Single-Side-Regel umgehen.

---

# 27. Profitabilitäts- und Promotion-Gates

Aktuell bestätigtes Gap:

```text
PROMOTION_ECONOMIC_GATES=DOCUMENTATION_ONLY
```

Verboten:

```text
eligible_for_live=true
based_only_on_confidence_score
```

Künftig:

```text
eligible_for_promotion_candidate =
economic_validity_pass
AND robustness_pass
AND evidence_admissible
AND safety_policy_pass
```

Live- oder Runtime-Authority entsteht dadurch nicht.

---

# PART IV — RUNTIME SAFETY AND EXECUTION

# 28. Safety Kernel

Mandatory für jeden ausführungsrelevanten Intent.

Prüft mindestens:

- Governance,
- Environment,
- Runtime Eligibility,
- KillSwitch,
- Data Quality,
- Clock Trust,
- Trading Epoch,
- Executor Epoch,
- Authority Lease,
- Execution Permission,
- Position State,
- Reconciliation State,
- Risk Limits,
- Venue Metadata,
- Single Writer,
- Duplicate Intent,
- Unknown Outcome.

Safety darf nur begrenzen oder ablehnen.

---

# 29. KillSwitch

Explizite Modi:

```text
KILL_MODE_BLOCK_NEW
KILL_MODE_CANCEL_PENDING
KILL_MODE_REDUCE_TO_FLAT
KILL_MODE_EMERGENCY_FLATTEN
```

Ohne eindeutige Policy:

```text
NO_NEW_POSITIONS
NO_POSITION_INCREASE
NO_NEW_TRADING_PERMISSION
RECONCILIATION_REQUIRED
```

Kein automatischer Resume.

---

# 30. Runtime Eligibility, Lease und Permissions

Getrennte Permission-Typen:

```text
TradingExecutionPermissionV1
SafetyExitPermissionV1
CancelPermissionV1
ReconciliationQueryPermissionV1
```

Authority-Bindung:

```text
venue_id
account_id
subaccount_id
instrument_id
position_mode
margin_mode
execution_owner_id
writer_lease_id
fencing_token
executor_epoch
```

---

# 31. Durable-before-submit und Single Writer

Vor möglichem Netzwerk-Byte durable persistieren:

```text
intent_id
client_order_id
permission_id
lease_id
venue_id
account_id
instrument_id
submission_attempt_number
executor_epoch
authority_epoch
revocation_epoch
writer_lease_id
fencing_token
policy_digest
config_digest
implementation_digest
```

```text
NO_SUBMISSION_BEFORE_DURABLE_INTENT_PERSISTENCE=true
NO_STALE_WRITER_MAY_SUBMIT=true
PROCESS_ID_IS_NOT_A_FENCING_TOKEN=true
```

---

# 32. Unknown Outcomes und Reconciliation

Bei Timeout nach möglicher Übertragung:

```text
kein automatischer Resubmit
→ Query by Client Order ID
→ Open Orders
→ Recent Orders
→ Fills
→ Position
→ Reconciliation
```

Delivery-Semantik:

```text
at-least-once communication
+
idempotent intent processing
+
reconciliation-based effect resolution
```

---

# PART V — IMPLEMENTATION AND VALIDATION LADDER

# 33. Reuse-First-Regel

Vor jedem neuen Modul:

```text
REUSE_AS_IS
→ REUSE_WITH_NARROW_ADAPTER
→ REWIRE_EXISTING_COMPONENT
→ CONSOLIDATE_TO_EXISTING_OWNER
→ DEPRECATE_LEGACY_PATH
→ NEW_IMPLEMENTATION_JUSTIFIED
```

Ein neuer Owner ist nur zulässig bei:

```text
DISTINCT_AUTHORITY_SEMANTICS
OR DISTINCT_PERSISTENCE_LIFECYCLE
OR DISTINCT_VALIDATION_BOUNDARY
OR CONSUMER_CONTRACT_INCOMPATIBLE
```

---

# 34. Korrigierte kanonische Implementierungsreihenfolge

## STEP 29A — Constitutional and Semantic Contract Freeze

- v4.3 als Zielsemantik binden,
- bestehende Owner und Reuse Decisions ratifizieren,
- keine Runtime-Wirkung.

## STEP 29B — Canonical Market Context Binding

Reuse:

```text
src/trading/master_v2/double_play_futures_input.py
FuturesInputSnapshot
evaluate_futures_input_snapshot
```

Ziel:

```text
CanonicalMarketContextV1
```

Pflicht:

- finalisierte Trading Epoch,
- Warmup,
- Clock Trust,
- Mark/Index/Bid/Ask,
- Data Integrity,
- Input Digest,
- Idempotenz,
- Out-of-Order-Block.

## STEP 29C — Canonical Scope Initialization

- Scope Lifecycle,
- Initialisierung,
- Reinitialisierung,
- keine impliziten Defaults,
- keine freie Reinitialisierung bei offener oder unbekannter Position.

## STEP 29D — Deterministic Scope Event Generator

Erst nach 29B und 29C.

Reuse:

- `transition_state()`,
- `DynamicScopeRules`,
- `RuntimeScopeState`,
- bestehende Test-Harness-Fixtures.

Kein isolierter Preis-gegen-Grenze-Shortcut.

## STEP 29E — Bull/Bear Directional Assessment Completion

- ein gemeinsamer Contract,
- Symmetrie,
- Candidate/Confirmed,
- keine Authority-Wirkung.

## STEP 29F — Survival and Suitability Binding

Reuse vorhandener Module.

Ergänzen:

- Kostenmodell,
- Regime-Owner,
- deterministische Strategy-Auswahl.

## STEP 29G — Double Play Composition Matrix Completion

- vollständige Matrix,
- Konfliktregel,
- kein implizites Scoring-Override.

## STEP 29H — Entry, Position Management and Exit Policy

- Entry Preconditions,
- Exit-Klassen,
- Profit Protection,
- Reversal Preparation,
- Partial-Fill-Semantik.

## STEP 29I — Integrated Offline Trading Logic Replay

Kette:

```text
CanonicalMarketContextV1
→ Scope Initialization
→ Scope Event
→ Bull/Bear
→ State Switch
→ Survival
→ Suitability
→ Double Play
→ CanonicalTradingDecisionEvidenceV1
→ MANIFEST.sha256
```

Keine Runtime, keine Orders.

## STEP 29J — Default Backtest Economic Realism Binding

Reuse:

```text
scripts/run_backtest.py
src/backtest/engine.py
config.toml
```

Pflicht:

- keine impliziten Nullkosten,
- Fees/Slippage aus versionierter Config,
- Tests für Default-Binding,
- bestehende CLI-Kompatibilität.

## STEP 29K — Strategy Registry Consolidation

Zielowner:

```text
src/strategies/registry.py
```

Legacy-Keys nur über explizite Aliase und Deprecation.

## STEP 29L — MV2 Research Wiring

Kette:

```text
Canonical MV2 Decision Path
→ Backtest
→ Walk-Forward
→ Monte Carlo
→ Stress
→ Metrics
→ Evidence Chain
```

Keine duplizierte Signal- oder Strategy-Logik.

## STEP 29M — Economic Viability Evidence

Erzeuge persistierte, manifest-verifizierte Netto-Evidence.

## STEP 29N — Promotion Economic Gate Binding

Bindung an:

- EconomicViabilityEvidenceV1,
- Strategy Profiles,
- Robustness,
- Evidence Admissibility.

Kein Live-GO.

## STEP 29O — Intent Compatibility Firewall

Konsolidierung der parallelen Intent-Typen.

## STEP 29P — Capital / Risk / Sizing Mathematics

Monotone Quantity-Kette.

## STEP 29Q — Canonical Order Intent

Keine Adapter-Kompatibilität ohne explizite Transformation.

## STEP 29R — Runtime Rewire

Erst nach:

```text
TRADING_LOGIC_COMPLETION_GATE_PASS
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS
INTENT_COMPATIBILITY_FIREWALL_PASS
```

## STEP 29S — Fenced Writer and Restart Contract

## STEP 29T — Zero-Order Runtime

## STEP 29U — Shadow

## STEP 29V — Paper

## STEP 29W — Testnet

## STEP 29X — Measured SLO Evidence

## STEP 29Y — Bounded Canary

## STEP 29Z — Full Autonomous Production

---

# 35. Aktuell autorisierter nächster Schritt

Der bisherige STEP29A–29R-Implementierungs- und Revalidierungspfad ist bis zur Economic-Validity-Grenze abgearbeitet.

Die Final Research Fleet ist vollständig versioniert gebunden, offline wirtschaftlich evaluiert und terminal abgeschlossen.

```text
FINAL_RESEARCH_FLEET_BINDING_READY=true
FINAL_RESEARCH_FLEET_EVALUATION_COMPLETE=true
FINAL_RESEARCH_FLEET_STATUS=COMPLETE_NO_PASS
PASS_COUNT=0
FAIL_COUNT=3
PROMOTION_CANDIDATES=[]
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false
RUNTIME_REWIRE_ADMISSIBLE=false
```

Final konvergierte und abgeschlossene Research Fleet:

```text
trend_following/v1  → FAIL (ROBUSTNESS_FAILED; 219 Trades; Net Return -0,24 %; Profit Factor 0,95)
bollinger_bands/v1  → FAIL (PROMISING; 0 Trades / 1307 Nonzero-Signals; Net Return 0 %; Profit Factor 0,0)
momentum_1h/v1      → FAIL (ROBUSTNESS_FAILED; 2 Trades; Net Return -0,19 %; Profit Factor 0,28)
```

```text
PROMISING != PASS
PROMISING != ECONOMICALLY_VIABLE_OFFLINE
PROMISING != PROMOTION_CANDIDATE
```

Gemeinsame Bindungen (unverändert):

```text
DATASET_BINDING=inst-eth-usdt-perp_v1
FUTURES_ONLY=true
BITCOIN_DIRECTION_ALLOWED=false
ECONOMIC_POLICY_BINDING=economic_validity_policy_v1
POLICY_DRIFT=false
BINDING_DRIFT=false
```

Verbindlich ausgeschlossen — unveränderte Retries:

```text
trend_following/v1 unverändert
bollinger_bands/v1 unverändert
momentum_1h/v1 unverändert
macd unverändert
breakout_donchian unverändert
ma_crossover unverändert
unchanged single-instrument ETH technical retries on same dataset profile
```

Verbindlich ausgeschlossen — Near-Duplicate-Archetypen:

```text
Trend-Following-/MA-ADX-Filter-Familie
Bollinger-Bands-/Mean-Reversion-Band-Touch-Familie
Momentum-1h-/Short-Horizon-Price-Momentum-Familie
```

Keine weitere Evaluation, kein Retry und keine Near-Duplicate-Research ohne neue ausdrücklich ratifizierte Operator-Hypothese.

Der nächste kanonische Schritt ist:

```text
NEXT_STEP=OPERATOR_INPUT_REQUIRED_FOR_NEW_RESEARCH_SCOPE_DEFINITION_V0
DECISION=NO_ADMISSIBLE_NEXT_RESEARCH_SCOPE
NEXT_SCOPE_NAME=NONE
```

Der verbleibende unerforschte Raum ist ausschließlich als nicht ratifizierte Operator-Hypothese dokumentiert:

```text
Cross-sectional Multi-Instrument-Panel
neue historische Dataset-/Perioden-Coverage
nicht-technische oder nicht-single-instrument Archetypen
```

Diese Punkte sind **kein** automatisch autorisierter nächster Scope.

Verbindlich ausgeschlossen:

```text
NO_CORE_SYSTEM_CHANGE
NO_CANONICAL_TRADING_LOGIC_CHANGE
NO_MASTER_V2_CHANGE
NO_DOUBLE_PLAY_CHANGE
NO_RISK_SIZING_CHANGE
NO_SAFETY_RUNTIME_CHANGE
NO_RUNTIME_REWIRE
NO_SHADOW
NO_PAPER
NO_TESTNET
NO_SCHEDULER
NO_ADAPTER_SUBMISSION
NO_ORDERS
NO_CREDENTIALS
NO_ARMING
NO_CANARY
NO_LIVE
NO_NEW_CANDIDATE_RATIFICATION
NO_STRATEGY_IMPLEMENTATION
NO_PARAMETER_OPTIMIZATION
NO_THRESHOLD_REDUCTION
NO_DATASET_GENERATION
NO_ECONOMIC_EVALUATION
```

---

# 36. Testleiter

## LEVEL 0 — Unit und Contract

- Schemas,
- State Transitions,
- Digests,
- Futures-only,
- Bitcoin-Verbot,
- negative Tests.

## LEVEL 1 — Integrated Offline Replay

- vollständige MV2-Handelslogik,
- kein Runtime-/Adapter-Zugriff,
- MANIFEST-verifizierte Evidence.

## LEVEL 2 — Economic Backtest

- realistische Kosten,
- gleiche Trading Logic,
- persistierte Resultate.

## LEVEL 3 — Walk-Forward / Monte Carlo / Stress

- OOS,
- Parameterstabilität,
- Sequenzrobustheit,
- Kostenstress.

## LEVEL 4 — Zero-Order Runtime

## LEVEL 5 — Shadow

## LEVEL 6 — Paper

## LEVEL 7 — Testnet

## LEVEL 8 — Measured SLO Evidence

## LEVEL 9 — Bounded Canary

## LEVEL 10 — Full Autonomous Production

Keine Stufe darf übersprungen werden.

---

# 37. Definition of Done — Trading Logic

```text
CANONICAL_MARKET_CONTEXT_BOUND=true
FINALIZED_TRADING_EPOCH_BOUND=true
WARMUP_POLICY_BOUND=true
SCOPE_INITIALIZATION_BOUND=true
SCOPE_EVENT_FORMULAS_BOUND=true
BULL_ASSESSMENT_BOUND=true
BEAR_ASSESSMENT_BOUND=true
SURVIVAL_FORMULAS_BOUND=true
SUITABILITY_SELECTION_BOUND=true
DOUBLE_PLAY_MATRIX_COMPLETE=true
DECISION_PRECEDENCE_BOUND=true
ENTRY_POLICY_BOUND=true
POSITION_MANAGEMENT_POLICY_BOUND=true
EXIT_POLICY_BOUND=true
PARTIAL_FILL_SEMANTICS_BOUND=true
RISK_SIZING_FORMULAS_BOUND=true
INSTRUMENT_SELECTION_BOUNDARY_ENFORCED=true
DETERMINISTIC_REPLAY_PASS=true
```

---

# 38. Definition of Done — Economic Validity

```text
DEFAULT_BACKTEST_COSTS_BOUND=true
NO_IMPLICIT_ZERO_COST_PATH=true
MV2_BACKTEST_WIRING_PASS=true
MV2_WALK_FORWARD_WIRING_PASS=true
MV2_MONTE_CARLO_WIRING_PASS=true
MV2_STRESS_WIRING_PASS=true
PARAMETER_SENSITIVITY_COMPUTED=true
NET_PERFORMANCE_EVIDENCE_PERSISTED=true
ECONOMIC_VIABILITY_EVIDENCE_VALID=true
PROMOTION_ECONOMIC_GATE_ENFORCED=true
```

---

# 39. Definition of Done — Safety and Runtime

```text
SAFETY_KERNEL_MANDATORY=true
KILL_SWITCH_RUNTIME_DRILL_PASS=true
RECONCILIATION_PASS=true
UNKNOWN_OUTCOME_RECOVERY_PASS=true
CLOCK_TRUST_PASS=true
SINGLE_WRITER_PASS=true
FENCING_TOKEN_ENFORCED=true
DURABLE_BEFORE_SUBMIT_PASS=true
RESTART_RECONCILIATION_PASS=true
```

---

# 40. Kanonische Sicherheitsinvarianten

```text
FAVORABLE_EXTREME_MOVE_ALONE_DOES_NOT_TRIGGER_KILLSWITCH=true
ADVERSE_MOVE_USES_RISK_EXIT_STATE_SWITCH_FIRST=true
OPPOSITE_SIDE_CANNOT_OPEN_BEFORE_RECONCILED_FLAT=true
RECONCILIATION_FAILURE_BLOCKS_NEW_EXPOSURE=true
UNKNOWN_OUTCOME_NEVER_AUTO_RESUBMITS=true
DYNAMIC_SCOPE_CANNOT_EXPAND_BEYOND_HARD_LIMITS=true
CURRENT_SCOPE_IS_IMMUTABLE_WITHIN_DECISION_CYCLE=true
NO_ORDER_WITHOUT_QUANTITY_PROVENANCE=true
NO_ADAPTER_WITHOUT_SINGLE_USE_PERMISSION=true
NO_RUNTIME_AUTHORITY_FROM_EVIDENCE=true
NO_ENTRY_FROM_UNFINALIZED_MARKET_DATA=true
NO_DYNAMIC_SCOPE_UPDATE_FROM_UNTRUSTED_DATA=true
NO_IMPLICIT_STRATEGY_SELECTION=true
NO_IMPLICIT_ENTRY_OR_EXIT_ORDER_TYPE=true
ROUNDING_MUST_NOT_INCREASE_RISK=true
NO_RUNTIME_REWIRE_BEFORE_TRADING_LOGIC_COMPLETION_GATE=true
NO_ECONOMIC_CLAIM_WITHOUT_REALISTIC_COSTS=true
NO_PROMOTION_ELIGIBILITY_FROM_CONFIDENCE_ONLY=true
```

---

# 41. Audit-bestätigte Reuse Decisions

## REUSE_AS_IS

```text
src/trading/master_v2/*
src/execution/pipeline.py
src/live/safety.py
src/ops/gates/risk_gate.py
src/backtest/walkforward.py
src/experiments/monte_carlo.py
src/experiments/stress_tests.py
scripts/ops/ci_test_selection_v1.py
scripts/ops/primary_evidence_retention_v0.py
src/webui/market_instrument_eligibility_v0.py
```

## REUSE_WITH_NARROW_ADAPTER

```text
scripts/run_backtest.py
src/experiments/strategy_profiles.py
src/experiments/stress_tests.py
src/execution/paper/futures_accounting.py
```

## REWIRE_EXISTING_COMPONENT

```text
Master V2 → Offline Replay
Master V2 → Backtest
Promotion Loop → Economic Gates
Live Gates → Governed Session Start
```

## CONSOLIDATE_TO_EXISTING_OWNER

```text
Strategy Registry → src/strategies/registry.py
Portfolio Backtest → src/backtest/engine.py
Regime Owner → canonical MV2-bound path
```

## DEPRECATE_LEGACY_PATH

```text
legacy load_strategy path after alias migration
src/portfolio/manager.py after parity
execution_simple after decoupling
ShadowPaperSession after LiveSessionRunner parity
```

---

# 42. Nicht zulässige Fehlinterpretationen

```text
TECHNICAL_CAPABILITY_PRESENT
!= ECONOMIC_VALIDITY_PROVEN
```

```text
NEGATIVE_COMMITTED_PROFILE
!= WHOLE_SYSTEM_UNPROFITABLE
```

```text
MISSING_EVIDENCE
!= MISSING_IMPLEMENTATION
```

```text
RUNBOOK_TARGET_STATE
!= CURRENT_REPO_STATE
```

```text
AUDIT_RANKING
!= AUTOMATIC_IMPLEMENTATION_ORDER
```

Die endgültige Reihenfolge folgt der semantischen Abhängigkeit des kanonischen Kernsystems.

---

# 43. Abschlussgrundsatz

Peak Trade ist erst dann fachlich und wirtschaftlich bereit, wenn:

```text
die Handelslogik konsistent und deterministisch ist,
Bull und Bear symmetrisch und konfliktfrei koordiniert werden,
Dynamic Scope, Exit und Reversal getrennt sind,
die gleiche Logik in Research und Runtime verwendet wird,
Backtests realistische Kosten enthalten,
Walk-Forward, Monte Carlo und Stress auf der kanonischen Logik laufen,
Netto-Performance-Evidence reproduzierbar persistiert wird,
Promotion technisch auf Economic Validity und Safety blockiert,
Runtime Safety unabhängig bleibt,
und keine Authority aus Readiness oder Evidence abgeleitet wird.
```

Der kanonische Weg lautet:

```text
Canonical Market Context
→ Scope Initialization
→ Scope Event Generator
→ Bull/Bear Assessments
→ Survival and Suitability
→ Double Play
→ Entry/Position/Exit Policy
→ Integrated Offline Replay
→ Realistic Backtest
→ Walk-Forward / Monte Carlo / Stress
→ Economic Viability Evidence
→ Promotion Gates
→ Capital/Risk/Sizing
→ Canonical Order Intent
→ Zero-Order Runtime
→ Shadow
→ Paper
→ Testnet
→ Measured SLO Evidence
→ Bounded Canary
→ Full Autonomous Production
```

Keine Stufe darf übersprungen werden.

---

# 43.1 Operativer Current-State-Anhang vom 3. Juli 2026

```text
CANONICAL_REVALIDATION_HEAD=ffae153f754ef7ffb5e34edca441bd8072c05399
ORIGIN_MAIN=ffae153f754ef7ffb5e34edca441bd8072c05399
HEAD_EQUALS_ORIGIN_MAIN=true
WORKTREE_CLEAN=true
PRIMARY_WORKTREE_MUTATED=false
REPO_MUTATION=false
FINAL_RESEARCH_FLEET_STATUS=COMPLETE_NO_PASS
PASS_COUNT=0
FAIL_COUNT=3
PROMOTION_CANDIDATES=[]
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false
RUNTIME_REWIRE_ADMISSIBLE=false
DECISION=NO_ADMISSIBLE_NEXT_RESEARCH_SCOPE
NEXT_STEP=OPERATOR_INPUT_REQUIRED_FOR_NEW_RESEARCH_SCOPE_DEFINITION_V0
```

Manifest-verifizierte Planning-Bundles (Vorläufer):

```text
bounded_post_step30a_economic_validity_recovery_governance_matrix_canonical_revalidation_read_only_v0_20260702T212800Z
bounded_multi_candidate_futures_research_fleet_inventory_and_archetype_mapping_read_only_v0_20260702T234800Z
bounded_multi_candidate_futures_research_fleet_final_convergence_and_binding_readiness_read_only_v0_20260702T235500Z
```

Manifest-verifizierte Execution-, Closeout- und Decision-Evidence:

```text
bounded_final_research_fleet_offline_economic_evaluation_execution_v0_20260703T052244Z
bounded_final_research_fleet_offline_economic_evaluation_execution_squash_merge_closeout_v0_20260703T053410Z
bounded_final_research_fleet_negative_economic_evidence_closeout_and_next_research_decision_v0_20260703T073600Z
```

Für alle sechs Bundles gilt:

```text
MANIFEST_VERIFY_RC=0
```

Evidence-Pfade (externes Runtime-Archive):

```text
SOURCE_EXECUTION_EVIDENCE_PATH=/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/bounded_final_research_fleet_offline_economic_evaluation_execution_v0_20260703T052244Z
SOURCE_CLOSEOUT_EVIDENCE_PATH=/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/implementation/bounded_final_research_fleet_offline_economic_evaluation_execution_squash_merge_closeout_v0_20260703T053410Z
SOURCE_DECISION_EVIDENCE_PATH=/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/bounded_final_research_fleet_negative_economic_evidence_closeout_and_next_research_decision_v0_20260703T073600Z
```

Dieser Current-State-Anhang ist Fortschritts- und Governance-Evidence. Er ersetzt keine versionierten Repo-Owner, keine Strategy-Bindings und keine EconomicViabilityEvidenceV1.

---

# 44. v4.4 Änderungsprotokoll

Gegenüber v4.3 wurden ausschließlich Governance-, Fortschritts- und Economic-Evidence-Aktualisierungen vorgenommen.

Nicht geändert wurden:

- Core-System,
- kanonische Handelslogik,
- Master V2,
- Double Play,
- Scope-, Entry-, Exit- oder Reversal-Semantik,
- Risk-/Sizing-Verträge,
- Safety Kernel,
- Reconciliation,
- Runtime-Authority-Semantik.

Ergänzt oder aktualisiert wurden:

1. realer Abschlussstand STEP29M, STEP30A, STEP29N, STEP29O und STEP29R,
2. terminale negative Evidence für fünf abgeschlossene Bindings,
3. Klarstellung, dass historische Economic Failures durch Operator-Policy nicht verändert werden,
4. Aufhebung des `NO_NEW_CANDIDATE_HOLD`,
5. Autorisierung eines bounded Multi-Candidate-Futures-Research-Fleet-Modells,
6. ausdrücklicher Schutz des Core-Systems vor Research-bedingten Mutationen,
7. Wiederholungsverbot unveränderter fehlgeschlagener Bindings,
8. Final-Convergence der neuen Fleet auf:
   - `trend_following`,
   - `bollinger_bands`,
   - `momentum_1h`,
9. Ausschluss von:
   - unveränderten Negativbindungen,
   - near-duplicate Breakout-Varianten,
   - redundanten Mean-Reversion-Slots,
   - R&D-Skeletons ohne vollständige Daten- und Evaluation-Capability,
10. neuer nächster kanonischer Schritt: versionierte Fleet-Bindings und separate Offline-Evaluationsratifikation,
11. Bestätigung, dass Economic-Validity-, Promotion-, Safety- und Runtime-Gates unverändert bleiben.

**Aktualisierung vom 3. Juli 2026 (bounded negative-economic current-state sync):**

12. erfolgreiche versionierte Final-Research-Fleet-Bindung (`FINAL_RESEARCH_FLEET_BINDING_READY=true`),
13. abgeschlossene Offline-Economic-Evaluation aller drei Fleet-Kandidaten,
14. drei neue terminal negative Economic-Evidence-Ergebnisse:
    - `trend_following&#47;v1` FAIL (`ROBUSTNESS_FAILED`),
    - `bollinger_bands&#47;v1` FAIL (`PROMISING`; explizit kein PASS und kein Promotion Candidate),
    - `momentum_1h&#47;v1` FAIL (`ROBUSTNESS_FAILED`),
15. terminale Entscheidung `DECISION=NO_ADMISSIBLE_NEXT_RESEARCH_SCOPE`,
16. Operator-Input-Grenze: jede neue Research-Hypothese erfordert separates Operator-GO und versionierte Binding-Ratifikation,
17. Klarstellung `PROMISING != PASS`, `PROMISING != ECONOMICALLY_VIABLE_OFFLINE`, `PROMISING != PROMOTION_CANDIDATE`,
18. Ausschluss unveränderter Retries und Near-Duplicate-Archetypen für alle drei Fleet-Kandidaten,
19. `NEXT_STEP=OPERATOR_INPUT_REQUIRED_FOR_NEW_RESEARCH_SCOPE_DEFINITION_V0`.

---

# 45. Kanonische Gesamtentscheidung

```text
V4_4_IS_CANONICAL_TARGET=true
CURRENT_REPO_REQUIRES_NO_REBUILD=true

CORE_SYSTEM_MUTATION_ALLOWED=false
CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED=false
MASTER_V2_MUTATION_ALLOWED=false
DOUBLE_PLAY_MUTATION_ALLOWED=false
RISK_SIZING_MUTATION_ALLOWED=false
SAFETY_RUNTIME_MUTATION_ALLOWED=false

OPERATOR_POLICY_DECISION=AUTHORIZE_BOUNDED_MULTI_CANDIDATE_FUTURES_RESEARCH_FLEET_V0
NO_NEW_CANDIDATE_HOLD=REVOKED
MULTI_CANDIDATE_RESEARCH_FLEET_ALLOWED=true

FINAL_RESEARCH_FLEET=trend_following,bollinger_bands,momentum_1h
FINAL_RESEARCH_FLEET_BINDING_READY=true
FINAL_RESEARCH_FLEET_EVALUATION_COMPLETE=true
FINAL_RESEARCH_FLEET_STATUS=COMPLETE_NO_PASS
PASS_COUNT=0
FAIL_COUNT=3
PROMOTION_CANDIDATES=[]
NEW_CANDIDATES_RATIFIED=true
ECONOMIC_EVALUATION_AUTHORIZED=false
ECONOMIC_EVALUATION_COMPLETE=true

ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false
RUNTIME_REWIRE_DEFERRED=true
RUNTIME_REWIRE_ADMISSIBLE=false
LIVE_AUTHORIZED=false

DECISION=NO_ADMISSIBLE_NEXT_RESEARCH_SCOPE
NEXT_SCOPE_NAME=NONE
NEXT_STEP=OPERATOR_INPUT_REQUIRED_FOR_NEW_RESEARCH_SCOPE_DEFINITION_V0
```

Der kanonische Fortschrittspfad ist bis zur Fleet-Evaluation abgeschlossen. Weitere Research-Schritte erfordern explizite Operator-Hypothese:

```text
Operator-Hypothese (nicht autorisierter Default)
→ Versioned Candidate Bindings
→ Versioned Parameter/Dataset/Period Bindings
→ Offline Economic Evaluation
→ Walk-Forward / Monte Carlo / Stress
→ Manifest-Verified EconomicViabilityEvidenceV1
→ PASS / FAIL / INCONCLUSIVE
→ nur bei vollständigem PASS: Promotion-Candidate
→ Runtime-Rewire weiterhin separat gegated
```

Verbleibender unerforschter Raum (nur als Operator-Hypothese, nicht autorisierter nächster Scope):

```text
Cross-sectional Multi-Instrument-Panel
neue historische Dataset-/Perioden-Coverage
nicht-technische oder nicht-single-instrument Archetypen
```

Der bisherige kanonische Fortschrittspfad lautete:

```text
Final Research Fleet
→ Versioned Candidate Bindings
→ Versioned Parameter/Dataset/Period Bindings
→ Offline Economic Evaluation
→ Walk-Forward / Monte Carlo / Stress
→ Manifest-Verified EconomicViabilityEvidenceV1
→ PASS / FAIL / INCONCLUSIVE
→ nur bei vollständigem PASS: Promotion-Candidate
→ Runtime-Rewire weiterhin separat gegated
```

Dieser Pfad ist für die Final Research Fleet terminal abgeschlossen (`COMPLETE_NO_PASS`).

Keine Research- oder Operator-Entscheidung darf negative Evidence überschreiben oder Runtime Authority erzeugen.
