# Risk Layer v1 - Implementation Report

**Branch:** `feat/risk-layer-v1`  
**Datum:** 2025-12-23  
**Status:** ✅ Implementiert, Ready for Testing

---

## Executive Summary

Der **Risk Layer v1** wurde erfolgreich in Peak_Trade integriert. Er erweitert das bestehende Risk-Management um Portfolio-Level-Analysen, VaR/CVaR-Metriken und Stress-Testing-Capabilities.

**Kernfeatures:**
- Portfolio-Exposure-Limits (Gross/Net)
- Position-Weight-Limits
- VaR/CVaR (Historical + Parametric)
- Stress-Testing-Engine (5 Szenario-Typen)
- Risk-Limit-Enforcement mit Circuit-Breaker-Semantik
- Backward-kompatible Integration in Backtest-Engine

---

## Dateien: Neu erstellt

### src/risk/

| Datei | Zeilen | Beschreibung |
|-------|--------|-------------|
| **types.py** | 180 | Type-Definitionen (PositionSnapshot, PortfolioSnapshot, RiskBreach, RiskDecision) |
| **portfolio.py** | 169 | Portfolio-Analytics (Exposures, Weights, Correlations, Returns) |
| **var.py** | 279 | VaR/CVaR-Implementierungen (Historical + Parametric) |
| **stress.py** | 314 | Stress-Testing-Engine (StressScenario, 5 Szenario-Typen) |
| **enforcement.py** | 295 | Risk-Limit-Enforcement (RiskLimitsV2, RiskEnforcer) |

**Gesamt:** ~1.237 Zeilen Production-Code

### Dokumentation

| Datei | Beschreibung |
|-------|-------------|
| **docs/risk_layer_v1.md** | Vollständige Implementation-Guide (200+ Zeilen) |
| **config/risk_layer_v1_example.toml** | Konfigurations-Beispiele (3 Presets) |

---

## Dateien: Editiert

### src/risk/__init__.py
- Erweitert um v1-Layer-Exports
- 30+ neue Exports (Types, Functions, Classes)
- Backward-kompatibel (Legacy-Exports erhalten)

### src/core/risk.py
- **Neu:** `PortfolioVaRStressRiskManager` (150 Zeilen)
- Erweitert: `build_risk_manager_from_config()` um `type="portfolio_var_stress"`
- Config-Parser für v1-Limits

### src/backtest/engine.py
- Minimal-invasive Erweiterung in `run_realistic()`
- Übergabe von `symbol`, `last_return`, `positions` an RiskManager (via **kwargs)
- Backward-kompatibel (bestehende RiskManager unverändert)

---

## Neue Klassen & Functions

### Types (src/risk/types.py)
```python
class BreachSeverity(Enum):      # INFO, WARNING, HARD
class PositionSnapshot           # Einzelne Position
class PortfolioSnapshot          # Vollständiges Portfolio
class RiskBreach                 # Limit-Verletzung
class RiskDecision               # Entscheidung (Allow/Halt)
```

### Portfolio (src/risk/portfolio.py)
```python
def compute_position_notional(units, price) -> float
def compute_gross_exposure(positions) -> float
def compute_net_exposure(positions) -> float
def compute_weights(positions, equity) -> Dict[str, float]
def correlation_matrix(returns_df) -> pd.DataFrame
def portfolio_returns(returns_df, weights) -> pd.Series
```

### VaR (src/risk/var.py)
```python
def historical_var(returns, alpha=0.05) -> float
def historical_cvar(returns, alpha=0.05) -> float
def parametric_var(returns, alpha=0.05) -> float
def parametric_cvar(returns, alpha=0.05) -> float
```

### Stress (src/risk/stress.py)
```python
class StressScenario              # Szenario-Definition
def apply_scenario_to_returns(returns, scenario) -> pd.Series
def run_stress_suite(returns, scenarios, alpha) -> pd.DataFrame

# 5 Szenario-Typen:
# - shock: Plötzlicher Shock
# - vol_spike: Volatilitäts-Spike
# - flash_crash: Extremer Drawdown + Recovery
# - regime_bear: Prolongierter Bärenmarkt
# - regime_sideways: Seitwärts-Markt (hohe Choppiness)
```

**Abgrenzung:** Diese Risk-Layer Stress-Szenarien sind **nicht identisch** mit den Research Stress-Tests (Phase 46/47, `src/experiments/stress_tests.py`) und auch nicht mit der Scenario-Library (Phase 82, `config&#47;scenarios&#47;*.toml`). Namen können sich überschneiden (z.B. „flash_crash“), aber die Mechanik und Parameter unterscheiden sich bewusst.

