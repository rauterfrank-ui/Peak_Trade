
# Peak_Trade – Roadmap (logische Reihenfolge)

Ziel: Das Peak_Trade-Framework von einem Set einzelner Bausteine zu einem runden **MVP** bringen, mit dem reproduzierbare Backtests, Registry-Logging und Paper-Trades (inkl. Live-Risk-Limits) möglich sind.

---

## Phase 1 – End-to-End-Backtest sauber machen (höchste Priorität)

**Ziel:** Ein einziger Einstiegspunkt (Script), der einen vollständigen Backtest von Daten → Strategie → Engine → Stats → Registry ausführt.

### Aufgaben

1. **Backtest-Engine & Stats abrunden**
   - `src/backtest/engine.py`:
     - Edge-Cases absichern (leere Trades, NaNs, Zeiträume ohne Signale, Timezone-Themen falls relevant).
     - Einheitliche Schnittstelle: Input (Preis-/Signal-Daten), Output (Trades, Equity, Meta-Daten).
   - `src/backtest/stats.py`:
     - Standard-Kennzahlen fix definieren (z. B. CAGR, Max Drawdown, Sharpe, Winrate, Profit-Faktor, Max Losing Streak).
     - Einheitliches Output-Format (z. B. `dict` oder kleines Dataclass-Objekt, optional zusätzlich `DataFrame`).

2. **Zentrales Backtest-Script erstellen**
   - Neues Script, z. B. `scripts/run_backtest.py`, das:
     - `config.toml` lädt.
     - Die Data-Pipeline (`src/data/*`) nutzt.
     - Eine Strategie aus dem Strategy-Layer lädt.
     - Die Backtest-Engine aufruft.
     - Stats in der Konsole ausgibt.
     - Ergebnis + Meta-Daten in der Registry loggt.

3. **Warnings & kleine Bugs fixen**
   - Bekannte Pandas-FutureWarnings und kleinere Unsauberkeiten (z. B. Type-Warnungen, SettingWithCopy) bereinigen.
   - Sicherstellen, dass Demo-Skripte ohne Warnings durchlaufen (oder nur mit bewusst akzeptierten Hinweisen).

**Ergebnis Phase 1:**  
Du hast **einen** klaren Befehl für einen vollständigen Backtest, inkl. Stats und Registry-Eintrag.

---

## Phase 2 – Registry & Experiments auf 90–100 % bringen

**Ziel:** Alle Runs (Backtest, Risk-Checks, Paper-Trades) sind in der Registry sauber und einheitlich nachvollziehbar.

### Aufgaben

1. **Konventionen für `run_type` & Meta-Daten**
   - Feste `run_type`-Werte definieren, z. B.:
     - `backtest`
     - `live_risk_check`
     - `paper_trade`
   - Standard-Felder für Meta-Daten festlegen, z. B.:
     - `strategy_name`, `config_hash`, `data_source`, `start_date`, `end_date`, `timeframe`, `notes`.

2. **Registry-Helper-Funktionen bauen**
   - Datei(en) im Registry-Modul (z.B. unter `src/`):
     - `log_backtest_result(result, meta)`
     - `log_live_risk_check(result, meta)`
     - `log_paper_trade_run(result, meta)`
   - Ziel: überall denselben Weg nutzen, um Runs zu loggen.

3. **Analyse-Skript für Experiments**
   - Script z. B. `scripts/list_experiments.py` oder `scripts/show_experiment.py`:
     - Experiments nach `run_type`, Datum, Strategie filtern.
     - Stats von ausgewählten Runs anzeigen (Kurzsummary in der Konsole).
     - Optional Export nach CSV/Parquet.

**Ergebnis Phase 2:**  
Alle wichtigen Aktionen hinterlassen **strukturierte Spuren** in der Registry, und du kannst Runs vergleichen.

---

## Phase 3 – Strategie-Layer von 35 % → 80 %

**Ziel:** Saubere Strategie-API + mehrere Beispiel-Strategien, die produktionsnah aussehen.

### Aufgaben

1. **Strategy-Baseclass / Interface definieren**
   - Neue Datei `src/strategies/base.py`:
     - z. B. Interface:
       - `generate_signals(df: pd.DataFrame) -> pd.Series | pd.DataFrame`
     - Klar definieren, welche Spalten erwartet und welche Signale geliefert werden.

2. **Bestehende MA-Crossover-Strategie aufräumen**
   - `ma_crossover.py` an die Baseclass/Interface anpassen.
   - State-Handling, Events und Positionslogik sauber kapseln.

3. **Weitere Beispielstrategien hinzufügen**
   - Mindestens 2 zusätzliche Strategien, z. B.:
     - Breakout-Strategie (Donchian/Range-Breakout).
     - Mean-Reversion mit Volatility-Filter.
   - Ziel: unterschiedliche Stilrichtungen (Trendfolge, Mean-Reversion).

