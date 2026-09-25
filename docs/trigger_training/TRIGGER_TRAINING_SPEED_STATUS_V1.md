# Trigger Training Speed & Execution Latency Metriken – Status v1

**Status:** ✅ Production Ready  
**Version:** v1.0  
**Datum:** 2025-12-10

---

## 🎯 Überblick

Diese Integration erweitert das bestehende Offline Trigger Training System um **Geschwindigkeits- und Latenz-Metriken**. Ziel ist es, sowohl die **menschliche Reaktionsgeschwindigkeit** (Operator) als auch die **technische Execution-Latenz** (System) systematisch zu messen und zu verbessern.

### Key Features

- ✅ **Trigger-Reaktions-Metriken** – Kategorisierung: IMPULSIVE / ON_TIME / LATE / MISSED / SKIPPED
- ✅ **Execution-Latenz-Tracking** – Signal → Order → Fill (mit Quantilen P50/P90/P95/P99)
- ✅ **Slippage-Analyse** – Vergleich Expected vs. Actual Fill Price
- ✅ **HTML-Report-Integration** – Neue Sektionen im Trigger Training Report
- ✅ **CSV-Export** – Detaillierte Metriken als CSV für weitere Analyse
- ✅ **100% Test-Coverage** – 25 neue Tests (12 Reaction Stats + 13 Execution Latency)

---

## 📊 Metriken-Übersicht

### 1. Trigger-Reaktionsgeschwindigkeit (Human / Operator)

#### Kategorien

| Kategorie | Beschreibung | Schwellenwert | Interpretation |
|-----------|--------------|---------------|----------------|
| **IMPULSIVE** | Sehr schnelle Reaktion | < 300 ms (konfigurierbar) | Kann auf Überreaktion hinweisen |
| **ON_TIME** | Normale Reaktionszeit | 300 ms – 3 s | ✅ Ideal |
| **LATE** | Zu späte Reaktion | > 3 s (konfigurierbar) | ⚠️ Verbesserungspotential |
| **MISSED** | Kein Action-Event | – | ❌ Kritisch |
| **SKIPPED** | Bewusst übersprungen | – | Neutral (diszipliniert) |

#### Statistiken

- **Mean / Median / Std Reaktionszeit** (ms)
- **Quantile**: P50 / P90 / P95 / P99
- **Verteilung** nach Kategorie

---

### 2. Execution-Latenz (Technik / System)

#### Delay-Komponenten

| Metrik | Beschreibung | Formel |
|--------|--------------|--------|
| **Trigger-Delay** | Signal → Order-Sent | `t_order_sent - t_signal` |
| **Send-to-Ack** | Order-Sent → Exchange-Ack | `t_exchange_ack - t_order_sent` |
| **Send-to-Fill** | Order-Sent → First/Last Fill | `t_first_fill - t_order_sent` |
| **Total-Delay** | Signal → Last Fill | `t_last_fill - t_signal` |

#### Slippage

- **Formel**: `(avg_fill_price - reference_price) * direction`
- **Positiv** = ungünstiger Fill
- **Negativ** = besserer Fill

---

## 📁 Neue Module

### 1.

**Zweck:** Berechnung und Analyse von Trigger-Reaktionszeiten

**Hauptkomponenten:**

```python
# Enums & Dataclasses
TriggerReactionCategory      # Enum: IMPULSIVE, ON_TIME, LATE, MISSED, SKIPPED
TriggerReactionConfig         # Schwellenwerte (impulsive_threshold_ms, late_threshold_ms)
TriggerReactionRecord         # Einzelner Datensatz pro Signal
TriggerReactionSummary        # Aggregierte Statistiken

# Core-Funktionen
compute_reaction_records(signals_df, actions_df, config, session_id)
summarize_reaction_records(records)
reaction_records_to_df(records)
reaction_summary_to_dict(summary)
```

**Verwendung:**

