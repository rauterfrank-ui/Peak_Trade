# Merge Log Workflow — Standard Process

**Ziel:** Jeder Merge-Log wird als eigener PR erstellt (Review + CI + Audit-Trail).  
**Warum:** Konsistenz, Nachvollziehbarkeit, kein "Direct Push" auf main, saubere Historie.

---

## ⚡ Quick Start — One-Block Workflow

Für erfahrene Operators: Kompletter Workflow in einem Block.

**Du editierst nur zwei Variablen:** `PR` und `TOPIC`

```bash
set -euo pipefail
cd ~/Peak_Trade

# ========================================
# EDIT THESE TWO VARIABLES
# ========================================
PR=261
TOPIC="stash triage helper"
# ========================================

git checkout main
git pull --ff-only
git checkout -b "docs/merge-log-$PR"

cat > "docs/ops/PR_${PR}_MERGE_LOG.md" <<EOF
# PR #${PR} — Merge Log

## Summary
PR #${PR} wurde gemerged. Thema: ${TOPIC}.

- Squash-Commit: **<hash>**
- Änderungen: **N Dateien**, **+X / -Y**
- Ziel: <kurze-beschreibung>

## Why
- Warum diese Änderung notwendig ist.
- Problem X wurde gelöst.

## Changes
### New
- \`<file>\` — <beschreibung>

### Updated
- \`<file>\` — <beschreibung>

## Verification
### CI (X/Y passed)
- ✅ <check-name>

### Post-Merge Checks (lokal)
- \`<command>\` ✅

## Risk
<Niedrig|Mittel|Hoch>.
- Einschätzung + Mitigations.

## Operator How-To
\\\`\\\`\\\`bash
# wichtigste Operator-Kommandos
\\\`\\\`\\\`

## References
- PR: #${PR}
- Commit: <hash>
EOF

# README-Link setzen (öffnet Editor; alternativ automatisieren mit sed/rg)
\${EDITOR:-vi} docs/ops/README.md

git add "docs/ops/PR_${PR}_MERGE_LOG.md" docs/ops/README.md
git commit -m "docs(ops): add compact merge log for PR #${PR}"
git push -u origin "docs/merge-log-$PR"

gh pr create \
  --title "docs(ops): add merge log for PR #${PR} (${TOPIC})" \
  --body "Adds compact merge log for PR #${PR} and links it from ops README." \
  --label ops
```

**Hinweis:** Die generierte Datei ist ein Minimal-Template. Für vollständige Merge-Logs siehe detaillierte Workflow-Schritte unten.

---

## 📋 Workflow-Schritte (detailliert)

### 1) Datei anlegen (kompakt)

**Datei:** `docs/ops/PR_<NUM>_MERGE_LOG.md`

**Inhalt-Struktur:**
- **Summary** — PR-Nummer, Commit, Änderungen, Ziel
- **Why** — Motivation und Nutzen
- **Changes** — Detaillierte Auflistung (New + Updated)
- **Verification** — CI-Status + Post-Merge Checks
- **Risk** — Risikoeinschätzung
- **Operator How-To** — Praxis-Beispiele
- PR #262 — merge-log workflow standard + template (Meta-Beispiel): `docs/ops/PR_262_MERGE_LOG.md`
- **Follow-Up Actions** — Optional nächste Schritte
- **References** — Links zu Policy, Tool, Tests

**Verlinkung:**
- In `docs/ops/README.md` verlinken (Merge-Logs Sektion)
- Format: `- [PR #<NUM>](PR_<NUM>_MERGE_LOG.md) — <title> (merged YYYY-MM-DD)`

---

### 2) Branch/Commit/PR (Safe Naming)

**Branch:**
```bash
docs/merge-log-<NUM>
```

**Commit Message:**
```bash
docs(ops): add compact merge log for PR #<NUM>
```

**PR Title:**
```bash
docs(ops): add merge log for PR #<NUM> (<topic>)
```

> ⚠️ **Hinweis:** Vermeide Titel/Commits im exakten Pattern `docs(ops): add PR #<NUM> merge log` (falls Depth/Pattern-Guards aktiv sind).

---

### 3) Merge

- **Standard:** Squash + Delete Branch
- **CI:** Muss grün sein (Audit ggf. nur wenn policy erlaubt)
- **Tool:** `scripts/ops/review_and_merge_pr.sh` (empfohlen)

---

### 4) Operator Quick Commands

