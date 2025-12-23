# P0 Guardrails Quick Reference

> **P0 = Priority Zero** = Nicht-verhandelbare Sicherheits- und Qualitätsgates

---

## 🚦 Quick Status Check

```bash
# Zeige alle P0 Workflows und deren Status
gh workflow list | grep -E "(Dependency Review|CodeQL|CI|Lint|Audit|Policy|deps-sync|Health|Guard)"

# Prüfe ob Branch Protection aktiv ist
gh api repos/:owner/:repo/branches/main/protection

# Zeige aktuelle Required Checks
gh api repos/:owner/:repo/branches/main/protection/required_status_checks
```

---

## 📋 P0 Workflows (Required Checks)

| Workflow | File | Trigger | Zweck | Bypass? |
|----------|------|---------|-------|---------|
| **Dependency Review** | `dependency-review.yml` | PR | Blockiert HIGH/CRITICAL Schwachstellen | ❌ NEIN |
| **CodeQL** | `codeql.yml` | PR, Push, Weekly | Static Code Analysis | ❌ NEIN |
| **CI Tests** | `ci.yml` | PR, Push, merge_group | Unit/Integration Tests | ❌ NEIN |
| **Lint** | `lint.yml` | PR, Push, merge_group | Code Quality (Ruff) | ❌ NEIN |
| **CI Health Gate** | `test_health.yml` | PR, Push, merge_group | Test Health Metrics | ❌ NEIN |
| **Policy Critic** | `policy_critic.yml` | PR, merge_group | Governance Review | ⚠️ LITE Mode bei >250 Files |
| **Audit** | `audit.yml` | PR, Push, merge_group | Compliance Checks | ❌ NEIN |
| **Deps Sync Guard** | `deps_sync_guard.yml` | PR, merge_group | requirements.txt ↔ uv.lock sync | ❌ NEIN |
| **Reports Guard** | `guard-reports-ignored.yml` | PR, merge_group | reports/ MUSS ignored sein | ❌ NEIN |
| **No Tracked Reports** | `policy_tracked_reports_guard.yml` | PR, merge_group | Keine tracked reports/ | ❌ NEIN |

**Alle Workflows haben `merge_group` trigger** für Merge Queue Support ✅

---

## 🛡️ CODEOWNERS

**Datei:** `.github/CODEOWNERS`

**Kritische Pfade (benötigen Review):**
- `/src/governance/` - Governance & Compliance
- `/src/execution/` - Order Execution
- `/src/risk/` - Risk Management
- `/src/live/` - Live Trading
- `/.github/workflows/` - CI/CD
- `/config/` - Configuration

**Syntax:**
```
# Pfad                      Owner(s)
/src/live/**               @rauterfrank-ui
/src/governance/**         @rauterfrank-ui
```

---

## 🚀 Merge Queue (Optional)

**Aktivieren:** Settings → Pull Requests → Enable Merge Queue

**Verwendung:**
```bash
# CLI
gh pr merge --merge-queue

# UI: "Add to merge queue" Button
```

**Warum Merge Queue?**
- ✅ Eliminiert "broken main" durch Race Conditions
- ✅ Serialisiert Merges automatisch
- ✅ Testet finalen Merge-Commit (nicht nur PR HEAD)

---

## 🔥 Common Workflows

### Neuen PR erstellen
```bash
git checkout -b feature/my-feature
# ... changes ...
git commit -m "feat: my feature"
git push -u origin feature/my-feature
gh pr create --title "feat: My Feature" --body "Description"
```

**Was passiert:**
1. ⚡ Alle P0 Workflows starten automatisch
2. ⏳ Warte auf grüne Checks (~5-15min)
3. 👀 Review von CODEOWNER (falls kritischer Pfad)
4. ✅ Merge via "Squash and merge" oder Merge Queue

---

### Dependency Review blockiert meinen PR

**Problem:** `Dependency Review` schlägt fehl mit "High Severity Vulnerability"

**Lösung:**
```bash
# 1. Identifiziere vulnerable Dependency im PR Check
# 2. Update Dependency
pip install --upgrade <vulnerable-package>

# 3. Sync mit uv.lock
uv pip compile pyproject.toml -o requirements.txt
uv sync

# 4. Commit & Push
git add requirements.txt uv.lock pyproject.toml
git commit -m "chore(deps): update vulnerable dependency"
git push
```

---

### CodeQL findet Security Issue

**Problem:** GitHub Security Alert: "Potential SQL Injection"

**Lösung:**
1. **Alert ansehen:** Security → Code scanning alerts → Details
2. **Code fixen:**
   ```python
   # BAD
   query = f"SELECT * FROM users WHERE id = {user_id}"

   # GOOD
   query = "SELECT * FROM users WHERE id = %s"
   cursor.execute(query, (user_id,))
   ```
3. **Pushen:** CodeQL re-runs automatisch
4. **Alert schließt sich** automatisch bei Fix

