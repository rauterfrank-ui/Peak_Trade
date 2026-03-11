# Wave 29 — Live PR/Check Reality Scan

**Stand:** 2026-03-11  
**Branch:** feat/full-scan-wave29-required-contexts-proof-review  
**Mode:** Proof-only; evidence from GitHub API

---

## 1. Branch Protection Required Contexts (Evidence)

**Source:** `gh api repos/rauterfrank-ui/Peak_Trade/branches/main/protection`  
**Timestamp:** 2026-03-11

### Actual GitHub Branch Protection Required Contexts (9)

| # | Context Name |
|---|--------------|
| 1 | Guard tracked files in reports directories |
| 2 | audit |
| 3 | tests (3.11) |
| 4 | strategy-smoke |
| 5 | Policy Critic Gate |
| 6 | Lint Gate |
| 7 | dispatch-guard |
| 8 | docs-token-policy-gate |
| 9 | docs-reference-targets-gate |

**Note:** `PR Gate` is **NOT** in the branch protection required contexts list.

---

## 2. Config vs Reality Discrepancy

| Source | Required Contexts |
|-------|------------------|
| `config/ci/required_status_checks.json` | `["PR Gate"]` only |
| GitHub Branch Protection API | 9 contexts (see above); **PR Gate not included** |

**Finding:** The repo config and docs state that only "PR Gate" is required for branch protection. The actual GitHub branch protection settings require **9 different checks**, and **PR Gate is not among them**. This is a significant docs/config-to-reality gap.

---

## 3. Check-Runs Observed on main HEAD

**Source:** `gh api repos/.../commits/<main_sha>/check-runs`  
**Commit:** 2ea37f640a57ad7e1b501c2508ab0e5919ede516 (origin/main at scan time)

### Consistently Appearing PR-Critical Checks

- Guard tracked files in reports directories
- audit
- tests (3.9), tests (3.10), tests (3.11)
- strategy-smoke
- Policy Critic Gate
- Lint Gate
- dispatch-guard
- docs-token-policy-gate
- docs-reference-targets-gate
- required-checks-hygiene-gate
- ci-required-contexts-contract
- Fast-Lane
- Evidence Validator
- PR Gate (produced by ci.yml; not in branch protection)

### Skipped / Informational

- CI Health Gate (weekly_core) — skipped on push
- Generate Trend Seed / Generate Trend Ledger — skipped
- Manual Health Check, R&D Experimental, Daily Quick, Weekly Core — skipped

---

## 4. Summary

- **Branch protection** enforces 9 required checks; none is "PR Gate".
- **Config** claims only "PR Gate" is required.
- **Docs** (CI.md, GATES_OVERVIEW) state "Nur PR Gate ist required" / "Branch protection: require only PR Gate".
- **Reality:** GitHub enforces 9 checks; PR Gate is produced by CI but not in branch protection.
- **required-checks-hygiene-gate** validates config (PR Gate) against workflows; it does not validate branch protection settings.
