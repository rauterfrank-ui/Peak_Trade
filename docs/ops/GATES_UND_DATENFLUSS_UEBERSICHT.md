# Peak_Trade – Gates und Datenfluss: Ausführliche Übersicht

> **Zweck:** Zentrale Übersicht aller Gates (Daten- und Kontrollflüsse), was wo reinkommt und rausgeht, inkl. Live-Bezug.  
> **Stand:** 2026-02-01

---

## 1. Einleitung

Dieses Dokument beschreibt **alle relevanten Gates** im Peak_Trade-System: wo sie sitzen, welche **Daten rein-** und **rausgehen** und wie **Live** (Shadow/Testnet/Live-Design) einbezogen ist. Es dient als Referenz für Ops, Entwicklung und Audits.

**Gate** bedeutet hier: eine **Prüf- oder Grenzstelle**, an der entweder
- **Daten** ein- oder ausgeleitet werden (Daten-Gates), oder
- **Entscheidungen** (erlaubt/blockiert) getroffen werden (Kontroll-Gates).

---

## 2. Übersicht aller Gates

### 2.1 Kategorien

| Kategorie        | Zweck                                      | Beispiele                                      |
|------------------|--------------------------------------------|------------------------------------------------|
| **Execution**    | Order-Pipeline (Intent → Recon)            | Stage 3 Pre-Trade Risk Gate, Kill Switch       |
| **Live/Safety**  | Freigabe für Live/Testnet/Paper            | Gate 1, Gate 2, Technisches Gate, SafetyGuard |
| **Eligibility**  | Ob Strategie/Portfolio live-fähig ist     | LiveGateResult, check_strategy_live_eligibility |
| **Data Safety**  | Keine synthetischen Daten im Live-Trade   | DataSafetyGate, DataSafetyContext              |
| **Governance**   | Live-Mode-Freigabe, Config-Validierung    | LiveModeGate, enforce_live_mode_gate           |
| **Escalation**   | Wann Alerts/Eskalation rausgehen           | EscalationManager Gate 1/2/3                    |

---

## 3. Execution-Pipeline und Stage-Gates

Die **8-Stage-Execution-Pipeline** (`src/execution/orchestrator.py`) ist der zentrale Pfad von **Intent** bis **Recon Hand-off**. Einige Stages wirken als Gates (Daten/Entscheidung).

### 3.1 Stage-Übersicht

| Stage | Name                    | Funktion (Kurz)                    | Daten REIN                    | Daten RAUS                         |
|-------|-------------------------|------------------------------------|-------------------------------|------------------------------------|
| 1     | Intent Intake           | Korrelation, Idempotenz            | `OrderIntent`                 | `correlation_id`, `idempotency_key`, INTENT-Event |
| 2     | Contract Validation     | WP0E-Invarianten                   | Intent, run_id, session_id   | `Order` (CREATED), ggf. Validierungsfehler |
| 3     | **Pre-Trade Risk Gate** | RiskHook (ALLOW/BLOCK/PAUSE)       | `Order`                      | RiskResult, ggf. REJECT/Fail, Ledger |
| 4     | Route Selection         | Adapter nach Mode (paper/shadow/…) | Order, execution_mode       | gewählter Adapter, ggf. POLICY_LIVE_NOT_ENABLED |
| 5     | Adapter Dispatch        | Order an Adapter senden            | Order, idempotency_key       | ExecutionEvent (ACK/REJECT/FILL)    |
| 6     | Execution Event Handling| ACK/REJECT/FILL verarbeiten        | Order, ExecutionEvent        | Order-State-Update, Ledger-Einträge |
| 7     | Post-Trade Hooks        | Ledger, Events                     | Order, Event, Fill-Info      | Ledger-Entries, Audit-Events       |
| 8     | Recon Hand-off          | Daten für Abgleich bereitstellen   | Order, Ledger                | PipelineResult, Ledger-Entries, Recon-Daten |

**Stage 3 (Pre-Trade Risk Gate)** ist das explizite **Risk-Gate**: `RiskHook.evaluate_order(order)` entscheidet ALLOW/BLOCK/PAUSE. Bei BLOCK/PAUSE wird die Pipeline mit `PipelineResult(success=False)` beendet; es gehen u.a. Ledger-Einträge und ggf. Beta-Events (z. B. RISK_REJECT) raus.

Zusätzlich kann **vor** Stage 3 der **Kill Switch** greifen: `kill_switch_active` → sofortiger Abbruch mit `RISK_REJECT_KILL_SWITCH`.

### 3.2 Daten rein (Execution-Pipeline gesamt)

- **OrderIntent**: symbol, side, quantity, order_type, limit_price, time_in_force, strategy_id, session_id, run_id, intent_id.
- **Laufzeit**: risk_hook, adapter/adapter_registry, execution_mode, retry_policy, kill_switch_active, max_position_qty (Runbook B).

