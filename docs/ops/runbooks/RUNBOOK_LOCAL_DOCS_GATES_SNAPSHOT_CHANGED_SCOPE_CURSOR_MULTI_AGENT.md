# RUNBOOK: Local Docs Gates Snapshot (Changed Scope) — Cursor Multi-Agent

## Purpose
Dieses Runbook beschreibt einen **wiederholbaren Snapshot-Ablauf** für Operatoren, um lokal (oder in CI-ähnlicher Umgebung) die Docs-Gates **für den geänderten Scope** auszuführen und das Ergebnis als **prüfbaren Nachweis** zu sichern.

## When to Use
- Vor PR-Erstellung (docs-only oder mixed) zur schnellen Gate-Validierung
- Nach einem kleinen Docs-Fix, um Reference Targets / Token Policy / Diff Guard früh zu erkennen
- Als “Operator Evidence” für Review und Merge Logs

## Inputs
- Working tree mit geplanten Änderungen
- Optional: ein Base-Ref (typisch `origin&#47;main`) für Changed-Scope Diff

## Outputs
- Konsistenter “Local Docs Gates Snapshot” Block (Commands + Ergebnis)
- Optional: Attachments/Logs lokal gespeichert (nur wenn bereits Repo-konform vorgesehen)

## Non-Goals
- Keine Watch-Loops
- Keine automatische Reparatur (Fixes sind separater Schritt / separate PR)

---

## Phase A — Pre-Flight (Repo + Continuation-Guard)

Wenn dein Terminal mit `>` oder `dquote>` hängt: **Ctrl-C**.

```bash
cd /Users/frnkhrz/Peak_Trade 2>/dev/null || cd "$HOME/Peak_Trade" 2>/dev/null || pwd
pwd
git rev-parse --show-toplevel
git status -sb
git log -1 --oneline
```

**Pass-Kriterium:** Repo root korrekt, Branch sauber sichtbar, kein Continuation-Hang.

---

## Phase B — Changed-Scope bestimmen (Snapshot)

### Option B1 (Standard): Diff gegen origin/main

```bash
git fetch origin --prune
git diff --name-only origin/main...HEAD
```

### Option B2: Staged-only (wenn du bewusst nur staged prüfen willst)

```bash
git diff --name-only --cached
```

**Hinweis:** Paths sind Output; keine Pfade als illustrative Inline-Code-Beispiele erfinden.

---

## Phase C — Local Docs Gates Snapshot (Changed Scope)

Dieses Repo stellt ein Operator-Skript bereit, das die Docs-Gates in einem Snapshot bündelt.

```bash
bash scripts/ops/pt_docs_gates_snapshot.sh --changed
```

Wenn das Skript zusätzliche Flags dokumentiert (z.B. base-ref), nutze nur bereits vorhandene Optionen:

```bash
bash scripts/ops/pt_docs_gates_snapshot.sh --help
```

**Pass-Kriterium:** Snapshot läuft durch, Exit-Code und Gate-Resultate sind klar ersichtlich.

---

## Phase D — Evidence Block (zum Copy-Paste in PR / Merge Log)

Paste den Block **unverändert** in PR Description oder Merge Log.

```text
Local Docs Gates Snapshot (Changed Scope)
Repo Root: <paste git rev-parse --show-toplevel>
Branch: <paste git branch --show-current>
Base Ref: origin&#47;main
Changed Files: <paste output von git diff --name-only origin&#47;main...HEAD oder staged-only liste>
Snapshot Command: bash scripts/ops/pt_docs_gates_snapshot.sh --changed
Result: <PASS/FAIL + kurze gate-namen>
Notes: <optional, max 2 zeilen>
Risk: <LOW/MED/HIGH>
```
