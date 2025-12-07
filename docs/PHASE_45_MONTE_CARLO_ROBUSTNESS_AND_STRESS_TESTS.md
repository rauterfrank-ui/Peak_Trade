# Phase 45 – Monte-Carlo-Robustness & Stress-Testing

**Status:** ✅ Implementiert  
**Datum:** 2025-12-07  
**Basiert auf:** Phasen 29, 41–44 (Experiments, Sweeps, Top-N, Walk-Forward)

---

## 1. Status & Kontext

Phase 45 implementiert **Monte-Carlo-Robustness-Analysen** für Peak_Trade-Strategien. Diese Phase baut auf den vorherigen Phasen auf:

- **Phase 29:** Experiment-Registry & Sweeps
- **Phase 41:** Strategy-Sweeps & Research-Playground
- **Phase 42:** Top-N Promotion
- **Phase 43:** Visualisierung & Sweep-Dashboards
- **Phase 44:** Walk-Forward-Testing

### Ziel

Während Walk-Forward-Testing die **zeitliche Robustheit** einer Strategie prüft (wie gut funktioniert sie in verschiedenen Zeitfenstern?), quantifiziert Monte-Carlo die **statistische Robustheit** durch Bootstrap-Resampling der Returns.

**Hauptnutzen:**
- Konfidenzintervalle für Kennzahlen (Sharpe, CAGR, Max-Drawdown)
- Quantifizierung der Unsicherheit in Backtest-Ergebnissen
- Identifikation von Strategien mit hoher Varianz (instabil)

---

## 2. Konzept: Monte-Carlo-Robustness

### 2.1 Grundidee

Monte-Carlo-Simulationen basieren auf **Bootstrap-Resampling** der originalen Returns:

1. **Original-Backtest:** Strategie liefert eine Serie von Returns (z.B. tägliche/höchstfrequente Returns)
2. **Bootstrap:** Ziehe zufällig Returns aus der Original-Serie (mit Replacement)
3. **Simulation:** Berechne Kennzahlen für die resampled Serie
4. **Wiederholung:** Führe Schritt 2–3 viele Male durch (z.B. 1000 Runs)
5. **Zusammenfassung:** Analysiere Verteilung der Kennzahlen über alle Runs

### 2.2 Unterschied zu Walk-Forward

| Aspekt | Walk-Forward | Monte-Carlo |
|--------|--------------|-------------|
| **Robustheitstyp** | Zeitlich (verschiedene Zeitfenster) | Statistisch (Resampling) |
| **Input** | Verschiedene Train/Test-Fenster | Original-Returns (resampled) |
| **Output** | Performance über Zeit | Verteilung der Kennzahlen |
| **Frage** | "Funktioniert die Strategie in verschiedenen Perioden?" | "Wie unsicher sind die Backtest-Kennzahlen?" |

**Beide Methoden ergänzen sich:** Eine robuste Strategie sollte sowohl zeitlich als auch statistisch robust sein.

### 2.3 Bootstrap-Methoden

#### Simple Bootstrap (i.i.d.)
- Zieht einzelne Returns zufällig mit Replacement
- Annahme: Returns sind unabhängig (i.i.d.)
- **Vorteil:** Schnell, einfach
- **Nachteil:** Ignoriert Autokorrelation

#### Block-Bootstrap
- Zieht Blöcke von Returns (z.B. 20 aufeinanderfolgende Returns)
- Erhält grob die Autokorrelation
- **Vorteil:** Realistischer für seriell korrelierte Returns
- **Nachteil:** Langsamer, benötigt Block-Größe

---

## 3. Technischer Überblick

### 3.1 Module-Struktur

```
src/experiments/monte_carlo.py          # Monte-Carlo-Engine & Config
src/reporting/monte_carlo_report.py     # Report-Generierung
scripts/run_monte_carlo_robustness.py   # CLI-Script
scripts/research_cli.py                 # Integration (Subcommand "montecarlo")
```

### 3.2 Kern-Komponenten

#### `MonteCarloConfig`
```python
@dataclass
class MonteCarloConfig:
    num_runs: int = 1000
    method: Literal["simple", "block_bootstrap"] = "simple"
    block_size: int = 20
    seed: Optional[int] = 42
```

#### `run_monte_carlo_from_returns`
```python
def run_monte_carlo_from_returns(
    returns: pd.Series,
    config: MonteCarloConfig,
    *,
    stats_fn: Optional[Callable[[pd.Series], Dict[str, float]]] = None,
) -> MonteCarloSummaryResult:
    """
    Führt Monte-Carlo-Simulationen auf einer Serie von Returns durch.
    
    Returns:
        MonteCarloSummaryResult mit Verteilungen + Quantilen
    """
```

