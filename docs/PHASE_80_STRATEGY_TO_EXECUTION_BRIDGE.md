# Phase 80: Strategy-to-Execution Bridge & Shadow/Testnet Runner v0

**Status:** ✅ Implementiert  
**Datum:** 2025-12-08  
**Autor:** Peak_Trade Engineering

---

## 1. Übersicht

Phase 80 implementiert eine **Strategy-to-Execution Bridge**, die einen orchestrierten Flow von konfigurierten Strategien über Signale zu Orders bietet, welche über die `ExecutionPipeline` an sichere Targets (Shadow/Testnet) durchgereicht werden.

### Kernkomponenten

| Komponente | Pfad | Beschreibung |
|------------|------|--------------|
| `LiveSessionRunner` | `src/execution/live_session.py` | Orchestrator für Strategy-to-Execution Flow |
| `LiveSessionConfig` | `src/execution/live_session.py` | Parametrisierbare Session-Konfiguration |
| CLI-Skript | `scripts/run_execution_session.py` | Command-Line Entry Point |
| Tests | `tests/test_live_session_runner.py` | 24 Unit- und Smoke-Tests |

---

## 2. Architektur

### 2.1 Flow-Diagramm

```
┌─────────────────────────────────────────────────────────────────┐
│                    LiveSessionRunner                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌─────────────┐     ┌──────────────────┐  │
│  │ Data-Source  │────▶│  Strategy   │────▶│ Signal-Event     │  │
│  │ (Kraken/Fake)│     │ (Registry)  │     │ (−1/0/+1)        │  │
│  └──────────────┘     └─────────────┘     └────────┬─────────┘  │
│                                                     │            │
│                                                     ▼            │
│                              ┌──────────────────────────────┐   │
│                              │    ExecutionPipeline         │   │
│                              │   .execute_with_safety()     │   │
│                              └──────────────┬───────────────┘   │
│                                             │                   │
│         ┌───────────────────────────────────┼───────────────┐   │
│         │                                   │               │   │
│         ▼                                   ▼               ▼   │
│  ┌──────────────┐                 ┌──────────────┐ ┌──────────┐│
│  │ SafetyGuard  │                 │ RiskLimits   │ │ Executor ││
│  │ (Phase 17)   │                 │ (Phase 46)   │ │ (Shadow) ││
│  └──────────────┘                 └──────────────┘ └──────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Ausführungsmodi

| Mode | Beschreibung | API-Calls | Phase 80 Status |
|------|--------------|-----------|-----------------|
| `shadow` | Paper-/Dummy-Execution | Keine | ✅ Voll unterstützt |
| `testnet` | Testnet mit validate_only | Nur Validierung | ✅ Als Dry-Run |
| `live` | Echte Orders | Echt | ❌ **HART BLOCKIERT** |

---

## 3. Safety-First Design

### 3.1 LIVE-Mode Blockierung

Phase 80 blockiert LIVE-Mode an **mehreren Stellen**:

```python
# 1. LiveSessionConfig.__post_init__()
if self.mode == "live":
    raise LiveModeNotAllowedError(
        "LIVE-Mode ist in Phase 80 NICHT erlaubt!"
    )

# 2. LiveSessionRunner.__init__()
if session_config.mode == "live":
    raise LiveModeNotAllowedError(...)

# 3. CLI argparse
parser.add_argument(
    "--mode",
    choices=["shadow", "testnet"],  # "live" nicht in choices!
)
```

### 3.2 Bestehende Safety-Komponenten

Phase 80 nutzt und erweitert bestehende Safety-Layer:

- **SafetyGuard** (Phase 17): Environment-Checks, Audit-Logging
- **LiveRiskLimits** (Phase 46): Order-Validierung, Notional-Limits
- **ExecutionPipeline.execute_with_safety()** (Phase 16A): Zentrale Safety-Prüfung

---

## 4. Verwendung

### 4.1 CLI-Beispiele

```bash
# Shadow-Mode (Default) - Simulation ohne API-Calls
python3 scripts/run_execution_session.py --strategy ma_crossover

# Mit spezifischem Symbol und Timeframe
python3 scripts/run_execution_session.py \
    --strategy rsi_reversion \
    --symbol ETH/EUR \
    --timeframe 5m

