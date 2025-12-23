# Peak_Trade – PR Management Toolkit

Vollständiges Toolkit für sicheres PR-Review und Merge mit Safe-by-Default-Design.

---

## 📋 Übersicht

Das PR-Management-Toolkit bietet drei Komponenten für unterschiedliche Use-Cases:

| Tool | Typ | Use Case | Kontrolle |
|------|-----|----------|-----------|
| `review_and_merge_pr.sh` | Basis-Tool | Flexibles Review & Merge mit voller Kontrolle | ⭐⭐⭐⭐⭐ Max |
| `pr_review_merge_workflow.sh` | One-Shot | Hardcoded für spezifische PRs | ⭐⭐ Medium |
| `pr_review_merge_workflow_template.sh` | Template | Wiederverwendbar für beliebige PRs | ⭐⭐⭐⭐ Hoch |

---

## 🛠️ 1. Basis-Tool: `review_and_merge_pr.sh`

Das Haupt-Werkzeug mit voller Kontrolle über jeden Parameter.

### Features

#### Sicherheits-Guards 🛡️

- ✅ **Safe-by-Default**: Review-only ohne `--merge` Flag
- ✅ **Working Tree Check**: Erfordert sauberen Working Tree (Override mit `--dirty-ok`)
- ✅ **GitHub Auth Validation**: Prüft `gh auth status`
- ✅ **Mergeable Status**: Automatische Retries bei `UNKNOWN` (konfigurierbar)
- ✅ **Review Decision Check**: Blockiert bei `CHANGES_REQUESTED`
- ✅ **CI Checks Validation**: Mit selektiven `--allow-fail` Options

#### Intelligente Features 🧠

- 🔄 **Retry-Logik**: 3-5 Versuche bei `UNKNOWN` Mergeable-Status
- 👀 **Watch Mode**: Wartet automatisch auf CI-Check-Completion
- 🎯 **Flexible Allow-Fail**: Für bekannte Flaky-Checks (z.B. audit)
- 🧪 **Dry-Run**: Test-Modus ohne echte Änderungen
- 📊 **Detaillierte Reports**: Pre/Post-Merge Summaries

### Verwendung

```bash
# Review-only (safe default)
scripts/ops/review_and_merge_pr.sh --pr 259

# Review mit Watch
scripts/ops/review_and_merge_pr.sh --pr 259 --watch --allow-fail audit

# Merge + Update main
scripts/ops/review_and_merge_pr.sh --pr 259 --merge --update-main

# Dry-run zum Testen
scripts/ops/review_and_merge_pr.sh --pr 259 --merge --dry-run

# Alle Optionen kombiniert
MERGEABLE_RETRIES=5 MERGEABLE_SLEEP_SEC=3 \
  scripts/ops/review_and_merge_pr.sh \
  --pr 259 \
  --watch \
  --allow-fail audit \
  --merge \
  --method squash \
  --update-main \
  --dirty-ok
```

### Optionen

```
Usage:
  scripts/ops/review_and_merge_pr.sh --pr <number> [options]

Options:
  --watch                 Watch PR checks until completion.
  --merge                 Perform merge (default is review-only).
  --method <squash|merge|rebase>  Merge method (default: squash).
  --delete-branch         Delete remote branch after merge (default: on).
  --no-delete-branch      Do not delete remote branch.
  --update-main           After merge, checkout main and pull --ff-only.
  --allow-fail <name>     Allow a specific check to fail (repeatable).
  --dirty-ok              Do not require clean working tree.
  --dry-run               Print actions but do not merge/update.
  -h, --help              Show help.

Environment Variables:
  MERGEABLE_RETRIES       Number of retries for mergeable status (default: 3).
  MERGEABLE_SLEEP_SEC     Seconds to sleep between retries (default: 2).
```

### Workflow-Ablauf