4. **Config-Anbindung für Strategien**
   - In `config.toml` pro Strategie eigenen Block bereitstellen, z. B.:
     - `[strategy.ma_crossover]`, `[strategy.breakout]`, ...
   - Backtest-Script liest aus `config.toml`, welche Strategie und welche Parameter verwendet werden sollen.

**Ergebnis Phase 3:**  
Strategien sind austauschbar, parametrierbar und lassen sich schnell erweitern.

---

## Phase 4 – Live-/Paper-Pipeline konsolidieren (inkl. Live-Risk-Limits)

**Ziel:** Der Live-/Paper-Flow ist konsistent, nutzt überall dieselbe Risk-Logik und ist in Workflows klar beschrieben.

### Aufgaben

1. **Risk-Limits konsistent in allen relevanten Scripts nutzen**
   - Sicherstellen, dass folgende Scripts dieselbe Logik und Flags verwenden:
     - `scripts/preview_live_orders.py`
     - `scripts/paper_trade_from_orders.py`
     - `scripts/check_live_risk_limits.py`
   - Flags:
     - `--enforce-live-risk`
     - `--skip-live-risk`

2. **Cash, PnL & Exposure sauber definieren**
   - Klarer Umgang mit:
     - `starting_cash`
     - Tages-PnL (aus Registry vs. lokal gerechnet)
     - Exposure-Berechnung pro Symbol und gesamt
   - Dokumentieren, welche Quelle für `max_daily_loss_pct` verwendet wird.

3. **Standard-Workflows definieren (Playbooks)**
   - Z. B.:
     - Workflow A: “Preview → Risk-Check → Paper-Trade”
       1. `preview_live_orders.py` aufrufen
       2. `check_live_risk_limits.py` laufen lassen
       3. `paper_trade_from_orders.py` mit `--enforce-live-risk`

**Ergebnis Phase 4:**  
Ein sicherer, reproduzierbarer Weg von Signal → Order → Paper-Execution mit integriertem Risk-Framework.

---

## Phase 5 – Doku & Developer Experience (DX)

**Ziel:** Das Projekt ist für dich (und andere) in kurzer Zeit wieder verständlich und benutzbar.

### Aufgaben

1. **Zentrale README / Einstiegspunkt**
   - Inhalt:
     - Kurze Projektbeschreibung.
     - “Getting Started” mit:
       - Repo clonen,
       - `.venv` anlegen und Requirements installieren,
       - `config.toml` vorbereiten,
       - ersten Backtest ausführen (`scripts/run_backtest.py`).

2. **Architektur-Übersicht**
   - Markdown-Seite, z. B. `ARCHITECTURE_OVERVIEW` (geplant; Dateiname TBD):
     - Data-Layer
     - Strategy-Layer
     - Backtest-Layer
     - Live/Paper/Risk
     - Registry
   - Einfaches Diagramm (ASCII oder später als Bild).

3. **Workflow-Dokumentation**
   - Separate Seiten/Abschnitte:
     - “End-to-End-Backtest”
     - “Paper-Trade mit Risk-Check”
     - “Neue Strategie hinzufügen”

**Ergebnis Phase 5:**  
Du hast eine klare Doku, mit der du nach Pausen sofort wieder einsteigen kannst.

---

## Phase 6 – Infrastruktur, Packaging & CI

**Ziel:** Peak_Trade verhält sich wie ein “richtiges” Python-Projekt mit Tests, CI und optional Docker.

### Aufgaben

1. **Packaging (installierbares Modul)**
   - `pyproject.toml` / `setup.cfg` erstellen.
   - Paketnamen festlegen (z. B. `peak_trade`).
   - Lokale Installation via `pip install -e .` ermöglichen.

2. **Tests & Continuous Integration**
   - `tests/`-Ordner für Unit- und Integrationstests.
   - Fokus zuerst auf:
     - Backtest-Engine,
     - Stats,
     - Strategie-Logik.
   - GitHub Actions Workflow:
     - `pytest` ausführen,
     - optional Linting (`ruff`, `black`).

3. **Optional: Docker-Image**
   - Dockerfile mit:
     - passender Python-Version,
     - Installation der Dependencies,
     - Einstiegspunkt-Script für Standard-Backtests.

**Ergebnis Phase 6:**  
Stabile Infra, einfache Reproduzierbarkeit, Basis für spätere Automatisierung und Deployment.

---

---

## Phase 7 – Exchange-Layer & Live-Daten ✓

**Ziel:** Zugriff auf echte Marktdaten via Exchange-APIs (read-only).

