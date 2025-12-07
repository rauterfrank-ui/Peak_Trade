# Peak_Trade – Runbooks & Incident-Handling

> **Status:** Phase 25 – Governance & Safety-Dokumentation
> **Scope:** Runbooks für Shadow-Modus, Vorlagen für Testnet/Live
> **Hinweis:** Runbooks sind lebende Dokumente, die bei Bedarf aktualisiert werden

---

## 1. Einleitung

### Was ist ein Runbook?

Ein **Runbook** ist eine dokumentierte Schritt-für-Schritt-Anleitung für wiederkehrende oder kritische Operationen. Runbooks stellen sicher, dass:

- Operationen konsistent durchgeführt werden
- Im Notfall keine Zeit mit Nachdenken verloren geht
- Wissen nicht nur in einzelnen Köpfen steckt

### Warum Runbooks für Peak_Trade?

Auch im Shadow-Modus ist systematisches Vorgehen wichtig:

- **Reproduzierbarkeit**: Gleiche Bedingungen, gleiche Ergebnisse
- **Fehlerminimierung**: Checklisten verhindern vergessene Schritte
- **Vorbereitung**: Übung für spätere Testnet-/Live-Szenarien
- **Dokumentation**: Nachvollziehbarkeit aller Aktionen

### Runbooks aktiv üben

Runbooks sollten **aktiv geübt** werden, um sicherzustellen, dass sie in der Praxis funktionieren. Die Szenarien für Incident-Drills sind in [`INCIDENT_SIMULATION_AND_DRILLS.md`](INCIDENT_SIMULATION_AND_DRILLS.md) dokumentiert (Phase 56). Regelmäßige Drills helfen dabei, Runbooks zu validieren und kontinuierlich zu verbessern.

---

## 2. Runbook: Shadow-Run

### 2.1 Zweck

Durchführung eines Shadow-/Dry-Run mit der Shadow-Execution-Pipeline (Phase 24).

### 2.2 Voraussetzungen

- [ ] Python-Environment aktiviert (`.venv`)
- [ ] `config.toml` vorhanden und aktuell
- [ ] `[shadow]`-Sektion konfiguriert
- [ ] Datenquelle verfügbar (CSV oder API-Zugang)

### 2.3 Durchführung

**Schritt 1: Konfiguration prüfen**

```bash
# Config-Datei prüfen
cat config.toml | grep -A 10 "\[shadow\]"

# Erwartete Ausgabe:
# [shadow]
# enabled = true
# run_type = "shadow_run"
# fee_rate = 0.0005
# slippage_bps = 0.0
```

**Schritt 2: Strategie & Daten prüfen**

```bash
# Verfügbare Strategien auflisten
python -c "from src.strategies.registry import get_available_strategy_keys; print(get_available_strategy_keys())"

# Datenquelle prüfen (falls CSV)
ls -la data/*.csv
```

**Schritt 3: Shadow-Run starten**

```bash
# Standard-Run mit ma_crossover
python scripts/run_shadow_execution.py --strategy ma_crossover --verbose

# Mit CSV-Daten und Datumsbeschränkung
python scripts/run_shadow_execution.py \
    --strategy rsi_strategy \
    --data-file data/btc_eur_1h.csv \
    --start 2023-01-01 \
    --end 2023-12-31 \
    --tag shadow_run_v1

# Mit Fee-/Slippage-Überschreibung
python scripts/run_shadow_execution.py \
    --fee-rate 0.001 \
    --slippage-bps 10 \
    --verbose
```

**Schritt 4: Ergebnisse prüfen**

```bash
# Experiments-Registry prüfen
python scripts/experiments_explorer.py --run-type shadow_run --limit 5

# Oder: HTML-Report generieren (falls Reporting v2 aktiviert)
python scripts/report_experiment.py --run-id <RUN_ID>
```

**Schritt 5: Dokumentation**

- [ ] Run-ID notieren
- [ ] Ergebnis-Summary dokumentieren
- [ ] Bei Auffälligkeiten: Incident-Prozess starten

### 2.4 Troubleshooting

| Problem | Mögliche Ursache | Lösung |
|---------|------------------|--------|
| "Config nicht gefunden" | Falscher Pfad | `--config` mit korrektem Pfad |
| "Strategie nicht gefunden" | Tippfehler oder nicht registriert | `get_available_strategy_keys()` prüfen |
| "Keine Daten" | CSV fehlt oder leer | Datenquelle prüfen |
| "Shadow disabled" | `[shadow].enabled = false` | Config korrigieren |

---

