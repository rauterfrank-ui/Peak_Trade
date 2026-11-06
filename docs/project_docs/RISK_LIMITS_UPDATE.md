# Risk Limits Update - Neue Implementierung

**Datum:** 2024-12-02
**Status:** ✅ Implementiert & Getestet

---

## Übersicht

Die `src/risk/limits.py` Datei wurde überarbeitet und an deine Spezifikation angepasst.

### Neue Klasse: `RiskLimits`

Ersetzt die alte `RiskLimitChecker` Klasse mit einer klareren, funktionaleren API.

---

## API-Änderungen

### Alte API (Legacy, noch unterstützt):

```python
from src.risk import RiskLimitChecker, RiskLimitsConfig, PortfolioState

config = RiskLimitsConfig(
    max_daily_loss=0.03,      # Dezimalwerte (0.03 = 3%)
    max_drawdown=0.20,
    max_positions=2,
    max_total_exposure=0.75
)

checker = RiskLimitChecker(config)
state = PortfolioState(
    equity=10000,
    peak_equity=10500,
    daily_start_equity=10200
)

result = checker.check_limits(state, proposed_position_value=2000)
if result.rejected:
    print(f"Blocked: {result.reason}")
```

### Neue API (Empfohlen):

```python
from src.risk import RiskLimits, RiskLimitsConfig

config = RiskLimitsConfig(
    max_drawdown_pct=20.0,      # Prozentwerte (20.0 = 20%)
    max_position_pct=10.0,
    daily_loss_limit_pct=5.0
)

limits = RiskLimits(config)

# Kombinierter Check
ok = limits.check_all(
    equity_curve=[10000, 10200, 10500],
    returns_today_pct=[0.5, -1.0, 0.3],
    new_position_nominal=2000,
    capital=10500
)

if not ok:
    print("Trade blocked!")
```

---

## Neue Features

### 1. Statische Check-Methoden

Alle Check-Methoden sind jetzt auch als `@staticmethod` verfügbar:

```python
# Drawdown Check
ok = RiskLimits.check_drawdown(
    equity_curve=[10000, 10500, 9500, 9000],
    max_dd_pct=20.0
)

# Daily Loss Check
ok = RiskLimits.check_daily_loss(
    returns_today_pct=[0.5, -1.2, 0.3, -2.1],
    max_loss_pct=5.0
)

# Position Size Check
ok = RiskLimits.check_position_size(
    size_nominal=2500,
    capital=10000,
    max_pct=25.0
)
```

### 2. Klarere Semantik

**Alte API:**
- Config mit Dezimalwerten (0.03 = 3%)
- Portfolio-State als Wrapper
- Komplexe Check-Logik

**Neue API:**
- Config mit Prozentwerten (3.0 = 3%)
- Direkte Parameter
- Klare Return-Werte (True/False)

### 3. check_all() Methode

Kombiniert alle Checks in einem Aufruf:

```python
limits = RiskLimits(config)

ok = limits.check_all(
    equity_curve=equity_history,      # Vollständige Historie
    returns_today_pct=today_returns,  # Nur heutige Returns
    new_position_nominal=position_value,
    capital=current_capital
)
```

---

## Migration-Guide

### Schritt 1: Config anpassen

**Alt:**
```python
config = RiskLimitsConfig(
    max_daily_loss=0.03,
    max_drawdown=0.20,
    max_positions=2,
    max_total_exposure=0.75
)
```

**Neu:**
```python
config = RiskLimitsConfig(
    max_drawdown_pct=20.0,
    max_position_pct=10.0,
    daily_loss_limit_pct=5.0
)
```

### Schritt 2: Code umschreiben

**Alt:**
```python
from src.risk import RiskLimitChecker, PortfolioState

checker = RiskLimitChecker(config)
state = PortfolioState(
    equity=equity,
    peak_equity=peak,
    daily_start_equity=start
)
result = checker.check_limits(state, position_value)

if result.rejected:
    # Blockieren
    pass
```

**Neu:**
```python
from src.risk import RiskLimits

limits = RiskLimits(config)

ok = limits.check_all(
    equity_curve=equity_history,
    returns_today_pct=today_returns,
    new_position_nominal=position_value,
    capital=current_equity
)

if not ok:
    # Blockieren
    pass
```

### Schritt 3: Legacy-Code läuft weiter

**Wichtig:** Die alte API ist noch vollständig verfügbar!

```python
# Das funktioniert noch:
from src.risk import RiskLimitChecker, PortfolioState

checker = RiskLimitChecker(old_config)
result = checker.check_limits(state, value)
```

---

## Beispiele

### Beispiel 1: Drawdown-Check

```python
from src.risk import RiskLimits

equity_curve = [10000, 10500, 9500, 8000, 8500]

# Statisch
ok = RiskLimits.check_drawdown(equity_curve, max_dd_pct=20.0)

if ok:
    print("Drawdown OK")
else:
    print("Drawdown zu hoch!")
```

### Beispiel 2: Daily Loss Check

```python
from src.risk import RiskLimits

# Returns des Tages (in %)
returns_today = [0.5, -1.2, 0.3, -2.1, 0.8]

ok = RiskLimits.check_daily_loss(returns_today, max_loss_pct=5.0)

if ok:
    print("Daily Loss OK")
else:
    print("Daily Loss Limit überschritten!")
```

