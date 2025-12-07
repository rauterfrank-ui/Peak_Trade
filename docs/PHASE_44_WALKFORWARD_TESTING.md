# Phase 44 – Walk-Forward Testing

## Status

**Phase 44 ist vollständig implementiert und getestet.**

Phase 44 erweitert den Research-Playground um **Walk-Forward-Backtesting** für Out-of-Sample-Validierung von Strategiekonfigurationen. Walk-Forward-Testing ist ein wichtiger Schritt zur Robustness-Validierung, da es Strategien auf Daten testet, die nicht für die Parameter-Optimierung verwendet wurden.

**Track:** Research & Backtest (keine Live-Execution)

---

## 1. Ziel & Kontext

### Warum Walk-Forward-Testing?

Nach Phase 41 (Strategy-Sweeps), Phase 42 (Top-N Promotion) und Phase 43 (Visualisierung) fehlte eine **Out-of-Sample-Validierung** der identifizierten Top-Konfigurationen. Phase 44 schließt diese Lücke:

- **Out-of-Sample-Validierung**: Strategien werden auf Daten getestet, die nicht für die Parameter-Optimierung verwendet wurden
- **Robustness-Check**: Mehrere Train/Test-Fenster zeigen, ob Strategien über verschiedene Marktphasen stabil performen
- **Reduziert Overfitting**: Walk-Forward hilft, Strategien zu identifizieren, die nicht nur auf historischen Daten gut funktionieren

### Integration in Peak_Trade

Phase 44 baut auf drei vorherigen Phasen auf:

1. **Phase 41 – Strategy-Sweeps & Research-Playground**
   - Sweep-Definition und -Ausführung
   - Ergebnis-Speicherung unter `reports/experiments/`
   - Siehe `docs/PHASE_41_STRATEGY_SWEEPS_AND_RESEARCH_PLAYGROUND.md` für Details

2. **Phase 42 – Top-N Promotion**
   - Automatische Auswahl der besten Konfigurationen aus Sweep-Ergebnissen
   - Export in TOML-Format
   - Siehe `docs/PHASE_42_TOPN_PROMOTION.md` für Details

3. **Phase 43 – Visualisierung & Sweep-Dashboards**
   - Visuelle Auswertung von Sweep-Ergebnissen
   - Siehe `docs/PHASE_43_VISUALIZATION_AND_SWEEP_DASHBOARDS.md` für Details

Phase 44 nutzt die Top-N-Konfigurationen aus Phase 42 und validiert sie mit Walk-Forward-Backtesting über mehrere Train/Test-Fenster.

---

## 2. Konzeptueller Überblick

### Was ist Walk-Forward-Testing?

Walk-Forward-Testing ist eine Methode zur Out-of-Sample-Validierung von Trading-Strategien:

1. **Zeitraum aufteilen**: Der Gesamtzeitraum wird in mehrere Train/Test-Fenster aufgeteilt
2. **Train-Fenster**: Parameter werden auf Train-Daten optimiert (optional, aktuell nicht implementiert)
3. **Test-Fenster**: Strategie wird auf Test-Daten mit optimierten Parametern getestet
4. **Rolling Window**: Fenster werden schrittweise nach vorne verschoben (z.B. 6 Monate Train, 1 Monat Test)
5. **Aggregation**: Metriken über alle Test-Fenster werden aggregiert (Durchschnitts-Sharpe, Win-Rate, etc.)

### Vorteile

- **Reduziert Overfitting**: Strategien werden auf ungesehenen Daten getestet
- **Zeitliche Robustness**: Zeigt, ob Strategien über verschiedene Marktphasen stabil sind
- **Realistische Performance**: Näher an realer Performance als In-Sample-Backtests

### Beispiel

```
Zeitraum: 2020-01-01 bis 2020-12-31
Train Window: 180 Tage
Test Window: 30 Tage

Fenster 1:
  Train: 2020-01-01 bis 2020-06-29
  Test:  2020-06-30 bis 2020-07-29

Fenster 2:
  Train: 2020-07-01 bis 2020-12-28
  Test:  2020-12-29 bis 2021-01-28
```

---

## 3. Technischer Überblick

### Module

