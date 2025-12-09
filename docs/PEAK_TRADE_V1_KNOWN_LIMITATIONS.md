# Peak_Trade v1.0 – Known Limitations

> **Phase:** 68 – v1.0 Hardening & Polishing  
> **Status:** v1.0 Release  
> **Zweck:** Klare, ehrliche Dokumentation bewusst nicht implementierter Features und Limitierungen

---

## 1. Einleitung

Dieses Dokument listet **bewusst nicht implementierte Features** und **bekannte Limitierungen** von Peak_Trade v1.0 auf. Diese Liste dient:

- **Entwicklern** als Referenz für zukünftige Roadmaps
- **Operatoren** zur klaren Erwartungshaltung
- **Reviewern** zur vollständigen Transparenz

**Wichtig:** Diese Limitierungen sind **bewusst akzeptiert** für v1.0 und stellen keine Bugs dar.

---

## 2. Live-Trading & Order-Execution

### 2.1 Keine echte Live-Order-Ausführung

**Status:** Bewusst blockiert in v1.0

**Details:**
- Live-Trading-Modus (`environment.mode = "live"`) ist **nicht implementiert**
- Alle Versuche, echte Live-Orders zu senden, werden durch `SafetyGuard` blockiert
- `LiveNotImplementedError` wird bei jedem Versuch geworfen

**Begründung:**
- v1.0 fokussiert auf Research, Backtests, Shadow- und Testnet-Betrieb
- Live-Trading erfordert zusätzliche Safety-Layer, die erst in späteren Phasen implementiert werden

**Workaround:**
- Shadow-Runs für quasi-realistische Simulation
- Testnet-Runs für echte Exchange-Integration (aktuell nur Dry-Run)

**Referenz:**
- `src/live/safety.py` – SafetyGuard-Implementierung
- `src/core/environment.py` – Environment-Konfiguration

---

## 2.2 Testnet nur im Dry-Run-Modus

**Status:** Bewusst limitiert in v1.0

**Details:**
- Testnet-Modus (`environment.mode = "testnet"`) ist nur im Dry-Run verfügbar
- `testnet_dry_run = True` ist der Default und kann nicht deaktiviert werden
- Echte Testnet-Orders werden nicht gesendet, auch wenn `testnet_dry_run = False` gesetzt wird

**Begründung:**
- Testnet-Integration erfordert zusätzliche Exchange-Adapter und Error-Handling
- v1.0 fokussiert auf Architektur-Vorbereitung, nicht auf vollständige Exchange-Integration

**Workaround:**
- Shadow-Runs für Simulation
- Dry-Run-Logging für Order-Validation

---

## 3. Exchange-Integration

### 3.1 Unterstützte Exchanges

**Status:** Nur Kraken (Testnet & Live-API) vollständig unterstützt

**Details:**
- Kraken ist die Referenz-Exchange mit vollständiger Integration
- Weitere Exchanges (z.B. Binance, Coinbase) sind **nicht implementiert**

**Begründung:**
- v1.0 fokussiert auf eine stabile Referenz-Implementation
- Multi-Exchange-Support erfordert zusätzliche Abstraktions-Layer

**Workaround:**
- CCXT-basierte Adapter können in zukünftigen Phasen hinzugefügt werden
- Aktuell: Kraken als Referenz für Architektur-Patterns

**Referenz:**
- `src/exchange/kraken_testnet.py` – Kraken Testnet-Adapter
- `src/exchange/ccxt_client.py` – CCXT-Basis (vorbereitet für Erweiterungen)

---

## 4. Web-Dashboard

### 4.1 Keine Authentifizierung

**Status:** Bewusst nicht implementiert in v0

**Details:**
- Web-Dashboard (`src/live/web/app.py`) hat **keine Authentifizierung**
- Keine Access-Control-Mechanismen
- Keine Benutzer-Verwaltung

**Begründung:**
- v0 ist für lokale/vertrauenswürdige Netzwerke gedacht
- Authentifizierung wird in späteren Versionen hinzugefügt

**Workaround:**
- Nur in vertrauenswürdigen Netzwerken verwenden
- Firewall-Regeln für Zugriffskontrolle
- Reverse-Proxy mit Auth (z.B. nginx mit Basic-Auth)

**Referenz:**
- `docs/LIVE_OPERATIONAL_RUNBOOKS.md` Abschnitt 10d

---

### 4.2 Read-Only (keine Order-Erzeugung)

**Status:** Bewusst read-only in v0

**Details:**
- Web-Dashboard bietet **keine POST/PUT/DELETE-Endpunkte**
- Keine Order-Erzeugung, kein Start/Stop von Runs aus dem Web UI
- Nur GET-Endpunkte für Monitoring

**Begründung:**
- Safety-First: Trading-Operationen bleiben in CLI-Skripten
- Web-Dashboard dient ausschließlich dem Monitoring

**Workaround:**
- CLI-Skripte für Run-Steuerung (`testnet_orchestrator_cli.py`)
- Web-Dashboard nur für Monitoring

---

### 4.3 Kein SSE/WebSocket (Polling-basiert)

**Status:** Bewusst einfach gehalten in v0

**Details:**
- Auto-Refresh via JavaScript-Polling (alle 5 Sekunden)
- Keine Server-Sent Events (SSE) oder WebSocket-Integration

**Begründung:**
- v0 fokussiert auf Einfachheit und Robustheit
- SSE/WebSocket erfordern zusätzliche Infrastruktur

**Workaround:**
- Auto-Refresh-Intervall anpassbar (Default: 5 Sekunden)
- Manuelles Neuladen möglich

---

## 5. Daten & Market Access

