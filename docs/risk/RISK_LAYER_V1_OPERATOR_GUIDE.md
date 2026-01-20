# Risk Layer v1 - Operator Guide

## Überblick

Der **Risk Layer v1** ermöglicht Portfolio-Level Risk Management in Peak_Trade Backtests mit:

- **Portfolio-Exposure-Limits**: Gross/Net Exposure als Fraction of Equity
- **Position-Weight-Limits**: Max Weight pro Asset
- **VaR/CVaR**: Value at Risk / Conditional Value at Risk
- **Stress-Testing**: Szenario-basierte Risk-Analyse
- **Circuit-Breaker**: Automatisches Trading-HALT bei Hard Breaches

---

## Quick Start

### 1. Aktivierung in config.toml

```toml
[risk]
type = "portfolio_var_stress"
alpha = 0.05      # 95% VaR/CVaR (0.05 = 5% Tail)
window = 252      # Rolling-Window (252 = ~1 Trading Year)

[risk.limits]
max_gross_exposure = 1.5      # Max 150% of Equity
max_position_weight = 0.35    # Max 35% per Position
max_var = 0.08                # Max 8% VaR
max_cvar = 0.12               # Max 12% CVaR
```

### 2. Verwendung im Backtest

```python
from src.core.peak_config import load_config
from src.core.risk import build_risk_manager_from_config
from src.backtest.engine import BacktestEngine

# Load Config mit Risk-Limits
cfg = load_config()
risk_manager = build_risk_manager_from_config(cfg)

# Backtest-Engine mit RiskManager
engine = BacktestEngine(risk_manager=risk_manager)

# Run Backtest
result = engine.run_realistic(df, strategy_fn, params)

# Check Results
print(f"Sharpe: {result.stats['sharpe']:.2f}")
print(f"Max DD: {result.stats['max_drawdown']:.2%}")
```

---

## Konzepte & Konventionen

### Returns

**Konvention**: Returns sind period returns als Dezimalzahl
- `0.02` = +2% Gewinn
- `-0.03` = -3% Verlust

**Berechnung**: `return = (price_t / price_{t-1}) - 1`

### Alpha (Konfidenzniveau)

**Definition**: Alpha ist das Tail-Probability-Level für VaR/CVaR

| Alpha | Bedeutung | Interpretation |
|-------|-----------|----------------|
| 0.01  | 99% VaR   | Extremer Tail (1% Worst-Case) |
| 0.05  | 95% VaR   | Standard (5% Worst-Case) |
| 0.10  | 90% VaR   | Weniger konservativ (10% Worst-Case) |

**Wahl**:
- **Alpha=0.01** (99% VaR): Sehr konservativ, für risk-averse Strategien
- **Alpha=0.05** (95% VaR): Standard, gute Balance
- **Alpha=0.10** (90% VaR): Aggressiv, für risk-tolerant Strategien

### VaR vs CVaR

**VaR (Value at Risk)**:
- "Was ist der maximale Verlust im Alpha-Tail?"
- Quantil der Return-Verteilung
- Beispiel: VaR(95%) = 0.08 → "In 5% der Fälle verliere ich bis zu 8%"

**CVaR (Conditional Value at Risk / Expected Shortfall)**:
- "Was ist der durchschnittliche Verlust im Alpha-Tail?"
- Mittlerer Loss aller Returns <= VaR
- CVaR >= VaR (immer)
- Beispiel: CVaR(95%) = 0.12 → "Wenn ich im 5%-Tail lande, verliere ich durchschnittlich 12%"

**Interpretation**:
- VaR: Worst-Case-Schwelle
- CVaR: Durchschnitt im Worst-Case (konservativere Metrik)

### Window (Rolling-Window)

**Definition**: Anzahl Returns für VaR/CVaR-Berechnung

