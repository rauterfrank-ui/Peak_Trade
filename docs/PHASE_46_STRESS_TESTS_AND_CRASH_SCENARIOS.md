# Phase 46 – Stress-Tests & Crash-Szenarien

**Status:** ✅ Implementiert  
**Datum:** 2025-12-07  
**Basiert auf:** Phasen 41–45 (Sweeps, Promotion, Visualisierung, Walk-Forward, Monte-Carlo)

---

## 1. Status & Kontext

Phase 46 implementiert **Stress-Tests & Crash-Szenarien** für Peak_Trade-Strategien. Diese Phase baut auf den vorherigen Phasen auf:

- **Phase 41:** Strategy-Sweeps & Research-Playground
- **Phase 42:** Top-N Promotion
- **Phase 43:** Visualisierung & Sweep-Dashboards
- **Phase 44:** Walk-Forward-Testing
- **Phase 45:** Monte-Carlo-Robustness

### Ziel

Während Walk-Forward-Testing die **zeitliche Robustheit** und Monte-Carlo die **statistische Robustheit** prüft, fokussieren Stress-Tests auf **extreme Szenarien**:

- Was passiert bei einem plötzlichen Crash?
- Wie reagiert die Strategie auf Volatilitäts-Spikes?
- Werden Drawdowns unter Stress unkontrollierbar?

**Hauptnutzen:**
- Gezielte Tests von Crash-Szenarien
- Baseline vs. Szenario-Vergleiche
- Identifikation von Schwachstellen unter extremen Bedingungen

---

## 2. Konzept: Stress-Testing

### 2.1 Grundidee

Stress-Tests wenden **deterministische Transformationen** auf Returns/Equity-Curves an:

1. **Baseline:** Original-Returns einer Strategie
2. **Szenario:** Transformation (z.B. Crash-Bar, Vol-Spike)
3. **Vergleich:** Metriken vorher vs. nachher

### 2.2 Unterschied zu Walk-Forward & Monte-Carlo

| Aspekt | Walk-Forward | Monte-Carlo | Stress-Tests |
|--------|--------------|-------------|--------------|
| **Robustheitstyp** | Zeitlich (verschiedene Zeitfenster) | Statistisch (Resampling) | Szenario-basiert (extreme Events) |
| **Input** | Verschiedene Train/Test-Fenster | Original-Returns (resampled) | Original-Returns (transformiert) |
| **Output** | Performance über Zeit | Verteilung der Kennzahlen | Baseline vs. Szenario-Metriken |
| **Frage** | "Funktioniert die Strategie in verschiedenen Perioden?" | "Wie unsicher sind die Backtest-Kennzahlen?" | "Was passiert bei einem Crash?" |

**Alle drei Methoden ergänzen sich:** Eine robuste Strategie sollte zeitlich, statistisch und unter Stress robust sein.

### 2.3 Szenario-Typen

#### `single_crash_bar`
- Einzelner starker negativer Return an einem Tag
- Parameter: `severity` (z.B. 0.2 = 20% Crash)
- Position: `start`, `middle`, `end`

#### `vol_spike`
- Volatilität sprunghaft erhöht in einem Fenster
- Parameter: `severity` (Multiplikator), `window` (Fenstergröße)
- Erhöht die Amplitude der Returns im betroffenen Fenster

#### `drawdown_extension`
- Vorhandene Drawdowns werden verlängert/vertieft
- Identifiziert die stärkste Drawdown-Phase und verstärkt negative Returns dort
- Parameter: `severity` (Verstärkungsfaktor)

#### `gap_down_open`
- Großer einmaliger Gap nach unten
- Additiver negativer Return an einem Zeitpunkt
- Parameter: `severity` (Gap-Größe)

---

## 3. Technischer Überblick

### 3.1 Module-Struktur

```
src/experiments/stress_tests.py          # Stress-Test-Engine & Config
src/reporting/stress_test_report.py      # Report-Generierung
scripts/run_stress_tests.py              # CLI-Script
scripts/research_cli.py                   # Integration (Subcommand "stress")
```

### 3.2 Kern-Komponenten

#### `StressScenarioConfig`
```python
@dataclass
class StressScenarioConfig:
    scenario_type: StressScenarioType
    severity: float = 0.2
    window: int = 5
    position: Literal["start", "middle", "end"] = "middle"
    seed: Optional[int] = 42
```

#### `apply_stress_scenario_to_returns`
```python
def apply_stress_scenario_to_returns(
    returns: pd.Series,
    scenario: StressScenarioConfig,
) -> pd.Series:
    """
    Wendet ein Stress-Szenario auf eine Serie von Returns an.
    """
```

