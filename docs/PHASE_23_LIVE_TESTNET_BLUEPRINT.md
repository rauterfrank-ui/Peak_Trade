# Peak_Trade – Phase 23: Live-/Testnet-Blueprint (Safety-First)

> **Status:** Architektur-Blueprint & Governance-Skizze
> **Scope:** Rein dokumentarisch, keine Aktivierung von Live-Trading
> **Ziel:** Klarer Zielzustand für Testnet-/Live-Architektur – mit Safety-First-Mindset und Gatekeeper-Phasen

---

## 1. Einordnung im Projektkontext

Peak_Trade steht aktuell (nach Phasen 1–22 + Stabilization) an folgendem Punkt:

* **Research & Strategien**

  * Fertiger Strategy-Playground (Phase 18) inkl. `trend_following`, `mean_reversion`, `my_strategy`, `ma_crossover`, `ecm_cycle` (konfiguriert).
  * Regime-Analyse & Robustheits-Tools (Phase 19).
  * Hyperparameter-Sweeps (Phase 20).

* **Analytics & Reporting**

  * Reporting v2 – HTML-Reports & CLI-UX (Phase 21).
  * Experiment & Metrics Explorer (Phase 22).

* **Execution & Environment**

  * Backtest-/Paper-Execution-Layer inkl. `ExecutionPipeline`.
  * `TradingEnvironment` (paper/testnet/live).
  * `SafetyGuard` als mehrstufiger Schutz.
  * Live-/Testnet-Executors existieren nur als Stubs / geblockte Pfade.
  * Live-Risk-Limits und `LiveRiskLimits` (Phase 15/17) für potenzielles Live-Szenario vorbereitet.

* **Qualität & Stabilität**

  * Stabilization-Phase abgeschlossen: **alle Tests (609/609) grün**, Config/Settings aufgeräumt.
  * Safety-/Environment-/Live-Pfade bewusst **nicht** aktiviert.

**Phase 23** ist jetzt ein **Blueprint-Schritt**:

* Kein Code, der Orders an eine echte Börse schickt.
* Stattdessen: **Zielarchitektur, Schichtenmodell, Gatekeeper & Checklisten** für spätere Testnet-/Live-Phasen (Phase 24–25+).

---

## 2. Grundprinzipien für Testnet-/Live-Architektur

Bevor konkrete Komponenten definiert werden, gelten für Peak_Trade folgende Kernprinzipien:

1. **Safety-first, nicht Speed-first**

   * Kein „mal eben Live gehen".
   * Jeder Schritt Richtung Testnet/Live benötigt explizite **Phasen**, **Gates** und **Review**.

2. **Research bleibt entkoppelt**

   * Backtests, Sweeps, Regime-Analysen laufen vollständig **ohne** Live-Funktionalität.
   * Research-Umgebung darf Live-Endpoints nicht einmal „zufällig" erreichen können.

3. **Explizite Modi**

   * `environment.mode ∈ {paper, testnet, live}` muss weiterhin der zentrale Modus-Schalter bleiben.
   * Live-Modus darf nur unter **Mehrfachbedingungen** aktivierbar sein (Konfig + Flags + Bestätigungen).

4. **Kein Geheimnis-Management im Kern**

   * Peak_Trade speichert **keine Klartext-API-Keys** im Code oder in Versionskontrolle.
   * Zugriffe auf echte Exchanges laufen über **konfigurierbare, austauschbare Adapters**, die wiederum externe Secret-Stores (z. B. ENV, Vault, OS Keychain) nutzen.

5. **Nachvollziehbarkeit & Audit**

   * Jede Live-/Testnet-Order muss rückverfolgbar sein:

     * Wer hat sie initiiert?
     * Welche Strategie, welche Parameter, welche Risk-Checks waren aktiv?
     * Welche Limits galten?

6. **Fail-safe > Fail-fast**

   * Bei Unsicherheit oder Inkonsistenz: lieber **Trade blockieren** als durchwinken.
   * Globale Circuit-Breaker für „alles stoppen" im Notfall.

---

## 3. Zielarchitektur – Schichtenmodell für Testnet/Live

### 3.1 Übersicht der Schichten

