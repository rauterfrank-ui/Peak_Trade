# Required Checks Drift Guard v1 - Operator Notes

**Status:** ✅ Implemented  
**Date:** 2025-12-25  
**Version:** v1

---

## 📦 What Was Delivered

### 1. Core Script: `verify_required_checks_drift.sh`
- **Location:** `scripts/ops/verify_required_checks_drift.sh`
- **Purpose:** Verifies Branch Protection Required Checks (doc vs live)
- **Features:**
  - Extracts checks from `docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md`
  - Fetches live checks via `gh` CLI
  - Compares and reports drift (missing/extra checks)
  - Supports `--warn-only` mode (exit 2 instead of 1)
  - CLI flags: `--owner`, `--repo`, `--branch`, `--doc`, `--warn-only`

### 2. Ops Center Integration
- **File:** `scripts/ops/ops_center.sh`
- **Integration Point:** `cmd_doctor()` function
- **Behavior:**
  - Runs drift guard in `--warn-only` mode
  - Shows PASS/WARN/FAIL status
  - Displays short diff summary on drift
  - Included in overall doctor exit code

### 3. Documentation Update
- **File:** `docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md`
- **New Section:** "Automated Drift Guard"
- **Content:**
  - Quick usage guide
  - Exit codes explanation
  - Interpreting WARN vs FAIL
  - Troubleshooting tips

### 4. Smoke Test
- **Location:** `scripts/ops/tests/test_verify_required_checks_drift.sh`
- **Coverage:**
  - Bash syntax check
  - Help output validation
  - Doc extraction logic (offline)
  - No network dependencies
  - 12 test cases

---

## 🚀 How to Use

### Quick Check (Manual)
```bash
cd ~/Peak_Trade
scripts/ops/verify_required_checks_drift.sh
```

**Expected Output (if no drift):**
```
✅ Required Checks: No Drift

📖 Doc matches live state
🔗 rauterfrank-ui/Peak_Trade (main)
📊 Total checks: 8
```

**Expected Output (if drift detected):**
```
🔍 Required Checks Drift Detected

❌ Missing from Live (in doc, not on GitHub):
   - Some Check Name

⚠️  Extra in Live (on GitHub, not in doc):
   - Another Check Name

📖 Doc: docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md
🔗 Live: rauterfrank-ui/Peak_Trade (branch: main)

💡 Action Required:
   Update doc to match live state, or adjust branch protection.
```

### Integrated Check (via Ops Doctor)
```bash
cd ~/Peak_Trade
ops_center.sh doctor
```

The drift guard runs as part of doctor and shows:
- ✅ **PASS** - No drift
- ⚠️ **WARN** - Drift detected (warn-only mode)
- ❌ **FAIL** - Check failed to run (preflight error)

### Warn-Only Mode
```bash
scripts/ops/verify_required_checks_drift.sh --warn-only
```

Exit code: `2` (instead of `1`) on drift. Useful for CI/ops_doctor integration.

---

## 🧪 Testing

### Smoke Test (Offline)
```bash
cd ~/Peak_Trade
scripts/ops/tests/test_verify_required_checks_drift.sh
```

**Expected:** All tests pass (12/12)

### Live Test (Requires gh CLI + network)
```bash
cd ~/Peak_Trade
scripts/ops/verify_required_checks_drift.sh --owner rauterfrank-ui --repo Peak_Trade --branch main
```

**Expected:**
- Exit 0 if doc matches live
- Exit 1 if drift detected

---

## 🛠️ Prerequisites

### Required Tools
1. **gh CLI** (authenticated)
   ```bash
   brew install gh
   gh auth login
   ```

2. **jq** (JSON processor)
   ```bash
   brew install jq
   ```

### Verify Preflight
```bash
gh auth status    # Should show authenticated
command -v jq     # Should show path to jq
```

---

## 📋 Exit Codes

| Code | Meaning | Context |
|------|---------|---------|
| 0    | No drift (match) | Doc and live state identical |
| 1    | Drift detected | Hard fail (or preflight error) |
| 2    | Drift detected (warn-only) | Soft warning in ops_doctor |

---

## 🔍 How It Works

### 1. Doc Extraction
Parses `docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md`:
- Finds section: `## Current Required Checks (main)`
- Extracts numbered list: `1. **Check Name**`
- Uses: `sed` + `grep` (BSD compatible)

### 2. Live Fetch
Queries GitHub API via `gh` CLI:
```bash
gh api "/repos/${OWNER}/${REPO}/branches/${BRANCH}/protection/required_status_checks"
```
Extracts: `.contexts[]` (list of check names)

### 3. Comparison
Uses `comm` to find:
- **Missing:** In doc, not on GitHub
- **Extra:** On GitHub, not in doc

### 4. Report
- Zero drift: ✅ PASS (exit 0)
- Any drift: Show diff + action required (exit 1 or 2)

---

## 🐛 Troubleshooting

### "gh not authenticated"
```bash
gh auth login
```