### Beispiel 3: Kompletter Check

```python
from src.risk import RiskLimits, RiskLimitsConfig

config = RiskLimitsConfig(
    max_drawdown_pct=20.0,
    max_position_pct=10.0,
    daily_loss_limit_pct=5.0
)

limits = RiskLimits(config)

# Vor Trade-Eröffnung
ok = limits.check_all(
    equity_curve=[10000, 10200, 10500, 10300],
    returns_today_pct=[0.5, -1.0, 0.3],
    new_position_nominal=1000,
    capital=10300
)

if ok:
    print("✅ Trade erlaubt")
    # Trade ausführen
else:
    print("❌ Trade blockiert")
```

---

## Demo-Script

Ausführen:
```bash
python3 scripts/demo_risk_limits.py
```

Zeigt:
- ✅ Drawdown Check (OK + Verletzung)
- ✅ Daily Loss Check (OK + Verletzung)
- ✅ Position Size Check (OK + Verletzung)
- ✅ check_all() (verschiedene Szenarien)
- ✅ Custom Configs (Aggressive vs Conservative)

---

## Tests

Alle Tests erfolgreich:

```
✅ RiskLimits initialized
✅ Drawdown Check (20%): True
✅ Daily Loss Check (5%): True
✅ Position Size Check (25%): True
✅ check_all(): True
✅ Legacy compatibility OK!
```

---

## Performance

### Drawdown-Berechnung

Nutzt NumPy für effiziente Berechnung:
```python
running_max = np.maximum.accumulate(equity_arr)
drawdown_pct = (equity_arr - running_max) / running_max * 100.0
max_dd = np.min(drawdown_pct)
```

### Daily Loss Berechnung

Filtert nur negative Returns:
```python
losses = returns_arr[returns_arr < 0]
total_loss_pct = abs(np.sum(losses))
```

---

## Integration mit Backtest-Engine

### Beispiel-Integration:

```python
from src.backtest import BacktestEngine
from src.risk import RiskLimits, RiskLimitsConfig

class BacktestEngineWithRisk(BacktestEngine):
    def __init__(self):
        super().__init__()
        config = RiskLimitsConfig(
            max_drawdown_pct=20.0,
            max_position_pct=10.0,
            daily_loss_limit_pct=5.0
        )
        self.risk_limits = RiskLimits(config)
        self.equity_history = []
        self.daily_returns = []

    def _should_open_position(self, position_value, capital):
        """Prüft Risk-Limits vor Position-Eröffnung."""
        ok = self.risk_limits.check_all(
            equity_curve=self.equity_history,
            returns_today_pct=self.daily_returns,
            new_position_nominal=position_value,
            capital=capital
        )
        return ok
```

---

## FAQ

### Q: Muss ich meinen bestehenden Code ändern?

**A:** Nein! Die alte API (`RiskLimitChecker`, `PortfolioState`) ist noch vollständig verfügbar und funktioniert wie gewohnt.

### Q: Wann sollte ich die neue API nutzen?

**A:**
- Bei neuem Code
- Wenn du klarere Semantik willst
- Wenn du einzelne Checks brauchst

### Q: Was sind die Hauptunterschiede?

**A:**
1. **Config:** Prozentwerte statt Dezimalwerte
2. **API:** Statische Methoden + check_all()
3. **Returns:** Boolean statt Result-Objekt

### Q: Wie berechne ich `returns_today_pct`?

**A:**
```python
# Aus Trades
returns_today = []
for trade in today_trades:
    ret_pct = (trade.pnl / (trade.size * trade.entry_price)) * 100
    returns_today.append(ret_pct)

# Oder aus Equity-Changes
start_equity = equity_at_day_start
current_equity = current_equity_value
return_pct = ((current_equity - start_equity) / start_equity) * 100
returns_today = [return_pct]
```

### Q: Was passiert bei leeren Arrays?

**A:** Alle Checks geben `True` zurück (keine Daten = kein Limit verletzt).

---

## Zusammenfassung

✅ **Neue Klasse:** `RiskLimits` mit klarer API
✅ **Statische Methoden:** Einzelne Checks möglich
✅ **check_all():** Kombinierter Check
✅ **Legacy-Support:** Alter Code läuft weiter
✅ **Tests:** Alle erfolgreich
✅ **Demo:** `scripts/demo_risk_limits.py`

**Migration:** Optional, aber empfohlen für neuen Code.

---

## Nächste Schritte

1. **Demo ausführen:**
   ```bash
   python3 scripts/demo_risk_limits.py
   ```

2. **In Backtest integrieren:**
   - Risk-Limits vor Trade-Eröffnung prüfen
   - Equity-History und Daily-Returns tracken

3. **Live-Trading:**
   - Risk-Limits in Trading-Loop einbauen
   - Alerts bei Limit-Annäherung

---

**Stand:** 2024-12-02
**Dokumentation:** `docs/NEW_FEATURES.md`
**Tests:** ✅ Alle erfolgreich
**Migration:** Optional (Legacy-Support vorhanden)
