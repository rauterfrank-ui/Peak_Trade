# Phase – Regime-Aware Reporting & Heatmaps

## Übersicht

Diese Phase erweitert die bestehende Reporting-Infrastruktur um **Regime-Aware Sichtweisen** für Backtests und Experimente. Regime-Aware Strategien und Portfolios können nun mit spezialisierten Kennzahlen und Visualisierungen analysiert werden.

**Status:** ✅ Implementiert
**Phase:** Research/Backtest/Experiments (kein Live)
**Datum:** 2025-12-07

---

## Ziele

1. **Regime-spezifische Kennzahlen** für Backtests:
   - Performance je Regime (Risk-On / Neutral / Risk-Off)
   - Anteil der Zeit in jedem Regime
   - Drawdown- & Risiko-Kennzahlen pro Regime
   - Trade-Statistiken nach Entry-Regime

2. **Regime-Visualisierungen**:
   - Equity-Kurve mit Regime-Overlay (farbige Hintergrund-Bänder)
   - Regime-Timeline (optional)
   - Für Sweeps: Heatmaps für Regime-Parameter (z.B. `neutral_scale` vs. `risk_off_scale`)

3. **Integration in bestehende Report-CLIs**:
   - Optionale Flags (`--with-regime`, `--with-regime-heatmaps`)
   - Automatische Erkennung von Regime-Aware Sweeps

---

## Features

### 1. Regime-Bucket-Kennzahlen

Für jeden Regime-Bucket (Risk-On, Neutral, Risk-Off) werden folgende Metriken berechnet:

- **Time Fraction**: Anteil der Zeit in diesem Regime (0.0-1.0)
- **Time Share [%]**: Anteil der Zeit als Prozent (0-100%)
- **Total Return**: Gesamtrendite in diesem Regime
- **Return Contribution [%]**: Beitrag dieses Regimes zur Gesamt-Performance in Prozent
- **Annualized Return**: Annualisierte Rendite (wenn möglich)
- **Sharpe Ratio**: Risk-adjusted Return
- **Max Drawdown**: Maximaler Drawdown in diesem Regime
- **Trades**: Anzahl Trades in diesem Regime
- **Win Rate**: Win-Rate der Trades (optional)

### 2. Equity mit Regime-Overlay

Die Equity-Curve wird mit farbigen Hintergrund-Bändern visualisiert:

- **Grün (Risk-On)**: Perioden mit Regime = 1
- **Grau (Neutral)**: Perioden mit Regime = 0
- **Rot (Risk-Off)**: Perioden mit Regime = -1

### 3. Regime-Heatmaps für Sweeps

Für `regime_aware_portfolio_*` Sweeps werden automatisch Heatmaps erstellt, die z.B.:

- `neutral_scale` vs. `risk_off_scale` mit Sharpe/CAGR kombinieren
- Vol-Metrik vs. Kennzahl für Preset C

### 4. Regime Contribution View

**Return Contribution by Regime** – Ein Balken-Plot zeigt auf einen Blick:

- **Wo wird wirklich Geld verdient?** (positive Contribution)
- **Wo wird Geld verbrannt?** (negative Contribution)
- **Wie verteilt sich die Performance auf die Regimes?**

Der Plot wird automatisch in Backtest-Reports mit `--with-regime` erstellt und zeigt:

- Farbcodierte Balken (Grün=Risk-On, Grau=Neutral, Rot=Risk-Off)
- Prozentuale Contribution-Werte auf jedem Balken
- Nulllinie zur schnellen Orientierung

**Tabelle mit Contribution & Time-Share:**

Die Regime-Analyse-Tabelle enthält zusätzlich:

- **Bars [%]**: Zeitanteil als Prozent (z.B. "33.3%")
- **Return Contribution [%]**: Beitrag zur Gesamt-Performance (z.B. "60.0%")

Diese Metriken helfen dabei, schnell zu erkennen:

- Welches Regime den größten Beitrag zur Performance leistet
- Ob die Zeitverteilung (Time Share) mit der Performance-Verteilung (Contribution) übereinstimmt
- Ob z.B. Risk-On nur 20% der Zeit ist, aber 80% der Performance beiträgt

