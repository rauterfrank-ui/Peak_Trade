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
**Einsatzort:** GitHub PR Description (oder `docs/ops/PR_<N>_MERGE_LOG.md` als Verified Log).

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
| P0 | Baseline & Contracts | Contracts/Types, import-smokes | `src/execution/…` + `tests/…` | CI grün | Tests, Lint, Policy |
| P1 | Shadow stabil | deterministic runs, quality reports | `src/data/shadow/…`, `scripts/shadow_…`, `docs/shadow/…` | HTML/JSON (untracked) | reports guard, docs targets |
| P2 | Risk validation | VaR validation, backtest suite | `src/risk/…` oder `src/risk_layer/…`, `docs/risk/…`, `scripts/risk/…`, `tests/risk/…` | backtest suite report | tests, docs gate |
| P3 | Risk runtime | runtime policies, audit logging | `src/execution/risk_runtime/…` | audit logs + tests | Policy Critic, tests |
| P4 | Execution pipeline (paper/shadow) | routing skeleton, hooks | `src/execution/…` | e2e dry run logs | tests, policy |
| P5 | Monitoring/alerting | dashboards, routing | `src/…/alerting…`, `docs/ops/…` | screenshots/logs | docs + tests |
| P6 | Bounded auto (shadow) | gates, overrides | `src/governance/…` | go/no-go evidence | governance |
| P7 | Canary | limited exposure config | `config/…`, `docs/ops/…` | canary logs | strict gates |
| P8 | Incident drills | kill switch drills | `docs/ops/…`, `scripts/ops/…` | drill reports | ops evidence |
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

---

# Appendix C — Operator Artefakte (Repo-Standards)
**Einsatzort:** Docs/Runbooks und Ops Center

Minimum je operator-relevant PR:
- Runbook-Abschnitt: **Purpose, Preconditions, How-To, Outputs, Failure modes, Rollback**
- Output-Location (z.B. `reports/...`) und Hinweis: **Reports nicht tracken**
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

## Änderungslog
- v1.1: Repo-Anchoring Pass (Appendix E) + Existenz-Check (Appendix B.1) + konkrete Ankerliste (verifizieren und pflegen).
