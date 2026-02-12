# RUNBOOK — Peak_Trade „bis Finish“ (Master Runbook)

**Ziel:** Dieses Runbook führt dich vom aktuellen **docs-only Branch-Stand** (untracked Files + 1× EOF-Newline) bis zu einem klar definierten „Finish“-Zustand – inkl. PR‑Lieferung, DoD‑Verifikationen für D2/D3/D4 und optionalen (governance‑locked) Finish‑C / Option‑B Tracks.

**Geltungsbereich:** Standardmäßig **docs-only** (kein Code‑Change, keine Live‑Aktivierung).  
**NO‑LIVE Default:** gilt durchgehend. Alles Live‑nahe bleibt **Governance‑locked**.

---

## 0) Quickstart (Operator)

### Entry
- Du bist lokal im Repo und auf deinem Branch (z.B. `feat/reporting-generator-d2-d3`).
- Working Tree enthält docs-only Änderungen + untracked docs.

### Exit
- Alles committed, PR erstellt, Docs Gates/Tests nach Plan nachweisbar PASS.
- D2/D3/D4 sind **operational „Done“** (DoD‑Checks reproduzierbar).
- „Finish“-Definition ist **Single Source of Truth** (SSoT) dokumentiert & verlinkt (konkret).

---

## 1) Definitionen (was heißt „Finish“?)

Du willst verhindern, dass „Finish“ diffus bleibt. Nutze **genau eine** Definition als SSoT.

### Finish-Optionen
1. **Konservativ (Default, empfohlen):**  
   **Finish = MVP v1.0 + D2/D3/D4 vollständig (ops/reporting/watch-only) inkl. Runbooks + Tests/Verify-Snapshots.**
2. **Roadmap-basiert:**  
   **Finish = Phasen 11–12 (Advanced Research + Realtime) abgeschlossen; Phase 13 (Live) nur nach Governance-Gate.**
3. **Ops-basiert:**  
   **Finish = Finish‑A/B/C Tracks vollständig; C endet in „Controlled Readiness“ (ohne Live-Freischaltung).**

### SSoT-Place (wähle 1 Datei)
- [INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md](../INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md) (wenn bereits „Roadmap-Snapshot“ enthält)
- oder [PEAK_TRADE_STATUS_OVERVIEW.md](PEAK_TRADE_STATUS_OVERVIEW.md) (falls vorhanden)
- oder [WORKFLOW_FRONTDOOR.md](WORKFLOW_FRONTDOOR.md) (wenn du es als Frontdoor führst)

**Acceptance:** In SSoT steht 1 Satz „Finish = …“ + Link auf dieses Runbook + Link auf D2/D3/D4 Runbooks.

---

## 2) Rollen & Arbeitsmodus (Cursor Multi‑Agent)

**Arbeitsmodus:** Cursor Multi‑Agent Chat.  
**Rollen-Set (empfohlen 5–7 Agents parallel):**
- **ORCHESTRATOR** (führt, weist Aufgaben zu, sammelt Ergebnisse)
- **SCOPE_KEEPER** (docs-only, NO‑LIVE, keine Sidequests)
- **DOCS_GATES_GUARD** (Token‑Policy, Reference Targets, Diff Guard, Format)
- **RUNBOOK_EDITOR** (strukturierte Runbooks/Indices/Frontdoor)
- **EVIDENCE_SCRIBE** (Verification Notes, Evidence Pack, Merge‑Log‑Style)
- **RISK_OFFICER** (Go/No‑Go Checks, Governance wording)
- **RESEARCH_REVIEWER** (Option‑B Doku: Scope/Claims/No‑Code Klarheit)

---

## 3) Phase A — Branch „lieferfähig“ machen (Docs Hygiene + Integration)

### A1 — Pre‑Flight (lokal, deterministisch)
**Entry:** egal welcher Zustand, aber du willst sicherstellen: richtiges Repo, keine Shell‑Continuation.  
**Exit:** Repo-Root bestätigt, Branch korrekt, Status sichtbar.

