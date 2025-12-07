# Tech-Debt Backlog

Dieses Dokument sammelt bewusst aufgeschobene Tech-Debt-Items und größere TODOs.

> **Hinweis:** Diese Items sind bewusst nicht in v1.0 enthalten, werden aber für zukünftige Phasen dokumentiert.

---

## Kategorie A – Code-Struktur / Refactors

### Backtest-Engine: Portfolio-Allocation-Methoden

- [ ] `risk_parity` Allocation-Methode implementieren
  - Fundstelle: `src/backtest/engine.py:1318`
  - Kontext: Portfolio-Allocation-Methode für gleiches Risk-Level pro Strategie
  - Vorschlag: Implementierung basierend auf Volatility/Risk-Metriken

- [ ] `sharpe_weighted` Allocation-Methode implementieren
  - Fundstelle: `src/backtest/engine.py:1319`
  - Kontext: Portfolio-Allocation basierend auf historischer Sharpe-Ratio
  - Vorschlag: Benötigt historische Backtests als Input

### Walk-Forward: Parameter-Optimierung

- [ ] Parameter-Optimierung auf Train-Daten implementieren
  - Fundstelle: `src/backtest/walkforward.py:387`
  - Kontext: Train-Backtest für spätere Optimierung vorbereitet, aber noch nicht aktiv
  - Vorschlag: Integration mit Sweep-System für automatische Parameter-Optimierung

### Legacy-API Cleanup

- [ ] Legacy-Funktionen in `macd.py` entfernen
  - Fundstelle: `src/strategies/macd.py:232`
  - Kontext: Legacy-Funktion für Backwards Compatibility
  - Vorschlag: Prüfen, ob alle Pipelines auf MACDStrategy (OOP) umgestellt sind, dann entfernen

- [ ] Legacy-Funktionen in `bollinger.py` entfernen
  - Fundstelle: `src/strategies/bollinger.py:237`
  - Kontext: Legacy-Funktion für Backwards Compatibility
  - Vorschlag: Prüfen, ob alle Pipelines auf BollingerBandsStrategy (OOP) umgestellt sind, dann entfernen

---

## Kategorie B – Daten-Integration & Exchange

### Echte Daten-Adapter

- [ ] Echten Daten-Adapter in `live_ops.py` integrieren
  - Fundstelle: `scripts/live_ops.py:189`
  - Kontext: Aktuell Dummy-Implementation, später mit echtem Daten-Adapter (Kraken API etc.) ersetzen
  - Vorschlag: Integration mit bestehender Kraken-Integration in `src/data/kraken.py`

- [ ] Echten Daten-Adapter in `preview_live_orders.py` integrieren
  - Fundstelle: `scripts/preview_live_orders.py:157`
  - Kontext: Aktuell Dummy-Implementation
  - Vorschlag: Integration mit bestehender Kraken-Integration

- [ ] Echte Kraken-Daten in `run_portfolio_backtest.py` verwenden
  - Fundstelle: `scripts/run_portfolio_backtest.py:119`
  - Kontext: Aktuell Dummy-Daten, später mit echten Kraken-Daten ersetzen
  - Vorschlag: Integration mit `src/data/kraken.py`

- [ ] Echten Exchange-Client in `preview_live_portfolio.py` integrieren
  - Fundstelle: `scripts/preview_live_portfolio.py:96`
  - Kontext: Später echten Exchange-Client integrieren (z.B. Kraken)
  - Vorschlag: Integration mit `src/exchange/kraken_testnet.py` oder `src/exchange/ccxt_client.py`

- [ ] Timeframe aus Daten ableiten in `run_shadow_execution.py`
  - Fundstelle: `scripts/run_shadow_execution.py:502`
  - Kontext: Timeframe aktuell hardcoded, sollte aus Daten abgeleitet werden
  - Vorschlag: Automatische Erkennung aus DataFrame-Index oder Config

---

## Kategorie C – Features / Nice-to-have

### Vollständige Implementierungen

- [ ] Vollständige Stress-Test-Implementierung
  - Fundstelle: `src/experiments/stress_tests.py:389`
  - Kontext: Vollständige Implementierung, die Equity-Curves aus Backtest-Results lädt
  - Vorschlag: Integration mit Backtest-Registry für automatisches Laden

- [ ] Vollständige Monte-Carlo-Implementierung
  - Fundstelle: `src/experiments/monte_carlo.py:303`
  - Kontext: Vollständige Implementierung, die Equity-Curves aus Backtest-Results lädt
  - Vorschlag: Integration mit Backtest-Registry

- [ ] Vollständige Monte-Carlo-Robustness-Implementierung
  - Fundstelle: `scripts/run_monte_carlo_robustness.py:139`
  - Kontext: Vollständige Implementierung, die Equity-Curves aus Backtest-Results lädt
  - Vorschlag: Integration mit Backtest-Registry

### Registry-Logging

- [ ] Registry-Logging in `demo_order_pipeline_backtest.py` implementieren
  - Fundstelle: `scripts/demo_order_pipeline_backtest.py:306`
  - Kontext: Registry-Logging für automatisches Tracking
  - Vorschlag: Integration mit `src/core/experiments.py`

---

## Kategorie D – Tests & Infra

### Pandas FutureWarnings (Phase 59)

- [ ] Pandas `.fillna` Downcasting Warnings beheben
  - Fundstelle: Diverse `src/strategies/*.py`
  - Kontext: `.shift(1).fillna(False)` Pattern löst FutureWarning in pandas 2.x aus
  - Aktueller Status: Warning in `tests/conftest.py` gefiltert (Phase 59)
  - Vorschlag: Bei pandas 3.0 Migration auf `.astype(bool)` umstellen
  - Priorität: Niedrig (funktioniert, Warning gefiltert)

### test_live_web.py Collection Error

- [ ] test_live_web.py reparieren oder entfernen
  - Fundstelle: `tests/test_live_web.py`
  - Kontext: Fehler bei Test-Collection (vermutlich fehlende Dependency)
  - Aktueller Status: In pytest-Runs mit `--ignore=tests/test_live_web.py` übersprungen
  - Vorschlag: Prüfen, ob Test noch benötigt wird, sonst entfernen
  - Priorität: Niedrig

---

**Hinweis:** Diese Items werden bei Bedarf in zukünftigen Phasen angegangen. Priorisierung erfolgt basierend auf Nutzer-Feedback und Projekt-Roadmap.

