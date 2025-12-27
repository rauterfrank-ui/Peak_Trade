# Peak_Trade – Phase 72: Live-Operator-Konsole & Status-CLI

> **Status:** Phase 72 – Read-Only Status-CLI (keine State-Änderungen)  
> **Datum:** 2025-12  
> **Ziel:** Operator-Interface für transparenten Live-/Gating-/Risk-Status

---

## 1. Überblick

Phase 72 implementiert ein **Read-Only Operator-Interface** (CLI), das Operatoren in Sekunden beantwortet:

- "In welchem Modus sind wir wirklich?"
- "Welche Gates stehen wie?"
- "Was sagen die Risk-Limits?"
- "Würde `is_live_execution_allowed()` theoretisch JA sagen – und blockiert Phase 71/72 trotzdem echte Orders?"

**Kernprinzipien:**
- **Read-Only**: Keine Config-Änderungen, keine State-Änderungen, keine echten Orders
- **Transparenz**: Vollständiger Status-Snapshot für Operatoren
- **Safety-First**: Klare Kennzeichnung von Phase 71/72 (Dry-Run only)

**WICHTIG:** Diese Phase ist **reiner Status & Transparenz** – NICHT Konfiguration, NICHT Live-Scharfschaltung.

---

## 2. CLI-Script: `scripts/live_operator_status.py`

### 2.1 Beschreibung

Das Script `scripts/live_operator_status.py` ist eine zentrale CLI für Operatoren zur Anzeige des kompletten Live-/Gating-/Risk-Status.

**Features (Read-Only):**
1. **Environment-Status**: Mode, Effective Mode, alle Gating-Flags
2. **Live-Execution-Status**: Ergebnis von `is_live_execution_allowed()` mit Erklärung
3. **Live-Risk-Limits**: Konfigurierte Limits (Phase 71: Design)
4. **Hinweise & Empfehlungen**: Phase-71/72-Status, qualitative Bewertungen

### 2.2 Usage

```bash
# Status mit Default-Config
python scripts/live_operator_status.py

# Status mit expliziter Config
python scripts/live_operator_status.py --config config/config.toml
```

### 2.3 Beispiel-Ausgabe

```
======================================================================
Peak_Trade - Live Operator Status (Phase 71/72)
======================================================================
Phase 71/72 – Live-Execution Design (Dry-Run only, keine echten Orders möglich)

──────────────────────────────────────────────────────────────────────
Environment & Gating Status
──────────────────────────────────────────────────────────────────────
Mode:                    live
Effective Mode:          live_dry_run

Gating Status:
  enable_live_trading:    True
  live_mode_armed:        False (Gate 2 - Phase 71)
  live_dry_run_mode:      True (Phase 71: Technisches Gate)
  require_confirm_token:  True
  confirm_token:          SET (valid)

──────────────────────────────────────────────────────────────────────
Live-Execution Status (is_live_execution_allowed)
──────────────────────────────────────────────────────────────────────
Allowed:                 False
Reason:                  live_mode_armed=False (Gate 2 blockiert - Phase 71)

Blocking Gates:
  ✗ Gate 2: live_mode_armed = False (Phase 71)
  ✗ Technisches Gate: live_dry_run_mode = True (Phase 71)

──────────────────────────────────────────────────────────────────────
Live Risk-Limits
──────────────────────────────────────────────────────────────────────
Risk-Limits Enabled:     True
Base Currency:           EUR

Live-Specific Limits (Phase 71: Design):
  max_live_notional_per_order: 1000.00 EUR
  max_live_notional_total:     5000.00 EUR
  live_trade_min_size:         10.00

✓  Live-Limits konfiguriert (Design-Status: Phase 71)

──────────────────────────────────────────────────────────────────────
Hinweise & Empfehlungen
──────────────────────────────────────────────────────────────────────
Phase 71/72 Status:
  • Live-Execution-Path existiert als Design/Dry-Run
  • Keine echten Orders werden gesendet (live_dry_run_mode=True)
  • System ist ein reines Research-/Testnet-System (v1.0)

Live-Modus aktiv (Design):
  • Alle Operationen laufen im Dry-Run-Modus
  • Logs sind mit [LIVE-DRY-RUN] gekennzeichnet
  • Echte Live-Orders erfordern spätere Phase (z.B. Phase 73+)

======================================================================
```

### 2.4 Implementierung

**Hauptfunktion:**
- `generate_live_status_report(env_config, safety_guard, live_risk_limits)` – Generiert Status-Report als String
- `main()` – CLI-Hauptfunktion

**Datenquellen:**
- `EnvironmentConfig` aus Config
- `SafetyGuard` für `get_effective_mode()` und Gating-Status
- `LiveRiskLimits` (optional) für Risk-Limits
- `is_live_execution_allowed()` für Live-Execution-Status

---

## 3. Read-Only Scope

### 3.1 Was das Script DARF

