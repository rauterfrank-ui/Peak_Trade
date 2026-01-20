# Peak_Trade — Cursor Multi-Agent Runbook (Front Door + Appendices)
Version: v1.1 (Repo-Anchored)  
Datum: 2025-12-30  
Geltungsbereich: Shadow → Bounded Auto → Live (mit Governance & Risk Gates)  
Zielgruppe: Operator, Cursor Multi-Agent (A0–A5), Reviewer

---

## 0. Datei-Status und Ablageort (Repo-Anker)
Diese Datei ist als **normatives Steuerdokument** gedacht. Lege sie im Repo ab unter:

- **Pfad:** `docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md`

**Regel:** Im Repo gibt es **genau eine** "Front Door" für Cursor Multi-Agent. Alles andere sind Appendices/Referenzen.

---

## 1. Warum dieses Dokument (Front Door)
Dieses Dokument ist die **primäre Steuerungsquelle** für Cursor Multi-Agent-Arbeit an Peak_Trade bis zum finalen Live-Trade.  
Es ist bewusst **kurz, normativ und umsetzungsorientiert**. Detaillierte Inhalte liegen in den **Appendices**.

**Prinzip:**  
- *Front Door* = Wie wir liefern (Rollen, Task-Packet, PR-Contract, Gates, Stop-Regeln).  
- *Appendices* = Was genau wir liefern (Phase-Matrix, Befehle, Troubleshooting, Repo-Anker/Current Reality).

---

## 1.1 Start in 60 Sekunden

Schnelleinstieg für neue Cursor Multi-Agent Sessions:

1. **Öffne dieses Frontdoor-Dokument** (du bist bereits hier)
2. **Öffne den Phasen-Runbook**: [CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2.md](CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2.md)
3. **Erstelle einen Session Runlog** aus dem Template: [CURSOR_MULTI_AGENT_SESSION_RUNLOG_TEMPLATE.md](CURSOR_MULTI_AGENT_SESSION_RUNLOG_TEMPLATE.md)

**Phasen-Auswahl:**
- **Phase 0** — Foundation / Contracts / Docs-First (siehe PHASES_V2, Abschnitt 5)
- **Phase 1** — Shadow Trading (siehe PHASES_V2, Abschnitt 5)
- **Phase 2** — Paper / Simulated Live (siehe PHASES_V2, Abschnitt 5)
- **Phase 3** — Bounded Auto (siehe PHASES_V2, Abschnitt 5)
- **Phase 4** — Live Readiness (siehe PHASES_V2, Abschnitt 5)
- **Phase 5** — Final Live Trade (siehe PHASES_V2, Abschnitt 5)

Für Details zu jeder Phase siehe das Phasen-Dokument oben.

---

## 2. Betriebsprinzipien (nicht verhandelbar)
1. **Safety-First / Governance-First:** Kein Schritt Richtung Live ohne explizite Gates (Risk, Policies, Tests, Evidence).
2. **Kleine PR-Slices:** Multi-Agent arbeitet nur stabil, wenn PRs klein und eindeutig sind.
3. **Beweisführung statt Behauptung:** Jede Phase produziert Evidence-Artefakte (Reports, Logs, Links, Checks).
4. **Determinismus & Reproduzierbarkeit:** Jeder Run ist reproduzierbar (Seeds, Snapshots, feste Inputs).
5. **Keine “Footguns” in Docs/Code:** Keine Beispiele, die Live-Flags aktivieren; Sprache: *blocked / gated / requires operator enablement*.

---

## 3. Rollenmodell (A0–A5)
**A0 — Orchestrator (Lead Agent)**  
- Zerlegt Phasen in PR-fähige Task-Packets, delegiert an A1–A5, prüft Schnitt & Risiko.
- Erzwingt PR-Contract, Gate-Konformität, DoD und Stop-Regeln.

**A1 — Implementer (Code Agent)**  
- Implementiert genau das Task-Packet, keine Nebenrefactors.
- Hält locked-paths/policy constraints ein.

