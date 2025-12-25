# Peak_Trade — Shadow Trading Prep Roadmap

**Version:** 1.0  
**Datum:** 2025-12-25  
**Status:** 📋 PLANNING  
**Ziel:** Systematische Vorbereitung für Shadow Trading nach Backtest-Validierung

---

## 🎯 Executive Summary

Shadow Trading ist die kritische Brücke zwischen Backtesting und Live-Trading. In dieser Phase werden Strategien mit **echten Marktdaten in Echtzeit** ausgeführt, aber **ohne echte Orders**. Ziel: Validierung, dass die Backtest-Performance unter realen Bedingungen reproduzierbar ist.

**Timeline:** 12-16 Wochen (3-4 Monate)  
**Voraussetzung:** Risk-Layer 100% complete, Backtest-Engine validiert

---

## 📊 Phasen-Übersicht

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SHADOW TRADING PREP ROADMAP                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Phase 1: Infrastructure     ████████░░░░░░░░░░░░░░░░░░  Wochen 1-3    │
│  Phase 2: Data Pipeline      ░░░░░░░░████████░░░░░░░░░░  Wochen 4-6    │
│  Phase 3: Shadow Engine      ░░░░░░░░░░░░░░░░████████░░  Wochen 7-10   │
│  Phase 4: Signal Validation  ░░░░░░░░░░░░░░░░░░░░░░████  Wochen 11-12  │
│  Phase 5: Ops & Monitoring   ░░░░░░░░░░░░░░░░░░░░░░░░██  Wochen 13-16  │
│                                                                         │
│  ──────────────────────────────────────────────────────────────────     │
│  Gate: 90%+ Signal Match     │  Gate: 4 Wochen stabil   │  → Testnet   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔷 Phase 1: Infrastructure Setup (Wochen 1-3)

### Ziel
Technische Grundlagen für Echtzeit-Datenverarbeitung und Shadow Execution.

### Deliverables

| # | Deliverable | Datei/Location | Effort |
|---|-------------|----------------|--------|
| 1.1 | WebSocket Client für Kraken | `src/data/kraken_ws.py` | M |
| 1.2 | Message Queue (Redis/ZMQ) | `src/infra/message_queue.py` | M |
| 1.3 | Timestamp Synchronization | `src/infra/time_sync.py` | S |
| 1.4 | Config für Shadow Mode | `config/shadow.toml` | S |
| 1.5 | Logging Infrastructure | `src/infra/shadow_logger.py` | S |

### Akzeptanzkriterien

- [ ] WebSocket verbindet zu Kraken und empfängt Trades/OHLCV
- [ ] Latenz < 100ms zwischen Kraken-Event und lokaler Verarbeitung
- [ ] Message Queue verarbeitet 1000+ msg/sec ohne Verlust
- [ ] UTC-Timestamps mit ms-Präzision
- [ ] Structured Logging (JSON) für alle Shadow-Events

### Config Template

```toml
# config/shadow.toml
[shadow]
enabled = true
mode = "shadow"  # shadow | paper | live (NEVER auto-enable live)

[shadow.data]
source = "kraken_ws"
symbols = ["BTC/EUR", "ETH/EUR"]
reconnect_delay_sec = 5
max_reconnect_attempts = 10

[shadow.logging]
level = "INFO"
format = "json"
file = "logs/shadow_{date}.jsonl"
rotate_mb = 100

[shadow.validation]
require_backtest_match = true
min_signal_match_rate = 0.90
```

### Tests (15+)

```
tests/infra/
├── test_kraken_ws_connection.py
├── test_kraken_ws_reconnect.py
├── test_message_queue_throughput.py
├── test_time_sync_accuracy.py
└── test_shadow_config_validation.py
```

---

## 🔷 Phase 2: Live Data Pipeline (Wochen 4-6)

### Ziel
Echtzeit-Daten in das gleiche Format bringen wie Backtest-Daten (OHLCV-Normalisierung).

### Deliverables

| # | Deliverable | Datei/Location | Effort |
|---|-------------|----------------|--------|
| 2.1 | Tick-to-OHLCV Aggregator | `src/data/tick_aggregator.py` | M |
| 2.2 | Real-time Normalizer | `src/data/realtime_normalizer.py` | M |
| 2.3 | Data Quality Monitor | `src/data/quality_monitor.py` | M |
| 2.4 | Gap Detection & Handling | `src/data/gap_handler.py` | S |
| 2.5 | Historical Backfill | `src/data/backfill.py` | M |

