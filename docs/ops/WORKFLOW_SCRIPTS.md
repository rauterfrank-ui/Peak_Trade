# Ops – Workflow Scripts

Diese Datei dokumentiert die Peak_Trade Ops-Automations-Skripte für **Post-Merge Doku** und **PR Merge Automation**.

---

## Voraussetzungen

- `git` (Repo lokal vorhanden)
- `gh` (GitHub CLI) installiert & authentifiziert:
  ```bash
  gh auth status
  
  # Falls nicht authentifiziert:
  gh auth login
  ```
- Workspace: `~/Peak_Trade`

---

## Übersicht

| Script | Zweck | Use-Case |
|--------|-------|----------|
| `scripts/post_merge_workflow_pr203.sh` | All-in-One: Docs erstellen + PR-Flow | PR #203 Merge-Log vollautomatisch |
| `scripts/quick_pr_merge.sh` | Quick PR-Merge | Wenn Docs bereits committet sind |
| `scripts/post_merge_workflow.sh` | Generisches Post-Merge Verification | Hygiene + Verification nach jedem Merge |

---

## 1. Post-Merge Workflow PR #203 (All-in-One)

**Script:** `scripts/post_merge_workflow_pr203.sh`

### Was es macht

1. **Branch-Setup:**
   - Checkout `main` + Pull
   - Erstellt Branch `docs/ops-pr203-merge-log`

