# Peak_Trade – Architekturübersicht

## 1. Zielbild

Peak_Trade ist ein Forschungs- und Trading-Framework mit Fokus auf:

- Backtests und Risikoauswertung auf Basis von OHLCV-Daten
- sauberes Risk-Management (Risk-per-Trade, Stops, Drawdowns)
- klar getrennte Module für Daten, Strategien, Backtests, Theorie (Quant-Finance)
- gute Erweiterbarkeit (LLM-Assist, Makro/ECM-Overlay, Pricing-Modelle)

Diese Datei beschreibt die **logische Architektur** und die **Ordnerstruktur** des Projekts.

---

## 2. Ordnerstruktur (Sollzustand)

```text
Peak_Trade/
├─ config.toml
├─ README.md
│
├─ docs/
│  ├─ armstrong_notes.md
│  ├─ trading_bot_notes.md
│  ├─ nicole_el_karoui_notes.md
│  ├─ Peak_Trade_setup_notes.md
│  └─ architecture.md              ← diese Datei
│
├─ data/                            (lokale Daten, z. B. CSV/Parquet)
│  └─ raw/                          (Rohdaten-Exporte, nicht ins Repo nötig)
│
├─ results/                         (Backtest-Ergebnisse)
│  ├─ backtests/                    (Equity-Curves, Trades, Stats)
│  └─ reports/                      (aggregierte Auswertungen, Plots)
│
├─ src/
│  ├─ core/
│  │  └─ config.py                  (Settings & Config-Loader)
│  │
│  ├─ data/
│  │  └─ kraken.py                  (Datenzugriff via ccxt, Caching)
│  │
│  ├─ strategies/
│  │  ├─ __init__.py
│  │  └─ ma_crossover.py            (erste Beispiel-Strategie)
│  │
│  ├─ risk/
│  │  ├─ __init__.py
│  │  └─ position_sizer.py          (Positionsgrößen & Risk-per-Trade)
│  │
│  ├─ backtest/
│  │  ├─ __init__.py
│  │  ├─ engine.py                  (Backtest-Engine, bar-für-bar)
│  │  └─ stats.py                   (Sharpe, MaxDD, Trade-Stats, Reports)
│  │
│  ├─ features/
│  │  └─ ecm.py                     (Armstrong/ECM-Eventfenster & Flags)
│  │
│  └─ theory/
│     ├─ stochastics.py             (SDE-/Pfad-Simulationen, GBM/Heston)
│     └─ pricing.py                 (Black–Scholes & Erweiterungen)
│
├─ scripts/
│  ├─ run_ma_realistic.py           (Realistic-Backtest für MA-Strategie)
│  └─ run_ma_vectorized.py          (optional: schneller Test-Backtest)
│
└─ tests/
   ├─ test_backtest_dummy.py        (Dummy-Daten-Smoketest)
   └─ test_stats_dummy.py           (Unit-Tests für Kennzahlen)
```

---

## 3. Kernmodule und Verantwortlichkeiten

### 3.1 `src/core/config.py`

Aufgaben:

- Laden von `config.toml`
- Validierung und Strukturierung in Pydantic-Modelle (`Settings`, `BacktestConfig`, `RiskConfig`, `ExchangeConfig`, `StrategyConfig`)
- Hilfsfunktion `get_strategy(settings, name)`, um eine Strategie-Konfiguration abzurufen.

Damit wird sichergestellt, dass alle Module (Backtest, Risk, Daten, Strategien) einen **zentralen, typisierten** Zugang zu Einstellungen haben.

---

### 3.2 `src/data/` – Daten- & Exchange-Layer

**`kraken.py`**

- Stellt `get_kraken_client()` bereit:
  - baut einen ccxt-Kraken-Client basierend auf `Settings.exchange`
  - berücksichtigt Rate Limits und (später) API-Keys / Testnet

- Stellt `fetch_ohlcv_df(symbol, timeframe, limit, since_ms, use_cache)` bereit:
  - holt OHLCV-Daten von Kraken
  - speichert/liest optional einen Parquet-Cache unter `backtest.data_dir`
  - gibt einen `DataFrame` mit `DatetimeIndex` und Spalten `open, high, low, close, volume` zurück

Später können hier weitere Datenquellen ergänzt werden (andere Börsen, CSV-Loader, Onchain, Makro-Daten).

---

### 3.3 `src/strategies/` – Strategielogik

**`ma_crossover.py`**

- Implementiert eine einfache Moving-Average-Crossover-Strategie:
  - Input: OHLCV-DataFrame
  - Output: zeitdiskrete Signale (z. B. `1` = long, `0` = flat)
- Parameter (z. B. `fast_window`, `slow_window`, `stop_pct`) kommen aus `config.toml`.

Später können weitere Strategiemodule hinzukommen, z. B. Breakout, Mean Reversion, Vol-Strategien etc.

---

### 3.4 `src/risk/` – Risk- & Money-Management

**`position_sizer.py`**

- Kern-Aufgabe: Berechnung der Positionsgröße auf Basis von
  - aktuellem Kontostand (`equity`)
  - Entry-Preis & Stop-Loss-Level
  - konfiguriertem `risk_per_trade` (z. B. 1 %)
  - Limits wie `max_position_size` (max. Anteil des Kontos pro Position)
  - `min_position_value` (untere Grenze für Trade-Größen)