---

## Verwendung

### Backtest-Reports mit Regime-Analyse

```bash
# Standard-Backtest-Report mit Regime-Daten
python scripts/generate_backtest_report.py \
    --results-file results/regime_aware_backtest.parquet \
    --equity-file results/equity.parquet \
    --with-regime \
    --output reports/regime_aware_backtest.md
```

**Voraussetzungen:**

- Regime-Daten müssen verfügbar sein (entweder in Results-Datei oder als separate Datei `*_regime.parquet`/`*_regime.csv`)
- Regime-Werte müssen numerisch sein: `1` (Risk-On), `0` (Neutral), `-1` (Risk-Off)

**Output:**

- Standard Backtest-Report mit zusätzlicher "Regime-Analyse" Section
- Equity-Plot mit Regime-Overlay (`equity_with_regimes.png`)
- **Return Contribution by Regime** Balken-Plot (`regime_contribution.png`)
- Tabelle mit Regime-Bucket-Kennzahlen (inkl. Contribution & Time-Share)
- Zusammenfassung (z.B. "Risk-On trägt X% zur Gesamtrendite bei")

### Experiment-/Sweep-Reports mit Regime-Heatmaps

```bash
# Regime-Aware Portfolio Sweep Report
python scripts/generate_experiment_report.py \
    --input results/regime_aware_portfolio_aggressive.parquet \
    --output reports/regime_aware_aggressive_sweep.md \
    --with-regime-heatmaps \
    --sort-metric metric_sharpe \
    --top-n 20
```

**Automatische Erkennung:**

Wenn der Titel "regime_aware" enthält, werden Regime-Heatmaps automatisch erstellt (auch ohne `--with-regime-heatmaps` Flag).

**Output:**

- Standard Experiment-Report
- Zusätzliche Heatmaps für Regime-Parameter (z.B. `neutral_scale` vs. `risk_off_scale`)
- Top-N Konfigurationen nach Sharpe / niedrigstem MaxDD

---

## Interpretation

### Regime-Bucket-Kennzahlen lesen

**Beispiel-Interpretation:**

```
Regime-Performance Übersicht:
| Regime   | Time Fraction | Total Return | Sharpe | Max Drawdown | Trades |
|----------|---------------|--------------|--------|--------------|--------|
| Risk-On  | 50.0%         | 15.00%       | 1.50   | -5.00%       | 10     |
| Neutral  | 30.0%         | -2.00%       | -0.30  | -3.00%       | 5      |
| Risk-Off | 20.0%         | -5.00%       | -0.80  | -8.00%       | 2      |
```

**Erkenntnisse:**

- **Risk-On trägt 60% zur Gesamtrendite bei** (50% der Zeit, 10 Trades) → Sehr effizient!
- **Risk-Off ist Hauptquelle der Drawdowns** (-8% MaxDD, nur 20% der Zeit) → Vermeiden!
- **Neutral-Perioden sind schwach** (negative Rendite, niedrige Sharpe) → Reduzieren!

**Contribution-Interpretation:**

- **Risk-On**: 50% der Zeit, aber 60% der Performance → **Überproportional profitabel**
- **Neutral**: 30% der Zeit, aber -10% der Performance → **Unterproportional, sogar negativ**
- **Risk-Off**: 20% der Zeit, aber -30% der Performance → **Sehr schädlich, komplett vermeiden**

**Handlungsempfehlungen:**

- Erhöhe `risk_off_scale` auf 0.0 (komplett aus in Risk-Off)
- Reduziere `neutral_scale` (Neutral-Perioden sind nicht profitabel)
- Fokussiere auf Risk-On-Perioden (starke Performance)

### Regime-Heatmaps interpretieren

**Beispiel-Heatmap:** `neutral_scale` (X-Achse) vs. `risk_off_scale` (Y-Achse), Farbe = Sharpe

