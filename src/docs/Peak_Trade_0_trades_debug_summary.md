# Peak_Trade – Projektzustand & aktuelles Problem (0 Trades)

## 1. Projektziel

Aufbau eines **Trading-/Research-Frameworks „Peak_Trade“** mit:

- sauberen Backtests (OHLCV, MA-Crossover als Beispiel)
- **Risk-Management** (Risk-per-Trade, Stop-Loss, Positionsgrößen)
- klarer Modulstruktur (`core`, `data`, `risk`, `strategies`, `backtest`, `features`, `theory`)
- später: ECM-/Makro-Overlay, Armstrong/El-Karoui-Themen, Live-Trading

---

## 2. Projektstruktur & Infrastruktur (fertig, ~100 %)

Wichtige Dateien & Ordner:

- `config.toml` – zentrale Konfiguration
- `README.md` – Setup & erster Backtest
- `.gitignore`, `requirements.txt` – Repo/Env sauber
- `docs/`
  - `architecture.md`
  - `Peak_Trade_setup_notes.md`
  - `armstrong_notes.md`
  - `trading_bot_notes.md`
  - `nicole_el_karoui_notes.md`
- `src/`
  - `core/` – Config-System
  - `data/` – Marktdaten (z.B. Kraken)
  - `risk/` – Position Sizing
  - `strategies/` – Strategien (MA-Crossover)
  - `backtest/` – Engine + Stats
  - `features/`, `theory/` – für ECM/El-Karoui etc. reserviert
- `scripts/`
  - `run_ma_realistic.py` – Script für realistischen Backtest
- `tests/`
  - `test_basics.py` – Basis-Test

Alle relevanten Verzeichnisse haben `__init__.py` → saubere Python-Packages.

---

## 3. Config-System (funktioniert, inkl. tomli)

- `src/core/config.py`:
  - Pydantic-`Settings`-Modell für:
    - `risk` (z.B. `risk_per_trade`, `max_position_size`, `min_position_value`)
    - `backtest` (z.B. `initial_cash`, `results_dir`, `data_dir`)
    - `strategy` (Dictionary mit Strategy-Configs, z.B. `momentum_1h` / `ma_crossover`)
  - Funktionen:
    - `load_settings_from_file(...)` (lädt `config.toml` via `tomli`)
    - **`get_config(force_reload=False)`** mit globalem Cache
    - **`get_strategy_cfg(name: str)`** → holt eine StrategyConfig mit guter Fehlermeldung
- `tomli` ist installiert und importierbar (`tomli OK, Version: 2.3.0`).
- Test:

  ```bash
  python -c "from src.core import get_config; cfg = get_config(); print('Risk:', cfg.risk.risk_per_trade)"
  ```

  Ausgabe z.B.: `Risk: 0.01` → Config funktioniert.

---

## 4. Kern-Module (Backtests)

### 4.1 Daten

- `src/data/kraken.py`
  - Holt OHLCV-Daten von Kraken (mit Caching)
  - Für später: echte Live- oder Historik-Backtests

### 4.2 Strategie

- `src/strategies/ma_crossover.py`
  - Enthält eine MA-Crossover-Strategie
  - Bietet mindestens `generate_signals(df, cfg)` → gibt ein Signal-`Series` (`0` = flat, `1` = long)

### 4.3 Risk / Position Sizing

- `src/risk/position_sizer.py`
  - Funktion `calc_position_size(req, max_position_pct, min_position_value)`:
    - berechnet Positionsgröße aus:
      - Konto-Eigenkapital
      - Entry-Preis
      - Stop-Preis
      - `risk_per_trade` (z.B. 1 % des Kapitals)
    - gibt `PositionSizeResult` zurück (`size`, `rejected`, `reason`)

### 4.4 Backtest-Stats

- `src/backtest/stats.py`
  - `compute_all_stats(equity, trades_df, periods_per_year)` mit:
    - `total_return`, `max_drawdown`, `sharpe_ratio`, `calmar_ratio`
    - trade-basierte Kennzahlen: `total_trades`, `win_rate`, `profit_factor`, `expectancy`, etc.
  - `print_stats_report(stats)` formatiert den Report im Terminal

### 4.5 Engine