### 3.3 Daten raus (Execution-Pipeline gesamt)

- **PipelineResult**: success, order, stage_reached, correlation_id, reason_code, reason_detail, ledger_entries, idempotency_key, metadata (inkl. risk_result, execution_event, beta_events).
- **Persistenz**: execution_events.jsonl (Beta-Events: INTENT, RISK_REJECT, ORDER, FILL, etc.), OrderLedger, PositionLedger, AuditLog.
- **Recon**: Daten für ReconciliationEngine (Position/Order-Ledger).

---

## 4. Live- und Safety-Gates (SafetyGuard, Phase 71)

Die **SafetyGuard**-Logik (`src/live/safety.py`) und **EnvironmentConfig** entscheiden, ob eine Aktion (z. B. Order senden) in PAPER, TESTNET oder LIVE erlaubt ist. Für **echte Live-Execution** sind mehrere Gates nacheinander zu erfüllen.

### 4.1 Gate 1 – enable_live_trading

- **Wo:** `EnvironmentConfig.enable_live_trading`; ausgewertet in `is_live_execution_allowed()` und im SafetyGuard.
- **Daten rein:** Config (environment, enable_live_trading).
- **Daten raus:** Erlaubt/blockiert; bei Block: `LiveTradingDisabledError`, Reason „enable_live_trading = False (Gate 1)“.

### 4.2 Gate 2 – live_mode_armed (Phase 71)

- **Wo:** `EnvironmentConfig.live_mode_armed`; ausgewertet in `is_live_execution_allowed()`.
- **Daten rein:** Config (live_mode_armed).
- **Daten raus:** Erlaubt/blockiert; bei Block: „live_mode_armed = False (Gate 2 - Phase 71)“.

### 4.3 Technisches Gate – live_dry_run_mode (Phase 71)

- **Wo:** `EnvironmentConfig.live_dry_run_mode`; in Phase 71 faktisch immer `True`.
- **Daten rein:** Config (live_dry_run_mode).
- **Daten raus:** Wenn True → keine echten Live-Orders; bei Versuch echte Order: `LiveNotImplementedError` („Technisches Gate blockiert echte Orders“).

### 4.4 Confirm-Token (optional)

- **Wo:** `require_confirm_token` und `confirm_token == LIVE_CONFIRM_TOKEN`.
- **Daten rein:** Config (confirm_token, require_confirm_token).
- **Daten raus:** Bei ungültigem Token: `ConfirmTokenInvalidError`.

### 4.5 Vollständige Kriterien für „Live-Execution erlaubt“

Alle müssen erfüllt sein (siehe `is_live_execution_allowed()`):

1. `environment == TradingEnvironment.LIVE`
2. `enable_live_trading == True` (Gate 1)
3. `live_mode_armed == True` (Gate 2)
4. `live_dry_run_mode == False` (technisches Gate; in Phase 71 nicht erreichbar)
5. Falls `require_confirm_token`: `confirm_token == LIVE_CONFIRM_TOKEN`

**Daten rein (aggregiert):** EnvironmentConfig (environment, enable_live_trading, live_mode_armed, live_dry_run_mode, require_confirm_token, confirm_token).  
**Daten raus:** Tuple `(allowed: bool, reason: str)`; bei Aktionen ggf. Exceptions und Audit-Log.

---

## 5. Live-Eligibility-Gates (Strategie & Portfolio)

`src/live/live_gates.py` prüft, ob eine **Strategie** oder ein **Portfolio** für Shadow/Testnet/Live **eligible** ist (kein R&D im Live-Pfad, Metriken, Diversifikation).

### 5.1 Strategy-Eligibility

- **Wo:** `check_strategy_live_eligibility()`.
- **Daten rein:** strategy_id, optional StrategyProfile, LivePolicies, Tiering-Config (z. B. config/strategy_tiering.toml), config/live_policies.toml.
- **Kriterien:** Tier core/aux (kein r_and_d/legacy), ggf. allow_live, Sharpe/MaxDD innerhalb Tier-Grenzen.
- **Daten raus:** `LiveGateResult` (entity_id, entity_type="strategy", is_eligible, reasons, details, tier, allow_live_flag). Bei Verstoß: `RnDLiveTradingBlockedError` wenn R&D für Live/Paper/Testnet genutzt wird.

### 5.2 Portfolio-Eligibility

- **Wo:** `check_portfolio_live_eligibility()`.
- **Daten rein:** portfolio_id, optional strategies/weights, LivePolicies, Tiering, Presets (config/portfolio_presets).
- **Kriterien:** Alle Strategien eligible, Mindestanzahl Strategien, max_concentration (Diversifikation).
- **Daten raus:** `LiveGateResult` (entity_type="portfolio", is_eligible, reasons, details).

---

## 6. Data-Safety-Gate