| Modul | Datei | Beschreibung |
|-------|-------|--------------|
| **Walk-Forward Engine** | `src/backtest/walkforward.py` | Kern-Logik für Walk-Forward-Backtesting |
| **Walk-Forward Reporting** | `src/reporting/walkforward_report.py` | Report-Generierung für Walk-Forward-Ergebnisse |
| **Top-N Integration** | `src/experiments/topn_promotion.py` | Lädt Top-N-Konfigurationen aus Sweeps |

### Haupt-Klassen & Funktionen

| Klasse/Funktion | Beschreibung |
|----------------|--------------|
| `WalkForwardConfig` | Konfiguration für Walk-Forward-Analyse (Train/Test-Fenster, etc.) |
| `WalkForwardWindowResult` | Ergebnis eines einzelnen Train/Test-Fensters |
| `WalkForwardResult` | Gesamtergebnis über alle Fenster |
| `split_train_test_windows()` | Teilt Zeitraum in Train/Test-Fenster auf |
| `run_walkforward_for_config()` | Führt Walk-Forward für eine Konfiguration aus |
| `run_walkforward_for_top_n_from_sweep()` | Führt Walk-Forward für Top-N-Konfigurationen aus Sweep aus |
| `build_walkforward_report()` | Erstellt Markdown-Report für WalkForwardResult |
| `build_multi_config_report()` | Erstellt Vergleichs-Report für mehrere Konfigurationen |

### Tests

**Datei:** `tests/test_walkforward_backtest.py`

**Tests in 3 Kategorien:**
- `TestSplitTrainTestWindows` (7 Tests): Fenster-Aufteilung
- `TestRunWalkforwardForConfig` (8 Tests): Walk-Forward-Engine
- `TestWalkforwardTopNIntegration` (1 Test, optional): Integration mit Sweeps

**Status:** ✅ Alle Tests grün

Ausführen:
```bash
pytest tests/test_walkforward_backtest.py -v
```

---

## 4. Workflow: Von Sweep zu Walk-Forward-Validierung

### Übersicht

Der vollständige Workflow besteht aus vier Schritten:

1. **Sweep ausführen** (Phase 41) → Ergebnisse unter `reports/experiments/`
2. **Top-N auswählen** (Phase 42) → Top-Kandidaten unter `reports/sweeps/`
3. **Walk-Forward ausführen** (Phase 44) → Walk-Forward-Ergebnisse unter `reports/walkforward/`
4. **Reports analysieren** (Phase 44) → Markdown-Reports mit aggregierten Metriken

### Schritt-für-Schritt Anleitung

#### Schritt 1: Virtual Environment aktivieren

```bash
cd ~/Peak_Trade
source .venv/bin/activate
```

#### Schritt 2: Sweep ausführen (falls noch nicht geschehen)

**Hinweis:** Für Details zur Sweep-Definition und -Ausführung siehe `docs/PHASE_41_STRATEGY_SWEEPS_AND_RESEARCH_PLAYGROUND.md`.

```bash
# Beispiel: rsi_reversion_basic mit max. 20 Runs
python scripts/run_strategy_sweep.py \
  --sweep-name rsi_reversion_basic \
  --config config/config.toml \
  --max-runs 20
```

**Output:** `reports/experiments/rsi_reversion_basic_*.csv`

#### Schritt 3: Top-N Kandidaten exportieren (optional, aber empfohlen)

**Hinweis:** Für Details zur Top-N Promotion siehe `docs/PHASE_42_TOPN_PROMOTION.md`.

```bash
python scripts/promote_sweep_topn.py \
  --sweep-name rsi_reversion_basic \
  --metric metric_sharpe_ratio \
  --top-n 5
```

**Output:** `reports/sweeps/rsi_reversion_basic_top_candidates.toml`

#### Schritt 4: Walk-Forward-Backtest ausführen

```bash
python scripts/run_walkforward_backtest.py \
  --sweep-name rsi_reversion_basic \
  --top-n 3 \
  --train-window 180d \
  --test-window 30d \
  --use-dummy-data \
  --dummy-bars 1000
```

**Mit echten Daten:**

```bash
python scripts/run_walkforward_backtest.py \
  --sweep-name rsi_reversion_basic \
  --top-n 3 \
  --train-window 180d \
  --test-window 30d \
  --data-file data/btc_eur_1h.csv \
  --start-date 2024-01-01 \
  --end-date 2024-12-31
```

**Output:**
- `reports/walkforward/{sweep_name}/{config_id}_walkforward_YYYYMMDD.md` (ein Report pro Konfiguration)
- `reports/walkforward/{sweep_name}/comparison_YYYYMMDD.md` (Vergleichs-Report)