- **Grüne Bereiche**: Hohe Sharpe-Ratio → gute Parameter-Kombination
- **Rote Bereiche**: Niedrige Sharpe-Ratio → vermeiden
- **Muster erkennen**: Z.B. "Niedrige `risk_off_scale` + mittlere `neutral_scale` = beste Performance"

---

## Praxisbeispiel: BTCUSDT Regime-Aware Portfolio

Als Referenz für die praktische Nutzung der Regime-Reporting-Infrastruktur gibt es eine ausführliche Case Study:

- [`docs/CASE_STUDY_REGIME_ANALYSIS_BTCUSDT.md`](CASE_STUDY_REGIME_ANALYSIS_BTCUSDT.md)

Diese Case Study zeigt den kompletten Flow:

- Setup & Kontext einer konkreten Strategie (BTCUSDT Regime-Aware Portfolio)
- Regime-Analyse-Tabelle mit:
  - Bars [%]
  - Return
  - Return Contribution [%]
  - Sharpe und Max Drawdown je Regime
- Quant-Lead-Analyse mit:
  - Effizienz-Betrachtung (Contribution% / Bars%)
  - klaren Parametervorschlägen (z.B. `risk_off_scale = 0.00`)
- Ableitung konkreter Folge-Experimente (Sweeps, Walk-Forward, Regime-Threshold-Checks)

Damit dient die Case Study als Blaupause, wie Regime-Reporting-Ergebnisse in konkrete Portfolio- und Parameter-Entscheidungen übersetzt werden können.

---

## Technische Details

### Regime-Datenformat

Regime-Daten müssen als `pd.Series` mit numerischen Werten vorliegen:

- `1` = Risk-On (Low-Vol, Trading erlaubt)
- `0` = Neutral (Mittlere Vol, reduzierte Aktivität)
- `-1` = Risk-Off (High-Vol, Trading blockiert)

**Quellen:**

1. **Vol-Regime-Filter** mit `regime_mode=True`:
   ```python
   from src.strategies.vol_regime_filter import VolRegimeFilter
   
   filter = VolRegimeFilter(
       regime_mode=True,
       low_vol_threshold=0.5,
       high_vol_threshold=2.0,
   )
   regimes = filter.generate_signals(data)  # 1/0/-1
   ```

2. **Regime-Aware Portfolio**:
   ```python
   from src.strategies.regime_aware_portfolio import RegimeAwarePortfolioStrategy
   
   strategy = RegimeAwarePortfolioStrategy(...)
   regimes = strategy.get_regime_signals(data)  # 1/0/-1
   ```

### Integration in Backtest-Results

Regime-Daten können auf verschiedene Weise in Backtest-Results integriert werden:

1. **Als separate Datei**: `backtest_result_regime.parquet`
2. **In BacktestResult.metadata**: `metadata["regime_series"] = regimes`
3. **In Results DataFrame**: Spalte `regime` oder `regime_signal`

Die Reporting-Funktionen versuchen automatisch, Regime-Daten zu finden.

---

## Code-Struktur

### Neue Module

- **`src/reporting/regime_reporting.py`**:
  - `RegimeBucketMetrics`: Dataclass für Regime-Bucket-Metriken
  - `RegimeStatsSummary`: Zusammenfassung aller Buckets
  - `compute_regime_stats()`: Berechnet Regime-spezifische Kennzahlen
  - `build_regime_report_section()`: Erstellt ReportSection

### Erweiterte Module

- **`src/reporting/plots.py`**:
  - `save_equity_with_regime_overlay()`: Equity-Plot mit numerischen Regime-Werten

- **`src/reporting/backtest_report.py`**:
  - `build_backtest_report()`: Unterstützt jetzt `regimes` Parameter
  - Automatische Regime-Analyse wenn Regime-Daten vorhanden

- **`src/reporting/experiment_report.py`**:
  - `build_experiment_report()`: Unterstützt `with_regime_heatmaps` Flag
  - Automatische Heatmap-Erstellung für `regime_aware_*` Sweeps

### CLI-Skripte

- **`scripts/generate_backtest_report.py`**:
  - `--with-regime`: Aktiviert Regime-Analyse

