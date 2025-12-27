# Required Checks Drift Guard — PR Workflow System Summary

**Created:** 2025-12-25  
**Status:** ✅ Complete  
**Type:** Ops Automation + Governance

---

## 🎯 Überblick

Vollständiges PR-Workflow-System für den **Required Checks Drift Guard**, das automatisch PRs erstellt, Tests ausführt und Drift zwischen dokumentierten und Live-GitHub-Required-Checks erkennt.

---

## 📦 Komponenten

### Core Workflow Scripts
```
scripts/ops/
├── create_required_checks_drift_guard_pr.sh  # Main PR workflow
│   ├── Phase 1: Offline Checks (verify + doctor + pytest)
│   ├── Phase 2: Live Drift Check (optional, gh+jq)
│   ├── Phase 3: Commit + Push + PR
│   └── Phase 4: Labels + CI Watch
│   └── Flags: --dry-run, --offline-only
│
├── run_required_checks_drift_guard_pr.sh     # Intelligent wrapper/finder
│   └── Auto-detects main script, passes flags through
│
├── setup_drift_guard_pr_workflow.sh          # One-time setup script
│   ├── Creates/updates all workflow scripts
│   ├── Adds flags support
│   ├── Creates smoke tests
│   ├── Generates documentation
│   └── Updates README_REGISTRY.md
│
├── DRIFT_GUARD_ONE_LINER.sh                  # Ultra-quick setup + test
│   └── Copy/paste friendly complete setup
│
└── verify_required_checks_drift.sh           # Core drift detection
    └── Existing (already implemented)
```

### Test Suite
```
scripts/ops/tests/
├── test_drift_guard_pr_workflow.sh           # NEW: PR workflow smoke tests
│   ├── Test 1: Wrapper script exists
│   ├── Test 2: Main script exists
│   ├── Test 3: Wrapper can find main script
│   ├── Test 4: --help works
│   ├── Test 5: --dry-run flag supported
│   ├── Test 6: --offline-only flag supported
│   ├── Test 7: verify script exists
│   └── Test 8: Documentation exists
│
└── test_verify_required_checks_drift.sh      # Existing verify tests
```

### Documentation
```
docs/ops/
├── DRIFT_GUARD_QUICK_START.md                # NEW: Quick reference guide
│   ├── One-liner setup
│   ├── Testing commands (dry-run)
│   ├── Production run
│   ├── Flags reference
│   └── Troubleshooting
│
├── REQUIRED_CHECKS_DRIFT_GUARD.md            # NEW: Main guide
│   ├── Integration overview
│   ├── Exit codes
│   ├── Operator workflows
│   └── Architecture diagram
│
└── REQUIRED_CHECKS_DRIFT_GUARD_PR_WORKFLOW.md # Existing: Detailed workflow
    ├── Phase breakdown
    ├── Environment variables
    └── Examples

REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md # Existing: Root-level notes

DRIFT_GUARD_PR_WORKFLOW_SUMMARY.md            # NEW: This file (summary)
```

---

## 🚀 Quick Start (Copy/Paste)

### Option 1: One-Liner (Empfohlen)
```bash
cd ~/Peak_Trade && bash scripts/ops/DRIFT_GUARD_ONE_LINER.sh
```

Führt aus:
- ✅ Setup (falls erforderlich)
- ✅ Smoke Tests
- ✅ Dry-Run (offline only)

### Option 2: Full Setup
```bash
cd ~/Peak_Trade && bash scripts/ops/setup_drift_guard_pr_workflow.sh
```

Erstellt:
- ✅ Alle Workflow-Scripts
- ✅ Smoke Tests
- ✅ Dokumentation
- ✅ Commits changes

### Option 3: Manual Steps
```bash
# 1. Test (dry-run, offline)
scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run --offline-only

# 2. Test (dry-run, with live check)
scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run

# 3. Create PR (production)
scripts/ops/run_required_checks_drift_guard_pr.sh
```

---

## 🧪 Testing Strategy

### Level 1: Smoke Tests (schnell, offline)
```bash
scripts/ops/tests/test_drift_guard_pr_workflow.sh
```
- Prüft, ob alle Skripte existieren und ausführbar sind
- Validiert Flags und Help-Output
- Keine Git/Network-Operations

### Level 2: Dry-Run Offline (safe, keine Git-Ops)
```bash
scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run --offline-only
```
- Führt nur Offline-Checks aus
- Kein `gh`/`jq` erforderlich
- Keine Git-Operationen (commit/push/PR)

### Level 3: Dry-Run Full (safe, mit Live-Check)
```bash
scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run
```
- Offline + Live Drift Check
- Benötigt `gh` + `jq` + Auth
- Keine Git-Operationen