### Akzeptanzkriterien

- [ ] Tick-Daten werden korrekt zu 1m/5m/15m/1h OHLCV aggregiert
- [ ] Output-Format identisch zu `DataNormalizer.normalize()` aus Backtest
- [ ] Lücken werden erkannt und geloggt (nicht still ignoriert)
- [ ] Backfill holt fehlende Daten nach Reconnect
- [ ] Data Quality Score (Completeness, Latency, Accuracy) wird berechnet

### Architektur

```
┌──────────────┐    ┌───────────────┐    ┌────────────────┐
│  Kraken WS   │───▶│ Tick Aggregator│───▶│ OHLCV Buffer   │
│  (Trades)    │    │  (1m candles)  │    │ (Ring Buffer)  │
└──────────────┘    └───────────────┘    └────────┬───────┘
                                                   │
                                                   ▼
┌──────────────┐    ┌───────────────┐    ┌────────────────┐
│  Strategy    │◀───│  Normalizer   │◀───│ Quality Check  │
│  Engine      │    │  (OHLCV fmt)  │    │ (Gap/Latency)  │
└──────────────┘    └───────────────┘    └────────────────┘
```

### Data Quality Metrics

```python
@dataclass
class DataQualityReport:
    """Echtzeit Data Quality Metriken."""
    timestamp: datetime
    symbol: str

    # Completeness
    expected_candles: int
    received_candles: int
    completeness_pct: float  # >= 99.5% required

    # Latency
    avg_latency_ms: float    # < 100ms target
    max_latency_ms: float    # < 500ms hard limit
    p99_latency_ms: float

    # Gaps
    gap_count: int
    total_gap_duration_sec: float

    # Accuracy (vs REST API cross-check)
    price_deviation_bps: float  # < 1 bps
```

### Tests (20+)

```
tests/data/
├── test_tick_aggregator_1m.py
├── test_tick_aggregator_edge_cases.py
├── test_realtime_normalizer_format.py
├── test_gap_detection.py
├── test_gap_handling_strategies.py
├── test_backfill_integrity.py
├── test_quality_monitor_alerts.py
└── test_data_quality_thresholds.py
```

---

## 🔷 Phase 3: Shadow Execution Engine (Wochen 7-10)

### Ziel
Strategien in Echtzeit ausführen, Signale generieren, aber KEINE echten Orders.

### Deliverables

| # | Deliverable | Datei/Location | Effort |
|---|-------------|----------------|--------|
| 3.1 | Shadow Executor | `src/shadow/executor.py` | L |
| 3.2 | Virtual Portfolio | `src/shadow/virtual_portfolio.py` | M |
| 3.3 | Signal Recorder | `src/shadow/signal_recorder.py` | M |
| 3.4 | Slippage Simulator | `src/shadow/slippage_sim.py` | M |
| 3.5 | Shadow Session Manager | `src/shadow/session.py` | M |
| 3.6 | Performance Tracker | `src/shadow/performance.py` | M |

### Akzeptanzkriterien

- [ ] Strategien erhalten Echtzeit-OHLCV und generieren Signale
- [ ] Jedes Signal wird mit Timestamp, Preis, Kontext geloggt
- [ ] Virtual Portfolio trackt hypothetische Positionen (inkl. Fees)
- [ ] Slippage wird realistisch simuliert (basierend auf Orderbook-Daten)
- [ ] Session-State kann gespeichert und wiederhergestellt werden
- [ ] Performance-Metriken werden in Echtzeit berechnet

### Shadow Executor Interface