### "jq not found"
```bash
brew install jq
```

### "No checks found in doc"
- Verify section exists: `## Current Required Checks (main)`
- Check format: `1. **Check Name**`
- Ensure file path: `docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md`

### "Failed to fetch live checks from GitHub"
- Check network connectivity
- Verify repo/branch exist
- Ensure branch protection is configured

### Smoke test fails
```bash
# Run with verbose output
bash -x scripts/ops/tests/test_verify_required_checks_drift.sh
```

---

## 📝 Maintenance

### When to Run
- **After branch protection changes:** Immediately
- **During quarterly audits:** Every 3 months
- **Before major releases:** Part of release checklist
- **In CI:** Via ops_doctor integration

### Updating Doc Format
If you change the doc format, update:
1. `extract_doc_checks()` function in `verify_required_checks_drift.sh`
2. Test in `test_verify_required_checks_drift.sh`

### Adding Custom Checks
1. Update `docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md`
2. Configure on GitHub (via API or UI)
3. Run drift guard to verify sync

---

## 🎯 Integration Points

### 1. Ops Center
- Command: `ops_center.sh doctor`
- Section: "🧭 Required Checks Drift Guard"
- Mode: Warn-only (exit 2)

### 2. Manual Workflow
- Script: `scripts/ops/verify_required_checks_drift.sh`
- Use case: Pre-release checks, audits

### 3. Future CI Integration (Optional)
```yaml
# .github/workflows/ops_doctor.yml
- name: Required Checks Drift Guard
  run: |
    scripts/ops/verify_required_checks_drift.sh --warn-only
```

---

## 📚 Related Documentation

- **Branch Protection Docs:** `docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md`
- **Ops Center Guide:** `docs/ops/OPS_OPERATOR_CENTER.md`
- **Ops Doctor:** `docs/ops/OPS_DOCTOR_README.md`

---

## ✅ Verification Checklist

After implementation, verify:

- [ ] Script exists and is executable
  ```bash
  test -x scripts/ops/verify_required_checks_drift.sh && echo "OK"
  ```

- [ ] Help works
  ```bash
  scripts/ops/verify_required_checks_drift.sh --help
  ```

- [ ] Bash syntax valid
  ```bash
  bash -n scripts/ops/verify_required_checks_drift.sh && echo "OK"
  ```

- [ ] Smoke test passes
  ```bash
  scripts/ops/tests/test_verify_required_checks_drift.sh
  ```

- [ ] Live check works (if gh + jq installed)
  ```bash
  scripts/ops/verify_required_checks_drift.sh
  ```

- [ ] Ops doctor integration works
  ```bash
  ops_center.sh doctor | grep "Required Checks Drift Guard"
  ```

- [ ] Doc section exists
  ```bash
  grep -q "Automated Drift Guard" docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md && echo "OK"
  ```

---

## 🎉 Success Criteria

✅ **Script created and executable**  
✅ **Ops Center integration complete**  
✅ **Documentation updated**  
✅ **Smoke test implemented**  
✅ **Preflight checks included**  
✅ **Exit codes clearly defined**  
✅ **Help output comprehensive**  
✅ **BSD/macOS compatible (sed/grep)**

---

## 📦 Deliverables Summary

| File | Purpose | Status |
|------|---------|--------|
| `scripts/ops/verify_required_checks_drift.sh` | Core drift guard script | ✅ Complete |
| `scripts/ops/ops_center.sh` | Ops Center integration | ✅ Updated |
| `docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md` | Documentation | ✅ Updated |
| `scripts/ops/tests/test_verify_required_checks_drift.sh` | Smoke test | ✅ Complete |
| `REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md` | This file | ✅ Complete |

---

## 🚢 Recommended Commit Message

```
feat(ops): implement Required Checks Drift Guard v1

Automates verification that documented Required Checks match live
GitHub Branch Protection state.

Components:
- scripts/ops/verify_required_checks_drift.sh (core guard)
- scripts/ops/ops_center.sh (doctor integration)
- docs/ops/BRANCH_PROTECTION_REQUIRED_CHECKS.md (drift guard section)
- scripts/ops/tests/test_verify_required_checks_drift.sh (smoke tests)

Features:
- CLI flags: --owner, --repo, --branch, --doc, --warn-only
- Exit codes: 0 (match), 1 (drift), 2 (warn-only drift)
- BSD/macOS compatible (sed/grep, no GNU extensions)
- Integrated into ops_doctor workflow
- Offline smoke tests (12 test cases)

Usage:
  scripts/ops/verify_required_checks_drift.sh
  ops_center.sh doctor

See: REQUIRED_CHECKS_DRIFT_GUARD_v1_OPERATOR_NOTES.md
```

---

## 📧 PR Title Suggestion

```
feat(ops): Required Checks Drift Guard v1 - auto-verify branch protection sync
```

**Labels:** `ops`, `tooling`, `automation`, `P1`

---

**End of Operator Notes**