# Testnet-Mode (Dry-Run mit validate_only)
python3 scripts/run_execution_session.py \
    --mode testnet \
    --strategy ma_crossover

# Für begrenzte Dauer (30 Minuten)
python3 scripts/run_execution_session.py \
    --strategy ma_crossover \
    --duration 30

# Für N Schritte
python3 scripts/run_execution_session.py \
    --strategy ma_crossover \
    --steps 100

# Dry-Run (nur Config validieren)
python3 scripts/run_execution_session.py \
    --strategy ma_crossover \
    --dry-run

# Verfügbare Strategien auflisten
python3 scripts/run_execution_session.py --list-strategies
```

### 4.2 Programmatische Verwendung

```python
from src.execution.live_session import LiveSessionConfig, LiveSessionRunner
from src.core.peak_config import load_config

# Config erstellen
config = LiveSessionConfig(
    mode="shadow",
    strategy_key="ma_crossover",
    symbol="BTC/EUR",
    timeframe="1m",
    warmup_candles=200,
    position_fraction=0.1,
)

# PeakConfig laden
peak_config = load_config("config/config.toml")

# Runner erstellen
runner = LiveSessionRunner.from_config(config, peak_config=peak_config)

# Warmup (lädt historische Daten)
runner.warmup()

# Option A: N Schritte ausführen
results = runner.run_n_steps(10, sleep_between=True)

# Option B: Für bestimmte Dauer
results = runner.run_for_duration(minutes=30)

# Option C: Unbegrenzt (Ctrl+C zum Stoppen)
runner.run_forever()

# Zusammenfassung
print(runner.get_summary())
```

---

## 5. Komponenten-Details

### 5.1 LiveSessionConfig

Parametrisierbare Konfiguration für Sessions:

```python
@dataclass
class LiveSessionConfig:
    mode: Literal["shadow", "testnet"] = "shadow"
    strategy_key: str = "ma_crossover"
    symbol: str = "BTC/EUR"
    timeframe: str = "1m"
    config_path: str = "config/config.toml"
    warmup_candles: int = 200
    position_fraction: float = 0.1
    poll_interval_seconds: float = 60.0
    fee_rate: float = 0.001
    slippage_bps: float = 5.0
    start_balance: float = 10000.0
    enable_risk_limits: bool = True
    enable_logging: bool = True
    run_id: Optional[str] = None
```

### 5.2 LiveSessionRunner

Orchestriert den kompletten Execution-Flow:

| Methode | Beschreibung |
|---------|--------------|
| `from_config()` | Factory: Erstellt Runner aus Config |
| `warmup()` | Lädt historische Daten für Strategie |
| `step_once()` | Führt einen einzelnen Step aus |
| `run_n_steps(n)` | Führt N Schritte aus |
| `run_for_duration(min)` | Läuft für bestimmte Zeit |
| `run_forever()` | Unbegrenzter Loop (Ctrl+C) |
| `shutdown()` | Graceful Shutdown |
| `get_summary()` | Gibt Session-Zusammenfassung zurück |

### 5.3 LiveSessionMetrics

Laufzeit-Metriken der Session:

```python
@dataclass
class LiveSessionMetrics:
    steps: int = 0
    start_time: Optional[datetime] = None
    last_bar_time: Optional[datetime] = None
    total_orders_generated: int = 0
    orders_executed: int = 0
    orders_rejected: int = 0
    orders_blocked_risk: int = 0
    current_position: float = 0.0
    last_signal: int = 0