`src/data/safety/data_safety_gate.py` verhindert, dass **synthetische** Daten im **Live-Trading** verwendet werden (IDEA-RISK-008).

### 6.1 DataSafetyGate

- **Wo:** `DataSafetyGate.check(context)` / `DataSafetyGate.ensure_allowed(context)`.
- **Daten rein:** `DataSafetyContext`: source_kind (REAL, HISTORICAL, SYNTHETIC_OFFLINE_RT), usage (BACKTEST, RESEARCH, PAPER_TRADE, LIVE_TRADE).
- **Regeln:** SYNTHETIC_OFFLINE_RT ist für LIVE_TRADE verboten; für BACKTEST/RESEARCH/PAPER_TRADE erlaubt. REAL/HISTORICAL in allen Kontexten erlaubt.
- **Daten raus:** `DataSafetyResult` (allowed, reason, details); bei Verstoß `DataSafetyViolationError`.

---

## 7. Governance: LiveModeGate und enforce_live_mode_gate

### 7.1 LiveModeGate (WP0C)

- **Wo:** `src/governance/live_mode_gate.py` – LiveModeGate, create_gate(), is_live_allowed().
- **Zweck:** Blocked-by-default, explizite Freigabe, Config-Validierung, Audit von Mode-Übergängen.
- **Daten rein:** environment (ExecutionEnvironment), config (session_id, strategy_id, risk_limits, …), request_approval(requester, reason, config_hash).
- **Daten raus:** LiveModeGateState (environment, status BLOCKED/APPROVED/SUSPENDED/FAILED_VALIDATION), ValidationResult; Audit-Log (JSONL).

### 7.2 enforce_live_mode_gate (Fail-Fast)

- **Wo:** `enforce_live_mode_gate(config, env)`.
- **Daten rein:** config (live.enabled, live.operator_ack, session_id, strategy_id, risk_limits), env (z. B. "prod", "live").
- **Regeln:** Wenn live.enabled=True → env in {"prod","live"}, operator_ack == "I_UNDERSTAND_LIVE_TRADING", risk_runtime importierbar.
- **Daten raus:** Kein Rückgabewert; bei Verstoß `LiveModeViolationError` mit Fehlerliste.

---

## 8. Escalation-Gates (Infra)

`src/infra/escalation/manager.py`: Eskalation (Alerts nach außen) nur, wenn drei Gates durchlaufen:

- **Gate 1:** Escalation global enabled.
- **Gate 2:** current_environment in enabled_environments.
- **Gate 3:** event.severity in critical_severities.

**Daten rein:** EscalationEvent (severity, summary, …), Config (enabled, enabled_environments, critical_severities, targets).  
**Daten raus:** Aufruf an Provider (z. B. Alert-Sink); kein Rückgabewert nach außen (Fehler werden nur geloggt).

---

## 9. Datenfluss: Was kommt wo rein (aggregiert)

| Quelle / Gate-Eingang     | Daten / Typen                                                    | Verwendung / Gate                    |
|---------------------------|-------------------------------------------------------------------|--------------------------------------|
| Strategie / Session       | OrderIntent (symbol, side, qty, order_type, …)                   | Execution Stage 1–2                  |
| Config                    | environment, enable_live_trading, live_mode_armed, live_dry_run_mode, confirm_token | SafetyGuard, is_live_execution_allowed |
| Config                    | session_id, strategy_id, risk_limits, live.enabled, operator_ack  | LiveModeGate, enforce_live_mode_gate |
| Tiering / Policies        | strategy_tiering.toml, live_policies.toml, portfolio presets     | Live Eligibility (Strategy/Portfolio) |
| Datenquelle               | DataSafetyContext (source_kind, usage)                           | DataSafetyGate                       |
| Market Data               | Candles, Buffer (z. B. poll_latest, get_buffer)                   | Live Session, Strategie-Signal       |
| Risk-Config               | LiveRiskConfig, risk_limits, starting_cash                       | LiveRiskLimits, RiskHook             |
| Escalation-Config         | enabled, enabled_environments, critical_severities, targets      | EscalationManager                    |

---

## 10. Datenfluss: Was geht wo raus (aggregiert)

