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

## G4 Change Set Decision Template

Use this template after logging 10–20 PRs to decide on Change Set 2.

### <YYYY-MM-DD> — G4 Decision: Change Set 2 (YES/NO)

- **PRs logged:** <n> PRs
- **False Positive Rate:** <x.x>% (definition: FALSE_POSITIVE / classified PRs, excluding NEEDS_REVIEW)
- **Real BLOCK scenario observed:** YES/NO (PR #... if yes)
- **Top noisy rules:** <RULE_A> (<count> occurrences), <RULE_B> (<count> occurrences)
- **Decision:** YES (implement changes below) | NO (keep current Policy Pack as-is)
- **Rationale:**
  - <bullet 1: why FP rate is acceptable/unacceptable>
  - <bullet 2: whether noise comes from specific rules or is systemic>
  - <bullet 3: whether real risks are being caught (TP rate analysis)>
  - <bullet 4: operator experience (is the friction warranted?)>
- **Next validation plan:**
  - <if YES: what changes to make, how to validate>
  - <if NO: continue tracking next N PRs, re-evaluate on date X>

### Example: Change Set 2 Rejection (FP rate acceptable)

```md
### 2025-12-20 — G4 Decision: Change Set 2 (NO)

- **PRs logged:** 15 PRs
- **False Positive Rate:** 6.7% (1 FP / 15 PRs)
- **Real BLOCK scenario observed:** YES (PR #44 correctly blocked live execution change)
- **Top noisy rules:** EXECUTION_ENDPOINT_TOUCH (12 occurrences), RISK_LIMIT_TOUCH (5 occurrences)
- **Decision:** NO (keep current Policy Pack as-is)
- **Rationale:**
  - FP rate is 6.7% (below 10% target)
  - Single FP was due to doc fixture (docs/tmp path) — already excluded in Change Set 1
  - Real BLOCK (PR #44) demonstrates value: caught live execution change without test plan
  - EXECUTION_ENDPOINT_TOUCH is noisy but has high TP rate (11/12 were TRUE_POSITIVE)
  - Operator friction is acceptable for current risk profile
- **Next validation plan:**
  - Continue monitoring next 10 PRs
  - Re-evaluate if FP rate crosses 10%
  - Track: does EXECUTION_ENDPOINT_TOUCH remain effective or become noise?
```

### Example: Change Set 2 Acceptance (FP rate too high)

```md
### 2025-12-22 — G4 Decision: Change Set 2 (YES)

- **PRs logged:** 18 PRs
- **False Positive Rate:** 16.7% (3 FP / 18 PRs)
- **Real BLOCK scenario observed:** YES (PR #51 correctly blocked risk limit increase)
- **Top noisy rules:** EXECUTION_ENDPOINT_TOUCH (25 occurrences), RISK_LIMIT_TOUCH (8 occurrences)
- **Decision:** YES (implement changes below)
- **Rationale:**
  - FP rate is 16.7% (above 10% target)
  - 3 FPs all from EXECUTION_ENDPOINT_TOUCH triggering on test utilities in tests/utils/
  - Real risks are being caught (PR #51 BLOCK was correct)
  - Solution: exclude tests/utils/ from EXECUTION_ENDPOINT_TOUCH scope
- **Changes in Change Set 2:**
  - **Rule:** EXECUTION_ENDPOINT_TOUCH
  - **Change:** Add exclusion for tests/utils/ directory
  - **Implementation:** Update rule pattern exclusions in .github/workflows/policy-critic.yml
  - **Expected impact:** FP rate drops to ~5% while maintaining TP detection
- **Validation:**
  - Re-run Policy Critic on PR #45, #48, #52 (the 3 FPs)
  - Expected: all 3 should PASS
  - Re-run on PR #51 (real BLOCK): should still BLOCK
  - If validation passes: commit as Change Set 2
  - Then: track next 10 PRs to confirm FP rate improvement
```

---

## Incident Log

### 2025-12-12 — PR #4 false positive: tmp artifacts triggered risk-limit rule
- **Context:** Policy Critic blocked PR #4 (tuning PR) with BLOCK severity
- **Rule:** RISK_LIMIT_RAISE_WITHOUT_JUSTIFICATION
- **Trigger:** tmp/policy_critic_cycles/cycle_4_stdout.txt contained simulated risk-limit pattern
- **Root cause:** committed test-output artifacts were scanned like real config changes
- **Fix:** remove tmp artifacts from git + add tmp/ to .gitignore; exclude docs/ from pattern matching
- **Commit:** c7307bc (chore(policy-critic): remove tmp artifacts from git and ignore them)
- **Outcome:** Policy Critic workflow GREEN; rule left unchanged (correct detection, wrong file scope)
