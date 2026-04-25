# Peak_Trade – Live-Deployment-Playbook


## Authority and epoch note

This playbook preserves historical and operational deployment context. Deployment, live, go/no-go, checklist, production-ready, complete, or readiness wording is not, by itself, current Master V2 approval, Doubleplay authority, PRE_LIVE completion, First-Live readiness, operator authorization, production readiness, or permission to route orders into any live capital path.

Any live or first-live promotion remains governed by current candidate-specific gate/evidence/signoff artifacts, Scope / Capital Envelope boundaries, Risk / Exposure Caps, Safety / Kill-Switches, and staged Execution Enablement. This docs-only note changes no runtime behavior and changes no checklist items, status values, tables, dates, or historical claims.

> **Phase:** 39 – Live-Deployment-Playbook & Ops-Runbooks
> **Version:** v1.1
> **Zweck:** Stufenplan für den Weg von Research zu Live-Trading
> **Zielgruppe:** Entwickler, Operatoren, Risk-Team

---

## 1. Einleitung

### Was bedeutet „Live-Deployment" bei Peak_Trade?

Peak_Trade ist ein Trading-Framework, das **bewusst mehrstufig** aufgebaut ist. „Live-Deployment" bezeichnet nicht nur den finalen Schritt zum echten Handel, sondern den **gesamten kontrollierten Pfad** von der Strategie-Entwicklung bis zum produktiven Einsatz.

Dieses Playbook beschreibt:
- Die **5 Rollout-Stufen** und ihre jeweiligen Anforderungen
- Die **Gatekeeper-Bedingungen** zwischen den Stufen
- Den konkreten **Deployment-Flow** für Stufen-Übergänge
- **Rollback- und Pause-Strategien** für den Notfall

### Grundprinzipien

1. **Safety First**: Keine Abkürzungen, keine Ausnahmen
2. **Schrittweise Eskalation**: Jede Stufe muss bestanden werden
3. **Nachvollziehbarkeit**: Alle Entscheidungen dokumentiert
4. **Reversibilität**: Jeder Schritt kann rückgängig gemacht werden

---

## 2. Übersicht

### 2.1 Stufenmodell

Peak_Trade folgt einem **5-Stufen-Modell** für den sicheren Weg zu Live-Trading:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Peak_Trade Deployment-Stufen                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Stufe 0          Stufe 1          Stufe 2          Stufe 3          Stufe 4
│  ════════         ════════         ════════         ════════         ════════
│  RESEARCH    ──►  SHADOW      ──►  TESTNET     ──►  SHADOW-LIVE  ──►  LIVE
│                                                                         │
│  • Backtests      • Dry-Run        • Echte API      • Live-Daten       • Echte
│  • Sweeps         • Simulierte     • Testnet-       • Simulierte         Orders
│  • Regime-          Orders           Orders           Orders           • Echtes
│    Analyse        • Lokale         • Echte Fees     • Live-Preise        Kapital
│                     Fills          • Kein echtes    • Paper-PnL
│                                      Kapital
│                                                                         │
│  [✅ AKTIV]       [✅ AKTIV]       [⚠️ PHASE 38+]   [🔜 GEPLANT]      [❌ NICHT
│                                                                          IMPL.]
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Dokumentenstruktur

| Dokument | Zweck |
|----------|-------|
| **Dieses Playbook** | Stufenplan, Voraussetzungen, Hochfahren/Runterfahren |
| `LIVE_READINESS_CHECKLISTS.md` | Detaillierte Checklisten für Stufen-Übergänge |
| `LIVE_OPERATIONAL_RUNBOOKS.md` | Konkrete Step-by-Step-Anleitungen für Ops |
| `RUNBOOKS_AND_INCIDENT_HANDLING.md` | Incident-Response, Troubleshooting |
| `SAFETY_POLICY_TESTNET_AND_LIVE.md` | Safety-Policies |

---

## 2. Stufen-Details

### 2.1 Stufe 0: Research

**Status:** ✅ Aktiv

**Beschreibung:**  
Reine Analyse- und Entwicklungsphase. Keine Verbindung zu echten Exchanges.

**Aktivitäten:**
- Backtests mit historischen Daten
- Parameter-Sweeps
- Regime-Analyse
- Strategie-Entwicklung

**Voraussetzungen:**
- [x] Python-Environment (`.venv`)
- [x] `config/config.toml` konfiguriert
- [x] Testdaten vorhanden
- [x] Alle Unit-Tests grün: `python3 -m pytest -q --tb=no`

**Befehle:**
```bash
# Backtest ausführen
python3 scripts/run_backtest.py --strategy ma_crossover

# Sweep starten
python3 scripts/run_sweep.py \
  --config config/config.toml \
  --strategy ma_crossover \
  --symbol BTC/EUR \
  --grid config/sweeps/ma_crossover.toml \
  --tag deploy-prep \
  --max-runs 10
```