#### `run_stress_test_suite`
```python
def run_stress_test_suite(
    returns: pd.Series,
    scenarios: Iterable[StressScenarioConfig],
    stats_fn: Callable[[pd.Series], Dict[str, float]],
) -> StressTestSuiteResult:
    """
    Führt eine Suite von Stress-Szenarien aus.
    """
```

#### `StressTestSuiteResult`
```python
@dataclass
class StressTestSuiteResult:
    returns: pd.Series
    baseline_metrics: Dict[str, float]
    scenario_results: list[StressScenarioResult]
```

### 3.3 Integration mit Experiment-Registry

Stress-Tests können auf Top-N-Konfigurationen aus Sweeps angewendet werden:

1. **Input:** Sweep-Name + Top-N
2. **Lade:** Top-N-Konfigurationen (via `load_top_n_configs_for_sweep`)
3. **Extrahiere:** Returns/Equity-Curves für jede Konfiguration
4. **Führe aus:** Stress-Tests für jede Konfiguration
5. **Output:** Reports pro Konfiguration

---

## 4. Workflow: Von Top-N zu Stress-Tests

### 4.1 Standard-Workflow

```bash
# 1. Sweep ausführen
python scripts/research_cli.py sweep \
    --sweep-name rsi_reversion_basic \
    --config config/config.toml

# 2. Top-N Promotion
python scripts/research_cli.py promote \
    --sweep-name rsi_reversion_basic \
    --top-n 5

# 3. Stress-Tests
python scripts/research_cli.py stress \
    --sweep-name rsi_reversion_basic \
    --config config/config.toml \
    --top-n 3 \
    --scenarios single_crash_bar vol_spike \
    --severity 0.2 \
    --format both
```

### 4.2 Beispiel-CLI-Aufrufe

#### Einfacher Crash-Test
```bash
python scripts/research_cli.py stress \
    --sweep-name rsi_reversion_basic \
    --config config/config.toml \
    --top-n 3 \
    --scenarios single_crash_bar \
    --severity 0.2
```

#### Mehrere Szenarien
```bash
python scripts/research_cli.py stress \
    --sweep-name ma_crossover_basic \
    --config config/config.toml \
    --top-n 5 \
    --scenarios single_crash_bar vol_spike drawdown_extension \
    --severity 0.3 \
    --window 10 \
    --format both
```

#### Mit Dummy-Daten (für Tests)
```bash
python scripts/research_cli.py stress \
    --sweep-name test_sweep \
    --config config/config.toml \
    --top-n 3 \
    --scenarios single_crash_bar \
    --use-dummy-data \
    --dummy-bars 500
```

### 4.3 Output-Struktur

```
reports/stress/
└── {sweep_name}/
    ├── config_1/
    │   ├── stress_test_report.md
    │   ├── stress_test_report.html
    │   └── equity_comparison.png
    ├── config_2/
    │   └── ...
    └── ...
```

---

## 5. Konfiguration & Parameter

### 5.1 Stress-Test-Parameter

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `scenarios` | `["single_crash_bar", "vol_spike"]` | Liste von Szenario-Typen |
| `severity` | `0.2` | Schweregrad (z.B. 0.2 = 20% Crash) |
| `window` | `5` | Fenster-Größe für vol_spike / drawdown_extension |
| `position` | `"middle"` | Position des Shocks (`start`, `middle`, `end`) |
| `seed` | `42` | Random Seed für Reproduzierbarkeit |

### 5.2 Szenario-spezifische Parameter

**single_crash_bar:**
- `severity`: Größe des Crashs (z.B. 0.2 = -20%)
- `position`: Wo der Crash auftritt

**vol_spike:**
- `severity`: Multiplikator für Volatilität (z.B. 0.5 = +50%)
- `window`: Größe des betroffenen Fensters
- `position`: Wo der Spike auftritt

**drawdown_extension:**
- `severity`: Verstärkungsfaktor für negative Returns
- `window`: Optional, für Fallback wenn keine Drawdown-Phase gefunden wird

**gap_down_open:**
- `severity`: Größe des Gaps (additiv)
- `position`: Wo der Gap auftritt

---

## 6. Reports & Interpretation

### 6.1 Report-Struktur

Ein Stress-Test-Report enthält:

1. **Overview:** Anzahl Szenarien, Baseline-Metriken
2. **Baseline Metrics:** Tabelle mit allen Baseline-Kennzahlen
3. **Scenario Comparison:** Übersichtstabelle mit Baseline vs. Stressed für alle Szenarien
4. **Detailed Scenario Results:** Detaillierte Metriken pro Szenario
5. **Visualizations:** Equity-Kurven-Vergleich (optional)
6. **Interpretation:** Erklärung der Metriken

