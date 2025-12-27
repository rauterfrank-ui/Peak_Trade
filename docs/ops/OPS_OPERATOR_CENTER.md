# Ops Operator Center

**Ein Einstiegspunkt für alle Operator-Workflows.**

---

## 🎯 Überblick

`scripts/ops/ops_center.sh` ist der zentrale Einstiegspunkt für Operator-Tasks im Peak_Trade Repository:
- **Safe-by-default**: Keine destruktiven Aktionen ohne explizite Flags
- **Robust**: Fehlende Tools → Warnungen statt Fehler
- **Konsistent**: Ein Interface für Status, PR-Review, Health-Checks, Merge-Logs

---

## 📦 Quick Start

```bash
# Zentral-Script ausführbar machen (einmalig)
chmod +x scripts/ops/ops_center.sh

# Status anzeigen
scripts/ops/ops_center.sh status

# PR reviewen (safe, kein Merge)
scripts/ops/ops_center.sh pr 263

# Health-Check
scripts/ops/ops_center.sh doctor

# Merge-Log Quick Reference
scripts/ops/ops_center.sh merge-log

# Hilfe
scripts/ops/ops_center.sh help
```

---

## 🔧 Commands

### `status`
Zeigt Repository-Status an:
- Git-Branch & Working-Tree-Status
- Ahead/Behind Remote
- Letzte Commits
- GitHub CLI Authentication-Status (optional)

**Beispiel:**
```bash
scripts/ops/ops_center.sh status
```

**Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Repository Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔹 Branch:
main

🔹 Working Tree:
✅ Clean

🔹 Remote Status:
✅ Up-to-date with origin/main

🔹 Recent Commits:
b521b79 docs(ops): add PR #262 as merge log workflow example (#264)
f8d3ceb docs(ops): add merge log for PR #262 (meta: workflow standard) (#263)
...
```

---

### `status --json` (Machine-Readable Status)

**Version:** v1.1+

Gibt Repository-Status als **valides JSON-Objekt** auf stdout aus. Keine ANSI-Codes, keine Emojis, keine zusätzlichen Zeilen.

**Verwendung:**
- CI/CD-Pipelines
- Monitoring-Tools
- Automatisierte Workflows
- Dashboard-Integration

**Beispiel:**
```bash
scripts/ops/ops_center.sh status --json
```

**Output (Beispiel):**
```json
{
  "repo_root": "/Users/operator/Peak_Trade",
  "branch": "main",
  "working_tree_clean": true,
  "untracked_count": 0,
  "modified_count": 0,
  "ahead": 0,
  "behind": 0,
  "remote": "origin/main",
  "recent_commits": [
    {"sha": "b521b79", "subject": "docs(ops): add PR #262 as merge log workflow example (#264)"},
    {"sha": "f8d3ceb", "subject": "docs(ops): add merge log for PR #262 (meta: workflow standard) (#263)"}
  ],
  "gh_available": true,
  "gh_authenticated": true
}
```

**JSON Schema:**
| Field | Type | Beschreibung |
|-------|------|--------------|
| `repo_root` | string | Absoluter Pfad zum Repository-Root |
| `branch` | string | Aktueller Branch-Name |
| `working_tree_clean` | boolean | `true` wenn keine uncommitted Änderungen |
| `untracked_count` | integer | Anzahl untracked Files |
| `modified_count` | integer | Anzahl modified/staged Files |
| `ahead` | integer | Commits ahead von Remote |
| `behind` | integer | Commits behind von Remote |
| `remote` | string\|null | Upstream-Branch (z.B. `"origin/main"`) oder `null` |
| `recent_commits` | array | Letzte 5 Commits (je `{sha, subject}`) |
| `gh_available` | boolean | `true` wenn `gh` CLI installiert |
| `gh_authenticated` | boolean\|null | `true`/`false`/`null` (wenn `gh` nicht verfügbar) |

**Robustheit:**
- **Ohne `gh` CLI:** `"gh_available": false`, `"gh_authenticated": null`
- **Außerhalb git repo:** Exit 1 + `{"error": "not a git repository"}` auf stderr
- **Kein Remote konfiguriert:** `"remote": null`, `"ahead": 0`, `"behind": 0`

**Beispiel-Integration:**
```bash
# Parse mit jq
STATUS=$(scripts/ops/ops_center.sh status --json)
BRANCH=$(echo "$STATUS" | jq -r '.branch')
CLEAN=$(echo "$STATUS" | jq -r '.working_tree_clean')

