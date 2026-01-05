# AI-Ops Evals Scoreboard

**Purpose:** Track eval baseline and drift for AI-Ops prompts over time.

**Scope:** Agent governance compliance (path restrictions, secret leakage, output contracts).

**Governance:** Evals guide operator decisions; no autonomous actions.

---

## How to Run Locally

```bash
# Prerequisites: Node.js installed, OPENAI_API_KEY set
cd /Users/frnkhrz/Peak_Trade  # or your local Peak_Trade path

# Set API key (never commit this!)
export OPENAI_API_KEY="sk-..."

# Run eval
bash scripts/aiops/run_promptfoo_eval.sh
```

**Output:**
- Logs: `.artifacts/aiops/promptfoo_eval_<timestamp>.log`
- Console: Pass/fail summary

---

## What to Record

**For each eval run, track:**
- Date (UTC)
- Git SHA (`git rev-parse HEAD`)
- Node version (`node -v`)
- Promptfoo version (from `scripts/aiops/run_promptfoo_eval.sh`)
- Model (e.g., `openai:gpt-4`)
- Pass rate (e.g., `8/10 tests passed`)
- Failed test names (if any)

**Example scoreboard entry:**

```
Date: 2026-01-05T04:00:00Z
SHA: 452bf1e6
Node: v20.19.6
Promptfoo: 0.95.0
Model: openai:gpt-4
Pass Rate: 10/10
Failed: None
```

### Recording Your First Baseline

**After running evals for the first time:**

1. Check audit telemetry in log header:
   ```bash
   head -20 .artifacts/aiops/promptfoo_eval_<timestamp>.log
   ```

2. Record versions:
   - Git SHA (from log or `git rev-parse HEAD`)
   - Node version (from log or `node -v`)
   - Promptfoo version (from log or script header)

3. Add entry to baseline table below

4. Commit scoreboard update:
   ```bash
   git add docs/ai/AI_EVALS_SCOREBOARD.md
   git commit -m "docs(ai): Record eval baseline for SHA <sha>"
   ```

---

## Baseline (V1 — 2026-01-05)

| Date       | SHA      | Model       | Pass Rate | Failed Tests |
|------------|----------|-------------|-----------|--------------|
| 2026-01-05 | 452bf1e6 | openai:gpt-4 | 2/2       | None         |

**Notes:**
- Initial testcases: `docs_link_fixer`, `ci_failure_triage`
- Both tests validate governance compliance (path restrictions, no secret leakage)

---

## How to Interpret Failures

### 1. Policy Regression
**Symptom:** Test that previously passed now fails (e.g., agent proposes changes to `src/execution/`).

**Action:**
- Review recent prompt/rule changes (`.cursor/rules/`, `evals/aiops/promptfooconfig.yaml`)
- Check if model behavior drifted (OpenAI model update)
- Restore governance constraints or update testcase if intended behavior changed

### 2. Prompt Drift
**Symptom:** Test fails due to model output format change (e.g., missing "Changed files" section).

**Action:**
- Review model output (logs in `.artifacts/aiops/`)
- Update testcase assertions if new format is acceptable
- Update delivery contract (`.cursor/rules/peak-trade-delivery-contract.mdc`) if needed

### 3. False Positive
**Symptom:** Test fails but manual review shows agent behavior is correct.

**Action:**
- Refine testcase (too strict assertions)
- Add context to prompt to avoid edge-case failures

---

## Governance Note

**Evals are advisory, not blocking:**
- Failed evals signal potential issues → manual review required
- Passing evals do not guarantee safe agent behavior → operator must review outputs
- Evals test prompt compliance, not trading logic correctness

**When to escalate:**
- Repeated failures of governance-critical tests (secret leakage, path violations)
- Model behavior drift affecting production workflows
- New failure patterns not covered by existing testcases

---

## Adding New Tests

1. Create testcase YAML in `evals/aiops/testcases/`
2. Register in `evals/aiops/promptfooconfig.yaml`
3. Run eval locally to verify
4. Record new baseline in this scoreboard

**See:** `docs/ai/AI_EVALS_RUNBOOK.md` for testcase creation guide.

---

## CI Integration

**Trigger:** PR to `main` changes `.cursor/**`, `docs/ai/**`, `evals/aiops/**`, `scripts/aiops/**`

**Behavior:**
- Runs `scripts/aiops/run_promptfoo_eval.sh`
- Uploads logs as artifacts
- **Non-blocking:** Failures do not block PR merge (advisory only)
- Skipped if `OPENAI_API_KEY` secret not available

**See:** `.github/workflows/aiops-promptfoo-evals.yml`

---

**Last Updated:** 2026-01-05  
**Version:** 1.0
