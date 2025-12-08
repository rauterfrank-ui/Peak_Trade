# Phase 84 – Live-Track Demo Walkthrough & Case Study

**Status:** ✅ Dokumentiert
**Datum:** 2025-12-08
**Zielgruppe:** Operatoren, Entwickler, Reviewer

---

## 1. Einleitung & Ziel

### 1.1 Was ist Phase 84?

Phase 84 ist ein **Live-Track Demo Walkthrough & Case Study** – ein praxisnaher Leitfaden, mit dem Operatoren in ca. **10–15 Minuten** eine vollständige Demo-Session (Shadow oder Testnet) durchspielen können.

### 1.2 Einordnung in die Phase-Architektur

Phase 84 baut auf den vorherigen Live-Track-Phasen auf:

| Phase | Komponente | Funktion |
|-------|------------|----------|
| **80** | Strategy-to-Execution Bridge | `LiveSessionRunner` orchestriert Strategy → Signals → Orders → ExecutionPipeline |
| **81** | Live-Session-Registry & Report-CLI | Persistiert Session-Records als JSON, CLI für Reports |
| **82** | Live-Track Panel im Web-Dashboard | Visualisiert Sessions (Snapshot-Kachel + Sessions-Tabelle) |
| **83** | Operator-Workflow & Runbooks | Definiert tägliche Checks, Fehlerbehandlung, Governance |
| **84** | **Dieser Demo-Walkthrough** | Kombiniert alles zu einem konkreten Hands-On-Durchlauf |
| **85** | Session Explorer (Web-Dashboard v1) | Filter, Detail-View, Stats-API – klickbare Sessions im Browser |

### 1.3 Ziel des Dokuments

Nach Durcharbeiten dieses Walkthroughs kann ein Operator:

- ✅ Eine Shadow-/Testnet-Session starten und beobachten
- ✅ Die Registry-Einträge über das CLI prüfen
- ✅ Das Live-Track Panel im Dashboard verifizieren
- ✅ Die Operator-Checks aus Phase 83 anwenden
- ✅ Plausibilitäts-Checks zwischen CLI-Report und Dashboard durchführen

---

## 2. Voraussetzungen & Setup

### 2.1 Technische Voraussetzungen

- [ ] Repo geklont und aktuell (`git pull`)
- [ ] Virtuelle Umgebung aktiviert:
  ```bash
  cd ~/Peak_Trade
  source .venv/bin/activate
  ```
- [ ] Test-Suite zuletzt grün (Kurzcheck):
  ```bash
  pytest -q --tb=no
  ```
  (Details in `docs/PEAK_TRADE_STATUS_OVERVIEW.md`)
- [ ] Abhängigkeiten aktuell:
  ```bash
  pip install -e ".[dev]"
  ```

### 2.2 Betriebsmodus für die Demo

**⚠️ WICHTIG: Nur Shadow- oder Testnet-Mode!**

```
╔══════════════════════════════════════════════════════════════════════════╗
║  Diese Demo ist für SHADOW- und TESTNET-Mode konzipiert.                  ║
║                                                                          ║
║  • Keine echten Orders                                                   ║
║  • Kein echtes Kapital im Risiko                                         ║
║  • Rein simulativer Betrieb                                              ║
║                                                                          ║
║  Live-Mode ist technisch blockiert (Phase 80 Safety-First Design)        ║
╚══════════════════════════════════════════════════════════════════════════╝
```

### 2.3 Komponenten im Demo-Flow

| Komponente | Funktion in der Demo |
|------------|---------------------|
| `scripts/run_execution_session.py` | Startet die Demo-Session (Phase 80) |
| `scripts/report_live_sessions.py` | Zeigt Registry-Reports (Phase 81) |
| `src/webui/app.py` | Web-Dashboard mit Live-Track Panel (Phase 82) |
| Operator-Checks | Aus `PHASE_83_LIVE_TRACK_OPERATOR_WORKFLOW.md` |

---

## 3. Schritt 1 – System & Dashboard prüfen

**Zeitbedarf:** ca. 2–3 Minuten

### 3.1 Web-Dashboard starten

Öffne ein Terminal und starte das Dashboard:

```bash
cd ~/Peak_Trade
source .venv/bin/activate

# Dashboard starten (mit Auto-Reload für Entwicklung)
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000
```

