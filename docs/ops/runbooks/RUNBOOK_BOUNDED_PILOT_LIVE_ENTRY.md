# RUNBOOK — Bounded Pilot Live Entry (Ist-Zustand Repo)

**status:** ACTIVE  
**last_updated:** 2026-04-20  
**owner:** Peak_Trade  
**purpose:** Einheitliche Operator-Anleitung für den **ersten eng begrenzten Real-Money-Pilot** (Bounded Pilot)—abgestimmt auf den **aktuellen Code- und Governance-Stand** im Repository.  
**docs_token:** DOCS_TOKEN_RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY

---

## 1. Intent & Abgrenzung

### 1.1 Ziel

Dieses Runbook beschreibt **end-to-end**, wie ein Operator von **Dry-Validation** bis zum **Start einer Bounded-Pilot-Session** vorgeht—ohne „Broad Live“ oder dauerhafte Vollautonomie zu implizieren.

### 1.2 Was dieses Runbook **nicht** tut

- Keine Finanzberatung.
- **Keine** Freigabe von generellem Live-Trading: Der Governance-Key `live_order_execution` bleibt **`locked`**; erlaubt ist nur der **Bounded-Pilot-Kontext** über `live_order_execution_bounded_pilot` (Stand Code: `approved_2026` in `src/governance/go_no_go.py`).
- Kein Umgehen von Gates, Kill-Switch oder Confirm-Tokens.
- Kein Ersatz für menschliches Urteil bei Mehrdeutigkeit (**Mehrdeutigkeit → NO_TRADE / Abbruch**).

### 1.3 Technischer Ist-Zustand (Kurz)

| Komponente | Stand |
|------------|--------|
| Kanonischer Preflight (read-only) | `scripts/ops/check_bounded_pilot_readiness.py` bündelt **`check_live_readiness.py --stage live`** und **`pilot_go_no_go_eval_v1`**; Exit 0 nur bei voller Live-Readiness **und** `GO_FOR_NEXT_PHASE_ONLY`. Startet **keine** Session und setzt **kein** Gate-Handoff-Env. |
| Operator-Preflight-Packet (read-only) | `scripts/ops/bounded_pilot_operator_preflight_packet.py` orchestriert Readiness + **Stop-Signal-Snapshot** (`snapshot_operator_stop_signals`) in ein festes JSON; gleiche fail-closed Hartfehler wie im Skript-Docstring. |
| Entry-Gate + Session-Handoff | `scripts/ops/run_bounded_pilot_session.py` nutzt den Preflight-Stack und dasselbe Operator-Preflight-Packet **vor** jedem erfolgreichen Abschluss (Gate-only **`--no-invoke`** oder vor Handoff); bei `packet_ok` und ohne `--no-invoke` ruft es **`run_execution_session.py --mode bounded_pilot`** auf. Bei Packet-Blockade: **kein** Runner-Handoff / kein „alles grün“ bei `--no-invoke`. |
| Session-CLI | `scripts/run_execution_session.py` unterstützt `shadow`, `testnet`, **`bounded_pilot`**. |
| Runner | `LiveSessionRunner` / Konfiguration für `bounded_pilot` in `src/execution/live_session.py` (u. a. `bounded_pilot_mode`, `live_dry_run_mode=False` im Pilot-Kontext). |
| Governance | Pipeline wählt bei Bounded-Pilot-Kontext den Key **`live_order_execution_bounded_pilot`** (`select_live_order_execution_key`). |

**Hinweis:** Einige ältere Dokumente (z. B. `BOUNDED_PILOT_LIVE_ENTRY_GAP_NOTE.md`, Schritt 5 in `RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md`) sprechen noch von „kein Session-Start“—das ist **überholt**; maßgeblich ist dieses Runbook plus die referenzierten Specs.

---

## 2. Voraussetzungen (hart)

Alle Punkte müssen **vor** dem ersten Aufruf mit echten Orders erfüllt sein.

### 2.1 Vertrags- und Checklisten-Doku

- `docs/ops/specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md` — Entry Contract (Pilot-Haltung).
- `docs/ops/specs/PILOT_GO_NO_GO_CHECKLIST.md` — Checklistenbasis für Go/No-Go.
- Optional: `docs/ops/runbooks/live_pilot_execution_plan.md` — übergeordneter Plan (PRBI, Ops-Status, Export-Smokes).