---

## 5. CLI-Optionen

### Unified Research-CLI (Empfohlen)

Alternativ zur direkten Verwendung von `run_walkforward_backtest.py` kann Walk-Forward-Testing über die Unified Research-CLI gestartet werden:

```bash
python scripts/research_cli.py walkforward \
  --sweep-name rsi_reversion_basic \
  --top-n 3 \
  --train-window 90d \
  --test-window 30d \
  --use-dummy-data
```

Für komplette Pipelines (Sweep → Report → Promotion → Walk-Forward) kann das `pipeline`-Subcommand genutzt werden:

```bash
python scripts/research_cli.py pipeline \
  --sweep-name rsi_reversion_basic \
  --config config/config.toml \
  --format both \
  --with-plots \
  --top-n 5 \
  --run-walkforward \
  --train-window 90d \
  --test-window 30d \
  --use-dummy-data
```

### run_walkforward_backtest.py

**Datei:** `scripts/run_walkforward_backtest.py`

#### Erforderliche Argumente

| Argument | Beschreibung | Beispiel |
|----------|--------------|----------|
| `--sweep-name`, `-s` | Name des Sweeps | `rsi_reversion_basic` |
| `--train-window`, `-t` | Trainingsfenster-Dauer | `180d`, `6M` |
| `--test-window` | Testfenster-Dauer | `30d`, `1M` |

#### Optionale Argumente

| Argument | Beschreibung | Default |
|----------|--------------|---------|
| `--top-n`, `-n` | Anzahl der Top-Konfigurationen | `3` |
| `--step-size` | Schrittgröße zwischen Fenstern | `test-window` |
| `--data-file`, `-d` | Pfad zur OHLCV-Datei (CSV/Parquet) | - |
| `--use-dummy-data` | Verwende Dummy-Daten für Tests | `False` |
| `--dummy-bars` | Anzahl Bars für Dummy-Daten | `1000` |
| `--start-date` | Startdatum (YYYY-MM-DD) | Aus Daten abgeleitet |
| `--end-date` | Enddatum (YYYY-MM-DD) | Aus Daten abgeleitet |
| `--symbol` | Trading-Symbol | `BTC/EUR` |
| `--metric-primary` | Primäre Metrik für Top-N | `metric_sharpe_ratio` |
| `--metric-fallback` | Fallback-Metrik | `metric_total_return` |
| `--output-dir`, `-o` | Ausgabe-Verzeichnis | `reports/walkforward` |
| `--verbose`, `-v` | Verbose Output | `False` |

#### Beispiele

**Minimal (mit Dummy-Daten):**

```bash
python scripts/run_walkforward_backtest.py \
  --sweep-name rsi_reversion_basic \
  --train-window 180d \
  --test-window 30d \
  --use-dummy-data
```

**Vollständig (mit echten Daten):**

```bash
python scripts/run_walkforward_backtest.py \
  --sweep-name ma_crossover_basic \
  --top-n 5 \
  --train-window 90d \
  --test-window 15d \
  --data-file data/btc_eur_1h.csv \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --metric-primary metric_total_return \
  --metric-fallback metric_sharpe_ratio \
  --output-dir reports/walkforward
```

**Mit Custom Step-Size:**

```bash
python scripts/run_walkforward_backtest.py \
  --sweep-name breakout_basic \
  --train-window 180d \
  --test-window 30d \
  --step-size 60d \
  --use-dummy-data
```

---

## 6. Output-Struktur

### Verzeichnisstruktur

```
reports/walkforward/
└── {sweep_name}/
    ├── {config_id}_walkforward_YYYYMMDD.md    # Einzelner Report
    ├── {config_id}_walkforward_YYYYMMDD.md    # Weitere Konfigurationen
    └── comparison_YYYYMMDD.md                  # Vergleichs-Report
```

### Einzelner Walk-Forward-Report

Jeder Report enthält:

1. **Summary**
   - Config-ID, Strategiename, Anzahl Fenster
   - Walk-Forward-Konfiguration (Train/Test-Fenster)
   - Quick Stats (Avg Sharpe, Avg Return, Win Rate)

