# Peak_Trade – G4 Telemetry Collection (Policy Critic)

**Goal:** Track 10–20 real PRs → False Positive Rate < 10% → potentially create Change Set 2.

---

## A) Per-PR: 2-Min Workflow (Tool: Cursor Terminal / Shell)

> Replace `<PR>` with the PR number.

```bash
set -euo pipefail
PR=<PR>

echo "==[1] PR Overview =="
gh pr view "$PR" --json number,title,author,baseRefName,headRefName,changedFiles,additions,deletions,url \
  --jq '{number,title,author:.author.login,base:.baseRefName,head:.headRefName,changedFiles,additions,deletions,url}'

echo "==[2] Checks / Policy Critic Status =="
gh pr checks "$PR" || true

echo "==[3] (Optional) Quick Policy-Critic run logs =="
# If you know the workflow run ID, use:
# gh run view <RUN_ID> --log-failed
# Otherwise: open the PR checks output and grab the Run ID.

echo "==[4] Record Decision =="
echo "If BLOCK: Violation Key(s) + affected file(s) + whether True/False Positive."
```

---

## B) Telemetry Entry Template

Copy/paste into: `docs/governance/POLICY_CRITIC_TELEMETRY_G4.md`

> One block per PR. Brief, reproducible, no novels.

```md
## PR #<PR> — <YYYY-MM-DD>
- **Title:** <short description>
- **Result:** PASS | WARN | BLOCK
- **Severity:** <LOW/MED/HIGH/BLOCK>
- **Rules triggered:**
  - <RULE_KEY_1> (files: <paths...>)
  - <RULE_KEY_2> (files: <paths...>)
- **Classification:** TRUE_POSITIVE | FALSE_POSITIVE | MIXED | NEEDS_REVIEW
- **Operator action:**
  - <e.g. "added justification", "excluded path", "changed threshold", "no change">
- **Notes:**
  - <1–2 bullets: why, what was learned>
```

---

## C) Tuning Log Template

Copy/paste into: `docs/governance/POLICY_PACK_TUNING_LOG.md`

> Only when you actually change Policy Pack / Rules.

```md
### <YYYY-MM-DD> — Change Set <N>: <short title>
- **Trigger:** PR #<PR> telemetry showed <problem>
- **Change:**
  - <what was changed, 1–3 bullets>
- **Rationale:**
  - <why this reduces FP without losing real risk detection>
- **Expected impact:**
  - FP ↓, TP maintained (no blind spots)
- **Validation:**
  - Re-ran on PR(s): #<PR>, #<PR>
  - Outcome: <PASS/WARN/BLOCK> + brief note
```

---

## D) Classification Rules (Operator Quick Rule)

* **TRUE_POSITIVE:** Real risky change (e.g., live risk limits) without sufficient justification/plan.
* **FALSE_POSITIVE:** Artifact/Doc/Test fixture/Non-live path, or purely textual without real impact.
* **MIXED:** One hit correct, one hit FP → evaluate separately, make only necessary adjustments.
* **NEEDS_REVIEW:** Unclear → add 1 note, batch-review later.

---

## E) "What Do I Do When BLOCKED?"

1. Check affected file (is this really live-relevant?)
2. If real: PR needs Justification/Test Plan or change must be removed/split
3. If FP: Adjust Scope/Rule (ideally via Path Exclusions / File Types), then document:
   * Telemetry: "FP"
   * Tuning Log: only if Code/Policy Pack was changed

---

## F) Mini-Exit Criteria (G4 Done)

* ✅ 10–20 PRs logged
* ✅ False Positive Rate < 10%
* ✅ At least 1 "Smoke Scenario" (real BLOCK, real Risk change) observed
* ✅ Change Set 2 either created or explicitly "no changes needed" documented

---

## G) Quick Commands Reference

### View PR with Policy Critic results
```bash
gh pr view <PR>
gh pr checks <PR>
```

### View failed Policy Critic logs
```bash
gh run view <RUN_ID> --log-failed
```

### View Policy Critic job summary (GitHub UI)
Navigate to: `Actions → Policy Critic Review → Job Summary`

### Download Policy Critic results artifact
```bash
gh run download <RUN_ID> -n policy-critic-results
cat policy_result.json | jq '.'
```

---

## H) Telemetry Analysis Commands

### Count PRs by result
```bash
grep -E "^- \*\*Result:\*\*" docs/governance/POLICY_CRITIC_TELEMETRY_G4.md | sort | uniq -c
```

### Count False Positives
```bash
grep -E "^- \*\*Classification:\*\* FALSE_POSITIVE" docs/governance/POLICY_CRITIC_TELEMETRY_G4.md | wc -l
```

### List all rules that triggered
```bash
grep -E "^\s+- [A-Z_]+ \(" docs/governance/POLICY_CRITIC_TELEMETRY_G4.md | sed 's/.*- \([A-Z_]*\).*/\1/' | sort | uniq -c | sort -rn
```

---

## I) Batch Analysis (After 10+ PRs)

```bash
cd docs/governance

echo "=== Summary Statistics ==="
echo "Total PRs logged:"
grep -c "^## PR #" POLICY_CRITIC_TELEMETRY_G4.md

echo -e "\nResults breakdown:"
grep "^- \*\*Result:\*\*" POLICY_CRITIC_TELEMETRY_G4.md | sed 's/.*Result:\*\* //' | sort | uniq -c

echo -e "\nClassification breakdown:"
grep "^- \*\*Classification:\*\*" POLICY_CRITIC_TELEMETRY_G4.md | sed 's/.*Classification:\*\* //' | sort | uniq -c

echo -e "\nTop triggered rules:"
grep -E "^\s+- [A-Z_]+ \(" POLICY_CRITIC_TELEMETRY_G4.md | sed 's/.*- \([A-Z_]*\).*/\1/' | sort | uniq -c | sort -rn | head -5

echo -e "\nFalse Positive Rate:"
TOTAL=$(grep -c "^## PR #" POLICY_CRITIC_TELEMETRY_G4.md)
FP=$(grep -c "FALSE_POSITIVE" POLICY_CRITIC_TELEMETRY_G4.md)
echo "scale=2; $FP * 100 / $TOTAL" | bc
echo "%"
```

---

## J) Example Telemetry Entry (Reference)

```md
## PR #42 — 2025-12-15
- **Title:** feat(strategies): add new momentum indicator
- **Result:** WARN
- **Severity:** WARN
- **Rules triggered:**
  - EXECUTION_ENDPOINT_TOUCH (files: src/strategies/momentum_v2.py)
- **Classification:** TRUE_POSITIVE
- **Operator action:**
  - Added test plan covering edge cases
  - Marked as reviewed
- **Notes:**
  - Rule correctly identified strategy touching execution path
  - No changes to Policy Critic needed
```