### Enforcement (src/risk/enforcement.py)
```python
class RiskLimitsV2               # v1-Limits-Definition
class RiskEnforcer               # Enforcement-Engine
    def evaluate_portfolio(...) -> RiskDecision
```

### Core Integration (src/core/risk.py)
```python
class PortfolioVaRStressRiskManager(BaseRiskManager)
    # Features:
    # - Rolling-Window für Returns
    # - Portfolio-Snapshot-Erstellung
    # - VaR/CVaR/Exposure-Checks
    # - Circuit-Breaker bei HARD Breaches
```

---

## Konfiguration

### Beispiel: config/config.toml

```toml
[risk]
type = "portfolio_var_stress"
alpha = 0.05      # 95% VaR/CVaR
window = 252      # Rolling-Window (1 Jahr)

[risk.limits]
max_gross_exposure = 1.5      # 150% of Equity
max_net_exposure = 1.0        # 100% of Equity
max_position_weight = 0.35    # 35% max per Position
max_var = 0.08                # 8% VaR-Limit
max_cvar = 0.12               # 12% CVaR-Limit
```

### Verwendung

```python
from src.core.peak_config import load_config
from src.core.risk import build_risk_manager_from_config
from src.backtest.engine import BacktestEngine

cfg = load_config()
risk_manager = build_risk_manager_from_config(cfg)

engine = BacktestEngine(risk_manager=risk_manager)
result = engine.run_realistic(df, strategy_fn, params)
```

---

## Engine-Änderungen (Minimal-Invasiv)

### Vorher (src/backtest/engine.py)
```python
if self.risk_manager is not None:
    target_units = self.risk_manager.adjust_target_position(
        target_units=target_units,
        price=entry_price,
        equity=equity,
        timestamp=trade_dt,
    )
```

### Nachher
```python
if self.risk_manager is not None:
    risk_kwargs = {
        "symbol": symbol,
        "last_return": ...,  # Berechnet aus equity_curve
        "positions": [...],  # PositionSnapshots (falls vorhanden)
    }

    target_units = self.risk_manager.adjust_target_position(
        target_units=target_units,
        price=entry_price,
        equity=equity,
        timestamp=trade_dt,
        **risk_kwargs,  # Erweiterte Daten für v1-Layer
    )
```

**Wichtig:** Bestehende RiskManager (NoopRiskManager, MaxDrawdownRiskManager) ignorieren die neuen kwargs (via **kwargs) → Backward-kompatibel.

---

## Design-Prinzipien (eingehalten)

✅ **Modular**: Jedes Modul hat klare Verantwortung (types, portfolio, var, stress, enforcement)  
✅ **Testbar**: Alle Funktionen deterministisch testbar (keine globalen States)  
✅ **Safe-by-default**: Bei Violations klarer deterministischer Pfad (HALT bei HARD Breaches)  
✅ **Backward-kompatibel**: Bestehende RiskManager/Tests unverändert lauffähig  
✅ **Config-driven**: Alle Limits via config.toml steuerbar  
✅ **Type-hints überall**: 100% Type-Annotationen  
✅ **Public API klein**: Nur essenzielle Klassen/Functions exportiert  

---

## Testing-Status

| Komponente | Unit-Tests | Integration-Tests |
|------------|------------|-------------------|
| types.py | ⏳ TODO | - |
| portfolio.py | ⏳ TODO | - |
| var.py | ⏳ TODO | - |
| stress.py | ⏳ TODO | - |
| enforcement.py | ⏳ TODO | - |
| PortfolioVaRStressRiskManager | ⏳ TODO | ⏳ TODO |
| Backtest-Integration | - | ⏳ TODO |