**A2 — Test & Verification Agent**  
- Schreibt/aktualisiert Tests, führt lokale Verifications aus, dokumentiert Evidence.
- Minimiert Flakiness, sorgt für deterministische Tests.

**A3 — Docs & Operator-UX Agent**  
- Runbook-Updates, Operator-How-To, Navigation/README-Links, Beispiele ohne Footguns.
- Hält docs gates ein (targets existieren, Links stimmen).

**A4 — Risk & Controls Agent**  
- Validiert Risk-Limits, kill-switches, runtime policies, Monitoring-Artefakte.
- Erstellt “Go/No-Go” Kriterien pro Phase.

**A5 — Policy Critic / Governance Agent**  
- Prüft Policy-Konformität, Live-Gates, verbotene Patterns, Evidence-Vollständigkeit.
- Gibt “Approve/Request Changes” anhand des PR-Contracts.

---

## 4. Standard-Arbeitsformat: Task-Packet (Template)
**Einsatzort:** Cursor Chat (A0), anschließend als Arbeitsauftrag an Multi-Agents.

```yaml
task_packet:
  id: "P<phase>-PR<slice>-<short_name>"
  goal: "Ein-Satz Ziel, messbar"
  scope_in:
    - "konkrete Dateien/Module"
    - "konkrete Deliverables"
  scope_out:
    - "Explizit: kein Refactor, keine Umbenennungen, keine unrelated changes"
  constraints:
    - "locked paths beachten"
    - "no live flags / no enabling examples"
    - "deterministic outputs"
  deliverables:
    - "Code:"
    - "Tests:"
    - "Docs:"
    - "Evidence:"
  verification:
    local_commands:
      - "…"
    ci_expectations:
      - "blocking gates must pass"
  risks:
    - "Haupt-Risiken + Mitigation"
  acceptance_criteria:
    - "DoD bullets"
  handoff:
    owner: "A1/A2/A3/A4/A5"
    next_action: "PR öffnen / Review anfordern / Merge vorbereiten"
```

---

## 5. PR-Contract (DoD) — Muss in jeder PR-Beschreibung stehen
**Einsatzort:** GitHub PR Description (oder `docs&#47;ops&#47;PR_<N>_MERGE_LOG.md` als Verified Log).

Pflichtsektionen:
- **Summary:** Was wurde geändert (max 6 bullets)
- **Why:** Warum nötig (1–3 bullets)
- **Changes:** Dateien/Module + Highlights
- **Verification:** Exakte Kommandos + erwartetes Ergebnis
- **Risk:** Einschätzung + mögliche Failure-Modes + Rollback
- **Operator How-To:** Wie nutzt man es (inkl. Pfade, Beispiele ohne Footguns)
- **References:** Links auf Runbooks, Evidence, Issues, PRs

**Hard DoD-Checks:**
- Keine scope creep Änderungen (nur Task-Packet).
- Tests vorhanden/angepasst (oder explizit begründet, warum nicht).
- Docs/Navi aktualisiert, wenn Operator-relevant.
- Evidence abgelegt (Report/Log) oder CI-Links dokumentiert.

---

## 6. Gate-Index (typisch in eurem Repo)
> Diese Liste ist “Front Door”; Details/Fehlerbilder siehe Appendix D.

**Blocking (muss grün sein):**
- Unit/Integration Tests (alle Python-Versionen, falls relevant)
- Lint Gate (Ruff/Format)
- Policy Critic Gate (Governance)
- docs-reference-targets-gate (keine toten Links/Targets)
- CI Health Gate / required contexts contract (falls aktiv)

**Policy/Repo-Spezialgates (meist blocking):**
- Docs Diff Guard Policy Gate
- Guard tracked files in reports directories (keine Reports einchecken)

---