### Aufgaben (abgeschlossen)

1. **Exchange-Client mit CCXT**
   - Exchange-Client-Modul (siehe `src/exchange/`) – `ExchangeClient` Klasse
   - Read-only: OHLCV, Ticker, Order-Book
   - Konfiguration über `config.toml`

2. **Helper-Funktionen**
   - Exchange-Helper-Modul – Timeframe-Umrechnung, Symbol-Normalisierung

3. **Scripts**
   - `scripts/inspect_exchange.py` – Exchange-Daten inspizieren
   - `scripts/scan_markets.py` – Multi-Market-Scanner

**Ergebnis Phase 7:** ✓
Exchange-Layer für Live-Daten, integriert in Forward-Signals und Scan-Workflows.

---

## Phase 8 – Forward-Signals & Out-of-Sample Pipeline ✓

**Ziel:** Forward-Signal-Generierung mit Exchange-Daten für Out-of-Sample-Validierung.

### Aufgaben (abgeschlossen)

1. **Experiment-Registry erweitern**
   - `log_forward_signal_run()` in `src/core/experiments.py`
   - `RUN_TYPE_FORWARD_SIGNAL = "forward_signal"`

2. **Forward-Signal-Script**
   - `scripts/run_forward_signals.py` – Generiert Signale mit Exchange-Client
   - CLI: `--symbol`, `--strategy`, `--timeframe`, `--dry-run`

3. **Tests**
   - `tests/test_forward_signals_smoke.py` – 11 Smoke-Tests

**Ergebnis Phase 8:** ✓
Forward-Signals werden generiert, in Registry geloggt, und können später evaluiert werden.

---

## Phase 9 – Portfolio-Backtests & Multi-Asset Runner ✓

**Ziel:** Multi-Asset Portfolio-Backtests mit aggregierten Statistiken.

### Aufgaben (abgeschlossen)

1. **Experiment-Registry erweitern**
   - `log_portfolio_backtest_result()` in `src/core/experiments.py`
   - `RUN_TYPE_PORTFOLIO_BACKTEST = "portfolio_backtest"`

2. **Portfolio-Backtest-Script**
   - `scripts/run_portfolio_backtest.py` – Erweitert mit `--tag`, `--dry-run`
   - Aggregiert Equity-Kurven mehrerer Assets
   - Berechnet Portfolio-Statistiken (Sharpe, Drawdown)

3. **Tests**
   - `tests/test_portfolio_backtest_smoke.py` – 10 Smoke-Tests

**Ergebnis Phase 9:** ✓
Portfolio-Backtests werden vollständig geloggt, inkl. Component-Runs und Portfolio-Metriken.

---

## Phase 10 – Analytics & Reporting ✓

**Ziel:** Analytics-Layer für Registry-Aggregationen, Strategie-Vergleiche und Reports.

### Aufgaben (abgeschlossen)

1. **Analytics-Modul**
   - `src/analytics/experiments_analysis.py`:
     - `StrategySummary`, `PortfolioSummary` Dataclasses
     - `load_experiments_df_filtered()` – Gefilterte Registry-Daten
     - `summarize_strategies()`, `summarize_portfolios()` – Aggregationen
     - `top_runs_by_metric()` – Top-N Runs
     - `compare_strategies()` – Strategie-Vergleich
     - `write_markdown_report()` – Markdown-Report-Generierung

2. **CLI-Script**
   - `scripts/analyze_experiments.py`:
     - Modi: `summary`, `top-runs`, `portfolios`, `compare`
     - Filter: `--run-type`, `--strategy`, `--symbol`, `--tag`
     - Output: `--write-report` für Markdown

3. **Tests**
   - `tests/test_analytics_experiments_smoke.py` – 20 Smoke-Tests

**Ergebnis Phase 10:** ✓
Vollständiger Analytics-Layer mit CLI, Reports und Tests.

---

## Empfohlene Reihenfolge (Kurzfassung)

1. **Phase 1:** End-to-End-Backtest + Engine/Stats. ✓
2. **Phase 2:** Registry-Integration & Analyse-Skripte. ✓
3. **Phase 3:** Strategie-API + mehrere Strategien. ✓
4. **Phase 4:** Live-/Paper-Workflows mit Risk-Limits glätten. ✓
5. **Phase 5:** Doku & Developer Experience. ✓
6. **Phase 6:** Packaging, Tests & CI, optional Docker. ✓
7. **Phase 7:** Exchange-Layer & Live-Daten. ✓
8. **Phase 8:** Forward-Signals & Out-of-Sample Pipeline. ✓
9. **Phase 9:** Portfolio-Backtests & Multi-Asset Runner. ✓
10. **Phase 10:** Analytics & Reporting. ✓
