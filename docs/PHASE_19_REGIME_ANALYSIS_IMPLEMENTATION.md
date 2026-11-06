# Phase 19 – Regime-Analyse & Robustheits-Tools: Implementation Summary

## Übersicht

Phase 19 implementiert Regime-Analyse-Funktionalität für Peak_Trade. Das Modul ermöglicht die Erkennung von Marktregimes (Volatilität + Trend) und die Analyse der Strategie-Performance in unterschiedlichen Marktphasen.

**Scope: Rein analytisch** – keine Änderungen an Order-, Execution- oder Safety-Komponenten.

---

## Neue Dateien

| Pfad | Beschreibung |
|------|--------------|
| `config/regimes.toml` | Konfiguration für Regime-Parameter (Volatilitäts-Schwellen, Trend-MAs) |
| `src/analytics/regimes.py` | Haupt-Modul mit Regime-Erkennung und Performance-Analyse |
| `scripts/analyze_regimes.py` | CLI-Tool für Regime-Analyse (single, strategy, sweep) |
| `docs/REGIME_ANALYSIS.md` | Dokumentation mit Quickstart, Beispielen und Best Practices |
| `tests/test_regimes.py` | 35 Tests für Config-Laden, Regime-Erkennung, Analyse, CLI |

---

## Geänderte Dateien

| Pfad | Änderung |
|------|----------|
| `src/analytics/__init__.py` | Export der neuen Regime-Funktionen hinzugefügt |

---

## CLI-Beispiele

### Einzelnes Experiment analysieren
```bash
python3 scripts/analyze_regimes.py single \
    --id abc12345-1234-5678-abcd-1234567890ab \
    --verbose
```

### Strategie über mehrere Backtests analysieren
```bash
python3 scripts/analyze_regimes.py strategy \
    --strategy ma_crossover \
    --run-type backtest \
    --limit 50
```

### Sweep-Robustheits-Check
```bash
python3 scripts/analyze_regimes.py sweep \
    --sweep-name ma_crossover_opt_v1 \
    --metric sharpe \
    --top-n 20
```

### Mit Export
```bash
python3 scripts/analyze_regimes.py strategy \
    --strategy rsi_reversion \
    --export-csv out/regime_analysis.csv \
    --export-json out/regime_analysis.json
```

---

## Teststatus

| Metrik | Wert |
|--------|------|
| Neue Tests (`tests/test_regimes.py`) | 35 |
| Alle Tests bestanden | 35/35 ✓ |
| Gesamtzahl Tests (Projekt) | 609 (606 passed, 3 pre-existing failures) |

### Pre-existing Failures (nicht von Phase 19)
- `test_ecm_config`: Fehlende `ecm_cycle` Strategie in config.toml
- `test_portfolio_backtest`: Settings-Subscript-Issue
- `test_get_strategy_cfg_success`: Feld-Name-Mismatch (`fast_period` vs `fast_window`)

---

## Scope-Statement

**Phase 19 ist rein analytisch:**

✓ **Erlaubt:**
- Lesen aus Experiment-Registry
- Lesen von Backtest-Ergebnissen
- Lesen von Preis-/Equity-Daten
- Berechnen von Regime-Labels und Statistiken
- Ausgabe von Reports (Terminal, CSV, JSON)

✗ **Nicht erlaubt / unberührt:**
- `TradingEnvironment` – keine Änderungen
- `SafetyGuard` – keine Änderungen
- Live-/Testnet-Executor – nicht aktiviert
- Order-/Execution-Pfade – nicht modifiziert

---

## Features im Detail

### Regime-Erkennung

**Volatilitäts-Regimes:**
- `low_vol`: Annualisierte Volatilität < 30%
- `mid_vol`: 30% ≤ Volatilität ≤ 60%
- `high_vol`: Volatilität > 60%

**Trend-Regimes:**
- `uptrend`: MA_short > MA_long + 2%
- `sideways`: MA_short ≈ MA_long
- `downtrend`: MA_short < MA_long - 2%

**Kombiniert:** 9 mögliche Regimes (z.B. `low_vol_uptrend`, `high_vol_downtrend`)

### Performance-Analyse

Pro Regime werden berechnet:
- Weight (Anteil an Gesamtzeit)
- Return Mean/Sum/Std
- Sharpe Ratio (annualisiert)
- Max Drawdown (lokal)
- Total Return

### Sweep-Robustheit

- Robustness Score: Anteil Runs mit positivem Sharpe über alle Regimes
- Best/Worst Regime: Konsistenteste Über-/Unterperformance
- Regime-Konsistenz: Wie oft ist Sharpe > 0 pro Regime?

---

## API-Übersicht

```python
from src.analytics.regimes import (
    # Dataclasses
    RegimeConfig,
    RegimeStats,
    RegimeAnalysisResult,
    SweepRobustnessResult,

    # Funktionen
    load_regime_config,       # Config aus TOML laden
    detect_regimes,           # Regimes in Preisdaten erkennen
    analyze_regimes_from_equity,  # Performance pro Regime
    analyze_experiment_regimes,   # High-Level-Analyse
    compute_sweep_robustness,     # Sweep-Robustheits-Metriken

    # Utilities
    format_regime_stats_table,
    create_regime_summary_df,
)
```

---

## Datum

Implementation abgeschlossen: 2025-12-04