```bash
# Variables
PR=<NUM>
TOPIC="<short-topic>"  # z.B. "stash-triage"

# 1) Branch erstellen
git checkout main && git pull --ff-only
git checkout -b docs/merge-log-$PR

# 2) Merge-Log erstellen
cat > docs/ops/PR_${PR}_MERGE_LOG.md <<'EOF'
# PR #<NUM> — Merge Log

**Title:** <PR-title>
**Merged:** YYYY-MM-DD
**Commit:** `<commit-hash>`
**Author:** <author>
**PR URL:** https://github.com/rauterfrank-ui/Peak_Trade/pull/<NUM>

---

## Summary

PR #<NUM> **<title>** wurde erfolgreich gemerged.

- Squash-Commit: **<hash>**
- Änderungen: **N Dateien**, **+X / -Y**
- Ziel: <kurze-beschreibung>

---

## Why

<motivation-und-kontext>

---

## Changes

### New

- `<file>`
  - <beschreibung>

### Updated

- `<file>`
  - <beschreibung>

---

## Verification

### CI (X/Y passed)

**Passed:**
- ✅ <check-name>

**Allowed fail (optional):**
- ⚠️ <check-name> — <reason>

### Post-Merge Checks (lokal)

- `<command>` ✅
- Working directory clean ✅

---

## Risk

<risikoeinschätzung>

---

## Operator How-To

\`\`\`bash
# Beispiele für Operator
<commands>
\`\`\`

---

## Follow-Up Actions

- [ ] Optional: <action>

---

## References

- **Docs:** [<link>](<path>)
- **Tool:** [<link>](<path>)

---

**Merge Method:** Squash
**Branch Deleted:** ✅ Yes
**Local Main Updated:** ✅ Yes
EOF

# 3) README.md aktualisieren (Merge-Logs Sektion)
# Füge neue Zeile an erster Stelle der Merge-Logs Sektion ein:
# - [PR #${PR}](PR_${PR}_MERGE_LOG.md) — <title> (merged YYYY-MM-DD)

# 4) Stage + Commit
git add docs/ops/PR_${PR}_MERGE_LOG.md docs/ops/README.md
git commit -m "docs(ops): add compact merge log for PR #${PR}"

# 5) Push + PR erstellen
git push -u origin docs/merge-log-$PR
gh pr create \
  --title "docs(ops): add merge log for PR #${PR} (${TOPIC})" \
  --body "Adds compact merge log and README link for PR #${PR}." \
  --label ops

# 6) Watch CI + Merge
gh pr checks --watch
scripts/ops/review_and_merge_pr.sh --pr <NEW_PR> --merge --method squash --update-main
```

---

## 📚 Template

Eine Merge-Log-Template-Datei findest du in: `templates/ops/merge_log_template.md`

---

## 🔍 Beispiele

- [PR #261](PR_261_MERGE_LOG.md) — Stash Triage Helper
- [PR #250](PR_250_MERGE_LOG.md) — Ops Doctor
- [PR #237](PR_237_MERGE_LOG.md) — Bash Run Helpers
- [PR #123](PR_123_MERGE_LOG.md) — Core Architecture & Workflow Documentation

---

## ⚠️ Anti-Patterns (zu vermeiden)

### ❌ Direct Push auf main
```bash
# NICHT EMPFOHLEN
git checkout main
git add docs/ops/PR_XXX_MERGE_LOG.md
git commit -m "add merge log"
git push
```

**Warum schlecht:**
- Kein Review-Prozess
- Keine CI-Validierung
- Keine Audit-Trail (kein eigener PR)

### ❌ Pattern-Konflikte
```bash
# VERMEIDE (wenn Pattern-Guards aktiv)
git commit -m "docs(ops): add PR #261 merge log"
```

**Besser:**
```bash
git commit -m "docs(ops): add compact merge log for PR #261"
```

---

## 🎯 Best Practices

1. **Konsistente Struktur** — Verwende Template für alle Merge-Logs
2. **Zeitnah** — Erstelle Merge-Log direkt nach PR-Merge
3. **PR-basiert** — Immer über eigenen PR (kein Direct Push)
4. **Verlinkung** — README.md immer aktualisieren
5. **Verifikation** — CI + Post-Merge Checks dokumentieren
6. **Risk Assessment** — Immer Risk-Sektion ausfüllen

---

## 🤖 Automation (optional)

Für künftige Verbesserungen:

```bash
# Helper-Skript (nicht implementiert)
scripts/ops/create_merge_log_pr.sh --pr 261 --topic "stash-triage"
```

Würde automatisch:
- Branch erstellen
- Merge-Log-Template mit PR-Infos füllen
- README.md aktualisieren
- Commit + Push + PR erstellen

---

**Version:** 1.0.0  
**Letzte Aktualisierung:** 2025-12-23  
**Maintainer:** Peak_Trade Ops Team
