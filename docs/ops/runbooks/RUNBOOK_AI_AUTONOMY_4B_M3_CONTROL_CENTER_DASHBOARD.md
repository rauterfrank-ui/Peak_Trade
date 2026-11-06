# RUNBOOK — AI Autonomy (Phase 4B · Milestone 3)
## Control Center Dashboard: Local Viewing & PR/CI Monitoring (No-Watch)

**Status:** Operator-ready (v0.1)  
**Scope:** Docs-only  
**Risk:** LOW (view-only operations, no code/config changes)  
**Owner:** Ops / AI Autonomy  
**Last updated:** 2026-01-09

---

## 0) Purpose & Guardrails

### Purpose
This runbook provides standardized procedures for:
1. Viewing the AI Autonomy Control Center Dashboard locally
2. Monitoring PR and CI status WITHOUT using `--watch` flags (which frequently time out)
3. Capturing evidence for audit and closeout

### Guardrails (Non-negotiable)
- **Evidence-first:** All statements reference concrete artifacts, logs, or docs
- **No-live / Governance-locked:** No live trading, no production changes, no secrets handling
- **Deterministic operations:** Steps are repeatable and produce predictable outputs
- **No production changes:** Dashboard viewing is read-only; no execution paths triggered

### Non-Goals
- Dashboard implementation or modification (covered in separate development runbooks)
- Automated CI triggers or merges (operator monitors; automation is controlled via PR settings)
- Real-time alerting or pager integration

---

## 1) Inputs & Prerequisites

### Required Tools
- Git (repository access)
- GitHub CLI (`gh`) — version 2.0+
- Web browser (for viewing HTML dashboards or GitHub UI)
- Python 3.x (optional, for local HTTP server)

### Prerequisites
**A) Repository checkout:**
```bash
cd /Users/frnkhrz/Peak_Trade  # or your local path
git rev-parse --show-toplevel
# Expected output: /Users/frnkhrz/Peak_Trade (or equivalent)
```

**B) Correct branch context:**
```bash
git status -sb
# Verify you are on the intended branch or main
```

**C) GitHub CLI authentication:**
```bash
gh auth status
# Expected: "Logged in to github.com"
```

---

## 2) Artifacts & Locations

### Dashboard Artifacts (Post-Merge)
Locate dashboard documentation via:
```bash
# Navigate to AI Autonomy Control Center documentation
ls -la docs/ops/control_center/

# Expected files (example):
# - AI_AUTONOMY_CONTROL_CENTER.md (primary dashboard doc)
# - CONTROL_CENTER_NAV.md (navigation index)
# - *.html (if static HTML dashboard exists)
```

**To confirm artifacts exist:**
```bash
# Check for Control Center docs
find docs/ops/control_center -name "*.md" -o -name "*.html" | head -10

# Check for runbooks
ls -la docs/ops/runbooks/RUNBOOK_AI_AUTONOMY_*
```

### Expected File Types
- **Markdown (*.md):** Primary documentation format
- **HTML (*.html):** Optional static dashboards (if implemented)
- **JSON (*.json):** Evidence packs, CI status snapshots (if present)

---

## 3) Operating Procedure — Local Dashboard View

### Method A: View Markdown Documentation

**Step 1 — Open Control Center primary doc:**
```bash
# Option 1: Using system default editor/viewer
open docs/ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md

# Option 2: Using specific editor
code docs/ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md  # VS Code
vim docs/ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md   # Vim
```

**Step 2 — Verify sanity checks:**
- [ ] Document renders correctly (headers, tables, links visible)
- [ ] "No-Live" or governance guardrails explicitly stated
- [ ] Timestamp/version information present
- [ ] Navigation links point to valid relative paths
- [ ] Layer status matrix visible (L0-L6)

### Method B: View HTML Dashboard (If Present)

**Step 1 — Locate HTML artifact:**
```bash
find docs/ops/control_center -name "*.html" -type f
# If found: note path (e.g., docs/ops/control_center/dashboard.html)
```

**Step 2 — Open in browser (static file):**
```bash
# Direct file open
open docs/ops/control_center/dashboard.html  # macOS
xdg-open docs/ops/control_center/dashboard.html  # Linux

# Or drag file into browser window
```

**Step 3 — Verify sanity checks:**
- [ ] Page loads without errors (check browser console: F12)
- [ ] All sections render (KPIs, layer matrix, quick actions, runbooks)
- [ ] Links are functional (internal navigation, external docs)
- [ ] Timestamp/version footer visible

### Method C: Local HTTP Server (For Complex HTML)

**When to use:** If HTML dashboard has relative resource links (CSS/JS/images) that require HTTP context.