## 7. PR-Slicing Policy (Multi-Agent stabilisieren)
1. **Maximal eine Subsystem-Story pro PR.**
2. **Keine “cleanup refactors” nebenbei.** Cleanup nur in eigener PR.
3. **Prefer 200–600 LOC Diffs** (größer nur mit Begründung).
4. **Docs-only PR** ist erlaubt/empfohlen, wenn Gates/Navigation betroffen sind.
5. **Reihenfolge:** Contracts/Types → Runtime/Orchestrator → Tests → Docs/Runbooks → Ops UX.
6. **Wenn ein Gate rot wird:** Stop, fix in derselben PR, keine Umgehungen.

---

## 8. Stop / Abort Criteria
A0 muss abbrechen und neu planen, wenn:
- Scope nicht mehr eindeutig ist (Task-Packet driftet).
- Ein blocking gate dauerhaft rot bleibt und Ursache unklar ist.
- Risk- oder Governance-Impact nicht sauber eingegrenzt werden kann.
- Änderungen würden Live-Enablement ermöglichen (Footgun) oder Policies verletzen.
- Es braucht Interaktion/Secrets/externes System, das nicht im Repo lösbar ist.

---

## 9. Cursor Multi-Agent Ablauf (Minimalprozess)
**Einsatzort:** Cursor (Multi-Agent), pro Phase/PR-Slice.

1. **A0 erstellt Task-Packet** (Template oben) und definiert PR-Slice.
2. **A1 implementiert** nur Scope-In.
3. **A2 ergänzt Tests & verifiziert lokal** (Appendix B).
4. **A3 aktualisiert Docs/Runbooks/Navi**, wenn Operator-relevant.
5. **A4 prüft Risk/Controls & Evidence** (Appendix A/C).
6. **A5 macht Policy-Review** gegen PR-Contract.
7. **A0 finalisiert PR Description + Evidence links** und fordert Review/Merge an.

**Operator Tooling Standard:**
- Für lange laufende Tasks (Backtests, Sweeps, VaR-Suites): siehe **bg_job Execution Pattern** in [CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2.md](CURSOR_MULTI_AGENT_RUNBOOK_PHASES_V2.md), Abschnitt 7.

---

## 10. Copy-Paste: A0 Orchestrator Prompt (Cursor Chat)
**Einsatzort:** Cursor Chat

```text
Du bist A0 (Orchestrator) für Peak_Trade. Nutze dieses Dokument als Source-of-Truth:
- Front Door: Rollen A0–A5, Task-Packet, PR-Contract, Gate-Index, Stop-Regeln
- Appendices: Phase-Matrix, Verifications, Troubleshooting, Repo-Anker/Current Reality

Aufgabe:
1) Führe zuerst den Repo-Anchoring Pass (Appendix E.1) gedanklich durch und stelle sicher, dass die in Appendix E genannten Pfade existieren.
2) Erzeuge dann ein Task-Packet für den nächsten PR-Slice der aktuellen Phase.
3) Slice so, dass der Diff klein bleibt (200–600 LOC) und genau ein Subsystem betrifft.
4) Definiere exakte deliverables, lokale verification commands, CI Erwartungen, Risiken.
5) Gib die Delegation an A1–A5 aus (je 3–6 bullet responsibilities).
6) Gib eine PR-Description nach PR-Contract aus.

Constraints:
- Kein scope creep, keine refactors nebenbei.
- Keine Live-Footguns in Docs/Code; Sprache: gated/blocked.
- Evidence muss geplant sein (wo entsteht sie, wie wird sie referenziert).
Wenn irgendein Stop-Kriterium erfüllt ist, brich ab und schlage einen kleineren Slice vor.
```

---

# Appendix A — Phase-Matrix (Shadow → Live) mit Repo-Ankern
> Diese Matrix ist der Plan. “Repo-Anker” sind konkrete Artefakte im Repo. Falls ein Anker fehlt: in Appendix E.2 nachziehen.