```python
from src.trigger_training.reaction_stats import (
    TriggerReactionConfig,
    compute_reaction_records,
    summarize_reaction_records,
)

config = TriggerReactionConfig(
    impulsive_threshold_ms=300,
    late_threshold_ms=3000,
)

records = compute_reaction_records(
    signals_df=signals_df,
    actions_df=actions_df,
    config=config,
    session_id="DRILL_20251210",
)

summary = summarize_reaction_records(records)
print(f"On-Time: {summary.count_on_time}")
print(f"Mean Reaction: {summary.mean_reaction_ms:.1f} ms")
```

---

### 2. `src/execution/metrics/execution_latency.py`

**Zweck:** Messung technischer Execution-Latenzen

**Hauptkomponenten:**

```python
# Dataclasses
ExecutionLatencyTimestamps    # Rohe Timestamps (signal_ts, order_sent_ts, fill_ts, etc.)
ExecutionLatencyMeasures      # Berechnete Delays (trigger_delay_ms, send_to_fill_ms, etc.)
ExecutionLatencySummary       # Aggregierte Statistiken mit Quantilen

# Core-Funktionen
compute_latency_measures(timestamps)
summarize_latency(measures)
latency_measures_to_df(measures)
latency_summary_to_dict(summary)

# Convenience für Offline/Paper
create_latency_timestamps_from_trades_and_signals(trades_df, signals_df, session_id)
```

**Verwendung:**

```python
from src.execution.metrics.execution_latency import (
    create_latency_timestamps_from_trades_and_signals,
    compute_latency_measures,
    summarize_latency,
)

# Timestamps aus Trades & Signals erstellen
timestamps = create_latency_timestamps_from_trades_and_signals(
    trades_df=trades_df,
    signals_df=signals_df,
    session_id="DRILL_20251210",
)

# Metriken berechnen
measures = [compute_latency_measures(ts) for ts in timestamps]

# Zusammenfassen
summary = summarize_latency(measures)
print(f"Avg Trigger-Delay: {summary.mean_trigger_delay_ms:.1f} ms")
print(f"P90 Send-to-Fill: {summary.p90_send_to_first_fill_ms:.1f} ms")
```

---

## 🚀 Integration in Offline Trigger Training Drill

### Erweiterung in `scripts/run_offline_trigger_training_drill_example.py`

**Neue Schritte:**

1. **Reaktions-Stats berechnen** (nach Event-Generierung):

```python
from src.trigger_training.reaction_stats import (
    TriggerReactionConfig,
    compute_reaction_records,
    summarize_reaction_records,
    reaction_records_to_df,
    reaction_summary_to_dict,
)

reaction_cfg = TriggerReactionConfig(
    impulsive_threshold_ms=300,
    late_threshold_ms=3000,
    consider_skipped=True,
)

reaction_records = compute_reaction_records(
    signals_df=signals_df,
    actions_df=actions_df,
    config=reaction_cfg,
    session_id=session_id,
)

reaction_summary = summarize_reaction_records(reaction_records)
reaction_records_df = reaction_records_to_df(reaction_records)
```

2. **Latenz-Stats berechnen**:

```python
from src.execution.metrics.execution_latency import (
    create_latency_timestamps_from_trades_and_signals,
    compute_latency_measures,
    summarize_latency,
    latency_measures_to_df,
    latency_summary_to_dict,
)

latency_timestamps = create_latency_timestamps_from_trades_and_signals(
    trades_df=trades_df,
    signals_df=signals_df,
    session_id=session_id,
)

latency_measures = [compute_latency_measures(ts) for ts in latency_timestamps]
latency_summary = summarize_latency(latency_measures)
latency_measures_df = latency_measures_to_df(latency_measures)
```

3. **CSV-Export** (optional):

```python
# DataFrames speichern
session_report_dir = base_reports_dir / session_id
reaction_records_df.to_csv(session_report_dir / "reaction_records.csv", index=False)
latency_measures_df.to_csv(session_report_dir / "latency_measures.csv", index=False)
```

4. **An Report übergeben**:

```python
result_paths = generate_reports_for_offline_paper_trade(
    trades=trades_df,
    report_config=report_cfg,
    trigger_events=trigger_events,
    session_meta_for_trigger={
        "session_id": session_id,
        # ... weitere Meta-Daten
        "reaction_summary": reaction_summary_to_dict(reaction_summary),
        "latency_summary": latency_summary_to_dict(latency_summary),
    },
)
```

