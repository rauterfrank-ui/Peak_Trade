# PR #605 — Audit Dependency Remediation + Makefile Fix

**Merged:** 2026-01-07T22:35:00Z (approx)  
**Commit:** `59fa5eb4`  
**Status:** ✅ Merged to main (squash)

---

## Summary

- **Remediated 2 pip-audit security vulnerabilities** (urllib3, wheel)
- **Fixed Makefile audit target** pointing to non-existent `scripts/run_audit.sh` → correct `scripts/ops/run_audit.sh`
- **Enhanced audit script** with summary output and pip-audit invocation
- **Fixed docs reference** to avoid stale path in documentation (unblocked docs-reference-targets-gate)

**Scope:** Security remediation + build tooling fix.

---

## Why

**Motivation:** Address pip-audit findings and fix broken Makefile target preventing local audit execution.

**Context:**
- pip-audit flagged urllib3 <2.6.3 (CVE) and wheel <0.38.1 (security advisory)
- Makefile `audit` target referenced wrong script path
- docs-reference-targets-gate caught stale script path reference in documentation

**Goal:** security posture + working local audit workflow.

---

## Changes

### Files Changed (6)

1. **`pyproject.toml`** (2 lines)
   - `urllib3>=2.6.2,<3` → `urllib3>=2.6.3,<3`
   - `requires = ["setuptools>=61.0", "wheel"]` → `requires = ["setuptools>=61.0", "wheel>=0.38.1"]`

2. **`requirements.txt`** (1 line)
   - `urllib3==2.6.2` → `urllib3==2.6.3`
   - Auto-regenerated via `uv export`

3. **`uv.lock`** (20 lines)
   - Updated urllib3 and wheel lock entries

4. **`Makefile`** (1 line)
   - Fixed audit target: `./scripts/run_audit.sh` → `./scripts/ops/run_audit.sh`

5. **`scripts/ops/run_audit.sh`** (26 lines modified)
   - Added summary output on success
   - Added pip-audit invocation
   - Enhanced error handling

6. **`docs/ops/AUDIT_DEPENDENCY_REMEDIATION_2026-01-07.md`** (171 lines, NEW)
   - Complete remediation documentation
   - Fixed stale script path reference (unblocked docs-reference-targets-gate)

---

## Verification

### CI Status (19/19 passing)

✅ **All checks passed:**
- Audit/audit Lint/lint, Lint Gate — pass
- Policy Critic Gate — 1m17s
- Docs Reference Targets Gate — 5s (was failing, now fixed)
- Docs Reference Targets Trend — 11s
- Docs Diff Guard Policy Gate — pass
- CI/tests (3.9, 3.10, 3.11) — all pass
- CI/strategy-smoke — 1m24s
- Quarto Smoke Test, Recon Audit Gate, Test Health Automation — all pass

### Local Verification
- `make audit` now works (previously broken)
- `./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main` — pass (5 references, all exist)
- No stale path references: `rg "scripts/run_audit\.sh"` in docs — clean

---

## Evidence Trail

- **PR:** [#605](https://github.com/rauterfrank-ui/Peak_Trade/pull/605)
- **Branch:** `fix/audit-remediation-pip-audit-20260107`
- **CI Run (final):** https://github.com/rauterfrank-ui/Peak_Trade/actions/runs/20795354684
- **Docs Gate Fix Commit:** `57013f53` (removed stale script path reference)
- **Merge Commit:** `59fa5eb4` (squash)

---

## Impact

**Security:** 2 vulnerabilities reE, wheel advisory).  
**Developer Experience:** `make audit` target now functional.  
**Documentation Quality:** Stale references removed, docs-reference-targets-gate passing.  
**CI Hygiene:** All 19 checks green, no regressions.

---

**Merged by:** frnkhrz  
**Reviewed by:** CI automation (all gates passed)