### 2.2 Konfiguration & Kapital-Grenzen

- Zentrale Config ladbar: z. B. `config/config.toml` (oder `PEAK_TRADE_CONFIG_PATH`).
- Sektion **`[live_risk]`** mit greifbaren Caps (siehe `scripts/check_live_readiness.py` und `src/live/risk_limits.py`).
- Pilot-spezifische Caps: siehe `docs/ops/runbooks/live_pilot_caps.md` und `config/ops/live_pilot_caps.toml` (Empfehlungen im Live-Pilot-Plan: sehr kleine Notionale, wenige Orders pro Session).

### 2.3 Börse (Kraken Live im Bounded-Pilot-Pfad)

- `exchange.default_type` muss zum **Live-Kraken-Pfad** passen (siehe Kommentare in `live_session.py`: u. a. **`kraken_live`** für Bounded Pilot).
- Umgebungsvariablen für echte API-Zugänge müssen **vom Operator gesetzt** sein (siehe `check_live_readiness.py` für Live: u. a. `KRAKEN_API_KEY`, `KRAKEN_API_SECRET`). **Keine** Schlüssel in Git.

### 2.4 Kill-Switch & Operativer Schutz

- Kill-Switch-Disziplin und State gemäß Runbooks (`src/ops/gates/risk_gate.py`, Bounded-Pilot-Pipeline prüft bei aktivem Switch).
- Operator kennt **sofortigen** Abbruch (siehe Abschnitt 7).

---

## 3. Operator-Ablauf (Reihenfolge)

### Phase A — Dry-Validation (Pflicht)

**Nicht überspringen.** Vollständige Sequenz:

1. **Live-Dry-Run-Drills**  
   `python3 scripts/run_live_dry_run_drills.py`  
   Erwartung: Exit 0.

2. **Pilot Go/No-Go**  
   `python3 scripts/ops/pilot_go_no_go_eval_v1.py`  
   Erwartung für Entry: `verdict=GO_FOR_NEXT_PHASE_ONLY`.  
   Bei `NO_GO` oder unklarem `CONDITIONAL`: **stopp**, Payload prüfen (`--json`).

3. **Execution-Session Dry-Run**  
   `python3 scripts/run_execution_session.py --dry-run`  
   (bei Bedarf mit eurer geplanten Strategie/Symbol/Config-Flags, **ohne** `bounded_pilot`).  
   Erwartung: Validierung ohne Live-Start.

4. **Optional: Nur Gate-Check ohne Session**  
   `python3 scripts/ops/run_bounded_pilot_session.py --no-invoke`  
   Erwartung: Readiness + Go/No-Go **und** Operator-Preflight-Packet **GREEN**, **kein** Handoff / keine Session.

Detaillierte Einordnung: `docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md` (Schritt 5 dort ist historisch; Gate-only = `--no-invoke` hier in Phase A.4).

### Phase B — Readiness (empfohlen)

**Kanonischer Bounded-Pilot-Preflight (ein Aufruf, technisch + Go/No-Go):**

```bash
python3 scripts/ops/check_bounded_pilot_readiness.py --repo-root . --json
```

Erwartung: Exit **0** und `ok: true` nur wenn Live-Readiness **und** Cockpit-Verdict `GO_FOR_NEXT_PHASE_ONLY`. Bei Fehlern: **kein** Pilot.

**Alternativ einzeln (Debugging):**

```bash
python3 scripts/check_live_readiness.py --stage live --verbose
python3 scripts/ops/pilot_go_no_go_eval_v1.py --json
```

**Vollständiges Operator-Packet (Readiness + Stop-Signale, read-only):**

```bash
python3 scripts/ops/bounded_pilot_operator_preflight_packet.py --repo-root . --json
```

Vor **Session-Start ohne `--no-invoke`** wird dieses Packet im Entry-Wrapper intern nochmals gebaut; ein eigener Aufruf bleibt für Logs/Artefakte sinnvoll.

### Phase C — Erweiterter Ops-Check (optional, laut live_pilot_execution_plan)

- `scripts/ops/ops_status.sh` (Repo-Root) → Exit 0
- PRBI Live-Pilot-Scorecard: Entscheidung `READY_FOR_LIVE_PILOT`, keine `hard_blocks`
- Weitere organisatorische Gates (PRBC, PRK, AWS Export Write Smoke)—**wie in eurem Betrieb verbindlich definiert**

