# Policy Pack Tuning Log (G3.6)

## Change Set 1

* **Date:** 2025-12-12
* **Motivation:** Based on G3.5 synthetic cycles (commit 405503d), improve operator UX and strengthen enforcement for critical paths without introducing false positives
* **Packs touched:** `ci.yml` (documentation update)
* **Changes:**
  * **severity_overrides:** None (no changes to severity levels)
  * **critical_paths:** None (kept existing paths)
  * **required_context_keys:** Documentation updated to clarify test_plan requirements
  * **evidence formatting / operator UX:**
    * **Violation deduplication:** Implemented `_dedupe_violations()` in `PolicyCritic` to merge duplicate rule violations (e.g., RISK_LIMIT_RAISE_WITHOUT_JUSTIFICATION appearing 2× for old+new values)
      - Groups by (rule_id, message), combines evidence, shows count: "(2 occurrences)"
      - Reduces noise in operator reports: Cycle 4 now shows "1 violation" instead of "2 violations"
    * **Lower threshold for highly critical paths:** Updated `MissingTestPlanRule`
      - New `HIGH_CRITICAL_PATHS` list: src/live/, src/execution/, src/exchange/, config/live, config/production
      - Threshold: 10 lines (down from 50) for highly critical paths
      - Improves test plan enforcement for small but risky changes to execution/live systems
* **Expected effect:**
  * Cleaner violation reports with deduplicated entries
  * Earlier detection of untested changes in critical paths (10+ lines vs 50+)
  * Zero impact on false positive rate (all changes are additive/tightening only)
  * Better operator questions generated for missing test plans
* **Verified by:**
  * All 64 existing tests pass (`tests/governance/policy_critic/`)
  * Manual verification:
    - Cycle 4 re-run: 2 violations → 1 violation with "(2 occurrences)"
    - Small critical change (10 lines in src/live/): Correctly triggers MISSING_TEST_PLAN
  * No severity downgrades or permissive changes made (fail-closed principle maintained)

## Tuning Philosophy (G3.6)

**Minimal & Safe:**
- ✅ Only tune where it improves operator UX
- ✅ No severity downgrades
- ✅ No relaxation of hard gates (NO_SECRETS, NO_LIVE_UNLOCK remain BLOCK)
- ✅ Additive only: tighten enforcement for critical paths, reduce noise
- ❌ No aggressive overfitting to synthetic tests
- ❌ No premature optimization for hypothetical scenarios

**Next Steps (G4):**
1. Deploy to real PRs and collect telemetry
2. Monitor false positive rate on non-critical changes
3. Track how often MISSING_TEST_PLAN triggers (expect increase due to lower threshold)
4. Consider adding pack-specific violation count limits if noise emerges

## Incident Log

### 2025-12-12 — PR #4 false positive: tmp artifacts triggered risk-limit rule
- **Context:** Policy Critic blocked PR #4 (tuning PR) with BLOCK severity
- **Rule:** RISK_LIMIT_RAISE_WITHOUT_JUSTIFICATION
- **Trigger:** tmp/policy_critic_cycles/cycle_4_stdout.txt contained simulated `max_leverage = 2.0`
- **Root cause:** committed test-output artifacts were scanned like real config changes
- **Fix:** remove tmp artifacts from git + add tmp/ to .gitignore
- **Commit:** c7307bc (chore(policy-critic): remove tmp artifacts from git and ignore them)
- **Outcome:** Policy Critic workflow GREEN; rule left unchanged (correct detection, wrong file scope)
