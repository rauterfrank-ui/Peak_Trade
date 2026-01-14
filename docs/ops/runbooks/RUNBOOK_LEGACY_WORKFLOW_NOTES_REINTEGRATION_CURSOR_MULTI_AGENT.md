# RUNBOOK: Legacy Workflow Notes Reintegration (KEEP EVERYTHING) — Cursor Multi-Agent

## Purpose
Dieses Runbook beschreibt einen **repo-konformen**, **minimal-invasiven** Ablauf, um Legacy-Workflow-Notizen (`Peak_Trade_WORKFLOW_NOTES.md`) **vollständig** (KEEP EVERYTHING) in das aktuelle Docs-Setup zu integrieren, inklusive **Frontdoor-Linking** und **Token-Policy-konformer** Behandlung von Inline-Code Tokens mit “/”.

## Scope
- **Docs-only** Änderungen (Runbook, Archive, Index/Frontdoor-Link).
- Keine inhaltliche Kürzung, keine semantische Umformulierung der Legacy Notes.
- Keine Watch-Loops; nur Snapshot-Ausführung.

## Roles (Multi-Agent)
- **ORCHESTRATOR**: steuert Phasen, stellt Guardrails sicher
- **DISCOVERY_AGENT**: findet existierende Files/Frontdoors (keine Annahmen)
- **DOCS_ENGINEER**: implementiert Archive + Link-Integration + Header/Appendix (minimal)
- **TOKEN_POLICY_AUDITOR**: klassifiziert/remediert Inline-Code Tokens mit “/”
- **QA_GATEKEEPER**: Snapshot-Verifikation (einmalig)
- **EVIDENCE_SCRIBE**: Evidence-Block + Changed-Files + Risk

## Guardrails
- **KEEP EVERYTHING**: Legacy-Text bleibt inhaltlich unverändert; nur additive Meta-Abschnitte (Header/Appendix) und minimale Escape-Fixes.
- **Token Policy**: Inline-Code Tokens mit “/” nur **unescaped**, wenn es **reale Repo-Pfade** sind; sonst policy-konform (z.B. `&#47;`) remediaten.
- **Reference Targets Gate**: Keine neuen Links auf nicht existierende Targets. Targets immer via `test -f`/`test -d` verifizieren.
- **No Watch**: keine laufenden Loops; nur Snapshots.

---

## Phase 0 — Pre-Flight (Repo + Continuation-Guard)
> Wenn dein Terminal mit `>` oder `dquote>` hängt: **Ctrl-C**, dann weiter.

1. `cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd`
2. `pwd`
3. `git rev-parse --show-toplevel`
4. `git status -sb`
5. `git log -1 --oneline`

**Pass-Kriterium:** Repo root korrekt, `main` sauber, kein Continuation-Hang.

---

## Phase 1 — Branch (docs-only)
Branch-Name: `docs/ops-legacy-workflow-notes-reintegration`

1. `git switch main`
2. `git pull --ff-only`
3. `git switch -c docs/ops-legacy-workflow-notes-reintegration`

**Pass-Kriterium:** Branch aktiv, Working Tree clean.

---

## Phase 2 — Discovery (Existenz + Frontdoor)
### A) Legacy Notes finden
Snapshot:
1. `test -f Peak_Trade_WORKFLOW_NOTES.md && echo "FOUND: repo-root legacy notes" || echo "MISSING: repo-root legacy notes"`
2. `find docs -maxdepth 4 -type f -name "*WORKFLOW*NOTES*.md" -print`

### B) Primäre Frontdoor/Index-Datei bestimmen (genau EINE updaten)
Priorität:
1. `WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md`
2. `docs/WORKFLOW_FRONTDOOR.md`
3. `docs/ops/README.md`
4. `docs/README.md`

Snapshot:
1. `test -f WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md && echo "FOUND: overview" || echo "NOTE: overview missing"`
2. `test -f docs/WORKFLOW_FRONTDOOR.md && echo "FOUND: frontdoor" || echo "NOTE: frontdoor missing"`
3. `test -f docs/ops/README.md && echo "FOUND: ops readme" || echo "NOTE: ops readme missing"`
4. `test -f docs/README.md && echo "FOUND: docs readme" || echo "NOTE: docs readme missing"`

**Pass-Kriterium:** 1 canonical “Index/Frontdoor” Ziel ist identifiziert.

---

## Phase 3 — Install (Canonical Archive Location, KEEP EVERYTHING)
Ziel: Legacy Notes als stabiler Docs-Asset unter `docs/ops/archives/` ablegen (oder dort spiegeln), ohne Inhalt zu ändern.

1. `mkdir -p docs/ops/archives`

### Entscheidung
- Wenn `Peak_Trade_WORKFLOW_NOTES.md` im Repo-Root existiert: **beibehalten**, zusätzlich canonical Kopie erstellen:
  - `docs/ops/archives/Peak_Trade_WORKFLOW_NOTES_2025-12-03.md` (Inhalt 1:1)
- Wenn Root-Datei fehlt: canonical Datei direkt unter `docs/ops/archives/Peak_Trade_WORKFLOW_NOTES_2025-12-03.md` anlegen (Inhalt 1:1)