---

### 2.2 Stufe 1: Shadow

**Status:** ✅ Aktiv

**Beschreibung:**  
Shadow-Execution mit simulierten Orders. Keine echten API-Calls, aber vollständiger Order-Flow.

**Aktivitäten:**
- Shadow-Runs mit Strategien
- Lokale Fill-Simulation
- PnL-Tracking
- Risk-Limit-Tests

**Voraussetzungen:**
- [x] Stufe 0 abgeschlossen
- [x] `[shadow]`-Sektion in Config
- [x] `[live_risk]`-Limits definiert
- [x] Shadow-Executor getestet
- [ ] Checklist `Research → Shadow` ausgefüllt (siehe `LIVE_READINESS_CHECKLISTS.md`)

**Befehle:**
```bash
# Shadow-Run starten
python3 scripts/run_shadow_execution.py --strategy ma_crossover --verbose

# Mit Tag für Registry
python3 scripts/run_shadow_execution.py --strategy rsi_strategy --tag daily-shadow
```

**Hochfahren:**
1. Config prüfen: `cat config/config.toml | grep -A 10 "\[shadow\]"`
2. Tests laufen lassen: `python3 -m pytest tests/test_shadow_*.py -v`
3. Shadow-Run starten (siehe oben)

**Runterfahren:**
1. Laufenden Prozess stoppen: `Ctrl+C` oder `kill <PID>`
2. Logs sichern: `cp -r reports&#47;experiments&#47; reports&#47;experiments_backup_$(date +%Y%m%d)&#47;`

#### Shadow-/Testnet-Session mit Phase-80-Runner

**Zweck:** Strategy-to-Execution Bridge (Phase 80) als Shadow- bzw. Testnet-Session fahren, bevor Live-Gates überhaupt in Reichweite kommen.

**Wann nutzen:**
- Nach erfolgreichem Backtest/Sweep, bevor eine Strategie ins Tiering aufgenommen wird
- Um den vollständigen Order-Flow (Strategy → Signals → Orders → ExecutionPipeline) zu validieren
- Um Safety-Gates und RiskLimits unter realistischeren Bedingungen zu beobachten

**Typische Schritte:**

1. Stelle sicher, dass die Strategie im Backtest/Research-Pipeline stabil ist (siehe Research-Dokus).
2. Starte eine Shadow-Session mit dem Phase-80-Runner:
   ```bash
   python3 scripts/run_execution_session.py --strategy ma_crossover --duration 30
   ```
3. Für Testnet-Validierung (`validate_only`):
   ```bash
   python3 scripts/run_execution_session.py --mode testnet --strategy rsi_reversion --duration 30
   ```
4. Werte die Session-Metriken und Logs aus (siehe Abschnitt 8 in `PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md`).
5. **Post-Session-Registry & Reporting (Phase 81):**
   - Stelle sicher, dass die Session von `scripts/run_execution_session.py` erfolgreich beendet wurde (Status `completed` oder definierter Abbruch).
   - Führe das Live-Session-Reporting-CLI aus, um die Registry zu prüfen und eine Kurz-Summary zu erzeugen:
     ```bash
     # Für Shadow-Sessions:
     python3 scripts/report_live_sessions.py \
       --run-type live_session_shadow \
       --status completed \
       --output-format markdown \
       --summary-only \
       --stdout

     # Für Testnet-Sessions:
     python3 scripts/report_live_sessions.py \
       --run-type live_session_testnet \
       --status completed \
       --output-format markdown \
       --summary-only \
       --stdout
     ```
   - Überprüfe die Summary-Ausgabe (PnL, Status-Verteilung, Drawdowns) und dokumentiere Auffälligkeiten gemäß den Runbooks (z.B. Incident-Runbooks für PnL-Divergenzen oder Data-Gaps).
6. Dokumentiere das Ergebnis im Run-Log oder in der Experiments-Registry.

⚠️ **WICHTIG:** Der Phase-80-Runner blockt LIVE-Mode technisch an mehreren Stellen. Nur Shadow und Testnet sind erlaubt – bewusster Safety-First-Ansatz.

**Referenz:**
- Für CLI-Optionen, Metriken-Interpretation und Troubleshooting siehe `PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md`, Abschnitt 8.
- Details zur Live-Session-Registry und Report-CLI: siehe `PHASE_81_LIVE_SESSION_REGISTRY.md`.

---

### 2.3 Stufe 2: Testnet

**Status:** ⚠️ In Vorbereitung (Phase 38+)

**Beschreibung:**  
Echte API-Calls an Exchange-Testnet. Orders werden validiert, aber nicht mit echtem Kapital ausgeführt.

**Aktivitäten:**
- Testnet-Orders (validate_only)
- Echte API-Responses
- Order-Flow-Validierung
- Fee-/Slippage-Vergleich

