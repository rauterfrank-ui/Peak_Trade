# PR Management Toolkit – Quick Start

Schnelleinstieg für Operatoren.

---

## 📌 TL;DR

```bash
# Review (safe)
scripts/ops/review_and_merge_pr.sh --pr 259 --watch

# Merge (wenn Review OK)
scripts/ops/review_and_merge_pr.sh --pr 259 --merge --update-main
```

---

## Docs Diff Guard (auto beim Merge)

Beim `--merge` läuft standardmäßig automatisch ein **Docs Diff Guard**, der große versehentliche Löschungen in `docs/*` erkennt und **den Merge blockiert**.

### Override-Optionen
```bash
# Custom Threshold (z.B. bei beabsichtigter Restrukturierung)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --docs-guard-threshold 500

# Warn-only (kein Fail, nur Warnung)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --docs-guard-warn-only

# Guard komplett überspringen (NOT RECOMMENDED)
scripts/ops/review_and_merge_pr.sh --pr 123 --merge --skip-docs-guard
```

**Siehe auch:**
- Vollständige Dokumentation: `docs/ops/README.md` (Abschnitt "Docs Diff Guard")
- PR Management Toolkit: `docs/ops/PR_MANAGEMENT_TOOLKIT.md`
- Standalone Script: `scripts/ops/docs_diff_guard.sh`
- Merge-Log: `docs/ops/PR_311_MERGE_LOG.md`

---


## 🎯 Use Cases

### Use Case 1: Standard PR Review & Merge

```bash
cd ~/Peak_Trade

# Step 1: Review
scripts/ops/review_and_merge_pr.sh --pr 259 --watch --allow-fail audit

# Step 2: Merge (nur wenn alles grün)
scripts/ops/review_and_merge_pr.sh --pr 259 --merge --update-main
```

**Was passiert:**
- ✅ Prüft Mergeable-Status (+ Retries)
- ✅ Prüft Review Decision
- ✅ Wartet auf CI-Checks (`--watch`)
- ✅ Validiert alle Checks (erlaubt audit zu failen)
- 🚀 Merged (squash) + löscht Branch + updated local main

---

### Use Case 2: Quick One-Shot (Template)

```bash
cd ~/Peak_Trade

# Generic Template (für beliebige PRs)
PR=259 ./scripts/ops/pr_review_merge_workflow_template.sh
```

**Wann nutzen:**
- ✅ Routine-PRs
- ✅ Pre-Approved PRs
- ✅ Time-Critical Merges

**Wann NICHT nutzen:**
- ❌ High-Risk Changes (Execution/Risk/Config)
- ❌ First-Time Use (nutze 2-Step stattdessen)

---

### Use Case 3: Format-Only PRs

```bash
cd ~/Peak_Trade

# Review (audit darf failen, working tree egal)
scripts/ops/review_and_merge_pr.sh --pr 259 --allow-fail audit --dirty-ok

# Merge
scripts/ops/review_and_merge_pr.sh --pr 259 --merge --dirty-ok
```

**Hinweis:** Für Format-Only PRs sollte das `ops/format-only` Label + CI-Verifier genutzt werden (siehe [Policy Critic Runbook](POLICY_CRITIC_TRIAGE_RUNBOOK.md)).

---

### Use Case 4: Dry-Run (Testing)

```bash
cd ~/Peak_Trade

# Test Merge (keine echten Änderungen)
scripts/ops/review_and_merge_pr.sh --pr 259 --merge --dry-run
```

**Wann nutzen:**
- ✅ Neuer Workflow
- ✅ Unsicher über Merge-Status
- ✅ Testing von Skript-Änderungen

---

## 🛡️ Safety Checklist

Vor jedem Merge:

- [ ] **PR reviewed?** Code-Review durchgeführt
- [ ] **Checks passing?** Alle CI-Checks grün (oder explizit allowed)
- [ ] **Conflicts resolved?** Keine Merge-Konflikte
- [ ] **Approved?** Review Decision = APPROVED
- [ ] **Working tree clean?** Oder `--dirty-ok` bewusst genutzt

---

## 🐛 Common Issues

### Issue: `gh auth not available`

**Fix:**
```bash
gh auth login
```

### Issue: `Working tree not clean`

**Options:**
```bash
# Option 1: Commit/Stash
git stash

# Option 2: Override
--dirty-ok
```

### Issue: `PR has merge conflicts`

**Fix:**
```bash
# Im PR-Branch
git checkout feature-branch
git fetch origin main
git merge origin/main
# Resolve conflicts
git push
```

### Issue: `Checks still pending`

**Fix:**
```bash
# Nutze Watch-Modus
--watch
```

### Issue: `Mergeable status is UNKNOWN`

**Fix:**
```bash
# Mehr Retries
MERGEABLE_RETRIES=10 MERGEABLE_SLEEP_SEC=5 \
  scripts/ops/review_and_merge_pr.sh --pr 259
```

---

## 📋 Cheat Sheet

```bash
# === Review Only ===
scripts/ops/review_and_merge_pr.sh --pr <NUM>

# === Review + Watch ===
scripts/ops/review_and_merge_pr.sh --pr <NUM> --watch

# === Allow Specific Fails ===
scripts/ops/review_and_merge_pr.sh --pr <NUM> --allow-fail audit

# === Merge (after review) ===
scripts/ops/review_and_merge_pr.sh --pr <NUM> --merge --update-main

# === Dry Run ===
scripts/ops/review_and_merge_pr.sh --pr <NUM> --merge --dry-run

# === One-Shot Template ===
PR=<NUM> ./scripts/ops/pr_review_merge_workflow_template.sh

# === Custom Merge Method ===
PR=<NUM> MERGE_METHOD=rebase ./scripts/ops/pr_review_merge_workflow_template.sh

# === Multiple Allow-Fails ===
scripts/ops/review_and_merge_pr.sh --pr <NUM> --allow-fail audit --allow-fail lint

# === Extended Retries ===
MERGEABLE_RETRIES=10 MERGEABLE_SLEEP_SEC=5 \
  scripts/ops/review_and_merge_pr.sh --pr <NUM>
```

---

## 🔗 Weiterführende Links

- **Vollständige Dokumentation**: [PR_MANAGEMENT_TOOLKIT.md](PR_MANAGEMENT_TOOLKIT.md)
- **Ops Tools Overview**: [README.md](README.md)
- **Policy Critic Runbook**: [POLICY_CRITIC_TRIAGE_RUNBOOK.md](POLICY_CRITIC_TRIAGE_RUNBOOK.md)

---

**Version:** 1.0.0  
**Letzte Aktualisierung:** 2025-12-23

<!-- toolkit-smoke: 2025-12-23 -->
