# Peak_Trade - Neue Features (Dezember 2024)

## Übersicht

Diese Dokumentation beschreibt die neu implementierten Features:

1. **Erweiterter Risk-Layer** (Position Sizing + Portfolio Limits)
2. **TOML-basiertes Config-System** (bereits vorhanden, erweitert)
3. **Kraken Data Pipeline** (nahtlose Integration mit Data-Layer)

---

## 1. Risk-Layer

### Position Sizing

**Dateien:**
- `src/risk/position_sizer.py` - Erweiterte Position-Sizing-Methoden
- `src/risk/limits.py` - Portfolio Risk Limits

**Features:**

#### Fixed Fractional Position Sizing (Standard)
```python
from src.risk import PositionSizer, PositionSizerConfig

# Konfiguration
config = PositionSizerConfig(
    method="fixed_fractional",
    risk_pct=1.0,           # 1% Risiko pro Trade
    max_position_pct=25.0   # Max. 25% des Kapitals pro Trade
)

sizer = PositionSizer(config)

# Position berechnen
capital = 10_000
stop_distance = 1_000  # Entry - Stop in Quote-Währung

size = sizer.size_position(capital, stop_distance)
print(f"Position Size: {size:.4f} BTC")
```

#### Kelly Criterion Position Sizing
```python
config = PositionSizerConfig(
    method="kelly",
    max_position_pct=25.0,
    kelly_scaling=0.5  # Konservativ (empfohlen)
)

sizer = PositionSizer(config)

# Benötigt historische Performance-Daten
size = sizer.size_position(
    capital=10_000,
    stop_distance=1_000,
    win_rate=0.55,      # 55% Win-Rate
    avg_win=200,        # Durchschnittlicher Gewinn
    avg_loss=100        # Durchschnittlicher Verlust
)
```

**Wichtig:** Kelly-Methode sollte nur mit ausreichend Trade-Historie verwendet werden (mindestens 30-50 Trades).

---

### Portfolio Risk Limits

**Features:**
- Daily Loss Limit (Kill-Switch)
- Max Drawdown Limit
- Max parallele Positionen
- Max Total Exposure

**Verwendung:**

```python
from src.risk import RiskLimitChecker, RiskLimitsConfig, PortfolioState
from datetime import date

# Konfiguration (aus config.toml)
config = RiskLimitsConfig(
    max_daily_loss=0.03,      # 3% Tagesverlust
    max_drawdown=0.20,        # 20% Portfolio-Drawdown
    max_positions=2,          # Max. 2 parallele Positionen
    max_total_exposure=0.75   # Max. 75% investiert
)

checker = RiskLimitChecker(config)

# Portfolio-Status
state = PortfolioState(
    equity=10_000,
    peak_equity=10_500,
    daily_start_equity=10_200,
    open_positions=1,
    total_exposure=2_000,
    current_date=date.today()
)

# Vor Trade-Eröffnung prüfen
proposed_position_value = 2_500
result = checker.check_limits(state, proposed_position_value)

if result.rejected:
    print(f"Trade blocked: {result.reason}")
else:
    print("Trade allowed")
```

---

## 2. Config-System (TOML)

**Datei:** `config.toml`

### Neue Risk-Parameter

```toml
[risk]
# ===== Position Sizing =====
position_sizing_method = "fixed_fractional"  # oder "kelly"
risk_per_trade = 0.01
max_position_size = 0.25
min_position_value = 50.0
min_stop_distance = 0.005
kelly_scaling = 0.5

# ===== Portfolio Risk Limits =====
max_daily_loss = 0.03
max_drawdown = 0.20
max_positions = 2
max_total_exposure = 0.75
```

### Verwendung im Code

```python
from src.core import get_config

config = get_config()

# Zugriff auf Risk-Parameter
print(config.risk.risk_per_trade)        # 0.01
print(config.risk.max_daily_loss)        # 0.03
print(config.risk.max_positions)         # 2

# Zugriff auf Backtest-Parameter
print(config.backtest.initial_cash)      # 10000.0

# Zugriff auf Strategie-Parameter
from src.core import get_strategy_cfg
params = get_strategy_cfg("ma_crossover")
print(params['fast_period'])             # 10
```

---

