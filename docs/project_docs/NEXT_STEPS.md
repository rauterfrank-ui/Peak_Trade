# Peak_Trade - Nächste Schritte

> **Venue clarification (2026-07-08):** Kraken is **not** the current canonical target venue (`default_exchange=okx_europe_eea`). Kraken references below are **historical/legacy** infrastructure only unless separately ratified.

## ✅ Fertig Implementiert

1. ✅ Risk-Layer (Position Sizing + Limits)
2. ✅ Config-System mit TOML
3. ✅ Kraken Data Pipeline (legacy / guarded infrastructure)
4. ✅ Demo-Scripts
5. ✅ Dokumentation

---

## 🎯 Empfohlene Nächste Schritte

### 1. Testing & Validation (Priorität: HOCH)

**Tests schreiben:**
```bash
# Neue Test-Dateien erstellen
tests/test_risk_limits.py
tests/test_position_sizing.py
tests/test_kraken_pipeline.py
```

**Was testen:**
- ✅ Position Sizing mit verschiedenen Parametern
- ✅ Risk Limits (Daily Loss, Drawdown, etc.)
- ✅ Kraken Pipeline (mit Mock-Daten)
- ✅ Config-Loading

**Beispiel-Test:**
```python
# tests/test_position_sizing.py
import pytest
from src.risk import PositionSizer, PositionSizerConfig

def test_fixed_fractional_basic():
    config = PositionSizerConfig(method="fixed_fractional", risk_pct=1.0)
    sizer = PositionSizer(config)

    size = sizer.size_position(capital=10_000, stop_distance=1_000)
    assert size == 0.1  # 1% von 10000 = 100, 100/1000 = 0.1
```

---

### 2. Backtest-Engine Integration (Priorität: HOCH)

**Ziel:** Risk-Limits in BacktestEngine integrieren

**Änderungen in `src/backtest/engine.py`:**

```python
from src.risk import RiskLimitChecker, PortfolioState

class BacktestEngine:
    def __init__(self):
        self.config = get_config()
        self.risk_checker = RiskLimitChecker(...)  # ← NEU

    def run_realistic(self, ...):
        # Vor jedem Trade:
        state = PortfolioState(...)
        result = self.risk_checker.check_limits(state, position_value)

        if result.rejected:
            # Trade blockieren + loggen
            continue
```

**Benefits:**
- Realistische Backtests mit Risk-Management
- Vermeidung von Overfitting
- Genauere Live-Trading-Simulation

---

### 3. Live-Trading Integration (Priorität: MITTEL)

**Ziel:** Risk-Layer in Live-Trading einbauen

**Änderungen:**
```python
# In Live-Trading-Loop:
from src.risk import RiskLimitChecker, PortfolioState

# Vor Order-Platzierung:
result = risk_checker.check_limits(portfolio_state, order_value)

if result.rejected:
    logger.warning(f"Order blocked: {result.reason}")
    # Alert senden
else:
    # Order platzieren
    exchange.create_order(...)
```

**Zusätzlich benötigt:**
- Portfolio-State-Tracking in Datenbank/File
- Daily Reset-Mechanismus (für Daily Loss Limit)
- Alert-System (Email/Telegram bei Limit-Annäherung)

---

### 4. Monitoring & Logging (Priorität: MITTEL)

**Ziel:** Risk-Metriken tracken und visualisieren

**Implementierung:**

```python
# src/risk/monitor.py (NEU)
class RiskMonitor:
    """Tracked Risk-Metriken über Zeit."""

    def log_position_sizing_decision(self, request, result):
        # Logge Position-Sizing-Entscheidungen
        pass

    def log_risk_limit_check(self, state, result):
        # Logge Risk-Limit-Checks
        pass

    def get_daily_summary(self):
        # Daily Risk Summary
        return {
            'trades_blocked': ...,
            'avg_position_size': ...,
            'max_drawdown_today': ...,
        }
```

**Visualisierung:**
- Grafana-Dashboard für Risk-Metriken
- Jupyter Notebook für Analyse
- CSV-Export für Excel