✅ **Lesen:**
- Config-Dateien lesen
- Environment-Status auswerten
- Gating-Status prüfen
- Risk-Limits anzeigen
- Status-Report generieren

✅ **Anzeigen:**
- Formatierte Ausgabe in der Konsole
- Klare Kennzeichnung von Phase 71/72
- Erklärungen für Blockierungen

### 3.2 Was das Script NICHT DARF

❌ **Schreiben:**
- Config-Dateien überschreiben
- Flags ändern (`enable_live_trading`, `live_mode_armed`, etc.)
- State-Änderungen vornehmen

❌ **Execution:**
- Orders erzeugen/versenden
- Exchange-APIs aufrufen
- Live-Trading aktivieren

### 3.3 Warum Read-Only?

**Safety-First:**
- Operatoren haben ein "Röntgenbild" des Systems (Status-Snapshot)
- Keine "Waffe" in der Hand (keine versehentlichen Änderungen)
- Klare Trennung: Status-Anzeige vs. State-Änderungen

**Zukünftige Phasen:**
- Phase 73+ könnten sich um kontrollierte State-Änderungen kümmern
- Separate Tools für Config-Management (falls nötig)
- Explizite Freigabe-Prozesse für Live-Aktivierung

---

## 4. Integration & Tests

### 4.1 Tests

Tests befinden sich in `tests/test_phase72_live_operator_status.py`:

**Abgedeckte Bereiche:**
- Status-Report für alle Modi (Paper, Testnet, Live)
- Gating-Status-Anzeige
- `is_live_execution_allowed()` Integration
- LiveRiskLimits-Anzeige (mit/ohne Limits)
- Phase-71/72-Hinweise
- Read-Only-Scope-Verifikation

**WICHTIG:** Tests prüfen nur Status-Generierung, keine State-Änderungen.

### 4.2 Integration in bestehende Doku

**Verwandte Dokumente:**
- `docs/PHASE_71_LIVE_EXECUTION_DESIGN_AND_GATING.md` – Phase 71 (Design & Gating)
- `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md` – Abschnitt 8 (Live-Readiness v1.1)
- `docs/PEAK_TRADE_V1_OVERVIEW_FULL.md` – v1.0-Übersicht

---

## 5. Operator-Workflow

### 5.1 Typischer Einsatz

**Vor einem Live-Run (Design-Test):**
```bash
python scripts/live_operator_status.py
```

**Fragen, die beantwortet werden:**
1. In welchem Modus sind wir? → `Mode: live`, `Effective Mode: live_dry_run`
2. Welche Gates sind offen/geschlossen? → Gating-Status-Block
3. Würde `is_live_execution_allowed()` JA sagen? → Live-Execution-Status-Block
4. Welche Risk-Limits sind gesetzt? → Live Risk-Limits-Block
5. Ist Phase 71/72 aktiv? → Phase-Hinweise im Header

### 5.2 Interpretation

**Beispiel-Interpretation:**
- `Mode: live` + `Effective Mode: live_dry_run` → Live-Design aktiv, aber Dry-Run
- `Allowed: False` + `Reason: live_dry_run_mode=True` → Phase 71 blockiert echte Orders
- `live_mode_armed: False` → Gate 2 blockiert zusätzlich
- `max_live_notional_per_order: NOT SET` → Limit nicht konfiguriert (Hinweis)

---

## 6. Zusammenfassung

**Was Phase 72 getan hat:**
- ✅ Read-Only Status-CLI implementiert (`scripts/live_operator_status.py`)
- ✅ Status-Report-Generierung mit allen relevanten Informationen
- ✅ Integration von `is_live_execution_allowed()` für klare Gating-Erklärungen
- ✅ LiveRiskLimits-Anzeige (Phase 71: Design)
- ✅ Phase-71/72-Hinweise für Operatoren
- ✅ Tests für Status-Logik hinzugefügt
- ✅ Dokumentation erstellt

**Was Phase 72 NICHT getan hat:**
- ❌ Keine Config-Änderungen
- ❌ Keine State-Änderungen
- ❌ Keine Live-Trading-Aktivierung
- ❌ Keine echten Orders

**Ergebnis:**
Operatoren haben jetzt ein **transparentes "Röntgenbild"** des Systems, können den Status in Sekunden erfassen, aber haben keine Möglichkeit, versehentlich State zu ändern oder echte Orders zu aktivieren.

---

## 7. Referenzen

- `scripts/live_operator_status.py` – CLI-Implementierung
- `tests/test_phase72_live_operator_status.py` – Tests
- `src/live/safety.py` – `is_live_execution_allowed()`, `SafetyGuard`
- `src/core/environment.py` – `EnvironmentConfig`
- `src/live/risk_limits.py` – `LiveRiskLimits`
- `docs/PHASE_71_LIVE_EXECUTION_DESIGN_AND_GATING.md` – Phase 71
- `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md` – Safety-Policy

---

**Built with ❤️ and safety-first architecture**