## 3. Runbook: System pausieren / stoppen

### 3.1 Zweck

Sichere Pausierung oder Abschaltung des Systems bei unerwartetem Verhalten.

### 3.2 Wann pausieren?

- Shadow-Run zeigt unerwartete Resultate (z.B. extreme PnL)
- Viele Risk-Blocks in kurzer Zeit
- Fehler/Exceptions in Scheduler oder Daemon
- Unklare Situation, die Analyse erfordert

### 3.3 Durchführung: Scheduler stoppen

Falls der Scheduler (`run_scheduler.py`) läuft:

**Schritt 1: Scheduler-Prozess finden**

```bash
# Prozess-ID finden
ps aux | grep run_scheduler

# Oder mit pgrep
pgrep -f run_scheduler.py
```

**Schritt 2: Scheduler stoppen**

```bash
# Sanft stoppen (SIGTERM)
kill <PID>

# Falls notwendig: Forciert stoppen (SIGKILL)
kill -9 <PID>
```

**Schritt 3: Keine neuen Runs starten**

- Keine manuellen `run_*.py`-Aufrufe
- Scheduler nicht neu starten

### 3.4 Durchführung: Logs sichern

```bash
# Logs kopieren
cp -r reports/experiments/ reports/experiments_backup_$(date +%Y%m%d_%H%M%S)/

# Scheduler-Logs (falls vorhanden)
cp logs/*.log logs_backup_$(date +%Y%m%d_%H%M%S)/
```

### 3.5 Nachbereitung

1. **Incident-Analyse starten** (siehe Abschnitt 4)
2. **Dokumentation**: Zeitpunkt und Grund der Pausierung
3. **Kommunikation**: Team informieren (falls relevant)

---

## 4. Incident-Handling

### 4.1 Definition: Was ist ein Incident?

Ein **Incident** ist ein unerwartetes Ereignis, das den normalen Betrieb beeinträchtigt oder ein Risiko darstellt.

**Beispiele für Incidents:**
- Unerwartete Trade-Frequenz (viel mehr/weniger als erwartet)
- Ausreißer im PnL (extrem hoher Gewinn oder Verlust)
- Dauerhafte Fehler in Risk-/Execution-Layern
- System-Crashes oder Hangs
- Datenverlust oder -korruption

### 4.2 Schweregrade

| Grad | Name | Beschreibung | Reaktionszeit |
|------|------|--------------|---------------|
| **Low** | Minor | Kleine Anomalie, System läuft normal | Innerhalb 1 Woche |
| **Medium** | Significant | Merkliche Abweichung, System eingeschränkt | Innerhalb 24h |
| **High** | Critical | Kritischer Fehler, System gestoppt | Sofort |

### 4.3 Beispiele und Einstufung

| Situation | Grad | Reaktion |
|-----------|------|----------|
| Ein Backtest zeigt leicht andere Ergebnisse | Low | Ursache dokumentieren, bei Gelegenheit analysieren |
| Shadow-Run erzeugt doppelt so viele Orders wie erwartet | Medium | System pausieren, analysieren |
| Risk-Limits werden ignoriert | High | Sofort stoppen, Code-Review |
| Unbekannte Exception crasht System | Medium–High | Logs sichern, Ursache finden |
| API-Credentials kompromittiert | High | Sofort rotieren, Security-Review |

**Hinweis:** Siehe auch Drill-Szenarien in [`INCIDENT_SIMULATION_AND_DRILLS.md`](INCIDENT_SIMULATION_AND_DRILLS.md) für praktische Übungen zu diesen Incident-Typen.

### 4.4 Reaktionsschema

#### Phase 1: Sofortmaßnahmen (0–15 Min)

1. **Erkennen**: Incident identifizieren und Schweregrad einschätzen
2. **Stoppen**: Bei Medium/High: System pausieren (Runbook 3)
3. **Sichern**: Logs und Registry-State sichern
4. **Melden**: Team/Owner informieren (bei High)

#### Phase 2: Analyse (15 Min – 24h)

1. **Logs prüfen**: Experiments-Registry, Scheduler-Logs, Error-Logs
2. **Reproduzieren**: Kann der Incident nachgestellt werden?
3. **Root Cause**: Was ist die eigentliche Ursache?
4. **Dokumentieren**: Alles Gefundene festhalten

#### Phase 3: Behebung (24h – 1 Woche)

1. **Fix implementieren**: Code-/Config-Änderung
2. **Tests**: Neue Tests für den Fall schreiben
3. **Review**: Änderung reviewen lassen
4. **Deploy**: Fix aktivieren