| Phase | Ziel | Kern-Deliverables | Repo-Anker (Beispiele; verifizieren) | Evidence | Gates |
|---|---|---|---|---|---|
| P0 | Baseline & Contracts | Contracts/Types, import-smokes | src/execution/, tests/ | CI grün | Tests, Lint, Policy |
| P1 | Shadow stabil | deterministic runs, quality reports | src/data/shadow/, scripts/shadow_*, docs/shadow/ | HTML/JSON (untracked) | reports guard, docs targets |
| P2 | Risk validation | VaR validation, backtest suite | src/risk/ oder src/risk_layer/, docs/risk/, scripts/risk/, tests/risk/ | backtest suite report | tests, docs gate |
| P3 | Risk runtime | runtime policies, audit logging | src/execution/risk_runtime/ | audit logs + tests | Policy Critic, tests |
| P4 | Execution pipeline (paper/shadow) | routing skeleton, hooks | src/execution/ | e2e dry run logs | tests, policy |
| P5 | Monitoring/alerting | dashboards, routing | src/*/alerting*, docs/ops/ | screenshots/logs | docs + tests |
| P6 | Bounded auto (shadow) | gates, overrides | src/governance/ | go/no-go evidence | governance |
| P7 | Canary | limited exposure config | config/, docs/ops/ | canary logs | strict gates |
| P8 | Incident drills | kill switch drills | docs/ops/, scripts/ops/ | drill reports | ops evidence |
| P9 | Live readiness review | checklist approvals | `docs/ops/LIVE_READINESS_PHASE_TRACKER.md` | review artifacts | governance |
| P10 | Live (manual enable) | operator-only enablement | runbooks + gating | signed evidence | final gates |

---

# Appendix B — Verification Commands (Repo-verankert: Muster + Pflicht-Check)
**Einsatzort:** Cursor Terminal / Shell

## B.1 Pflicht-Check: “Existenz der Anker”
```bash
python - <<'PY'
from pathlib import Path
root = Path(".")
candidates = [
  "docs/ops/CURSOR_MULTI_AGENT_WORKFLOW.md",
  "docs/ops/LIVE_READINESS_PHASE_TRACKER.md",
  # Erwartete (aus aktuellem Projekt-Kontext) — falls fehlend: in Appendix E ergänzen/korrekt mappen
  "docs/ops/README.md",
  "docs/risk/VAR_BACKTEST_SUITE_GUIDE.md",
  "scripts/risk/run_var_backtest_suite_snapshot.py",
  "src/data/shadow/quality_report.py",
  "scripts/shadow_run_tick_to_ohlcv_smoke.py",
  "docs/shadow/SHADOW_PIPELINE_PHASE2_OPERATOR_RUNBOOK.md",
]
for p in candidates:
  fp = root / p
  print(("OK     " if fp.exists() else "MISSING"), p)
PY
```

## B.2 Muster für PR-Verification (Scope-spezifisch)
```bash
pytest -q
pytest -q tests/execution
pytest -q tests/risk
pytest -q tests/risk/validation

uv run ruff check .
uv run ruff format --check .
```

## B.3 bg_job Runner (Timeout-sichere Background Jobs)

Für lange laufende Tasks (Backtests, Sweeps, Trainings) mit Timeout-Risiko:

**Discovery-first Command:**
```bash
bash 'scripts'/'ops'/'bg_job.sh' --help || bash 'scripts'/'ops'/'bg_job.sh' help
```

**Referenz:** `docs/ops/RUNBOOK_BACKGROUND_JOBS.md`

**Gate-Safety Hinweis:** In Dokumentations-Referenzen muss der Pfad maskiert werden (`'scripts'&#47;'ops'&#47;'bg_job.sh'`), um docs-reference-targets-gate Konflikte zu vermeiden.

---

# Appendix C — Operator Artefakte (Repo-Standards)
**Einsatzort:** Docs/Runbooks und Ops Center

Minimum je operator-relevant PR:
- Runbook-Abschnitt: **Purpose, Preconditions, How-To, Outputs, Failure modes, Rollback**
- Output-Location (z.B. `reports&#47;...`) und Hinweis: **Reports nicht tracken**
- 1–2 Operator Quick Commands (oder Integration in ein existierendes Ops-Script)
- Evidence: Screenshot/Log Snippet/CI Links

---

# Appendix D — Troubleshooting (Gates & häufige Fehler)
**docs-reference-targets-gate fails**  
- Ursache: Link/Target verweist auf nicht existierende Datei/Anchor.  
- Fix: Link korrigieren oder Ziel anlegen; danach lokal prüfen und PR aktualisieren.

**Guard tracked files in reports directories**  
- Ursache: Ein Report unter `reports/` wurde ins Git staging aufgenommen.  
- Fix: Unstage + gitignore/policy beachten; Reports nur lokal erzeugen.

**Locked path violation**  
- Ursache: Änderungen in “locked” Bereichen.  
- Fix: Änderungen verschieben oder Ansatz neu planen (A0 Stop, falls nicht lösbar).

**Policy Critic Gate**  
- Ursache: Live-Footguns, verbotene Patterns, unsafe language.  
- Fix: Sprache und Beispiele auf *gated/blocked* umstellen; keine enablement snippets.

---

# Appendix E — Repo-Anchoring Pass (v1.1 Kern)
Diese Appendix macht die Front Door “repo-verankert”. Sie verhindert, dass Agents raten müssen.

## E.1 Schnellscan (Auto-Discovery)
**Einsatzort:** Cursor Terminal / Shell

```bash
# Top-Discovery: Wo liegen Runbooks/Tracker/Gates?
rg -n "RUNBOOK|PLAYBOOK|MERGE_LOG|LIVE_READINESS|Cursor Multi-Agent|Policy Critic|kill switch" docs src scripts || true

# Risk/Execution discovery
rg -n "risk_runtime|RiskRuntime|risk hook|execution pipeline" src tests docs || true

# Shadow discovery
rg -n "shadow|tick_to_ohlcv|quality_report|quality report" src scripts docs || true
```

## E.2 “Anchored Current Reality” (ausfüllen, dann ist der Plan stabil)
**Einsatzort:** A3 (Docs Agent) — Update in dieser Datei nach jedem großen Merge

> Trage hier die **tatsächlichen** Pfade ein. Alles, was hier steht, muss im Repo existieren.

- Cursor Multi-Agent Workflow: `docs/ops/CURSOR_MULTI_AGENT_WORKFLOW.md`
- Live Readiness Tracker: `docs/ops/LIVE_READINESS_PHASE_TRACKER.md`
- Ops Index / Verified Merge Logs: `docs/ops/README.md` (falls anders: korrigieren)
- Risk Backtest Suite Guide: `docs/risk/VAR_BACKTEST_SUITE_GUIDE.md` (falls anders: korrigieren)
- Snapshot Runner: `scripts/risk/run_var_backtest_suite_snapshot.py` (falls anders: korrigieren)
- Shadow Quality Report: `src/data/shadow/quality_report.py` (falls anders: korrigieren)
- Shadow Smoke Script: `scripts/shadow_run_tick_to_ohlcv_smoke.py` (falls anders: korrigieren)
- Shadow Operator Runbook: `docs/shadow/SHADOW_PIPELINE_PHASE2_OPERATOR_RUNBOOK.md` (falls anders: korrigieren)

**Regel:** Wenn du in `docs/` oder `scripts/` neue Operator-Artefakte anlegst, müssen sie hier als Anker auftauchen.

## E.3 Copy-Paste: Anchoring Packet für Cursor Multi-Agent
**Einsatzort:** Cursor Chat (A3 als Docs Agent)

```text
Du bist A3 (Docs & Operator-UX). Ziel: Repo-Anker stabilisieren.

1) Suche im Repo nach den Anchors aus Appendix E.2 (existieren sie wirklich?).
2) Falls Pfade abweichen: aktualisiere Appendix E.2 und (falls nötig) Appendix A (Repo-Anker-Spalte).
3) Ergänze fehlende Anker (z.B. neue Runbooks, Tracker, Ops Index), aber ohne Footguns.
4) Stelle sicher, dass docs-reference-targets-gate nicht verletzt wird (keine toten Links/Targets).
5) Gib am Ende eine kurze “Anchoring Summary” (OK/MISSING + Fixes) aus.
```

---

# Appendix F — Live Execution Roadmap Runner (Frontdoor-Ausführung)

## F.0 Source of Truth (Repo-Anker)
Dieses Frontdoor-Runbook ist der **Einstiegspunkt** (Prozess, Rollen, Gates, Prompt-Pack).
Die **inhaltliche Roadmap** (Phasen + Work Packages + Gates) ist hier verankert:

- `docs/execution/PEAK_TRADE_LIVE_EXECUTION_ROADMAP_MULTI_AGENT_v1_0.md`

**Regel:** Änderungen an Phasen/WPs/Gates passieren **in der Roadmap**, nicht „ad hoc" in PR-Bodies.

---

## F.1 Rollen-Mapping (Frontdoor A0–A5 ↔ Roadmap-Rollen)
- **A0 Orchestrator** = Integrator (Lead)
- **A1 Exec-Agent** = Workstream „Execution Core"
- **A2 Risk-Agent** = Workstream „Risk Layer"
- **A3 Gov-Agent** = Workstream „Governance & Config"
- **A4 Obs-Agent** = Workstream „Observability"
- **A5 Reviewer/Policy** = Review + Gate Readout + „Stop/Abort" Authority

**Hinweis:** Shared-Files werden **nur** durch A0 geändert oder nach explizitem Lock (siehe File-Ownership Regeln).

---

## F.2 Runner-Semantik (wie „wir führen die Roadmap aus")
Die Ausführung läuft immer als wiederholbarer 6-Step Zyklus:

1. **Anchoring Pass** (Appendix E verwenden): „Current Reality" (bestehende Pfade, Packages, Gates) erfassen.
2. **Phase wählen** (standard: Phase 0) und **WPs selektieren**.
3. **Branch anlegen** nach Namensschema: `feat&#47;live-exec-phase{X}-<slug>`
4. **Task-Packets erzeugen** (pro WP) + Ownership-Locks setzen.
5. Agents implementieren in Ownership, liefern DoD/Tests/Evidence.
6. **Integration Day**: A0 integriert, fährt CI/Tests, erstellt Gate-Report + Evidence Pack.

**Stop/Abort:** Wenn Contracts/Ownership unklar sind, wird NICHT geraten. Dann „Lock-Request" an A0.

---

## F.3 Phase-0 (Foundation) — Default Startpaket
Phase-0 ist der Start, weil sie Contracts/Execution/Risk/Gov/Obs als Fundament stabilisiert.

**Work Packages (Roadmap):**
- **WP0E** Contracts & Interfaces (Integrator-Blocker)
- **WP0A** Execution Core v1
- **WP0B** Risk Layer v1.0
- **WP0C** Governance & Config Hardening
- **WP0D** Observability Minimum

**Phase-0 Gate:** Evidence Pack + CI grün + Kill-Switch/Limits verifiziert (siehe Roadmap).

---

## F.4 Task-Packet Template (WP-Ausführung)
(Verweist auf den Frontdoor Task-Packet Standard; hier nur die WP-spezifischen Pflichtfelder)

```yaml
task_packet_wp:
  wp_id: "WP0X"
  owner_agent: "A1/A2/A3/A4"
  ownership_patterns:
    - "src/execution/contracts/*"
    - "tests/execution/test_contracts*"
  out_of_scope:
    - "Keine Drive-By-Refactors"
    - "Keine Shared-Files ohne A0 Lock"
  contracts_shared_files:
    - "src/execution/types.py (A0 only)"
    - "config/execution_telemetry.toml (A0 only)"
  definition_of_done:
    - "DoD Bullet 1 (max 10 bullets)"
    - "DoD Bullet 2"
    - "…"
  tests:
    - "pytest tests/execution/test_contracts*"
    - "uv run ruff check src/execution/"
  evidence_outputs:
    - "reports/execution/contracts_smoke_report.json"
    - "docs/execution/WP0X_COMPLETION_REPORT.md"
  risks_open_points:
    - "Risiko 1 + Mitigation"
    - "Offener Punkt 2 (max 5)"
  merge_integration_notes:
    - "Integration-Reihenfolge: nach WP0E"
    - "Shared-File Conflicts: A0 koordiniert"
```

---

## F.5 Copy-Paste: A0 Roadmap Kickoff Prompt (Phase-0)
**Einsatzort:** Cursor Multi-Agent Chat. A0 erzeugt A1–A5 und verteilt Task-Packets.

```text
### A0 PROMPT — Phase-0 Kickoff (Roadmap-Runner)

Du bist A0 (Integrator). Ziel: Phase-0 der Live-Execution Roadmap umsetzen, konfliktarm und gate-driven.

INPUTS (Repo-Anker):
- docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md
- docs/execution/PEAK_TRADE_LIVE_EXECUTION_ROADMAP_MULTI_AGENT_v1_0.md

VORGEHEN:
1) Führe den Anchoring Pass (Appendix E) aus und schreibe ein kurzes „Anchored Current Reality" (bestehende Packages/Pfade/Gates).
2) Lege den Phase-0 Branch an: `feat/live-exec-phase0-foundation`
3) Erzeuge fünf Task-Packets: WP0E, WP0A, WP0B, WP0C, WP0D
   - Setze Ownership-Pattern strikt.
   - Markiere Shared-Files, die nur A0 ändern darf.
4) Spawne Agents:
   - A1 = WP0A (Execution Core)
   - A2 = WP0B (Risk Layer)
   - A3 = WP0C (Governance & Config)
   - A4 = WP0D (Observability)
   - A5 = Review/Policy/Gate Readout
5) Jeder Agent liefert am Ende:
   - geänderte Dateien
   - Test-Kommandos
   - Evidence Outputs
   - Risiken/Offene Punkte
6) Plane „Integration Day": Reihenfolge WP0E → parallel (0A/0B/0C/0D) → Gate-Report.

REGELN:
- Keine Drive-By-Refactors außerhalb Ownership.
- Schnittstellenfragen sofort an A0 eskalieren („Lock-Request").
- Kein Live-Mode Enablement; alles bleibt standardmäßig blocked (Governance).

OUTPUT:
- Task-Packets (vollständig, Format F.4)
- Agent Assignments
- Integration-Plan + Gate-Checklist
```

---

## F.6 Copy-Paste: Integration Day Prompt (A0)
**Einsatzort:** Cursor Chat (A0) — nach WP-Completion, vor PR-Merge.

```text
### A0 PROMPT — Integration Day (Phase-0)

Ziel: Integration ohne Konflikte und mit eindeutiger Gate-Evidenz.

SCHRITTE:
1) Merge-Reihenfolge: WP0E zuerst, dann 0A/0B/0C/0D.
2) Run: ruff + tests (repo-standard, alle Python-Versionen falls CI das fordert).
   - pytest -q tests/execution
   - pytest -q tests/risk
   - pytest -q tests/governance
   - uv run ruff check .
   - uv run ruff format --check .
3) Evidence Pack sicherstellen:
   - reports/execution/* (contracts smoke, state machine coverage, crash restart)
   - reports/risk/* (var/cvar/kupiec, stress suite)
   - reports/governance/* (config validation, live blocked proof)
   - reports/observability/* (metrics snapshot, logging fields)
4) Erstelle Gate-Report (Phase-0 Go/No-Go): Blocker status + offene Punkte + Stop/Abort flags.
5) PR-Contract aus Frontdoor in die PR-Beschreibung übernehmen.

OUTPUT:
- Gate-Report (Format F.7)
- PR Description (PR-Contract Compliance)
- Evidence Links (z.B. in docs/execution/WP0*_COMPLETION_REPORT.md)
```

---

## F.7 Gate Report Template (Phase-0)
**Einsatzort:** Completion Report für Phase-0 Integration.

```markdown
# Phase-0 (Foundation) Gate Report

**Phase:** 0 (Foundation)  
**Branch/PR:** feat/live-exec-phase0-foundation / PR #XXX  
**Datum:** YYYY-MM-DD  
**Integrator:** A0

---

## Blocker Status

| WP-ID | Workstream | Status | Blocker | Evidence |
|---|---|---|---|---|
| WP0E | Contracts & Interfaces | ✅ GO / ⛔ NO-GO | — | docs/execution/WP0E_COMPLETION_REPORT.md |
| WP0A | Execution Core v1 | ✅ GO / ⛔ NO-GO | — | docs/execution/WP0A_COMPLETION_REPORT.md |
| WP0B | Risk Layer v1.0 | ✅ GO / ⛔ NO-GO | — | reports/risk/* |
| WP0C | Governance & Config | ✅ GO / ⛔ NO-GO | — | reports/governance/* |
| WP0D | Observability Minimum | ✅ GO / ⛔ NO-GO | — | reports/observability/* |

---

## CI/Tests

```bash
# Commands run:
pytest -q tests/execution
pytest -q tests/risk
pytest -q tests/governance
uv run ruff check .
uv run ruff format --check .

# Result: ✅ PASS / ❌ FAIL
```

---

## Evidence Pack (Links/Pfade)

- **Execution:** `reports/execution/contracts_smoke_report.json`, `docs/execution/WP0A_COMPLETION_REPORT.md`
- **Risk:** `reports/risk/var_validation_snapshot.json`, `reports/risk/stress_suite_summary.md`
- **Governance:** `reports/governance/config_validation.json`, `reports/governance/live_blocked_proof.txt`
- **Observability:** `reports/observability/metrics_snapshot.json`, `reports/observability/logging_fields.yaml`

---

## Risiken / Red Flags

1. **Risiko 1:** Beschreibung + Mitigation
2. **Risiko 2:** Beschreibung + Mitigation
3. *(max 5 bullets)*

---

## Entscheidung

**✅ GO** / **⛔ NO-GO**

*(Begründung: max 3 Sätze)*

---

## Nächste Schritte

- Falls GO: PR mergen, Phase-1 planen.
- Falls NO-GO: Blocker beheben, Gate erneut ausführen.
```

---

## Änderungslog
- v1.1: Repo-Anchoring Pass (Appendix E) + Existenz-Check (Appendix B.1) + konkrete Ankerliste (verifizieren und pflegen).
- v1.2: Live Execution Roadmap Runner (Appendix F) hinzugefügt — Multi-Agent-Workflow für Phase-0 bis Live.

---

## Appendix: Maintenance / Ownership

- Owner: Ops / Operator Tooling
- Update triggers:
  - Cursor Multi-Agent workflow changes (roles, protocol, handoffs)
  - New operator runbooks or readiness gates
  - CI policy changes affecting docs reference validation
- Guardrails:
  - Avoid repo-relative file paths for non-existent targets (docs-reference-targets-gate).
  - Prefer discovery instructions (e.g., `rg`) when referencing evolving files.

### CI: Docs Reference Targets Gate

Wenn der CI-Check **Docs Reference Targets Gate** fehlschlägt, liegt das häufig an
pfadähnlichen Tokens in Markdown (Links, Inline-Code oder „bare paths"), die der Gate
als zu validierende Targets interpretiert.

Verbindliche Regeln und robuste Schreibweisen findest du hier:
- [Docs Reference Targets Gate – Style Guide](DOCS_REFERENCE_TARGETS_GATE_STYLE_GUIDE.md)

Pragmatische Sofort-Triage:
```bash
# Suche nach potenziellen "bare path" Kandidaten (Gate-Trigger)
rg -n '(^|[^\\])(docs|src)\/' docs -S || true
```

Daumenregel:
- Nur zu **existing** Targets verlinken.
- **Future** Targets nur als Text erwähnen: in Anführungszeichen, mit `(future)` und Slashes escaped (z.B. `docs\&#47;...`).