#### `MonteCarloSummaryResult`
```python
@dataclass
class MonteCarloSummaryResult:
    config: MonteCarloConfig
    metric_distributions: Dict[str, pd.Series]  # Pro Metrik: Serie der Werte
    metric_quantiles: Dict[str, Dict[str, float]]  # Pro Metrik: {"p5": ..., "p50": ..., "p95": ...}
    num_runs: int
```

### 3.3 Integration mit Experiment-Registry

Monte-Carlo kann auf Top-N-Konfigurationen aus Sweeps angewendet werden:

1. **Input:** Sweep-Name + Top-N
2. **Lade:** Top-N-Konfigurationen (via `load_top_n_configs_for_sweep`)
3. **Extrahiere:** Returns/Equity-Curves für jede Konfiguration
4. **Führe aus:** Monte-Carlo für jede Konfiguration
5. **Output:** Reports pro Konfiguration

---

## 4. Workflow: Von Top-N zu Monte-Carlo

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

# 3. Monte-Carlo-Analyse
python scripts/research_cli.py montecarlo \
    --sweep-name rsi_reversion_basic \
    --config config/config.toml \
    --top-n 3 \
    --num-runs 1000 \
    --method simple \
    --format both
```

### 4.2 Beispiel-CLI-Aufrufe

#### Simple Bootstrap (Standard)
```bash
python scripts/research_cli.py montecarlo \
    --sweep-name rsi_reversion_basic \
    --config config/config.toml \
    --top-n 3 \
    --num-runs 1000 \
    --method simple \
    --seed 42
```

#### Block-Bootstrap
```bash
python scripts/research_cli.py montecarlo \
    --sweep-name ma_crossover_basic \
    --config config/config.toml \
    --top-n 5 \
    --num-runs 2000 \
    --method block_bootstrap \
    --block-size 20
```

#### Mit Dummy-Daten (für Tests)
```bash
python scripts/research_cli.py montecarlo \
    --sweep-name test_sweep \
    --config config/config.toml \
    --top-n 3 \
    --use-dummy-data \
    --dummy-bars 500
```

### 4.3 Output-Struktur

```
reports/monte_carlo/
└── {sweep_name}/
    ├── config_1/
    │   ├── monte_carlo_report.md
    │   ├── monte_carlo_report.html
    │   ├── sharpe_distribution.png
    │   ├── cagr_distribution.png
    │   └── max_drawdown_distribution.png
    ├── config_2/
    │   └── ...
    └── ...
```

---

## 5. Konfiguration & Parameter

### 5.1 Monte-Carlo-Parameter

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `num_runs` | 1000 | Anzahl Monte-Carlo-Runs (mehr = präziser, aber langsamer) |
| `method` | `"simple"` | Bootstrap-Methode (`"simple"` oder `"block_bootstrap"`) |
| `block_size` | 20 | Block-Größe für Block-Bootstrap (nur relevant für `block_bootstrap`) |
| `seed` | 42 | Random Seed für Reproduzierbarkeit |

### 5.2 Performance vs. Genauigkeit

- **100 Runs:** Schnell (~1–2 Sekunden), aber ungenau
- **1000 Runs:** Guter Kompromiss (~10–20 Sekunden), Standard
- **10000 Runs:** Sehr präzise (~2–5 Minuten), für finale Analysen

**Empfehlung:** Starte mit 1000 Runs, erhöhe auf 5000–10000 für finale Validierung.

### 5.3 Bootstrap-Methode wählen

**Simple Bootstrap verwenden, wenn:**
- Returns annähernd i.i.d. sind
- Schnelle Ergebnisse benötigt werden
- Erste Robustheits-Checks

**Block-Bootstrap verwenden, wenn:**
- Returns seriell korreliert sind (z.B. durch Regime-Wechsel)
- Realistischere Unsicherheitsschätzung benötigt wird
- Finale Validierung vor Live-Trading

---

## 6. Reports & Interpretation

### 6.1 Report-Struktur

Ein Monte-Carlo-Report enthält:

1. **Overview:** Konfiguration, Anzahl Runs, Methode
2. **Metric Summary (Quantiles):** Tabelle mit p5, p25, p50, p75, p95 für alle Metriken
3. **Distributions:** Histogramme für wichtige Metriken (Sharpe, CAGR, Max-Drawdown)
4. **Interpretation:** Erklärung der Quantilen

### 6.2 Beispiel-Tabelle

| Metric | Mean | Std | p5 | p25 | p50 | p75 | p95 |
|--------|------|-----|----|----|----|----|----|
| sharpe | 1.5234 | 0.2341 | 1.1234 | 1.3456 | 1.5123 | 1.6789 | 1.9123 |
| cagr | 0.1523 | 0.0234 | 0.1123 | 0.1345 | 0.1512 | 0.1678 | 0.1912 |
| max_drawdown | -0.1023 | 0.0123 | -0.1234 | -0.1112 | -0.1012 | -0.0923 | -0.0812 |

### 6.3 Interpretation

**Robustes Setup sollte haben:**

1. **Hoher Median (p50):** z.B. Sharpe p50 > 1.5
2. **Kleine Spannweite:** p95 - p5 sollte nicht zu groß sein (niedrige Unsicherheit)
3. **Positive p5-Werte:** Für Return-Metriken sollte p5 > 0 sein (auch im Worst-Case positiv)

**Beispiel-Interpretation:**

- **Sharpe p50 = 1.5, p5 = 1.1, p95 = 1.9:** Robust, auch im Worst-Case noch Sharpe > 1.0 ✅
- **Sharpe p50 = 1.8, p5 = 0.3, p95 = 3.2:** Instabil, hohe Varianz ⚠️
- **CAGR p50 = 0.15, p5 = -0.05, p95 = 0.35:** Riskant, kann negativ sein ❌

---

## 7. Stress-Tests

### 7.1 Status

**Monte-Carlo** (Phase 45) fokussiert auf Bootstrap-basierte Robustheit durch statistisches Resampling.

**Stress-Tests** (Phase 46) sind in einer separaten Phase implementiert und fokussieren auf deterministische Szenario-Transformationen (Crash-Szenarien, Vol-Spikes, etc.).

Siehe: [PHASE_46_STRESS_TESTS_AND_CRASH_SCENARIOS.md](PHASE_46_STRESS_TESTS_AND_CRASH_SCENARIOS.md) für Details.

### 7.2 Unterschied

| Aspekt | Monte-Carlo (Phase 45) | Stress-Tests (Phase 46) |
|--------|------------------------|------------------------|
| **Methode** | Bootstrap-Resampling | Deterministische Transformationen |
| **Frage** | "Wie unsicher sind die Kennzahlen?" | "Was passiert bei einem Crash?" |
| **Output** | Verteilungen & Quantilen | Baseline vs. Szenario-Vergleiche |

---

## 8. Integration in Research-CLI

### 8.1 Subcommand `montecarlo`

```bash
python scripts/research_cli.py montecarlo \
    --sweep-name {sweep_name} \
    --config {config_path} \
    --top-n {n} \
    [--num-runs {runs}] \
    [--method {simple|block_bootstrap}] \
    [--block-size {size}] \
    [--format {md|html|both}]