---

## 📄 HTML-Report-Erweiterung

### Neue Sektionen in `src/reporting/trigger_training_report.py`

#### 1. Trigger-Geschwindigkeit & Reaktionsmuster

**Inhalt:**

- **Summary-Badges**: Total Signale, Impulsive, On-Time, Late, Missed, Skipped
- **Reaktionszeit-Statistiken**: Mean, Median, P90, P95, P99 (ms / s)
- **Interpretation-Hinweis**: Was bedeuten die Kategorien?

**Funktion:** `_build_trigger_speed_section_html(reaction_summary)`

**Beispiel-Output:**

```
⚡ Trigger-Geschwindigkeit & Reaktionsmuster
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[5 Signale] [1 Impulsive] [2 On-Time ✓] [1 Late] [1 Missed] [0 Skipped]

Reaktionszeit-Statistiken:
  - Durchschnitt: 1250.0 ms (1.250 s)
  - Median (P50):  800.0 ms (0.800 s)
  - P90:          2500.0 ms (2.500 s)
```

---

#### 2. Execution-Latenz & Slippage

**Inhalt:**

- **Total Orders**: Anzahl
- **Trigger-Delay**: Mean, Median, P90, P95, P99
- **Send-to-First-Fill**: Mean, Median, P90, P95, P99
- **Total-Delay**: Mean, Median, P90, P95, P99
- **Slippage**: Mean, Median

**Funktion:** `_build_execution_latency_section_html(latency_summary)`

**Beispiel-Output:**

```
🚀 Execution-Latenz & Slippage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Orders: 4

Trigger-Delay (Signal → Order-Sent):
  - Durchschnitt: 500.0 ms (0.500 s)
  - P90:          700.0 ms (0.700 s)

Send-to-First-Fill (Order-Sent → First Fill):
  - Durchschnitt: 250.0 ms (0.250 s)
  - P90:          350.0 ms (0.350 s)

Slippage:
  - Durchschnitt: 2.5 (ungünstiger Fill)
```

---

## 🧪 Tests

### Test-Abdeckung

**Neue Tests:** 25 Tests (100% bestanden)

#### `tests/trigger_training/test_reaction_stats.py` (12 Tests)

- `test_compute_reaction_records_impulsive` – Impulsive Reaktion (< 300 ms)
- `test_compute_reaction_records_on_time` – On-Time Reaktion (300 ms – 3 s)
- `test_compute_reaction_records_late` – Late Reaktion (> 3 s)
- `test_compute_reaction_records_missed` – Missed Signal (keine Aktion)
- `test_compute_reaction_records_skipped` – Skipped Signal
- `test_compute_reaction_records_multiple_signals` – Mehrere Signale
- `test_summarize_reaction_records` – Aggregation
- `test_summarize_reaction_records_empty` – Leere Liste
- `test_reaction_records_to_df` – DataFrame-Konvertierung
- `test_reaction_records_to_df_empty` – Leere DataFrame
- `test_reaction_summary_to_dict` – Dict-Konvertierung
- `test_compute_reaction_records_with_session_id` – Session-ID

#### `tests/execution/metrics/test_execution_latency.py` (13 Tests)

- `test_compute_latency_measures_full` – Vollständige Timestamps
- `test_compute_latency_measures_minimal` – Minimale Timestamps
- `test_compute_latency_measures_slippage_sell` – SELL-Slippage
- `test_summarize_latency_multiple_orders` – Aggregation
- `test_summarize_latency_empty` – Leere Liste
- `test_summarize_latency_partial_data` – Partielle Daten
- `test_latency_measures_to_df` – DataFrame-Konvertierung
- `test_latency_measures_to_df_empty` – Leere DataFrame
- `test_latency_summary_to_dict` – Dict-Konvertierung
- `test_create_latency_timestamps_from_trades` – Timestamps aus Trades
- `test_create_latency_timestamps_with_signals` – Mit Signal-Verknüpfung
- `test_create_latency_timestamps_empty` – Leerer Input
- `test_percentile_calculations` – Quantile (P90/P95/P99)

