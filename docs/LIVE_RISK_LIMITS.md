# Live-Risk-Limits

Dieses Modul implementiert zentrale Risikobegrenzungen für Live- und Paper-Trading-Flows in Peak_Trade.
Es stellt sowohl eine Python-API als auch CLI-Tools zur Verfügung, um Orders vor Ausführung automatisiert zu prüfen.

---

## 1. Konfiguration (`config.toml`)

Die Live-Risk-Limits werden im Block `[live_risk]` der Projektkonfiguration gepflegt:

```toml
[live_risk]
# Absoluter maximaler Tagesverlust in Account-Währung
max_daily_loss_abs = 500.0

# Maximaler Tagesverlust in Prozent des Startkapitals (starting_cash)
max_daily_loss_pct = 5.0

# Maximaler gesamter Notional-Exposure über alle offenen Positionen
max_total_exposure_notional = 5000.0

# Maximaler Notional-Exposure pro Symbol
max_symbol_exposure_notional = 2500.0

# Maximal erlaubte Anzahl offener Positionen
max_open_positions = 10

# Maximal erlaubtes Order-Notional pro Einzelorder
max_order_notional = 1000.0

# Verhalten bei Verletzung:
# true  → Skript bricht mit Exit Code 1 ab
# false → nur Warnung, Ausführung läuft weiter
block_on_violation = true

# Ob Tages-PnL aus der Registry (Experiments) aggregiert werden soll
use_experiments_for_daily_pnl = true
```

> Hinweis: Alle Werte sind Beispielwerte und sollten je nach Account-Größe, Strategie und Broker-Risiko angepasst werden.

---

## 2. Python-API (`src/live/risk_limits.py`)

### 2.1 `LiveRiskConfig`

Dataclass, die die Konfiguration aus `PeakConfig` / `config.toml` repräsentiert:

* `max_daily_loss_abs: float`
* `max_daily_loss_pct: float`
* `max_total_exposure_notional: float`
* `max_symbol_exposure_notional: float`
* `max_open_positions: int`
* `max_order_notional: float`
* `block_on_violation: bool`
* `use_experiments_for_daily_pnl: bool`

### 2.2 `LiveRiskCheckResult`

Dataclass für das Ergebnis eines Risk-Checks:

* `allowed: bool` – ob die Ausführung zulässig ist
* `reasons: list[str]` – Liste der Verletzungen / Warnungen
* `metrics: dict[str, float]` – verwendete Metriken (z. B. `daily_pnl`, `total_exposure`, `max_symbol_exposure`, ...)

### 2.3 `LiveRiskLimits`

Hauptklasse zur Durchführung der Checks:

* `@classmethod from_config(cls, peak_config) -> LiveRiskLimits`
  Erzeugt eine Instanz aus der globalen `PeakConfig` (inkl. `live_risk`-Block).

* `check_orders(orders, *, starting_cash: float | None = None) -> LiveRiskCheckResult`
  Prüft einen Batch von Orders gegen alle konfigurierten Limits.
  Nutzt intern u. a.:

  * Positions-/Exposure-Berechnung
  * Tages-PnL (entweder aus Registry oder aus aktuellem Kontext)
  * Order-Notional je Order
  * Anzahl offener Positionen

* `_compute_daily_pnl_from_experiments()`
  Interne Methode: Aggregiert das Tages-PnL aus der Registry anhand von `run_type`, Datum etc., falls `use_experiments_for_daily_pnl = true`.

---

## 3. Modul-Export (`src/live/__init__.py`)

`LiveRiskLimits`, `LiveRiskConfig` und `LiveRiskCheckResult` werden in `src/live/__init__.py` exportiert, sodass sie als:

```python
from src.live import LiveRiskLimits, LiveRiskConfig, LiveRiskCheckResult
```

verwendet werden können.

---

## 4. CLI-Integration

Die Live-Risk-Limits sind in mehrere Skripte integriert. Alle relevanten Skripte teilen sich konsistente CLI-Flags.

### 4.1 Gemeinsame CLI-Flags

* `--enforce-live-risk`
  Aktiviert **Hard Enforcement**:

  * Bei Verletzung eines Limits → Skript bricht mit Exit Code 1 ab.
  * Geeignet für echte Live- oder strikt kontrollierte Paper-Umgebungen.

* `--skip-live-risk`
  Deaktiviert den Risk-Check explizit:

  * Keine Limit-Prüfung.
  * Nützlich für Debugging oder historische Backfills (bewusster Einsatz!).

> Standardverhalten (wenn kein Flag gesetzt ist):
> Risk-Check wird ausgeführt, **bei Verletzung erfolgt nur eine Warnung**, die Ausführung läuft weiter.

---

### 4.2 `scripts/preview_live_orders.py`

Purpose:
Vorab-Vorschau von Live-Orders inkl. Risk-Check, **ohne** die Orders real oder im Paper-Mode auszuführen.

Verhalten:

* Erzeugt Orders auf Basis der Strategie / des Signals.
* Führt `LiveRiskLimits.check_orders(...)` aus.
* Bei Verletzung:

  * Ohne `--enforce-live-risk`: Warnung, aber Skript läuft weiter.
  * Mit `--enforce-live-risk`: Abbruch mit Exit Code 1.

Beispielaufrufe:

```bash
# Standard: Risk-Check mit Warnung bei Verletzung
python scripts/preview_live_orders.py --signals reports/forward/..._signals.csv

# Strikte Durchsetzung – bricht bei Verletzung sofort ab
python scripts/preview_live_orders.py --signals reports/forward/..._signals.csv --enforce-live-risk

# Risk-Check bewusst deaktivieren
python scripts/preview_live_orders.py --signals reports/forward/..._signals.csv --skip-live-risk
```

---

### 4.3 `scripts/paper_trade_from_orders.py`

Purpose:
Ausführung von Orders im Paper-Trading-Modus mit vorgeschaltetem Risk-Check.

Besonderheiten:

* Führt **vor** Paper-Execution den Risk-Check aus.
* Nutzt `starting_cash` zur Berechnung von `max_daily_loss_pct`.

Verhalten:

* Erfolgreicher Risk-Check → Paper-Trade wird ausgeführt.
* Verletzung + `--enforce-live-risk` → Abbruch (Exit Code 1), keine Ausführung.
* Verletzung ohne Enforcement → Warnung, Ausführung läuft weiter.

Beispiel:

```bash
python scripts/paper_trade_from_orders.py \
  --orders reports/live/preview_..._orders.csv \
  --start-cash 10000 \
  --enforce-live-risk
```

---

### 4.4 `scripts/check_live_risk_limits.py`

Purpose:
Eigenständiges Tool, um die Live-Risk-Limits und aktuellen Metriken zu prüfen, **ohne** Orders auszuführen.

Features:

* Lädt `config.toml` und erstellt `LiveRiskLimits` via `from_config()`.
* Führt einen Risk-Check basierend auf aktuellem Status (PnL, Exposure, Positions etc.) durch.
* Schreibt einen Eintrag in die Registry mit `run_type = "live_risk_check"`.
* Gibt Metriken und eventuelle Verletzungen im CLI-Output aus.

Beispiel:

```bash
python scripts/check_live_risk_limits.py --orders reports/live/preview_..._orders.csv
```

Bekannter Hinweis:

* Der `--help`-Flag ist von einem bekannten `argparse`-Bug unter Python 3.9 betroffen.
* **Workaround**: Skript einfach normal mit Parametern aufrufen; die eigentliche Funktionalität ist nicht betroffen.

---

## 5. Registry-Logging

Folgende Aspekte werden in der Registry festgehalten:

* Bei `scripts/check_live_risk_limits.py`:

  * `run_type = "live_risk_check"`
  * Relevante Metriken (z. B. `daily_pnl`, `total_exposure_notional`, `max_symbol_exposure_notional`, `open_positions`, ...)
  * Ergebnis (`allowed = true/false`, Anzahl und Art der Verletzungen)

* Bei Risk-Checks, die innerhalb anderer Skripte stattfinden, können ebenfalls Metriken und Status optional geloggt werden, um spätere Analysen und Monitoring zu ermöglichen.

---

## 6. Typische Workflow-Beispiele

### 6.1 Schnellcheck der aktuellen Risikosituation

```bash
python scripts/check_live_risk_limits.py --orders reports/live/preview_..._orders.csv
```

Ergebnis:

* Konsolen-Output mit Metriken und möglichen Limitverletzungen.
* Registry-Eintrag mit `run_type = "live_risk_check"`.

---

### 6.2 Orders prüfen, ohne sie auszuführen (Preview)

```bash
python scripts/preview_live_orders.py \
  --signals reports/forward/..._signals.csv \
  --enforce-live-risk
```

Mögliche Ausgabe bei Verletzung:

```text
Live-Risk-Verletzungen:
  - max_order_notional_exceeded(max=1000.00, observed=1500.00)

ValueError: Live-Risk-Limits verletzt (preview_live_orders) und --enforce-live-risk gesetzt.
```

---

### 6.3 Paper-Trade mit vorgeschaltetem Risk-Check

```bash
python scripts/paper_trade_from_orders.py \
  --orders reports/live/preview_..._orders.csv \
  --start-cash 10000 \
  --enforce-live-risk
```

* Bei Limitverletzung → **Abbruch vor Order-Ausführung**.
* Bei Erfolg → Paper-Execution gemäß Konfiguration.

---

## 7. Validierung & Tests

Kurz zusammengefasst getestete Szenarien:

* **Warnung bei Verletzung** (Standardmodus ohne `--enforce-live-risk`):

  * Beispiel: `max_order_notional_exceeded (max=1000.00, observed=1500.00)`
  * Skript läuft weiter, aber markiert das Risiko klar.

* **Enforcement**:

  * Mit `--enforce-live-risk`: Skript bricht bei Verletzung mit Exit Code 1 ab.

* **Skip-Flag**:

  * Mit `--skip-live-risk`: Risk-Check wird bewusst komplett übersprungen.

* **Registry-Logging**:

  * `run_type = "live_risk_check"`-Einträge sind in der Registry erstellt.

* **Paper-Trade**:

  * Risk-Check wird vor Ausführung durchgeführt.
  * `starting_cash` wird berücksichtigt für `max_daily_loss_pct`.

---

## 8. Nächste sinnvolle Erweiterungen (Ideen)

* Konfigurierbare **Severity-Stufen** pro Limit (z. B. nur Warnung vs. harter Abbruch).
* Zusätzliche Limits:

  * Maximaler Intraday-Drawdown auf Basis intraday-Equity.
  * Rate-Limits (max. Orders / Minute).
* Export der Risk-Check-Ergebnisse an externe Monitoring-Systeme (Prometheus, Logs, UI).
* Unit-Tests für typische Edge-Cases (kein PnL, kein Exposure, extrem hohe Orders, viele Symbole).