2. **Aggregate Metrics**
   - Tabelle mit aggregierten Metriken über alle Fenster:
     - Avg Sharpe, Avg Return, Avg Max Drawdown
     - Min/Max Sharpe, Min/Max Return
     - Positive Windows, Total Windows, Win Rate

3. **Window Details**
   - Tabelle mit allen Fenstern:
     - Fenster-Index, Train/Test-Zeitraum
     - Sharpe, Return, Max Drawdown, Trades pro Fenster

4. **Strategy Parameters**
   - Liste der verwendeten Strategie-Parameter

### Vergleichs-Report

Der Vergleichs-Report enthält eine Tabelle mit allen getesteten Konfigurationen:

| Config ID | Strategy | Avg Sharpe | Avg Return | Avg Max DD | Win Rate | Positive Windows | Total Windows |
|-----------|----------|------------|------------|------------|----------|------------------|---------------|
| config_1  | rsi_reversion | 1.25 | 12.5% | -8.2% | 75.0% | 3 | 4 |
| config_2  | rsi_reversion | 1.18 | 11.2% | -9.1% | 66.7% | 2 | 3 |
| config_3  | rsi_reversion | 1.32 | 13.8% | -7.5% | 80.0% | 4 | 5 |

---

## 7. Programmatische Verwendung

### Einzelne Konfiguration testen

```python
from src.backtest.walkforward import (
    WalkForwardConfig,
    run_walkforward_for_config,
)
from src.strategies.rsi_reversion import generate_signals

# Walk-Forward-Config erstellen
wf_config = WalkForwardConfig(
    train_window="180d",
    test_window="30d",
    symbol="BTC/EUR",
)

# Strategie-Parameter
strategy_params = {
    "rsi_period": 14,
    "oversold_level": 30,
    "overbought_level": 70,
}

# Walk-Forward ausführen
result = run_walkforward_for_config(
    config_id="my_config",
    wf_config=wf_config,
    df=df,  # OHLCV-DataFrame
    strategy_name="rsi_reversion",
    strategy_params=strategy_params,
    strategy_signal_fn=generate_signals,
)

# Ergebnisse analysieren
print(f"Avg Sharpe: {result.aggregate_metrics['avg_sharpe']:.2f}")
print(f"Win Rate: {result.aggregate_metrics['win_rate_windows']:.1%}")
```

### Top-N-Konfigurationen aus Sweep testen

```python
from src.backtest.walkforward import (
    WalkForwardConfig,
    run_walkforward_for_top_n_from_sweep,
)

# Walk-Forward-Config
wf_config = WalkForwardConfig(
    train_window="180d",
    test_window="30d",
)

# Walk-Forward für Top-N aus Sweep
results = run_walkforward_for_top_n_from_sweep(
    sweep_name="rsi_reversion_basic",
    wf_config=wf_config,
    top_n=3,
    df=df,
)

# Beste Konfiguration finden
best = max(results, key=lambda r: r.aggregate_metrics.get("avg_sharpe", 0.0))
print(f"Beste Config: {best.config_id}")
print(f"Avg Sharpe: {best.aggregate_metrics['avg_sharpe']:.2f}")
```

### Reports generieren

```python
from src.reporting.walkforward_report import (
    build_walkforward_report,
    build_multi_config_report,
    save_walkforward_report,
)

# Einzelner Report
report = build_walkforward_report(
    result,
    sweep_name="rsi_reversion_basic",
    wf_config=wf_config,
)
save_walkforward_report(
    report,
    Path("reports/walkforward"),
    sweep_name="rsi_reversion_basic",
    config_id=result.config_id,
)

# Vergleichs-Report
comparison_report = build_multi_config_report(
    results,
    sweep_name="rsi_reversion_basic",
)
```

---

## 8. Technische Details

### Fenster-Aufteilung

Die Funktion `split_train_test_windows()` teilt den Zeitraum in Train/Test-Fenster auf:

- **Strikte Regel**: Nur vollständige Fenster werden erstellt
- **Keine Überlappung**: Test-Fenster folgen direkt auf Train-Fenster
- **Schrittgröße**: Standard = `test_window` (keine Überlappung), konfigurierbar via `step_size`
- **Unvollständige Fenster**: Werden am Ende verworfen

### Metriken-Aggregation

Die Funktion `_compute_aggregate_metrics()` berechnet:

- **Durchschnitte**: `avg_sharpe`, `avg_return`, `avg_max_drawdown`
- **Min/Max**: `min_sharpe`, `max_sharpe`, `min_return`, `max_return`
- **Win-Rate**: `positive_windows`, `total_windows`, `win_rate_windows`

