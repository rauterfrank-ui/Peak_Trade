# Tech-Debt Backlog

Dieses Dokument sammelt bewusst aufgeschobene Tech-Debt-Items und größere TODOs.

> **Hinweis:** Diese Items sind bewusst nicht in v1.0 enthalten, werden aber für zukünftige Phasen dokumentiert.

---

## Kategorie A – Code-Struktur / Refactors

### Backtest-Engine: Portfolio-Allocation-Methoden

- [ ] `risk_parity` Allocation-Methode implementieren
  - Fundstelle: `src&#47;backtest&#47;engine.py:1318` (illustrative)
  - Kontext: Portfolio-Allocation-Methode für gleiches Risk-Level pro Strategie
  - Vorschlag: Implementierung basierend auf Volatility/Risk-Metriken

- [ ] `sharpe_weighted` Allocation-Methode implementieren
  - Fundstelle: `src&#47;backtest&#47;engine.py:1319` (illustrative)
  - Kontext: Portfolio-Allocation basierend auf historischer Sharpe-Ratio
  - Vorschlag: Benötigt historische Backtests als Input

### Walk-Forward: Parameter-Optimierung

- [ ] Parameter-Optimierung auf Train-Daten implementieren
  - Fundstelle: `src&#47;backtest&#47;walkforward.py:387` (illustrative)
  - Kontext: Train-Backtest für spätere Optimierung vorbereitet, aber noch nicht aktiv
  - Vorschlag: Integration mit Sweep-System für automatische Parameter-Optimierung

### Legacy-API Cleanup

- [ ] Legacy-Funktionen in `macd.py` entfernen
  - Fundstelle: `src&#47;strategies&#47;macd.py:232` (illustrative)
  - Kontext: Legacy-Funktion für Backwards Compatibility
  - Vorschlag: Prüfen, ob alle Pipelines auf MACDStrategy (OOP) umgestellt sind, dann entfernen

- [ ] Legacy-Funktionen in `bollinger.py` entfernen
  - Fundstelle: `src&#47;strategies&#47;bollinger.py:237` (illustrative)
  - Kontext: Legacy-Funktion für Backwards Compatibility
  - Vorschlag: Prüfen, ob alle Pipelines auf BollingerBandsStrategy (OOP) umgestellt sind, dann entfernen

---

## Kategorie B – Daten-Integration & Exchange

### Echte Daten-Adapter

- [ ] Echten Daten-Adapter in `live_ops.py` integrieren
  - Fundstelle: `scripts&#47;live_ops.py:189` (illustrative)
  - Kontext: Aktuell Dummy-Implementation, später mit echtem Daten-Adapter (Kraken API etc.) ersetzen
  - Vorschlag: Integration mit bestehender Kraken-Integration in `src&#47;data&#47;kraken.py`

- [ ] Echten Daten-Adapter in `preview_live_orders.py` integrieren
  - Fundstelle: `scripts&#47;preview_live_orders.py:157` (illustrative)
  - Kontext: Aktuell Dummy-Implementation
  - Vorschlag: Integration mit bestehender Kraken-Integration

- [ ] Echte Kraken-Daten in `run_portfolio_backtest.py` verwenden
  - Fundstelle: `scripts&#47;run_portfolio_backtest.py:119` (illustrative)
  - Kontext: Aktuell Dummy-Daten, später mit echten Kraken-Daten ersetzen
  - Vorschlag: Integration mit `src&#47;data&#47;kraken.py`

- [ ] Echten Exchange-Client in `preview_live_portfolio.py` integrieren
  - Fundstelle: `scripts&#47;preview_live_portfolio.py:96` (illustrative)
  - Kontext: Später echten Exchange-Client integrieren (z.B. Kraken)
  - Vorschlag: Integration mit `src&#47;exchange&#47;kraken_testnet.py` oder `src&#47;exchange&#47;ccxt_client.py`

- [ ] Timeframe aus Daten ableiten in `run_shadow_execution.py`
  - Fundstelle: `scripts&#47;run_shadow_execution.py:502` (illustrative)
  - Kontext: Timeframe aktuell hardcoded, sollte aus Daten abgeleitet werden
  - Vorschlag: Automatische Erkennung aus DataFrame-Index oder Config
  - Status: implemented in PR #1021 (merge commit `3d6aee01aee77373a190a509e93a38c7d5298ffc`)
    - Fundstellen: `scripts/run_shadow_execution.py` (Function `infer_timeframe_from_index`, CLI `--timeframe`, wiring in Registry-Logging), `tests/test_timeframe_infer.py`