### 5.1 Begrenzte Exchange-Datenquellen

**Status:** Nur Kraken vollständig unterstützt

**Details:**
- Andere Exchanges (Binance, Coinbase, etc.) sind nicht implementiert
- Keine aggregierten Multi-Exchange-Datenfeeds

**Begründung:**
- v1.0 fokussiert auf eine stabile Referenz-Implementation
- Multi-Exchange-Support ist für zukünftige Phasen geplant

---

### 5.2 Keine Real-Time-Streams

**Status:** Nur REST-API, keine WebSocket-Streams

**Details:**
- Daten werden via REST-API geladen (Polling)
- Keine WebSocket-basierten Real-Time-Streams

**Begründung:**
- REST-API ist einfacher und robuster für v1.0
- WebSocket-Streams erfordern zusätzliche Infrastruktur

**Workaround:**
- Caching reduziert API-Calls
- Polling-Intervall anpassbar

---

## 6. Strategien & Features

### 6.1 Begrenzte Strategie-Bibliothek

**Status:** Fokus auf bewährte Strategien

**Details:**
- Aktuell ~20 Strategien implementiert
- Keine ML-basierten Strategien
- Keine komplexen Multi-Factor-Modelle

**Begründung:**
- v1.0 fokussiert auf regelbasierte, nachvollziehbare Strategien
- ML-Strategien erfordern zusätzliche Infrastruktur und Validierung

**Workaround:**
- Neue Strategien können via Registry hinzugefügt werden
- Siehe `docs/DEV_GUIDE_ADD_STRATEGY.md`

---

### 6.2 Keine Corporate Actions / Dividenden

**Status:** Nicht implementiert

**Details:**
- Corporate Actions (Splits, Dividenden, etc.) werden nicht behandelt
- Nur Spot-Trading, keine Futures/Options

**Begründung:**
- v1.0 fokussiert auf Spot-Trading
- Corporate Actions erfordern zusätzliche Datenquellen und Logik

---

## 7. Risk & Safety

### 7.1 Keine automatische Position-Liquidation

**Status:** Bewusst nicht automatisiert in v1.0

**Details:**
- Risk-Limits blockieren neue Orders, aber liquidieren nicht automatisch
- Position-Liquidation muss manuell erfolgen

**Begründung:**
- Safety-First: Automatische Liquidation erfordert zusätzliche Validierung
- v1.0 fokussiert auf Prevention, nicht auf automatische Korrektur

**Workaround:**
- Alerts warnen bei Risk-Violations
- Manuelle Intervention erforderlich

---

## 8. Testing & Qualitätssicherung

### 8.1 Test-Coverage

**Status:** ~1709 Tests, aber nicht 100% Coverage

**Details:**
- Nicht alle Code-Pfade sind vollständig getestet
- Einige Edge-Cases möglicherweise nicht abgedeckt

**Begründung:**
- v1.0 fokussiert auf kritische Pfade (Safety, Order-Execution, Risk)
- Vollständige Coverage ist für zukünftige Phasen geplant

**Workaround:**
- Manuelle Tests für kritische Operationen
- Incident-Drills für praktische Validierung

---

## 9. Dokumentation

### 9.1 API-Dokumentation

**Status:** Keine automatisch generierte API-Dokumentation

**Details:**
- Keine OpenAPI/Swagger-Specs für Web-Dashboard
- Keine automatisch generierte Code-Dokumentation

**Begründung:**
- v1.0 fokussiert auf Markdown-basierte Dokumentation
- API-Dokumentation ist für zukünftige Phasen geplant

**Workaround:**
- Manuelle Dokumentation in `docs/LIVE_OPERATIONAL_RUNBOOKS.md`
- Code-Kommentare und Docstrings

---

## 10. Performance & Skalierung

### 10.1 Keine horizontale Skalierung

**Status:** Single-Instance-Design

**Details:**
- Keine Multi-Instance-Unterstützung
- Keine verteilte Ausführung

**Begründung:**
- v1.0 fokussiert auf Single-Operator-Setup
- Skalierung ist für zukünftige Phasen geplant

---

## 11. Zusammenfassung

**Bewusst nicht implementiert in v1.0:**
- ✅ Echte Live-Order-Ausführung
- ✅ Testnet ohne Dry-Run
- ✅ Multi-Exchange-Support (nur Kraken)
- ✅ Web-Dashboard-Authentifizierung
- ✅ Real-Time-WebSocket-Streams
- ✅ ML-basierte Strategien
- ✅ Corporate Actions
- ✅ Automatische Position-Liquidation
- ✅ 100% Test-Coverage
- ✅ Automatisch generierte API-Dokumentation
- ✅ Horizontale Skalierung

**Diese Limitierungen sind bewusst akzeptiert** und stellen keine Bugs dar. Sie dienen als Grundlage für zukünftige Roadmaps.

---

## 12. Roadmap-Hinweise

**Für zukünftige Phasen geplant:**
- Phase 69+: Live-Trading-Implementation
- Phase 70+: Multi-Exchange-Support
- Phase 71+: Web-Dashboard v1 (mit Auth)
- Phase 72+: Real-Time-Streams
- Phase 73+: ML-Strategien

**Siehe auch:**
- [`docs/PEAK_TRADE_V1_OVERVIEW_FULL.md`](PEAK_TRADE_V1_OVERVIEW_FULL.md) – Vollständige Übersicht
- [`docs/PEAK_TRADE_STATUS_OVERVIEW.md`](PEAK_TRADE_STATUS_OVERVIEW.md) – Status-Übersicht

---

**Erstellt:** Phase 68 (v1.0 Hardening & Polishing)  
**Letzte Aktualisierung:** Phase 68