### Phase D — Bounded Pilot Entry (Handoff + Session)

**Nur** wenn Phase A–B (und verbindlich Phase C) **grün** sind.

1. **Finale Verifikation Go/No-Go** (erneut oder aus Logs bestätigen):  
   `python3 scripts/ops/pilot_go_no_go_eval_v1.py`

2. **Entry mit Session-Start** (Standardpfad—ruft den Runner auf):  
   ```bash
   python3 scripts/ops/run_bounded_pilot_session.py
   ```  
   Optionen siehe `--help` (u. a. `--steps`, `--position-fraction`, `--json`).  
   Unmittelbar vor dem Handoff an den Runner prüft der Wrapper das **Operator-Preflight-Packet** (fail-closed bei Stop-Signal-**error**-Status wie im Packet definiert).  
   **Hinweis:** Default ist **extrem klein** steps/sizing im Wrapper-Docstring; Cap an eure Pilot-Tabelle anpassen, aber **immer innerhalb** der konfigurierten `live_risk`-Grenzen.

3. **Alternativ (Operator kontrolliert den Aufruf selbst):**  
   Nach Gate-Logik manuell (inkl. kanonischem Handoff-Env und **demselben** read-only Operator-Preflight-Packet wie im Wrapper — `run_execution_session.py` baut es im **non-dry-run**-Pfad nach dem Handoff-Bit erneut, fail-closed):  
   `python3 scripts/run_execution_session.py --mode bounded_pilot --strategy <key> --steps <n> ...`  
   Nur nutzen, wenn dieselben Vorbedingungen wie oben erfüllt sind und der Go/No-Go **GO_FOR_NEXT_PHASE_ONLY** ist.

---

## 4. Evidenz & Artefakte

Nach jeder Pilot-Session-Durchführung mindestens:

- Ausgabe / Logs der Session und der Execution-Pipeline.
- `PT_EXEC_EVENTS_ENABLED` wird für `bounded_pilot` vom Runner gesetzt—Execution-Events JSONL gemäß eurer Observability-Runbooks sichern.
- Read-only Rekonstruktion: kanonische Registry- und (session-scoped) Execution-Events-Pfade für eine Session anzeigen —  
  `python3 scripts/report_live_sessions.py --evidence-pointers --session-id <SESSION_ID>`  
  oder letzte Registry-Session mit `mode=bounded_pilot`:  
  `python3 scripts/report_live_sessions.py --evidence-pointers --latest-bounded-pilot [--json]`  
  (schreibt keine Artefakte; `present: no` bedeutet: erwarteter Pfad, Datei fehlt noch oder liegt woanders).
- Read-only **offene Sessions** (Registry `status=started`, Operator: OPEN; pro Artefakt inkl. Registry-Pfad und session-scoped Execution-Events-Pfad):  
  `python3 scripts/report_live_sessions.py --open-sessions [--bounded-pilot-only] [--latest-bounded-pilot-open] [--json]`  
  (`status=started` allein belegt keinen laufenden Prozess — siehe CLI-Hinweis `closeout_note`.)
- Read-only **Zusammenfassung** (aktueller bounded-pilot Readiness-/Go-No-Go-Lauf, Operator-Preflight-Packet-Build, plus Registry-Fokus offene/letzte `bounded_pilot`-Session und Pointer):  
  `python3 scripts/report_live_sessions.py --bounded-pilot-readiness-summary [--json] [--config-path <path>] [--registry-base <dir>]`  
  (kein Live-Unlock; nur Momentaufnahme; siehe JSON-Feld `disclaimer`.)
- Read-only **Closeout-/Final-Status-Sicht** (Registry-Terminalstatus im **neuesten** JSON pro `session_id`, Konflikt-Hinweis bei `started`+älterem Terminal-Artefakt, Pointer wie oben; **ohne** Readiness-/Packet-Lauf):  
  `python3 scripts/report_live_sessions.py --bounded-pilot-closeout-status-summary [--json] [--registry-base <dir>]`  
  (kein Urteil über Handoff-Erfolg; siehe JSON-Feld `disclaimer` und `closeout.closeout_signal_summary`.)
