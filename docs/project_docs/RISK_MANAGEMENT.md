# Risk Management – Peak_Trade

**Stand:** 2025-12-02
**Version:** 1.0
**Author:** Peak_Trade Risk Management Team

---

## 1. Zweck & Scope

Dieses Dokument beschreibt das zentrale Risk-Management-System von **Peak_Trade**.
Ziel ist es, klare Regeln und Mechanismen zu definieren, die:

- das **Gesamtrisiko des Portfolios** begrenzen,
- **Positionsgrößen** systematisch steuern,
- **Verlustphasen** abfedern (Drawdown-Kontrolle),
- und das Verhalten des Systems über **Config** und **Code** reproduzierbar machen.

Das Dokument richtet sich an:

- Entwickler:innen, die am Risk-Layer arbeiten,
- Quant/Strategy-Designer,
- Operator/DevOps, die das System im Live-Betrieb überwachen.

---

## 2. Verwandte Dokumente & Artefakte

**Dokumentation**

- `docs/project_docs/RISK_LIMITS_UPDATE.md` – Implementation Details und Updates zu Risikolimits.
- `docs/project_docs/IMPLEMENTATION_SUMMARY.md` – Überblick über Architektur und Implementierung.
- `docs/project_docs/CONFIG_SYSTEM.md` – Allgemeines Config-System.

**Konfiguration**

- `config/config.toml` – insbesondere Sektion `[risk]`.

**Code**

- `src/risk/limits.py` – Implementierung der Risiko-Limits & Portfolio-Guards.
- `src/risk/position_sizer.py` – Implementierung des Position Sizers (inkl. Kelly-Logik, falls aktiviert).

**Demos**

- `scripts/demo_risk_limits.py` – Demonstration und Validierung der Risiko-Limits.
- – End-to-End Demo (Data + Risk + Backtest/Execution).

**Tests**

- `tests&#47;test_risk.py` (falls vorhanden) – Unit- und/oder Integrationstests für Risk-Komponenten.

---

## 3. Grundprinzipien des Risk Managements

Das Risk Management folgt diesen Kernprinzipien:

1. **Capital Preservation First**
   Erhalt des eingesetzten Kapitals hat Vorrang vor kurzfristiger Performance.

2. **Limitbasiertes Design**
   Alle Risiken (pro Trade, pro Tag, pro Portfolio) sind über **konfigurierbare Limits** begrenzt.