Zielbild (textuelles „Diagramm"):

```text
[ Strategies & Research ]
       |
       v
[ Signal & Order Generation ]
       |
       v
[ Risk & Limits Layer ]
       |
       v
[ Environment & SafetyGuard ]
       |
       v
[ ExecutionPipeline ]
       |
       v
[ Exchange Adapters (Testnet / Live) ]
       |
       v
[ Broker / Exchange ]
       |
       v
[ Confirmations, Fills, Positions ]
       |
       v
[ Registry, Analytics, Reporting, Monitoring ]
```

**Schichten im Detail:**

1. **Strategies & Research**

   * Bestehende Strategien (MA, Trend, Mean-Reversion, Vol-Breakout, ECM).
   * Backtest-/Paper-Layer, Sweeps, Regime-Analyse.

2. **Signal & Order Generation**

   * Übersetzt Strategie-Signale in `OrderRequest`s.
   * Treibt Execution-Backtests (Paper) und future Testnet-/Live-Routen.

3. **Risk & Limits Layer**

   * `LiveRiskLimits`, Positionslimits, Exposure-Limits, Daily-Loss-Limits.
   * Muss **vor jeder Order** prüfen, ob das Setup unter den konfigurierten Limits bleibt.

4. **Environment & SafetyGuard**

   * `TradingEnvironment(mode="paper"|"testnet"|"live")`.
   * `SafetyGuard` mit:

     * Hard-Stop-Schaltern (global kill switch),
     * Multi-Flag-Checks (z. B. `enable_live_trading`, `require_manual_confirm`),
     * Whitelisting von Symbolen/Exchanges.

5. **ExecutionPipeline**

   * Einheitlicher Execution-Pfad:

     * nimmt `OrderRequest`s entgegen,
     * wählt Executor (Paper, Testnet, später Live),
     * handhabt Retries, Timeout, Partial-Fills, etc.
   * Schnittstelle zu Exchange-Adaptern.

6. **Exchange Adapters**

   * Pro Ziel-Exchange (z. B. Kraken, Binance, etc.) ein Adapter-Modul:

     * uniformes Interface (z. B. `submit_order`, `cancel_order`, `fetch_positions`),
     * Umsetzung der Exchange-spezifischen API-Details.

7. **Registry, Analytics, Reporting, Monitoring**

   * Logging von:

     * Order-Flows,
     * Fills,
     * PnL-Entwicklung (Realized, Unrealized),
     * Risk-Events (Geblockte Orders, Circuit-Breaker).
   * Verwendung durch:

     * Explorer (Phase 22),
     * Reporting v2 (Phase 21),
     * Regime-Analyse (Phase 19),
     * externe Monitoring-Tools (mittelfristig).

---

### 3.2 Daten- & Kontrollflüsse

**Normaler Flow (Zielbild)**

1. Strategie erzeugt Signal (z. B. „BUY 1 BTC/USDT").

2. Signal wird in `OrderRequest` übersetzt.

3. `LiveRiskLimits.check_orders()` prüft:

   * Exposure, Daily Loss, Symbol-Limits, etc.
   * Ergebnis: erlaubt / blockiert + Gründe.

4. `SafetyGuard` prüft:

   * `environment.mode` (paper/testnet/live),
   * globale Flags:

     * `enable_live_trading`,
     * `allow_symbol("BTC/USDT")`,
     * `max_notional_per_order`.
   * ggf. manuelle Bestätigungspflichten.

5. `ExecutionPipeline` wählt Executor:

   * `PaperOrderExecutor` (paper),
   * `TestnetOrderExecutor` (testnet),
   * `LiveOrderExecutor` (live, **später** mit starken Safeguards).

6. Exchange-Adapter setzt Order ab (Testnet/Live) oder simuliert Fill (Paper).

7. Fills, Positions & Fees werden:

   * im Registry/Experiments-System geloggt,
   * in PnL/Analytics überführt,
   * für Reporting v2 & Monitoring aufbereitet.

---

## 4. Phasenmodell Richtung Testnet/Live

Phase 23 legt nur das **Modell & die Gates** fest – **keine Umsetzung**.

### 4.1 Stufenplan

1. **Stufe 0 – Research-Only (Status quo)**

   * Nur Backtests, Paper-Execution, Sweeps, Regime-Analyse.
   * Kein Zugriff auf Testnet-/Live-Endpoints.
   * Alle Live-Executors bleiben Stubs / NotImplemented.

2. **Stufe 1 – Testnet „Shadow" (später)**

   * Ausgewählte Strategien laufen auf Testnet-Umgebung,
   * aber: Orders werden z. B. **nur in Logs** geschrieben, nicht wirklich an Exchange gesendet
     (z. B. „Shadow-Mode": wir rechnen so, als wären sie ausgeführt worden).

3. **Stufe 2 – Reines Testnet**

   * Orders gehen tatsächlich an Testnet-API,
   * Positions & Fills kommen real-time vom Testnet zurück,
   * **nie** mit echten Geldern verknüpft.

4. **Stufe 3 – Shadow Live**

   * Live-Marktdaten, aber Orders weiterhin nur simuliert.
   * Ziel: Check, wie System in realistischen Bedingungen performen würde, ohne echte Orders.

5. **Stufe 4 – Evtl. Live-Trading**

   * Nur bei Erfüllung strenger Voraussetzungen (s. Gatekeeper).
   * Nur für definierte Strategien & Limits.
   * Mit 24/7-Monitoring & klaren Notfall-Prozeduren.

---

## 5. Gatekeeper & Checklisten

Bevor Peak_Trade in eine höhere Stufe übergeht, müssen definierte Bedingungen erfüllt sein.

### 5.1 Beispiel: Übergang von Stufe 0 → Stufe 1 (Testnet Shadow)

* Alle Tests grün (Unit + Integration).
* Kein bekannter „roter" Bug im Execution- oder Risk-Layer.
* Mindestens:

  * X Strategien über **ausreichende historische Zeiträume** backgetestet.
  * Y Sweeps & Regime-Analysen pro Strategie durchgeführt.
* Dokumentierte:

  * Limit-Profile (max Drawdown, max Notional, max Exposure).
  * feste Konfiguration `live_risk` in `config.toml`.

### 5.2 Beispiel: Übergang von Stufe 1 → Stufe 2 (echtes Testnet)

Zusätzlich:

* Shadow-Mode-Run über N Wochen ohne kritische Fehler (Fehl-Orders, Crashs).
* Logging & Monitoring stabil:

  * Keine unbeobachteten Exceptions in Scheduler-/Daemon-Prozessen.
* Manuelle Review von:

  * Order-Frequenzen,
  * Risk-Event-Logs (wie oft wurde geblockt?).

### 5.3 Übergang von Stufe 2/3 → Stufe 4 (Hypothetisches Live)

Strengste Gates:

* Formale **Go/No-Go-Entscheidung** (mindestens 2-Personen-Prinzip).
* Dokumentierte:

  * Runbooks (Start/Stop, Emergency-Stop, Incident-Response),
  * maximale Kapital-Zuteilung (z. B. „max 5 % des Gesamtportfolios"),
  * Liste erlaubter Märkte/Symbole.
* Protokolliertes **Rollout-Planungsszenario**:

  * Start mit minimalem Kapital,
  * sukzessive Erhöhung nur bei Erfüllung definierter KPIs.

---

## 6. Konfigurations- & Safety-Schalter

Phase 23 definiert, welche Schalter später existieren sollen (zum Teil sind einige schon vorhanden, aber rein „Paper-scope" genutzt):

### 6.1 Multi-Level-Schalter

1. **Environment Mode**

   * `environment.mode = "paper" | "testnet" | "live"`
   * Hard-Gate: Live-Executors tun **gar nichts**, wenn `mode != "live"`.

2. **Global Live-Flag**

   * `enable_live_trading = false` (in `config.toml` bzw. Environment-Variablen).
   * Live-Execution-Pfade dürfen nur aktiv werden, wenn:

     * `environment.mode == "live"` **und**
     * `enable_live_trading == true`.

3. **Per-Symbol-Whitelisting**

   * Liste erlaubter Symbole:

     * `live_allowed_symbols = ["BTC/USDT", "ETH/USDT", ...]`
   * Orders auf nicht-whitelistete Symbole werden geblockt.

4. **Two-Man-Rule / Manual Confirm**

   * Optionales Flag:

     * `require_manual_confirm_for_live = true`.
   * Jeder Live-Trade muss manuell bestätigt werden (z. B. CLI-Prompt oder Web-UI später).

5. **Maximal-Limits (Defense in Depth)**

   * `max_total_notional_live`
   * `max_notional_per_order_live`
   * `max_open_positions_live`

Diese Schalter sollen später im `SafetyGuard` und `LiveRiskLimits` **kombiniert** geprüft werden.

---

## 7. Monitoring, Logging & Incident-Handling (Zielbild)

### 7.1 Logging

* Jeder Order-Flow (auch im Testnet/Shadow) soll geloggt werden mit:

  * Zeitstempel,
  * Strategie & Parameter-Set,
  * Environment-Mode,
  * Resultat (accepted, rejected, risk_blocked, error),
  * ggf. Exchange-Antwort (bei Testnet/Live).

* Logs werden so strukturiert, dass:

  * Explorer/Reporting sie auswerten kann,
  * später externe Tools sie konsistent verarbeiten können (ELK, Loki, etc., optional).

### 7.2 Monitoring

* Ziel: Aufbau eines simplen Monitoring-Layers, z. B.:

  * Heartbeat von Scheduler/Daemon,
  * Count & Rate von:

    * Orders,
    * Risk-Blocks,
    * Errors/Exceptions,
  * einfache Alerts (z. B. per E-Mail/Notification-Modul).

### 7.3 Incident-Handling

* Für Live (Phase 26+ hypothetisch) sollen vorab definiert sein:

  * **Runbooks**:

    * „Stoppe alle neuen Orders",
    * „Stoppe alle laufenden Bots",
    * „Gib alle offenen Orders frei" (oder geordneter Exit).

  * **Rollen**:

    * Wer darf den globalen Kill-Switch betätigen?
    * Wer darf Limits erhöhen?

Phase 23 definiert nur, **dass** diese Dinge später nötig sind und wie sie ungefähr aussehen sollen – nicht ihre technische Umsetzung.

---

## 8. Abgrenzung zu zukünftigen Phasen (24, 25+)

Phase 23 ist der **Blueprint/Planungs-Baustein** für Testnet-/Live-Themen.

Geplante nachgelagerte Phasen (High-Level):

* **Phase 24 – Simulation & Dry-Run-Flows**

  * Technische Umsetzung eines Shadow-/Dry-Run-Modus:

    * Execution-Pipeline erzeugt hypothetische Orders,
    * keine API-Calls an Exchanges,
    * PnL & Regime-Auswertung im quasi-realistischen Environment.

* **Phase 25 – Governance & Safety-Dokumentation**

  * Ausarbeitung von:

    * Runbooks,
    * Rollen & Verantwortlichkeiten,
    * Policies (z. B. Change-Management, Limit-Änderungen),
    * Checklisten für Phasen-Übergänge (0→1→2→...).

* **Phase 26+ – Testnet-/Live-Implementation (optional, weit in der Zukunft)**

  * Konkrete Implementation der Live-/Testnet-Executors,
  * Integration mit Exchange-Adaptern,
  * Aktivierung der hier geplanten Schalter & Gatekeeper.

---

## 9. Fazit

Mit diesem Blueprint definiert Phase 23:

* das **Zielbild der Testnet-/Live-Architektur**,
* ein Schichten- und Phasenmodell, das Safety & Research sauber trennt,
* notwendige **Gatekeeper, Schalter und Prozesse**, bevor Live-Trading überhaupt denkbar ist.

Wichtig:

* Peak_Trade bleibt bis inklusive Phase 23 ein **reines Research-, Backtest- & Paper-Framework**.
* Alle hier beschriebenen Live-/Testnet-Elemente sind **Planung**, keine aktive Funktionalität.
* Jede spätere Aktivierung wird eigene Phasen (24–26+) mit zusätzlichen Tests, Doku und Governance erfordern.

Phase 23 liefert damit die architektonische und organisatorische Grundlage, auf der später **sichere** Testnet-/Live-Schritte aufgebaut werden können – ohne das aktuelle Safety-Level zu gefährden.

---

## 10. Weiterführende Governance-Dokumentation (Phase 25)

Phase 25 ergänzt diesen technischen Blueprint um den **organisatorischen Layer**:

| Dokument | Beschreibung |
|----------|--------------|
| [GOVERNANCE_AND_SAFETY_OVERVIEW.md](GOVERNANCE_AND_SAFETY_OVERVIEW.md) | Grundprinzipien, Rollen & Verantwortlichkeiten, Entscheidungsprozesse |
| [SAFETY_POLICY_TESTNET_AND_LIVE.md](SAFETY_POLICY_TESTNET_AND_LIVE.md) | Konkrete Safety-Policies, Risk-Limits, Verbote & rote Linien |
| [RUNBOOKS_AND_INCIDENT_HANDLING.md](RUNBOOKS_AND_INCIDENT_HANDLING.md) | Runbooks für Shadow-Run, System-Pause, Incident-Handling |
| [LIVE_READINESS_CHECKLISTS.md](LIVE_READINESS_CHECKLISTS.md) | Checklisten für Stufen-Übergänge |

→ Die Governance-Dokumentation (Phase 25) ergänzt die technische Architektur (Phase 23) um die prozessualen Aspekte.

---

## Changelog

- **Phase 25** (2025-12): Querverweis auf Governance-Dokumentation hinzugefügt
- **Phase 23** (2025-12): Initial Blueprint erstellt
  - Architektur-Schichtenmodell definiert
  - 5-Stufen-Plan für Testnet/Live
  - Gatekeeper-Checklisten spezifiziert
  - Safety-Schalter dokumentiert
  - Keine Code-Änderungen, rein dokumentarisch
