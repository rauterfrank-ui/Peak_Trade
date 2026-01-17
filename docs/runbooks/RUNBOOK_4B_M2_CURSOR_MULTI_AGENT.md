# RUNBOOK — 4B Milestone 2: Cursor Multi-Agent Chat (Peak_Trade)

**Stand:** 2026-01-09  
**Owner:** Operator (Frank)  
**System:** Peak_Trade  
**Milestone:** 4B M2 - Cursor Multi-Agent Workflow Integration

---

## 0. Zweck / Outcome

Dieses Runbook standardisiert die Vorbereitung und Durchführung von **4B Milestone 2** als **Cursor Multi-Agent Chat Session**:
- Reproduzierbarer Workspace (Git Worktree)
- Klare Rollen/Verantwortlichkeiten (Agents)
- Einheitliche Artefakte (Logs, Checklisten, PR-Pakete)
- Auditstabile Verifikation (Lint/Audit/Docs-Gates, Tests)

**Definition "Done" (Milestone-2-ready):**
- ✅ Worktree existiert, ist clean und auf korrekter Base (origin/main)
- ✅ Cursor-Multi-Agent Chat initialisiert mit System-Prompt + Rollen
- ✅ Session-Log & Task-Board angelegt
- ✅ Standard-Gates lokal ausführbar (mind. ruff + unit test slice)
- ✅ PR-Skeleton (Titel/Scope/Checkliste) vorbereitet

---

## 1. Kontext (Peak_Trade Basis)

Peak_Trade ist modular aufgebaut (Data/Strategy/Core/Backtest/Runner).  
Workflows sind prompt-getrieben und auditfokussiert (Docs-Gates, Lint-Gate, Audit-Gate).  
Siehe `WORKFLOW_NOTES.md` für den etablierten "All-in-One Prompt"-Stil.

**Governance:**
- NO autonomous live trading/execution
- NO bypass von governance locks, risk gates, safety gates
- High-risk paths (`src/execution/`, `src/governance/`, `src/risk/`) require explicit operator approval

---

## 2. Rollenmodell (Cursor Multi-Agent)

### Agent A — LEAD / Orchestrator
- Zerlegt Milestone 2 in Tasks, hält die "Definition of Done"
- Kontrolliert Scope-Creep, priorisiert CI-Stabilität
- Macht Go/No-Go Entscheidungen für Task-Chunks

### Agent B — IMPLEMENTER
- Code-Änderungen (kleine, reviewbare Commits ≤ 200 LOC)
- Schreibt Tests/Fixtures, hält APIs stabil
- Focused auf minimale Diffs

### Agent C — CI_GUARDIAN / Quality Guardian
- Führt Gates lokal aus, minimiert CI-Roundtrips
- Prüft ruff/pytest/pip-audit, dokumentiert Findings
- Proposes verification commands with expected outputs

### Agent D — DOCS_OPS
- Aktualisiert Runbooks, Merge-Logs, Index-Links
- Sorgt für "Docs Reference Targets Gate"-Konformität
- Maintains session artifacts (log, taskboard, decisions)

### Operator (du)
- Trifft Entscheidungen bei Trade-offs (Scope, risk)
- Führt Terminal-Aktionen aus, wenn nötig
- Approves high-risk changes explicitly

---

## 3. Workspace-Standard (Worktree)

### 3.1 Naming
- **Worktree-Ordner:** `~/.cursor-worktrees/Peak_Trade/4b-m2`
- **Branch:** `feat/4b-m2-cursor-multi-agent`
- **PR Title:** `feat(ai): 4B M2 cursor multi-agent workflow`

### 3.2 Setup-Prozess
```bash
# Automatisiertes Setup via Skript (historical, script no longer exists)
# bash /Users/frnkhrz/Peak_Trade/scripts/ops/setup_worktree_4b_m2.sh /Users/frnkhrz/Peak_Trade

# Öffne Worktree in Cursor
code /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2
```