**Voraussetzungen:**
- [ ] Stufe 1 abgeschlossen
- [ ] Mehrere Wochen Shadow-Erfahrung ohne kritische Incidents
- [ ] `TradingExchangeClient` konfiguriert (Phase 38)
- [ ] API-Credentials in Environment-Variablen
- [ ] Testnet-Limits definiert (`[testnet_limits]`)
- [ ] Checklist `Shadow → Testnet` ausgefüllt

**Config:**
```toml
[exchange]
default_type = "kraken_testnet"

[exchange.kraken_testnet]
enabled = true
validate_only = true  # WICHTIG: Orders nur validieren
```

**Befehle:**
```bash
# Readiness prüfen
python3 scripts/check_live_readiness.py --stage testnet

# Testnet-Stack Smoke-Test
python3 scripts/smoke_test_testnet_stack.py

# Testnet-Session starten (wenn implementiert)
python3 scripts/run_testnet_session.py --profile quick_smoke
```

**Hochfahren:**
1. Readiness-Check: `bash python3 scripts/check_live_readiness.py --stage testnet`
2. Environment-Variablen setzen (API-Keys)
3. Smoke-Test: `bash python3 scripts/smoke_test_testnet_stack.py`
4. Testnet-Session starten

**Runterfahren:**
1. Session beenden: `Ctrl+C` oder graceful shutdown
2. Offene Orders prüfen (sollten keine echten sein bei validate_only)
3. Logs sichern

---

### 2.4 Stufe 3: Shadow-Live

**Status:** 🔜 Geplant (zukünftige Phase)

**Beschreibung:**  
Echte Live-Marktdaten, aber simulierte Order-Ausführung. "Paper-Trading" mit echten Preisen.

**Aktivitäten:**
- Live-Ticker-Daten
- Paper-Order-Simulation mit echten Preisen
- Realistische Slippage-Schätzung
- Performance-Tracking vs. echtem Markt

**Voraussetzungen:**
- [ ] Stufe 2 abgeschlossen
- [ ] Mehrere Wochen Testnet-Erfahrung
- [ ] Performance-Validierung Testnet vs. Shadow
- [ ] Monitoring-System eingerichtet
- [ ] Checklist `Testnet → Shadow-Live` ausgefüllt

---

### 2.5 Stufe 4: Live

**Status:** ❌ Nicht implementiert

**Beschreibung:**  
Echtes Trading mit echtem Kapital. Höchste Anforderungen an Governance, Safety und Monitoring.

**⚠️ WARNUNG:**
```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   Peak_Trade befindet sich NICHT in dieser Phase!                    ║
║                                                                      ║
║   Live-Trading birgt erhebliche finanzielle Risiken.                 ║
║   Diese Stufe erfordert:                                             ║
║   - Monate erfolgreicher Testnet-/Shadow-Live-Erfahrung              ║
║   - Vollständige Governance-Dokumentation                            ║
║   - Zwei-Personen-Freigabe                                           ║
║   - 24/7-Monitoring                                                  ║
║   - Kill-Switch implementiert und getestet                           ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

**Voraussetzungen:**
Siehe `LIVE_READINESS_CHECKLISTS.md`, Abschnitt 4 ("Testnet → Live").

---

## 4. Voraussetzungen und Gatekeeper

### 4.1 Gatekeeper-Matrix

Jeder Stufen-Übergang erfordert spezifische Voraussetzungen und Freigaben:

| Übergang | Mindestvoraussetzungen | Entscheider | Dokumentation |
|----------|------------------------|-------------|---------------|
| 0 → 1 | Backtest OK, Code-Review | Owner | Checklist Research→Shadow |
| 1 → 2 | 2+ Wochen Shadow, Korrelation OK | Owner + Reviewer | Checklist Shadow→Testnet |
| 2 → 3 | 4+ Wochen Testnet, Kill-Switch OK | Owner + Risk Officer | Checklist Testnet→Shadow-Live |
| 3 → 4 | 8+ Wochen Shadow-Live, Governance OK | Owner + Risk Officer + 2. Person | Vollständige Live-Checklist |

### 4.2 Harte Blocker (verhindern JEDEN Übergang)

Diese Bedingungen blockieren jeden Stufen-Übergang:

1. **Offene kritische Bugs** im Execution- oder Risk-Layer
2. **Nicht-grüne Tests** in `python3 -m pytest tests/ -q` (Baseline muss grün sein)
3. **Fehlende oder veraltete Checklists**
4. **Unklare Verantwortlichkeiten** (Owner/Risk Officer nicht definiert)
5. **Fehlende Runbooks** für die Zielstufe

### 4.3 Weiche Kriterien (Ermessensspielraum)

Bei diesen Kriterien ist Ermessen möglich, aber Abweichungen müssen dokumentiert werden:

- Exakte Zeitdauern (z.B. „4 Wochen" → ggf. 3,5 Wochen bei exzellenten Ergebnissen)
- Exakte Performance-Schwellen (z.B. Sharpe 0.95 statt 1.0 bei guter Konsistenz)
- Zusätzliche Strategien oder Symbole

---

## 5. Deployment-Flow

### 5.1 Ablauf: Shadow → Testnet (Stufe 1 → 2)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ÜBERGANG SHADOW → TESTNET                             │
└─────────────────────────────────────────────────────────────────────────┘

Schritt 1: Vorbereitung (1-2 Tage vor Übergang)
─────────────────────────────────────────────────
□ Shadow-Statistiken exportieren und analysieren
  $ python3 scripts/experiments_explorer.py list --run-type shadow_run --limit 50

□ Checklist "Shadow → Testnet" aus docs/LIVE_READINESS_CHECKLISTS.md kopieren
  und vollständig ausfüllen

□ Testnet-Credentials prüfen (ohne sie im Klartext zu loggen!)
  $ test -n "$KRAKEN_TESTNET_API_KEY" && echo "API Key gesetzt"

□ Config für Testnet vorbereiten
  - [environment] mode = "testnet"
  - [testnet_limits.*] konfigurieren
  - [testnet_profiles.*] definieren

Schritt 2: Review (Tag des Übergangs, vor Aktivierung)
─────────────────────────────────────────────────────────
□ Checklist von zweiter Person (Reviewer/Risk Officer) prüfen lassen
□ Offene Punkte klären und dokumentieren
□ Freigabe einholen (Owner)

Schritt 3: Technische Aktivierung
─────────────────────────────────────
□ Config committen (ohne Secrets!)
  $ git add config/config.toml
  $ git commit -m "feat: activate testnet mode"

□ Tests ausführen
  $ python3 -m pytest tests/ -q --tb=short

□ Dry-Run des Testnet-Profils
  $ python3 -m scripts.orchestrate_testnet_runs --profile <PROFIL> --dry-run

□ Bei Erfolg: Echter erster Testnet-Run
  $ python3 -m scripts.orchestrate_testnet_runs --profile <PROFIL>

Schritt 4: Monitoring & Dokumentation
───────────────────────────────────────
□ Ersten Run überwachen (Logs, Reports)
□ Run-ID und Ergebnis dokumentieren
□ Ausgefüllte Checklist archivieren
  → reports/checklists/YYYY-MM-DD_shadow_to_testnet_vX.Y.md
```