```python
class ShadowExecutor:
    """
    Führt Strategien in Echtzeit aus, ohne echte Orders.

    CRITICAL: Keine Verbindung zur Order-API!
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        config: ShadowConfig,
        portfolio: VirtualPortfolio,
        recorder: SignalRecorder,
    ):
        self.strategy = strategy
        self.config = config
        self.portfolio = portfolio
        self.recorder = recorder

        # SAFETY: Verify no live trading capability
        assert not hasattr(self, 'order_client'), "Shadow mode must not have order client"

    def on_candle(self, candle: OHLCVCandle) -> Optional[Signal]:
        """
        Verarbeitet neue Kerze und generiert ggf. Signal.

        Returns:
            Signal oder None
        """
        # 1. Strategy evaluieren
        signal = self.strategy.evaluate(candle)

        # 2. Signal aufzeichnen (immer, auch None)
        self.recorder.record(
            timestamp=candle.timestamp,
            signal=signal,
            candle=candle,
            portfolio_state=self.portfolio.snapshot(),
        )

        # 3. Virtual Portfolio updaten (wenn Signal)
        if signal:
            fill = self._simulate_fill(signal, candle)
            self.portfolio.apply_fill(fill)

        return signal

    def _simulate_fill(self, signal: Signal, candle: OHLCVCandle) -> VirtualFill:
        """Simuliert Order-Ausführung mit realistischem Slippage."""
        slippage = self.slippage_sim.estimate(
            side=signal.side,
            size=signal.size,
            orderbook_snapshot=self._get_orderbook(),
        )

        return VirtualFill(
            timestamp=datetime.utcnow(),
            signal=signal,
            executed_price=candle.close + slippage,
            executed_size=signal.size,
            fees=self._calculate_fees(signal.size, candle.close),
        )
```

### Signal Recording Schema

```python
@dataclass
class RecordedSignal:
    """Vollständig aufgezeichnetes Signal für spätere Analyse."""

    # Identifikation
    session_id: str
    signal_id: str

    # Timing
    candle_timestamp: datetime      # Wann die Kerze geschlossen wurde
    signal_timestamp: datetime      # Wann das Signal generiert wurde
    latency_ms: float               # signal_ts - candle_ts

    # Signal Details
    symbol: str
    side: Literal["BUY", "SELL", "HOLD"]
    size: float
    entry_price: float              # Preis bei Signal-Generierung

    # Kontext
    strategy_name: str
    strategy_params: dict
    indicator_values: dict          # MA, RSI, etc. zum Zeitpunkt

    # Virtual Execution
    simulated_fill_price: float
    simulated_slippage_bps: float
    simulated_fees: float

    # Portfolio State
    portfolio_value_before: float
    portfolio_value_after: float
    position_before: float
    position_after: float
```

### Tests (25+)

```
tests/shadow/
├── test_shadow_executor_lifecycle.py
├── test_shadow_executor_no_live_orders.py  # CRITICAL
├── test_virtual_portfolio_tracking.py
├── test_virtual_portfolio_fees.py
├── test_signal_recorder_completeness.py
├── test_signal_recorder_format.py
├── test_slippage_simulation.py
├── test_session_persistence.py
├── test_session_recovery.py
└── test_performance_metrics.py
```

---

## 🔷 Phase 4: Signal Validation & Drift Detection (Wochen 11-12)

### Ziel
Vergleich Shadow-Signale vs. Backtest-Signale → Drift Detection.

### Deliverables

| # | Deliverable | Datei/Location | Effort |
|---|-------------|----------------|--------|
| 4.1 | Signal Comparator | `src/validation/signal_comparator.py` | M |
| 4.2 | Backtest Replayer | `src/validation/backtest_replayer.py` | M |
| 4.3 | Drift Detector | `src/validation/drift_detector.py` | M |
| 4.4 | Validation Report Generator | `src/validation/report.py` | M |
| 4.5 | Alert System | `src/validation/alerts.py` | S |

### Akzeptanzkriterien

- [ ] Shadow-Signale können mit historischen Backtest-Signalen verglichen werden
- [ ] Signal Match Rate wird kontinuierlich berechnet (Ziel: ≥90%)
- [ ] Drift wird erkannt und klassifiziert (Data Drift, Concept Drift, Bug)
- [ ] Automatische Alerts bei Match Rate < 85%
- [ ] Wöchentliche Validation Reports

### Signal Match Definition