> **Cursor Terminal — Single Block (Pre‑Flight + Status)**
```bash
# == CONTINUATION GUARD ==
# Wenn dein Prompt so aussieht: ">" oder "dquote>" oder "heredoc>" → erst Ctrl-C drücken.
printf "\n=== CONTINUATION GUARD ===\nIf you see > / dquote> / heredoc> → press Ctrl-C first.\n\n"

# == CD TO REPO (adjust if needed) ==
cd "/Users/frnkhrz/Peak_Trade" 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || cd "$PWD"

echo "=== PWD ==="
pwd

echo "=== GIT TOPLEVEL ==="
git rev-parse --show-toplevel 2>/dev/null || true

echo "=== GIT STATUS ==="
git status -sb || true

echo "=== BRANCH ==="
git branch --show-current 2>/dev/null || true
```

### A2 — Fix: EOF-Newline (merge‑relevant Hygiene)
**Target:** `docs/RUNBOOKS_AND_INCIDENT_HANDLING.md` finalen Newline ergänzen.

> **Cursor Terminal — Single Block (EOF-Newline fix)**
```bash
# == CONTINUATION GUARD ==
# If you see > / dquote> / heredoc> → Ctrl-C first.
printf "\n=== CONTINUATION GUARD ===\n"

cd "/Users/frnkhrz/Peak_Trade" 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || cd "$PWD"
pwd
git rev-parse --show-toplevel 2>/dev/null || true
git status -sb || true

FILE="docs/RUNBOOKS_AND_INCIDENT_HANDLING.md"
echo "=== EOF CHECK: $FILE ==="
python3 - <<'PY'
import pathlib
p = pathlib.Path("docs/RUNBOOKS_AND_INCIDENT_HANDLING.md")
b = p.read_bytes()
print("bytes:", len(b))
print("endswith_newline:", b.endswith(b"\n"))
PY

echo "=== APPLY: ensure trailing newline (idempotent) ==="
python3 - <<'PY'
import pathlib
p = pathlib.Path("docs/RUNBOOKS_AND_INCIDENT_HANDLING.md")
b = p.read_bytes()
if not b.endswith(b"\n"):
    p.write_bytes(b + b"\n")
    print("FIXED: appended newline")
else:
    print("OK: already ends with newline")
PY

git status -sb || true
```

### A3 — Untracked Files aufnehmen (Runbooks + Research)
**Targets (untracked):**
- [RUNBOOK_D4_OPS_GOVERNANCE_POLISH.md](ops/runbooks/RUNBOOK_D4_OPS_GOVERNANCE_POLISH.md)
- [RUNBOOK_FINISH_C_V1_LIVE_BROKER_OPS.md](ops/runbooks/RUNBOOK_FINISH_C_V1_LIVE_BROKER_OPS.md)
- docs/research/option_b (2 Dateien)

**Exit:** alle Dateien sind im Index (staged) oder bewusst **explizit** ausgeschlossen (und dokumentiert).

> **Cursor Terminal — Single Block (Stage docs-only)**
```bash
# == CONTINUATION GUARD ==
printf "\n=== CONTINUATION GUARD ===\n"

cd "/Users/frnkhrz/Peak_Trade" 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || cd "$PWD"
pwd
git rev-parse --show-toplevel 2>/dev/null || true
git status -sb || true

echo "=== ADD (docs-only) ==="
git add docs/RUNBOOKS_AND_INCIDENT_HANDLING.md         docs/ops/runbooks/README.md         docs/runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md         docs/ops/runbooks/RUNBOOK_D4_OPS_GOVERNANCE_POLISH.md         docs/ops/runbooks/RUNBOOK_FINISH_C_V1_LIVE_BROKER_OPS.md         docs/research/option_b || true

echo "=== STAGED DIFF (names) ==="
git diff --cached --name-only || true
```

---

## 4) Phase B — Docs Gates & Test-Snapshot (lokal)