## 3. Kraken Data Pipeline

**Dateien:**
- `src/data/kraken_pipeline.py` - Vollständige Pipeline
- `src/data/kraken.py` - Kraken-Client (bereits vorhanden)

**Features:**

### Einfache Verwendung

```python
from src.data import fetch_kraken_data

# Holt Daten von Kraken, normalisiert, cached
df = fetch_kraken_data("BTC/USD", timeframe="1h", limit=720)

print(df.head())
# → DatetimeIndex (UTC), Spalten: [open, high, low, close, volume]
```

### Erweiterte Verwendung

```python
from src.data import KrakenDataPipeline

pipeline = KrakenDataPipeline(use_cache=True)

# Daten holen und normalisieren
df = pipeline.fetch_and_prepare(
    symbol="BTC/USD",
    timeframe="1h",
    limit=720
)

# Resampling (z.B. 1h → 4h)
df_4h = pipeline.fetch_and_resample(
    symbol="BTC/USD",
    source_timeframe="1h",
    target_timeframe="4h",
    limit=1000
)

# Cache löschen
pipeline.clear_cache()
```

### Pipeline-Flow

```
Kraken API
    ↓
fetch_ohlcv_df()
    ↓
DataNormalizer
    ↓
ParquetCache
    ↓
Backtest-Ready DataFrame
```

**Vorteile:**
- Automatisches Caching (schneller Zugriff)
- Normalisiertes Format (Peak_Trade-Standard)
- Fehlerbehandlung
- Flexible Resampling-Optionen

---

## Demo-Scripts

### 1. Vollständiges Demo

Zeigt alle Features in Aktion:

```bash
python3 scripts/demo_complete_pipeline.py
```

**Demos:**
1. Config-System
2. Position Sizing (Fixed Fractional + Kelly)
3. Portfolio Risk Limits
4. Kraken Data Pipeline
5. Vollständiger Backtest mit allem

### 2. Kraken-Pipeline Demo

Fokus auf Daten-Beschaffung:

```bash
python3 scripts/demo_kraken_simple.py
```

**Zeigt:**
- Kraken-Verbindung testen
- Daten holen und cachen
- Resampling
- Convenience-Funktionen

---

## Integration in bestehenden Code

### Beispiel: Backtest mit neuem Risk-Layer

```python
from src.core import get_config
from src.data import fetch_kraken_data
from src.risk import RiskLimitChecker, RiskLimitsConfig, PortfolioState
from src.backtest.engine import BacktestEngine
from src.strategies.ma_crossover import generate_signals

# 1. Config laden
config = get_config()

# 2. Daten holen
df = fetch_kraken_data("BTC/USD", "1h", limit=720)

# 3. Risk-Limits konfigurieren
risk_config = RiskLimitsConfig(
    max_daily_loss=config.risk.max_daily_loss,
    max_drawdown=config.risk.max_drawdown,
    max_positions=config.risk.max_positions,
    max_total_exposure=config.risk.max_total_exposure
)
risk_checker = RiskLimitChecker(risk_config)

# 4. Backtest durchführen
engine = BacktestEngine()
result = engine.run_realistic(
    df=df,
    strategy_signal_fn=generate_signals,
    strategy_params={'fast_period': 10, 'slow_period': 30, 'stop_pct': 0.02}
)

print(f"Sharpe Ratio: {result.stats['sharpe']:.2f}")
print(f"Total Return: {result.stats['total_return']:.2%}")
```

---

## Best Practices

### Position Sizing

1. **Fixed Fractional für Live-Trading**
   - Einfach, robust, getestet
   - Empfohlen: 1-2% Risk per Trade

2. **Kelly nur mit ausreichend Daten**
   - Mindestens 30-50 Trades für Statistik
   - Immer mit Scaling-Faktor < 1.0 (typisch 0.25-0.5)
   - Regelmäßig neu berechnen

### Risk Limits

1. **Daily Loss Limit als Kill-Switch**
   - Typisch: 3-5% des Kapitals
   - Bei Erreichen: Alle Positionen schließen, Trading stoppen

2. **Max Drawdown Monitoring**
   - Typisch: 15-20% Portfolio-Drawdown
   - Warnung bei Annäherung, Stop bei Überschreitung