```python
def signals_match(shadow: RecordedSignal, backtest: BacktestSignal) -> bool:
    """
    Prüft ob Shadow-Signal mit Backtest-Signal übereinstimmt.

    Match-Kriterien:
    1. Gleiche Side (BUY/SELL/HOLD)
    2. Gleiches Symbol
    3. Timestamp innerhalb Toleranz (±1 Kerze)
    4. Entry-Preis innerhalb Toleranz (±0.1%)
    """
    return (
        shadow.side == backtest.side
        and shadow.symbol == backtest.symbol
        and abs((shadow.candle_timestamp - backtest.timestamp).seconds) <= 60
        and abs(shadow.entry_price - backtest.entry_price) / backtest.entry_price < 0.001
    )
```

### Drift Types

```python
class DriftType(Enum):
    """Klassifikation von Signal-Abweichungen."""

    # Data-related
    DATA_LATENCY = "data_latency"       # Verzögerte Daten → verpasste Signale
    DATA_GAP = "data_gap"               # Fehlende Daten → ausgelassene Signale
    DATA_QUALITY = "data_quality"       # Schlechte Datenqualität → falsche Signale

    # Strategy-related
    CONCEPT_DRIFT = "concept_drift"     # Marktregime hat sich geändert
    PARAMETER_SENSITIVITY = "param_sens" # Strategie reagiert anders auf Echtzeitdaten

    # Technical
    TIMING_ISSUE = "timing"             # Race Conditions, Reihenfolge-Probleme
    CALCULATION_BUG = "bug"             # Implementierungsfehler

    # Unknown
    UNKNOWN = "unknown"                 # Muss manuell untersucht werden
```

### Validation Report Schema

```markdown
# Shadow Trading Validation Report

**Zeitraum:** 2025-01-01 bis 2025-01-07
**Strategie:** MA_Crossover (fast=50, slow=200)
**Symbol:** BTC/EUR

## Signal Match Summary

| Metrik | Wert | Status |
|--------|------|--------|
| Total Shadow Signals | 47 | — |
| Matched Signals | 44 | ✅ |
| Mismatched Signals | 3 | ⚠️ |
| **Match Rate** | **93.6%** | ✅ ≥90% |

## Mismatch Analysis

| # | Timestamp | Shadow | Backtest | Drift Type | Notes |
|---|-----------|--------|----------|------------|-------|
| 1 | 2025-01-03 14:00 | BUY | HOLD | DATA_LATENCY | 200ms delay |
| 2 | 2025-01-05 09:15 | SELL | SELL | TIMING | 1.2s earlier |
| 3 | 2025-01-06 22:00 | HOLD | BUY | DATA_GAP | 3 candles missing |

## Performance Comparison

| Metrik | Shadow | Backtest | Δ |
|--------|--------|----------|---|
| Total Return | +4.2% | +4.5% | -0.3% |
| Sharpe Ratio | 1.45 | 1.52 | -0.07 |
| Max Drawdown | -3.1% | -2.8% | -0.3% |
| Win Rate | 58% | 61% | -3% |

## Recommendation

✅ **CONTINUE SHADOW TRADING**
- Match Rate über Threshold (93.6% > 90%)
- Performance-Delta akzeptabel (<1%)
- Bekannte Drift-Ursachen (Data Latency, Gaps)

**Nächste Schritte:**
1. Latency-Optimierung für WebSocket-Verbindung
2. Gap-Handling verbessern (Backfill beschleunigen)
3. Weitere Woche Shadow Trading vor Testnet-Gate
```

### Tests (20+)

```
tests/validation/
├── test_signal_comparator_exact_match.py
├── test_signal_comparator_tolerance.py
├── test_backtest_replayer.py
├── test_drift_detector_classification.py
├── test_drift_detector_thresholds.py
├── test_validation_report_format.py
├── test_alert_triggers.py
└── test_match_rate_calculation.py
```

---

## 🔷 Phase 5: Ops & Monitoring (Wochen 13-16)

### Ziel
Production-Grade Monitoring, Alerting, und Ops-Tooling für Shadow Trading.

### Deliverables

| # | Deliverable | Datei/Location | Effort |
|---|-------------|----------------|--------|
| 5.1 | Shadow Dashboard | `src/dashboard/shadow_dashboard.py` | L |
| 5.2 | Metrics Exporter | `src/observability/metrics.py` | M |
| 5.3 | Alert Manager | `src/observability/alerts.py` | M |
| 5.4 | Health Check Endpoint | `src/ops/health.py` | S |
| 5.5 | Ops Inspector Integration | `scripts/ops/shadow_inspector.sh` | M |
| 5.6 | Runbook | `docs/ops/SHADOW_RUNBOOK.md` | M |