**Step 1 — Start local server:**
```bash
cd docs/ops/control_center
python3 -m http.server 8080
# Expected output: "Serving HTTP on 0.0.0.0 port 8080"
```

**Step 2 — Open in browser:**
```bash
open http://localhost:8080/dashboard.html
# Or navigate manually: http://localhost:8080/
```

**Step 3 — Stop server when done:**
```bash
# In the terminal running server: Ctrl-C
```

**Sanity checks (same as Method B)**

---

## 4) PR / CI Monitoring WITHOUT --watch (Timeout-Safe)

### Problem Statement
GitHub CLI `--watch` flags (e.g., `gh pr checks --watch`, `gh run watch`) frequently time out or hang in long-running CI pipelines. This section provides timeout-safe alternatives using manual polling.

---

### Method 1: Poll PR Checks (Recommended for Quick Status)

**Command:**
```bash
gh pr checks <PR_NUMBER>
```

**Example:**
```bash
gh pr checks 625
```

**Output interpretation:**
- **All checks passing:** Exit code 0, "All checks successful"
- **Some failing:** Exit code 1, shows failing check names
- **Pending:** Exit code 8, "Some checks are still pending"

**Recommended polling cadence:**
- Initial check: Immediately after PR creation
- Follow-up: Every 60-90 seconds for first 5 minutes
- Extended: Every 3-5 minutes if CI is known to run long

**What to capture for evidence:**
```bash
# Snapshot all checks to file
gh pr checks <PR_NUMBER> > pr_<PR_NUMBER>_checks_$(date +%Y%m%d_%H%M%S).txt
```

---

### Method 2: List Recent Runs + Inspect Specific Run

**Step 1 — List recent workflow runs:**
```bash
gh run list --limit 10
# Shows: status, branch, workflow name, run ID, elapsed time
```

**Step 2 — Filter by branch (if needed):**
```bash
gh run list --branch docs/ai-autonomy-4b-m3-control-center-operations-runbook --limit 5
```

**Step 3 — View specific run details:**
```bash
gh run view <RUN_ID>
# Shows: jobs, steps, status, timing
```

**Step 4 — View logs for failed jobs only:**
```bash
gh run view <RUN_ID> --log-failed
# Saves time by showing only failed job logs
```

**Recommended polling cadence:**
- Initial check: After `git push`
- Follow-up: Every 2-3 minutes until run completes

---

### Method 3: JSON Output for Programmatic Parsing

**Command:**
```bash
gh pr view <PR_NUMBER> --json statusCheckRollup,mergeStateStatus
```

**Example:**
```bash
gh pr view 625 --json statusCheckRollup,mergeStateStatus | python3 -m json.tool
```

**Output fields:**
- `statusCheckRollup`: Array of all checks with state (SUCCESS, FAILURE, PENDING)
- `mergeStateStatus`: Overall merge readiness (CLEAN, BLOCKED, UNSTABLE)

**Use case:** Scripted monitoring or capturing structured evidence for audit

---

### Common Failure Modes & Next Actions

| Symptom | Likely Cause | Operator Action |
|---------|--------------|-----------------|
| Check pending >10 min | CI queue congestion or job hang | View run logs (`gh run view --log`), check GitHub Actions UI for queue status |
| "Reference targets" fail | Broken doc links or bare paths interpreted as files | See troubleshooting section 6.1 |
| "Policy critic" fail | Governance rule violation or config drift | Review policy critic output, escalate to governance owner |
| All checks timeout | GitHub Actions outage or rate limit | Check GitHub status page, retry after cooldown |
| PR not mergeable (BLOCKED) | Missing required reviews or checks | Verify branch protection rules, request review |

**Decision tree:**
1. Check exits with error? → Inspect specific job logs (`gh run view <ID> --log-failed`)
2. Check stuck pending? → Wait 5 min, then retry list/view commands
3. Multiple failures? → Create issue with evidence snapshot, escalate

---

## 5) Troubleshooting: "watch times out"

### Symptoms
- `gh pr checks --watch` or `gh run watch` hangs without output
- Terminal becomes unresponsive or shows no progress updates
- Commands exit with timeout error after extended wait

### Root Causes
- GitHub API rate limiting
- Long-running CI jobs (>5 minutes per job)
- Network interruptions during watch session
- GitHub Actions queue delays

### Mitigations

**M1 — Avoid --watch entirely (primary recommendation):**
```bash
# INSTEAD OF:
gh pr checks <PR> --watch  # DO NOT USE

# USE:
gh pr checks <PR>  # Run once, manually re-run every 60-90s
```