**Wichtig:** Keine Umsortierung, keine Kürzung, keine “Cleanup”-Edits. Nur 1:1 Übernahme.

---

## Phase 4 — Minimal-Header (Additiv, keine Meaning-Änderung)
In der canonical Datei `docs/ops/archives/Peak_Trade_WORKFLOW_NOTES_2025-12-03.md` ganz oben einen kurzen Header-Block ergänzen (additiv).

### Header-Block (einfügen, ohne bestehende Inhalte zu entfernen)
> **Legacy Workflow Notes (Stand: 03.12.2025)**  
> Diese Datei wird **vollständig** beibehalten (KEEP EVERYTHING) und dient als historischer Snapshot + Workflow-Referenz.  
> Aktueller Ops/Runbook-Index: `WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md` (nur als Referenz; Link-Integration erfolgt separat).  
> Hinweis: Inline-Code Tokens mit “/” bleiben nur dann unescaped, wenn sie auf **reale Repo-Pfade** verweisen; andernfalls werden sie policy-konform remediated (z.B. `&#47;`).

**Pass-Kriterium:** Header ist additiv, keine Links auf ungeprüfte Targets.

---

## Phase 5 — Token Policy Audit (Inline-Code Tokens mit “/”)
Ziel: Alle Inline-Code Tokens mit “/” finden, klassifizieren, minimal remediaten.

### A) Kandidaten extrahieren (Snapshot)
1. `rg -n "\`[^`]*\\/[^`]*\`" docs/ops/archives/Peak_Trade_WORKFLOW_NOTES_2025-12-03.md -S`

### B) Klassifikation (pro Token)
- **REAL**: Repo-Pfad existiert → unescaped lassen  
  Verifikation: `test -f <path>` oder `test -d <path>`
- **ILLUSTRATIVE / LEGACY / NICHT (MEHR) REAL**: existiert nicht oder ist offensichtlich exemplarisch → **nur den Slash remediaten**:
  - innerhalb des Inline-Code Tokens `/` → `&#47;`
  - sonst nichts ändern (keine zusätzlichen Zeichen, keine Umformulierungen)

### C) Appendix (Additiv, ganz unten)
Füge am Ende der canonical Datei eine neue Sektion hinzu:

#### Appendix — Token Policy Remediation Notes
- Remediated inline-code token `<old>` → `<new>` (Reason: illustrative / path not present)

**Regel:** Keine Einträge erfinden; nur tatsächliche Änderungen dokumentieren.

---

## Phase 6 — Frontdoor/Index Integration (minimal)
Update genau **EINE** der in Phase 2 gefundenen Index-Dateien.

### Link-Entry (Beispiel)
- `- Legacy Workflow Notes (03.12.2025): docs/ops/archives/Peak_Trade_WORKFLOW_NOTES_2025-12-03.md`

**Wichtig:**
- Als **Markdown-Link** nur dann, wenn Target existiert:
  - `test -f docs/ops/archives/Peak_Trade_WORKFLOW_NOTES_2025-12-03.md`
- Relative Pfade verwenden.
- Keine neuen illustrative Inline-Code Tokens mit “/” einführen.

---

## Phase 7 — Verification Snapshot (ohne Watch)
Snapshot:
1. `git status -sb`
2. `git diff --name-only`
3. `test -f docs/ops/archives/Peak_Trade_WORKFLOW_NOTES_2025-12-03.md && echo "OK: legacy archived" || echo "MISSING: legacy archived"`
4. `test -f docs/ops/runbooks/RUNBOOK_LEGACY_WORKFLOW_NOTES_REINTEGRATION_CURSOR_MULTI_AGENT.md && echo "OK: runbook exists" || echo "MISSING: runbook"`

Optional (wenn vorhanden, Snapshot-only):
- `test -f scripts/ops/pt_docs_gates_snapshot.sh && bash scripts/ops/pt_docs_gates_snapshot.sh --changed || echo "NOTE: snapshot script missing"`

**Pass-Kriterium:** Files existieren, Änderungen sind docs-only, keine offensichtlichen Broken Targets eingeführt.

---

## Phase 8 — Commit / Push / PR (repo-konform)
1. `git add -A`
2. `git commit -m "docs(ops): reintegrate legacy workflow notes into current frontdoor"`
3. `git push -u origin HEAD`

Optional PR:
- `gh pr create --base main --head docs/ops-legacy-workflow-notes-reintegration --title "docs(ops): reintegrate legacy workflow notes into current frontdoor" --body "Keeps legacy workflow notes intact, archives them under docs, adds frontdoor link, and adds a token-policy-safe operator runbook."`

---

## Evidence Block (Copy-Paste für PR / Merge Log)
```text
Legacy Workflow Notes Reintegration — Snapshot
Repo Root: <git rev-parse --show-toplevel>
Branch: <git branch --show-current>
Canonical Archive: docs/ops/archives/Peak_Trade_WORKFLOW_NOTES_2025-12-03.md
Frontdoor/Index Updated: <one file path>
Token Policy Remediations: <N> inline-code tokens remediated (see Appendix in canonical file)
Verification:
- git status -sb: <paste>
- git log -1 --oneline: <paste>
Risk: LOW
```