### 5.2 Ablauf: Testnet → Live (Stufe 2/3 → 4)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ÜBERGANG TESTNET → LIVE                               │
└─────────────────────────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════════════════════════╗
║  WARNUNG: Ab dieser Stufe sind ECHTE FINANZIELLE VERLUSTE möglich!       ║
║  Alle Schritte erfordern besondere Sorgfalt und Two-Man-Rule.            ║
╚══════════════════════════════════════════════════════════════════════════╝

Schritt 1: Vorprüfung (1 Woche vor geplantem Übergang)
────────────────────────────────────────────────────────
□ Testnet-Statistiken über gesamten Zeitraum analysieren
□ Order-Erfolgsquote berechnen (Ziel: > 95%)
□ Kill-Switch-Funktionalität testen
□ Checklist "Testnet → Live" vollständig ausfüllen

Schritt 2: Governance-Review (2-3 Tage vor Übergang)
──────────────────────────────────────────────────────
□ Checklist von Risk Officer prüfen lassen
□ Finanzielle Impact-Analyse reviewen
□ Kapital-Allokation bestätigen
□ Notfall-Kontakte aktualisieren

Schritt 3: Two-Man-Rule-Freigabe
──────────────────────────────────
□ Owner-Freigabe dokumentieren (Datum + Unterschrift)
□ Zweite-Person-Freigabe dokumentieren (Datum + Unterschrift)
□ Freigabe-Dokument archivieren

Schritt 4: Technische Aktivierung
─────────────────────────────────────
□ Live-Credentials sicher hinterlegen (Env-Variablen)
□ Config für Live vorbereiten mit konservativen Limits
□ Finale Test-Runde: python3 -m pytest tests/ -v
□ Dry-Run mit Live-Preview

Schritt 5: Go-Live
────────────────────
□ System starten (mit Owner und 2. Person anwesend)
□ Ersten Trade überwachen (beide Personen)
□ Monitoring aktiviert und Alerts konfiguriert
```

---

## 6. Rollback- und Pause-Strategien

### 6.1 Pause-Trigger (wann pausieren?)

| Trigger | Schwere | Aktion |
|---------|---------|--------|
| Daily-Loss-Limit erreicht | Hoch | Sofort-Pause, automatisch |
| API-Fehlerrate > 10% | Mittel | Manuelle Pause nach 3. Fehler |
| Unbekannte Exception im Core | Hoch | Sofort-Pause |
| PnL-Divergenz > 50% vs. Erwartung | Mittel | Pause nach Bestätigung |
| Data-Gap > 5 Minuten | Mittel | Pause, Datenquelle prüfen |

### 6.2 Pause-Prozedur

```
PAUSE-PROZEDUR
═══════════════

