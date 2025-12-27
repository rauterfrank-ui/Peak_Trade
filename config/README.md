# Peak_Trade Configuration Guide

**Stand:** 2025-12-27

Dieser Ordner enthält alle Konfigurationsdateien und Templates für Peak_Trade.

---

## 📋 Haupt-Konfigurationsdateien

### `config.toml`

**Zweck:** Haupt-Konfigurationstemplate für Peak_Trade  
**Verwendung:** Basis für alle Konfigurationen  
**Enthält:**
- Real-Market-Smokes Configuration
- Backtest-Parameter
- Risk-Parameter
- Position Sizing
- Regime-Konfiguration
- MLflow-Integration
- Und vieles mehr

**Note:** Root-Level `config.toml` ist eine "simplified" Version für OOP Strategy API.

### `config.test.toml`

**Zweck:** Konfiguration für Tests  
**Verwendung:** Wird von pytest verwendet  
**Enthält:** Test-spezifische Overrides

### `default.toml`

**Zweck:** Default-Werte  
**Verwendung:** Fallback-Werte wenn nicht in config.toml gesetzt

---

## 🔧 Feature-spezifische Configs

### Execution & Telemetry

- `execution_telemetry.toml` — Execution-Telemetrie-Konfiguration
- `telemetry_alerting.toml` — Alerting-Konfiguration

### Live Trading

- `live_policies.toml` — Live-Trading-Policies

### Promotion Loop

- `promotion_loop_config.toml` — Learning Promotion Loop Config

### R&D

- `r_and_d_presets.toml` — R&D Experiment Presets

### Regimes

- `regimes.toml` — Regime-Definitionen
- `macro_regimes/` — Macro-Regime-Konfiguration
  - `current.toml` — Aktuelles Regime
  - `schema.toml` — Regime-Schema

### Strategy Tiering

- `strategy_tiering.toml` — Strategy-Tier-Definitionen

### Test Health

- `test_health_profiles.toml` — Test-Health-Profile

---

## 📊 Risk Layer Configs

### Risk Gates (Examples)

- `risk_kill_switch_example.toml` — Kill-Switch-Konfiguration
- `risk_layer_v1_example.toml` — Risk-Layer-V1-Beispiel
- `risk_liquidity_gate_example.toml` — Liquidity-Gate-Beispiel
- `risk_liquidity_gate_paper.toml` — Liquidity-Gate für Paper-Trading
- `risk_stress_gate_example.toml` — Stress-Gate-Beispiel
- `risk_var_gate_example.toml` — VaR-Gate-Beispiel

**Note:** Diese sind Examples/Templates. Für Production: Kopieren und anpassen.

---

## 📁 Unterordner

### `portfolios/`

**Zweck:** Portfolio-Konfigurationen  
**Enthält:** 6 Portfolio-TOMLs  
**Verwendung:** Definiert Portfolio-Zusammenstellungen

### `portfolio_presets/`

**Zweck:** Portfolio-Presets  
**Enthält:** 3 Preset-TOMLs  
**Verwendung:** Vordefinierte Portfolio-Konfigurationen

### `portfolio_recipes.toml`

**Zweck:** Portfolio-Rezepte  
**Verwendung:** Kombinationen von Strategien

### `sweeps/`

**Zweck:** Parameter-Sweep-Konfigurationen  
**Enthält:** 15 Sweep-TOMLs  
**Verwendung:** Hyperparameter-Optimierung mit Optuna

### `scenarios/`

**Zweck:** Test-Szenarien  
**Enthält:** 3 Szenario-TOMLs  
**Verwendung:** Vordefinierte Test-Szenarien

### `scheduler/`

**Zweck:** Scheduler-Konfiguration  
**Enthält:** 1 Scheduler-TOML  
**Verwendung:** Scheduling von Tasks

### `markets/`

**Zweck:** Market-Konfigurationen  
**Enthält:** 2 Market-YAMLs  
**Verwendung:** Market-spezifische Parameter

### `market_outlook/`

**Zweck:** Market-Outlook-Konfiguration  
**Enthält:** 1 Outlook-YAML  
**Verwendung:** Market-Outlook-Parameter

---

## 🚀 Verwendung

### Basis-Konfiguration laden

```python
from src.core.peak_config import load_config

config = load_config("config/config.toml")
```

### Test-Konfiguration laden

```python
config = load_config("config/config.test.toml")
```

### Custom Config mit Overrides

```python
config = load_config("config/config.toml", overrides={
    "backtest.initial_cash": 50000.0,
    "risk.risk_per_trade": 0.02
})
```

---

## 🔒 Secrets & Sensitive Data

**WICHTIG:** Niemals Secrets in Config-Dateien committen!

**Für Secrets verwenden:**
- `.env` Datei (in .gitignore)
- Umgebungsvariablen
- `secrets.toml` (in .gitignore)

**Beispiel `.env`:**
```bash
KRAKEN_API_KEY=your_key_here
KRAKEN_API_SECRET=your_secret_here
```

---

## 📖 Siehe auch

- **Repo-Struktur:** `docs/architecture/REPO_STRUCTURE.md`
- **Config-Dokumentation:** `src/core/peak_config.py`
- **Risk-Layer-Docs:** `docs/risk/`