if [[ "$CLEAN" == "true" ]]; then
  echo "✅ Working tree clean on branch: $BRANCH"
fi

# Python
import json, subprocess
result = subprocess.run(["scripts/ops/ops_center.sh", "status", "--json"],
                       capture_output=True, text=True)
status = json.loads(result.stdout)
print(f"Branch: {status['branch']}, Clean: {status['working_tree_clean']}")
```

---

### `pr <NUM>`
Ruft `review_and_merge_pr.sh` im **Review-Only-Modus** auf.

**Safe-by-default:**
- Kein Merge ohne explizites `--merge` Flag
- Zeigt PR-Summary, Diff, Checks

**Beispiel:**
```bash
scripts/ops/ops_center.sh pr 263
```

**Für Merge:**
Nutze `review_and_merge_pr.sh` direkt mit `--merge` Flag:
```bash
scripts/ops/review_and_merge_pr.sh --pr 263 --merge --update-main
```

---

### `merge-log`
Zeigt Quick-Links zu Merge-Log-Dokumentation & Templates:
- Workflow: `docs/ops/MERGE_LOG_WORKFLOW.md`
- Template: `templates/ops/merge_log_template.md`
- Existierende Merge-Logs: `docs/ops/PR_*_MERGE_LOG.md`

**Beispiel:**
```bash
scripts/ops/ops_center.sh merge-log
```

**Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Merge Log Quick Reference
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔹 Workflow:
   docs/ops/MERGE_LOG_WORKFLOW.md

🔹 Template:
   templates/ops/merge_log_template.md

🔹 Examples:
   - PR_262_MERGE_LOG.md
   - PR_250_MERGE_LOG.md
   ...
```

---

### `doctor`
Ruft `ops_doctor.sh` auf (vollständiger Repository-Health-Check).

**Features:**
- 9 Health-Checks (Git, Dependencies, Config, Docs, Tests, CI/CD)
- JSON- und Human-Readable-Output
- Exit-Codes für CI/CD

**Beispiel:**
```bash
scripts/ops/ops_center.sh doctor

# JSON-Output
scripts/ops/ops_center.sh doctor --json

# Spezifische Checks
scripts/ops/ops_center.sh doctor --check repo.git_root --check deps.uv_lock
```

Siehe auch: [OPS_DOCTOR_README.md](OPS_DOCTOR_README.md)

---

### `help`
Zeigt Hilfe & Command-Übersicht.

```bash
scripts/ops/ops_center.sh help
```

---

### `selftest` (Smoke Tests)

**Version:** v1.1+

Führt integrierte Smoke-Tests für `ops_center.sh` selbst aus. Validiert kritische Funktionalität ohne externe Dependencies (abgesehen von Python3 für JSON-Validierung).

**Tests:**
1. `ops_center.sh help` → exit 0
2. `ops_center.sh status` → exit 0
3. `ops_center.sh status --json` → exit 0 + valides JSON
4. `pytest tests/ops/test_ops_center_smoke.py` (wenn verfügbar)

**Beispiel:**
```bash
scripts/ops/ops_center.sh selftest
```

**Output (Erfolg):**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧪 Ops Center Selftest
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔹 Test: ops_center.sh help
   ✅ PASS
🔹 Test: ops_center.sh status
   ✅ PASS
🔹 Test: ops_center.sh status --json
   ✅ PASS (valid JSON)
🔹 Test: pytest smoke tests
   ✅ PASS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All tests passed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Output (Fehler):**
```
🔹 Test: ops_center.sh status --json
   ❌ FAIL (invalid JSON)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 1 test(s) failed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Exit Codes:**
- `0` → Alle Tests erfolgreich
- `1` → Mindestens ein Test fehlgeschlagen

**Verwendung:**
- **Pre-deployment Check:** Validierung vor Rollout
- **CI/CD:** Automatisierte Regression-Tests
- **Debugging:** Schnelle Diagnose bei Problemen
- **Post-upgrade:** Verification nach Upgrade (z.B. v1.0 → v1.1)

**Robustheit:**
- Funktioniert auch ohne `pytest` (skips Test 4)
- Funktioniert auch ohne `uv` (fallback auf `pytest`)
- Keine destruktiven Aktionen (read-only checks)

---

## ⚠️ Was macht es NICHT?

**Safe-by-default Design:**
- ❌ **Kein automatischer Merge** (nur Review-Modus bei `pr <NUM>`)
- ❌ **Keine Branch-Deletions**
- ❌ **Keine git push/force-push**
- ❌ **Keine destruktiven Änderungen**

**Für Merge-Aktionen:**
Nutze die entsprechenden Tools direkt mit expliziten Flags:
- `review_and_merge_pr.sh --merge`
- `pr_review_merge_workflow.sh`

---

## 🔍 Troubleshooting

### `gh` nicht installiert
**Symptom:** `⚠️ gh not installed (optional)`

**Lösung:**
```bash
# macOS
brew install gh