> **Hinweis:** Das Terminal bleibt offen – für die nächsten Schritte ein neues Terminal verwenden.

### 3.2 Health-Check durchführen

In einem neuen Terminal:

```bash
# API-Health prüfen
curl http://127.0.0.1:8000/api/health
```

**Erwartetes Ergebnis:**
```json
{"status": "ok"}
```

### 3.3 Dashboard im Browser öffnen

Öffne im Browser:

- **Dashboard:** http://127.0.0.1:8000/
- **OpenAPI-Docs (optional):** http://127.0.0.1:8000/docs

### 3.4 Checkliste: System-Prüfung

- [ ] Dashboard läuft ohne Fehler im Terminal
- [ ] `http://127.0.0.1:8000/` lädt erfolgreich
- [ ] Health-Check gibt `{"status": "ok"}` zurück
- [ ] Live-Track Panel ist sichtbar (auch wenn "Keine Live-Sessions gefunden" angezeigt wird)

---

## 4. Schritt 2 – Demo-Session im Shadow-Mode starten

**Zeitbedarf:** ca. 3–5 Minuten

### 4.1 Verfügbare Strategien prüfen (optional)

```bash
python scripts/run_execution_session.py --list-strategies
```

### 4.2 Shadow-Session starten

In einem separaten Terminal starte die Demo-Session:

```bash
cd ~/Peak_Trade
source .venv/bin/activate

# Shadow-Session mit Standard-Strategie (ma_crossover)
python scripts/run_execution_session.py \
    --strategy ma_crossover \
    --symbol BTC/EUR \
    --steps 10
```

**Parameter-Erklärung:**

| Parameter | Bedeutung |
|-----------|-----------|
| `--strategy ma_crossover` | Verwendet die MA-Crossover-Strategie |
| `--symbol BTC/EUR` | Handelt BTC gegen EUR |
| `--steps 10` | Führt 10 Bars/Schritte aus (kurze Demo) |

### 4.3 Alternativen für die Demo

**Längere Session (30 Minuten):**
```bash
python scripts/run_execution_session.py \
    --strategy rsi_reversion \
    --symbol ETH/EUR \
    --duration 30
```

**Testnet-Mode (validate_only):**
```bash
python scripts/run_execution_session.py \
    --mode testnet \
    --strategy ma_crossover \
    --steps 10
```

**Dry-Run (nur Config validieren):**
```bash
python scripts/run_execution_session.py \
    --strategy ma_crossover \
    --dry-run
```

### 4.4 Erwartetes Verhalten während der Session

Nach dem Start siehst du im Terminal:

1. **Session startet** – Config wird geladen und validiert
2. **Warmup** – Historische Daten werden geladen
3. **Step-by-Step Ausführung** – Für jeden Bar:
   - Signal wird generiert (-1/0/+1)
   - Order wird (ggf.) erzeugt und an ExecutionPipeline gegeben
   - RiskLimits werden geprüft
4. **Session-Summary** – Am Ende werden Metriken ausgegeben

### 4.5 Checkliste: Session-Start

- [ ] Session startet ohne Fehler
- [ ] "Warmup complete" wird angezeigt (oder ähnlich)
- [ ] Schritte werden durchlaufen
- [ ] Session-Summary wird am Ende ausgegeben

---

## 5. Schritt 3 – Registry & Report prüfen (Phase 81)

**Zeitbedarf:** ca. 2–3 Minuten

Nach Abschluss der Session wurde ein Eintrag in der Live-Session-Registry erstellt.

### 5.1 Letzte Session im CLI prüfen

```bash
# Summary der letzten Shadow-Sessions
python scripts/report_live_sessions.py \
    --run-type live_session_shadow \
    --status completed \
    --limit 5 \
    --summary-only \
    --stdout
```

**Erwarteter Output (Beispiel):**

```
## Live-Session Summary

- **Anzahl Sessions:** 5
- **Status-Verteilung:** completed: 5
- **Total Realized PnL:** 123.45 EUR
- **Durchschnittlicher Max Drawdown:** 2.3%
```

### 5.2 Detaillierter Report der letzten Session

```bash
# Detaillierter Markdown-Report
python scripts/report_live_sessions.py \
    --run-type live_session_shadow \
    --limit 1 \
    --output-format markdown \
    --stdout
```

### 5.3 Relevante Kennzahlen

Die wichtigsten Kennzahlen aus dem Report:

| Kennzahl | Beschreibung | Wo im Dashboard? |
|----------|--------------|------------------|
| **Realized PnL** | Realisierte Gewinne/Verluste | PnL-Spalte in Tabelle, Snapshot-Kachel |
| **Max Drawdown** | Maximaler Verlust während Session | Max DD-Spalte |
| **Num Orders** | Anzahl generierter/ausgeführter Orders | Orders-Spalte |
| **Status** | completed/failed/aborted | Status-Badge |

### 5.4 Checkliste: Registry & Report

- [ ] CLI-Report zeigt die eben abgeschlossene Session
- [ ] Status ist `completed`
- [ ] PnL und Max Drawdown werden angezeigt
- [ ] Notiere: PnL = _____, Max DD = _____ (für späteren Abgleich)

---

## 6. Schritt 4 – Live-Track Session Explorer (Phase 82/85)

**Zeitbedarf:** ca. 3–4 Minuten

Wechsle nun in den Browser zum Dashboard – jetzt mit dem erweiterten **Session Explorer** (Phase 85).

#### Dashboard-Ansicht während der Demo

Sobald die Shadow-/Testnet-Session läuft, wird der technische Flow im Web-Dashboard v1 sichtbar. 
Nutze diesen Schritt in der Demo, um Operatoren und Stakeholdern den Live-Track-Stack zu zeigen:

> **Dashboard in 5 Schritten nutzen**
> 1. **Dashboard öffnen** – Im Browser die Dashboard-URL aufrufen (z.B. wie in README/Web-Dashboard-Doku angegeben).
> 2. **System-Status prüfen** – Auf der Startseite kurz Version, Tags und CI-Status zeigen (Tiering: Research/Beta/Live-ready).
> 3. **Live-Track Panel öffnen** – Zum Live-Track-Bereich wechseln und die gerade gestartete Session (Environment: Shadow/Testnet) identifizieren.
> 4. **Session Explorer öffnen** – Die Session anklicken und im Session Explorer die Registry-Metadaten, Laufzeit und Ergebnisstatus durchgehen.
> 5. **Operator-Links highlighten** – Zeigen, dass aus dem Explorer heraus Playbook- und Runbook-Links verfügbar sind (für Reviews, Drills, Post-Mortems).

**Kurz-Fazit (für die Demo):**  
Der Operator startet die Session über CLI – das Dashboard macht den Live-Track-Stack sichtbar, ohne Orders direkt auszulösen. 
So können Monitoring, Reviews und Schulungen durchgeführt werden, bevor echte Orders jemals das Haus verlassen.

#### Storyboard: Ideale Demo-Session im Web-Dashboard v1

Um die Live-Track-Demo greifbar zu machen, empfiehlt es sich, 3–4 Screens im Web-Dashboard v1 vorzubereiten. 
So entsteht ein konsistentes Narrativ für Operatoren, Quant-Leads und Stakeholder:

- **Screen 1 – System-Status & Tiering (Landing-Page)**  
  - Dashboard-Startseite mit sichtbarer Version, Tag und CI-Status.  
  - Tiering (Research/Beta/Live-ready) ist klar ersichtlich.  
  - Message: *„Wir wissen genau, in welchem Zustand der Stack gerade ist."*

- **Screen 2 – Live-Track Panel (Session-Übersicht)**  
  - Live-Track-Ansicht mit mindestens einer frisch gelaufenen Shadow-/Testnet-Session.  
  - Spalten wie Environment, Start-/Endzeit, Ergebnisstatus sind lesbar.  
  - Message: *„Wir sehen alle relevanten Sessions zentral aggregiert."*

- **Screen 3 – Session Explorer (Detail-Ansicht)**  
  - Geöffnete Session mit Registry-Metadaten, Laufzeit, Ergebnisstatus und ggf. Error-Feldern.  
  - Links zu Playbook-/Runbook-Dokumentation sichtbar.  
  - Message: *„Wir können jede Session im Detail nachvollziehen und reviewen."*

- **Screen 4 (optional) – Incident-/Review-Sicht**  
  - Falls verfügbar: Beispiel einer Session mit einem auffälligen Ergebnis (z.B. Error/Warning) 
    und referenziertem Incident/Review.  
  - Message: *„Auch wenn etwas schiefgeht, bleibt der Prozess nachvollziehbar und auditierbar."*

