# Peak_Trade – Phase 73: Live-Dry-Run Drills & Safety-Validation

> **Status:** Phase 73 – Read-Only Simulation (keine echten Orders)  
> **Datum:** 2025-12  
> **Ziel:** Systematische Sicherheitsübungen im Dry-Run zur Validierung von Gating & Safety-Mechanismen

---

## 1. Überblick

Phase 73 implementiert ein System von **Live-Sicherheitsübungen („Drills") im Dry-Run**, das:

1. Typische Live-Szenarien durchspielt (Gates, Risk-Limits, falsche Konfigs)
2. Systematisch prüft, ob:
   - Gating + Dry-Run-Verhalten korrekt greifen
   - kein Pfad zu echten Orders existiert
   - `is_live_execution_allowed()` konsistent mit der Safety-Policy ist
3. Operatoren & Reviewer mit einem Report versorgt:
   - "Welche Drills wurden gefahren?"
   - "Welche Gates/Limits haben ausgelöst?"
   - "Wo wären wir theoretisch drohen-scharf – aber durch Phase 71/72 trotzdem gebremst?"

**Kernprinzipien:**
- **Read-Only Simulation**: Keine Config-Änderungen, keine echten Orders, keine Exchange-API-Calls
- **Systematische Validierung**: Alle Gating-Pfade werden durchgespielt
- **Operator-Training**: Drills dienen auch als Training für Operatoren

**WICHTIG:** Diese Phase ist **reine Simulation & Validierung** – keine Config-Änderungen, keine State-Änderungen, keine echten Orders.

---

## 2. Drill-System

### 2.1 Datamodel

**`LiveDrillScenario`** (`src/live/drills.py`):
- Definiert ein Test-Szenario mit:
  - Name, Beschreibung
  - Environment-Overrides (z.B. `{"enable_live_trading": False}`)
  - Erwartete Ergebnisse (`expected_is_live_execution_allowed`, `expected_reasons`)
  - Optionale simulierte Orders/PnL für Risk-Checks

**`LiveDrillResult`** (`src/live/drills.py`):
- Enthält Ergebnis eines Drills:
  - `passed`: Ob Drill bestanden wurde
  - `is_live_execution_allowed`: Tatsächliches Ergebnis
  - `reason`: Reason-String
  - `effective_mode`: Effektiver Modus
  - `notes`: Details (Gates, Limits)
  - `violations`: Verletzungen (wo Erwartung ≠ Realität)

**`LiveDrillRunner`** (`src/live/drills.py`):
- Führt Drill-Szenarien aus:
  - `run_scenario(scenario)` → `LiveDrillResult`
  - `run_all(scenarios)` → `List[LiveDrillResult]`
  - Alle Änderungen rein im Speicher (keine Datei-Änderungen)

### 2.2 Standard-Drills

`get_default_live_drill_scenarios()` definiert folgende Standard-Drills:

**Drill A – Voll gebremst (Default-Safety)**
- `mode="live"`, aber `enable_live_trading=False`
- Erwartung: `is_live_execution_allowed=False`, Reason enthält `enable_live_trading=False`

**Drill B – Gate 1 ok, Gate 2 fehlt**
- `mode="live"`, `enable_live_trading=True`, aber `live_mode_armed=False`
- Erwartung: `is_live_execution_allowed=False`, Reason enthält `live_mode_armed=False`

**Drill C – Alles armed, aber Dry-Run aktiv**
- `mode="live"`, alle Gates offen, aber `live_dry_run_mode=True`
- Erwartung: `is_live_execution_allowed=False`, Reason enthält `live_dry_run_mode=True`
- Ziel: Sicherstellen, dass Dry-Run im Report klar erkennbar ist

**Drill D – Confirm-Token fehlt**
- `mode="live"`, alle Gates offen, aber `confirm_token` ungültig/nicht gesetzt
- Erwartung: `is_live_execution_allowed=False`, Reason enthält `confirm_token`

**Drill E – Risk-Limits schlagen an (Design)**
- Alle Gates so gesetzt, dass Execution theoretisch möglich wäre
- Risk-Limits würden blockieren (z.B. `max_live_notional_total` überschritten)
- Erwartung: `is_live_execution_allowed=True` (Gating erlaubt), aber Risk würde blockieren

**Drill F – Nicht-Live-Modus (Testnet)**
- `mode="testnet"`
- Erwartung: `is_live_execution_allowed=False`, Reason erklärt, dass Environment nicht LIVE ist

**Drill G – Paper-Modus**
- `mode="paper"`
- Erwartung: `is_live_execution_allowed=False`, Reason erklärt, dass Environment nicht LIVE ist

---

## 3. CLI: `scripts/run_live_dry_run_drills.py`

### 3.1 Beschreibung

Das Script führt Live-Dry-Run-Drills aus und generiert einen Report.

**Features:**
- Führt alle Standard-Drills aus
- Generiert übersichtlichen Text-Report
- Optional: JSON-Output
- Optional: Nur einen bestimmten Drill ausführen

### 3.2 Usage

```bash
# Alle Standard-Drills ausführen
python scripts/run_live_dry_run_drills.py

# Nur einen bestimmten Drill
python scripts/run_live_dry_run_drills.py --scenario "A - Voll gebremst"

# JSON-Output
python scripts/run_live_dry_run_drills.py --format json
```

### 3.3 Beispiel-Ausgabe

```
======================================================================
Peak_Trade - Live-Dry-Run Drills & Safety-Validation (Phase 73)
======================================================================
Phase 73 – Read-Only Simulation, keine echten Orders

──────────────────────────────────────────────────────────────────────
Übersicht
──────────────────────────────────────────────────────────────────────
Anzahl Drills:            7
Bestanden:                7 ✓
Fehlgeschlagen:           0 ✗

──────────────────────────────────────────────────────────────────────
Drill: A - Voll gebremst (Default-Safety)
──────────────────────────────────────────────────────────────────────
Status:                  ✓ PASSED
is_live_execution_allowed: False
Reason:                  enable_live_trading=False (Gate 1 blockiert)
Effective Mode:          live_dry_run

Details:
  • Mode: live
  • Effective Mode: live_dry_run
  • enable_live_trading: False
  • live_mode_armed: False
  • live_dry_run_mode: True
  • confirm_token: NOT SET

──────────────────────────────────────────────────────────────────────
Drill: C - Alles armed, aber Dry-Run aktiv
──────────────────────────────────────────────────────────────────────
Status:                  ✓ PASSED
is_live_execution_allowed: False
Reason:                  live_dry_run_mode=True (Phase 71: Technisches Gate blockiert echte Orders)
Effective Mode:          live_dry_run

Details:
  • Mode: live
  • Effective Mode: live_dry_run
  • enable_live_trading: True
  • live_mode_armed: True
  • live_dry_run_mode: True
  • confirm_token: SET (valid)

======================================================================
Phase 73: Alle Drills sind Simulationen im Dry-Run-Modus.
Keine echten Orders werden gesendet, keine Config-Dateien geändert.
======================================================================
```

---

## 4. Read-Only Scope

### 4.1 Was Drills DÜRFEN

✅ **Lesen:**
- Config-Dateien lesen (optional, für Basis-Config)
- Environment-Status auswerten
- Gating-Status prüfen
- `is_live_execution_allowed()` aufrufen

✅ **Simulieren:**
- EnvironmentConfig im Speicher modifizieren (Overrides)
- Drill-Szenarien durchspielen
- Reports generieren

### 4.2 Was Drills NICHT DÜRFEN

❌ **Schreiben:**
- Config-Dateien überschreiben
- Flags persistent ändern
- State-Änderungen vornehmen

❌ **Execution:**
- Orders erzeugen/versenden
- Exchange-APIs aufrufen
- Live-Trading aktivieren

### 4.3 Warum Read-Only?

**Safety-First:**
- Drills sind reine Validierung, keine Aktivierung
- Keine versehentlichen Änderungen möglich
- Klare Trennung: Validierung vs. Aktivierung

**Operator-Training:**
- Operatoren können Drills regelmäßig ausführen
- Verstehen, welche Gates/Limits greifen
- Keine Gefahr, etwas versehentlich zu aktivieren

---

## 5. Governance & Training

### 5.1 Regelmäßige Drills

**Empfehlung:**
- Wöchentlich: Alle Standard-Drills ausführen
- Vor Live-Promotion: Vollständiger Drill-Set
- Nach Config-Änderungen: Relevante Drills

**Workflow:**
```bash
# Wöchentlicher Drill
python scripts/run_live_dry_run_drills.py > reports/drills/weekly_$(date +%Y%m%d).txt

# Review des Reports
# Alle Drills sollten "PASSED" sein
```

### 5.2 Operator-Training

Drills dienen auch als **Training** für Operatoren:

1. **Verstehen der Gates:**
   - Welche Gates gibt es?
   - Wie greifen sie zusammen?
   - Was blockiert was?

2. **Interpretation der Reports:**
   - Was bedeutet `is_live_execution_allowed=False`?
   - Welche Gates/Limits haben blockiert?
   - Warum ist Phase 71/72 trotzdem sicher?

3. **Incident-Preparedness:**
   - Was passiert, wenn ein Gate fehlt?
   - Wie erkenne ich, ob Dry-Run aktiv ist?
   - Was sind typische Fehlkonfigurationen?

### 5.3 Audit & Review

Drills können für **Audits** genutzt werden:

- **Compliance:** Zeigt, dass Gating-Mechanismen funktionieren
- **Documentation:** Reports dokumentieren Safety-Status
- **Validation:** Systematische Prüfung aller Gating-Pfade

---

## 6. Integration & Tests

### 6.1 Tests

Tests befinden sich in `tests/test_phase73_live_dry_run_drills.py`:

**Abgedeckte Bereiche:**
- Standard-Szenarien (A-G)
- Drill-Runner-Funktionalität
- Violation-Erkennung
- Safety-Verifikation (keine Config-Änderungen, keine API-Calls)

**WICHTIG:** Tests prüfen nur Drill-Logik, keine State-Änderungen.

### 6.2 Integration in bestehende Doku

**Verwandte Dokumente:**
- `docs/PHASE_71_LIVE_EXECUTION_DESIGN_AND_GATING.md` – Phase 71 (Design & Gating)
- `docs/PHASE_72_LIVE_OPERATOR_CONSOLE.md` – Phase 72 (Status-CLI)
- `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md` – Safety-Policy
- `docs/LIVE_READINESS_CHECKLISTS.md` – Readiness-Checklisten

---

## 7. Zusammenfassung

**Was Phase 73 getan hat:**
- ✅ Drill-System implementiert (`src/live/drills.py`)
- ✅ Standard-Drills definiert (A-G)
- ✅ CLI für Drill-Ausführung (`scripts/run_live_dry_run_drills.py`)
- ✅ Tests für Drill-Logik hinzugefügt
- ✅ Dokumentation erstellt

**Was Phase 73 NICHT getan hat:**
- ❌ Keine Config-Änderungen
- ❌ Keine State-Änderungen
- ❌ Keine echten Orders
- ❌ Keine Exchange-API-Calls

**Ergebnis:**
Operatoren haben jetzt ein **systematisches Tool** zur Validierung der Gating- und Safety-Mechanismen. Drills können regelmäßig ausgeführt werden, um sicherzustellen, dass alle Safety-Mechanismen korrekt funktionieren.

---

## 8. Referenzen

- `src/live/drills.py` – Drill-System-Implementierung
- `scripts/run_live_dry_run_drills.py` – CLI
- `tests/test_phase73_live_dry_run_drills.py` – Tests
- `src/live/safety.py` – `is_live_execution_allowed()`, `SafetyGuard`
- `src/core/environment.py` – `EnvironmentConfig`
- `docs/PHASE_71_LIVE_EXECUTION_DESIGN_AND_GATING.md` – Phase 71
- `docs/PHASE_72_LIVE_OPERATOR_CONSOLE.md` – Phase 72
- `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md` – Safety-Policy

---

**Built with ❤️ and safety-first architecture**