```

---

## 6. Integration mit bestehender Architektur

Phase 80 integriert sich nahtlos mit:

| Bestehende Komponente | Integration |
|----------------------|-------------|
| `ExecutionPipeline` (Phase 16A) | Nutzt `execute_with_safety()` |
| `SafetyGuard` (Phase 17) | Environment-Checks |
| `LiveRiskLimits` (Phase 46) | Order-Validierung |
| `Strategy-Registry` | Lädt Strategien per Key |
| `KrakenLiveCandleSource` | Data-Feed für Live-Daten |
| `ShadowOrderExecutor` | Paper-Execution |
| `TestnetOrchestrator` (Phase 64) | Ergänzt (nicht ersetzt) |

---

## 7. Tests

### 7.1 Test-Suite

24 Tests in `tests/test_live_session_runner.py`:

```bash
python3 -m pytest tests/test_live_session_runner.py -v
```

| Test-Kategorie | Anzahl | Status |
|----------------|--------|--------|
| Config-Validierung | 10 | ✅ |
| Runner-Lifecycle | 7 | ✅ |
| Factory-Method | 2 | ✅ |
| CLI-Smoke-Tests | 4 | ✅ |
| Pipeline-Integration | 1 | ✅ |

### 7.2 Wichtige Test-Cases

- **LIVE-Mode Blockierung**: Wird an mehreren Stellen getestet
- **Signal-to-Order Flow**: Deterministische Fake-Strategy
- **CLI-Parsing**: --help, --list-strategies, --dry-run
- **Graceful Shutdown**: shutdown() bricht Loop ab

---

## 8. Wie du Phase 80 in der Praxis nutzt

Dieser Abschnitt beschreibt, wie du Phase 80 im Alltag einsetzt – als Operator, Researcher oder Future-Ich.

### 8.1 Typische Einsatzszenarien

- **Shadow-Run für neue Strategie-Konfigurationen**: Bevor du eine neue Strategie-Config in größere Backtests oder Sweeps steckst, fährst du einen kurzen Shadow-Run, um zu sehen, ob Signale generiert werden und der Order-Flow funktioniert.

- **Testnet-Session für Order-Flow-Validierung**: Du willst beobachten, wie Safety-Gates und RiskLimits unter realistischeren Bedingungen reagieren – ohne echte Trades. Testnet-Mode validiert Orders gegen die Exchange-API (validate_only).

- **Kurze Smoke-Tests vor größeren Runs**: Ein schneller `--steps 10 --dry-run` Check, ob Config, Strategy-Registry und Pipeline korrekt zusammenspielen.

- **Integration in Research-Workflow**: Nach einem erfolgreichen Backtest/Sweep testest du die Top-Kandidaten im Shadow-Mode, bevor du sie in das Tiering aufnimmst.

- **Operator-Debugging**: Wenn ein Testnet-/Shadow-Run unerwartet abbricht, liefern die Session-Metriken (`get_summary()`) schnell einen Überblick über generierte vs. geblockte Orders.

### 8.2 Typischer Workflow: Research → Backtest → Shadow → Testnet

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. Research-Phase                                                   │
│     └─▶ Strategie entwickeln, Parameter definieren                  │
│                                                                      │
│  2. Backtest-Phase                                                   │
│     └─▶ `research_cli.py backtest --strategy ...`                   │
│     └─▶ Sweeps, Monte-Carlo, Stress-Tests                           │
│                                                                      │
│  3. Shadow-Phase (Phase 80)                                          │
│     └─▶ `run_execution_session.py --strategy ... --steps 50`        │
│     └─▶ Beobachte: Signale, Orders, Safety-Blocks                   │
│                                                                      │
│  4. Testnet-Phase (Phase 80)                                         │
│     └─▶ `run_execution_session.py --mode testnet --strategy ...`    │
│     └─▶ Validierung gegen echte Exchange-API (validate_only)        │
│                                                                      │
│  5. Tiering & Live-Readiness                                         │
│     └─▶ Strategie in `strategy_tiering.toml` als `core`/`aux`       │
│     └─▶ Live-Gates (Phase 83) prüfen                                │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.3 Praktische CLI-Rezepte

**Schneller Smoke-Test einer Strategie:**
```bash
python3 scripts/run_execution_session.py \
    --strategy rsi_reversion \
    --steps 5 \
    --dry-run
```

**30-Minuten Shadow-Session mit Logging:**
```bash
python3 scripts/run_execution_session.py \
    --strategy ma_crossover \
    --symbol BTC/EUR \
    --duration 30 2>&1 | tee shadow_run_$(date +%Y%m%d_%H%M).log
```

**Testnet-Validierung für ETH-Strategie:**
```bash
python3 scripts/run_execution_session.py \
    --mode testnet \
    --strategy trend_following \
    --symbol ETH/EUR \
    --steps 20
