# Peak_Trade Autonomous AI-Driven Workflow

> **Autonomer KI-gesteuerter Workflow** – Automatisierte, intelligente Entscheidungsfindung und Workflow-Ausführung für Trading-Research und -Monitoring.

---

## Überblick

Der **Autonomous AI-Driven Workflow** ist ein intelligentes System, das automatisch Marktbedingungen analysiert, Entscheidungen trifft und entsprechende Workflows ausführt – mit minimaler menschlicher Intervention.

### Hauptfeatures

- 🤖 **AI-Enhanced Decision Making**: Intelligente Entscheidungslogik basierend auf Markt-, Signal- und Performance-Metriken
- 📊 **Continuous Monitoring**: Überwacht Marktbedingungen, Signalqualität und Portfolio-Performance
- 🔄 **Autonomous Execution**: Führt Research-Workflows automatisch aus, wenn Bedingungen erfüllt sind
- 🛡️ **Safety-First**: Integriert mit bestehenden Risk-Limits und Safety-Gates
- 📈 **Adaptive Behavior**: Passt sich an Marktbedingungen an und wählt optimale Workflows

---

## Architektur

### Komponenten

```
┌─────────────────────────────────────────────────────┐
│         Autonomous Workflow Orchestrator            │
│  (scripts/run_autonomous_workflow.py)               │
└─────────────────┬───────────────────────────────────┘
                  │
      ┌───────────┴───────────┐
      │                       │
      ▼                       ▼
┌──────────────┐    ┌──────────────────┐
│   Monitors   │    │ Decision Engine  │
│              │    │                  │
│ • Market     │◄───┤ • Criteria       │
│ • Signals    │    │ • Rules          │
│ • Performance│    │ • AI Logic       │
└──────┬───────┘    └────────┬─────────┘
       │                     │
       │      ┌──────────────┘
       │      │
       ▼      ▼
┌──────────────────────────┐
│   Workflow Engine        │
│                          │
│ • Execution              │
│ • State Management       │
│ • Integration            │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Existing Pipeline       │
│                          │
│ • Research Scripts       │
│ • Scheduler              │
│ • Registry               │
└──────────────────────────┘
```

### Module

1. **Workflow Engine** ()
   - Koordiniert Workflow-Ausführung
   - Verwaltet Workflow-Status
   - Integriert mit bestehenden Scripts

2. **Decision Engine** ()
   - Trifft intelligente Entscheidungen
   - Bewertet Kriterien und Metriken
   - Berechnet Confidence-Scores

3. **Monitors** ()
   - `MarketMonitor`: Marktbedingungen
   - `SignalMonitor`: Signalqualität
   - `PerformanceMonitor`: Portfolio-Performance

---

## Quick Start

### 1. Einmalige Ausführung

```bash
# Auto-Entscheidung basierend auf aktuellen Bedingungen
python3 scripts/run_autonomous_workflow.py --once

# Spezifischer Workflow-Typ
python3 scripts/run_autonomous_workflow.py \
  --workflow-type signal_analysis \
  --symbol BTC/EUR \
  --once
```

### 2. Continuous Monitoring

```bash
# Läuft dauerhaft und prüft alle 5 Minuten
python3 scripts/run_autonomous_workflow.py \
  --continuous \
  --poll-interval 300
```

### 3. Dry-Run (Simulation)

```bash
# Simuliert Ausführung ohne echte Actions
python3 scripts/run_autonomous_workflow.py \
  --once \
  --dry-run \
  --verbose
```

### 4. Integration mit Scheduler

```bash
# Scheduler mit autonomen Workflows starten
python3 scripts/run_scheduler.py \
  --config config/scheduler/jobs.toml \
  --include-tags autonomous
```

---

## Workflow-Typen

### 1. Signal Analysis
Analysiert aktuelle Trading-Signale und deren Qualität.

**Trigger-Bedingungen:**
- Signal-Stärke > 0.5
- Volatilität akzeptabel (< 0.3)

**Ausführt:**
- `scripts&#47;run_forward_signals.py`
- Generiert Forward-Signale für konfigurierte Symbole

### 2. Risk Check
Prüft aktuelle Risk-Limits und Portfolio-Status.

**Trigger-Bedingungen:**
- Drawdown < 20%
- Position Size < 15%

**Ausführt:**
- `scripts&#47;check_live_risk_limits.py`
- Validiert Risk-Compliance

### 3. Market Scan
Scannt Markt nach Trading-Gelegenheiten.

**Trigger-Bedingungen:**
- Markt-Stunden aktiv
- Mindest-Aktivität vorhanden