# Linux
# siehe: https://cli.github.com/manual/installation

# Authenticate
gh auth login
```

**Hinweis:** `ops_center.sh status` funktioniert auch ohne `gh` (reduzierte Features).

---

### `review_and_merge_pr.sh` nicht gefunden
**Symptom:** `⚠️ Script not found or not executable: scripts/ops/review_and_merge_pr.sh`

**Lösung:**
```bash
# Existiert das Script?
ls -la scripts/ops/review_and_merge_pr.sh

# Ausführbar machen
chmod +x scripts/ops/review_and_merge_pr.sh
```

Siehe: [PR_MANAGEMENT_TOOLKIT.md](PR_MANAGEMENT_TOOLKIT.md)

---

### `ops_doctor.sh` nicht gefunden
**Symptom:** `⚠️ Script not found or not executable: scripts/ops/ops_doctor.sh`

**Lösung:**
```bash
# Existiert das Script?
ls -la scripts/ops/ops_doctor.sh

# Ausführbar machen
chmod +x scripts/ops/ops_doctor.sh
```

Siehe: [OPS_DOCTOR_README.md](OPS_DOCTOR_README.md)

---

### Git fetch fails (offline)
**Symptom:** `⚠️ Could not fetch (offline?)`

**Hinweis:** `ops_center.sh status` zeigt trotzdem lokalen Status (degraded mode).

---

## 📚 Verwandte Dokumentation

- **PR Management**: [PR_MANAGEMENT_TOOLKIT.md](PR_MANAGEMENT_TOOLKIT.md)
- **Ops Doctor**: [OPS_DOCTOR_README.md](OPS_DOCTOR_README.md)
- **Merge Logs**: [MERGE_LOG_WORKFLOW.md](MERGE_LOG_WORKFLOW.md)
- **Ops Tools Index**: [README.md](README.md)

---

## 🎯 Operator Workflow (Empfohlen)

```bash
# 0) Selftest (einmalig nach Upgrade/Installation)
scripts/ops/ops_center.sh selftest

# 1) Status-Check (vor jedem Task)
scripts/ops/ops_center.sh status

# 1b) Machine-readable Status (für Automation)
scripts/ops/ops_center.sh status --json | jq '.branch'

# 2) PR reviewen
scripts/ops/ops_center.sh pr 265

# 3) Health-Check (bei Bedarf)
scripts/ops/ops_center.sh doctor

# 4) Merge-Log erstellen (nach Merge)
scripts/ops/ops_center.sh merge-log  # → Links anzeigen
scripts/ops/create_and_open_merge_log_pr.sh  # → Workflow ausführen
```

---

## ✅ Design-Prinzipien

1. **Safe-by-default**: Keine destruktiven Aktionen ohne explizite Flags
2. **Robust**: Fehlende Tools → Warnungen (exit 0), keine harten Fehler
3. **Consistent**: Ein Interface für häufige Tasks
4. **Discoverable**: Hilfreiche Fehlermeldungen + Links auf Doku
5. **Testable**: Smoke-Tests für alle Commands

---

## 🧪 Testing

```bash
# Integrierter Selftest (empfohlen)
scripts/ops/ops_center.sh selftest

# Externe Smoke-Tests
pytest -q tests/ops/test_ops_center_smoke.py

# Manuell
scripts/ops/ops_center.sh help
scripts/ops/ops_center.sh status
scripts/ops/ops_center.sh status --json | jq
```

---

**Siehe auch:**
- [README.md](README.md) — Ops Tools Index
- [PR_MANAGEMENT_QUICKSTART.md](PR_MANAGEMENT_QUICKSTART.md) — PR Management Quick Start