3. **Deterministisches Verhalten**
   Risiko-Entscheidungen basieren auf klar definierten Regeln und Parametern (keine „magische" Logik).

4. **Trennung von Logik & Parametern**
   - Logik: in `src/risk/limits.py` und `src/risk/position_sizer.py`
   - Parameter: in `config/config.toml` (`[risk]` und ggf. Subsektionen)

5. **Testbarkeit & Transparenz**
 - Demos (`scripts/demo_risk_limits.py`, ) zeigen das Verhalten.
   - Tests (`tests&#47;test_risk.py`) sichern grundlegende Invarianten ab.

---

## 4. Zentrale Risiko-Kennzahlen & Limits

> **Hinweis:** Konkrete Werte & Details entnimmst du `RISK_LIMITS_UPDATE.md` und `config/config.toml`.
> In diesem Abschnitt wird die Struktur beschrieben, nicht zwingend die exakten Zahlen.

Typische zentrale Größen:

### 4.1. Maximaler Verlust pro Trade

- **Ziel:** Einzelpositionen dürfen nur einen definierten Prozentsatz des Gesamtkapitals riskieren.
- Konfigurationsparameter (Beispiel):
  - `risk.max_risk_per_trade = 0.01`  → max. 1% des Kapitals pro Trade riskieren.
- Verwendung:
  - Der Position Sizer (`position_sizer.py`) berechnet Positionsgrößen so, dass dieses Limit nicht verletzt wird.

### 4.2. Maximaler täglicher Verlust (Daily Loss Limit)

- **Ziel:** Begrenzung des Verlusts pro Tag, um „Blow-Up"-Tage zu verhindern.
- Mögliche Parameter:
  - `risk.max_daily_loss = 0.03` → max. 3% Verlust des Kapitals pro Tag.
  - `risk.daily_loss_cooldown = 1` → nach Erreichen des Limits keine neuen Trades mehr an diesem Tag.
- Umsetzung:
  - `limits.py` prüft, ob das Tagesverlust-Limit überschritten ist und blockiert weitere Orders.

### 4.3. Maximaler Drawdown (Portfolio Drawdown Limit)

- **Ziel:** Begrenzung des kumulierten Verlusts über eine längere Periode.
- Parameter-Beispiele:
  - `risk.max_drawdown = 0.20` → max. 20% Peak-to-Trough Drawdown.
  - `risk.max_drawdown_action = "pause"` → System geht in „Pause"-Modus, wenn Limit erreicht ist.
- Umsetzung:
  - `limits.py` überwacht Equity-Curve / NAV und löst bei Überschreitung entsprechende Maßnahmen aus.

### 4.4. Exposure-Limits

- **Ziel:** Begrenzen der Summe aller offenen Positionen.
- Beispiele:
  - `risk.max_gross_exposure = 1.0` → max. 100% des Kapitals gleichzeitig im Markt.
  - `risk.max_net_exposure = 0.5` → z.B. max. 50% Netto-Exposure Long oder Short.
- Umsetzung:
  - `limits.py` aggregiert offene Positionen und blockiert neue Orders, wenn die Exposure-Limits überschritten würden.

---

## 5. Position Sizing (inkl. Kelly-Logik)

Der Position Sizer in `src/risk/position_sizer.py` ist verantwortlich für:

1. Ableitung der **Positionsgröße** aus:
   - verfügbarem Kapital,
   - Risikoparametern,
   - Volatilität / Stop-Distanz (falls verwendet),
   - optional: Kelly-Logik oder Fixed-Fraction-Modellen.

2. Sicherstellen, dass keine der unter Abschnitt 4 beschriebenen Limits verletzt wird.

### 5.1. Grundlegende Parameter

Typische Konfigurationsparameter in `[risk]`:

- `risk.base_risk_fraction`
  Basisanteil des Kapitals, der pro Trade riskiert werden darf (z.B. 1%).

- `risk.use_kelly = true&#47;false`
  Schaltet Kelly-Logik ein/aus.

- `risk.kelly_fraction`
  Skaliert die Kelly-Position (z.B. 0.5 = halbes Kelly).

- `risk.min_position_size`, `risk.max_position_size`
  Grenzen für die absolute Anzahl an Kontrakten/Units.

### 5.2. Kelly-Logik (falls aktiviert)

Wenn `use_kelly = true`:

- Der Position Sizer kann basierend auf:
  - geschätzter Trefferquote,
  - Payoff-Ratio,
  eine optimale Kelly-Fraktion berechnen.
- Diese wird mit `kelly_fraction` skaliert, um konservativer zu agieren.

> Details zur konkreten Implementierung entnimmst du `position_sizer.py` und `RISK_LIMITS_UPDATE.md`.

---

## 6. Globale Portfolio-Limits & Safeguards

Die Komponente `src/risk/limits.py` implementiert globale Schutzmechanismen:

### 6.1. Kill-Switch / Trading Pause

- Bei Überschreiten bestimmter Limits (z.B. `max_drawdown`, `max_daily_loss`) kann das System:
  - alle offenen Orders/Positionen glattstellen (falls implementiert),
  - neue Trades blockieren,
  - einen „PAUSE"-Status setzen, der in der Pipeline / im Orchestrator beachtet wird.

### 6.2. Circuit-Breaker

- Optional: zusätzliche Schwellenwerte (z.B. ungewöhnlich hohe Volatilität, Verlust in kurzer Zeit), die:
  - Trading temporär stoppen,
  - eine manuelle Überprüfung erzwingen.

### 6.3. Logging & Alerts

- Alle Limit-Verletzungen sollten:
  - **geloggt** werden (z.B. mit Level WARN/ERROR),
  - optional Alerts triggern (E-Mail, Slack, etc. – außerhalb dieses Dokuments).

---

## 7. Konfiguration in `config/config.toml`

Die Risk-Parameter werden in `config/config.toml` (Sektion `[risk]`) gepflegt.

### 7.1. Beispiel-Konfiguration

```toml
[risk]
max_risk_per_trade = 0.01
max_daily_loss = 0.03
max_drawdown = 0.20
max_gross_exposure = 1.0
max_net_exposure = 0.5

use_kelly = false
kelly_fraction = 0.5
base_risk_fraction = 0.01

min_position_size = 0.001
max_position_size = 1.0

daily_loss_cooldown = 1
max_drawdown_action = "pause"
```

**Wichtig:**
Die tatsächlichen Parameter-Werte bitte aus `RISK_LIMITS_UPDATE.md` und der produktiven `config.toml` übernehmen.

### 7.2. Wie Config laden?

```python
from src.core.config import load_config

config = load_config("config/config.toml")
risk_params = config["risk"]

# Zugriff auf einzelne Werte
max_risk_per_trade = risk_params["max_risk_per_trade"]
use_kelly = risk_params.get("use_kelly", False)
```

---

## 8. Praktische Beispiele & Best Practices

### 8.1. Fixed Fractional Position Sizing (Standard)

**Prinzip:**
Festes Risiko pro Trade basierend auf Stop-Loss-Distanz.

**Formel:**
```
risk_amount = equity * risk_per_trade
position_size = risk_amount / stop_distance
```

**Beispiel:**
```python
from src.risk import PositionSizer, PositionSizerConfig

config = PositionSizerConfig(
    method="fixed_fractional",
    risk_pct=1.0,           # 1% Risiko pro Trade
    max_position_pct=25.0   # Max. 25% des Kapitals
)

sizer = PositionSizer(config)

# Capital: $10,000, Entry: $50,000, Stop: $49,000
capital = 10000
stop_distance = 1000  # $1,000 Stop-Distanz

size = sizer.fixed_fractional(capital, 0.01, stop_distance)
# Output: 0.1 BTC (= $100 Risiko bei $1,000 Stop)
```

**Vorteile:**
- Einfach und transparent
- Konstantes Risiko pro Trade
- Keine historischen Daten erforderlich

**Nachteile:**
- Keine Anpassung an Win-Rate oder Erwartungswert
- Konservativ bei guten Strategien

### 8.2. Kelly Criterion (Fortgeschritten)

**Prinzip:**
Statistisch optimale Position Size basierend auf historischer Performance.

**Formel:**
```
kelly_fraction = win_rate - (1 - win_rate) / (avg_win / avg_loss)
position_size = equity * kelly_fraction * kelly_scaling
```

**Beispiel:**
```python
from src.risk import PositionSizer

# Win-Rate: 55%, Avg Win: $200, Avg Loss: $100
kelly = PositionSizer.kelly_criterion(0.55, 200, 100)
# Output: 0.325 (32.5% Full-Kelly)

# Mit Kelly-Scaling von 0.5 (Half-Kelly)
safe_kelly = kelly * 0.5
# Output: 0.1625 (16.25% des Kapitals)
```

**Vorteile:**
- Mathematisch optimal für Erwartungswert-Maximierung
- Passt sich an Strategie-Performance an

**Nachteile:**
- Benötigt historische Daten (min. 30-50 Trades)
- Full-Kelly ist zu aggressiv (immer Scaling verwenden!)

**Empfehlung:**
Starte mit Fixed Fractional. Wechsle zu Kelly erst nach mind. 50 erfolgreichen Backtest-Trades.

### 8.3. Risk-Aware Backtest Integration

```python
from src.backtest import BacktestEngine
from src.risk import RiskLimits, RiskLimitsConfig

class RiskAwareBacktest(BacktestEngine):
    def __init__(self, risk_config: RiskLimitsConfig):
        super().__init__()
        self.risk_limits = RiskLimits(risk_config)
        self.equity_history = []

    def before_order(self, position_value: float) -> bool:
        """Prüft Risk-Limits vor Order-Ausführung."""
        ok = self.risk_limits.check_all(
            equity_curve=self.equity_history,
            returns_today_pct=self.get_today_returns(),
            new_position_nominal=position_value,
            capital=self.current_equity
        )

        if not ok:
            self.log("Trade blocked by risk limits")

        return ok
```

---

## 9. Empfohlene Profile

### 9.1. Conservative (Anfänger)

```toml
[risk]
risk_per_trade = 0.005       # 0.5% pro Trade
max_position_size = 0.10     # 10% max. Position
max_daily_loss = 0.02        # 2% Kill-Switch
max_drawdown = 0.15          # 15% Max. Drawdown
max_positions = 1            # Nur 1 Position
kelly_scaling = 0.25         # Quarter-Kelly
```

**Empfohlen für:**
- Anfänger mit < 6 Monaten Erfahrung
- Kleine Accounts (< $5,000)
- Volatile Märkte (Krypto-Altcoins)

### 9.2. Moderate (Standard)

```toml
[risk]
risk_per_trade = 0.01        # 1% pro Trade
max_position_size = 0.25     # 25% max. Position
max_daily_loss = 0.03        # 3% Kill-Switch
max_drawdown = 0.20          # 20% Max. Drawdown
max_positions = 2            # Max. 2 Positionen
kelly_scaling = 0.5          # Half-Kelly
```

**Empfohlen für:**
- Intermediate Trader mit Backtest-Erfahrung
- Accounts > $5,000
- Strategien mit Sharpe > 1.5

### 9.3. Aggressive (Experten)

```toml
[risk]
risk_per_trade = 0.02        # 2% pro Trade
max_position_size = 0.40     # 40% max. Position
max_daily_loss = 0.05        # 5% Kill-Switch
max_drawdown = 0.25          # 25% Max. Drawdown
max_positions = 5            # Max. 5 Positionen
kelly_scaling = 0.75         # 3/4-Kelly
```

**Empfohlen für:**
- Profis mit > 2 Jahren Erfahrung
- Große Accounts (> $50,000)
- Strategien mit Sharpe > 2.0

**WARNUNG:** Nur nach ausgiebigem Backtesting verwenden!

---

## 10. Best Practices & Warnings

### 10.1. Niemals über 2% Risk per Trade

```python
# ✅ RICHTIG
risk_per_trade = 0.01  # 1%

# ❌ FALSCH
risk_per_trade = 0.05  # 5% (viel zu riskant!)
```

### 10.2. Immer Stop-Loss setzen

```python
# ✅ RICHTIG
stop_price = entry_price * (1 - 0.02)  # 2% Stop

# ❌ FALSCH
stop_price = None  # Kein Stop = Risiko unbegrenzt!
```

### 10.3. Drawdown-Limits respektieren

```python
# Bei 20% Drawdown: STOPPEN, ANALYSIEREN, STRATEGIE ÜBERPRÜFEN
if current_drawdown > 0.20:
    halt_trading()
    analyze_losses()
```

### 10.4. Kelly nur mit ausreichend Daten

```python
# ✅ RICHTIG
if trade_count >= 50:
    use_kelly_criterion()
else:
    use_fixed_fractional()
```

---

## 11. FAQ

### F: Was passiert, wenn ein Limit überschritten wird?

**A:** Die `check_all()` Methode gibt `False` zurück. Es liegt an deinem Trading-Code, wie darauf reagiert wird:
- **Backtest:** Trade wird übersprungen
- **Live-Trading:** Order wird nicht platziert, Alert wird ausgelöst

### F: Kann ich Risk-Limits zur Laufzeit ändern?

**A:** Ja, aber nicht empfohlen. Besser: Verschiedene Config-Profile erstellen und mit diesen testen.

### F: Was ist der Unterschied zwischen `max_position_size` und `risk_per_trade`?

**A:**
- `risk_per_trade`: Wie viel du **verlieren** darfst (Stop-Loss)
- `max_position_size`: Wie viel du **investieren** darfst (Nominal)

### F: Sollte ich Fixed Fractional oder Kelly verwenden?

**A:**
- **Fixed Fractional:** Für Anfänger und neue Strategien (< 50 Trades History)
- **Kelly:** Für erfahrene Trader mit min. 50-100 erfolgreichen Backtest-Trades

### F: Was bedeutet "Half-Kelly"?

**A:** Half-Kelly = 50% des Full-Kelly-Werts. Full-Kelly maximiert Erwartungswert, ist aber sehr volatil. Half-Kelly ist konservativer und in der Praxis sicherer.

---

## 12. Nächste Schritte & Roadmap

### Kurzfristig (implementiert)
- ✅ Basic Risk Limits (Drawdown, Daily Loss, Position Size)
- ✅ Position Sizer (Fixed Fractional + Kelly)
- ✅ Config-Integration
- ✅ Demo Scripts

### Mittelfristig (geplant)
- ⏳ Erweiterte Portfolio-Metriken (Sharpe, Sortino, Calmar)
- ⏳ Dynamische Risk-Adjustierung basierend auf Volatilität
- ⏳ Multi-Asset Position Sizing mit Korrelation
- ⏳ Alert-System (E-Mail, Slack) bei Limit-Verletzungen

### Langfristig (Vision)
- 🔮 Machine-Learning-basierte Risk-Modelle
- 🔮 Real-time Risk Dashboard
- 🔮 Stress-Testing & Scenario-Analysis Tools

---

**Dokumenten-Ende**
Bei Fragen oder Anmerkungen siehe: `docs/project_docs/RISK_LIMITS_UPDATE.md` oder kontaktiere das Development-Team.