**Ausführt:**
- `scripts&#47;run_market_scan.py`
- Analysiert mehrere Symbole

### 4. Portfolio Analysis
Führt umfassende Portfolio-Analyse durch.

**Trigger-Bedingungen:**
- Tagesabschluss
- Ausreichend Trades vorhanden

**Ausführt:**
- `scripts&#47;research_cli.py portfolio`
- Generiert Portfolio-Reports

### 5. Auto (Default)
Wählt automatisch den optimalen Workflow basierend auf aktuellen Bedingungen.

**Entscheidungslogik:**
1. Performance kritisch → Risk Check
2. Starke Signale → Signal Analysis
3. Default → Market Scan

---

## Decision Engine

### Kriterien-System

Jeder Workflow-Typ hat definierte **Decision Criteria**:

```python
DecisionCriteria(
    name="signal_strength",
    threshold=0.5,
    weight=0.8,
    metric_name="signal_strength",
    comparison="gt"  # greater than
)
```

### Confidence-Berechnung

```
confidence = Σ(weight * is_met) / Σ(weight)

- confidence >= 0.8 → EXECUTE (hoch)
- confidence >= 0.6 → EXECUTE (moderat)
- confidence >= 0.4 → ALERT (niedrig)
- confidence <  0.4 → SKIP (sehr niedrig)
```

### Beispiel-Decision

```
Workflow: signal_analysis
Metrics:
  - signal_strength: 0.65 ✓ (> 0.5)
  - volatility: 0.18 ✓ (< 0.3)

Confidence: 0.85 (85%)
Action: EXECUTE
Reasoning: High confidence - All key criteria met
```

---

## Monitoring

### Market Monitor
- Volatilität
- Volumen
- Preisbewegungen
- Spread

### Signal Monitor
- Signal-Stärke
- Signal-Konsistenz
- False-Signal-Rate
- Signal-Frequenz

### Performance Monitor
- Drawdown
- Win-Rate
- Daily PnL
- Sharpe Ratio

### Alert-Levels

| Level | Bedeutung | Trigger |
|-------|-----------|---------|
| `INFO` | Normal | Workflow erfolgreich |
| `WARNING` | Achtung | Niedrige Confidence, moderate Probleme |
| `CRITICAL` | Aktion erforderlich | Workflow fehlgeschlagen, Risk-Limits überschritten |

---

## Scheduler-Integration

### Vordefinierte Jobs

Die Datei `config&#47;scheduler&#47;jobs.toml` enthält mehrere autonome Workflows:

1. **autonomous_morning_analysis** (08:15)
   - Morgendliche Marktanalyse
   - Auto-Workflow-Typ

2. **autonomous_midday_check** (12:00)
   - Mittags-Check
   - Signal- und Risk-Validierung

3. **autonomous_evening_review** (20:00)
   - Tages-Review
   - Portfolio-Analyse

4. **autonomous_hourly_monitor** (jede Stunde, optional)
   - Kontinuierliches Monitoring
   - Standardmäßig deaktiviert

### Job aktivieren/deaktivieren

```toml
[[job]]
name = "autonomous_morning_analysis"
enabled = true  # false zum Deaktivieren
```

---

## CLI-Referenz

### run_autonomous_workflow.py

```bash
python3 scripts/run_autonomous_workflow.py [OPTIONS]

Options:
  --config PATH              Pfad zur Config (default: config/config.toml)
  --workflow-type TYPE       Workflow-Typ (signal_analysis, risk_check,
                            market_scan, portfolio_analysis, auto)
  --symbol SYMBOL           Trading-Symbol (default: BTC/EUR)
  --strategy STRATEGY       Strategie (default: ma_crossover)
  --once                    Einmalige Ausführung
  --continuous              Continuous Mode (Daemon)
  --poll-interval SECONDS   Polling-Intervall (default: 300)
  --dry-run                 Simulation ohne Ausführung
  --verbose, -v             Ausführliche Ausgabe
  --no-alerts               Alerts deaktivieren
  --alert-log PATH          Alert-Log-Pfad
```

### Beispiele

```bash
# Morning Analysis
python3 scripts/run_autonomous_workflow.py --once

# Continuous mit 10-Minuten-Intervall
python3 scripts/run_autonomous_workflow.py --continuous --poll-interval 600

# Risk Check mit Dry-Run
python3 scripts/run_autonomous_workflow.py \
  --workflow-type risk_check \
  --dry-run \
  --verbose

# Scheduler mit autonomen Workflows
python3 scripts/run_scheduler.py \
  --config config/scheduler/jobs.toml \
  --include-tags autonomous,daily
```