| Window | Bedeutung | Use Case |
|--------|-----------|----------|
| 30     | 1 Monat   | Kurzfristig, reagiert schnell auf neue Daten |
| 126    | 6 Monate  | Mittelfristig, Balance zwischen Aktualität und Stabilität |
| 252    | 1 Jahr    | Langfristig, stabile Schätzung |

**Wahl**:
- **Klein (30-60)**: Schnelle Reaktion auf Regime-Wechsel, aber volatilere VaR-Schätzung
- **Mittel (126-180)**: Balance
- **Groß (252+)**: Stabile Schätzung, aber langsame Anpassung

**Warmup**: VaR/CVaR-Checks sind erst nach `window` Tagen aktiv!

---

## Config-Beispiele

### Conservative (Low Risk)

```toml
[risk]
type = "portfolio_var_stress"
alpha = 0.01           # 99% VaR (sehr konservativ)
window = 252           # 1 Jahr

[risk.limits]
max_gross_exposure = 1.0    # Kein Leverage
max_position_weight = 0.20  # Max 20% pro Position
max_var = 0.05              # Max 5% VaR
max_cvar = 0.08             # Max 8% CVaR
```

**Use Case**: Risk-averse Strategien, lange Hold-Perioden

### Balanced (Standard)

```toml
[risk]
type = "portfolio_var_stress"
alpha = 0.05           # 95% VaR
window = 126           # 6 Monate

[risk.limits]
max_gross_exposure = 1.5    # 50% Leverage erlaubt
max_position_weight = 0.35  # Max 35% pro Position
max_var = 0.08              # Max 8% VaR
max_cvar = 0.12             # Max 12% CVaR
```

**Use Case**: Standard-Strategien, mittelfristig

### Aggressive (High Risk)

```toml
[risk]
type = "portfolio_var_stress"
alpha = 0.10           # 90% VaR (weniger konservativ)
window = 30            # 1 Monat

[risk.limits]
max_gross_exposure = 2.0    # 100% Leverage erlaubt
max_position_weight = 0.50  # Max 50% pro Position
max_var = 0.15              # Max 15% VaR
max_cvar = 0.20             # Max 20% CVaR
```

**Use Case**: High-Frequency, kurzfristige Strategien

### Nur Exposure-Limits (ohne VaR)

```toml
[risk]
type = "portfolio_var_stress"
alpha = 0.05
window = 252

[risk.limits]
max_gross_exposure = 1.5
max_position_weight = 0.35
# max_var nicht gesetzt -> wird nicht geprüft
# max_cvar nicht gesetzt -> wird nicht geprüft
```

**Use Case**: Wenn VaR zu restriktiv ist oder Window zu kurz

---

## Limit-Typen

### Exposure-Limits

**max_gross_exposure** (Fraction of Equity)
```
Gross Exposure = Sum(|notional|) / Equity
```
- Misst Gesamtexposure (long + short)
- 1.0 = 100% of Equity (kein Leverage)
- 1.5 = 150% of Equity (50% Leverage)
- 2.0 = 200% of Equity (100% Leverage)

**max_net_exposure** (Fraction of Equity)
```
Net Exposure = Abs(long_notional - short_notional) / Equity
```
- Misst direktionale Exposure
- 0.0 = Market-neutral
- 1.0 = Vollständig long oder short

**Beispiel**:
- Equity: 100.000 €
- Position 1: 50.000 € long BTC
- Position 2: 30.000 € short ETH
- Gross Exposure: (50.000 + 30.000) / 100.000 = 0.8 (80%)
- Net Exposure: (50.000 - 30.000) / 100.000 = 0.2 (20% net long)

### Position-Weight-Limits

**max_position_weight** (Fraction of Equity)
```
Position Weight = |notional| / Equity
```
- Misst Konzentration pro Asset
- 0.35 = Max 35% of Equity in einem Asset

**Beispiel**:
- Equity: 100.000 €
- Position BTC: 40.000 €
- Weight BTC: 40.000 / 100.000 = 0.40 (40%)
- Bei `max_position_weight = 0.35` → BREACH!

