# Peak_Trade – Phase 74: Live-Config Audit & Export

> **Status:** Phase 74 – Read-Only Audit-Export (keine Config-Änderungen)  
> **Datum:** 2025-12  
> **Ziel:** Audit-Snapshot für Governance, Audits und "Proof of Safety"

---

## 1. Überblick

Phase 74 implementiert einen **Audit-Export** für den gesamten Live-Sicherheitszustand, der:

1. Alle Live-bezogenen Configs, Gating-Flags, Risk-Limits und Drill-Setups in einem **Snapshot** zusammenfasst
2. In **maschinenlesbarer Form (JSON)** und optional **Markdown/Text** exportiert
3. Für Governance, externe Audits und "Future Me will wissen, wie sicher v1.0 wirklich war" nutzbar ist
4. **100 % read-only** bleibt: keine Config-Schreibzugriffe, keine State-Changes, keine Orders

**Kernprinzipien:**
- **Read-Only**: Keine Config-Änderungen, keine State-Änderungen, keine echten Orders
- **Security**: Keine Token-Werte exportieren (nur Boolean-Präsenz)
- **Transparenz**: Vollständiger Snapshot für Governance & Audits

**WICHTIG:** Diese Phase ist **reiner Audit-Export** – keine Config-Änderungen, keine State-Änderungen, keine echten Orders.

---

## 2. Audit-Modul: `src/live/audit.py`

### 2.1 Datamodel

**`LiveAuditGatingState`**:
- `mode`: Environment-Mode (paper/testnet/live)
- `effective_mode`: Effektiver Modus aus SafetyGuard
- `enable_live_trading`: Gate 1
- `live_mode_armed`: Gate 2 (Phase 71)
- `live_dry_run_mode`: Technisches Gate (Phase 71)
- `confirm_token_present`: Boolean (Wert wird NICHT exportiert!)
- `require_confirm_token`: Ob Token erforderlich ist

**`LiveAuditRiskState`**:
- `max_live_notional_per_order`: Max. Notional pro Order (Phase 71)
- `max_live_notional_total`: Max. Gesamt-Notional (Phase 71)
- `live_trade_min_size`: Min. Order-Größe (Phase 71)
- `limits_enabled`: Ob Risk-Limits aktiviert sind
- `limits_source`: Quelle der Limits (z.B. "config.toml")

**`LiveAuditDrillSummary`**:
- `available_scenarios`: Liste von Drill-Namen (z.B. ["A - Voll gebremst", ...])
- `num_scenarios`: Anzahl verfügbarer Drills
- `drills_executable`: Ob Drills ausführbar sind (Meta-Info)

**`LiveAuditSafetySummary`**:
- `is_live_execution_allowed`: Ergebnis von `is_live_execution_allowed()`
- `reasons`: Liste von Gründen (warum erlaubt/blockiert)
- `safety_guarantee_v1_0`: Kurzer Text zur Safety-Garantie

**`LiveAuditSnapshot`**:
- `timestamp_utc`: Zeitstempel des Snapshots (ISO-Format)
- `environment_id`: Optional Identifier (z.B. Config-Name)
- `gating`: Gating-Status
- `risk`: Risk-Limits-Status
- `drills`: Drill-Meta-Informationen
- `safety`: Safety-Zusammenfassung
- `versions`: Optional Versions-Info (z.B. Test-Anzahlen)

### 2.2 Funktionen

**`build_live_audit_snapshot(env_config, safety_guard, live_risk_limits, environment_id)`**:
- Erstellt einen vollständigen Audit-Snapshot
- Nutzt `EnvironmentConfig`, `SafetyGuard`, `is_live_execution_allowed()`, `LiveRiskLimits`
- Keine Config-Änderungen, keine State-Änderungen

**`live_audit_snapshot_to_dict(snapshot)`**:
- Konvertiert Snapshot zu JSON-serialisierbarem Dict
- Token-Werte werden NICHT exportiert (nur Boolean-Präsenz)

**`live_audit_snapshot_to_markdown(snapshot)`**:
- Konvertiert Snapshot zu Markdown-Text
- Formatierter Audit-Bericht für Menschen

---

## 3. CLI: `scripts/export_live_audit_snapshot.py`

### 3.1 Beschreibung

Das Script exportiert Live-Audit-Snapshots in verschiedenen Formaten.

