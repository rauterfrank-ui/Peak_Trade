# Peak_Trade – Registry, Engine & End-to-End-Backtests

> Stand: Erste produktionsreife Version der Registry‑ und Engine‑Integration ist umgesetzt.

---

## 1. Kontext & Ziel

**Peak_Trade** ist ein modularer Backtesting‑ und Trading‑Framework‑Prototyp mit dem Ziel:

- Strategien **sauber getrennt** nach:
  - Data‑Layer
  - Strategy‑Layer
  - Risk-/Position‑Sizing
  - Engine
  - Config/Registry
- Portfolios aus **mehreren Strategien** über eine zentrale Registry in `config.toml` zu steuern.
- Reproduzierbare **End‑to‑End‑Backtests** mit klaren CLI‑Skripten zu ermöglichen.

Dieses Dokument fasst den aktuellen Stand zusammen und dient als „Einstiegspunkt“, wenn du später wieder einsteigst.

---

## 2. Aktueller Stand (Checkliste)

### 2.1 Architektur / Code

- ✅ **Data‑Layer** (realistische Daten)
  - Module in `src/data/` (z. B. Loader, Normalizer, Cache, Kraken‑Integration).
  - Pipelines, die OHLCV‑Daten in ein einheitliches DataFrame‑Format bringen.

- ✅ **Strategy‑Layer**
  - Strategien leben in `src/strategies/` und haben eine klare API (z. B. `generate_signals(ohlcv, cfg)`).
  - Mehrere Beispiel‑Strategien (Trend, Mean‑Reversion, etc.).

- ✅ **Registry‑Layer**
  - Zentrale Definition aller Strategien und Portfolios in `config/config.toml`.
  - Registry‑Modul `src/core/config_registry.py` kapselt Zugriff/Filter/Selektion.
  - Doku und Demo:
    - `README_REGISTRY.md` (Quick Start)
    - `docs/CONFIG_REGISTRY_USAGE.md` (API‑Referenz & Beispiele)
    - `scripts/demo_config_registry.py` (Registry‑Demo)

- ✅ **Engine‑Integration**
  - Backtest‑Engine (`src/backtest/engine.py`) kann Strategien nicht nur einzeln, sondern **über Registry & Portfolio** ansteuern.
  - Registry‑Helper werden genutzt, um:
    - aktive Strategien,
    - zugehörige Config‑Blöcke,
    - Portfolio‑Gewichte
    zu kombinieren.

- ✅ **End‑to‑End‑Backtest**
  - Neues Skript (z. B. `scripts/run_registry_portfolio_backtest.py`) für „echte“ Backtests:
    - liest Config & Registry,
    - lädt Marktdaten über den Data‑Layer,
    - ruft die Engine für ein ganzes Portfolio auf,
    - berechnet Kennzahlen und gibt sie aus.

- ✅ **Demo‑Backtests**
  - `scripts/demo_registry_backtest.py` zeigt die Registry‑Integration mit künstlichen Daten:
    - Läuft vollständig durch.
    - Alle 4 Demo‑Szenarien funktionieren.
    - Keine Trades in der Demo (erwartbar, weil Random‑Daten selten Entry‑Signale triggern).

- ⚠️ **Pandas FutureWarnings**
  - Es existiert mindestens eine FutureWarning (z. B. durch Rolling/Resample‑Aufrufe).
  - Nicht kritisch für die Funktionalität, aber langfristig ein Aufräum‑Punkt.

---

## 3. Architektur‑Überblick (logisch)

### 3.1 Komponenten

- **Config / Registry**
  - `config/config.toml`
  - `src/core/config.py` → `load_config()`
  - `src/core/config_registry.py` → Registry‑/Portfolio‑Helper

- **Data‑Layer (`src/data/`)**
  - Verantwortlich für:
    - Laden (CSV, Kraken, …)
    - Normalisieren
    - Resampling
    - Caching (z. B. Parquet)

- **Strategy‑Layer (`src/strategies/`)**
  - Strategien mit sauberer Signatur, z. B.:
    ```python
    class SomeStrategy(StrategyBase):
        def generate_signals(self, ohlcv: pd.DataFrame, cfg: dict) -> tuple[pd.Series, dict]:
            ...
    ```
  - Signale sind typischerweise `{-1, 0, +1}` (short, flat, long).

- **Engine & Stats**
  - `src/backtest/engine.py` – orchestriert:
    - Daten → Strategie → Risk/Position‑Sizing → Trades/Equity
  - `src/backtest/stats.py` – Kennzahlen und Auswertung:
    - z. B. Equity‑Kurven, Drawdowns, Sharpe, Winrate (abhängig von deiner Implementierung).

- **Skripte (`scripts/`)**
  - `demo_config_registry.py` – Registry lesen, Strategien/Portfolios inspizieren.
  - `demo_registry_backtest.py` – Demo‑Backtest mit Registry (künstliche Daten).
  - `run_registry_portfolio_backtest.py` – End‑to‑End‑Portfolio‑Backtest mit realistischen Daten.