### VaR/CVaR-Limits

**max_var / max_cvar** (Fraction of Equity)
- VaR/CVaR werden als Fraction of Equity interpretiert
- 0.08 = Max 8% VaR/CVaR

**Beispiel**:
- Returns: [-0.01, -0.05, -0.10, 0.02, -0.03, ...]
- VaR(95%) = 0.09 (9%)
- Bei `max_var = 0.08` → BREACH!

---

## Circuit-Breaker-Semantik

### Breach-Severities

| Severity | Bedeutung | Action |
|----------|-----------|--------|
| INFO     | Informativ | Trading läuft weiter |
| WARNING  | Warnung | Trading läuft weiter, Log-Eintrag |
| **HARD** | **Hard Limit** | **Trading HALT** |

**Alle aktuellen Limits sind HARD Breaches!**

### Trading HALT

Bei HARD Breach:
1. RiskManager setzt `trading_stopped = True`
2. `adjust_target_position()` returned `0.0` (blockiert Trade)
3. Backtest läuft weiter, aber keine neuen Positionen
4. Log-Eintrag mit Breach-Details

**Persistenz**: Einmal gestoppt, bleibt gestoppt (kein Auto-Recovery)

---

## Troubleshooting

### "VaR immer 0.0"

**Problem**: VaR/CVaR sind immer 0.0 im Backtest

**Ursachen**:
1. **Window Warmup**: VaR-Check ist erst nach `window` Bars aktiv
   - Lösung: Warte `window` Bars oder reduziere `window`

2. **Nur positive Returns**: Bei nur Gewinnen ist VaR = 0
   - Lösung: Normal, kein Problem

3. **Leere Returns-History**: RiskManager bekommt keine Returns
   - Lösung: Check `last_return` in Engine-Integration

### "Trading sofort gestoppt"

**Problem**: Erster Trade wird sofort blockiert

**Ursachen**:
1. **Position-Weight zu klein**: `max_position_weight` zu restriktiv
   - Lösung: Erhöhe `max_position_weight` (z.B. 0.35)

2. **Gross-Exposure zu klein**: `max_gross_exposure` < 1.0
   - Lösung: Erhöhe auf mindestens 1.0 (= 100% of Equity)

3. **VaR-Limit zu niedrig**: `max_var` unrealistisch niedrig
   - Lösung: Erhöhe auf mindestens 0.05 (5%)

### "scipy not available" Warning

**Problem**: Parametric VaR nutzt Fallback-Quantile

**Lösung**:
- Optional: `pip install scipy` für exakte Normal-Quantile
- Oder: Nutze `historical_var/cvar` (kein scipy nötig)
- Fallback funktioniert für alpha=0.01, 0.05, 0.10

### "NaN in Returns"

**Problem**: NaNs in Returns-Series

**Lösung**: Alle Risk-Funktionen handhaben NaNs via `dropna()`
- Automatisch ignoriert
- Falls zu viele NaNs: Check Datenqualität

---

## Monitoring & Debugging

### Check RiskManager-State

```python
# Nach Backtest
if hasattr(engine.risk_manager, 'trading_stopped'):
    print(f"Trading stopped: {engine.risk_manager.trading_stopped}")
    print(f"Breach count: {engine.risk_manager.breach_count}")
    print(f"Returns history size: {len(engine.risk_manager.returns_history)}")
```

### Log-Level erhöhen

```python
import logging
logging.getLogger("src.core.risk").setLevel(logging.INFO)
logging.getLogger("src.risk.enforcement").setLevel(logging.INFO)
```

→ Zeigt Breaches und Risk-Decisions

### Manual VaR-Check

