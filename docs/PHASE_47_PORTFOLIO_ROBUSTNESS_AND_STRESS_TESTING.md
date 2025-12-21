# Phase 47 – Portfolio-Level Robustness & Stress-Testing

**Status:** ✅ Implementiert  
**Datum:** 2025-12-07  
**Basiert auf:** Phasen 26 (Portfolio-Layer), 41–46 (Single-Strategy Research & Robustness)

---

## 1. Status & Kontext

Phase 47 implementiert **Portfolio-Level Robustness & Stress-Tests** für Peak_Trade. Diese Phase baut auf den vorherigen Phasen auf:

- **Phase 26:** Portfolio-Strategien & Portfolio-Manager
- **Phase 41:** Strategy-Sweeps & Research-Playground
- **Phase 42:** Top-N Promotion
- **Phase 43:** Visualisierung & Sweep-Dashboards
- **Phase 44:** Walk-Forward-Testing
- **Phase 45:** Monte-Carlo-Robustness
- **Phase 46:** Stress-Tests & Crash-Szenarien

### Ziel

Während Phasen 44–46 sich auf **Single-Strategy-Robustness** fokussieren, erweitert Phase 47 die Robustness-Analyse auf **Multi-Strategy-Portfolio-Ebene**:

- Portfolio-Return-Synthese aus mehreren Strategien
- Portfolio-Level Monte-Carlo
- Portfolio-Level Stress-Tests
- Diversifikations-Analyse

**Hauptnutzen:**
- Verständnis, wie sich Diversifikation auf Robustheit auswirkt
- Identifikation von Portfolio-Schwachstellen
- Vergleich Portfolio vs. Einzel-Strategien

---

## 2. Konzept: Portfolio-Level vs. Single-Strategy Robustness

### 2.1 Grundidee

Portfolio-Level Robustness analysiert **Multi-Strategy-Portfolios** statt einzelner Strategien:

1. **Portfolio-Definition:** Mehrere Strategien mit Gewichten
2. **Portfolio-Return-Synthese:** Gewichtete Summe der Einzel-Strategie-Returns
3. **Portfolio-Metriken:** Sharpe, Max-Drawdown, etc. auf Portfolio-Ebene
4. **Robustness-Analyse:** Monte-Carlo & Stress-Tests auf Portfolio-Returns

### 2.2 Unterschied zu Single-Strategy

| Aspekt | Single-Strategy (Phasen 44–46) | Portfolio-Level (Phase 47) |
|--------|--------------------------------|----------------------------|
| **Input** | Eine Strategie-Konfiguration | Mehrere Strategien mit Gewichten |
| **Returns** | Direkt aus Backtest | Synthetisiert (gewichtete Summe) |
| **Frage** | "Wie robust ist Strategie X?" | "Wie robust ist Portfolio aus X, Y, Z?" |
| **Diversifikation** | Nicht relevant | Zentral (Korrelationen, Gewichtung) |

**Beide Ebenen ergänzen sich:** Ein robustes Portfolio sollte aus robusten Einzel-Strategien bestehen, aber Diversifikation kann zusätzliche Robustheit schaffen.

---

## 3. Technischer Überblick

### 3.1 Module-Struktur

```
src/experiments/portfolio_robustness.py          # Portfolio-Robustness-Engine
src/reporting/portfolio_robustness_report.py     # Report-Generierung
scripts/run_portfolio_robustness.py              # CLI-Script
scripts/research_cli.py                          # Integration (Subcommand "portfolio")
```

### 3.2 Kern-Komponenten

#### `PortfolioDefinition`
```python
@dataclass
class PortfolioDefinition:
    name: str
    components: list[PortfolioComponent]  # Liste von Strategien mit Gewichten
    rebalancing: Literal["none", "daily", "weekly", "monthly"] = "none"
```

#### `PortfolioComponent`
```python
@dataclass
class PortfolioComponent:
    strategy_name: str
    config_id: str  # z.B. "config_1" aus Top-N
    weight: float   # Gewicht im Portfolio (0.0-1.0)
```

#### `build_portfolio_returns`
```python
def build_portfolio_returns(
    components: Iterable[PortfolioComponent],
    returns_loader: Callable[[str, str], Optional[pd.Series]],
) -> pd.Series:
    """
    Synthetisiert Portfolio-Returns aus mehreren Komponenten.
    """
```

#### `run_portfolio_robustness`
```python
def run_portfolio_robustness(
    robustness_config: PortfolioRobustnessConfig,
    returns_loader: Callable[[str, str], Optional[pd.Series]],
) -> PortfolioRobustnessResult:
    """
    Führt Portfolio-Level Robustness-Analyse durch.
    """
```

### 3.3 Integration mit Experiment-Registry