- Gibt ein Result-Objekt zurück (`PositionSizeResult`), das neben der Größe auch angibt, ob die Position aufgrund von Constraints abgelehnt wurde.

Dieses Modul ist die Grundlage für alle realistischen Backtests und später für Live-Trading.

---

### 3.5 `src/backtest/` – Backtest-Engine & Kennzahlen

**`engine.py`**

- Führt den eigentlichen Backtest aus:
  - holt Strategie-Parameter aus `Settings`
  - ruft die Strategiefunktion (z. B. `ma_crossover.generate_signals`) auf
  - läuft Bar-für-Bar über den OHLCV-DataFrame
  - verwaltet Equity, offene Positionen, Ein- und Ausstiege
  - nutzt `position_sizer.calc_position_size()` für realistisches Risk-Management
  - erzeugt eine Equity-Curve und eine Liste von Trades in strukturierter Form

- Liefert ein `BacktestResult` mit:
  - `equity_curve` (`pd.Series`)
  - `trades` (`pd.DataFrame`)
  - `stats` (Dict mit Kennzahlen)

**`stats.py`**

- Berechnet Kennzahlen wie:
  - Gesamt-Return
  - Maximaler Drawdown
  - Sharpe Ratio (annualisiert)
  - Calmar Ratio
  - Trade-basierte Metriken (Anzahl Trades, Win Rate, Profit Factor, Average Win/Loss, Expectancy)
- Bietet eine Funktion `print_stats_report(stats)`, die einen gut lesbaren Text-Report ausgibt.

---

### 3.6 `src/features/ecm.py` – Armstrong/ECM-Overlay

- Definiert eine Struktur für ECM-Turning-Points (Datum, Label, Fenstergröße).  
- Fügt einem OHLCV-DataFrame Flag-Spalten hinzu, z. B.:
  - `ecm_window` (True/False innerhalb des Event-Fensters)
  - `ecm_label` (z. B. `major_high`, `minor_low`)

So können Strategien oder Auswertungen später konditional auf ECM-Regime reagieren.

---

### 3.7 `src/theory/` – El-Karoui-/Quant-Theorie

**`stochastics.py`**

- SDE-/Prozess-Simulationen (z. B. GBM, später Heston)  
- Monte-Carlo-Pfade für Underlyings → theoretische Risikostudien für Strategien

**`pricing.py`**

- Pricing-Funktionen (z. B. Black–Scholes für Calls/Puts)  
- später Erweiterungen Richtung lokaler/stochastischer Volatilität, BSDE-Ansätze, Zins-/Credit-Modelle

Diese Module sind die Brücke zur Theorie-Schiene (Nicole El Karoui) und erlauben langfristig ein Zusammenspiel von Modellwelt und empirischer Backtest-Welt.

---

## 4. Scripte & Tests

### 4.1 `scripts/`

Typische Beispiele:

- `run_ma_realistic.py`  
  - Lädt Settings
  - holt OHLCV-Daten (Dummy oder von Kraken)
  - startet einen Realistic-Backtest der MA-Strategie
  - gibt den Stats-Report aus und speichert Ergebnisse in `results/backtests/`

- `run_ma_vectorized.py` (optional)  
  - einfacher, vektorisierter Backtest ohne detailliertes Risk-Management
  - nur für schnelle Experimente, nicht für Risk-Entscheidungen

### 4.2 `tests/`

- `test_backtest_dummy.py`  
  - lässt den Realistic-Backtest auf Dummy-Daten laufen und prüft, dass eine Equity-Curve und Stats entstehen.

- `test_stats_dummy.py`  
  - prüft, dass `compute_all_stats()` auf einfachen Beispiel-Equity-Kurven sinnvolle Werte liefert.

Ziel: früh Bugs finden, bevor echte Exchange-Daten und Geld im Spiel sind.

---

## 5. Typischer Datenfluss

1. **Config laden**  
   `Settings = load_config("config.toml")`

2. **Daten beschaffen**  
   - Dummy-Daten für Entwicklung, oder  
   - reale OHLCV-Daten via `fetch_ohlcv_df()`

3. **Features & Regime** (optional)  
   - ECM-Flags über `features/ecm.py`  
   - spätere Makro-/Sentiment-Features

4. **Strategie-Signale erzeugen**  
   - z. B. `ma_crossover.generate_signals(df, params)`

5. **Backtest ausführen**  
   - `BacktestEngine.run_realistic(df, strategy_name)`  
   - nutzt Risk- und Positionsgrößen-Logik

6. **Stats & Reports**  
   - `compute_all_stats()` + `print_stats_report()`  
   - Speicherung in `results/backtests/` und `results/reports/`

---

## 6. Roadmap-Hinweise (Architektur-Ebene)

- **Kurzfristig:**
  - Realistic-Backtest auf echten Daten (Kraken) stabilisieren
  - Grundstrategie(n) + Stats zuverlässig machen
- **Mittelfristig:**
  - weitere Strategien, bessere Feature-Sets (inkl. ECM)
  - visuelle Dashboards / Plots (Equity, Drawdown, Regime)
- **Langfristig:**
  - Theorie-Module (El Karoui) ausbauen
  - Pricing-/Risk-Modelle mit Backtests verknüpfen
  - Teil-automatisierte Workflows mit LLM-Co-Piloten (Code-Generierung, Reports)

Diese Architektur soll es ermöglichen, Stück für Stück von einem
„Spielplatz“ für Strategien zu einem robusteren Research- und
Trading-Framework zu wachsen.