### Akzeptanzkriterien

- [ ] Dashboard zeigt Live-Metriken (Signal Rate, P&L, Drift)
- [ ] Prometheus-Metriken für alle Key-Indicators
- [ ] Alerts bei: Match Rate < 85%, Latency > 500ms, Gap > 5min
- [ ] Health Check gibt Auskunft über System-Zustand
- [ ] Runbook dokumentiert alle Ops-Prozeduren

### Metrics to Track

```python
# Prometheus Metrics
shadow_signals_total = Counter(
    "shadow_signals_total",
    "Total number of signals generated",
    ["strategy", "symbol", "side"]
)

shadow_signal_match_rate = Gauge(
    "shadow_signal_match_rate",
    "Current signal match rate vs backtest",
    ["strategy", "symbol"]
)

shadow_latency_seconds = Histogram(
    "shadow_latency_seconds",
    "Latency from candle close to signal generation",
    ["strategy", "symbol"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)

shadow_pnl_unrealized = Gauge(
    "shadow_pnl_unrealized",
    "Unrealized PnL in shadow portfolio",
    ["strategy", "symbol"]
)

shadow_data_gaps_total = Counter(
    "shadow_data_gaps_total",
    "Total number of data gaps detected",
    ["symbol"]
)
```

### Alert Rules

```yaml
# alertmanager/rules/shadow.yml
groups:
  - name: shadow_trading
    rules:
      - alert: ShadowMatchRateLow
        expr: shadow_signal_match_rate < 0.85
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Shadow signal match rate below 85%"

      - alert: ShadowMatchRateCritical
        expr: shadow_signal_match_rate < 0.75
        for: 30m
        labels:
          severity: critical
        annotations:
          summary: "Shadow signal match rate critical - investigate immediately"

      - alert: ShadowLatencyHigh
        expr: histogram_quantile(0.99, shadow_latency_seconds) > 0.5
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Shadow trading latency p99 > 500ms"

      - alert: ShadowDataGap
        expr: increase(shadow_data_gaps_total[1h]) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Multiple data gaps in last hour"
```

### Tests (15+)

```
tests/ops/
├── test_dashboard_metrics.py
├── test_metrics_exporter.py
├── test_alert_thresholds.py
├── test_health_check_endpoint.py
└── test_shadow_inspector.py
```

---

## 🚦 Gates & Checkpoints

### Gate 1: Infrastructure Ready (Ende Woche 3)

**Kriterien:**
- [ ] WebSocket-Verbindung stabil (24h ohne Disconnect)
- [ ] Message Queue Throughput ≥1000 msg/sec
- [ ] Alle Phase-1-Tests grün
- [ ] Config für Shadow Mode dokumentiert

**Go/No-Go Decision:** Peak_Risk + Peak_Data

---

### Gate 2: Data Pipeline Validated (Ende Woche 6)

**Kriterien:**
- [ ] Data Quality Score ≥99% Completeness
- [ ] Latency p99 <100ms
- [ ] OHLCV-Format identisch zu Backtest
- [ ] 48h Continuous Run ohne Gaps

**Go/No-Go Decision:** Peak_Data + Peak_Backtest

---

### Gate 3: Shadow Engine Operational (Ende Woche 10)

**Kriterien:**
- [ ] Shadow Executor läuft 7 Tage stabil
- [ ] Alle Signale werden aufgezeichnet
- [ ] Virtual Portfolio trackt Positionen korrekt
- [ ] Keine Verbindung zur Order-API (Audit)

**Go/No-Go Decision:** Peak_Risk (MANDATORY)

---

### Gate 4: Signal Validation Passed (Ende Woche 12)

**Kriterien:**
- [ ] Signal Match Rate ≥90% über 2 Wochen
- [ ] Kein unklärter Drift
- [ ] Performance-Delta <2% vs Backtest
- [ ] Validation Report reviewed

**Go/No-Go Decision:** Peak_Strategy + Peak_Risk

---

### Gate 5: Ops Ready for Testnet (Ende Woche 16)

**Kriterien:**
- [ ] Monitoring Dashboard operational
- [ ] Alerting funktioniert (Test-Alerts ausgelöst)
- [ ] Runbook vollständig und reviewed
- [ ] 4 Wochen stabiler Shadow-Betrieb
- [ ] Match Rate durchgehend ≥90%