---

## 4. Registry & Portfolio – Konzept

### 4.1 TOML‑Struktur (vereinfacht)

In `config/config.toml`:

- **Meta‑Registry (optional):**
  ```toml
  [strategies]
  default_timeframe = "1h"
  default_base_risk = 0.01
  ```

- **Pro Strategie ein Registry‑Eintrag:**
  ```toml
  [strategies.ma_crossover]
  enabled        = true
  config_key     = "strategy.ma_crossover"
  timeframe      = "1h"
  group          = "trend"
  default_weight = 0.20
  ```

  Wichtige Felder:
  - `enabled`       → globales Ein/Aus.
  - `config_key`    → Verknüpfung zum Parameter‑Block, z. B. `[strategy.ma_crossover]`.
  - `timeframe`     → Meta‑Info (Filter, UI, Logging).
  - `group`         → z. B. `trend`, `mean_reversion`, `cycle`, `any`.
  - `default_weight`→ Fallback‑Gewichtung, falls das Portfolio nichts spezifischer vorgibt.

- **Strategie‑Parameter‑Blöcke (Existieren bereits):**
  ```toml
  [strategy.ma_crossover]
  fast_ma   = 10
  slow_ma   = 30
  ma_type   = "sma"
  risk_per_trade = 0.01
  ```

- **Portfolio‑Definition:**
  ```toml
  [portfolio]
  base_currency = "EUR"
  rebalance     = "daily"

  [portfolio.default]
  strategies = [
    "ma_crossover",
    "momentum_1h",
    "rsi_strategy",
    "macd",
  ]

  [portfolio.default.weights]
  ma_crossover = 0.30
  momentum_1h  = 0.25
  rsi_strategy = 0.25
  macd         = 0.20
  ```

> **Merke:**  
> Registry (`[strategies.*]`) beschreibt **was vorhanden und aktiv ist**,  
> `[strategy.*]` enthält die **Detailparameter**,  
> `[portfolio.*]` legt fest, **welche Strategien wie kombiniert** werden.

---

## 5. Engine‑Integration über die Registry

Die neue Engine‑Integration folgt logisch etwa diesem Ablauf:

1. `cfg = load_config()` lädt `config/config.toml` als Dict.
2. `config_registry` hilft, die passenden Strategien für ein Portfolio zu bestimmen, z. B.:
   - `portfolio_name = "default"`
   - alle Strategien in `portfolio.default.strategies`
   - gefiltert nach `enabled = true`
3. Für jede Strategie:
   - Registry‑Eintrag aus `cfg["strategies"][name]` lesen.
   - `config_key` aus Registry holen → z. B. `"strategy.ma_crossover"`.
   - Parameter‑Block unter `cfg[config_key]` auflösen → Strategie‑Config (`strat_cfg`).
4. Engine baut die Strategie‑Instanz:
   - z. B. via Mapping `{ "ma_crossover": MACrossover, ... }`.
5. Engine:
   - berechnet Signale (`generate_signals`).
   - wendet Risk-/Position‑Sizing an.
   - erzeugt Trades/Equity.
6. `stats` berechnet Kennzahlen, die das End‑to‑End‑Script ausgibt oder in Dateien schreibt.

Die genaue Funktionssignatur (z. B. `run_portfolio_from_config(...)`) hängt von deiner aktuellen Implementierung ab, ist aber konzeptionell an diesen Flow gebunden.

---

## 6. End‑to‑End‑Backtest‑Script

**Datei:**  
`scripts/run_registry_portfolio_backtest.py`

### 6.1 Typischer CLI‑Aufruf

Beispiel‑Aufrufe (die genauen Optionen hängen von deiner Implementierung ab, typisches Muster):

```bash
# 1) Portfolio-Backtest mit Default-Portfolio und Standard-Zeitraum
python scripts/run_registry_portfolio_backtest.py

# 2) Portfolio spezifisch, Symbol/Zeitraum explizit
python scripts/run_registry_portfolio_backtest.py     --portfolio default     --symbol BTC/EUR     --start 2021-01-01     --end 2022-01-01

# 3) Mit Output-Directory für Ergebnisse
python scripts/run_registry_portfolio_backtest.py     --portfolio default     --symbol BTC/EUR     --start 2021-01-01     --end 2022-01-01     --output-dir reports/btc_default_2021
```

Typische Aufgaben des Scripts:

- `argparse` für CLI‑Parameter.
- `load_config()` + Registry/Portfolio auswerten.
- Marktdaten über den Data‑Layer laden.
- Engine aufrufen (für alle Strategien im Portfolio).
- Kennzahlen je Strategie + Gesamtportfolio berechnen.
- Ergebnis:
  - verständliche Ausgabe im Terminal,
  - optional CSV/JSON im Output‑Verzeichnis.