### Tests ausführen

```bash
# Alle neuen Tests
python3 -m pytest tests/trigger_training/test_reaction_stats.py -v
python3 -m pytest tests/execution/metrics/test_execution_latency.py -v

# Bestehende Tests (Kompatibilität prüfen)
python3 -m pytest tests/trigger_training/ -v
python3 -m pytest tests/reporting/test_trigger_training_report.py -v
```

**Erwartetes Ergebnis:** ✅ 30 passed (alle Tests bestanden)

---

## 🎯 Verwendungsbeispiel: End-to-End

### 1. Drill ausführen (mit Speed-Metriken)

```bash
cd /Users/frnkhrz/Peak_Trade

PYTHONPATH=. python3 scripts/run_offline_trigger_training_drill_example.py \
    --session-id DRILL_SPEED_TEST_20251210 \
    --symbol BTCEUR \
    --timeframe 1m \
    --reports-dir reports/offline_paper_trade
```

### 2. Outputs

**Terminal-Output (NEU):**

```
═══════════════════════════════════════════════════════════════════
📊 TRIGGER-GESCHWINDIGKEITS-METRIKEN
═══════════════════════════════════════════════════════════════════
Total Signale:        5
  - Impulsive:        1
  - On-Time:          2
  - Late:             1
  - Missed:           1
  - Skipped:          0
Avg Reaktionszeit:    1250.5 ms
Median Reaktionszeit: 800.0 ms
P90 Reaktionszeit:    2500.0 ms

═══════════════════════════════════════════════════════════════════
⚡ EXECUTION-LATENZ-METRIKEN
═══════════════════════════════════════════════════════════════════
Total Orders:         4
Avg Trigger-Delay:    500.0 ms
Median Trigger-Delay: 450.0 ms
Avg Send-to-Fill:     250.0 ms
P90 Send-to-Fill:     350.0 ms
Avg Slippage:         2.5000
═══════════════════════════════════════════════════════════════════
```

**Dateien:**

```
reports/offline_paper_trade/DRILL_SPEED_TEST_20251210/
├── offline_paper_trade_report.html     # Paper-Trade-Report
├── trigger_training_report.html        # Trigger-Report (mit neuen Sektionen!)
├── reaction_records.csv                # Detaillierte Reaktions-Daten
├── latency_measures.csv                # Detaillierte Latenz-Daten
└── reaction_delay_hist.png             # Reaktionszeit-Histogramm
```

### 3. HTML-Report öffnen

```bash
open reports/offline_paper_trade/DRILL_SPEED_TEST_20251210/trigger_training_report.html
```

**Im Report sichtbar:**

- Bestehende Sektionen (Outcome-Übersicht, Pain Points, Psychologie-Heatmap)
- **NEU:** Trigger-Geschwindigkeit & Reaktionsmuster
- **NEU:** Execution-Latenz & Slippage

---

## 📈 Interpretation & Best Practices

### Zielwerte (Richtwerte)

| Metrik | Zielwert | Bemerkung |
|--------|----------|-----------|
| **On-Time Rate** | ≥ 70% | Anteil rechtzeitiger Reaktionen |
| **Missed Rate** | ≤ 10% | Verpasste Signale minimieren |
| **Mean Reaction Time** | 0.5 – 2.0 s | Je nach Setup-Komplexität |
| **P90 Reaction Time** | < 3.0 s | 90% der Reaktionen unter 3s |
| **Mean Trigger-Delay** | < 1.0 s | Offline: meist sehr niedrig |
| **Mean Slippage** | < 0.01% | Abhängig von Markt & Order-Größe |

### Typische Muster

#### 🟢 Gutes Muster

- **On-Time:** 75%
- **Impulsive:** < 10%
- **Late:** < 15%
- **Missed:** < 10%
- **Mean Reaction:** 1.2 s
- **P90 Reaction:** 2.5 s

**Interpretation:** Disziplinierte, aber nicht überhastete Ausführung.

#### 🟡 Verbesserungspotential