**False Positive?**
- Alert als "Dismissed" markieren
- Reason: "False positive - <explanation>"

---

### Policy Critic beschwert sich über große PR

**Problem:** PR hat >250 geänderte Dateien → LITE Mode

**Optionen:**

**Option A: PR splitten (EMPFOHLEN)**
```bash
# Split in kleinere PRs (<250 Files pro PR)
git checkout -b feature/part-1
# cherry-pick commits für Part 1
git push -u origin feature/part-1
```

**Option B: large-pr-approved Label (Falls split nicht möglich)**
```bash
gh pr edit <number> --add-label large-pr-approved
```

**⚠️ Achtung:**
- LITE Mode analysiert nur Subset (prioritiert sensitive Pfade)
- Bei sensitive Pfaden (src/governance, src/execution, etc.) **KEIN Bypass möglich**

---

### Merge Queue steckt fest

**Problem:** PR wartet >30min in Merge Queue

**Diagnose:**
```bash
# Check Status
gh pr view <number> --json statusCheckRollup

# Queue Status
gh api repos/:owner/:repo/merge-queue
```

**Lösungen:**
- **Failed Check:** Check fixen, Queue retried automatisch
- **Merge Conflict:** Rebase auf main
- **Timeout:** Warte oder Admin kann Queue leeren

**Notfall (Admin only):**
```bash
gh pr merge <number> --admin --merge
```

---

## 🔧 Workflow Re-Runs

### Einzelnen Workflow re-runnen
```bash
# Finde Run ID
gh run list --workflow "Dependency Review" --branch my-branch

# Re-run
gh run rerun <run-id>
```

### Alle failed Checks re-runnen
```bash
gh pr checks <number> --required  # Show required checks
gh run rerun <run-id> --failed    # Re-run only failed jobs
```

---

## 📊 Monitoring

### Wöchentliche P0 Health Checks

```bash
# 1. CodeQL Alerts
gh api repos/:owner/:repo/code-scanning/alerts

# 2. Dependabot Alerts
gh api repos/:owner/:repo/dependabot/alerts

# 3. Workflow Success Rate (letzte 30 Tage)
gh run list --workflow ci.yml --created ">$(date -u -d '30 days ago' +%Y-%m-%d)" \
  --json conclusion --jq 'group_by(.conclusion) | map({conclusion: .[0].conclusion, count: length})'
```

**Target Metrics:**
- CodeQL Alerts: 0 HIGH/CRITICAL
- Dependabot Alerts: 0 HIGH/CRITICAL
- Workflow Success Rate: >95%

---

## 🆘 Emergency Procedures

### PRODUCTION IS DOWN - Need Emergency Hotfix

**Normale P0 Regeln gelten IMMER** - keine Exceptions!

**Aber:** Optimiere für Speed:

1. **Minimal Change** - kleinster möglicher Fix
2. **Parallel Review** - Review während CI läuft
3. **Merge Queue Skip** - Direct Merge (wenn Admin)
4. **Post-Mortem** - Danach dokumentieren warum P0 hier hilfreich/hinderlich war

```bash
# Emergency Hotfix PR (Admins only, if Merge Queue enabled)
gh pr create --title "HOTFIX: <issue>" --label emergency
# ... Warte auf P0 Checks (NICHT skippen!) ...
gh pr merge --admin --merge  # Skip Merge Queue if needed
```

**⚠️ Nach Hotfix:**
- Post-Mortem schreiben
- P0 Prozess evaluieren (zu langsam? zu strikt?)

---

## 📚 Documentation

- **Full Setup Guide:** [docs/GITHUB_P0_GUARDRAILS_SETUP.md](docs/GITHUB_P0_GUARDRAILS_SETUP.md)
- **Policy Critic:** [docs/governance/POLICY_CRITIC.md](docs/governance/POLICY_CRITIC.md)
- **GitHub Docs:** [Merge Queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)

---

## ✅ Quick Verification

Nach P0 Setup oder Änderungen:

```bash
# 1. CODEOWNERS existiert
test -f .github/CODEOWNERS && echo "✅ CODEOWNERS" || echo "❌ FEHLT"

# 2. Alle Workflows haben merge_group
for wf in ci.yml lint.yml audit.yml policy_critic.yml deps_sync_guard.yml test_health.yml guard-reports-ignored.yml policy_tracked_reports_guard.yml; do
  grep -q "merge_group" .github/workflows/$wf && echo "✅ $wf" || echo "❌ $wf FEHLT merge_group"
done

# 3. Branch Protection aktiv
gh api repos/:owner/:repo/branches/main/protection >/dev/null && echo "✅ Branch Protection" || echo "❌ FEHLT"

# 4. Test-PR erstellen
gh pr create --title "test: P0 verification" --body "Testing P0 guardrails" --draft
```

---

**Last Updated:** 2025-12-23  
**Maintainer:** @rauterfrank-ui