3. **Position Limits**
   - Max. 2-3 parallele Positionen für Retail
   - Max. 75% Total Exposure (25% Cash-Buffer)

### Kraken Integration

1. **Cache verwenden**
   - Spart API-Requests
   - Schnellerer Entwicklungszyklus

2. **Rate Limits beachten**
   - Kraken-Client hat enableRateLimit=True
   - Bei vielen Requests: Pausen einbauen

3. **Fehlerbehandlung**
   - Netzwerkfehler abfangen
   - Fallback auf gecachte Daten

---

## API-Referenz

### Position Sizing

```python
# PositionSizerConfig
class PositionSizerConfig:
    method: Literal["fixed_fractional", "kelly"]
    risk_pct: float                # Risiko pro Trade (%)
    max_position_pct: float        # Max. Position (%)
    kelly_scaling: float           # Kelly-Faktor (0-1)

# PositionSizer
class PositionSizer:
    def size_position(
        capital: float,
        stop_distance: float,
        win_rate: float = None,
        avg_win: float = None,
        avg_loss: float = None
    ) -> float
```

### Risk Limits

```python
# RiskLimitsConfig
class RiskLimitsConfig:
    max_daily_loss: float          # Max. Tagesverlust (0-1)
    max_drawdown: float            # Max. Drawdown (0-1)
    max_positions: int             # Max. parallele Positionen
    max_total_exposure: float      # Max. Gesamt-Exposure (0-1)

# RiskLimitChecker
class RiskLimitChecker:
    def check_limits(
        state: PortfolioState,
        proposed_position_value: float
    ) -> LimitCheckResult
```

### Kraken Pipeline

```python
# KrakenDataPipeline
class KrakenDataPipeline:
    def fetch_and_prepare(
        symbol: str,
        timeframe: str = "1h",
        limit: int = 720,
        force_refresh: bool = False
    ) -> pd.DataFrame

    def fetch_and_resample(
        symbol: str,
        source_timeframe: str = "1m",
        target_timeframe: str = "1h",
        limit: int = 720
    ) -> pd.DataFrame

# Convenience
def fetch_kraken_data(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 720
) -> pd.DataFrame
```

---

## Troubleshooting

### Kraken-Verbindungsfehler

**Problem:** `NetworkError` oder `ExchangeError`

**Lösung:**
1. Internetverbindung prüfen
2. Kraken-Status checken: https://status.kraken.com/
3. Rate Limits beachten (max. 1 Request/Sekunde)
4. VPN/Firewall prüfen

### Config-Fehler

**Problem:** `FileNotFoundError: Config nicht gefunden`

**Lösung:**
1. Prüfe ob `config.toml` im Projekt-Root liegt
2. Setze Environment Variable: `export PEAK_TRADE_CONFIG=&#47;path&#47;to&#47;config.toml`

### Position Sizing gibt 0 zurück

**Problem:** `size = 0.0`

**Mögliche Ursachen:**
1. Stop zu eng (< min_stop_distance)
2. Position zu groß (> max_position_pct)
3. Position zu klein (< min_position_value)

**Lösung:** Prüfe `PositionResult.reason` für Details

---

## Changelog

### 2024-12-02

**Neu:**
- ✅ Erweiterte Position-Sizing-Methoden (Fixed Fractional + Kelly)
- ✅ Portfolio Risk Limits (Daily Loss, Drawdown, Positions, Exposure)
- ✅ Kraken Data Pipeline mit vollständiger Integration
- ✅ Erweiterte config.toml mit neuen Risk-Parametern
- ✅ Demo-Scripts für alle Features

**Verbessert:**
- ✅ Risk-Modul komplett überarbeitet
- ✅ Data-Layer Integration mit Kraken
- ✅ Config-System erweitert

---

## Support

Bei Fragen oder Problemen:
1. Demo-Scripts durchgehen
2. API-Referenz konsultieren
3. Bestehende Strategie-Implementierungen ansehen

**Wichtige Dateien:**
- `src/risk/position_sizer.py` - Position Sizing
- `src/risk/limits.py` - Risk Limits
- `src/data/kraken_pipeline.py` - Kraken Integration
- `config.toml` - Zentrale Konfiguration