- **On-Time:** 50%
- **Impulsive:** 5%
- **Late:** 30%
- **Missed:** 15%
- **Mean Reaction:** 3.5 s
- **P90 Reaction:** 8.0 s

**Interpretation:** Zu zögerlich, viele Late/Missed. Fokus auf schnellere Signal-Erkennung.

#### 🔴 Kritisches Muster

- **On-Time:** 30%
- **Impulsive:** 40%
- **Late:** 10%
- **Missed:** 20%
- **Mean Reaction:** 0.8 s
- **P90 Reaction:** 2.0 s

**Interpretation:** Zu viele impulsive Reaktionen. Risiko von Überreaktionen / FOMO.

---

## 🔄 Workflow-Integration

### Standard-Workflow

1. **Drill durchführen** → `run_offline_trigger_training_drill_example.py`
2. **Speed-Metriken prüfen** → Terminal-Output + HTML-Report
3. **CSV-Daten analysieren** → `reaction_records.csv`, `latency_measures.csv`
4. **Schwachstellen identifizieren** → Late / Missed / Impulsive
5. **Gezielte Wiederholung** → Drills für Problemzonen

### Multi-Session-Tracking (Zukünftig)

- **Trend-Analyse:** Hit-Rate über Zeit
- **Session-Vergleich:** Welche Sessions hatten beste/schlechteste Speed?
- **Operator-Meta-Report:** Aggregierte Stats über alle Drills

---

## 🚫 Nicht-Ziele (Safety)

### Was diese Integration NICHT tut:

- ❌ **Keine Live-Order-Execution** – Rein offline / paper / drill
- ❌ **Keine echten API-Keys** – Keine Live-Broker-Anbindung
- ❌ **Keine Business-Logik-Änderung** – Strategien bleiben unverändert
- ❌ **Keine automatischen Trades** – Alles ist manuell / simuliert

---

## 📚 Weitere Dokumentation

- **Trigger Training README:** `docs/trigger_training/README.md`
- **Offline Drill Runbook:** `docs/runbooks/OFFLINE_TRIGGER_TRAINING_DRILL_V1.md`
- **Psychology Heatmap:** `docs/psychology_heatmap_integration.md`
- **Armstrong El-Karoui Playbook:**

---

## 🐛 Troubleshooting

### Problem: CSV-Dateien leer

**Ursache:** Keine Signals/Actions/Trades im Input.

**Lösung:** Prüfe, ob DataFrames vor Berechnung gefüllt sind:

```python
print(f"Signals: {len(signals_df)}, Actions: {len(actions_df)}, Trades: {len(trades_df)}")
```

---

### Problem: Alle Reaktionen = MISSED

**Ursache:** `actions_df` ist leer oder `signal_id` fehlt.

**Lösung:** Stelle sicher, dass:

1. `actions_df` die Spalte `signal_id` enthält
2. Signal-IDs in beiden DataFrames übereinstimmen

---

### Problem: Tests schlagen fehl

**Ursache:** Import-Fehler / Dependencies fehlen.

**Lösung:**

```bash
# PYTHONPATH setzen
export PYTHONPATH=/Users/frnkhrz/Peak_Trade:$PYTHONPATH

# Dependencies prüfen
python3 -c "import pandas, numpy, pytest; print('OK')"

# Tests erneut ausführen
python3 -m pytest tests/trigger_training/test_reaction_stats.py -v
```

---

## 🏆 Erfolge

```
[2025-12-10] ✅ TriggerReactionStats Modul implementiert
[2025-12-10] ✅ ExecutionLatencyTracker Modul implementiert
[2025-12-10] ✅ Integration in run_offline_trigger_training_drill_example.py
[2025-12-10] ✅ HTML-Report erweitert (2 neue Sektionen)
[2025-12-10] ✅ 25 neue Tests geschrieben (12 + 13)
[2025-12-10] ✅ 30/30 Tests bestanden (inkl. bestehende Tests)
[2025-12-10] ✅ CSV-Export für weitere Analyse
[2025-12-10] ✅ Vollständige Dokumentation
```

---

**Happy Drilling – with Speed! 🚀**

*Peak_Trade Team – Dez 2025*