### B1 — Minimal Test Plan (D2)
**Pflicht:** `python3 -m pytest -q tests&#47;reporting&#47;test_report_generator.py`  
**Exit:** PASS + in Verification Note erfasst.

> **Cursor Terminal — Single Block**
```bash
# == CONTINUATION GUARD ==
printf "\n=== CONTINUATION GUARD ===\n"

cd "/Users/frnkhrz/Peak_Trade" 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || cd "$PWD"
pwd
git rev-parse --show-toplevel 2>/dev/null || true
git status -sb || true

echo "=== TEST (D2 subset) ==="
python3 -m pytest -q tests/reporting/test_report_generator.py || true
```

### B2 — Docs Gates (lokal best effort)
Da dein Repo mehrere Gates hat, ist der robuste Ansatz: **discover + run** ohne harte Exits.

> **Cursor Terminal — Single Block**
```bash
# == CONTINUATION GUARD ==
printf "\n=== CONTINUATION GUARD ===\n"

cd "/Users/frnkhrz/Peak_Trade" 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || cd "$PWD"
pwd
git rev-parse --show-toplevel 2>/dev/null || true
git status -sb || true

echo "=== DISCOVER docs gate scripts (best effort) ==="
ls -la scripts/ops 2>/dev/null | sed -n '1,120p' || true

echo "=== TRY: pre-commit (if present) ==="
pre-commit run -a || true

echo "=== NOTE ==="
echo "If your repo has dedicated docs gate snapshot scripts, run them here and capture PASS evidence."
```

**Evidence Hook:** `Verification note` in PR Description oder separate Evidence Datei unter `docs/ops/evidence/`.

---

## 5) Phase C — Commit + PR (docs-only)

### C1 — Commit Message (konkret & klein)
**Empfohlen (Beispiel):**
- `docs(ops): extend runbook indices for D4 + finish-c pointers`
- `docs(research): add option-b no-code roadmap docs`

### C2 — Commit & Push
> **Cursor Terminal — Single Block**
```bash
# == CONTINUATION GUARD ==
printf "\n=== CONTINUATION GUARD ===\n"

cd "/Users/frnkhrz/Peak_Trade" 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || cd "$PWD"
pwd
git rev-parse --show-toplevel 2>/dev/null || true
git status -sb || true

echo "=== COMMIT (edit message if needed) ==="
git commit -m "docs(ops): polish runbook indices (D4 + finish-c pointers)" || true

echo "=== PUSH (current branch) ==="
BR="$(git branch --show-current 2>/dev/null)"
echo "branch=$BR"
git push -u origin "$BR" || true
```

### C3 — PR Template (Kurz, merge‑log‑kompatibel)

**PR Description (copy/paste):**
```md
## Summary
Docs-only: runbook indices/landscape updated; new D4 ops/governance polish runbook; finish-c pointer runbook; option-b research docs.

## Why
Make “Finish” workstreams discoverable and operational via canonical entry points.

## Changes
- Updated:
  - docs/RUNBOOKS_AND_INCIDENT_HANDLING.md (index + EOF newline)
  - docs/ops/runbooks/README.md (D4 + finish-c pointers)
  - docs/runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md (D4 + finish-c pointers)
- Added:
  - docs/ops/runbooks/RUNBOOK_D4_OPS_GOVERNANCE_POLISH.md
  - docs/ops/runbooks/RUNBOOK_FINISH_C_V1_LIVE_BROKER_OPS.md
  - docs/research/option_b/* (no-code roadmap/policy)

## Verification
- PASS: python3 -m pytest -q tests&#47;reporting&#47;test_report_generator.py
- Docs gates: (list PASS snapshots or CI links)

## Risk
LOW (docs-only). No execution changes. NO-LIVE default unchanged.

## Operator Notes
Follow RUNBOOK_D4 for templates/frontdoor consistency.
```

---

## 6) Phase D — D2 „Done“ (Reporting + Compare Runs) operational verifizieren

