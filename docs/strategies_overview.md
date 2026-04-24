# Peak_Trade Strategien-Übersicht (historische Beispielauswahl)

## Authority and Coverage Note

This document is a historical and example-oriented strategy overview. It is not the complete current strategy registry, not a live-readiness source, not a Master V2 authority source, and not a Double Play authority source.

For current strategy-authority interpretation, use the dedicated governance and reconciliation documents:

- [`STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md`](ops/specs/STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md)
- [`STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md`](ops/specs/STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md)
- [`STRATEGY_REGISTRY_TIERING_MV2_RECONCILIATION_TABLE_V0.md`](ops/specs/STRATEGY_REGISTRY_TIERING_MV2_RECONCILIATION_TABLE_V0.md)
- [`STRATEGY_REGISTRY_SOURCE_COMMENT_DISCORD_NON_AUTHORITY_NOTE_V0.md`](ops/specs/STRATEGY_REGISTRY_SOURCE_COMMENT_DISCORD_NON_AUTHORITY_NOTE_V0.md)

The strategy registry, tiering configuration, and Master V2 documentation remain separate authority surfaces. A strategy appearing in this overview does not imply production readiness, live readiness, promotion approval, or Double Play selection authority.

Known follow-up audit topics include historical naming and epoch drift around ECM/Armstrong-style cycle references and TOML-only surfaces such as `vol_breakout`. Those topics are not resolved by this overview note.

## 🎯 Beispielhafte Darstellung: sechs Strategien

---

## 1️⃣ **MA Crossover** (Moving Average Crossover)

**Typ:** Trend-Following  
**Datei:** `src/strategies/ma_crossover.py`

### Konzept
- **Entry:** Fast MA kreuzt Slow MA von unten nach oben
- **Exit:** Fast MA kreuzt Slow MA von oben nach unten

### Parameter
```toml
[strategy.ma_crossover]
fast_period = 10
slow_period = 30
stop_pct = 0.02
```

### Eigenschaften
- ✅ Einfach und robust
- ✅ Gut in starken Trends
- ❌ Viele Fehlsignale in Seitwärtsmärkten

---

## 2️⃣ **Momentum**

**Typ:** Trend-Following  
**Datei:** `src/strategies/momentum.py`

### Konzept
- **Momentum** = (Close heute / Close vor N Tagen) - 1
- **Entry:** Momentum > entry_threshold (z.B. 2%)
- **Exit:** Momentum < exit_threshold (z.B. -1%)

### Parameter
```toml
[strategy.momentum_1h]
lookback_period = 20
entry_threshold = 0.02
exit_threshold = -0.01
stop_pct = 0.025
```

### Eigenschaften
- ✅ Erfasst starke Trends früh
- ✅ Flexibel über Thresholds
- ❌ Sensitiv auf Lookback-Periode

---

## 3️⃣ **MACD** (Moving Average Convergence Divergence)

**Typ:** Trend + Momentum  
**Datei:** `src/strategies/macd.py`

### Konzept
- **MACD Line** = EMA(12) - EMA(26)
- **Signal Line** = EMA(9) der MACD Line
- **Entry:** MACD kreuzt Signal von unten (Bullish)
- **Exit:** MACD kreuzt Signal von oben (Bearish)

### Parameter
```toml
[strategy.macd]
fast_ema = 12
slow_ema = 26
signal_ema = 9
stop_pct = 0.025
```

### Eigenschaften
- ✅ Kombiniert Trend + Momentum
- ✅ Weniger Fehlsignale als MA Crossover
- ✅ Histogram zeigt Stärke

---

## 4️⃣ **RSI** (Relative Strength Index)

**Typ:** Mean-Reversion  
**Datei:** `src/strategies/rsi.py`

### Konzept
- **RSI** = Relative Strength (0-100)
- **Entry:** RSI kreuzt oversold-Level (z.B. 30) von unten
- **Exit:** RSI kreuzt overbought-Level (z.B. 70) von unten

### Parameter
```toml
[strategy.rsi_strategy]
rsi_period = 14
oversold = 30
overbought = 70
stop_pct = 0.02
```

### Eigenschaften
- ✅ Exzellent in Range-Märkten
- ✅ Identifiziert Extreme
- ❌ Kann in Trends "overextended" bleiben

---

## 5️⃣ **Bollinger Bands**

**Typ:** Mean-Reversion + Volatilität  
**Datei:** `src/strategies/bollinger.py`

### Konzept
- **Middle Band** = SMA(20)
- **Upper/Lower** = Middle ± (2 × Std)
- **Entry:** Preis berührt untere Band (überverkauft)
- **Exit:** Preis erreicht Mittel-Band

### Parameter
```toml
[strategy.bollinger_bands]
bb_period = 20
bb_std = 2.0
entry_threshold = 0.95
exit_threshold = 0.50
stop_pct = 0.03
```

### Eigenschaften
- ✅ Passt sich an Volatilität an
- ✅ Gut für Mean-Reversion
- ✅ Bandwidth zeigt Squeeze/Expansion

---

## 6️⃣ **ECM** (Economic Confidence Model)

**Typ:** Cycle-Based (Armstrong)  
**Datei:** `src/strategies/ecm.py`

### Konzept
- **Zyklus:** 8.6 Jahre = Pi × 1000 Tage = 3141 Tage
- **Turning Points:** 0%, 25%, 50%, 75%, 100% im Zyklus
- **Entry:** Hohe Confidence + Bullish Trend
- **Exit:** Niedrige Confidence ODER Bearish Trend

### Parameter
```toml
[strategy.ecm_cycle]
ecm_cycle_days = 3141
ecm_confidence_threshold = 0.6
ecm_reference_date = "2020-01-18"
lookback_bars = 100
stop_pct = 0.03
```

### Eigenschaften
- ✅ Basiert auf Martin Armstrong's ECM-Theorie
- ✅ Pi-basierte Zyklen
- ✅ Langfrist-Perspektive
- ❌ Erfordert korrekte Referenz-Dates

---

## 📊 Portfolio-Kombination

### Empfohlene Allocation

**Balanced Portfolio (Equal Weight):**
```
MA Crossover:     16.7%
Momentum:         16.7%
MACD:             16.7%
RSI:              16.7%
Bollinger Bands:  16.7%
ECM:              16.7%
```

**Trend-Focused:**
```
MA Crossover:     25%
Momentum:         25%
MACD:             25%
RSI:              12.5%
Bollinger:        12.5%
```

**Mean-Reversion-Focused:**
```
RSI:              30%
Bollinger:        30%
MA Crossover:     15%
Momentum:         15%
MACD:             10%
```

---

## 🧪 Testing

```bash
# Einzelne Strategie
python3 scripts/run_momentum_realistic.py

# Portfolio mit allen 6
python3 scripts/run_full_portfolio.py

# Unit-Tests
python3 -m pytest tests/test_new_strategies.py -v
```

---

## 📈 Performance-Charakteristiken

| Strategie | Typ | Beste Märkte | Trades/Jahr | Avg Hold |
|-----------|-----|--------------|-------------|----------|
| MA Crossover | Trend | Trending | 10-20 | Wochen |
| Momentum | Trend | Trending | 15-30 | Tage |
| MACD | Trend | Trending | 12-25 | Wochen |
| RSI | Mean-Rev | Ranging | 30-50 | Tage |
| Bollinger | Mean-Rev | Ranging | 25-40 | Tage |
| ECM | Cycle | Alle | 5-10 | Monate |

---

**Built with ❤️ and strict risk management**