**Go/No-Go Decision:** ALL STAKEHOLDERS

---

## ⚠️ Risiken & Mitigations

| Risiko | Impact | Probability | Mitigation |
|--------|--------|-------------|------------|
| WebSocket-Disconnects | High | Medium | Exponential Backoff, Failover |
| Data Gaps | High | Medium | Backfill-Mechanismus, Lücken-Toleranz |
| Signal Drift | High | Low | Kontinuierliche Validierung, Alerts |
| Latency-Spikes | Medium | Medium | Buffer, Async Processing |
| Config-Fehler | High | Low | Config Validation, Defaults |
| Versehentliche Live-Orders | Critical | Very Low | Code Audit, No Order-API in Shadow |

---

## 📋 Checklisten

### Pre-Shadow Checklist

- [ ] Risk-Layer 100% implementiert und getestet
- [ ] Backtest-Engine validiert (alle Tests grün)
- [ ] Strategie hat ≥6 Monate Backtest-Daten
- [ ] Sharpe Ratio >1.0, Max DD <20%
- [ ] Config für Shadow Mode erstellt
- [ ] Logging-Infrastruktur ready
- [ ] Team über Shadow-Start informiert

### Daily Shadow Ops Checklist

- [ ] Data Quality Report prüfen
- [ ] Signal Match Rate prüfen
- [ ] Latency-Metriken prüfen
- [ ] Open Alerts reviewen
- [ ] Virtual P&L dokumentieren
- [ ] Auffälligkeiten loggen

### Weekly Shadow Review Checklist

- [ ] Validation Report generieren
- [ ] Match Rate Trend analysieren
- [ ] Drift-Fälle klassifizieren
- [ ] Performance vs Backtest vergleichen
- [ ] Entscheidung: Continue / Investigate / Stop

---

## 🎯 Success Criteria für Testnet-Progression

**ALLE folgenden Kriterien müssen erfüllt sein:**

1. **Signal Match Rate:** ≥90% über mindestens 4 Wochen
2. **Stabiler Betrieb:** Keine kritischen Ausfälle in 4 Wochen
3. **Performance-Alignment:** Shadow P&L innerhalb ±5% von Backtest
4. **Data Quality:** ≥99% Completeness, p99 Latency <200ms
5. **Ops Readiness:** Monitoring, Alerting, Runbook operational
6. **Risk Sign-Off:** Peak_Risk hat explizit freigegeben
7. **Dokumentation:** Alle Phasen dokumentiert, Lessons Learned erfasst

---

## 📅 Timeline Summary

| Phase | Wochen | Hauptziel | Key Deliverable |
|-------|--------|-----------|-----------------|
| 1. Infrastructure | 1-3 | WebSocket + Queue | `kraken_ws.py` |
| 2. Data Pipeline | 4-6 | Echtzeit-OHLCV | `tick_aggregator.py` |
| 3. Shadow Engine | 7-10 | Signal Generation | `shadow/executor.py` |
| 4. Validation | 11-12 | Drift Detection | `signal_comparator.py` |
| 5. Ops | 13-16 | Monitoring | Dashboard + Runbook |

**Total: 16 Wochen (4 Monate)**

---

## 🔜 Nach Shadow Trading

Bei erfolgreichem Abschluss aller Gates:

```
Shadow Trading (12-16 Wochen)
         │
         ▼
┌─────────────────────┐
│  TESTNET TRADING    │  ◀── Echte Orders auf Testnet
│  (8-12 Wochen)      │      (Fake Money)
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  PAPER TRADING      │  ◀── Echte Preise, simulierte Orders
│  (4-8 Wochen)       │      (Parallel zu Testnet)
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  LIVE TRADING       │  ◀── Erst nach 6+ Monaten Validation
│  (Minimal Size)     │      + Risk Sign-Off
└─────────────────────┘
```

---

**Erstellt:** 2025-12-25  
**Nächste Review:** Nach Phase 1 Gate  
**Owner:** Peak_Trade Team

---

*„Shadow Trading ist keine Abkürzung – es ist der Beweis, dass deine Strategie auch in Echtzeit funktioniert."*