---

## 7. Demo‑Skripte

### 7.1 `scripts/demo_config_registry.py`

- Lädt `config/config.toml`.
- Zeigt die Registry‑Struktur:
  - alle Registry‑Einträge,
  - aktive Strategien,
  - Mapping auf `config_key`.
- Dient als **Sanity‑Check** für die Struktur von `config.toml`.

### 7.2 `scripts/demo_registry_backtest.py`

- Verwendet die Registry‑Integration der Engine.
- Arbeitet mit **künstlichen/zufälligen Daten**.
- Zeigt:
  - Dass die Engine sauber mit Registry + Portfolio zusammenspielt.
  - Warum 0 %‑Returns oder keine Trades bei Random‑Daten erwartbar sind.
- Aktueller Status:
  - Script läuft vollständig durch.
  - Alle Demo‑Szenarien funktionieren.
  - Pandas FutureWarnings sind vorhanden, aber nicht kritisch.

---

## 8. Operator‑Guide – „Wie fahre ich einen echten Backtest?“

### 8.1 Minimal‑Checkliste

1. **Repo & venv:**
   - Sicherstellen, dass das venv aktiv ist:
     ```bash
     cd /Users/frnkhrz/Peak_Trade
     source .venv/bin/activate   # oder Äquivalent auf deinem System
     ```

2. **Config prüfen:**
   - In `config/config.toml`:
     - Ziel‑Portfolio unter `[portfolio.<name>]`.
     - Strategien in `[strategies.*]` auf `enabled = true` setzen, die du nutzen willst.
     - Daten‑/Symbol‑Settings passend setzen (falls dort hinterlegt).

3. **Probelauf (kurzer Zeitraum):**
   - z. B.:
     ```bash
     python scripts/run_registry_portfolio_backtest.py          --portfolio default          --symbol BTC/EUR          --start 2022-01-01          --end 2022-03-01
     ```
   - Prüfen:
     - Läuft das Script durch?
     - Werden sinnvolle Kennzahlen angezeigt?
     - Gibt es Trades?

4. **„Großen“ Backtest fahren:**
   - Zeitraum erweitern.
   - Optional `--output-dir` setzen, um Ergebnisse zu versionieren.

5. **Ergebnisse interpretieren:**
   - Equity‑Kurven & Kennzahlen je Strategie.
   - Gesamt‑Portfolio‑Return.
   - Besonders achten auf:
     - MaxDD
     - Anzahl Trades
     - Winrate
     - ggf. Sharpe

---

## 9. Nächste mögliche Schritte (Roadmap‑Ideen)

Die folgende Liste dient als Fahrplan, wenn du später am Projekt weiterarbeitest:

1. **Baseline‑Portfolios definieren**
   - z. B.:
     - `portfolio.default` (gemischtes Set)
     - `portfolio.trend_only`
     - `portfolio.mean_reversion_only`
   - Diese als „Referenzläufe“ etablieren.

2. **Backtest‑Ergebnisse versionieren**
   - Standard‑Output‑Ordner z. B. `reports/`.
   - Pro Lauf:
     - Datum + Commit‑Hash + Portfolio‑Name im Pfad/Dateinamen.
     - Summary als JSON/CSV ablegen.

3. **CI/Regression‑Tests**
   - Kleinen, schnellen Backtest in `pytest` integrieren.
   - Sicherstellen, dass Strategien‑Änderungen keine massiven Metrik‑Ausreißer verursachen.

4. **Qualitäts‑Checks**
   - Warnungen loggen, wenn:
     - kaum oder keine Trades generiert wurden.
     - Datenmenge zu gering ist.
   - Optional: einfache „Sanity Rules“:
     - z. B. „wenn Total Return > +1000 % auf kurzen Zeitraum → Flag setzen“.

5. **Doku abrunden**
   - In der Haupt‑`README.md`:
     - Kurzer Abschnitt „Backtests fahren“.
     - Verweis auf `README_REGISTRY.md` & `docs/CONFIG_REGISTRY_USAGE.md`.
   - Optional: Diagramm, das Data‑Layer → Strategy‑Layer → Engine → Stats visualisiert.

---

## 10. Notizen zum aktuellen Git‑Stand

- Registry‑Änderungen & Doku sind bereits sauber committet:
  - Commit für Registry & Engine‑Integration.
  - Separater Commit für Projektübersicht/Dokumentation.
- Working Directory:
  - war zuletzt nur mit `.claude/settings.local.json` als lokale Änderung belegt (Editor‑/AI‑Einstellungen, nicht kritisch).

> Wenn du später wieder einsteigst, ist dieser Markdown‑Stand ein guter Startpunkt, um:
> - den Überblick zu bekommen,  
> - zu sehen, wie Registry + Engine + Skripte zusammenspielen,  
> - und gezielt an den nächsten Roadmap‑Punkten weiterzubauen.