**Hinweis für die Vorbereitung:**  
Vor der Demo 1–2 Shadow-/Testnet-Sessions bewusst laufen lassen, damit im Live-Track Panel und im Session Explorer 
„schöne" Beispiele sichtbar sind (eine normale Session, optional eine mit Warning/Error).

### 6.1 Dashboard refreshen

Führe einen manuellen Refresh im Browser durch (F5 oder Ctrl+R).

### 6.2 Snapshot-Kachel prüfen

Die **Snapshot-Kachel** (oberer Bereich des Live-Track Panels) zeigt die **letzte abgeschlossene Session**:

| Element | Was du siehst | Bedeutung |
|---------|---------------|-----------|
| **Mode-Badge** | `shadow` (purple) | Session-Typ |
| **Status** | `Completed` (grün) | Erfolgreicher Abschluss |
| **Environment** | z.B. `kraken_futures / BTC/EUR` | Exchange + Symbol |
| **Realized PnL** | z.B. `+12.34` (grün) oder `-5.67` (rot) | PnL der Session |
| **Max Drawdown** | z.B. `2.3%` | Maximaler Drawdown |
| **Duration** | z.B. `5m 30s` | Berechnete Session-Dauer |

### 6.3 Filter-Leiste verwenden (Phase 85)

Die **Filter-Leiste** (neu in Phase 85) erlaubt das schnelle Filtern der Sessions:

**Mode-Filter:**
- `Alle` – Alle Sessions anzeigen
- `Shadow` – Nur Shadow-Sessions (purple)
- `Testnet` – Nur Testnet-Sessions (amber)
- `Paper` – Nur Paper-Sessions (sky)

**Status-Filter:**
- `Alle` – Alle Status anzeigen
- `Completed` – Nur erfolgreiche Sessions
- `Failed` – Nur fehlgeschlagene Sessions
- `Running` – Nur laufende Sessions

**Beispiel-URLs zum Testen:**
```
http://127.0.0.1:8000/?mode=shadow&status=completed
http://127.0.0.1:8000/?mode=testnet
http://127.0.0.1:8000/?status=failed
```

### 6.4 Sessions-Tabelle – Klickbare Zeilen (Phase 85)

Die **Sessions-Tabelle** zeigt die letzten N Sessions – **jede Zeile ist jetzt klickbar!**

| Spalte | Inhalt |
|--------|--------|
| Session | Session-ID (klickbar → öffnet Detail-Page) |
| Mode | shadow/testnet/paper/live (mit ⚠️ für Live) |
| Status | ✓ OK / ✕ FAIL / ⊘ ABORT / ● RUN |
| Started | Startzeitpunkt |
| Duration | Berechnete Dauer (z.B. "1h 30m") |
| PnL | Realized PnL (farbcodiert) |
| Max DD | Max Drawdown |
| Orders | Anzahl Orders |

> 💡 **Tipp:** Klicke auf eine Zeile, um die Detail-Ansicht zu öffnen!

### 6.5 Session-Detail-Page öffnen (Phase 85)

**Klicke auf deine Demo-Session** in der Tabelle → Du landest auf:

```
http://127.0.0.1:8000/session/{session_id}
```

**Was du auf der Detail-Page siehst:**

1. **Header mit Session-ID und Mode-Badge**
2. **Haupt-Metriken-Kacheln:**
   - Status (✓ Completed / ✕ Failed)
   - Realized PnL (grün/rot)
   - Max Drawdown (%)
   - Anzahl Orders

3. **Meta-Informationen:**
   - Environment & Symbol
   - Start/Ende-Zeitpunkt
   - Berechnete Dauer
   - Record-Erstellungszeitpunkt

4. **Alle Metrics (Tabelle):**
   - Jede Metrik aus der Session
   - z.B. realized_pnl, max_drawdown, num_orders, etc.

5. **Session-Config (JSON):**
   - Komplette Konfiguration der Session
   - Strategy-Name, Parameter, etc.

6. **CLI-Aufruf (wenn vorhanden):**
   - Der Original-Befehl, mit dem die Session gestartet wurde

### 6.6 Stats-API prüfen (Phase 85)

Die **Stats-API** gibt aggregierte Statistiken zurück:

```bash
curl http://127.0.0.1:8000/api/live_sessions/stats | jq .
```