### Entry
- Runbook `docs/runbooks/RUNBOOK_D2_REPORTING.md` existiert.
- Test subset PASS.

### Actions (DoD)
- Single‑Run HTML Report erzeugen (1‑Command).
- Compare‑Report erzeugen (1‑Command).
- Determinismus: fixed `generated_at_utc` / run_ids/inputs stabil.

### Evidence
- `Verification note` (PR) + optional Evidence Datei:
  - `docs&#47;ops&#47;evidence&#47;EV_D2_REPORTING_PASS_<UTC>.md`

### Exit
- DoD erfüllt, Runbook zeigt **genau** die Commands, die PASS sind.

> **Cursor Multi‑Agent Prompt (Chat) — D2 DoD Audit**
```text
TOOL: Cursor Multi-Agent Chat

ORCHESTRATOR: Prüfe das Runbook docs/runbooks/RUNBOOK_D2_REPORTING.md gegen den aktuellen Code/Tests.
Ziele:
1) DoD-Checkliste explizit machen (Single-Run, Compare, determinism).
2) Exakte Commands und erwartete Outputs definieren (token-policy safe in docs).
3) Verification Note Text liefern (copy/paste) inkl. Test-Subset.

Agents:
- DOCS_GATES_GUARD: token-policy & reference targets safety check
- RUNBOOK_EDITOR: Runbook-Text polieren ohne neue Scope-Claims
- EVIDENCE_SCRIBE: Evidence/Verification snippet erstellen
- SCOPE_KEEPER: docs-only + NO-LIVE prüfen
Output:
- Patch-Vorschlag als unified diff (nur benötigte Dateien)
- Verification note (ready-to-paste)
```

---

## 7) Phase E — D3 „Done“ (Watch‑Only Web/API + Grafana) operational verifizieren

### Entry
- D3 Runbook existiert: `docs/runbooks/RUNBOOK_D3_WATCH_ONLY_WEB_API_GRAFANA.md`.

### Actions (DoD)
- API Contract v0: Endpunkte & Pages überprüfbar.
- Security: **read‑only** Garantien (keine mutierenden Endpunkte im Watch‑Only Pfad).
- Grafana verify snapshot: **ohne Watch‑Loops**, reproduzierbar.

### Evidence
- `docs&#47;ops&#47;evidence&#47;EV_D3_WATCH_ONLY_PASS_<UTC>.md` (optional)
- oder PR Verification Note + CI Links.

### Exit
- Runbook enthält Snapshot‑Verify Commands + erwartete PASS Criteria.

> **Cursor Multi‑Agent Prompt (Chat) — D3 DoD Audit**
```text
TOOL: Cursor Multi-Agent Chat

ORCHESTRATOR: Audit D3 Watch-Only Web/API + Grafana Runbook (docs/runbooks/RUNBOOK_D3_WATCH_ONLY_WEB_API_GRAFANA.md).
Ziele:
1) DoD als testbare Checkliste (API pages/endpoints + read-only assurances + grafana verify snapshot).
2) Token-policy-safe Darstellung (keine inline backticks mit / in docs; nutze &#47; in inline code).
3) Operator Steps als snapshot-only (keine polling loops).
Agents:
- RISK_OFFICER: read-only/security wording + NO-LIVE compliance
- DOCS_GATES_GUARD: token-policy + link targets
- RUNBOOK_EDITOR: Struktur/Navigation
- EVIDENCE_SCRIBE: Evidence/Verification snippet
Output:
- Patch-Vorschlag (diff)
- „Verify Snapshot“ Block (terminal-ready)
- Verification note (ready-to-paste)
```

---

## 8) Phase F — D4 „Done“ (Ops/Governance Polish) operationalisieren

### Entry
- [RUNBOOK_D4_OPS_GOVERNANCE_POLISH.md](ops/runbooks/RUNBOOK_D4_OPS_GOVERNANCE_POLISH.md) liegt vor.