### Fehlerbehandlung

- **Fehlende Daten**: `ValueError` wenn DataFrame leer oder ohne DatetimeIndex
- **Zu kurzer Zeitraum**: `ValueError` wenn Zeitraum kürzer als Train + Test
- **Fehlende Strategie**: `ValueError` wenn Strategie nicht gefunden
- **Einzelne Fenster-Fehler**: Werden geloggt, aber brechen nicht den gesamten Run ab

---

## 9. Troubleshooting

### Problem: Keine Fenster erstellt

**Symptom:** `ValueError: Keine vollständigen Fenster erstellt`

**Ursache:** Zeitraum ist zu kurz für Train + Test

**Lösung:**
- Längeren Zeitraum verwenden (mehr Daten)
- Kürzere Train/Test-Fenster wählen
- Prüfen: `(end - start) >= train_window + test_window`

### Problem: Keine Sweep-Ergebnisse gefunden

**Symptom:** `FileNotFoundError: Keine Ergebnisse gefunden für Sweep`

**Ursache:** Sweep wurde noch nicht ausgeführt

**Lösung:**
```bash
# Sweep zuerst ausführen
python scripts/run_strategy_sweep.py --sweep-name rsi_reversion_basic
```

### Problem: Keine Top-N-Konfigurationen gefunden

**Symptom:** `ValueError: Keine Konfigurationen für Sweep gefunden`

**Ursache:** Sweep-Ergebnisse enthalten keine gültigen Metriken

**Lösung:**
- Prüfen, ob Sweep erfolgreich war
- Prüfen, ob Metriken vorhanden sind (z.B. `metric_sharpe_ratio`)
- Fallback-Metrik verwenden: `--metric-fallback metric_total_return`

### Problem: Walk-Forward dauert sehr lange

**Ursache:** Viele Fenster oder große Datenmengen

**Lösung:**
- Weniger Fenster: Kürzere Zeiträume oder größere `step_size`
- Weniger Top-N: `--top-n 3` statt `--top-n 10`
- Weniger Daten: Kürzerer Zeitraum via `--start-date` / `--end-date`

---

## 10. Zusammenfassung & Ausblick

### Was Phase 44 bietet

- **Out-of-Sample-Validierung** für Top-N-Konfigurationen aus Sweeps
- **Robustness-Check** über mehrere Marktphasen
- **Automatische Report-Generierung** mit aggregierten Metriken
- **Integration** in bestehenden Research-Workflow (Sweep → Top-N → Walk-Forward)

### Nächste Schritte

Phase 44 ist die Basis für weitere Robustness-Analysen:

- **Monte-Carlo-Simulationen** ✅ (Phase 45): Bootstrapped Sharpe-Ratio-Konfidenzintervalle, statistische Unsicherheitsquantifizierung
  - **Siehe:** `docs/PHASE_45_MONTE_CARLO_ROBUSTNESS_AND_STRESS_TESTS.md` für Details
  - **Abgrenzung:** Walk-Forward testet zeitliche Robustheit, Monte-Carlo testet statistische Robustheit
- **Erweiterte Stress-Tests**: Vol-Spikes, Flash-Crashes, Liquidity-Dry-ups (zukünftig)
- **Regime-basierte Analyse**: Walk-Forward getrennt nach Marktregimen (zukünftig)

Siehe `docs/Peak_Trade_Research_Strategy_Roadmap_2025-12-07.md` für Details zur Research-Roadmap.

---

## 11. Referenzen

- **Phase 41**: `docs/PHASE_41_STRATEGY_SWEEPS_AND_RESEARCH_PLAYGROUND.md`
- **Phase 42**: `docs/PHASE_42_TOPN_PROMOTION.md`
- **Phase 43**: `docs/PHASE_43_VISUALIZATION_AND_SWEEP_DASHBOARDS.md`
- **Phase 45**: `docs/PHASE_45_MONTE_CARLO_ROBUSTNESS_AND_STRESS_TESTS.md` (Monte-Carlo-Robustness)
- **Research Roadmap**: `docs/Peak_Trade_Research_Strategy_Roadmap_2025-12-07.md`
- **Research ToDo**: `docs/Peak_Trade_Research_Strategy_TODO_2025-12-07.md`