**M2 — Browser refresh pattern:**
```bash
# Open PR in browser
gh pr view <PR> --web

# Manually refresh page every 1-2 minutes
# GitHub UI shows real-time check updates
```

**M3 — Inspect single job directly:**
```bash
# If you know a specific job is slow:
gh run list --limit 5
gh run view <RUN_ID>  # Shows job-level status
gh run view <RUN_ID> --log --job <JOB_ID>  # Streams specific job log
```

**M4 — Use GitHub Actions UI (web fallback):**
```bash
# Navigate to Actions tab
open https://github.com/rauterfrank-ui/Peak_Trade/actions

# Filter by branch, click run, view logs directly in browser
```

### Decision Tree: When to Retry vs Stop

```
Check hangs or times out
  |
  ├─> Timeout <2 min? → Retry once immediately
  |
  ├─> Timeout 2-5 min? → Switch to browser UI (gh pr view --web)
  |
  └─> Timeout >5 min? → Stop watch, use polling (gh pr checks every 2-3 min)

Check shows "pending" for >10 min
  |
  ├─> Other PRs also pending? → GitHub Actions queue issue, wait
  |
  └─> Only this PR pending? → Inspect run logs (gh run view --log-failed)
```

---

## 6) Evidence & Closeout

### Evidence to Capture (Post-Merge)

**A) PR metadata:**
```bash
gh pr view <PR_NUMBER> --json number,title,state,mergedAt,mergeCommit > pr_<PR_NUMBER>_metadata.json
```

**B) Final CI status:**
```bash
gh pr checks <PR_NUMBER> > pr_<PR_NUMBER>_final_checks.txt
```

**C) Merge commit SHA:**
```bash
git log -1 --oneline <merge_commit_sha>
# Record SHA in closeout notes
```

**D) Artifacts list (changed files):**
```bash
gh pr view <PR_NUMBER> --json files | python3 -m json.tool > pr_<PR_NUMBER>_files.json
```

### Closeout Checklist (Operator)

Post-merge verification:
- [ ] PR merged successfully (check PR state: MERGED)
- [ ] Merge commit SHA recorded
- [ ] All CI checks passed (final snapshot captured)
- [ ] Dashboard artifacts present in merged branch (verify via `git ls-files`)
- [ ] No follow-up issues created during merge
- [ ] Evidence files stored in appropriate location (e.g., `docs/ops/evidence/`)

**Optional:** Record notes in operator log template:
```markdown
### AI Autonomy — Operator Closeout (Kurzbericht)

Datum: YYYY-MM-DD
PR: #<PR_NUMBER>
Merge Commit: <SHA>

#### CI Status (Final)
- All checks: PASS / FAIL
- Evidence: pr_<PR_NUMBER>_final_checks.txt

#### Artifacts Verified
- Dashboard docs: docs/ops/control_center/ (present)
- Runbooks: docs/ops/runbooks/ (present)

#### Notes
- (any deviations, issues, or follow-ups)
```

---

## 7) Reference Commands (Quick Copy/Paste)

### Repository Verification
```bash
cd /Users/frnkhrz/Peak_Trade
pwd
git rev-parse --show-toplevel
git status -sb
```

### Dashboard Viewing
```bash
# Markdown
open docs/ops/control_center/AI_AUTONOMY_CONTROL_CENTER.md

# HTML (if present)
open docs/ops/control_center/dashboard.html

# Local server
cd docs/ops/control_center && python3 -m http.server 8080
```

### PR/CI Monitoring (No-Watch)
```bash
# Quick status
gh pr checks <PR_NUMBER>

# List runs
gh run list --limit 10

# View specific run
gh run view <RUN_ID>

# Failed logs only
gh run view <RUN_ID> --log-failed

# JSON snapshot
gh pr view <PR_NUMBER> --json statusCheckRollup,mergeStateStatus | python3 -m json.tool
```

### Evidence Capture
```bash
# PR metadata
gh pr view <PR_NUMBER> --json number,title,state,mergedAt,mergeCommit > pr_metadata.json

# Final checks
gh pr checks <PR_NUMBER> > pr_final_checks.txt

# Files changed
gh pr view <PR_NUMBER> --json files | python3 -m json.tool > pr_files.json
```

---

## 8) Change Log

### v0.1 (2026-01-09)
- Initial runbook for Control Center Dashboard operations
- Focus on no-watch PR/CI monitoring to avoid timeout issues
- Added local dashboard viewing procedures (Markdown, HTML, HTTP server)
- Troubleshooting section for watch timeouts
- Evidence capture and closeout procedures