1. STOPPEN (0-1 Minute)
   □ Scheduler/Daemon stoppen
     $ kill $(pgrep -f run_scheduler.py)
   □ Keine neuen Orders mehr senden
   □ Offene Orders prüfen (cancel falls nötig)

2. SICHERN (1-5 Minuten)
   □ Aktuelle Position notieren
   □ Letzte Logs sichern
     $ cp -r logs/ logs_backup_$(date +%Y%m%d_%H%M%S)/
   □ Registry-State exportieren

3. KOMMUNIZIEREN (5-10 Minuten)
   □ Team/Owner informieren
   □ Grund der Pause dokumentieren

4. ANALYSIEREN (variabel)
   □ Logs durchgehen
   □ Root-Cause dokumentieren
```

### 6.3 Rollback-Szenarien

#### Szenario A: Rollback auf vorherige Stufe

**Wann:** Fundamentale Probleme in aktueller Stufe

**Vorgehen:**
1. System pausieren (siehe oben)
2. Config auf vorherige Stufe zurücksetzen
3. System in vorheriger Stufe neu starten
4. Incident-Report erstellen

#### Szenario B: Rollback einer Strategie

**Wann:** Eine spezifische Strategie performt schlecht

**Vorgehen:**
1. Strategie aus Rotation nehmen (Config-Änderung)
2. Offene Positionen der Strategie schließen
3. Strategie analysieren (Backtest mit aktuellen Daten)

#### Szenario C: Notfall-Liquidation

**Wann:** Kritische Situation erfordert sofortiges Schließen aller Positionen

**Vorgehen:**
1. Kill-Switch aktivieren
2. Alle offenen Orders canceln
3. Alle Positionen market-close
4. System in Read-Only-Modus

### 6.4 Wiederanlauf nach Pause

```
WIEDERANLAUF-PROZEDUR
═════════════════════

Voraussetzungen prüfen:
□ Ursache identifiziert und behoben
□ Fix getestet (Backtest/Shadow wenn möglich)
□ Dokumentation aktualisiert

Schritte:
1. □ Config prüfen
2. □ Tests ausführen: python3 -m pytest tests/ -q
3. □ Dry-Run durchführen
4. □ Bei Live: Freigabe durch Owner/2. Person
5. □ System starten
6. □ Erhöhtes Monitoring für erste Stunden
```

---

## 7. Verfahren: Hochfahren

### 7.1 Generisches Hochfahr-Verfahren

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Hochfahr-Verfahren (alle Stufen)                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. VORBEREITUNG                                                    │
│     ├── Config prüfen (config/config.toml)                          │
│     ├── Environment-Variablen setzen (falls nötig)                  │
│     └── Baseline-Tests: python3 -m pytest -q --tb=no                │
│                                                                     │
│  2. READINESS-CHECK                                                 │
│     ├── python3 scripts/check_live_readiness.py --stage <STUFE>     │
│     └── Bei Fehlern: STOPP, Probleme beheben                        │
│                                                                     │
│  3. SMOKE-TEST                                                      │
│     ├── python3 scripts/smoke_test_testnet_stack.py                 │
│     └── Bei Fehlern: STOPP, Probleme beheben                        │
│                                                                     │
│  4. START                                                           │
│     ├── Entsprechendes Script starten                               │
│     ├── Logs beobachten                                             │
│     └── Erste Orders/Signale verifizieren                           │
│                                                                     │
│  5. MONITORING                                                      │
│     ├── Logs: tail -f logs/*.log                                    │
│     ├── Registry: python3 scripts/experiments_explorer.py list      │
│     └── Bei Anomalien: Runterfahren (siehe 4)                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Quick-Start: Shadow-Run

```bash
# 1. Environment aktivieren
cd ~/Peak_Trade
source .venv/bin/activate

# 2. Tests prüfen
python3 -m pytest -q --tb=no

# 3. Shadow-Run starten
python3 scripts/run_shadow_execution.py --strategy ma_crossover --verbose
```

### 7.3 Quick-Start: Testnet (wenn implementiert)

```bash
# 1. Environment aktivieren
cd ~/Peak_Trade
source .venv/bin/activate

# 2. API-Keys setzen
export KRAKEN_TESTNET_API_KEY="..."
export KRAKEN_TESTNET_API_SECRET="..."

# 3. Readiness prüfen
python3 scripts/check_live_readiness.py --stage testnet

# 4. Smoke-Test
python3 scripts/smoke_test_testnet_stack.py

# 5. Testnet-Session starten
python3 scripts/run_testnet_session.py --profile quick_smoke
```

---

## 8. Verfahren: Runterfahren

### 8.1 Normales Runterfahren

```bash
# Option 1: Graceful (Ctrl+C im Terminal)
# Wartet auf laufende Operations, dann Exit