---

## Safety & Best Practices

### Safety-First Prinzipien

✅ **Dos:**
- Immer mit `--dry-run` testen
- Alerts beobachten
- Log-Files regelmäßig prüfen
- Scheduler-Jobs schrittweise aktivieren
- Confidence-Thresholds konservativ setzen

❌ **Don'ts:**
- Nie direkt in Live-Mode ohne Tests
- Decision-Thresholds nicht zu niedrig setzen
- Safety-Gates nicht umgehen
- Nicht ohne Monitoring betreiben

### Monitoring

```bash
# Alerts live verfolgen
tail -f logs/autonomous_alerts.log

# Scheduler-Status prüfen
python3 scripts/run_scheduler.py --config config/scheduler/jobs.toml --once --dry-run
```

---

## Konfiguration

### Decision Criteria anpassen

```python
from src.autonomous import DecisionEngine, DecisionCriteria

engine = DecisionEngine()

# Neues Kriterium hinzufügen
engine.add_criteria(
    workflow_type="signal_analysis",
    criteria=DecisionCriteria(
        name="custom_metric",
        threshold=0.7,
        weight=0.9,
        metric_name="my_metric",
        comparison="gte"
    )
)
```

### Monitor-Thresholds anpassen

```python
from src.autonomous import MarketMonitor

monitor = MarketMonitor()
monitor.thresholds["high_volatility"] = 0.40  # Von 0.35 erhöhen
```

---

## Erweiterte Nutzung

### Programmatische Nutzung

```python
from src.autonomous import (
    WorkflowEngine,
    DecisionEngine,
    MarketMonitor,
)

# Komponenten erstellen
workflow_engine = WorkflowEngine()
decision_engine = DecisionEngine()
market_monitor = MarketMonitor()

# Bedingungen prüfen
result = market_monitor.check_conditions("BTC/EUR")

# Metriken sammeln
metrics = {
    "signal_strength": 0.65,
    "volatility": 0.18,
}

# Entscheidung treffen
decision = decision_engine.make_decision(
    workflow_type="signal_analysis",
    metrics=metrics
)

if decision.should_execute:
    # Workflow erstellen und ausführen
    workflow_id = workflow_engine.create_workflow(
        name="my_workflow",
        workflow_type="signal_analysis",
        parameters={"symbol": "BTC/EUR"}
    )
    result = workflow_engine.execute_workflow(workflow_id)
```

---

## Troubleshooting

### "No workflow executed"
**Ursache:** Confidence-Score zu niedrig, Kriterien nicht erfüllt.
**Lösung:**
- `--verbose` nutzen um Decision-Details zu sehen
- Metriken mit `--dry-run` prüfen
- Kriterien-Thresholds anpassen

### "Workflow failed"
**Ursache:** Fehler in zugrunde liegendem Script.
**Lösung:**
- Script manuell testen
- Logs prüfen
- Parameter validieren

### "High false alert rate"
**Ursache:** Thresholds zu sensitiv.
**Lösung:**
- Monitor-Thresholds anpassen
- Confidence-Minimum erhöhen

---

## Roadmap & Erweiterungen

### Geplante Features

- [ ] **Machine Learning Integration**: Trainierte Modelle für Decision-Making
- [ ] **Multi-Asset Workflows**: Automatische Diversifikation
- [ ] **Adaptive Thresholds**: Selbst-anpassende Kriterien
- [ ] **Advanced Reporting**: Detaillierte Autonomous-Workflow-Reports
- [ ] **Backtesting**: Historische Simulation autonomer Entscheidungen

### Erweiterungsmöglichkeiten

1. **Custom Workflow Types**
   - Eigene Workflow-Typen definieren
   - Spezifische Decision-Criteria

2. **External Data Sources**
   - News-Feeds
   - Sentiment-Analysen
   - Macro-Indikatoren

3. **Advanced AI**
   - Reinforcement Learning
   - Ensemble-Methoden
   - Neural Networks

---

## Weitere Ressourcen

- **Scheduler-Doku:** `SCHEDULER.md` (planned)
- **Research-Pipeline:** `RESEARCH_PIPELINE.md` (planned)
- **Live-Workflows:** [`docs&#47;LIVE_WORKFLOWS.md`](LIVE_WORKFLOWS.md)
- **Safety & Governance:** [`docs&#47;GOVERNANCE_AND_SAFETY_OVERVIEW.md`](GOVERNANCE_AND_SAFETY_OVERVIEW.md)

---

**Built with ❤️ and AI-enhanced automation**
