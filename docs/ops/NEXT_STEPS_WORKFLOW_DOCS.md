# Next Steps – Workflow Scripts Documentation PR

## 📋 Status

✅ **Branch erstellt:** `docs&sol;ops-workflow-scripts-docs` (planned directory)   <!-- pt:ref-target-ignore -->
✅ **Commits:** 2 Commits (Dokumentation + Index/Changelog-Updates)  
⏳ **Push:** Noch nicht gepusht (SSH-Key-Probleme im Sandbox)  
⏳ **PR:** Noch nicht erstellt

---

## 🚀 Nächste Schritte

### Option A: Automatisiertes Script (empfohlen)

```bash
# Script ausführen (macht alles: Push + PR + Merge)
bash scripts/workflows/finalize_workflow_docs_pr.sh

# Script macht:
# 1. Branch pushen
# 2. PR erstellen
# 3. CI-Checks verfolgen
# 4. Interaktive Bestätigung
# 5. Merge (squash) + Branch löschen
# 6. main aktualisieren
```

### Option B: Manuelle Schritte

```bash
# 1. Branch pushen
git push -u origin docs&#47;ops-workflow-scripts-docs

# 2. PR erstellen
gh pr create \
  --title "docs(ops): workflow scripts documentation + automation infrastructure" \
  --body "Adds comprehensive documentation for ops automation scripts." \
  --base main

# 3. CI-Checks verfolgen
gh pr checks --watch

# 4. Merge (nach grünen Checks)
gh pr merge --squash --delete-branch

# 5. main aktualisieren
git checkout main
git pull --ff-only
```

---

## 📄 Was erstellt wurde

### Neue Dateien

1. **docs/ops/WORKFLOW_SCRIPTS.md** (353 Zeilen)
   - Komplette Dokumentation der Ops-Automation-Scripts
   - Verwendung von `post_merge_workflow_pr203.sh`
   - Verwendung von `quick_pr_merge.sh`
   - Verwendung von `post_merge_workflow.sh`
   - Workflow-Patterns, Troubleshooting, Best Practices

2. **scripts/workflows/post_merge_workflow_pr203.sh**
   - All-in-One: Docs erstellen + PR-Flow
   - Automatisiert PR #203 Merge-Log-Workflow

3. **scripts/workflows/quick_pr_merge.sh**
   - Quick PR-Merge (wenn Docs bereits committet sind)
   - Generisch verwendbar für beliebige PRs

4. **scripts/workflows/finalize_workflow_docs_pr.sh**
   - Finalisiert diesen Workflow-Docs-PR
   - Push + PR + Merge in einem Rutsch

### Aktualisierte Dateien

1. **docs/ops/README.md**
   - Link zu WORKFLOW_SCRIPTS.md im Guides-Abschnitt

2. **docs/PEAK_TRADE_STATUS_OVERVIEW.md**
   - Changelog-Eintrag für Workflow Scripts Doku

---

## 📊 Commits auf Branch

```
139c2cb docs(ops): update index + changelog for workflow scripts
324c6d0 docs(ops): add workflow scripts documentation
```

---

## ✨ Nach dem Merge

Nach erfolgreichem Merge kannst du die Scripts verwenden:

### PR #203 Merge-Log (All-in-One)
```bash
bash scripts/workflows/post_merge_workflow_pr203.sh
# → Erstellt Docs + PR + Merge für PR #203
```

### Beliebiger PR (Quick-Merge)
```bash
# Auf deinem Feature-Branch
bash scripts/workflows/quick_pr_merge.sh
# → PR erstellen + Merge (Docs bereits vorhanden)
```

### Post-Merge Verification
```bash
# Nach jedem Merge
bash scripts/workflows/post_merge_workflow.sh
# → Repo-Hygiene + Tests + Optional: Stage1-Monitoring
```

---

## 🔍 Troubleshooting

### "SSH-Key-Probleme beim Push"

```bash
# Check SSH-Key
ssh -T git@github.com

# Falls nicht funktioniert: HTTPS verwenden
git remote set-url origin https://github.com/user/Peak_Trade.git
git push -u origin docs&#47;ops-workflow-scripts-docs
```

### "gh: command not found"

```bash
# macOS
brew install gh

# Dann authentifizieren
gh auth login
```

---

## 📚 Dokumentation

Die vollständige Dokumentation ist jetzt verfügbar unter:
- **docs/ops/WORKFLOW_SCRIPTS.md** – Haupt-Dokumentation
- **docs/ops/README.md** – Ops-Index (Guides-Abschnitt)

---

**Nächster Schritt:** Führe `bash scripts/workflows/finalize_workflow_docs_pr.sh` aus! 🚀