---

## Kategorie C – Features / Nice-to-have

### Vollständige Implementierungen

- [ ] Vollständige Stress-Test-Implementierung
  - Fundstelle: `src&#47;experiments&#47;stress_tests.py:389` (illustrative)
  - Kontext: Vollständige Implementierung, die Equity-Curves aus Backtest-Results lädt
  - Vorschlag: Integration mit Backtest-Registry für automatisches Laden

- [ ] Vollständige Monte-Carlo-Implementierung
  - Fundstelle: `src&#47;experiments&#47;monte_carlo.py:303` (illustrative)
  - Kontext: Vollständige Implementierung, die Equity-Curves aus Backtest-Results lädt
  - Vorschlag: Integration mit Backtest-Registry

- [ ] Vollständige Monte-Carlo-Robustness-Implementierung
  - Fundstelle: `scripts&#47;run_monte_carlo_robustness.py:139` (illustrative)
  - Kontext: Vollständige Implementierung, die Equity-Curves aus Backtest-Results lädt
  - Vorschlag: Integration mit Backtest-Registry

### Registry-Logging

- [ ] Registry-Logging in `demo_order_pipeline_backtest.py` implementieren
  - Fundstelle: `scripts&#47;demo_order_pipeline_backtest.py:306` (illustrative)
  - Kontext: Registry-Logging für automatisches Tracking
  - Vorschlag: Integration mit `src&#47;core&#47;experiments.py`

---

## Kategorie D – Tests & Infra

### Pandas FutureWarnings (Phase 59)

- [ ] Pandas `.fillna` Downcasting Warnings beheben
  - Fundstelle: Diverse `src&#47;strategies&#47;*.py`
  - Kontext: `.shift(1).fillna(False)` Pattern löst FutureWarning in pandas 2.x aus
  - Aktueller Status: Warning in `tests&#47;conftest.py` gefiltert (Phase 59)
  - Vorschlag: Bei pandas 3.0 Migration auf `.astype(bool)` umstellen
  - Priorität: Niedrig (funktioniert, Warning gefiltert)

### test_live_web.py Collection Error

- [ ] test_live_web.py reparieren oder entfernen
  - Fundstelle: `tests&#47;test_live_web.py`
  - Kontext: Fehler bei Test-Collection (vermutlich fehlende Dependency)
  - Aktueller Status: In pytest-Runs mit `--ignore=tests&#47;test_live_web.py` übersprungen
  - Vorschlag: Prüfen, ob Test noch benötigt wird, sonst entfernen
  - Priorität: Niedrig

---

## Kategorie E – Performance & Scale

### Data-Layer Caching

- [ ] Data-Layer Caching für große Research-Sweeps verbessern
  - Kontext: siehe `docs/PERFORMANCE_NOTES.md`, Abschnitt 5
  - Idee: Caching-Layer weiter ausbauen / mehr Reuse zwischen Runs
  - Vorschlag: Parquet-Format für persistierte Daten nutzen (falls noch nicht geschehen)

### Plot-Generation

- [ ] Plot-Generation optional machen für Performance-Benchmarks
  - Kontext: siehe `docs/PERFORMANCE_NOTES.md`, Abschnitt 5
  - Idee: `--no-plots` Flag für reine Performance-Benchmarks
  - Vorschlag: Asynchrone Plot-Generierung (später)

### Logging

- [ ] Logging in großen Research-Runs weiter drosseln oder Batch-weisen Output einführen
  - Kontext: siehe `docs/PERFORMANCE_NOTES.md`, Abschnitt 5
  - Idee: „Benchmark-/Silent"-Mode für Logs
  - Vorschlag: Batch-weiser Output statt einzelner Log-Zeilen

### pandas-Optimierungen

- [ ] pandas-Operationen optimieren (Vektorization, Reduzierung von Zwischenkopien)
  - Kontext: siehe `docs/PERFORMANCE_NOTES.md`, Abschnitt 5
  - Idee: Vektorization & Reduzierung von Zwischenkopien prüfen
  - Vorschlag: Nutzung von `numba` oder `cython` für kritische Loops (später)

---

**Hinweis:** Diese Items werden bei Bedarf in zukünftigen Phasen angegangen. Priorisierung erfolgt basierend auf Nutzer-Feedback und Projekt-Roadmap.