```

**Alle verfügbaren Strategien auflisten:**
```bash
python3 scripts/run_execution_session.py --list-strategies
```

### 8.4 Interpretation der Session-Metriken

Nach einem Run liefert `get_summary()` (oder die CLI-Ausgabe) folgende Kennzahlen:

| Metrik | Was sie bedeutet | Worauf achten |
|--------|------------------|---------------|
| `steps` | Anzahl verarbeiteter Bars | Entspricht der erwarteten Laufzeit? |
| `total_orders_generated` | Signale, die zu Orders führten | Strategie generiert Signale? |
| `orders_executed` | Erfolgreich ausgeführte Orders | Im Shadow-Mode = Paper-Fills |
| `orders_rejected` | Von Pipeline abgelehnt | Ggf. Config-Problem oder Limit erreicht |
| `orders_blocked_risk` | Von RiskLimits geblockt | Safety funktioniert – aber zu restriktiv? |
| `current_position` | Aktuelle Position am Ende | Stimmt mit erwarteter Logik überein? |

**Faustregel:** Wenn `orders_blocked_risk` > 50% der generierten Orders, prüfe deine RiskLimit-Config oder reduziere `position_fraction`.

### 8.5 Häufige Fehler und Lösungen

| Problem | Ursache | Lösung |
|---------|---------|--------|
| `LiveModeNotAllowedError` | Versuch, `--mode live` zu nutzen | Phase 80 blockt LIVE hart – das ist Absicht |
| Keine Signale generiert | Strategie braucht mehr Warmup | Erhöhe `--warmup-candles` (z.B. auf 300) |
| Alle Orders geblockt | RiskLimits zu eng | Prüfe `config.toml` → `[live_risk]` Sektion |
| Strategy nicht gefunden | Tippfehler oder nicht registriert | `--list-strategies` zeigt verfügbare Keys |
| Timeout bei Testnet-Mode | Exchange-API nicht erreichbar | Prüfe Netzwerk, API-Keys in `.env` |

### 8.6 Einbettung in bestehende Toolchain

Phase 80 ergänzt (nicht ersetzt) bestehende Tools:

| Tool/Phase | Rolle | Zusammenspiel mit Phase 80 |
|------------|-------|----------------------------|
| `research_cli.py` | Backtests, Sweeps, Reports | Phase 80 kommt **nach** erfolgreichen Backtests |
| `TestnetOrchestrator` (Phase 64) | Multi-Symbol Testnet-Management | Phase 80 für Single-Strategy-Sessions |
| `preview_live_portfolio.py` | Portfolio-Snapshot | Nutze nach Phase-80-Runs für Gesamtbild |
| `live_ops.py` (Phase 51) | Operator-Commands | Ergänzend für Health-Checks, Alerts |
| Live-Gates (Phase 83) | Eligibility-Check | Vor Testnet-Session prüfen: `check_strategy_live_eligibility()` |

---

## 9. Nächste Schritte (Future Phases)

| Phase | Feature | Status |
|-------|---------|--------|
| 81+ | Echte Testnet-Orders (nicht nur validate_only) | 🔜 Geplant |
| 82+ | Live-Mode mit vollständigem Gating | 🔜 Geplant |
| 83+ | Scheduling & Restarts | 🔜 Geplant |
| 84+ | Monitoring Dashboard | 🔜 Geplant |

---

## 10. Glossar

| Begriff | Bedeutung |
|---------|-----------|
| **Shadow-Mode** | Simulation ohne echte API-Calls |
| **Testnet-Mode** | Testnet-API mit validate_only=True |
| **Live-Mode** | Echte Orders (Phase 80: BLOCKIERT) |
| **Signal-Event** | Strategie-Output (-1/0/+1) |
| **Position-Fraction** | Anteil des Kapitals pro Trade |
| **Warmup** | Laden historischer Daten für Indikatoren |

---

## 11. Referenzen

- `src/execution/live_session.py` - Haupt-Implementation
- `src/execution/pipeline.py` - ExecutionPipeline
- `src/live/safety.py` - SafetyGuard
- `src/strategies/registry.py` - Strategy-Registry
- `docs/PHASE_16A_EXECUTION_PIPELINE.md` - Pipeline-Dokumentation
- `docs/LIVE_DEPLOYMENT_PLAYBOOK.md` - Live-Deployment-Leitfaden
