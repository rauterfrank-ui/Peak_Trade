# docs(ops): Phase 9C Wave 5 remediation (broken targets + token policy)

## Objective

Reduce broken reference targets from **58 → ≤ 40** (−18 targets, −31%).

**Result:** ✅ **58 → 39** (−19, −32.8%) — **Goal exceeded by 1!**

---

## Summary

Wave 5 implements cluster-based remediation for remaining low-frequency broken targets, focusing on **illustrative code examples** and **historical branch references**.

### Key Metrics

| Metric | Before | After | Delta | % Change |
|--------|--------|-------|-------|----------|
| **Broken Targets** | 58 | 39 | −19 | −32.8% |
| **Total References** | 5826 | ~5807 | ~−19 | ~−0.3% |

### Approach

1. **Cluster-based targeting:** Group by theme (illustrative examples, historical references)
2. **Minimal escapes:** Apply `&#47;` to inline-code tokens only
3. **Semantic preservation:** No content deletions (escape vs. delete strategy)
4. **Token-Policy compliant:** All escapes follow established patterns

---

## Changes

### 2 Clusters Fixed

#### Cluster 1: Illustrative Code Examples (11 targets)

**Files:**
- `docs&#47;DEV_GUIDE_ADD_STRATEGY.md` (1 target)
- `docs&#47;DEV_GUIDE_ADD_EXCHANGE.md` (1 target)
- `docs&#47;AUTO_PORTFOLIOS.md` (2 targets)
- `docs&#47;ops&#47;TEST_HEALTH_AUTOMATION_V0.md` (3 targets)
- `docs&#47;Peak_Trade_Research_Strategy_Roadmap_2025-12-07.md` (1 target)
- `docs&#47;PORTFOLIO_RECIPES_AND_PRESETS.md` (2 targets)
- `docs&#47;project_docs&#47;CLAUDE_NOTES.md` (1 target)
- `docs&#47;runbooks&#47;R_AND_D_PLAYBOOK_ARMSTRONG_EL_KAROUI_V1.md` (2 targets)
- `docs&#47;SWEEPS_MARKET_SCANS.md` (1 target)

**Fix:** Escape slashes + add "(illustrative)" marker

**Examples:**
- `src&#47;strategies&#47;my_new_strategy.py` (illustrative)
- `src&#47;data&#47;my_exchange.py` (illustrative)
- `config&#47;portfolios`
- `config&#47;custom_recipes.toml` (illustrative)
- `scripts&#47;my_smoke_test.py` (illustrative)

#### Cluster 2: Historical Branch References (8 targets)

**Files:**
- `docs&#47;ops&#47;PR_593_MERGE_LOG.md` (5 targets)
- `docs&#47;ops&#47;PR_76_MERGE_LOG.md` (1 target)
- `docs&#47;ops&#47;PR_78_MERGE_LOG.md` (1 target)
- `docs&#47;ops&#47;PR_218_MERGE_LOG.md` (1 target)

**Fix:** Escape slashes + add "(historical)" marker

**Examples:**
- `docs&#47;pr-76-merge-log` (historical stub)
- `docs&#47;ops&#47;pr-93-merge-log` (historical stub)
- `docs&#47;ops-pr-85-merge-log` (historical stub)
- `docs&#47;pr-74-delivery-note` (historical branch)

### Total Escapes

- **Primary targets:** 19 broken targets resolved
- **Bonus escapes:** 4 additional paths (consistency)
- **Total inline-code escapes:** 23
- **Semantic markers:** 19 added

---

## Verification

### Snapshots

- **Before:** `docs&#47;ops&#47;graphs&#47;docs_graph_snapshot_wave5_before.txt` (58 targets)
- **After:** `docs&#47;ops&#47;graphs&#47;docs_graph_snapshot_wave5_after.txt` (39 targets)

### Gates

- ✅ **Docs Reference Targets Gate:** Expected PASS (39 validated targets)
- ✅ **Docs Token Policy Gate:** Expected PASS (no new violations introduced)
- ✅ **Docs Diff Guard Policy Gate:** Expected PASS (marker present)

### Commands

```bash
# Verify broken targets reduction
bash scripts&#47;ops&#47;verify_docs_reference_targets.sh

# Verify token policy compliance (changed files only)
python3 scripts&#47;ops&#47;validate_docs_token_policy.py --changed --base main

# Full gates snapshot
bash scripts&#47;ops&#47;pt_docs_gates_snapshot.sh
```

