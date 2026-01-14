# Phase 41B – Strategy Robustness & Tiering

## Implementation Status

Phase 41B ist **vollständig implementiert und getestet**:

- ✅ StrategyProfile-Datenmodell implementiert
- ✅ CLI-Command `strategy-profile` in research_cli.py
- ✅ Tiering-Config (`config/strategy_tiering.toml`) erstellt
- ✅ JSON/Markdown Export funktioniert
- ✅ Integration mit Monte-Carlo, Stress-Tests, Regime-Analyse
- ✅ Tests grün (34 Tests: 24 Unit + 10 CLI)

---

## Ziel & Motivation

Phase 41B erweitert das Research-Framework um ein standardisiertes **Strategy-Profiling-System**:

1. **Robustness-Profile**: Konsolidierte Ansicht aller Performance- und Robustness-Metriken für eine Strategie
2. **Tiering-System**: Klassifizierung von Strategien in `core`, `aux`, `legacy`
3. **Reproduzierbare Ausgaben**: JSON + Markdown für Dokumentation und Automatisierung

---

## Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                    research_cli.py                               │
│                   (strategy-profile Command)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               src/experiments/strategy_profiles.py               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ StrategyProfile  │  │ ProfileBuilder   │  │ TieringConfig  │ │
│  │ Datenmodell      │  │ (Builder-Pattern)│  │ (TOML Parser)  │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Monte-Carlo    │ │  Stress-Tests   │ │  Regime-Analyse │
│  (Optional)     │ │  (Optional)     │ │  (Optional)     │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                              │
                              ▼
              ┌───────────────┬───────────────┐
              ▼               ▼               ▼
        JSON Export      MD Export      Tiering-Info
```

---

## Komponenten

### 1. StrategyProfile Datenmodell

**Datei:** `src/experiments/strategy_profiles.py`

Zentrales Datenmodell für Strategy-Profile:

```python
from src.experiments.strategy_profiles import (
    StrategyProfile,
    StrategyProfileBuilder,
    Metadata,
    PerformanceMetrics,
    RobustnessMetrics,
    RegimeProfile,
    StrategyTieringInfo,
)
```

#### Struktur

```python
class StrategyProfile:
    metadata: Metadata           # Strategy-ID, Version, Zeitraum, Symbole
    performance: PerformanceMetrics  # Sharpe, CAGR, MaxDD, Trades, ...
    robustness: RobustnessMetrics    # MC p5/p50/p95, Stress Min/Max
    regimes: Optional[RegimeProfile] # Regime-Performance-Aufschlüsselung
    tiering: Optional[StrategyTieringInfo]  # Tier, Empfehlung
```

### 2. CLI-Command `strategy-profile`

**Datei:** `scripts/research_cli.py`

```bash
python scripts/research_cli.py strategy-profile \
  --strategy-id rsi_reversion \
  --output-format both \
  --with-regime \
  --with-montecarlo \
  --with-stress
```

#### Optionen

| Option | Beschreibung | Default |
|--------|--------------|---------|
| `--strategy-id` | Strategy-ID aus Registry (required) | - |
| `--config` | Pfad zur Config | `config/config.toml` |
| `--tiering-config` | Pfad zur Tiering-Config | `config/strategy_tiering.toml` |
| `--output-format` | `json`, `md`, `both` | `both` |
| `--output-dir` | Output-Verzeichnis | auto |
| `--with-regime` | Regime-Analyse durchführen | false |
| `--with-montecarlo` | Monte-Carlo-Analyse | false |
| `--with-stress` | Stress-Tests durchführen | false |
| `--mc-num-runs` | Anzahl Monte-Carlo-Runs | 100 |
| `--mc-method` | `simple` oder `block_bootstrap` | `simple` |
| `--stress-scenarios` | Stress-Szenarien | `single_crash_bar vol_spike` |
| `--stress-severity` | Stress-Severity | 0.2 |
| `--symbol` | Trading-Symbol | `BTC&#47;EUR` |
| `--timeframe` | Timeframe | `1h` |
| `--use-dummy-data` | Dummy-Daten verwenden | false |
| `--dummy-bars` | Anzahl Bars für Dummy | 500 |
| `--seed` | Random Seed | 42 |
| `--list-strategies` | Zeigt verfügbare Strategien | - |

### 3. Tiering-Config