Portfolio-Robustness nutzt Top-N-Konfigurationen aus Sweeps:

1. **Input:** Sweep-Name + Top-N
2. **Lade:** Top-N-Konfigurationen (via `load_top_n_configs_for_sweep`)
3. **Definiere:** Portfolio aus Top-N mit Gewichten
4. **Lade:** Returns für jede Komponente (via `returns_loader`)
5. **Synthetisiere:** Portfolio-Returns
6. **Analysiere:** Monte-Carlo & Stress-Tests auf Portfolio-Ebene

---

## 4. Workflow: Von Top-N zu Portfolio-Robustness

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

# 3. Portfolio-Robustness
python scripts/research_cli.py portfolio \
    --sweep-name rsi_reversion_basic \
    --config config/config.toml \
    --top-n 3 \
    --portfolio-name rsi_portfolio_v1 \
    --weights 0.4 0.3 0.3 \
    --run-montecarlo \
    --mc-num-runs 1000 \
    --run-stress-tests \
    --stress-scenarios single_crash_bar vol_spike \
    --stress-severity 0.25 \
    --format both
```

### 4.2 Beispiel-CLI-Aufrufe

#### Mit Equal-Weight
```bash
python scripts/research_cli.py portfolio \
    --sweep-name ma_crossover_basic \
    --config config/config.toml \
    --top-n 5 \
    --portfolio-name ma_portfolio_equal \
    --run-montecarlo \
    --mc-num-runs 2000
```

#### Mit Custom-Weights
```bash
python scripts/research_cli.py portfolio \
    --sweep-name rsi_reversion_basic \
    --config config/config.toml \
    --top-n 3 \
    --portfolio-name rsi_portfolio_weighted \
    --weights 0.5 0.3 0.2 \
    --run-montecarlo \
    --mc-num-runs 1000 \
    --run-stress-tests \
    --stress-scenarios single_crash_bar \
    --stress-severity 0.2
```

#### Mit Dummy-Daten (für Tests)
```bash
python scripts/research_cli.py portfolio \
    --sweep-name test_sweep \
    --config config/config.toml \
    --top-n 3 \
    --portfolio-name test_portfolio \
    --use-dummy-data \
    --dummy-bars 500 \
    --run-montecarlo \
    --mc-num-runs 100
```

### 4.3 Output-Struktur

```
reports/portfolio_robustness/
└── {portfolio_name}/
    ├── portfolio_robustness_report.md
    ├── portfolio_robustness_report.html
    └── portfolio_equity.png
```

---

## 5. Konfiguration & Parameter

### 5.1 Portfolio-Definition

| Parameter | Beschreibung |
|-----------|--------------|
| `--top-n` | Anzahl Top-Konfigurationen für das Portfolio |
| `--portfolio-name` | Name des Portfolios |
| `--weights` | Liste von Gewichten (optional, default: equal-weight) |

**Gewichtung:**
- Wenn `--weights` nicht gesetzt: Equal-Weight (jede Strategie = 1/top-n)
- Wenn `--weights` gesetzt: Muss genau `top-n` Werte haben, die zu 1.0 summieren (oder werden normalisiert)

### 5.2 Monte-Carlo-Parameter

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `--run-montecarlo` | `False` | Aktiviert Monte-Carlo |
| `--mc-num-runs` | `1000` | Anzahl Monte-Carlo-Runs |
| `--mc-method` | `simple` | Methode (`simple` oder `block_bootstrap`) |
| `--mc-block-size` | `20` | Block-Größe für Block-Bootstrap |
| `--mc-seed` | `42` | Random Seed |

### 5.3 Stress-Test-Parameter

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `--run-stress-tests` | `False` | Aktiviert Stress-Tests |
| `--stress-scenarios` | `["single_crash_bar", "vol_spike"]` | Liste von Szenario-Typen |
| `--stress-severity` | `0.2` | Basis-Severity (z.B. 0.2 = 20%) |
| `--stress-window` | `5` | Fenster-Größe für vol_spike / drawdown_extension |
| `--stress-position` | `middle` | Position des Shocks |
| `--stress-seed` | `42` | Random Seed |

---

## 6. Reports & Interpretation

### 6.1 Report-Struktur

Ein Portfolio-Robustness-Report enthält:

1. **Overview:** Portfolio-Name, Anzahl Komponenten, Portfolio-Bars
2. **Portfolio Composition:** Tabelle mit Strategien, Config-IDs, Gewichten
3. **Baseline Metrics:** Portfolio-Level-Metriken (Sharpe, CAGR, Max-Drawdown, etc.)
4. **Monte-Carlo Results (optional):** Quantile-Tabellen für Portfolio-Metriken
5. **Stress-Test Results (optional):** Szenario-Vergleiche (Baseline vs. Stressed)
6. **Visualizations:** Portfolio-Equity-Curve
7. **Interpretation:** Erklärung der Ergebnisse

### 6.2 Beispiel-Interpretation

**Portfolio-Zusammensetzung:**
- 3 Strategien mit Gewichten 40%, 30%, 30%
- Alle aus demselben Sweep (können korreliert sein)

**Baseline-Metriken:**
- Portfolio Sharpe: 1.5 (vs. Einzel-Strategien: 1.8, 1.6, 1.4)
- Portfolio Max-Drawdown: -12% (vs. Einzel-Strategien: -15%, -18%, -10%)

**Interpretation:**
- Diversifikation reduziert Max-Drawdown (von -18% auf -12%) ✅
- Aber auch Sharpe leicht reduziert (von 1.8 auf 1.5) ⚠️
- Trade-off zwischen Risiko-Reduktion und Rendite

**Monte-Carlo:**
- Sharpe p50 = 1.5, p5 = 1.2, p95 = 1.8
- Enge Bänder = robustes Portfolio ✅

**Stress-Tests:**
- Delta Sharpe unter Crash: -0.3 (von 1.5 auf 1.2)
- Portfolio hält Stress stand ✅

---

## 7. Integration in Research-CLI

### 7.1 Subcommand `portfolio`

```bash
python scripts/research_cli.py portfolio \
    --sweep-name {sweep_name} \
    --config {config_path} \
    --top-n {n} \
    --portfolio-name {portfolio_name} \
    [--weights {w1} {w2} ...] \
    [--run-montecarlo] \
    [--mc-num-runs {runs}] \
    [--run-stress-tests] \
    [--stress-scenarios {scenarios}] \
    [--format {md|html|both}]