---

## Risk

**Risk Level:** **LOW**

**Why:**
1. ✅ Docs-only changes (no code, config, or execution logic)
2. ✅ Semantic preservation (escape vs. delete strategy, KEEP EVERYTHING)
3. ✅ Token-Policy compliant (all escapes follow `&#47;` pattern)
4. ✅ Snapshot-verified (before/after confirms −19 targets)
5. ✅ Cluster-based (systematic, repeatable approach)

---

## Files Changed (13 core docs + 3 artifacts)

### Core Documentation (13 files)

```
docs/AUTO_PORTFOLIOS.md
docs/DEV_GUIDE_ADD_EXCHANGE.md
docs/DEV_GUIDE_ADD_STRATEGY.md
docs/PORTFOLIO_RECIPES_AND_PRESETS.md
docs/Peak_Trade_Research_Strategy_Roadmap_2025-12-07.md
docs/SWEEPS_MARKET_SCANS.md
docs/ops/PR_218_MERGE_LOG.md
docs/ops/PR_593_MERGE_LOG.md
docs/ops/PR_76_MERGE_LOG.md
docs/ops/PR_78_MERGE_LOG.md
docs/ops/TEST_HEALTH_AUTOMATION_V0.md
docs/project_docs/CLAUDE_NOTES.md
docs/runbooks/R_AND_D_PLAYBOOK_ARMSTRONG_EL_KAROUI_V1.md
```

### Artifacts (3 files)

```
docs/ops/graphs/REMEDIATION_WAVE5_2026-01-14.md (comprehensive report)
docs/ops/graphs/docs_graph_snapshot_wave5_before.txt
docs/ops/graphs/docs_graph_snapshot_wave5_after.txt
PHASE9C_WAVE5_CHANGED_FILES.txt
```

---

## Artifacts

- **Remediation Report:** `docs&#47;ops&#47;graphs&#47;REMEDIATION_WAVE5_2026-01-14.md` (comprehensive)
- **Before Snapshot:** `docs&#47;ops&#47;graphs&#47;docs_graph_snapshot_wave5_before.txt` (58 targets)
- **After Snapshot:** `docs&#47;ops&#47;graphs&#47;docs_graph_snapshot_wave5_after.txt` (39 targets)
- **Changed Files List:** `PHASE9C_WAVE5_CHANGED_FILES.txt`
- **PR Body:** `PHASE9C_WAVE5_PR_BODY.md` (this file)

---

## Related

- **Wave 3 PR:** #712 (114 → 89, −25, −21.9%)
- **Wave 4 PR:** #714 (87 → 65, −22, −25.3%)
- **Wave 5 PR:** (this PR) (58 → 39, −19, −32.8%)

**Cumulative Impact (Waves 3-5):**
- **Baseline (pre-Wave 3):** 114 broken targets
- **After Wave 5:** 39 broken targets
- **Total reduction:** −75 targets (−65.8%)

---

## Operator How-To

### Pre-Merge Checklist

- [ ] All required checks PASS
- [ ] Docs Reference Targets Gate: PASS (39 targets)
- [ ] Docs Token Policy Gate: PASS
- [ ] Docs Diff Guard Policy Gate: PASS
- [ ] Review: Approved

### Merge Command

```bash
gh pr merge <PR_NUMBER> --squash --auto --delete-branch
```

### Post-Merge Verification

```bash
git switch main
git pull --ff-only
gh pr view <PR_NUMBER> --json mergedAt,mergeCommit,state
```

---

**Generated by:** Cursor Multi-Agent (Phase 9C Wave 5)  
**Date:** 2026-01-14  
**Status:** ✅ Ready for Review

---

> [!NOTE]
> Reduces broken docs reference targets via cluster-based remediation (illustrative examples + historical references) and token-policy compliant escapes.
>
> - Escapes `scripts&#47;`, `src&#47;`, `config&#47;`, and `docs&#47;` paths in inline code across 13 docs (e.g., DEV_GUIDE_ADD_STRATEGY, AUTO_PORTFOLIOS, TEST_HEALTH_AUTOMATION_V0, merge logs), adding "(illustrative)" and "(historical)" markers
> - Result: Broken targets 58 → 39 (−19, −32.8%); ~19 references removed/adjusted; no content deletions
> - Token policy: Inline slashes escaped (`&#47;`); no new violations introduced
> - Adds before/after snapshots and comprehensive remediation report under `docs&#47;ops&#47;graphs&#47;`
