# Policy Critic – Real Cycles (G3.5)

## Cycle Log

| Cycle | Date | Scenario | Policy Pack | Max Severity | Action | Top Rules | False Positive? | Notes | Artifact/Report |
| ----: | ---- | -------- | ----------- | ------------ | ------ | --------- | --------------- | ----- | --------------- |
| 1 | 2025-12-12 | Baseline: docstring/comment change in utils | ci (default) | INFO | ALLOW | None | No | Clean pass as expected for low-risk utility change | `tmp&#47;policy_critic_cycles&#47;cycle_1_stdout.txt` |
| 2 | 2025-12-12 | Critical path: comment added to `src/live/` | ci (default) | WARN | REVIEW_REQUIRED | EXECUTION_ENDPOINT_TOUCH | No | Correctly flagged live execution path touch; generated operator questions | `tmp&#47;policy_critic_cycles&#47;cycle_2_stdout.txt` |
| 3 | 2025-12-12 | Docs-only: README update | ci (default) | INFO | ALLOW | None | No | Clean pass as expected for documentation | `tmp&#47;policy_critic_cycles&#47;cycle_3_stdout.txt` |
| 4 | 2025-12-12 | Risk limit raise: max_leverage 2.0→4.0 without justification | ci (default) | BLOCK | AUTO_APPLY_DENY | RISK_LIMIT_RAISE_WITHOUT_JUSTIFICATION (×2) | No | Hard gate worked correctly; detected missing justification in context | `tmp&#47;policy_critic_cycles&#47;cycle_4_stdout.txt` |
| 5 | 2025-12-12 | Fail-closed drill: malformed context JSON | ci (default) | WARN (when no context) | REVIEW_REQUIRED | EXECUTION_ENDPOINT_TOUCH | N/A | Malformed JSON → input error (fail-closed at boundary); without context, execution touch → REVIEW_REQUIRED | `tmp&#47;policy_critic_cycles&#47;cycle_5_stdout.txt` |

## Observations

### Noise sources:
* **None observed** - All violations were legitimate and correctly matched the test scenarios
* EXECUTION_ENDPOINT_TOUCH appropriately triggered for both `src/live/` and `src/execution/` paths
* No false positives in baseline or docs-only scenarios

### Missed risk signals:
* **None observed** in these synthetic cycles
* Risk limit raise was correctly caught with BLOCK severity
* Critical path touches properly escalated to REVIEW_REQUIRED

### Pack tweaks candidates:
* **Current CI pack is well-calibrated** for these test scenarios
* Consider adding severity escalation if risk limits change by >50% (cycle 4 doubled leverage)
* Could add specific rules for execution path comments (cycle 2) vs actual code changes
* May want explicit BLOCK for any `src/live/` touches (currently WARN → REVIEW_REQUIRED)

## Summary

All 5 synthetic cycles performed as expected:
- ✅ Baseline changes: ALLOW (low noise)
- ✅ Critical path: REVIEW_REQUIRED with operator questions
- ✅ Docs-only: ALLOW (correct filtering)
- ✅ Risk limits without justification: BLOCK (hard gate)
- ✅ Malformed input: Fail-closed at input boundary

**Next Steps (G3.6):**
1. Monitor real-world PR reviews for false positives
2. Consider severity escalation rules for large magnitude changes
3. Potentially add `src&#47;live&#47;**` to auto-BLOCK list vs current WARN
4. Document operator response patterns to common violations