- **`scripts/generate_experiment_report.py`**:
  - `--with-regime-heatmaps`: Aktiviert Regime-Heatmaps

---

## Tests

### Unit-Tests

- **`tests/test_reporting_regime_reporting.py`**:
  - Tests für `compute_regime_stats()`
  - Tests für `build_regime_report_section()`
  - Tests für `RegimeBucketMetrics`

### Integrationstests

- **`tests/test_reporting_regime_backtest_integration.py`**:
  - Backtest-Report mit Regime-Daten
  - Backtest-Report ohne Regime-Daten
  - Fehlerbehandlung bei ungültigen Regime-Daten

- **`tests/test_reporting_regime_experiment_report.py`**:
  - Experiment-Report mit Regime-Heatmaps
  - Automatische Erkennung von Regime-Aware Sweeps

**Tests ausführen:**

```bash
pytest tests/test_reporting_regime_reporting.py
pytest tests/test_reporting_regime_backtest_integration.py
pytest tests/test_reporting_regime_experiment_report.py
```

---

## Ausblick

### Potenzielle Erweiterungen

1. **Regime-spezifische Monte-Carlo-Analysen**:
   - Simulation von Regime-Übergängen
   - Stress-Tests für verschiedene Regime-Szenarien

2. **Regime-Heatmaps im HTML-Dashboard**:
   - Interaktive Heatmaps mit Hover-Informationen
   - Filter nach Regime-Parametern

3. **Regime-Transition-Analyse**:
   - Analyse von Regime-Übergängen (z.B. Risk-On → Risk-Off)
   - Performance während Übergängen

4. **Multi-Regime-Vergleich**:
   - Vergleich verschiedener Regime-Definitionen (Vol, Trend, Combined)
   - Heatmaps für Regime-Parameter-Kombinationen

---

## Bekannte Limitationen

1. **Regime-Daten müssen explizit bereitgestellt werden**:
   - Keine automatische Regime-Erkennung aus Equity-Curve
   - Regime-Daten müssen aus Strategie/Filter stammen

2. **Nur numerische Regime-Werte (1/0/-1)**:
   - String-Labels werden unterstützt, aber nicht für Regime-Analyse verwendet
   - Andere Kodierungen (z.B. 2, 3) werden als "unbekannt" behandelt

3. **Trade-Zuordnung zu Regimes**:
   - Trades werden dem Entry-Regime zugeordnet
   - Exit-Regime wird nicht berücksichtigt

---

## Changelog

### 2025-12-07: Initiale Implementierung

- ✅ `regime_reporting.py` Modul erstellt
- ✅ `save_equity_with_regime_overlay()` Funktion hinzugefügt
- ✅ Backtest-Report um Regime-Analyse erweitert
- ✅ Experiment-Report um Regime-Heatmaps erweitert
- ✅ CLI-Skripte um `--with-regime` / `--with-regime-heatmaps` erweitert
- ✅ Tests erstellt
- ✅ Dokumentation erstellt

### 2025-12-07: Regime Contribution & Risk Profile

- ✅ `RegimeBucketMetrics` um `return_contribution_pct` und `time_share_pct` erweitert
- ✅ `compute_regime_stats()` berechnet jetzt Contribution & Time-Share
- ✅ `save_regime_contribution_bars()` Plot-Funktion hinzugefügt
- ✅ Backtest-Report integriert Contribution-Plot automatisch
- ✅ Regime-Analyse-Tabelle zeigt jetzt Contribution & Time-Share
- ✅ Tests für Contribution & Time-Share erweitert
- ✅ Dokumentation um "Regime Contribution View" Abschnitt ergänzt

---

## Referenzen

- **Regime-Aware Strategien**: `docs/PHASE_REGIME_AWARE_PORTFOLIOS.md`
- **Regime-Aware Sweeps**: `docs/PHASE_REGIME_AWARE_SWEEPS_AND_PRESETS.md`
- **Reporting-Infrastruktur**: `docs/PHASE_30_REPORTING_AND_VISUALIZATION.md`