```
┌─────────────────────────────────────────┐
│ Preflight Checks                        │
├─────────────────────────────────────────┤
│ ✅ Working Tree sauber (oder --dirty-ok) │
│ ✅ GitHub Auth verfügbar                 │
│ ✅ Repo identifizierbar                  │
└─────────────────────────────────────────┘
              ⬇️
┌─────────────────────────────────────────┐
│ PR Information                          │
├─────────────────────────────────────────┤
│ 📊 PR Summary (Titel, Author, Labels)   │
│ 📈 Diff-Statistik                       │
└─────────────────────────────────────────┘
              ⬇️
┌─────────────────────────────────────────┐
│ Mergeable Status Check                  │
├─────────────────────────────────────────┤
│ 🔄 Retries bei UNKNOWN (bis zu 5x)     │
│ ✅ MERGEABLE → Continue                 │
│ ❌ CONFLICTING → FAIL (bei --merge)     │
│ ⚠️  UNKNOWN → Warning                   │
└─────────────────────────────────────────┘
              ⬇️
┌─────────────────────────────────────────┐
│ Review Decision (nur bei --merge)       │
├─────────────────────────────────────────┤
│ ✅ APPROVED → Continue                  │
│ ❌ CHANGES_REQUESTED → FAIL             │
│ ⚠️  REVIEW_REQUIRED → Warning           │
└─────────────────────────────────────────┘
              ⬇️
┌─────────────────────────────────────────┐
│ CI Checks Validation                    │
├─────────────────────────────────────────┤
│ 👀 Watch Mode (optional)                │
│ ✅ Validiert alle Checks                │
│ 🎯 Erlaubt spezifische Fails            │
│ ⏱️  Blockiert bei PENDING               │
└─────────────────────────────────────────┘
              ⬇️
┌─────────────────────────────────────────┐
│ Review Complete (oder Merge)            │
├─────────────────────────────────────────┤
│ 🛡️ Review-only: Exit (kein Merge)      │
│ 🚀 --merge: Merge + Branch Delete       │
│ 🔄 --update-main: Checkout + Pull       │
└─────────────────────────────────────────┘
```

---

## 🎯 2. One-Shot Workflow: `pr_review_merge_workflow.sh`

Hardcoded für spezifische PRs – schneller Einsatz ohne Parameter.

### Verwendung

```bash
# Einfacher One-Shot (PR ist im Skript hardcoded)
./scripts/ops/pr_review_merge_workflow.sh
```

### Was passiert

1. ⚠️ **Working Tree Check**: Warnung bei uncommitted files
2. 🔍 **Review-Only**: Mit Watch + allow-fail audit
3. 🚀 **Merge**: Squash + Update main
4. 📊 **Post-Merge Summary**: Status + Latest commit

### Konfiguration

Editiere `PR=` Zeile im Skript:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd ~/Peak_Trade

PR=259  # ← Hier PR-Nummer anpassen

# Mergeable-Retries
export MERGEABLE_RETRIES=5
export MERGEABLE_SLEEP_SEC=2

# ... Rest des Skripts
```

---

## 🔄 3. Template Workflow: `pr_review_merge_workflow_template.sh`

Wiederverwendbares Template für beliebige PRs mit flexibler Konfiguration.

### Verwendung

```bash
# Via Environment Variable
PR=259 ./scripts/ops/pr_review_merge_workflow_template.sh

# Mit Custom-Config
PR=300 \
MERGE_METHOD=rebase \
ALLOW_FAIL_CHECKS="audit lint" \
MERGEABLE_RETRIES=5 \
  ./scripts/ops/pr_review_merge_workflow_template.sh

# Oder: PR direkt im Skript setzen
# Editiere PR= Zeile, dann:
./scripts/ops/pr_review_merge_workflow_template.sh
```

### Konfiguration (Environment Variables)

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `PR` | *(erforderlich)* | PR-Nummer |
| `ALLOW_FAIL_CHECKS` | `audit` | Space-separated Liste |
| `MERGE_METHOD` | `squash` | `squash`, `merge`, oder `rebase` |
| `MERGEABLE_RETRIES` | `5` | Anzahl Retries für Mergeable-Status |
| `MERGEABLE_SLEEP_SEC` | `2` | Sekunden zwischen Retries |

### Features

- 🧹 **Auto Dirty-OK**: Automatisches `--dirty-ok` bei uncommitted files
- 📊 **Ausführliche Reports**: Preflight + Post-Merge Summaries
- 🎯 **Flexible Config**: Alle Parameter via Environment Variables
- ✅ **Error-Handling**: Klar strukturierte Fehlerausgabe

---

## 🚀 Quick Start Guide

### Szenario 1: Einfaches Review

```bash
cd ~/Peak_Trade