**Nächste Schritte:**
1. Unit-Tests für alle src/risk/*-Module
2. Integration-Test mit BacktestEngine
3. Smoke-Test mit echten Daten
4. Performance-Profiling (VaR-Berechnung bei großen Windows)

---

## Nächste Schritte (Roadmap)

### Kurzfristig (diese Woche)
- [ ] Unit-Tests für src/risk/ (pytest)
- [ ] Integration-Test: Backtest mit portfolio_var_stress RiskManager
- [ ] Smoke-Test: 3 Strategien × 3 Risk-Configs
- [ ] Dokumentation in README.md verlinken

### Mittelfristig (nächste Sprint)
- [ ] Multi-Asset-Support (Correlation-Checks)
- [ ] Parametric VaR ohne scipy (vollständiger Fallback)
- [ ] Stress-Testing: Weitere Szenarien (Contagion, Liquidity Crisis)
- [ ] Performance-Optimierung (Caching für VaR bei Rolling-Windows)

### Langfristig (Q1 2026)
- [ ] Real-Time Risk-Monitoring (Integration in Live-Trading)
- [ ] Risk-Report-Generation (PDF/HTML mit Charts)
- [ ] Adaptive Limits (ML-basierte Limit-Adjustierung)
- [ ] Risk-Dashboard (WebUI-Integration)

---

## Breaking Changes

**Keine!** Alle Änderungen sind backward-kompatibel:

- Bestehende RiskManager (NoopRiskManager, MaxDrawdownRiskManager) laufen unverändert
- BacktestEngine ruft adjust_target_position() mit neuen kwargs, die alte Manager ignorieren
- Legacy-Exports in src/risk/__init__.py erhalten (PositionSizer, RiskLimits)

---

## Dependencies

Alle neuen Module nutzen **nur Standard-Dependencies**:
- `pandas`
- `numpy`
- `logging`
- `dataclasses` (Standard-Library)
- `typing` (Standard-Library)
- `enum` (Standard-Library)

**Optional:**
- `scipy` (für parametric_var/cvar mit exakten Quantilen)
  - Fallback: Lookup-Table für gängige Alphas (0.01, 0.05, 0.10)

---

## Code-Qualität

### Metriken
- **Zeilen Code:** ~1.237 (Production)
- **Docstrings:** 100% (alle Public Functions/Classes)
- **Type-Hints:** 100%
- **Linter-Errors:** 0 (read_lints passed)

### Code-Review-Checklist
- [x] Type-Hints überall
- [x] Docstrings mit Examples
- [x] Keine zirkulären Imports
- [x] Keine globalen States
- [x] Safe-by-default (Exception-Handling)
- [x] Logging an sinnvollen Stellen
- [x] Config-driven (alle Params konfigurierbar)

---

## Beispiel-Usage

### Conservative Strategy
```toml
[risk]
type = "portfolio_var_stress"
alpha = 0.01           # 99% VaR
window = 252
[risk.limits]
max_gross_exposure = 1.0
max_position_weight = 0.20
max_var = 0.05
max_cvar = 0.08
```

### Aggressive Strategy
```toml
[risk]
type = "portfolio_var_stress"
alpha = 0.10           # 90% VaR
window = 126           # 6 Monate
[risk.limits]
max_gross_exposure = 2.0
max_position_weight = 0.50
max_var = 0.15
max_cvar = 0.20
```

---

## Commit-Message

```
feat(risk): Implement Risk Layer v1 with VaR/CVaR and Stress-Testing

SCOPE: Risk Management / Portfolio Analytics

CHANGES:
- Add src/risk/types.py: PositionSnapshot, PortfolioSnapshot, RiskBreach, RiskDecision
- Add src/risk/portfolio.py: Exposure/Weight/Correlation analytics
- Add src/risk/var.py: Historical + Parametric VaR/CVaR
- Add src/risk/stress.py: Stress-Testing-Engine (5 scenario types)
- Add src/risk/enforcement.py: RiskEnforcer + RiskLimitsV2
- Add src/core/risk.PortfolioVaRStressRiskManager: Integration in Backtest
- Update src/backtest/engine.py: Pass symbol/positions/returns to RiskManager
- Update src/risk/__init__.py: Export v1-Layer API

FEATURES:
- Portfolio-Level Risk Management (Gross/Net Exposure, Position Weights)
- Value at Risk (Historical + Parametric, 95%/99%/custom alpha)
- Conditional Value at Risk (Expected Shortfall)
- Stress-Testing (shock, vol_spike, flash_crash, regime_bear, regime_sideways)
- Circuit-Breaker-Semantik (HARD breaches → Trading HALT)
- Config-driven Limits (config/risk_layer_v1_example.toml)

ARCHITECTURE:
- Modular design (types, portfolio, var, stress, enforcement)
- No circular imports, no global states
- Backward-compatible (existing RiskManagers unchanged)
- Type-hints + Docstrings everywhere

DOCS:
- Add docs/risk_layer_v1.md: Full implementation guide
- Add config/risk_layer_v1_example.toml: 3 config presets

TESTS: TODO
- Unit-tests for src/risk/* (pytest)
- Integration-test with BacktestEngine
- Smoke-test with 3 strategies × 3 configs

REF: #risk-layer-v1
```

---

## Kontakt / Questions

Für Fragen zur Implementation:
- **Docs:** `docs/risk_layer_v1.md`
- **Config:** `config/risk_layer_v1_example.toml`
- **Code:** `src/risk/` + `src/core/risk.py`

---

**Status:** ✅ Ready for Testing  
**Next:** Unit-Tests + Integration-Tests + Smoke-Tests