**Erwarteter Output:**
```json
{
  "total_sessions": 5,
  "by_mode": {"shadow": 4, "testnet": 1},
  "by_status": {"completed": 4, "failed": 1},
  "total_pnl": 234.56,
  "avg_drawdown": 0.023
}
```

### 6.7 Erwartetes Verhalten nach der Demo-Session

Nach deiner eben durchgeführten Shadow-Session solltest du sehen:

1. ✅ Die Session erscheint **oben in der Tabelle** (neueste zuerst)
2. ✅ Snapshot-Kachel zeigt diese Session
3. ✅ Mode-Badge zeigt `shadow` (purple)
4. ✅ Status zeigt `Completed` (grün)
5. ✅ **Klick auf Zeile öffnet Detail-Page**
6. ✅ Detail-Page zeigt Config, Metrics, CLI-Args

### 6.8 Leerer Zustand (Falls keine Sessions)

Falls du keine Sessions siehst:

```
Keine Live-Sessions gefunden.
Sessions werden nach dem ersten Shadow-/Testnet-Run hier angezeigt.
```

**Lösung:** Führe Schritt 2 (Shadow-Session starten) erneut aus.

### 6.9 Checkliste: Session Explorer (Phase 85)

- [ ] Eben abgeschlossene Session erscheint in der Tabelle
- [ ] Snapshot-Kachel zeigt die richtige Session
- [ ] Filter-Leiste ist sichtbar und funktioniert
- [ ] Klick auf Session öffnet Detail-Page
- [ ] Detail-Page zeigt Config, Metrics, CLI-Args
- [ ] Stats-API gibt plausible Werte zurück
- [ ] PnL/Max DD stimmen mit CLI-Report überein

---

## 7. Schritt 5 – Checks laut Phase 83 anwenden

**Zeitbedarf:** ca. 2 Minuten

Wende nun die Operator-Checks aus Phase 83 an, um die Konsistenz zu verifizieren.

### 7.1 Zentrale Checks aus Phase 83

| Check | Beschreibung | Tool |
|-------|--------------|------|
| **Status-Konsistenz** | Status im Panel = Realität der Session? | Dashboard |
| **PnL-Abgleich** | PnL im Panel ≈ PnL im CLI-Report? | Dashboard vs. CLI |
| **Max DD-Abgleich** | Max DD im Panel ≈ Max DD im CLI? | Dashboard vs. CLI |
| **Orders-Plausibilität** | Anzahl Orders sinnvoll für Strategietyp? | Dashboard |
| **Keine Lücken** | Keine unerklärten Gaps in der Historie? | Dashboard-Tabelle |

### 7.2 Plausibilitäts-Check Demo-Session

Führe die folgenden Checks durch:

#### Checkliste: Plausibilitäts-Check

- [ ] **Session erscheint im Live-Track Panel**
  - In der Sessions-Tabelle sichtbar?

- [ ] **Snapshot-Kachel zeigt korrekten Mode**
  - Mode = `shadow` (purple) oder `testnet` (amber)?

- [ ] **PnL konsistent mit CLI-Report**
  - CLI-PnL: _____
  - Dashboard-PnL: _____
  - Differenz akzeptabel (< 1%)?

- [ ] **Max Drawdown konsistent**
  - CLI-Max-DD: _____
  - Dashboard-Max-DD: _____
  - Differenz akzeptabel?

- [ ] **Status ist wie erwartet**
  - `completed` wenn erfolgreich?
  - `failed` wenn Fehler aufgetreten?

- [ ] **Keine Fehlermeldung in Notes**
  - Notes-Feld leer oder erklärbar?

### 7.3 API-Check (optional)

Für tiefergehende Prüfung:

```bash
# Letzte Session via API abrufen
curl http://127.0.0.1:8000/api/live_sessions?limit=1 | jq .
```

**Prüfpunkte im JSON:**
- `status`: `"completed"`
- `realized_pnl`: Entspricht Dashboard-Anzeige?
- `max_drawdown`: Entspricht Dashboard-Anzeige?
- `notes`: Leer oder Fehlermeldung?

---

## 8. Beispiel-Szenario: Erfolgreiche Demo-Session

Hier ein typisches Beispiel einer erfolgreichen Demo:

### 8.1 Ausgangslage

```bash
# Session gestartet mit:
python scripts/run_execution_session.py \
    --strategy ma_crossover \
    --symbol BTC/EUR \
    --steps 10
```

### 8.2 CLI-Report zeigt