### 3.3 Struktur im Worktree (Session-Artefakte)
Automatisch erstellt:
- `docs/ops/sessions/SESSION_4B_M2_20260109.md` (laufendes Log, dated)
- `docs/ops/sessions/SESSION_4B_M2_TASKBOARD.md` (Task-Board/Checklist)
- `docs/ops/sessions/SESSION_4B_M2_DECISIONS.md` (Decision Log)

Templates:
- `docs/ops/sessions/APPENDIX_A_SYSTEM_PROMPT.md` (Multi-Agent System Prompt)
- `docs/ops/sessions/APPENDIX_B_TASKBOARD_TEMPLATE.md` (Wiederverwendbar)
- `docs/ops/sessions/APPENDIX_C_PR_TEMPLATE.md` (PR Structure)

---

## 4. Multi-Agent Chat Initialisierung (Cursor)

### 4.1 Session-Prompt
Verwende den Prompt aus `docs/ops/sessions/APPENDIX_A_SYSTEM_PROMPT.md`.  
Paste ihn als erste Nachricht im Cursor Multi-Agent Chat.

### 4.2 Kommunikationsprotokoll
Jede Agent-Antwort:
- Beginnt mit: `ROLE: [LEAD|IMPLEMENTER|CI_GUARDIAN|DOCS_OPS]`
- Endet mit:
  - `Next:` (konkreter nächster Schritt)
  - `Risk:` (Risiko/Unsicherheit)
  - `Evidence:` (Datei/Command/Log-Referenz)

### 4.3 Review-Takt
Nach jedem "Task Chunk" (max. 200 LOC):
- `ruff format --check`
- `ruff check`
- Relevante pytest-Subset
- Docs-Targets/Links (wenn Docs berührt)

---

## 5. Standard-Gates (lokal, minimal)

**Ziel:** "CI-Roundtrip minimieren" — lokal so viel wie möglich.

### Minimal Gates
```bash
cd /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2

# Lint Gate
uv run ruff format --check src/
uv run ruff check src/

# Test Gate (targeted)
uv run pytest -q tests/[module]

# Audit Gate (wenn Deps geändert)
uv run pip-audit
```

### Wenn Audit-Gate existiert
- `pip-audit` oder `uv pip-audit` (je nach Repo-Standard)

**Regel:** Audit-Findings sind keine "Warteschleife"; sie werden entweder:
1. Remediated
2. Sauber dokumentiert & scoped
3. In eine separate PR ausgelagert

---

## 6. Change-Management / PR-Disziplin

### PR-Scope
- **1 Milestone-2 PR = nur Milestone-2 Scope**
- Getrennte PRs für:
  - Audit-Remediation (Dependencies)
  - Reine Docs-Kosmetik
  - Refactors ohne funktionalen Gewinn

### Commit-Policy (empfohlen)
- Kleine Commits, eindeutige Messages
- Ein "Verification" Abschnitt im PR-Body mit lokalen Commands + Ergebnissen
- Pre-commit hooks müssen passen

### Branch-Hygiene
- Worktree-Branch basiert auf `origin&#47;main`
- Regelmäßig rebase (bei langer Session)
- Clean commit history vor final push

---

## 7. Incident-Playbook (typische Stolpersteine)

### 7.1 Lint Gate rot
```bash
# Problem: ruff format check fails
# Fix:
uv run ruff format src/
git add -u
git commit -m "style: apply ruff formatting"
```

### 7.2 Audit Gate rot (pip-audit Findings)
**Prozess:**
1. Finding identifizieren (Package, Version, CVE)
2. Prüfen: transitive vs direct
3. Fix path:
   - Bump/constraint
   - Replace dependency
   - (Notfalls) documented exception mit Ticket/Issue + Scope-Begründung