```python
from src.risk import historical_var, historical_cvar
import pandas as pd

# Berechne Returns aus Equity-Curve
equity_curve = result.equity_curve
returns = pd.Series(equity_curve).pct_change().dropna()

var_95 = historical_var(returns, alpha=0.05)
cvar_95 = historical_cvar(returns, alpha=0.05)

print(f"VaR(95%): {var_95:.2%}")
print(f"CVaR(95%): {cvar_95:.2%}")
```

---

## Best Practices

### 1. Start Conservative

Beginne mit konservativen Limits und lockere graduell:
```toml
[risk.limits]
max_gross_exposure = 1.2    # Start mit wenig Leverage
max_position_weight = 0.30  # Start mit niedriger Konzentration
max_var = 0.10              # Start mit höherem VaR-Limit
```

### 2. Window an Strategie anpassen

- **High-Frequency**: `window = 30-60`
- **Intraday/Swing**: `window = 126`
- **Position/Long-Term**: `window = 252`

### 3. Alpha an Risk-Tolerance anpassen

- **Risk-averse**: `alpha = 0.01` (99% VaR)
- **Standard**: `alpha = 0.05` (95% VaR)
- **Risk-tolerant**: `alpha = 0.10` (90% VaR)

### 4. Limits schrittweise aktivieren

Test-Workflow:
1. **Nur Exposure-Limits** (ohne VaR)
2. **+ VaR-Limits** (großzügig)
3. **Finales Tuning** (verschärfen)

### 5. Backtests mit/ohne Limits vergleichen

```bash
# Ohne Limits
python scripts/run_backtest.py --config config/no_risk.toml

# Mit Limits
python scripts/run_backtest.py --config config/risk_v1.toml

# Vergleiche Sharpe/DD
```

---

## Advanced: Stress-Testing (Optional)

### Stress-Report generieren

```bash
python scripts/run_risk_stress_report.py --config config/config.toml --output reports/stress_report.csv
```

→ Erzeugt CSV mit VaR/CVaR für verschiedene Stress-Szenarien

### Szenarien

| Szenario | Beschreibung | Params |
|----------|-------------|--------|
| shock | Plötzlicher Shock | `shock_pct=-0.20, days=5` |
| vol_spike | Volatilitäts-Spike | `multiplier=3.0` |
| flash_crash | Extremer Drawdown + Recovery | `crash_pct=-0.30, recovery_days=10` |
| regime_bear | Prolongierter Bärenmarkt | `drift_pct=-0.02, duration_days=60` |
| regime_sideways | Seitwärts-Markt | `chop_factor=2.0, duration_days=30` |

---

## Migration von Legacy Risk-Limits

### Vorher (src/risk/limits.py)

```python
from src.risk import RiskLimits, RiskLimitsConfig

config = RiskLimitsConfig(
    max_drawdown_pct=20.0,
    daily_loss_limit_pct=5.0,
    max_position_pct=10.0,
)
limits = RiskLimits(config)
```

### Nachher (Risk Layer v1)

```toml
[risk]
type = "portfolio_var_stress"
alpha = 0.05
window = 252

[risk.limits]
max_position_weight = 0.10    # = max_position_pct / 100
max_var = 0.08                # Neu: VaR-basiertes DD-Management
```

**Unterschiede**:
- Legacy: Daily-Loss-Limit (heute)
- v1: VaR/CVaR (rolling window, historisch)
- Legacy: Absolute Drawdown
- v1: VaR-basiert (wahrscheinlichkeitsbasiert)

**Beide können parallel laufen!** Legacy-Limits sind weiterhin verfügbar.

---

## References

- **Implementation Guide**: `docs/risk_layer_v1.md`
- **Config Examples**: `config/risk_layer_v1_example.toml`
- **Tests**: `tests/risk/`
- **Source**: `src/risk/` + `src/core/risk.py`

---

## Support

Bei Fragen:
1. Check `docs/risk_layer_v1.md` (Technical Guide)
2. Check Tests in `tests/risk/` (Usage Examples)
3. Run `pytest tests&#47;risk&#47; -v` (Smoke-Tests)