---

### 5. Parameter-Optimierung (Priorität: NIEDRIG)

**Ziel:** Optimale Risk-Parameter finden

**Methoden:**

1. **Grid-Search für Position Sizing:**
   ```python
   risk_pcts = [0.5, 1.0, 1.5, 2.0]
   max_positions = [1, 2, 3]

   for risk_pct in risk_pcts:
       for max_pos in max_positions:
           # Backtest durchführen
           # Sharpe Ratio tracken
   ```

2. **Kelly-Criterion vs Fixed Fractional:**
   - A/B-Test über mehrere Strategien
   - Vergleich: Sharpe, Drawdown, Return

3. **Daily Loss Limit Optimization:**
   - Zu eng: Viele gute Trades verpasst
   - Zu weit: Zu große Verluste möglich
   - Optimum finden via Backtest

---

### 6. Multi-Strategy Portfolio (Priorität: NIEDRIG)

**Ziel:** Risk-Management über mehrere Strategien

**Implementierung:**

```python
# src/risk/portfolio_risk.py (NEU)
class PortfolioRiskManager:
    """Risk-Management für Multi-Strategy-Portfolio."""

    def allocate_capital(self, strategies, total_capital):
        # Capital Allocation basierend auf Risk
        pass

    def check_portfolio_limits(self, all_positions):
        # Portfolio-weite Limits
        pass
```

**Features:**
- Korrelations-basierte Allocation
- Portfolio-Drawdown-Monitoring
- Cross-Strategy Risk Limits

---

## 🔧 Empfohlene Verbesserungen

### Position Sizing

**Short-Support hinzufügen:**
```python
# Aktuell: Nur Long-Positionen
# TODO: Short-Positionen unterstützen

class PositionSizer:
    def size_position(self, ..., side: Literal["long", "short"] = "long"):
        if side == "short":
            # Stop muss über Entry liegen
            if stop_price <= entry_price:
                return rejected
```

**Partial-Exit-Support:**
```python
# TODO: Position-Sizing für Partial-Exits
# z.B. 50% bei Target 1, 50% bei Target 2

def size_partial_exits(self, entry_size, exit_levels):
    # Berechne optimale Partial-Sizes
    pass
```

---

### Risk Limits

**Trailing Stop für Daily Loss:**
```python
# Wenn Trade profitabel läuft, Daily Loss Limit anpassen
# "Lock in Profits" Mechanismus

def update_daily_loss_limit_with_profits(state, locked_profit):
    new_daily_start = state.daily_start_equity + locked_profit
    return PortfolioState(..., daily_start_equity=new_daily_start)
```

**Volatility-Adjusted Limits:**
```python
# Risk-Limits basierend auf Markt-Volatilität anpassen
# Hohe Volatilität → strengere Limits

def adjust_limits_for_volatility(base_limits, current_vol, avg_vol):
    factor = current_vol / avg_vol
    return RiskLimitsConfig(
        max_daily_loss=base_limits.max_daily_loss / factor,
        ...
    )
```

---

### Kraken Pipeline

**Multi-Symbol-Support:**
```python
# TODO: Mehrere Symbols parallel laden

def fetch_multiple_symbols(symbols: List[str], timeframe: str):
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(fetch_kraken_data, sym, timeframe)
            for sym in symbols
        ]
        return {sym: f.result() for sym, f in zip(symbols, futures)}
```

**Websocket-Support:**
```python
# TODO: Real-time Daten via Websocket
# Für Live-Trading wichtig

class KrakenWebsocketStream:
    async def subscribe_ticker(self, symbol):
        # Real-time Ticker-Updates
        pass
```

---

## 📊 Performance-Optimierung

### Caching verbessern

**TTL (Time-To-Live) für Cache:**
```python
# src/data/cache.py
class ParquetCache:
    def save(self, df, key, ttl_hours: int = 24):
        # Cache mit Ablaufdatum
        metadata = {'saved_at': datetime.now(), 'ttl': ttl_hours}
        # Speichere mit Metadata
```

