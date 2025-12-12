# Policy Critic Telemetry Log (G4)

## Purpose

This log tracks real-world PR outcomes from the Policy Critic gate to:
- Monitor false positive/negative rates
- Identify patterns requiring pack tuning
- Validate fail-closed behavior in production
- Build empirical data for G5+ improvements

## Log Format

Each entry includes:
- **PR ID & Date**
- **Result:** Initial outcome (PASS/WARN/BLOCK) and final resolution
- **Severity:** Max severity detected
- **Rules triggered:** Which rules fired
- **Root cause:** What the PR was actually trying to do
- **False positive?:** Yes/No + explanation
- **Remediation:** How it was resolved
- **Notes:** Lessons learned, patterns observed

---

## PR #4 — 2025-12-12

- **Result:** BLOCK (initial) → PASS (after fix)
- **Severity:** BLOCK
- **Rule:** RISK_LIMIT_RAISE_WITHOUT_JUSTIFICATION
- **Root cause:** tmp/policy_critic_cycles/* test artifacts committed; contained simulated risk-limit patterns
- **False positive?:** Yes - test output files were scanned as if they were real config changes
- **Remediation:**
  - Removed tmp artifacts from VCS (git rm -r --cached tmp/policy_critic_cycles)
  - Added tmp/ to .gitignore
  - Commit: c7307bc
- **Notes:**
  - Confirms fail-closed behavior works correctly (rule detected pattern as designed)
  - Scope hygiene prevents false positives (exclude test artifacts from scanning)
  - Consider adding path exclusions in future (e.g., tmp/, tests/fixtures/)
  - PR was policy pack tuning itself, so meta-testing confirmed gate works

---

## Summary Statistics

- **Total PRs:** 1
- **BLOCK:** 1 (100%)
- **WARN:** 0 (0%)
- **PASS:** 0 (0%)
- **False positives:** 1 (100%)
- **False negatives:** 0 (0%)
- **Legitimate blocks:** 0 (0%)

**Action items:**
- [ ] Add path exclusion logic for tmp/, tests/fixtures/, docs/examples/
- [ ] Monitor next 10 PRs for pattern validation