#### Phase 4: Nachbereitung (Post-Mortem)

1. **Incident-Report**: Formale Dokumentation
2. **Lessons Learned**: Was haben wir gelernt?
3. **Prozess-Verbesserung**: Wie verhindern wir Wiederholung?
4. **Archivierung**: Report im Incident-Archiv ablegen

### 4.5 Incident-Report-Vorlage

```markdown
# Incident Report: [KURZER TITEL]

**Datum:** YYYY-MM-DD
**Schweregrad:** Low / Medium / High
**Status:** Open / Resolved

## Zusammenfassung
[2-3 Sätze: Was ist passiert?]

## Timeline
- HH:MM – Incident entdeckt
- HH:MM – System pausiert
- HH:MM – Analyse gestartet
- HH:MM – Root Cause gefunden
- HH:MM – Fix deployed

## Root Cause
[Technische Erklärung der Ursache]

## Impact
- Betroffene Systeme: [Liste]
- Betroffene Runs: [Run-IDs]
- Finanzieller Impact: [Keiner / Simulation / Real]

## Resolution
[Beschreibung der Lösung]

## Lessons Learned
1. [Lesson 1]
2. [Lesson 2]

## Action Items
- [ ] [Action 1]
- [ ] [Action 2]
```

---

## 5. Vorbereitung auf Testnet-/Live-Runbooks

### 5.1 Platzhalter: Zusätzliche Runbooks (zukünftig)

Für spätere Phasen (Testnet/Live) werden folgende Runbooks benötigt:

| Runbook | Phase | Beschreibung |
|---------|-------|--------------|
| **Start Testnet** | 2+ | System mit Testnet-Verbindung starten |
| **Stop Testnet** | 2+ | Testnet-Verbindung sauber beenden |
| **Start Live** | 4 | Live-Trading aktivieren (strenge Bedingungen) |
| **Stop Live (Normal)** | 4 | Geordnetes Beenden des Live-Tradings |
| **Kill Switch** | 4 | Notfall-Abschaltung aller Live-Orders |
| **Graceful Degradation** | 4 | Teilweiser Betrieb bei Störungen |
| **Position Liquidation** | 4 | Alle Positionen schließen |

### 5.2 Mindestanforderungen für Live-Runbooks

Bevor Stufe 4 (Live) aktiviert wird, müssen folgende Runbooks:

1. **Existieren**: Vollständig dokumentiert
2. **Reviewed sein**: Von mindestens zwei Personen geprüft
3. **Getestet sein**: Im Testnet durchgespielt
4. **Zugänglich sein**: Für alle Berechtigten verfügbar

### 5.3 Kill-Switch-Definition

Der **Kill-Switch** ist die letzte Verteidigungslinie:

**Funktion:**
- Stoppt ALLE neuen Order-Generierungen
- Cancelt ALLE offenen Orders (falls möglich)
- Setzt System in "Read-Only"-Modus
- Sendet Alarm an Owner/Operator

**Auslöser:**
- Manuell durch Owner/Operator
- Automatisch bei definierten Bedingungen (z.B. max. Drawdown erreicht)

**Hinweis:** Die technische Implementation des Kill-Switch ist Teil zukünftiger Phasen, nicht dieser Dokumentation.

---

## 6. Referenzen

| Dokument | Beschreibung |
|----------|--------------|
| `GOVERNANCE_AND_SAFETY_OVERVIEW.md` | Governance-Übersicht, Rollen |
| `SAFETY_POLICY_TESTNET_AND_LIVE.md` | Safety-Policies |
| `LIVE_READINESS_CHECKLISTS.md` | Checklisten für Stufen-Übergänge |
| `PHASE_24_SHADOW_EXECUTION.md` | Shadow-Execution-Dokumentation |
| `INCIDENT_SIMULATION_AND_DRILLS.md` | Incident-Drill-Playbook (Phase 56) |
| `INCIDENT_DRILL_LOG.md` | Drill-Log für dokumentierte Übungen |

---

## 7. Changelog

- **Phase 25** (2025-12): Initial erstellt
  - Shadow-Run-Runbook dokumentiert
  - System-Pause-Runbook erstellt
  - Incident-Handling-Prozess definiert
  - Incident-Report-Vorlage erstellt
  - Platzhalter für zukünftige Runbooks
  - Keine Code-Änderungen
- **Phase 56** (2025-12): Incident-Drills ergänzt
  - Verweise auf Incident-Drill-Playbook hinzugefügt
  - Hinweis auf aktive Übung von Runbooks ergänzt