### Level 4: Production (full workflow)
```bash
scripts/ops/run_required_checks_drift_guard_pr.sh
```
- Alle Checks (offline + live)
- Git: Commit + Push + PR
- CI Watch

---

## 🔧 Flags Reference

| Flag | Beschreibung | Git Ops | Live Check | Use Case |
|------|--------------|---------|------------|----------|
| (none) | Full production run | ✅ | ✅ | Create PR |
| `--dry-run` | Test without git ops | ❌ | ✅ | Pre-flight check |
| `--offline-only` | Skip live check | (depends) | ❌ | Offline dev |
| `--dry-run --offline-only` | Safe offline test | ❌ | ❌ | Quick smoke test |

---

## 📊 Exit Codes

### create_required_checks_drift_guard_pr.sh
- `0` — ✅ Success (all checks passed, PR created or dry-run successful)
- `1` — ❌ Error (checks failed or git operation failed)
- `2` — ⚠️ Drift detected (warn-only mode, not used in PR script)

### verify_required_checks_drift.sh (when called with --live --warn-only)
- `0` — ✅ No drift (Doc == Live)
- `2` — ⚠️ Drift detected (warn-only, review required but not fatal)
- `1` — ❌ Error (Preflight: gh/jq/auth problem)

---

## 🔗 Integration Points

### 1. Ops Center (ops_center.sh doctor)
```bash
scripts/ops/ops_center.sh doctor
```
- Führt `verify_required_checks_drift.sh --warn-only` aus
- Zeigt Drift-Status in Health-Check-Ausgabe
- Non-blocking (exit 2 wird als warning behandelt)

### 2. CI/CD Workflows
```yaml
# .github/workflows/ops-checks.yml
- name: Required Checks Drift Guard
  run: |
    scripts/ops/verify_required_checks_drift.sh --live --warn-only
```

### 3. Pre-Commit Hook (optional)
```bash
# .git/hooks/pre-commit
#!/bin/bash
scripts/ops/verify_required_checks_drift.sh --offline
```

### 4. PR Workflow (Manual)
```bash
scripts/ops/run_required_checks_drift_guard_pr.sh
```

---

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Operator Entry Points                     │
├─────────────────────────────────────────────────────────────┤
│  • DRIFT_GUARD_ONE_LINER.sh (setup + smoke + dry-run)      │
│  • setup_drift_guard_pr_workflow.sh (one-time setup)       │
│  • run_required_checks_drift_guard_pr.sh (wrapper)         │
│  • ops_center.sh doctor (health check)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│             create_required_checks_drift_guard_pr.sh        │
├─────────────────────────────────────────────────────────────┤
│  Phase 1: Offline Checks                                    │
│    ├─> verify_required_checks_drift.sh --offline           │
│    ├─> ops_center.sh doctor (optional)                     │
│    └─> pytest (optional)                                   │
│                                                             │
│  Phase 2: Live Drift Check (optional, --offline-only skips)│
│    └─> verify_required_checks_drift.sh --live --warn-only  │
│                                                             │
│  Phase 3: Git Operations (--dry-run skips)                 │
│    ├─> git commit (if changes)                             │
│    ├─> git push                                            │
│    └─> gh pr create                                        │
│                                                             │
│  Phase 4: PR Management (--dry-run skips)                  │
│    ├─> gh pr edit --add-label                              │
│    └─> gh pr checks --watch                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 Documentation Index

### Quick Reference
- `docs/ops/DRIFT_GUARD_QUICK_START.md` — **Start here!** Copy/paste commands

### Deep Dives
- `docs/ops/REQUIRED_CHECKS_DRIFT_GUARD.md` — Main guide (integration, workflows)
- `docs/ops/REQUIRED_CHECKS_DRIFT_GUARD_PR_WORKFLOW.md` — Detailed PR workflow
- `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md` — Operator notes

### Reference
- `docs/ops/OPS_OPERATOR_CENTER.md` — Ops Center overview
- `README_REGISTRY.md` — All project documentation

---

## 🐛 Common Issues

### 1. "❌ gh fehlt"
```bash
brew install gh
gh auth login
```

### 2. "❌ jq fehlt"
```bash
brew install jq
```

### 3. "❌ Konnte kein passendes Script finden"
```bash
# Ensure scripts are committed
git add scripts/ops/*.sh
git commit -m "feat(ops): add drift guard scripts"
```

### 4. "⚠️ Drift detected (warn-only)"
**Not an error!** Zwei Optionen:

**Option A: Update Docs** (wenn Live-State korrekt)
```bash
# Edit: REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md
# Add/remove checks to match GitHub Branch Protection
```