# Option 2: Prozess-ID finden und stoppen
pgrep -f "python3 scripts/run_"
kill <PID>

# Option 3: Alle Peak_Trade-Prozesse stoppen (Vorsicht!)
pkill -f "python3 scripts/run_"
```

### 8.2 Notfall-Runterfahren

Bei kritischen Incidents:

```bash
# 1. Sofort alle Prozesse stoppen
pkill -9 -f "python3 scripts/run_"

# 2. Logs sichern
cp -r logs/ logs_incident_$(date +%Y%m%d_%H%M%S)/
cp -r reports/experiments/ reports/experiments_incident_$(date +%Y%m%d_%H%M%S)/

# 3. Incident dokumentieren (siehe RUNBOOKS_AND_INCIDENT_HANDLING.md)
```

### 8.3 Checkliste nach Runterfahren

- [ ] Prozesse beendet (`pgrep -f "python3 scripts&#47;run_"` zeigt nichts)
- [ ] Logs gesichert
- [ ] Bei Testnet/Live: Offene Orders geprüft
- [ ] Registry-State dokumentiert
- [ ] Bei Incident: Incident-Report erstellt

---

## 9. Config-Referenz

### 9.1 Wichtige Config-Sektionen je Stufe

| Stufe | Config-Sektionen |
|-------|------------------|
| 0 (Research) | `[backtest]`, `[strategy.*]`, `[risk]` |
| 1 (Shadow) | `[shadow]`, `[live_risk]`, `[shadow_paper]` |
| 2 (Testnet) | `[exchange]`, `[exchange.kraken_testnet]`, `[testnet_limits]` |
| 3 (Shadow-Live) | `[live_exchange]`, `[live_risk]` |
| 4 (Live) | Alle oben + `[live]` mit `enabled = true` |

### 9.2 Environment-Variablen

| Variable | Stufe | Beschreibung |
|----------|-------|--------------|
| `PEAK_TRADE_CONFIG_PATH` | Alle | Alternativer Config-Pfad |
| `KRAKEN_TESTNET_API_KEY` | 2+ | Testnet API-Key |
| `KRAKEN_TESTNET_API_SECRET` | 2+ | Testnet API-Secret |
| `KRAKEN_API_KEY` | 4 | Live API-Key (nur Stufe 4!) |
| `KRAKEN_API_SECRET` | 4 | Live API-Secret (nur Stufe 4!) |

**⚠️ NIEMALS API-Keys in Config-Dateien oder Code speichern!**

---

## 10. Troubleshooting

### 10.1 Häufige Probleme

| Problem | Mögliche Ursache | Lösung |
|---------|------------------|--------|
| "Config nicht gefunden" | Falscher Pfad | `PEAK_TRADE_CONFIG_PATH` setzen |
| "Tests fehlgeschlagen" | Code-Änderungen | `python3 -m pytest -v` für Details |
| "Readiness-Check failed" | Voraussetzungen fehlen | Output lesen, Probleme beheben |
| "Exchange-Fehler" | API-Keys falsch/fehlend | Environment-Variablen prüfen |
| "Risk-Limit verletzt" | Limits zu streng | `[live_risk]` prüfen |

### 10.2 Diagnose-Befehle

```bash
# Config prüfen
python3 -c "from src.core.peak_config import load_config; c=load_config(); print(c.get('exchange.default_type'))"

# Environment prüfen
env | grep -i peak
env | grep -i kraken

# Prozesse prüfen
pgrep -af "python.*peak_trade"