### 6.2 Beispiel-Tabelle

| Scenario Type | Severity | Baseline Sharpe | Stressed Sharpe | Delta Sharpe |
|---------------|----------|-----------------|-----------------|--------------|
| single_crash_bar | 0.20 | 1.5234 | 1.2345 | -0.2889 |
| vol_spike | 0.50 | 1.5234 | 1.1123 | -0.4111 |

### 6.3 Interpretation

**Robustes Setup sollte haben:**

1. **Kleine Delta-Werte:** Metriken sollten nicht zu stark absinken
2. **Sharpe bleibt > 1.0:** Auch unter Stress sollte Sharpe akzeptabel bleiben
3. **Max Drawdown kontrolliert:** Drawdown sollte nicht unkontrollierbar ansteigen

**Beispiel-Interpretation:**

- **Baseline Sharpe = 1.5, Stressed Sharpe = 1.2, Delta = -0.3:** Akzeptabel, Strategie hält Stress stand ✅
- **Baseline Sharpe = 1.8, Stressed Sharpe = 0.5, Delta = -1.3:** Problematisch, Strategie bricht unter Stress zusammen ❌
- **Baseline Max DD = -10%, Stressed Max DD = -25%, Delta = -15%:** Riskant, Drawdown verdoppelt sich ⚠️

---

## 7. Integration in Research-CLI

### 7.1 Subcommand `stress`

```bash
python scripts/research_cli.py stress \
    --sweep-name {sweep_name} \
    --config {config_path} \
    --top-n {n} \
    [--scenarios {scenario_types}] \
    [--severity {severity}] \
    [--window {window}] \
    [--position {position}] \
    [--format {md|html|both}]
```

### 7.2 Pipeline-Integration ✅

Stress-Tests sind vollständig in die **Research-Pipeline v2** integriert:

```bash
python scripts/research_cli.py pipeline \
    --sweep-name rsi_reversion_basic \
    --config config/config.toml \
    --top-n 5 \
    --run-stress-tests \
    --stress-scenarios single_crash_bar vol_spike \
    --stress-severity 0.2
```

Die Pipeline führt automatisch Sweep → Report → Promotion → Stress-Tests aus. Siehe `docs/PHASE_41_STRATEGY_SWEEPS_AND_RESEARCH_PLAYGROUND.md` für Details zur vollständigen Pipeline.

---

## 8. Tests

### 8.1 Test-Coverage

- `tests/test_stress_tests.py`: Unit-Tests für Stress-Test-Engine
- `tests/test_research_cli.py`: Integration-Tests für `stress`-Subcommand

### 8.2 Test-Ausführung

```bash
# Alle Stress-Test-Tests
pytest tests/test_stress_tests.py -v

# Research-CLI-Tests (inkl. stress)
pytest tests/test_research_cli.py -v
```

---

## 9. Referenzen & Nächste Schritte

### 9.1 Verwandte Phasen

- **Phase 41:** Strategy-Sweeps & Research-Playground
- **Phase 42:** Top-N Promotion
- **Phase 43:** Visualisierung & Sweep-Dashboards
- **Phase 44:** Walk-Forward-Testing
- **Phase 45:** Monte-Carlo-Robustness

### 9.2 Nächste Schritte (Phase 47+)

- **Erweiterte Stress-Szenarien:** Multi-Asset-Crashes, Korrelations-Breakdown
- **Regime-bewusste Stress-Tests:** Stress nur in bestimmten Regimes
- **Portfolio-Level Stress-Tests:** Stress für Multi-Strategy-Portfolios
- **Live-Trading-Validierung:** Vergleich Stress-Tests vs. Live-Performance

---

## 10. Zusammenfassung

Phase 46 implementiert **Stress-Tests & Crash-Szenarien** als Ergänzung zu Walk-Forward und Monte-Carlo:

✅ **Implementiert:**
- 4 Szenario-Typen (single_crash_bar, vol_spike, drawdown_extension, gap_down_open)
- Baseline vs. Szenario-Vergleiche
- Integration in Research-CLI
- Reports mit Metriken-Vergleichen & Visualisierungen

🔮 **Zukünftig:**
- Erweiterte Stress-Szenarien (Multi-Asset, Korrelations-Breakdown)
- Regime-bewusste Stress-Tests
- Portfolio-Level-Analysen

**Fazit:** Stress-Tests identifizieren Schwachstellen unter extremen Bedingungen und helfen, robuste Strategien zu entwickeln.