**Option B: Update Branch Protection** (wenn Docs korrekt)
```bash
# GitHub UI: Settings > Branches > Branch Protection Rules
# Adjust "Required status checks"
```

### 5. Dry-Run funktioniert nicht
```bash
# Check script permissions
ls -la scripts/ops/*drift*.sh

# Make executable
chmod +x scripts/ops/*.sh
```

---

## 🎓 Learning Path

### Beginner
1. Read: `docs/ops/DRIFT_GUARD_QUICK_START.md`
2. Run: `scripts/ops/DRIFT_GUARD_ONE_LINER.sh`
3. Run: `scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run --offline-only`

### Intermediate
1. Read: `docs/ops/REQUIRED_CHECKS_DRIFT_GUARD.md`
2. Run: `scripts/ops/run_required_checks_drift_guard_pr.sh --dry-run`
3. Inspect: `scripts/ops/create_required_checks_drift_guard_pr.sh`

### Advanced
1. Read: `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md`
2. Customize: Environment variables + flags
3. Integrate: Add to CI/CD + pre-commit hooks

---

## 📈 Metrics & Success Criteria

### Setup Success
- ✅ All scripts executable
- ✅ Smoke tests pass (8/8)
- ✅ Documentation generated
- ✅ README_REGISTRY updated

### Runtime Success (Dry-Run)
- ✅ Offline checks pass
- ✅ Live check returns 0 or 2 (not 1)
- ✅ No exceptions or crashes

### Runtime Success (Production)
- ✅ PR created successfully
- ✅ Labels applied
- ✅ CI checks triggered

---

## 🚀 Future Enhancements

### Short Term
- [ ] Add `--verbose` flag for detailed output
- [ ] Add JSON output mode for programmatic use
- [ ] Add Slack/email notifications on drift

### Medium Term
- [ ] Auto-create PR to fix drift (with approval)
- [ ] Dashboard integration (Ops Doctor UI)
- [ ] Historical drift tracking

### Long Term
- [ ] AI-powered drift resolution suggestions
- [ ] Multi-repo drift monitoring
- [ ] Drift trend analysis

---

## 📞 Support

### Quick Help
```bash
# Get help
scripts/ops/run_required_checks_drift_guard_pr.sh --help
scripts/ops/create_required_checks_drift_guard_pr.sh --help

# Run diagnostics
scripts/ops/ops_center.sh doctor

# Run tests
scripts/ops/tests/test_drift_guard_pr_workflow.sh
```

### Documentation
- Start: `docs/ops/DRIFT_GUARD_QUICK_START.md`
- Details: `docs/ops/REQUIRED_CHECKS_DRIFT_GUARD.md`
- Ops: `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md`

### Community
- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Ops Team: Slack #ops-automation

---

## ✅ Completion Checklist

### Files Created/Updated
- ✅ `scripts/ops/create_required_checks_drift_guard_pr.sh` (updated with flags)
- ✅ `scripts/ops/run_required_checks_drift_guard_pr.sh` (updated with pass-through)
- ✅ `scripts/ops/setup_drift_guard_pr_workflow.sh` (new)
- ✅ `scripts/ops/DRIFT_GUARD_ONE_LINER.sh` (new)
- ✅ `scripts/ops/tests/test_drift_guard_pr_workflow.sh` (new)
- ✅ `docs/ops/DRIFT_GUARD_QUICK_START.md` (new)
- ✅ `docs/ops/REQUIRED_CHECKS_DRIFT_GUARD.md` (new)
- ✅ `docs/ops/REQUIRED_CHECKS_DRIFT_GUARD_PR_WORKFLOW.md` (existing, referenced)
- ✅ `DRIFT_GUARD_PR_WORKFLOW_SUMMARY.md` (new, this file)

### Integration Points
- ✅ Ops Center (`ops_center.sh doctor`)
- ✅ Smoke Tests (auto-run in setup)
- ✅ README Registry (auto-update in setup)
- ✅ Dry-Run Support (`--dry-run`, `--offline-only`)

### Testing
- ✅ Smoke tests implemented (8 tests)
- ✅ Dry-run mode (offline + full)
- ✅ All scripts executable
- ✅ Help output available

### Documentation
- ✅ Quick Start Guide (copy/paste friendly)
- ✅ Main Guide (comprehensive)
- ✅ Troubleshooting section
- ✅ Examples for all use cases

---

**System Status:** ✅ Production Ready  
**Next Action:** Run one-liner setup or test dry-run mode  
**Maintained by:** Peak_Trade Ops Team  
**Last Updated:** 2025-12-25