### 7.3 Docs Reference Targets Gate rot
**Problem:** Pfad-ähnliche Strings als Text ohne Backticks
**Fix:**
- Keine "pfadähnlichen Strings" als Text ohne Backticks/Codeblock
- To-Do Pfade in Backticks oder als "(File: …)" formatieren

### 7.4 Test Failures
**Prozess:**
1. Run targeted tests: `uv run pytest -xvs tests/[specific_test]`
2. Fix minimal, avoid scope creep
3. Re-run full test suite if broad changes

### 7.5 Pre-commit Hook Failures
**Common issues:**
- Trailing whitespace
- End of file fixes
- Mixed line endings
**Fix:** Pre-commit auto-fixes most; commit and retry

---

## 8. Closeout (Milestone-2-ready Output)

Am Ende muss existieren:
- ✅ Worktree-Setup dokumentiert
- ✅ Session-Log + Taskboard mit Status
- ✅ PR-Skeleton fertig (oder PR erstellt)
- ✅ Verification-Snippet im Log:
  - ruff ok
  - pytest subset ok
  - audit status dokumentiert (ok oder findings + plan)
- ✅ Decision log populated (mind. 2 Entscheidungen)
- ✅ All P0 tasks von Taskboard completed

---

## 9. Quick Reference Commands

### Worktree Operations
```bash
# List all worktrees
git worktree list

# Remove worktree (if cleanup needed)
git worktree remove /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2

# Prune stale worktree references
git worktree prune
```

### Development Environment
```bash
# Activate uv environment (auto-activated by uv run)
cd /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2

# Check environment
uv run python --version
uv run pip list | grep -E "(ruff|pytest|pip-audit)"
```

### Gate Verification
```bash
# Quick gate check (all in one)
cd /Users/frnkhrz/.cursor-worktrees/Peak_Trade/4b-m2
uv run ruff format --check src/ && \
uv run ruff check src/ && \
uv run pytest -q tests/ && \
echo "✅ All gates passed"
```

### Session Management
```bash
# Open session log
code docs/ops/sessions/SESSION_4B_M2_20260109.md

# Open taskboard
code docs/ops/sessions/SESSION_4B_M2_TASKBOARD.md

# Check git status
git status -sb
git log --oneline -5
```

---

## 10. References

### Documentation
- **Governance:** `.cursor/rules/peak-trade-governance.mdc`
- **Delivery Contract:** `.cursor/rules/peak-trade-delivery-contract.mdc`
- **Workflow Notes:** `docs/WORKFLOW_NOTES.md`

### Session Artifacts
- **Log:** `docs/ops/sessions/SESSION_4B_M2_20260109.md`
- **Taskboard:** `docs/ops/sessions/SESSION_4B_M2_TASKBOARD.md`
- **Decisions:** `docs/ops/sessions/SESSION_4B_M2_DECISIONS.md`

### Templates
- **System Prompt:** `docs/ops/sessions/APPENDIX_A_SYSTEM_PROMPT.md`
- **Taskboard Template:** `docs/ops/sessions/APPENDIX_B_TASKBOARD_TEMPLATE.md`
- **PR Template:** `docs/ops/sessions/APPENDIX_C_PR_TEMPLATE.md`

### Scripts
- **Worktree Setup:** `scripts&#47;ops&#47;setup_worktree_4b_m2.sh` (historical)

---

## 11. Success Criteria

### Technical
- ✅ All local gates pass (ruff, pytest, audit)
- ✅ No high-risk paths modified without explicit approval
- ✅ Pre-commit hooks pass
- ✅ Clean git history

### Process
- ✅ Session artifacts complete and up-to-date
- ✅ Task chunks ≤ 200 LOC each
- ✅ Verification commands documented
- ✅ Decision log populated

### Deliverables
- ✅ PR ready for review
- ✅ CI passes (or predicted behavior documented)
- ✅ Audit baseline documented
- ✅ Operator handoff complete

---

**Version:** 1.0  
**Last Updated:** 2026-01-09  
**Owner:** Frank (Operator)  
**Status:** Active