| Ziel / Gate-Ausgang   | Daten / Typen                                                    | Herkunft / Gate                     |
|------------------------|-------------------------------------------------------------------|-------------------------------------|
| Pipeline-Ergebnis      | PipelineResult (success, order, ledger_entries, reason_code, …)   | Execution Stages 1–8                |
| Events (Beta)          | INTENT, RISK_REJECT, ORDER, FILL, … (execution_events.jsonl)     | Orchestrator, Kill Switch, Stage 3   |
| Ledger                 | OrderLedger, PositionLedger, AuditLog, LedgerEntries             | Stages 2–7, Recon                   |
| Recon                  | Daten für ReconciliationEngine                                   | Stage 8                             |
| Live-Eligibility       | LiveGateResult (is_eligible, reasons, details)                   | live_gates (Strategy/Portfolio)     |
| Data Safety            | DataSafetyResult; bei Verstoß DataSafetyViolationError          | DataSafetyGate                      |
| Safety / Live          | (allowed, reason); Exceptions (LiveTradingDisabledError, …)      | SafetyGuard, is_live_execution_allowed |
| Governance             | LiveModeGateState, ValidationResult, Audit-Log                   | LiveModeGate                        |
| Alerts / Eskalation    | Send an Targets (z. B. Alert-Sink)                               | EscalationManager (nach Gate 1–3)   |
| Reporting / Ops        | Live-Status-Reports, Aggregates, Dashboards                      | reporting, live_status_report       |

---

## 11. Live-Spezifischer Datenfluss (Shadow / Testnet / Live-Design)

### 11.1 Live-Session (Strategy-to-Execution Bridge)

- **Rein:** LiveSessionConfig (mode=shadow/testnet, strategy_key, symbol, timeframe), Data-Source (poll_latest, get_buffer), EnvironmentConfig, RiskLimits, SafetyGuard.
- **Ablauf (pro Step):** Candle holen → Preis im Executor-Context setzen → Strategie-Signal aus Buffer → bei Signaländerung Orders → ExecutionPipeline (mit Safety) → Metriken.
- **Raus:** OrderExecutionResults, LiveSessionMetrics, Logging, ggf. Registry-Einträge (register_live_session_run).

### 11.2 Sicherheitsreihenfolge vor „echter“ Live-Order

1. **DataSafetyGate:** Keine synthetischen Daten im LIVE_TRADE-Kontext.
2. **Live Eligibility:** Strategie/Portfolio eligible (live_gates).
3. **Governance:** LiveModeGate / enforce_live_mode_gate (Config, env, operator_ack).
4. **SafetyGuard:** Gate 1 + Gate 2 + technisches Gate + Confirm-Token.
5. **Execution:** Route Selection (kein Live ohne Freigabe), Stage 3 Pre-Trade Risk Gate, ggf. Kill Switch.

In **Phase 71** ist echter Live-Trade durch `live_dry_run_mode=True` und explizites LiveNotImplementedError blockiert; der Datenfluss und die Gate-Reihenfolge sind dennoch für spätere Phasen vorgesehen.

### 11.3 Live-Reporting und -Monitoring

- **Rein:** Session-Daten, Order/Fill-Events, Risk-Check-Ergebnisse, Config-Snapshots.
- **Raus:** Live-Status-Reports (Aggregate, HTML/Markdown), Alerts (Phase 49), Dashboard-Daten (Live Track, Ops), Telemetrie (strategy_risk_telemetry).

---

## 12. Kurzreferenz: Gate → Rein/Raus

| Gate / Komponente           | Daten rein (Kurz)                    | Daten raus (Kurz)                          |
|-----------------------------|--------------------------------------|-------------------------------------------|
| Stage 1 Intent Intake       | OrderIntent                          | correlation_id, idempotency_key, INTENT   |
| Stage 2 Contract Validation  | Intent, run_id, session_id           | Order (CREATED), ggf. Fehler              |
| Stage 3 Pre-Trade Risk Gate | Order                                | RiskResult, REJECT/Fail, Ledger           |
| Stage 4 Route Selection     | Order, execution_mode                | Adapter oder POLICY_LIVE_NOT_ENABLED      |
| Stage 5–8                   | Order, idempotency_key, Events      | ExecutionEvent, Ledger, Recon, Result     |
| SafetyGuard (Gate 1/2/tech) | EnvironmentConfig                    | (allowed, reason), Exceptions, Audit       |
| check_strategy_live_eligibility | strategy_id, policies, tiering   | LiveGateResult                            |
| check_portfolio_live_eligibility | portfolio_id, strategies, weights | LiveGateResult                            |
| DataSafetyGate              | DataSafetyContext                    | DataSafetyResult, ggf. Exception          |
| LiveModeGate                | config, environment, approval request| State, ValidationResult, Audit            |
| enforce_live_mode_gate      | config, env                          | None / LiveModeViolationError             |
| EscalationManager           | EscalationEvent, Config              | Send to targets (Alerts)                  |

---

## 13. Referenzen

- Execution: `src/execution/orchestrator.py`, `src/execution/pipeline.py`
- Live/Safety: `src/live/safety.py`, `src/live/live_gates.py`, `src/core/environment.py`
- Data Safety: `src/data/safety/data_safety_gate.py`
- Governance: `src/governance/live_mode_gate.py`
- Escalation: `src/infra/escalation/manager.py`
- Docs: `docs/PHASE_71_LIVE_EXECUTION_DESIGN_AND_GATING.md`, `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md`