# Review-only (kein Merge)
scripts/ops/review_and_merge_pr.sh --pr 259
```

### Szenario 2: Review + Merge (2-Step, empfohlen)

```bash
cd ~/Peak_Trade

# Step 1: Review (wartet auf Checks)
scripts/ops/review_and_merge_pr.sh --pr 259 --watch --allow-fail audit

# Step 2: Merge (nur wenn Step 1 ✅)
scripts/ops/review_and_merge_pr.sh --pr 259 --merge --update-main
```

### Szenario 3: One-Shot Workflow

```bash
cd ~/Peak_Trade

# Hardcoded PR
./scripts/ops/pr_review_merge_workflow.sh

# Oder mit Template
PR=259 ./scripts/ops/pr_review_merge_workflow_template.sh
```

### Szenario 4: Custom Merge Method

```bash
cd ~/Peak_Trade

# Rebase statt squash
PR=259 MERGE_METHOD=rebase \
  ./scripts/ops/pr_review_merge_workflow_template.sh
```

---

## 🛡️ Sicherheitsfeatures

### 1. Safe-by-Default Design

- ❌ **Kein versehentliches Mergen**: `--merge` Flag explizit erforderlich
- ✅ **Review-only als Standard**: Zeigt alle Informationen ohne Änderungen
- 🧪 **Dry-Run Support**: Test-Modus für alle Operationen

### 2. Multi-Layer Validation

```
┌─────────────────────────┐
│ Layer 1: Local Checks   │  Working Tree, Git Repo, gh auth
├─────────────────────────┤
│ Layer 2: GitHub Status  │  Mergeable Status (+ Retries)
├─────────────────────────┤
│ Layer 3: Review         │  Review Decision (APPROVED/CHANGES_REQUESTED)
├─────────────────────────┤
│ Layer 4: CI Checks      │  Validiert alle Checks, Allow-Fail Support
├─────────────────────────┤
│ Layer 5: GitHub BP      │  Branch Protection (GitHub-side)
└─────────────────────────┘
```

### 3. Intelligent Retry Logic

GitHub berechnet Mergeable-Status asynchron. Das Toolkit wartet automatisch:

```bash
MERGEABLE_RETRIES=5       # 5 Versuche
MERGEABLE_SLEEP_SEC=3     # 3 Sekunden Pause

# Status: UNKNOWN → Retry 1/5 (3s) → ... → MERGEABLE ✅
```

### 4. Selective Allow-Fail

Bekannte Flaky-Checks (z.B. audit baseline) können explizit erlaubt werden:

```bash
# Single check
--allow-fail audit

# Multiple checks
--allow-fail audit --allow-fail lint

# Via Environment (Template)
ALLOW_FAIL_CHECKS="audit lint"
```

⚠️ **Wichtig**: `--allow-fail` bypassed NICHT GitHub Branch Protection!

---

## 🐛 Troubleshooting

### Error: `gh auth not available`

```bash
# GitHub CLI installieren
brew install gh

# Authentifizieren
gh auth login

# Status prüfen
gh auth status
```

### Error: `Working tree not clean`

```bash
# Option 1: Commiten
git add -A
git commit -m "WIP: cleanup"

# Option 2: Stashen
git stash

# Option 3: --dirty-ok verwenden
scripts/ops/review_and_merge_pr.sh --pr 259 --dirty-ok
```

### Error: `PR has merge conflicts`

```bash
# Im PR-Branch
git checkout feature-branch
git fetch origin main
git merge origin/main

# Konflikte lösen
git add .
git commit

# Push
git push
```

### Warning: `PR mergeable status is UNKNOWN`

Das ist normal nach frischem Push. Optionen:

```bash
# Option 1: Warten (GitHub berechnet Status)
sleep 10
scripts/ops/review_and_merge_pr.sh --pr 259

# Option 2: Mehr Retries
MERGEABLE_RETRIES=10 MERGEABLE_SLEEP_SEC=5 \
  scripts/ops/review_and_merge_pr.sh --pr 259