```

### 7.2 Pipeline-Integration (Zukünftig)

Die Pipeline könnte optional Portfolio-Robustness ausführen:

```bash
python scripts/research_cli.py pipeline \
    --sweep-name rsi_reversion_basic \
    --config config/config.toml \
    --top-n 5 \
    --run-portfolio-robustness \
    --portfolio-name rsi_portfolio_v1 \
    --weights 0.4 0.3 0.3
```

**Status:** Pipeline-Integration ist vorbereitet, aber aktuell nicht aktiv. Kann in späteren Phasen ergänzt werden (Pipeline v3).

---

## 8. Tests

### 8.1 Test-Coverage

- `tests/test_portfolio_robustness.py`: Unit-Tests für Portfolio-Robustness-Engine
- `tests/test_research_cli.py`: Integration-Tests für `portfolio`-Subcommand

### 8.2 Test-Ausführung

```bash
# Alle Portfolio-Robustness-Tests
pytest tests/test_portfolio_robustness.py -v

# Research-CLI-Tests (inkl. portfolio)
pytest tests/test_research_cli.py -v
```

---

## 9. Referenzen & Nächste Schritte

### 9.1 Verwandte Phasen

- **Phase 26:** Portfolio-Strategien & Portfolio-Manager
- **Phase 41:** Strategy-Sweeps & Research-Playground
- **Phase 42:** Top-N Promotion
- **Phase 44:** Walk-Forward-Testing
- **Phase 45:** Monte-Carlo-Robustness
- **Phase 46:** Stress-Tests & Crash-Szenarien

### 9.2 Nächste Schritte (Phase 48+)

- **Korrelations-Analyse:** Korrelations-Matrizen zwischen Portfolio-Komponenten
- **Regime-bewusste Portfolios:** Portfolio-Performance in verschiedenen Marktregimen
- **Multi-Asset-Portfolios:** Portfolios über verschiedene Assets hinweg
- **Dynamic Rebalancing:** Automatisches Rebalancing basierend auf Performance
- **Portfolio-Optimierung:** Automatische Gewichts-Optimierung (z.B. Sharpe-Maximierung)

---

## 10. Zusammenfassung

Phase 47 implementiert **Portfolio-Level Robustness & Stress-Testing** als Erweiterung der Single-Strategy-Robustness:

✅ **Implementiert:**
- Portfolio-Return-Synthese aus mehreren Strategien
- Portfolio-Level Monte-Carlo
- Portfolio-Level Stress-Tests
- Integration in Research-CLI
- Reports mit Portfolio-Metriken & Visualisierungen

🔮 **Zukünftig:**
- Korrelations-Analyse zwischen Komponenten
- Regime-bewusste Portfolio-Analysen
- Multi-Asset-Portfolios
- Portfolio-Optimierung

**Fazit:** Portfolio-Level Robustness hilft, die Robustheit von Multi-Strategy-Portfolios zu verstehen und Diversifikations-Effekte zu quantifizieren.