```
## Live-Session Summary

- **Session ID:** session_20251208_shadow_abc123
- **Status:** completed
- **Mode:** shadow
- **Symbol:** BTC/EUR
- **Realized PnL:** +45.67 EUR
- **Max Drawdown:** 1.8%
- **Num Orders:** 4
```

### 8.3 Dashboard zeigt

**Snapshot-Kachel:**
- Mode: `shadow` (purple Badge)
- Status: `Completed` (grüner Badge)
- PnL: `+45.67` (grün)
- Max DD: `1.8%`

**Sessions-Tabelle (erste Zeile):**
| Session | Mode | Status | PnL | Max DD | Orders |
|---------|------|--------|-----|--------|--------|
| ...abc123 | shadow | OK | +45.67 | 1.8% | 4 |

### 8.4 Bewertung

✅ **Erfolgreicher Demo-Durchlauf:**
- Session hat Signale generiert
- Orders wurden simuliert
- Keine Risk-Limit-Verletzungen
- PnL leicht positiv
- Max DD unter 5% (gut)

---

## 9. Beispiel-Szenario: Failed-Session

Hier ein Beispiel für eine fehlgeschlagene Session:

### 9.1 Mögliche Ursachen

- **ConnectionError:** Exchange-API nicht erreichbar
- **AuthenticationError:** API-Keys ungültig/fehlend
- **RateLimitError:** Zu viele API-Requests
- **ConfigError:** Ungültige Strategie-Config

### 9.2 Was du im Dashboard siehst

**Snapshot-Kachel:**
- Status: `Failed` (roter Badge)
- Notes: Fehlermeldung sichtbar (z.B. "ConnectionError: Exchange not reachable")

**Sessions-Tabelle:**
- Status: `FAIL` (rot)

### 9.3 Troubleshooting

```bash
# 1. Fehlerdetails aus API holen
curl http://127.0.0.1:8000/api/live_sessions?limit=1 | jq '.[0].notes'

# 2. Registry-File direkt prüfen
ls -lt reports/experiments/live_sessions/ | head -3
cat reports/experiments/live_sessions/<NEUESTE_DATEI>.json | jq .error
```

Weitere Schritte: Siehe Incident-Runbooks in `LIVE_OPERATIONAL_RUNBOOKS.md`.

---

## 10. Zusammenfassung

### 10.1 Was du gelernt hast

Nach diesem Walkthrough kannst du:

1. ✅ Das Web-Dashboard starten und Health-Checks durchführen
2. ✅ Eine Shadow-/Testnet-Session mit dem Phase-80-Runner starten
3. ✅ Session-Ergebnisse über das CLI (Phase 81) auswerten
4. ✅ Das Live-Track Panel (Phase 82) interpretieren
5. ✅ Operator-Checks (Phase 83) für Plausibilitätsprüfungen anwenden
6. ✅ Den Session Explorer (Phase 85) nutzen: Filter, Detail-View, Stats-API
7. ✅ Session-Details im Browser analysieren (Config, Metrics, CLI-Args)

### 10.2 Quick-Reference

| Aufgabe | Kommando |
|---------|----------|
| Dashboard starten | `uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000` |
| Health-Check | `curl http://127.0.0.1:8000/api/health` |
| Shadow-Session | `python scripts/run_execution_session.py --strategy ma_crossover --steps 10` |
| CLI-Report | `python scripts/report_live_sessions.py --summary-only --stdout` |
| Sessions-API | `curl http://127.0.0.1:8000/api/live_sessions?limit=5 \| jq .` |
| Gefilterte Sessions | `curl "http://127.0.0.1:8000/api/live_sessions?mode=shadow&status=completed"` |
| Session-Detail-API | `curl http://127.0.0.1:8000/api/live_sessions/{session_id} \| jq .` |
| Stats-API | `curl http://127.0.0.1:8000/api/live_sessions/stats \| jq .` |

### 10.3 Wichtige URLs (Phase 85 erweitert)