2. **Dokumentation erstellen:**
   - `docs/ops/PR_203_MERGE_LOG.md` – Umfassender Merge Log
   - `docs/ops/README.md` – Index-Update (PR #203 hinzufügen)
   - `docs/PEAK_TRADE_STATUS_OVERVIEW.md` – Changelog-Eintrag

3. **Git + PR-Flow:**
   - Commit mit strukturierter Message
   - Push Branch
   - PR erstellen via `gh pr create`
   - CI-Checks verfolgen (`gh pr checks --watch`)
   - **Interaktive Bestätigung** vor Merge
   - Merge (squash) + Branch löschen
   - `main` aktualisieren

### Verwendung

```bash
# Einfach ausführen
bash scripts/post_merge_workflow_pr203.sh

# Ablauf:
# 1. Script erstellt Dateien + committet + pushed
# 2. PR wird automatisch erstellt
# 3. CI-Checks laufen (live verfolgen oder Ctrl+C)
# 4. Script wartet auf ENTER-Taste
# 5. Merge + Branch-Cleanup
# 6. main wird aktualisiert
```

### Output-Beispiel

```
==> Update main
Already on 'main'
Already up to date.
==> Create branch: docs/ops-pr203-merge-log
Switched to a new branch 'docs/ops-pr203-merge-log'
==> Write merge log: docs/ops/PR_203_MERGE_LOG.md
==> Update docs/ops/README.md (add PR #203)
==> Update docs/PEAK_TRADE_STATUS_OVERVIEW.md (Changelog)
==> Commit
[docs/ops-pr203-merge-log abc1234] docs(ops): add PR #203 merge log + update index
 3 files changed, 120 insertions(+)
==> Push branch
...
==> Creating PR
https://github.com/user/Peak_Trade/pull/205
==> Watching PR checks
✓ lint (13s)
✓ audit (2m11s)
✓ tests (3m54s)

Press ENTER to merge PR...
==> Merging PR (squash + delete branch)
✓ Merged and deleted branch
==> Updating main
✅ PR docs merged + main up-to-date
abc1234 docs(ops): add PR #203 merge log + update index
```

### Anpassung für andere PRs

Für andere PR-Nummern:

1. **Kopiere das Script:**
   ```bash
   cp scripts/post_merge_workflow_pr203.sh scripts/post_merge_workflow_pr999.sh
   ```

2. **Suche & Ersetze:**
   - `203` → `999`
   - Branch-Name: `docs/ops-pr203-merge-log` → `docs/ops-pr999-merge-log`
   - PR-Titel/Body anpassen

3. **Merge Log Inhalt:**
   - Template in `cat > docs/ops/PR_999_MERGE_LOG.md` anpassen

---

## 2. Quick PR Merge

**Script:** `scripts/quick_pr_merge.sh`

### Wann nutzen

- Docs-Dateien sind bereits erstellt + committet
- Branch ist bereits gepusht
- Nur noch PR-Erstellung + Merge fehlen

### Verwendung

```bash
# Auf deinem Feature-Branch ausführen
git checkout docs/ops-pr203-merge-log

# Script ausführen
bash scripts/quick_pr_merge.sh

# Script macht:
# 1. Safety-Check (nicht auf main)
# 2. PR erstellen
# 3. CI-Checks verfolgen
# 4. Interaktive Bestätigung
# 5. Merge + Branch löschen
# 6. main aktualisieren
```

### Safety-Checks

- Script prüft, ob aktueller Branch ≠ `main`
- Verhindert versehentliches Ausführen auf `main`

---

## 3. Generisches Post-Merge Verification

**Script:** `scripts/post_merge_workflow.sh`

### Zweck

Hygiene + Verification nach **jedem** Merge (nicht nur Docs-PRs).

### Was es macht

1. **Repo-Hygiene:**
   - `git fetch --prune`
   - Branch-Cleanup
   - Status-Checks

2. **Core-Verification:**
   - `ruff check` (Linting)
   - `pytest -q` (Core-Tests ohne Web/Viz)

3. **Optional: Web-Stack:**
   - Auto-Detect Web-Extra aus `pyproject.toml`
   - Installiert Web-Extra falls vorhanden
   - Re-run pytest mit Web-Tests

4. **Optional: Stage1-Monitoring:**
   - Führt Stage1-Snapshot aus (falls vorhanden)
   - Führt Trend-Reports aus (falls vorhanden)

### Verwendung

```bash
# Nach jedem Merge auf main ausführen
bash scripts/post_merge_workflow.sh
```

### Hinweise

- **Viz-Tests (Matplotlib):** Script erkennt automatisch, ob `viz` Extra verfügbar ist
  - Falls ja: Installiert via `uv sync --extra viz`
  - Falls nein: Nur Core-Tests (Viz-Tests werden geskippt)
- **Web-Tests:** Analog für `web` Extra (auto-detection via pyproject.toml)

---

## Workflow-Patterns

### Pattern 1: "PR Merge + Docs in einem Rutsch"

```bash
# Für PR #203 (All-in-One)
bash scripts/post_merge_workflow_pr203.sh

# → Erstellt Docs + PR + Merge + main update
```

### Pattern 2: "Docs manuell, dann Quick-Merge"

```bash
# 1. Branch erstellen
git checkout -b docs/ops-pr999-merge-log

# 2. Docs manuell erstellen/editieren
vim docs/ops/PR_999_MERGE_LOG.md
vim docs/ops/README.md
vim docs/PEAK_TRADE_STATUS_OVERVIEW.md

# 3. Commit + Push
git add docs/
git commit -m "docs(ops): PR #999 merge log"
git push -u origin docs/ops-pr999-merge-log

# 4. Quick-Merge
bash scripts/quick_pr_merge.sh
```

### Pattern 3: "Nach Merge: Hygiene + Verification"

```bash
# Nach erfolgreichem Merge (egal welcher PR)
bash scripts/post_merge_workflow.sh

# → Prüft Repo + Tests + Optional: Stage1-Monitoring
```

---

## Troubleshooting

### "gh: command not found"

```bash
# macOS
brew install gh

# Linux
# Siehe: https://github.com/cli/cli#installation
```

### "gh: not authenticated"

```bash
gh auth login
# → Follow prompts (GitHub.com, HTTPS/SSH, Browser)
```

### "CI-Checks schlagen fehl"

- Script wartet bei `gh pr checks --watch`
- Drücke Ctrl+C zum Überspringen
- Prüfe CI-Logs auf GitHub
- Fixe Fehler lokal → Push → Checks laufen erneut

### "Merge schlägt fehl (Conflicts)"

```bash
# Auf Feature-Branch
git fetch origin main
git rebase origin/main

# Conflicts auflösen
git add .
git rebase --continue

# Force-Push (Branch ist bereits remote)
git push --force-with-lease

# Script erneut ausführen
bash scripts/quick_pr_merge.sh
```

### "Script stoppt bei read -p"

- Das ist gewollt: **Interaktive Bestätigung** vor Merge
- Prüfe CI-Ergebnisse + PR-Inhalt
- Drücke ENTER zum Fortfahren
- Oder Ctrl+C zum Abbrechen (PR bleibt offen)

---

## CI Smoke Guard

Peak_Trade enthält einen minimalen Pytest-Smoke-Test, der sicherstellt:
- Die 4 Ops-Workflow-Scripts existieren
- Ihre Bash-Syntax korrekt ist (`bash -n` Check)
- CI-sicher: Bei fehlendem `bash` wird der Test sauber übersprungen

**Wichtig:** Der Test führt die Scripts **nicht aus** – kein `gh`, keine Auth, keine Side-Effects. Nur Syntaxprüfung.

### Lokal ausführen

```bash
# Targeted Test (nur Workflow-Scripts)
uv run pytest -q tests/test_ops_workflow_scripts_syntax.py

# Oder im Full-Suite enthalten
uv run pytest -q
```

### Geprüfte Scripts

- `scripts/post_merge_workflow_pr203.sh`
- `scripts/quick_pr_merge.sh`
- `scripts/post_merge_workflow.sh`
- `scripts/finalize_workflow_docs_pr.sh`

---

## Best Practices

### 1. Immer auf aktuellem main starten

```bash
git checkout main
git pull --ff-only
# → Dann Script ausführen
```

### 2. CI-Checks immer prüfen

```bash
# Nicht blind mergen!
# Warte auf grüne Checks oder prüfe sie manuell:
gh pr checks
```

### 3. Merge Logs konsistent halten

- Nutze Template aus `docs/ops/PR_203_MERGE_LOG.md`
- Struktur: Problem/Motivation → Änderungen → CI → Nutzung → Breaking Changes → Follow-ups
- Metadaten: Status, Merge Commit, Branch, Intent

### 4. Changelog-Einträge

- Format: `YYYY-MM-DD: PR #NNN – Kurzbeschreibung`
- Immer am Ende von `docs/PEAK_TRADE_STATUS_OVERVIEW.md` anhängen

---

## Referenz: Script-Locations

```
scripts/
├── post_merge_workflow.sh           # Generisches Post-Merge Verification
├── post_merge_workflow_pr203.sh     # PR #203 All-in-One
└── quick_pr_merge.sh                # Quick PR-Merge (Docs bereits vorhanden)

docs/ops/
├── PR_201_MERGE_LOG.md              # Beispiel: Web-UI tests optional
├── PR_203_MERGE_LOG.md              # Beispiel: Matplotlib/Viz tests optional
├── README.md                        # Ops-Index (alle PRs)
└── WORKFLOW_SCRIPTS.md              # Diese Datei
```

---

## Siehe auch

- **Ops-Index:** `docs/ops/README.md` – Zentrale Übersicht aller Ops-Dokumente
- **Labeling Guide:** `docs/ops/LABELING_GUIDE.md` – PR-Labels & Conventions
- **Audit System:** `docs/ops/README.md` Abschnitt "Audit System" – CI-Audit-Workflow

---

**Erstellt:** 2025-12-21  
**Version:** 1.0  
**Maintainer:** Peak_Trade Ops Team