### Actions (DoD)
- Templates konsolidiert:
  - Merge‑Log Template (kompakt)
  - Evidence Template
  - Release Checklist
- Frontdoor Links konsistent:
  - [docs&#47;ops&#47;runbooks&#47;README.md](ops/runbooks/README.md)
  - [docs&#47;runbooks&#47;RUNBOOKS_LANDSCAPE_2026_READY.md](runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md)
  - optional [docs&#47;WORKFLOW_FRONTDOOR.md](WORKFLOW_FRONTDOOR.md)
- Gate‑Incidents reduzieren:
  - Styleguide / False‑Positive Runbooks zentral referenziert.

### Evidence
- PR enthält „Operator Notes“ und Links zu Templates.

### Exit
- Operator kann D4 nutzen, um zukünftige docs-only PRs schneller „gate-safe“ zu machen.

---

## 9) Phase G — Finish Definition in SSoT fixieren (1 Satz + Links)

### Entry
- Du hast dich für Option 1/2/3 entschieden.

### Actions
- In SSoT Datei: 1 Satz „Finish = …“
- Links:
  - D2 Runbook
  - D3 Runbook
  - D4 Runbook
  - (optional) Finish‑C pointer Runbook
  - (optional) Option‑B research docs

### Exit
- „Finish“ ist nicht mehr subjektiv: ein kanonischer Satz + Navigation.

---

## 10) Optional: Phase H — Finish‑C Track (Governance‑Locked, NO‑LIVE)

**Wichtig:** Das ist **Readiness** ohne Live‑Freischaltung.  
**Exit-Kriterium:** ausschließlich Artefakte/Runbooks/Evidence, keine Live‑Orders.

### Deliverables (C0–C5 + D1)
- C0 Governance Contract / Threat Model
- C1 Broker Adapter Skeleton (idempotent/retry/rate‑limit)
- C2 Orchestrator Dry‑Run (State Machine, Audit)
- C3 Reconciler & Safety Rails
- C4 Observability + Operator UX
- C5 Controlled Readiness (Artefakte)
- D1 Drill Pack (Kill‑Switch, Two‑man rule, Go/No‑Go)

**Operator Gate:** explizites Governance‑Gate vor Phase 13 (Live).

---

## 11) Optional: Phase I — Option‑B (Research-only, No‑Code Policy Track)

### Deliverables
- `DATA_POLICY_TECH_EQUITIES.md`
- `DATA_POLICY_INDEX_FUTURES.md`
- Phasen A–F (Design/Policy Deliverables):
  - Instrument Meta / Contract Chain
  - Roll Ledger / Continuous Builder + Attribution
  - Corporate Actions / Survivorship / Delistings
  - Cross‑Asset Risk / Sizing

### Exit
- Klare Entscheidung: bleibt Research-only vs. wird eigener Implementierungs‑Track.

---

## 12) „Done“ Kriterien (Final)

Du bist „bis Finish“ durch, wenn:

- **PR (docs-only) merged** und Navigation sauber.
- **D2**: Single + Compare Reports reproduzierbar; Test subset PASS.
- **D3**: Watch‑Only Contract + Read‑only Guarantees + Grafana verify snapshot operational.
- **D4**: Templates/Frontdoor/Gates‑Hygiene operational.
- **Finish‑Definition** als 1 Satz in SSoT + Links.
- Optional: Finish‑C / Option‑B bleiben korrekt als governance‑locked bzw. no‑code gekennzeichnet.

---

## Appendix A — Merge‑Log Mini‑Template (kompakt)

```md
# PR_<NUM>_MERGE_LOG

## Summary
## Why
## Changes
## Verification
## Risk
## Operator How-To
## References
```

## Appendix B — Evidence Mini‑Template

```md
# EV_<ID> — <Title>
Date: <UTC>
Scope: <docs-only/code>
Result: PASS|FAIL
Commands:
- <command 1>
Outputs:
- <key output>
Notes:
- <any constraints>
```