**Cache-Warming:**
```python
# Lade häufig genutzte Daten vor
def warm_cache(symbols: List[str], timeframes: List[str]):
    for symbol in symbols:
        for tf in timeframes:
            fetch_kraken_data(symbol, tf)
```

---

## 📚 Dokumentation erweitern

### Jupyter Notebooks erstellen

**Notebooks:**
```
notebooks/
├── 01_position_sizing_tutorial.ipynb
├── 02_risk_limits_explained.ipynb
├── 03_kraken_pipeline_usage.ipynb
└── 04_backtest_with_risk_management.ipynb
```

### Video-Tutorials

**Themen:**
1. Position Sizing Basics (5 min)
2. Kelly vs Fixed Fractional (10 min)
3. Risk Limits Setup (8 min)
4. Kraken Integration (12 min)
5. Complete Workflow (20 min)

---

## 🎓 Weiterbildung

### Empfohlene Literatur

**Position Sizing:**
- Ralph Vince: "Portfolio Management Formulas"
- Van K. Tharp: "Trade Your Way to Financial Freedom"

**Risk Management:**
- Jack Schwager: "Market Wizards" (Risk-Kapitel)
- Nassim Taleb: "Fooled by Randomness"

**Quantitative Finance:**
- Ernest Chan: "Quantitative Trading"
- Robert Pardo: "The Evaluation and Optimization of Trading Strategies"

---

## 🚀 Deployment

### Production Checklist

**Vor Live-Trading:**

- [ ] Alle Tests grün
- [ ] Risk-Limits validiert in Backtests
- [ ] Monitoring aufgesetzt
- [ ] Alert-System konfiguriert
- [ ] Backup-Strategie definiert
- [ ] Kill-Switch getestet
- [ ] Paper-Trading erfolgreich (min. 1 Monat)
- [ ] Code-Review durchgeführt
- [ ] Dokumentation vollständig
- [ ] Disaster-Recovery-Plan

**Deployment-Steps:**

1. Staging-Environment aufsetzen
2. Paper-Trading starten
3. Metriken über 1-2 Monate tracken
4. Live-Trading mit minimalem Kapital
5. Schrittweise hochskalieren

---

## ❓ Offene Fragen

**Zu klären:**

1. **Position Sizing:**
   - Welche Methode für welche Strategie?
   - Kelly-Scaling-Faktor optimal?
   - Update-Frequenz für Kelly-Parameter?

2. **Risk Limits:**
   - Sollten Limits strategie-spezifisch sein?
   - Wie Daily Loss Limit bei Overnight-Positionen?
   - Emergency-Exit-Strategie bei Limit-Verletzung?

3. **Integration:**
   - Risk-Limits in bestehende Strategien einbauen?
   - Backwards-Compatibility erhalten?
   - Migration-Plan für Live-System?

---

## 🎯 Prioritäten-Matrix

| Feature | Priorität | Aufwand | Impact |
|---------|-----------|---------|--------|
| Tests schreiben | HOCH | Mittel | HOCH |
| Backtest-Integration | HOCH | Klein | HOCH |
| Live-Trading-Integration | MITTEL | Groß | HOCH |
| Monitoring & Logging | MITTEL | Mittel | MITTEL |
| Short-Support | NIEDRIG | Klein | NIEDRIG |
| Multi-Strategy | NIEDRIG | Groß | MITTEL |

**Empfohlene Reihenfolge:**
1. Tests schreiben (1-2 Tage)
2. Backtest-Integration (1 Tag)
3. Monitoring & Logging (2-3 Tage)
4. Live-Trading-Integration (3-5 Tage)

---

## 📞 Support & Community

**Bei Problemen:**

1. Demo-Scripts durchgehen
2. Dokumentation konsultieren
3. Code-Kommentare lesen
4. Tests als Beispiele nutzen

**Weiterentwicklung:**

- GitHub Issues für Feature-Requests
- Pull Requests willkommen
- Code-Reviews für kritische Änderungen

---

**Stand:** 2024-12-02
**Nächstes Review:** Nach Testing-Phase