**Datei:** `config/strategy_tiering.toml`

```toml
[strategy.rsi_reversion]
tier = "core"
recommended_config_id = "rsi_reversion_v1_core"
allow_live = false
notes = "Robust über mehrere Vol-Regime, gute Sharpe/MaxDD-Balance."

[strategy.breakout]
tier = "aux"
recommended_config_id = "breakout_v1_balanced"
allow_live = false
notes = "Trend-folgend, höhere Tail-Risiken."

[strategy.sma_crossover_legacy]
tier = "legacy"
notes = "Nur zu Vergleichszwecken."
```

#### Tiering-Kriterien

| Tier | Kriterien |
|------|-----------|
| **core** | Sharpe ≥ 1.5, MaxDD ≥ -15%, robust über Regime |
| **aux** | Sharpe ≥ 1.0, MaxDD ≥ -20%, spezifische Stärken |
| **legacy** | Sharpe < 1.0 oder MaxDD < -20% oder ersetzt |

---

## Workflow

### Schritt-für-Schritt Anleitung

**1. Virtual Environment aktivieren**

```bash
cd ~/Peak_Trade
source .venv/bin/activate
```

**2. Verfügbare Strategien anzeigen**

```bash
python scripts/research_cli.py strategy-profile \
  --strategy-id dummy \
  --list-strategies
```

**3. Einfaches Profil generieren**

```bash
python scripts/research_cli.py strategy-profile \
  --strategy-id rsi_reversion \
  --use-dummy-data \
  --output-format both
```

**4. Profil mit allen Analysen**

```bash
python scripts/research_cli.py strategy-profile \
  --strategy-id rsi_reversion \
  --use-dummy-data \
  --with-regime \
  --with-montecarlo \
  --mc-num-runs 100 \
  --with-stress \
  --stress-scenarios single_crash_bar vol_spike \
  --output-format both
```

**5. Ergebnisse finden**

- **JSON:** `reports&#47;strategy_profiles&#47;{strategy_id}_profile_v1.json`
- **Markdown:** `docs&#47;strategy_profiles&#47;{STRATEGY_ID}_PROFILE_v1.md`

---

## Output-Formate

### JSON-Output

```json
{
  "metadata": {
    "strategy_id": "rsi_reversion",
    "profile_version": "v1",
    "created_at": "2025-12-07T10:30:00",
    "data_range": "2024-01-01..2024-12-31",
    "symbols": ["BTC/EUR"],
    "timeframe": "1h"
  },
  "performance": {
    "sharpe": 1.52,
    "cagr": 0.18,
    "max_drawdown": -0.12,
    "volatility": 0.25,
    "winrate": 0.55,
    "trade_count": 150,
    "total_return": 0.28
  },
  "robustness": {
    "montecarlo_p5": 0.05,
    "montecarlo_p50": 0.18,
    "montecarlo_p95": 0.35,
    "num_montecarlo_runs": 100,
    "stress_min": -0.25,
    "stress_max": 0.08,
    "num_stress_scenarios": 2
  },
  "regimes": {
    "regimes": [
      {"name": "low_vol", "contribution_return": 0.15, "time_share": 0.4},
      {"name": "neutral", "contribution_return": 0.08, "time_share": 0.35},
      {"name": "high_vol", "contribution_return": 0.05, "time_share": 0.25}
    ],
    "dominant_regime": "low_vol",
    "weakest_regime": "high_vol"
  },
  "tiering": {
    "tier": "core",
    "reason": "Robust über mehrere Vol-Regime",
    "recommended_config_id": "rsi_reversion_v1_core",
    "allow_live": false
  }
}
```

### Markdown-Output

```markdown
# Strategy Profile - RSI_REVERSION

## 1. Meta
- **Strategy ID:** `rsi_reversion`
- **Version:** v1
- **Erstellt:** 2025-12-07T10:30:00
- **Daten:** 2024-01-01..2024-12-31
- **Universe:** BTC/EUR
- **Timeframe:** 1h

## 2. Performance (Baseline)
| Metrik | Wert |
|--------|------|
| Sharpe | 1.52 |
| CAGR | 18.00% |
| Max Drawdown | -12.00% |
...

## 3. Robustness
### Monte-Carlo-Analyse
- **Runs:** 100
- **Return p5/p50/p95:** 5.00% / 18.00% / 35.00%

### Stress-Tests
- **Szenarien:** 2
- **Min/Avg/Max Return:** -25.00% / -8.50% / 8.00%

## 4. Regime-Profil
| Regime | Contribution% | Time% | Effizienz |
|--------|---------------|-------|-----------|
| low_vol | 15.00% | 40.00% | 0.38 |
...

## 5. Tiering & Empfehlung
- **Tier:** **Core**
- **Empfohlene Config:** `rsi_reversion_v1_core`
...
```