```

### 8.2 Pipeline-Integration (Zukünftig)

Die Pipeline könnte optional Monte-Carlo ausführen:

```bash
python scripts/research_cli.py pipeline \
    --sweep-name rsi_reversion_basic \
    --config config/config.toml \
    --top-n 5 \
    --run-walkforward \
    --run-montecarlo  # (noch nicht implementiert)
```

**Status:** Pipeline-Integration ist vorbereitet, aber aktuell nicht aktiv. Kann in späteren Phasen ergänzt werden.

---

## 9. Tests

### 9.1 Test-Coverage

- `tests/test_monte_carlo_robustness.py`: Unit-Tests für Monte-Carlo-Engine
- `tests/test_research_cli.py`: Integration-Tests für `montecarlo`-Subcommand

### 9.2 Test-Ausführung

```bash
# Alle Monte-Carlo-Tests
pytest tests/test_monte_carlo_robustness.py -v

# Research-CLI-Tests (inkl. montecarlo)
pytest tests/test_research_cli.py -v
```

---

## 10. Referenzen & Nächste Schritte

### 10.1 Verwandte Phasen

- **Phase 41:** Strategy-Sweeps & Research-Playground
- **Phase 42:** Top-N Promotion
- **Phase 43:** Visualisierung & Sweep-Dashboards
- **Phase 44:** Walk-Forward-Testing

### 10.2 Nächste Schritte (Phase 46+)

- **Erweiterte Stress-Tests:** Volatilitäts-Shocks, Crash-Szenarien
- **Regime-bewusste Monte-Carlo:** Berücksichtigung von Regime-Wechseln
- **Portfolio-Level Monte-Carlo:** Robustheit für Multi-Strategy-Portfolios
- **Live-Trading-Validierung:** Vergleich Monte-Carlo vs. Live-Performance

---

## 11. Zusammenfassung

Phase 45 implementiert **Monte-Carlo-Robustness-Analysen** als Ergänzung zu Walk-Forward-Testing:

✅ **Implementiert:**
- Simple & Block-Bootstrap
- Konfidenzintervalle für Kennzahlen
- Integration in Research-CLI
- Reports mit Quantilen & Visualisierungen

🔮 **Zukünftig:**
- Erweiterte Stress-Tests
- Regime-bewusste Simulationen
- Portfolio-Level-Analysen

**Fazit:** Monte-Carlo quantifiziert die statistische Unsicherheit in Backtest-Ergebnissen und hilft, robuste Strategien zu identifizieren.