**Features:**
- JSON-Export für maschinenlesbare Audits
- Markdown-Export für menschenlesbare Berichte
- STDOUT-Output für schnelle Ansicht
- Read-Only: keine Config-Änderungen, keine State-Änderungen

### 3.2 Usage

```bash
# Snapshot auf STDOUT (Markdown)
python scripts/export_live_audit_snapshot.py --stdout

# JSON-Export
python scripts/export_live_audit_snapshot.py --output-json audit/live_audit_2025-12-07.json

# Markdown-Export
python scripts/export_live_audit_snapshot.py --output-markdown audit/live_audit_2025-12-07.md

# Beides (JSON + Markdown)
python scripts/export_live_audit_snapshot.py \
    --output-json audit/live_audit_2025-12-07.json \
    --output-markdown audit/live_audit_2025-12-07.md

# Mit expliziter Config
python scripts/export_live_audit_snapshot.py \
    --config config/config.toml \
    --output-json audit/live_audit_2025-12-07.json
```

### 3.3 Beispiel-Ausgabe (Markdown)

```markdown
# Peak_Trade - Live Audit Snapshot

**Phase 71-74, v1.0**
**Timestamp:** 2025-12-07T12:00:00+00:00 (UTC)
**Environment ID:** config

## Gating Status

- **Mode:** live
- **Effective Mode:** live_dry_run
- **enable_live_trading (Gate 1):** True
- **live_mode_armed (Gate 2 - Phase 71):** False
- **live_dry_run_mode (Technisches Gate):** True
- **confirm_token_present:** True (Wert nicht exportiert)
- **require_confirm_token:** True

## Risk Limits

- **Limits Enabled:** True
- **Limits Source:** config.toml
- **max_live_notional_per_order:** 1000.0
- **max_live_notional_total:** 5000.0
- **live_trade_min_size:** 10.0

## Drills Summary

- **Available Scenarios:** 7
- **Drills Executable:** True

Available Drill Scenarios:
  - A - Voll gebremst (Default-Safety)
  - B - Gate 1 ok, Gate 2 fehlt
  - C - Alles armed, aber Dry-Run aktiv
  - D - Confirm-Token fehlt
  - E - Risk-Limits schlagen an (Design)
  - F - Nicht-Live-Modus (Testnet)
  - G - Paper-Modus

## Safety Summary

- **is_live_execution_allowed:** False
- **Safety Guarantee (v1.0):** Dry-Run only, no real orders possible (v1.0 - Phase 71-74)

**Reasons:**
  - live_mode_armed=False (Gate 2 blockiert - Phase 71)
  - Gate 2: live_mode_armed=False (Phase 71)
  - Technisches Gate: live_dry_run_mode=True (Phase 71)

---

**Note:** This snapshot is read-only. No config changes, no state changes, no real orders.
**Phase 71-74:** Live-Execution-Path exists as design/Dry-Run only.
**v1.0:** Research/Testnet system - no real live orders possible.
```

---

## 4. Read-Only Scope

### 4.1 Was Audit-Export DARF

✅ **Lesen:**
- Config-Dateien lesen
- Environment-Status auswerten
- Gating-Status prüfen
- Risk-Limits anzeigen
- Drill-Meta-Informationen sammeln
- Snapshots generieren

✅ **Exportieren:**
- JSON-Dateien schreiben (Audit-Export)
- Markdown-Dateien schreiben (Berichte)
- STDOUT-Output

### 4.2 Was Audit-Export NICHT DARF

❌ **Schreiben:**
- Config-Dateien überschreiben
- Flags ändern (`enable_live_trading`, `live_mode_armed`, etc.)
- State-Änderungen vornehmen

❌ **Exportieren:**
- Token-Werte (nur Boolean-Präsenz)
- API-Keys oder Secrets
- Sensible Credentials

❌ **Execution:**
- Orders erzeugen/versenden
- Exchange-APIs aufrufen
- Live-Trading aktivieren

### 4.3 Warum Read-Only?

**Safety-First:**
- Audit-Export ist reine Beobachtung, keine Aktivierung
- Keine versehentlichen Änderungen möglich
- Klare Trennung: Audit vs. Aktivierung

**Security:**
- Token-Werte werden NICHT exportiert (nur Boolean-Präsenz)
- Keine sensiblen Daten in Snapshots

---

## 5. Governance & Audits