# Option 3: Watch Mode nutzen
scripts/ops/review_and_merge_pr.sh --pr 259 --watch
```

### Error: `Checks still pending`

```bash
# Watch-Modus nutzt um auf Completion zu warten
scripts/ops/review_and_merge_pr.sh --pr 259 --watch
```

### Warning: `Review decision is REVIEW_REQUIRED`

Das ist nur eine Warnung. Optionen:

```bash
# Option 1: Review anfordern
gh pr review 259 --approve

# Option 2: Merge trotzdem versuchen (Branch Protection kann blocken)
scripts/ops/review_and_merge_pr.sh --pr 259 --merge

# Option 3: Als Admin mergen (wenn erlaubt)
gh pr merge 259 --admin --squash
```

---

## 📚 Beispiele

### Beispiel 1: Standard Review-Merge Flow

```bash
#!/usr/bin/env bash
# Standard 2-step workflow

cd ~/Peak_Trade
PR=259

# Step 1: Review
echo "═══ Review-Only ═══"
scripts/ops/review_and_merge_pr.sh \
  --pr "$PR" \
  --watch \
  --allow-fail audit

# User check point
read -p "Continue with merge? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

# Step 2: Merge
echo "═══ Merge ═══"
scripts/ops/review_and_merge_pr.sh \
  --pr "$PR" \
  --merge \
  --method squash \
  --update-main

echo "✅ Done."
```

### Beispiel 2: Batch PR Processing

```bash
#!/usr/bin/env bash
# Process multiple PRs

cd ~/Peak_Trade

PRS=(259 260 261 262)

for pr in "${PRS[@]}"; do
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Processing PR #$pr"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Review
  if scripts/ops/review_and_merge_pr.sh --pr "$pr" --watch --allow-fail audit; then
    echo "✅ Review OK for PR #$pr"

    # Merge
    if scripts/ops/review_and_merge_pr.sh --pr "$pr" --merge --update-main; then
      echo "✅ Merged PR #$pr"
    else
      echo "❌ Merge failed for PR #$pr"
      break
    fi
  else
    echo "❌ Review failed for PR #$pr"
    break
  fi
done

echo ""
echo "✅ Batch processing complete."
```

### Beispiel 3: CI/CD Integration

```bash
#!/usr/bin/env bash
# Auto-merge approved PRs (für CI/CD)

cd ~/Peak_Trade

# Find approved PRs
APPROVED_PRS=$(gh pr list --json number,reviewDecision \
  --jq '.[] | select(.reviewDecision == "APPROVED") | .number')

if [ -z "$APPROVED_PRS" ]; then
  echo "No approved PRs found."
  exit 0
fi

echo "Found approved PRs: $APPROVED_PRS"

for pr in $APPROVED_PRS; do
  echo ""
  echo "Processing PR #$pr..."

  # Merge mit allen Checks
  if MERGEABLE_RETRIES=10 scripts/ops/review_and_merge_pr.sh \
    --pr "$pr" \
    --watch \
    --allow-fail audit \
    --merge \
    --update-main; then
    echo "✅ Auto-merged PR #$pr"
  else
    echo "⚠️ Could not auto-merge PR #$pr (checks failed or conflicts)"
  fi
done
```

### Beispiel 4: Review-Only mit Report

```bash
#!/usr/bin/env bash
# Review mit Report-Generation

cd ~/Peak_Trade
PR=259
REPORT_FILE="reports/ops/PR_${PR}_review_$(date +%Y%m%d_%H%M%S).md"

mkdir -p reports/ops

{
  echo "# PR #$PR Review Report"
  echo ""
  echo "**Generated:** $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""

  echo "## PR Information"
  gh pr view "$PR" --json number,title,author,labels,state \
    --jq '"- **Title:** \(.title)\n- **Author:** \(.author.login)\n- **State:** \(.state)\n- **Labels:** \(.labels | map(.name) | join(", "))"'

  echo ""
  echo "## Checks Status"
  gh pr checks "$PR"

  echo ""
  echo "## Mergeable Status"
  gh pr view "$PR" --json mergeable,reviewDecision \
    --jq '"- **Mergeable:** \(.mergeable)\n- **Review Decision:** \(.reviewDecision)"'

  echo ""
  echo "## Diff Stat"
  gh pr diff "$PR" --stat
} > "$REPORT_FILE"