| URL | Beschreibung |
|-----|--------------|
| http://127.0.0.1:8000/ | Dashboard mit Session Explorer |
| http://127.0.0.1:8000/?mode=shadow | Gefiltert nach Shadow-Sessions |
| http://127.0.0.1:8000/?status=completed | Gefiltert nach Completed |
| http://127.0.0.1:8000/session/{id} | Session-Detail-Page (Phase 85) |
| http://127.0.0.1:8000/api/live_sessions | Sessions-API (JSON) |
| http://127.0.0.1:8000/api/live_sessions/stats | Aggregierte Stats (Phase 85) |
| http://127.0.0.1:8000/api/live_sessions/{id} | Session-Detail-API (Phase 85) |
| http://127.0.0.1:8000/api/health | Health-Check |
| http://127.0.0.1:8000/docs | OpenAPI/Swagger UI |

---

## 11. Nächste Schritte

Nach der Demo empfohlen:

1. **Längere Session fahren:**
   - `--duration 60` für 1 Stunde
   - Mehrere Sessions hintereinander

2. **Verschiedene Strategien testen:**
   - `rsi_reversion`, `trend_following`, etc.
   - `--list-strategies` zeigt alle verfügbaren

3. **Testnet-Mode ausprobieren:**
   - `--mode testnet` für validate_only gegen Exchange-API

4. **Operator-Workflow vertiefen:**
   - `docs/PHASE_83_LIVE_TRACK_OPERATOR_WORKFLOW.md` durcharbeiten
   - Tägliche Checklisten einüben

5. **Incident-Drills:**
   - `docs/LIVE_OPERATIONAL_RUNBOOKS.md`, Runbook 12a
   - Absichtlich Fehler provozieren und Behandlung üben

---

## 12. Appendix: 10-Minuten Demo-Cheatsheet

Für schnelle Demos – alle Befehle auf einen Blick:

### Phase A: Setup (2 Min)

```bash
# Terminal 1: Dashboard starten
cd ~/Peak_Trade && source .venv/bin/activate
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000
```

### Phase B: Session starten (3 Min)

```bash
# Terminal 2: Shadow-Session
cd ~/Peak_Trade && source .venv/bin/activate
python scripts/run_execution_session.py --strategy ma_crossover --symbol BTC/EUR --steps 10
```

### Phase C: CLI-Report prüfen (2 Min)

```bash
# Summary der letzten Sessions
python scripts/report_live_sessions.py --summary-only --stdout

# Letzte Session im Detail
python scripts/report_live_sessions.py --limit 1 --output-format markdown --stdout
```

### Phase D: Web-Dashboard erkunden (3 Min)

```bash
# Browser öffnen
open http://127.0.0.1:8000/

# Filter testen
open "http://127.0.0.1:8000/?mode=shadow&status=completed"

# Stats-API
curl http://127.0.0.1:8000/api/live_sessions/stats | jq .
```

### Golden Path im Browser

1. **Dashboard laden:** http://127.0.0.1:8000/
2. **Filter wählen:** Mode = Shadow
3. **Session anklicken** → Detail-Page öffnet sich
4. **Config & Metrics prüfen** auf der Detail-Page
5. **Zurück zur Übersicht** → Link oben links

---

## 13. Referenzen

| Dokument | Beschreibung |
|----------|--------------|
| `docs/PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md` | Strategy-to-Execution Bridge Details |
| `docs/PHASE_81_LIVE_SESSION_REGISTRY.md` | Live-Session-Registry & Report-CLI |
| `docs/PHASE_82_LIVE_TRACK_DASHBOARD.md` | Live-Track Panel im Web-Dashboard |
| `docs/PHASE_83_LIVE_TRACK_OPERATOR_WORKFLOW.md` | Operator-Workflow & Runbooks |
| `docs/PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md` | Session Explorer: Filter, Detail, Stats-API |
| `docs/LIVE_DEPLOYMENT_PLAYBOOK.md` | Stufenplan Shadow → Testnet → Live |
| `docs/LIVE_OPERATIONAL_RUNBOOKS.md` | Konkrete Ops-Anleitungen |
| `docs/CLI_CHEATSHEET.md` | Übersicht aller wichtigen CLI-Befehle |

---

## 14. Changelog

| Datum | Version | Änderung |
|-------|---------|----------|
| 2025-12-08 | v1.0 | Initiale Erstellung Phase 84 Demo-Walkthrough |
| 2025-12-08 | v1.1 | Phase 85 Session Explorer integriert (Filter, Detail-View, Stats-API) |

---

*Dieses Dokument ist Teil der Peak_Trade v1.0 Dokumentation und verbindet die Phasen 80–85 zu einem praxisnahen Operator-Walkthrough mit Session Explorer.*