### 5.1 Regelmäßige Snapshots

**Empfehlung:**
- Wöchentlich: Snapshot erstellen und archivieren
- Vor major Updates: Snapshot als Baseline
- Nach Config-Änderungen: Neuer Snapshot für Vergleich

**Workflow:**
```bash
# Wöchentlicher Snapshot
python scripts/export_live_audit_snapshot.py \
    --output-json audit/live_audit_$(date +%Y%m%d).json \
    --output-markdown audit/live_audit_$(date +%Y%m%d).md

# Archivierung
mkdir -p audit/archive
mv audit/live_audit_*.json audit/archive/
mv audit/live_audit_*.md audit/archive/
```

### 5.2 Externe Audits

Snapshots können für **externe Audits** genutzt werden:

- **Compliance:** Zeigt, dass Gating-Mechanismen funktionieren
- **Documentation:** Vollständiger Snapshot des Safety-Status
- **Proof of Safety:** Nachweis, dass v1.0 keine echten Orders ermöglicht

### 5.3 "Future Me will wissen, wie sicher v1.0 wirklich war"

Snapshots dokumentieren den Safety-Status zu einem bestimmten Zeitpunkt:

- Welche Gates waren aktiv?
- Welche Risk-Limits waren gesetzt?
- Welche Drills waren verfügbar?
- War `is_live_execution_allowed()` True oder False?

---

## 6. Integration & Tests

### 6.1 Tests

Tests befinden sich in `tests/test_phase74_live_audit_export.py`:

**Abgedeckte Bereiche:**
- `build_live_audit_snapshot()` für verschiedene Environments
- `live_audit_snapshot_to_dict()` JSON-Serialisierung
- `live_audit_snapshot_to_markdown()` Markdown-Format
- Token-Werte werden NICHT exportiert (nur Boolean-Präsenz)
- Read-Only-Verhalten (keine Config-Änderungen)

**WICHTIG:** Tests prüfen nur Audit-Logik, keine State-Änderungen.

### 6.2 Integration in bestehende Doku

**Verwandte Dokumente:**
- `docs/PHASE_71_LIVE_EXECUTION_DESIGN_AND_GATING.md` – Phase 71 (Design & Gating)
- `docs/PHASE_72_LIVE_OPERATOR_CONSOLE.md` – Phase 72 (Status-CLI)
- `docs/PHASE_73_LIVE_DRY_RUN_DRILLS.md` – Phase 73 (Drills)
- `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md` – Safety-Policy
- `docs/LIVE_READINESS_CHECKLISTS.md` – Readiness-Checklisten

---

## 7. Zusammenfassung

**Was Phase 74 getan hat:**
- ✅ Audit-Modul implementiert (`src/live/audit.py`)
- ✅ CLI für Audit-Export (`scripts/export_live_audit_snapshot.py`)
- ✅ JSON- und Markdown-Export
- ✅ Tests für Audit-Logik hinzugefügt
- ✅ Dokumentation erstellt

**Was Phase 74 NICHT getan hat:**
- ❌ Keine Config-Änderungen
- ❌ Keine State-Änderungen
- ❌ Keine echten Orders
- ❌ Keine Token-Werte exportiert

**Ergebnis:**
Operatoren und Auditoren haben jetzt ein **systematisches Tool** zur Erstellung von Audit-Snapshots. Snapshots können regelmäßig erstellt werden, um den Safety-Status zu dokumentieren und für Governance & Audits zu nutzen.

---

## 8. Referenzen

- `src/live/audit.py` – Audit-Modul-Implementierung
- `scripts/export_live_audit_snapshot.py` – CLI
- `tests/test_phase74_live_audit_export.py` – Tests
- `src/live/safety.py` – `is_live_execution_allowed()`, `SafetyGuard`
- `src/core/environment.py` – `EnvironmentConfig`
- `src/live/risk_limits.py` – `LiveRiskLimits`
- `src/live/drills.py` – Drill-System
- `docs/PHASE_71_LIVE_EXECUTION_DESIGN_AND_GATING.md` – Phase 71
- `docs/PHASE_72_LIVE_OPERATOR_CONSOLE.md` – Phase 72
- `docs/PHASE_73_LIVE_DRY_RUN_DRILLS.md` – Phase 73
- `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md` – Safety-Policy

---

**Built with ❤️ and safety-first architecture**