echo "✅ Report generated: $REPORT_FILE"

# Optional: Review-only run
scripts/ops/review_and_merge_pr.sh --pr "$PR"
```

---

## 🔬 Advanced Usage

### Custom Merge Messages

```bash
# Das Skript nutzt GitHub's Standard-Squash-Message.
# Für custom messages, nutze gh pr merge direkt:

gh pr merge 259 --squash --subject "feat: custom message" --body "Details..."

# Oder: Kombiniere mit dem Review-Script
scripts/ops/review_and_merge_pr.sh --pr 259  # Review-only
gh pr merge 259 --squash --subject "..."     # Custom merge
```

### Parallel PR Reviews

```bash
#!/usr/bin/env bash
# Review multiple PRs in parallel

PRS=(259 260 261)

for pr in "${PRS[@]}"; do
  (
    echo "Reviewing PR #$pr..."
    scripts/ops/review_and_merge_pr.sh --pr "$pr" > "review_$pr.log" 2>&1
    echo "✅ Review complete for PR #$pr"
  ) &
done

wait
echo "All reviews complete. Check review_*.log files."
```

### Conditional Merge Based on Labels

```bash
#!/usr/bin/env bash
# Only merge PRs with specific label

PR=259
REQUIRED_LABEL="ready-to-merge"

LABELS=$(gh pr view "$PR" --json labels --jq '.labels[].name')

if echo "$LABELS" | grep -q "$REQUIRED_LABEL"; then
  echo "✅ PR has required label. Proceeding..."
  scripts/ops/review_and_merge_pr.sh --pr "$PR" --merge --update-main
else
  echo "❌ PR missing required label: $REQUIRED_LABEL"
  exit 1
fi
```

---

## 📊 Exit Codes

| Code | Bedeutung |
|------|-----------|
| 0 | Erfolg (Review complete oder Merge successful) |
| 1 | Fehler (Checks failed, Conflicts, Auth failed, etc.) |

### Verwendung in Scripts

```bash
if scripts/ops/review_and_merge_pr.sh --pr 259; then
  echo "Success!"
else
  echo "Failed with exit code: $?"
  # Rollback oder Notification
fi
```

---

## 🔗 Integration mit anderen Tools

### Integration mit Slack

```bash
#!/usr/bin/env bash
# Notify Slack on merge

PR=259
SLACK_WEBHOOK="https://hooks.slack.com/services/..."