---

## API-Referenz

### StrategyProfileBuilder

Builder-Pattern für flexible Profil-Erstellung:

```python
from src.experiments.strategy_profiles import StrategyProfileBuilder

builder = StrategyProfileBuilder("rsi_reversion", timeframe="1h")

# Datenbereich setzen
builder.set_data_range("2024-01-01", "2024-12-31")

# Performance aus Backtest-Stats
builder.set_performance_from_stats({
    "sharpe": 1.5,
    "cagr": 0.18,
    "max_drawdown": -0.12,
})

# Monte-Carlo-Ergebnisse
builder.set_montecarlo_results(
    p5=0.05, p50=0.18, p95=0.35, num_runs=100
)

# Stress-Test-Ergebnisse
builder.set_stress_results(
    min_return=-0.25, max_return=0.08, avg_return=-0.08, num_scenarios=2
)

# Regime hinzufügen
builder.add_regime("low_vol", contribution_return=0.15, time_share=0.4)
builder.add_regime("neutral", contribution_return=0.08, time_share=0.35)
builder.finalize_regimes()

# Tiering setzen
builder.set_tiering(tier="core", reason="Robust über alle Regime")

# Profil bauen
profile = builder.build()

# Exportieren
profile.to_json("reports/strategy_profiles/rsi_reversion_profile_v1.json")
profile.to_markdown("docs/strategy_profiles/RSI_REVERSION_PROFILE_v1.md")
```

### Tiering-Config laden

```python
from src.experiments.strategy_profiles import (
    load_tiering_config,
    get_tiering_for_strategy,
)

# Komplette Config laden
tiering = load_tiering_config("config/strategy_tiering.toml")

# Tiering für einzelne Strategie
info = get_tiering_for_strategy("rsi_reversion", tiering)
print(f"Tier: {info.tier}")
print(f"Empfehlung: {info.recommended_config_id}")
```

---

## Tests

Tests befinden sich in:

- `tests/test_strategy_profiles.py` – 24 Unit-Tests
- `tests/test_strategy_profile_cli.py` – 10 CLI-Tests

```bash
# Unit-Tests
pytest tests/test_strategy_profiles.py -v

# CLI-Tests
pytest tests/test_strategy_profile_cli.py -v

# Alle Tests
pytest tests/test_strategy_profiles.py tests/test_strategy_profile_cli.py -v
```

---

## Output-Verzeichnisse

| Typ | Pfad |
|-----|------|
| JSON-Profile | `reports&#47;strategy_profiles&#47;` |
| Markdown-Profile | `docs/strategy_profiles/` |
| Tiering-Config | `config/strategy_tiering.toml` |

---

## Integration mit anderen Phasen

Phase 41B integriert mit:

- **Phase 41 (Strategy-Sweeps):** Profile können aus Sweep-Ergebnissen abgeleitet werden
- **Phase 45 (Monte-Carlo):** Robustness-Metriken aus MC-Analyse
- **Phase 46 (Stress-Tests):** Stress-Metriken aus Szenario-Tests
- **Phase 48 (Live-Monitoring):** Profile als Baseline für Live-Vergleiche

---

## Bekannte Einschränkungen

1. **Regime-Analyse:** Aktuell vereinfachte Volatilitäts-basierte Regime-Detection
2. **Backtest-Integration:** Bei Dummy-Daten keine echte Strategy-Ausführung
3. **Live-Freigabe:** `allow_live` ist aktuell immer `false` (Safety-First)

---

## Nächste Schritte

Nach Phase 41B:

1. **Integration mit Sweep-Pipeline:** Automatische Profil-Generierung nach Sweep
2. **Batch-Profiling:** Alle Strategien auf einmal profilieren
3. **Vergleichs-Reports:** Mehrere Profile nebeneinander vergleichen
4. **Dashboard:** Interaktive Visualisierung der Profile

