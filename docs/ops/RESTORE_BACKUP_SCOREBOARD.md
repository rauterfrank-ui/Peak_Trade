# Git Rescue Backup — Restore Scoreboard

**Status:** 2026-01-03  
**Operator:** Peak_Trade Restore Operation  
**Source:** `~/Peak_Trade_backups/rescue_20260101_160316/`

---

## 📦 Artefakte (Source of Truth)

| Artefakt | Pfad/Name | Status | Größe/Details |
|----------|-----------|--------|---------------|
| **Bundle** | `peak_trade_allrefs_20260101_160316.bundle` | ✅ Vorhanden | 9.8 MB, 484 refs |
| **Top-20 Report** | `reports&#47;triage_top20_20260101_181636.tsv` | ✅ | 21 Branches (Top-Prio) |
| **Key Branches Status** | `reports&#47;key_branches_status_20260101_181231.tsv` | ✅ | 160 Branches |
| **Cleanup Candidates** | `reports&#47;cleanup_candidates_key_branches_20260101_183049.tsv` | ✅ | 160 Branches |
| **Final Summary** | `FINAL_SUMMARY.md` | ✅ | Rescue-Overview |

---

## 🔄 Recovered Branches — PRs Created (2026-01-03)

### Summary

**Total:** 12 PRs (#524-535)  
**Status:** 7 OPEN | 5 DRAFT  
**Risk:** 7 Low-Risk 🟢 | 5 Medium/High-Risk 🟡

### Restore PRs (Git Rescue Backup 2026-01-01)

| PR | Branch | Status | Risk | Labels | Title |
|---:|---|---|:---:|---|---|
| [#524](https://github.com/rauterfrank-ui/Peak_Trade/pull/524) | `recovered&#47;feat-stability-wave-b` | ✅ OPEN | 🟢 | `restore-backup,needs-review,feature,stability,testing` | restore: feat/stability-wave-b - cache manifest + repro helpers |
| [#525](https://github.com/rauterfrank-ui/Peak_Trade/pull/525) | `recovered&#47;docs-audit-remediation-bounded-live-100go` | 🔒 DRAFT | 🟡 | `restore-backup,needs-review,docs,high-risk` | restore: docs-audit-remediation-bounded-live-100go |
| [#526](https://github.com/rauterfrank-ui/Peak_Trade/pull/526) | `recovered&#47;docs-risk-layer-phase0-alignment` | ✅ OPEN | 🟢 | `restore-backup,needs-review,docs` | restore: docs-risk-layer-phase0-alignment |
| [#527](https://github.com/rauterfrank-ui/Peak_Trade/pull/527) | `recovered&#47;docs&#47;bg-job-runbook-integration` | ✅ OPEN | 🟢 | `restore-backup,needs-review,docs` | restore: docs/bg-job-runbook-integration |
| [#528](https://github.com/rauterfrank-ui/Peak_Trade/pull/528) | `recovered&#47;docs&#47;fix-reference-targets-priority1` | ✅ OPEN | 🟢 | `restore-backup,needs-review,docs` | restore: docs/fix-reference-targets-priority1 |
| [#529](https://github.com/rauterfrank-ui/Peak_Trade/pull/529) | `recovered&#47;docs&#47;merge-log-pr488` | ✅ OPEN | 🟢 | `restore-backup,needs-review,docs` | restore: docs/merge-log-pr488 |
| [#530](https://github.com/rauterfrank-ui/Peak_Trade/pull/530) | `recovered&#47;docs&#47;ops-merge-logs-481-482` | ✅ OPEN | 🟢 | `restore-backup,needs-review,docs` | restore: docs/ops-merge-logs-481-482 |
| [#531](https://github.com/rauterfrank-ui/Peak_Trade/pull/531) | `recovered&#47;feat-data-offline-garch-feed` | ✅ OPEN | 🟢 | `restore-backup,needs-review,feature` | restore: feat-data-offline-garch-feed |
| [#532](https://github.com/rauterfrank-ui/Peak_Trade/pull/532) | `recovered&#47;feat-live-exec-phase0-foundation` | 🔒 DRAFT | 🟡 | `restore-backup,needs-review,feature,high-risk` | restore: feat-live-exec-phase0-foundation |
| [#533](https://github.com/rauterfrank-ui/Peak_Trade/pull/533) | `recovered&#47;feat-live-exec-phase1-shadow` | 🔒 DRAFT | 🟡 | `restore-backup,needs-review,feature,high-risk` | restore: feat-live-exec-phase1-shadow |
| [#534](https://github.com/rauterfrank-ui/Peak_Trade/pull/534) | `recovered&#47;feat-live-exec-wp0c-governance` | 🔒 DRAFT | 🟡 | `restore-backup,needs-review,feature,high-risk` | restore: feat-live-exec-wp0c-governance |
| [#535](https://github.com/rauterfrank-ui/Peak_Trade/pull/535) | `recovered&#47;feat-risk-layer-phase6-integration` | 🔒 DRAFT | 🟡 | `restore-backup,needs-review,feature,high-risk` | restore: feat-risk-layer-phase6-integration |

### Legende

**Status:**
- ✅ **OPEN:** Bereit für Review & Merge
- 🔒 **DRAFT:** Enthält Execution/Risk/Governance-Touches, extra Review erforderlich

**Risk:**
- 🟢 **Low Risk:** Docs/Tests/Tooling, keine kritischen Systeme
- 🟡 **Medium/High Risk:** Touches in Execution-Layer, Live-Trading, Risk-Layer oder Governance

---

## 🎯 Next Restore Queue (Priorisiert, Top 10)

| # | Branch Name | Ahead | Diff (files/ins/del) | Warum wichtig? | Status | Empfohlene Aktion | Risk Note |
|---|-------------|-------|----------------------|----------------|--------|-------------------|-----------|
| ~~**1**~~ | ~~`feat/stability-wave-b`~~ | ~~11~~ | ~~8f / +1280 / -7~~ | ~~Stability-Feature~~ | ✅ **PR #524** | ~~Restore → PR~~ | 🟢 DONE |
| **2** | `fix/audit-urllib3-fastapi` | 8 | 4f / +470 / -12 | Dependency-Fix (urllib3/fastapi) | ⏳ Pending | **Restore → PR** | 🟢 Audit-Fix |
| **3** | `feat/strategy-layer-vnext-runner` | 7 | 10f / +2614 / -31 | Strategy-Layer (Backtest) | ⏳ Pending | **Restore → Review → PR** | 🟡 Strategy-Code |
| **4** | `docs/docs-reference-targets-gate-cleanup` <!-- pt:ref-target-ignore --> | 6 | 21f / +105 / -99 | Docs-Gate-Cleanup | ⏳ Pending | **Park (evtl obsolet)** | 🟢 Docs-only |
| **5** | `docs&#47;ops&#47;stability-plan-v1` <!-- pt:ref-target-ignore --> | 6 | 1f / +11 / -0 | Stability-Plan Doku | ⏳ Pending | **Park** | 🟢 Docs-only |
| **6** | `docs/execution-wp4b-operator-drills-evidence-pack` <!-- pt:ref-target-ignore --> | 5 | 22f / +1592 / -18 | WP4B Operator-Docs | ⏳ Pending | **Review (bereits recovered?)** | 🟢 Docs+Scripts |
| **7** | `docs/fix-moved-script-paths-comprehensive` <!-- pt:ref-target-ignore --> | 5 | 20f / +84 / -78 | Script-Path-Fixes | ⏳ Pending | **Park (evtl obsolet)** | 🟢 Docs-only |
| **8** | `docs/phase0-foundation-prep` <!-- pt:ref-target-ignore --> | 5 | 8f / +4020 / -0 | Phase0-Prep-Docs | ⏳ Pending | **Park** | 🟢 Docs-only |
| **9** | `docs&#47;ops&#47;merge-log-ux-hardening-v2` <!-- pt:ref-target-ignore --> | 5 | 5f / +673 / -45 | Merge-Log UX | ⏳ Pending | **Park** | 🟢 Docs+Scripts |
| **10** | `fix/recon-audit-gate-python-runner` | 5 | 3f / +118 / -9 | Recon-Audit-Fix | ⏳ Pending | **Review → PR** | 🟡 Scripts+Tests |

**Priorisierungs-Heuristik:**
- ✅ **High Priority:** fix/* und feat/* mit Tests, kein execution-layer
- ⚠️ **Medium Priority:** docs/* mit Scripts, Strategy/Risk-Code (needs review)
- 🔵 **Low Priority:** reine docs/* ohne Code, merge-conflict-only branches

**Risk-Klassifikation:**
- 🟢 **Low Risk:** Docs-only, keine Live-Code-Touches
- 🟡 **Medium Risk:** SRC-Changes, aber Tests vorhanden oder Research-Code
- 🔴 **High Risk:** Execution-Layer, Live-Trading, Risk-Layer (extra Verifikation!)

---

## 📋 Restore-Regeln & Verifikation

### Wann ein Branch "parked" wird:
- Inhalt ist wahrscheinlich obsolet (main hat ähnliche Änderungen)
- Reine Docs-Änderungen mit niedriger Priorität
- Merge-Konflikte zeigen, dass Inhalt bereits in main integriert wurde
- Branch ist nicht in Top-20, aber im Backup gesichert

### Wann ein Branch zum PR wird:
- ✅ Enthält einzigartige, wertvolle Änderungen
- ✅ Tests vorhanden (für Code-Änderungen)
- ✅ Kein Execution-Layer (oder explizit als "never-live" markiert)
- ✅ Ruff/Pytest-Subset läuft sauber

### Minimale Verifikation vor PR:
```bash
# 1. Branch lokal erstellen
git checkout -b recovered/<name> refs/backup/gone/<original-name>

# 2. Rebase auf aktuellen main (sanity check)
git rebase origin/main  # Konflikt-Check

# 3. Ruff-Check (Formatter + Linter)
ruff format --check .
ruff check .

# 4. Pytest-Subset (schnell)
python3 -m pytest tests/ -k "not slow" --maxfail=3 -x

# 5. Push zu Remote
git push -u origin recovered/<name>

# 6. PR erstellen (siehe unten)
```

---

## 🎬 Operator-Anweisungen

### 1. Remote-vs-Local Abgleich (nächster Schritt)

**Kommando 1:** Prüfe, welche recovered/* Branches noch kein PR haben:

```bash
cd ~/Peak_Trade
for branch in $(git branch --list "recovered/*" | sed 's/^..//'); do
  pr_exists=$(gh pr list --head "$branch" --json number --jq '.[].number' 2>/dev/null)
  if [ -z "$pr_exists" ]; then
    echo "🔴 NO PR: $branch"
  else
    echo "✅ PR #$pr_exists: $branch"
  fi
done
```

**Kommando 2:** Liste alle Kandidaten aus Top-20, die noch nicht recovered sind:

```bash
cd ~/Peak_Trade_backups/rescue_20260101_160316/reports
awk -F'\t' 'NR>1 {print $1}' triage_top20_20260101_181636.tsv | while read ref; do
  branch_name=$(echo "$ref" | sed 's|refs/backup/gone/||')
  exists=$(git -C ~/Peak_Trade branch --list "recovered/*" | grep -q "$branch_name" && echo "YES" || echo "NO")
  echo "$branch_name|$exists"
done | grep '|NO$'
```

---

### 2. PR-Erstellung (ohne gh-watch/pager-Hänger)

**Sicherer PR-Workflow:**

```bash
# Umgebung: gh-watch/pager deaktivieren
export GH_PAGER=""
export PAGER="cat"

# Branch pushen (falls noch nicht geschehen)
git push -u origin recovered/<branch-name>

# PR erstellen (non-interactive, no-verify)
gh pr create \
  --base main \
  --head "recovered/<branch-name>" \
  --title "restore: <branch-name>" \
  --body "**Source:** Git Rescue Backup 2026-01-01

## Context
Restored from \`refs/backup/gone/<original-name>\` via rescue bundle.

## Changes
- [Summarize key changes from TSV report]

## Verification
- [ ] Ruff format/check: PASS
- [ ] Pytest subset: PASS
- [ ] No execution-layer touches: YES
- [ ] Docs-reference-targets: PASS

## Risk Assessment
🟢 Low | 🟡 Medium | 🔴 High

**Reason:** [Explain based on path_class and diff]

---
**Scoreboard:** \`docs/ops/RESTORE_BACKUP_SCOREBOARD.md\`
" \
  --label "restore-backup" \
  --label "needs-review" \
  --no-maintainer-edit

# Verify PR created
gh pr list --head "recovered/<branch-name>"
```

**Alternative (für Batch-PRs):**

```bash
# Script: scripts/ops/restore_queue_to_prs.sh (TODO: create)
# Liest RESTORE_BACKUP_SCOREBOARD.md, erstellt PRs für Queue-Items mit "Restore → PR"
```

---

## 🔍 Nächste Schritte (Empfohlen)

### ✅ Abgeschlossen (2026-01-03)
1. ✅ **12 PRs erstellt** für alle recovered Branches (#524-535)
2. ✅ **5 DRAFT PRs** markiert für High-Risk-Bereiche
3. ✅ **Batch-PR-Script** erstellt und erfolgreich ausgeführt

### 🎯 ToDo (Priorität)

**Priorität 1: Low-Risk PRs mergen** (7 PRs)
- PRs: [#524](https://github.com/rauterfrank-ui/Peak_Trade/pull/524), [#526](https://github.com/rauterfrank-ui/Peak_Trade/pull/526)-[#531](https://github.com/rauterfrank-ui/Peak_Trade/pull/531)
- Ruff/Pytest smoke-check empfohlen
- Können schnell gemerged werden (Status: OPEN 🟢)

**Priorität 2: DRAFT PRs reviewen** (5 PRs)
- PRs: [#525](https://github.com/rauterfrank-ui/Peak_Trade/pull/525), [#532](https://github.com/rauterfrank-ui/Peak_Trade/pull/532)-[#535](https://github.com/rauterfrank-ui/Peak_Trade/pull/535)
- Execution/Risk/Governance-Layer Touches
- Gründliches Review + Verifikation erforderlich
- Falls OK: Draft-Status entfernen mit `gh pr ready <PR-number>`

**Priorität 3: Welle 2** (Top 3 aus Queue restoren)
- `fix/audit-urllib3-fastapi` (Queue #2)
- `feat/strategy-layer-vnext-runner` (Queue #3)
- `docs/docs-reference-targets-gate-cleanup` <!-- pt:ref-target-ignore --> (Queue #4, evtl. park)

**Priorität 4: Audit**
- Cleanup-Candidates-Report auswerten → "park vs. restore" entscheiden

---

## 📚 Referenzen

- **Rescue-Bundle:** `~/Peak_Trade_backups/rescue_20260101_160316/peak_trade_allrefs_20260101_160316.bundle`
- **Rescue-Summary:** `~/Peak_Trade_backups/rescue_20260101_160316/FINAL_SUMMARY.md`
- **Verifikations-Script:** `scripts/ops/verify_git_rescue_artifacts.sh`
- **Restore-Notfallprozedur:** Siehe `FINAL_SUMMARY.md` → "Restore-Notfallprozedur (Bundle)"

---

**Last Updated:** 2026-01-03 (12 PRs created: #524-535)  
**Next Review:** Nach Low-Risk-PRs-Merge (geschätzt: 2026-01-04)