if scripts/ops/review_and_merge_pr.sh --pr "$PR" --merge --update-main; then
  curl -X POST "$SLACK_WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d "{\"text\":\"✅ PR #$PR merged successfully\"}"
else
  curl -X POST "$SLACK_WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d "{\"text\":\"❌ PR #$PR merge failed\"}"
fi
```

### Integration mit GitHub Actions

```yaml
# .github/workflows/auto-merge.yml
name: Auto-Merge Approved PRs

on:
  pull_request_review:
    types: [submitted]

jobs:
  auto-merge:
    if: github.event.review.state == 'approved'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup gh CLI
        run: |
          gh auth login --with-token <<< "${{ secrets.GITHUB_TOKEN }}"

      - name: Review & Merge
        run: |
          PR_NUMBER=${{ github.event.pull_request.number }}

          if scripts/ops/review_and_merge_pr.sh \
            --pr "$PR_NUMBER" \
            --watch \
            --allow-fail audit \
            --merge \
            --update-main; then
            echo "✅ Auto-merged PR #$PR_NUMBER"
          else
            echo "⚠️ Could not auto-merge PR #$PR_NUMBER"
          fi
```

---

## 📝 Best Practices

### 1. Immer 2-Step Workflow nutzen

```bash
# ✅ Gut: Review → Check → Merge
scripts/ops/review_and_merge_pr.sh --pr 259
# ... Review results ...
scripts/ops/review_and_merge_pr.sh --pr 259 --merge

# ❌ Riskant: One-shot Merge
scripts/ops/review_and_merge_pr.sh --pr 259 --merge  # Ohne Review!
```

### 2. Watch Mode für CI-abhängige PRs

```bash
# ✅ Gut: Warte auf Checks
scripts/ops/review_and_merge_pr.sh --pr 259 --watch

# ⚠️ Risk: Merge ohne Check-Completion
scripts/ops/review_and_merge_pr.sh --pr 259 --merge  # Checks pending!
```

### 3. Allow-Fail nur für bekannte Issues

```bash
# ✅ Gut: Explizit dokumentierte Flaky-Checks
--allow-fail audit  # Bekannt: audit baseline Drift

# ❌ Falsch: Breite Allow-Fail Liste
--allow-fail audit --allow-fail test --allow-fail lint  # Zu viel!
```

### 4. Dry-Run für neue Workflows

```bash
# ✅ Gut: Test vor Production
scripts/ops/review_and_merge_pr.sh --pr 259 --merge --dry-run
# ... Review dry-run output ...
scripts/ops/review_and_merge_pr.sh --pr 259 --merge  # Real run

# ❌ Riskant: Direkt in Production
scripts/ops/review_and_merge_pr.sh --pr 259 --merge  # Ohne Test!
```

---

## 🔮 Zukünftige Erweiterungen

### Geplant

- [ ] GitHub Actions Integration (Workflow-Dispatch)
- [ ] Auto-Review für Auto-Generated PRs (Dependabot, etc.)
- [ ] Slack/Discord Notifications
- [ ] PR-Queue Management (Batch Processing)
- [ ] Review-Approval-Requirement Check
- [ ] Label-based Auto-Merge

### Nice-to-Have

- [ ] Web-UI Dashboard (Live PR Status)
- [ ] Conflict Resolution Hints
- [ ] PR Health Score (Readiness Metric)
- [ ] Integration mit Knowledge DB (AI-Review Summaries)

---

## 📁 Datei-Struktur

```
/Users/frnkhrz/Peak_Trade/
├── scripts/ops/
│   ├── review_and_merge_pr.sh                    # ✅ Basis-Tool
│   ├── pr_review_merge_workflow.sh               # ✅ One-Shot (hardcoded)
│   └── pr_review_merge_workflow_template.sh      # ✅ Template (generic)
└── docs/ops/
    ├── README.md                                  # ✅ Ops Tools Overview
    └── PR_MANAGEMENT_TOOLKIT.md                   # ✅ Diese Dokumentation
```

---

## 📚 Verwandte Dokumentation

- [Ops Tools README](README.md) — Übersicht aller Ops-Tools
- [Policy Critic Triage Runbook](POLICY_CRITIC_TRIAGE_RUNBOOK.md) — Format-only PR Handling
- [CI Large PR Handling](CI_LARGE_PR_HANDLING.md) — Large PR Workflows
- [Merge Log Template](MERGE_LOG_TEMPLATE_COMPACT.md) — Post-Merge Documentation

---

**Version:** 1.0.0  
**Letzte Aktualisierung:** 2025-12-23  
**Maintainer:** Peak_Trade Ops Team


---

## Meta: Dogfooding

Das Besondere an diesem Workflow: **Das PR-Management-Toolkit reviewt und merged sich selbst!**

Der PR für das Toolkit wird mit dem Toolkit selbst verarbeitet:

```bash
scripts/ops/review_and_merge_pr.sh --pr "$PR_NUM" --watch
scripts/ops/review_and_merge_pr.sh --pr "$PR_NUM" --merge --update-main
```

Das demonstriert:
- ✅ Das Toolkit funktioniert End-to-End
- ✅ Safe-by-default Design in Action
- ✅ Multi-layer Validation funktioniert
- ✅ Watch + Merge Workflow ist produktionsreif

### Deployment Automation

Das vollständige Deployment (Branch → Test → PR → Review → Merge) kann automatisiert werden:

```bash
cd ~/Peak_Trade
./scripts/ops/pr_toolkit_deploy_workflow.sh
```

Dieses Skript:
1. Erstellt Branch
2. Staged alle Toolkit-Dateien
3. Verifiziert Bash-Syntax und führt Tests aus
4. Committet + Pushed
5. Erstellt PR
6. **Reviewt + Merged den PR mit dem Toolkit selbst** 🎭

Optional mit allow-fail für bekannte Checks:

```bash
ALLOW_FAIL_CHECKS="audit" ./scripts/ops/pr_toolkit_deploy_workflow.sh
```