- `src/backtest/engine.py`
  - **Realistic Mode**:
    - bar-für-bar Backtest mit Stop-Loss & Position Sizing
    - erzeugt:
      - `equity_curve` (Series)
      - `trades` (DataFrame mit `entry_time`, `exit_time`, `entry_price`, `exit_price`, `size`, `pnl`, `exit_reason`)
      - `stats` (Dict aus `compute_all_stats`)
  - **Vectorized Mode**:
    - schnell, ohne Risk-Management (All-In), eher für Experimente
  - Ergebnisse werden in `results/` als CSV/JSON gespeichert

### 4.6 Backtest-Runner

- `scripts/run_ma_realistic.py`:
  - Lädt Config (`get_config()`)
  - Erzeugt Dummy- oder Kraken-Daten
  - Ruft die Engine im Realistic Mode auf
  - Gibt den Backtest-Report im Terminal aus

---

## 5. Aktueller Status: Report zeigt **0 Trades**

Ein realistischer Backtestlauf (Dummy-Daten) liefert aktuell:

- **Equity Metriken**
  - Start Equity: 10.000
  - End Equity: 10.000
  - Total Return: 0 %
  - Max Drawdown: 0 %
- **Risk-Adjusted**
  - Sharpe: 0
- **Trade Statistiken**
  - Total Trades: 0
  - Win Rate: 0 %
  - Profit Factor: 0
- **Live-Trading-Validierung**:
  - Strategie nicht freigegeben (u.a. wegen 0 Trades)

🧩 Fazit: Infrastruktur & Stats funktionieren, aber es werden **keine Trades eröffnet**.

---

## 6. Vermutete Ursachen für „0 Trades“

Es gibt zwei Hauptkandidaten:

1. **Strategie-Signale**  
   - `generate_signals(df, cfg)` liefert möglicherweise nur `0` (nie Long-Signal).
   - Dann entstehen keine Entry/Exit-Situationen.

2. **Engine / Risk-Schicht**
   - Signale sind da, aber:
     - der Position Sizer lehnt jede Position ab (`rejected=True`), oder
     - die Entry/Exit-Logik in der Engine wird nie getriggert (z.B. wegen Index-Verschiebung), oder
     - Trades werden nicht korrekt in die Liste geschrieben.

---

## 7. Geplanter Debug-Ansatz

### Schritt 1 – Strategie-Signale isoliert prüfen

Mit einem kleinen Skript:

- Dummy-OHLCV-Daten generieren (per `numpy`/`pandas`)
- Strategy-Config laden:

  ```python
  from src.core import get_strategy_cfg
  cfg = get_strategy_cfg("momentum_1h")  # oder "ma_crossover"
  ```

- Signale berechnen:

  ```python
  from src.strategies.ma_crossover import generate_signals
  signals = generate_signals(df, cfg)
  ```

- Verteilung & Wechsel prüfen:

  ```python
  print(signals.value_counts())
  print(signals.diff().value_counts())
  ```

Interpretation:

- Nur `0` in `value_counts()` → Ursache liegt in der Strategie (keine Long-Signale).
- `0` und `1` vorhanden + `diff()` enthält `+1`/`-1` → Strategie ok, dann weiter zur Engine.

### Schritt 2 – Position Sizer & Engine prüfen (falls Signale ok)

- In `calc_position_size(...)` temporär Debug-Prints einbauen:
  - zeigen, ob `rejected=True` ist und warum (z.B. `min_position_value` zu hoch)
- In der Backtest-Schleife der Engine:
  - `sig_prev`, `sig`, `position_size` pro Bar ausgeben
  - im Entry-Block (`sig_prev == 0 and sig == 1`) prüfen, ob dieser Zweig jemals erreicht wird
  - sicherstellen, dass im Exit/Stop-Loss-Fall wirklich `trades.append(...)` aufgerufen wird

---

## 8. Ziel für den nächsten Schritt

Im nächsten Chat soll geholfen werden:

1. Ein minimales Debug-Snippet zu bauen, das:
   - Dummy-Daten generiert
   - Strategy-Config lädt
   - `generate_signals` ausführt
   - `value_counts()` und `diff()` ausgibt
2. Je nach Ergebnis:
   - entweder die **Strategie** so anzupassen, dass sinnvolle Signale entstehen
   - oder die **Engine-/Risk-Logik** so zu korrigieren, dass aus den Signalen auch wirklich Trades generiert werden