- Read-only **Operator-Gesamtübersicht** (Readiness + Preflight-Packet + Registry-Fokus + Closeout-Signale in **einem** Aufruf; gleiche Bausteine wie die Einzel-CLIs):  
  `python3 scripts/report_live_sessions.py --bounded-pilot-operator-overview [--json] [--config-path <path>] [--registry-base <dir>]`  
  (kein Live-Unlock; siehe JSON-Feld `disclaimer`.)
- Read-only **Gate-/Enablement-Index** (kompakter Index-Block `gate_enablement_index` aus bestehenden Readiness-/Packet-/Session-/Closeout-Signalen **plus** voller Kontext wie Overview):  
  `python3 scripts/report_live_sessions.py --bounded-pilot-gate-index [--json] [--config-path <path>] [--registry-base <dir>]`  
  (kein Gate-Closure-Urteil; siehe JSON-Felder `disclaimer` und `gate_enablement_index.index_notes`.)
- Read-only **First-Live-/Bounded-Pilot-Frontdoor** (ein Aufruf: Overview + Gate-Index + kanonische CLI-Hinweise für alle tieferen read-only Subansichten; gleiche Datenbasis wie Overview/Gate-Index):  
  `python3 scripts/report_live_sessions.py --bounded-pilot-first-live-frontdoor [--json] [--config-path <path>] [--registry-base <dir>]`  
  (kein Live-Unlock; siehe JSON-Feld `disclaimer`; `canonical_read_only_subcommands` ersetzt keine Einzel-CLIs, sondern verweist darauf.)
- Optional: Export über eure **Object-Storage-Kette** (Phase T/W), ohne bestehende Shadow/Paper-Original-Runs zu überschreiben (neue `run_id` / Export-ID).

Referenz: `docs/ops/runbooks/live_pilot_execution_plan.md` (Post-run, Scorecards).

---

## 5. Incident- & Abbruch-Runbooks

Bei Anomalien **sofort** stoppen und dokumentieren:

- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md`
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md`
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md`
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md`
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md`
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md`
- `docs/ops/runbooks/RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md`

---

## 6. Abbruchkriterien vor oder während der Session

**Nicht starten** bzw. **sofort beenden**, wenn z. B.:

- Go/No-Go ≠ `GO_FOR_NEXT_PHASE_ONLY`
- Kill-Switch aktiv / Trading gebunden
- Policy oder Cockpit zeigt Block / erfordert Operator-Eingriff
- Stale-State, Evidence- oder Dependency-Degradation über Pilot-Toleranz
- Unklarheit, ob **nur** Bounded Pilot mit expliziten Caps aktiv ist (**Unklarheit → NO_TRADE**)

---

## 7. Rollback / NO_TRADE (Operator)

1. Session beenden (Ctrl+C / Prozess stop), falls sicher möglich.  
2. `PT_LIVE_ARMED` bzw. projektspezifische Arming-Variablen **deaktivieren** (siehe `live_pilot_execution_plan.md` Gate B).  
3. Kill-Switch gemäß Betriebshandbuch setzen.  
4. Incident-Evidenz unter `out/ops/` erfassen und ggf. exportieren.

---

## 8. Verwandte Dokumente

| Dokument | Rolle |
|----------|--------|
| `docs/ops/specs/BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md` | Kanonischer Entry-Vertrag |
| `docs/ops/specs/BOUNDED_PILOT_LIVE_ENTRY_GAP_NOTE.md` | Historische Gap-Analyse; **operative Prozedur = dieses Runbook** |
| `docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md` | Dry-Validation vor Geld-Einsatz |
| `docs/ops/runbooks/live_pilot_execution_plan.md` | Gesamtplan inkl. PRBI/Export |
| `docs/governance/BOUNDED_PILOT_LIVE_ORDER_EXECUTION_DECISION_PACKAGE.md` | Governance-Entscheidungsgrundlage |
| `scripts/ops/run_bounded_pilot_session.py` | Gate + Handoff |
| `scripts/run_execution_session.py` | Session-CLI |

---

## 9. Non-Goals

- Broad Live aktivieren oder dokumentieren.
- Testnet mit echten Testnet-Orders (weiterhin separat durch `SafetyGuard` eingeschränkt—nicht Gegenstand dieses Runbooks).
- Autonomie ohne menschliche Aufsicht.