# Logs prüfen
tail -100 logs/*.log
```

---

## 11. Referenzen

| Dokument | Beschreibung |
|----------|--------------|
| `LIVE_READINESS_CHECKLISTS.md` | Detaillierte Checklisten |
| `LIVE_OPERATIONAL_RUNBOOKS.md` | Konkrete Ops-Anleitungen |
| `RUNBOOKS_AND_INCIDENT_HANDLING.md` | Incident-Response |
| `SAFETY_POLICY_TESTNET_AND_LIVE.md` | Safety-Policies |
| `GOVERNANCE_AND_SAFETY_OVERVIEW.md` | Governance-Übersicht |
| `PHASE_37_TESTNET_ORCHESTRATION_AND_LIMITS.md` | Testnet-Orchestrierung |
| `PHASE_38_EXCHANGE_V0_TESTNET.md` | Exchange-Integration |
| `PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md` | Strategy-to-Execution Bridge & Shadow/Testnet Runner v0 |
| `PHASE_81_LIVE_SESSION_REGISTRY.md` | Live-Session-Registry & Report-CLI |
| `PHASE_82_LIVE_TRACK_DASHBOARD.md` | Live-Track Panel im Web-Dashboard |
| `PHASE_83_LIVE_TRACK_OPERATOR_WORKFLOW.md` | Operator-Workflow für Live-Track Panel |
| `PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md` | Demo Walkthrough & Case Study (10–15 Min) |
| `PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md` | Session Explorer: Filter, Detail, Stats-API |

---

## 12. Live-Track Panel im Betrieb

### 12.1 Dashboard als Monitoring-Zentrale

Das Live-Track Panel (Phase 82) bietet eine zentrale Übersicht über alle laufenden und abgeschlossenen Sessions:

```bash
# Dashboard starten
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000

# Browser öffnen
open http://127.0.0.1:8000/
```

**Wichtige URLs:**

| URL | Funktion |
|-----|----------|
| http://127.0.0.1:8000/ | Dashboard mit Live-Track Panel |
| http://127.0.0.1:8000/api/live_sessions | JSON-API für Sessions |
| http://127.0.0.1:8000/api/health | Health-Check |
| http://127.0.0.1:8000/docs | OpenAPI/Swagger UI |

### 12.2 Live-Track Integration in Stufen-Workflow

#### Stufe 1 (Shadow) - Dashboard-Checks

```
VOR SESSION:
□ Dashboard öffnen und Health prüfen
□ Keine unbehandelten failed-Sessions in letzter Zeit

NACH SESSION:
□ Dashboard refreshen
□ Session erscheint in Tabelle mit Status "completed"
□ PnL und Drawdown plausibel
```

#### Stufe 2 (Testnet) - Erweitertes Monitoring

```
WÄHREND SESSION:
□ Dashboard alle 15-30 Min prüfen
□ Status-Änderungen beobachten
□ Bei "failed": Sofort stoppen und Notes prüfen

NACH SESSION:
□ API-Call für detaillierte Metriken:
  curl http://127.0.0.1:8000/api/live_sessions?limit=1 | jq .
□ Ergebnis dokumentieren
```

### 12.3 Kombination CLI + Dashboard

Für vollständige Transparenz beide Tools nutzen:

```bash
# Terminal 1: Dashboard
uvicorn src.webui.app:app --host 127.0.0.1 --port 8000

# Terminal 2: Session starten
python3 scripts/run_execution_session.py --mode shadow --strategy ma_crossover

# Terminal 3: CLI-Reports
python3 scripts/report_live_sessions.py --summary-only --stdout
```

**Empfohlener Workflow:** Siehe `PHASE_83_LIVE_TRACK_OPERATOR_WORKFLOW.md` für detaillierten Tagesablauf.

**Demo-Walkthrough:** Für einen praxisnahen 10–15 Minuten Durchlauf siehe [`PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md`](PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md).

### 12.4 Live-Track Session Explorer prüfen (Phase 85)

**Ziel:**
Nach einer Shadow-/Testnet-Session die Ergebnisse im Web-Dashboard kontrollieren und Auffälligkeiten markieren.

**Voraussetzungen:**
- Uvicorn-Server läuft: `uvicorn src.webui.app:app --reload` (oder entsprechendes Start-Skript)
- Live-Session-Registry enthält die Session (Phase 80/81 abgeschlossen)

**Vorgehen:**

1. **Dashboard öffnen**
   - Browser: `http://127.0.0.1:8000/`
   - Standardansicht zeigt aktuelle Live-Track Sessions.

2. **Nach Mode filtern**
   - Shadow-Run: `&#47;?mode=shadow`
   - Testnet-Run: `&#47;?mode=testnet`
   - Optional: Status filtern, z.B. `&#47;?mode=testnet&status=failed`

3. **Session-Detail öffnen**
   - Gewünschte Session-Zeile anklicken
   - Detailseite `/session/{session_id}` prüfen:
     - Config (Strategy, Presets, Environment)
     - Kennzahlen (Dauer, Result-Status, ggf. PnL/Exposure)
     - Hinweise zu passenden CLI-Befehlen (Re-Run / Debug)

4. **Statistiken prüfen (optional)**
   - API: `/api/live_sessions/stats`
   - Verwendung:
     - Wie viele Sessions heute pro Mode?
     - Wie viele `failed` vs. `completed`?

5. **Safety-Hinweise beachten**
   - Sessions im Mode `live` werden im UI mit ⚠️ markiert
   - Live-Mode ist in Shadow-/Testnet-Playbooks nicht vorgesehen → nur zur Übersicht, nicht aktiv nutzen.

**Erwartetes Ergebnis:**
- Alle relevanten Shadow-/Testnet-Sessions sind im Explorer sichtbar
- Auffällige Sessions (z.B. `failed`) sind identifiziert und markiert
- Operator weiß, welche Runs als nächstes im Detail analysiert oder erneut gefahren werden sollen.

**Referenz:** [`PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md`](PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md)

### 12.5 Kurz-How-To: Live-Track Dashboard Demo (ca. 2 Minuten)

Dieser Ablauf ist für Demos, Onboarding und interne Showcases gedacht.
Ziel: In **2 Minuten** das Live-Track Web-Dashboard v1.1 zeigen und die Safety-Botschaft transportieren – ohne echte Live-Orders.

**Voraussetzungen:**

* Mindestens **eine aktuelle Shadow-/Testnet-Session** wurde gemäß Playbook gestartet
  (z.B. über `scripts/run_execution_session.py` im Shadow-/Testnet-Mode).
* Das Web-Dashboard läuft (FastAPI/Uvicorn gestartet, URL bekannt).

**Demo-Ablauf (High-Level):**

1. **CLI → Registry zeigen**
   * Kurz auf die zuletzt gestartete Session hinweisen (Run-ID, Mode, Tiering).
   * Optional: `live_session_registry` / Report-CLI erwähnen.

2. **Web-Dashboard öffnen**
   * Dashboard-URL im Browser öffnen.
   * Zeigen, dass die zuletzt gestartete Session im Live-Track Panel / in der Tabelle sichtbar ist.

3. **System-Header & Safety hervorheben**
   * Betriebsmodus, Tiering und **Live-Lock / Safety-Lock** erklären.
   * Klar sagen: **Live-Mode bleibt blockiert**, Demo läuft nur in Shadow-/Testnet.

4. **Sessions & Status-Kacheln kurz erklären**
   * Anzahl Sessions, Shadow/Testnet-Verteilung, letzte Runs.
   * Eine konkrete Session anklicken / hervorheben.

5. **Brücke CLI ↔ Dashboard**
   * Verbindung erklären: „Was wir in der CLI gestartet/registriert haben, taucht hier im UI auf."

**Detail-Script & Referenzen:**

* Ausführlicher Schritt-für-Schritt-Walkthrough:
  [`docs/PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md`](PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md)

* Kompaktes 2-Minuten-Moderationsscript inkl. Cheat-Sheet:
  [`docs/DEMO_SCRIPT_DASHBOARD_V11.md`](DEMO_SCRIPT_DASHBOARD_V11.md)

* **Schnellstart-How-To (3 Minuten, CLI → Readiness → Dashboard):**
  [`docs/HOW_TO_LIVE_TRACK_V11_IN_3_MIN.md`](HOW_TO_LIVE_TRACK_V11_IN_3_MIN.md)

Damit haben Operatoren neben dem Playbook-Flow auch ein kurzes, reproduzierbares Demo-Format für das Live-Track Dashboard v1.1.

---

## 13. Changelog

- **v1.7** (Dashboard v1.1, 2025-12): Demo How-To
  - Neuer Abschnitt 12.5: Kurz-How-To für Live-Track Dashboard Demo
  - Verweise auf Phase-84-Walkthrough und 2-Minuten-Script

- **v1.6** (Phase 85, 2025-12): Live-Track Session Explorer
  - Neuer Abschnitt 12.4: Live-Track Session Explorer prüfen
  - Filter- und Detail-Workflow für Post-Session-Analyse
  - Referenz zu `PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md` hinzugefügt

- **v1.5** (Phase 84, 2025-12): Live-Track Demo Walkthrough
  - Referenz zu Phase 84 Demo Walkthrough hinzugefügt
  - Abschnitt 12.3 um Demo-Verweis ergänzt

- **v1.4** (Phase 82/83, 2025-12): Live-Track Dashboard & Operator-Workflow
  - Neuer Abschnitt 12: Live-Track Panel im Betrieb
  - Dashboard-Integration in Stufen-Workflow (Shadow, Testnet)
  - Referenzen zu Phase 82/83 Dokumentation hinzugefügt

- **v1.3** (Phase 81, 2025-12): Live-Session-Registry & Report-CLI ergänzt
  - Post-Session-Registry & Reporting als Schritt im Shadow-/Testnet-Ablauf verankert
  - CLI-Beispiele für `scripts/report_live_sessions.py` hinzugefügt
  - Referenz zu `PHASE_81_LIVE_SESSION_REGISTRY.md` hinzugefügt

- **v1.2** (Phase 80, 2025-12): Phase-80-Runner ergänzt
  - Shadow-/Testnet-Session mit Phase-80-Runner (Strategy-to-Execution Bridge) dokumentiert
  - Referenz zu `PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md` hinzugefügt

- **v1.1** (Phase 39, 2025-12): Erweitert
  - Gatekeeper-Matrix hinzugefügt
  - Deployment-Flow-Prozeduren ergänzt
  - Rollback- und Pause-Strategien erweitert
  - Nummerierung korrigiert

- **v1.0** (Phase 39, 2024-12): Initial erstellt
  - Stufenmodell dokumentiert
  - Hochfahr-/Runterfahrverfahren
  - Config-Referenz
  - Troubleshooting

---

*Dieses Playbook ist ein lebendes Dokument. Bei Änderungen an Prozessen oder Architektur sollte es aktualisiert werden.*