---

## Definition of Done

- [x] StrategyProfile-Datenmodell implementiert
- [x] JSON/Markdown Export funktioniert
- [x] CLI-Command `strategy-profile` verfügbar
- [x] Tiering-Config erstellt und integriert
- [x] Monte-Carlo-Integration
- [x] Stress-Test-Integration
- [x] Regime-Analyse-Integration
- [x] Unit-Tests (24 Tests)
- [x] CLI-Tests (10 Tests)
- [x] Dokumentation

---

## 7. Abschluss Phase 41B – Strategy Robustness & Tiering

Phase 41B ist vollständig implementiert und getestet. Der aktuelle Stand:

### Implementierung

**Neue Module & Dateien**

- `src/experiments/strategy_profiles.py`
  - Zentrales Datenmodell `StrategyProfile` mit:
    - `Metadata`
    - `PerformanceMetrics`
    - `RobustnessMetrics`
    - `RegimeProfile`
    - `StrategyTieringInfo`
  - `StrategyProfileBuilder` (Builder-Pattern) für flexible Profil-Erstellung
  - JSON-/Markdown-Exportfunktionen
  - Tiering-Config-Loader und Hilfsfunktionen

- `config/strategy_tiering.toml`
  - 14 Strategien klassifiziert (`core`, `aux`, `legacy`)
  - Empfohlene Config-IDs pro Strategie
  - Flags für Live-Eignung / Live-Trading

- `tests/test_strategy_profiles.py`
  - 24 Unit-Tests:
    - Aufbau und Validierung von `StrategyProfile`
    - JSON-Roundtrips
    - Tiering-Config-Parsing
    - Builder-/Export-Logik

- `tests/test_strategy_profile_cli.py`
  - 10 CLI-Tests:
    - Aufruf von `strategy-profile` über die CLI
    - Validierung der Output-Pfade (JSON/Markdown)
    - Fehlerfälle (unbekannte Strategie, ungültige Kombinationen)

- `docs/PHASE_41B_STRATEGY_ROBUSTNESS_AND_TIERING.md`
  - Vollständige Phase-Dokumentation:
    - Zielsetzung & Motivation
    - Datenmodell (`StrategyProfile`)
    - CLI-Workflow
    - Tiering-Kriterien
    - Beispielaufläufe und Output-Pfade

**Erweiterte Dateien**

- `scripts/research_cli.py`
  - Neuer Subcommand `strategy-profile` mit:
    - `--strategy-id` (Pflicht)
    - `--use-dummy-data` (schnelle Offline-Profil-Erstellung)
    - `--with-montecarlo` / `--mc-num-runs`
    - `--with-stress`
    - `--with-regime`
    - `--output-format` (`json`, `md`, `both`)

- `src/experiments/__init__.py`
  - Exports für `StrategyProfile` / `StrategyProfileBuilder` / Helper

### Beispiel-Aufruf

```bash
python scripts/research_cli.py strategy-profile \
  --strategy-id rsi_reversion \
  --use-dummy-data \
  --with-montecarlo --mc-num-runs 100 \
  --with-stress \
  --with-regime \
  --output-format both
```

**Output-Pfade**

* JSON: `reports&#47;strategy_profiles&#47;{strategy_id}_profile_v1.json`
* Markdown: `docs&#47;strategy_profiles&#47;{STRATEGY_ID}_PROFILE_v1.md`

### Tests & Qualität

* 34 neue Tests: **alle grün**
* 60 bestehende Tests im Research-/Strategy-Umfeld: **weiterhin grün**
* Keine Änderungen an Live-/Execution-Komponenten
* Strategy-Profiling läuft vollständig offline (kein Live-Datenbedarf)

### Kurz-Fazit (Quant-Lead)

* Jede Strategie kann jetzt über einen standardisierten Workflow profiliert werden.
* Tiering und empfohlene Config-IDs sind zentral versioniert (`config/strategy_tiering.toml`).
* Die erzeugten JSON-/Markdown-Profile bilden die Grundlage für:

  * spätere **Portfolio-Presets**,
  * **Regime-aware Allokation**,
  * und **Live-/Shadow-Gates** (nur `core`-Strategien mit grünem Profil).

---

*Phase 41B – Strategy Robustness & Tiering*
*Peak_Trade Framework*
