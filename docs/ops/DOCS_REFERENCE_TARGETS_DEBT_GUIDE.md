# Docs Reference Targets Debt Management Guide

**Version:** 1.0  
**Last Updated:** 2026-01-07  
**Owner:** Peak_Trade Ops Team

---

## Overview

This guide explains how Peak_Trade manages documentation link quality through two complementary mechanisms:

1. **Changed-Files Gate** (strict): Prevents new PRs from introducing broken links
2. **Full-Scan Trend Gate** (baseline): Prevents debt from growing while allowing gradual paydown

---

## Two Gates, Two Purposes

### Gate 1: Docs Reference Targets (Changed Files) 🔒

**Purpose:** Zero tolerance for new broken links in PRs

**Scope:** Only files changed in your PR

**Enforcement:** Required CI check (blocks merge)

**How it works:**
```bash
# Runs on every PR with doc changes
scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

**When it fails:** Your PR introduced new broken links

**How to fix:** Fix the broken links before merge

---

### Gate 2: Docs Reference Targets Trend 📊

**Purpose:** Track and prevent growth of historical debt

**Scope:** All markdown files in `docs/`

**Enforcement:** Informational check (visible but not required)

**How it works:**
```bash
# Compares current state against baseline
scripts/ops/verify_docs_reference_targets_trend.sh
```

**Baseline:** `docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json`

**When it fails:** Total missing targets increased (new debt added)

**How to fix:** Either fix the new broken links, or update baseline with justification

---

## Why Two Gates?

### Problem: Historical Debt

Peak_Trade's documentation has accumulated **118 missing targets** over time. These are:
- References to planned features not yet implemented
- Documentation stubs for future work
- Legacy paths from refactoring
- Intentional forward-references

### Solution: Controlled Debt Management

**Changed-Files Gate** ensures:
- ✅ New PRs don't introduce broken links
- ✅ Every new doc reference is validated immediately
- ✅ Zero tolerance for new debt

**Full-Scan Trend Gate** ensures:
- ✅ Total debt doesn't grow
- ✅ Debt reduction is tracked and encouraged
- ✅ Baseline updates require explicit decision + audit trail

---

## Common Workflows

### Workflow 1: Normal PR (No Debt Change)

Your PR changes docs but doesn't add new broken links.

**What happens:**
1. ✅ Changed-Files Gate: PASS (no new broken links)
2. ✅ Trend Gate: PASS (current_missing <= baseline_missing)

**Action:** None required - merge normally

---

### Workflow 2: PR Fixes Broken Links 🎉

Your PR fixes some of the 118 historical broken links.

**What happens:**
1. ✅ Changed-Files Gate: PASS
2. ✅ Trend Gate: PASS with improvement message

**Action (recommended):**
```bash
# Update baseline to reflect improvement
python scripts/ops/collect_docs_reference_targets_fullscan.py
git add docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json
git commit -m "docs: update reference targets baseline (debt reduced)"
```

**Why update?** Locks in your improvement and resets the trend baseline.

---

### Workflow 3: PR Adds Intentional Forward-Reference

Your PR documents a planned feature that doesn't exist yet.

**Example:** Adding docs for `src/trading/advanced_orders.py` <!-- pt:ref-target-ignore --> before implementing it.

**What happens:**
1. ❌ Changed-Files Gate: FAIL (new broken link)
2. ❌ Trend Gate: FAIL (debt increased)

**Option A: Use pt:ref-target-ignore (recommended)**
```markdown
See future implementation: `src/trading/advanced_orders.py` <!-- pt:ref-target-ignore -->
```

This:
- ✅ Bypasses Changed-Files Gate (intentional forward-ref)
- ✅ Trend Gate passes (ignored references don't count)

**Option B: Update baseline (requires justification)**
```bash
# Add to PR:
python scripts/ops/collect_docs_reference_targets_fullscan.py
git add docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json
```

Include in PR description:
```markdown
## Baseline Update

This PR intentionally adds forward-references for:
- docs/feature_x.md → config/feature_x.toml (planned in PR #XXX)
- docs/api.md → src/api/v2.py (roadmap item for Q1 2026)

Justification: [explain why these forward-refs are valuable now]
```

---

### Workflow 4: Mass Debt Paydown

You want to fix many historical broken links.

**Strategy:**
1. Create dedicated "docs debt paydown" PR
2. Fix broken links in batches (10-20 at a time)
3. Update baseline after each batch

**Example:**
```bash
# Fix batch 1
git checkout -b docs/debt-paydown-batch-1
# ... fix 20 broken links in docs/risk/
python scripts/ops/verify_docs_reference_targets_trend.sh --verbose
# Verify: should show improvement

# Update baseline
python scripts/ops/collect_docs_reference_targets_fullscan.py
git add docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json
git commit -m "docs(debt): fix 20 broken links in docs/risk/ (118→98)"

# PR and merge
gh pr create --title "docs(debt): paydown batch 1 - fix 20 broken links in risk/"
```

**Benefits:**
- Small, reviewable PRs
- Incremental progress
- Clear audit trail

---

## Baseline Management

### When to Update Baseline

**YES - Update baseline when:**
- ✅ You fixed broken links (debt reduced)
- ✅ You added intentional forward-references with justification
- ✅ You're doing a coordinated docs refactor

**NO - Don't update baseline when:**
- ❌ Your PR accidentally introduced broken links
- ❌ You're bypassing the gate to "just merge"
- ❌ No justification or audit trail

### How to Update Baseline

```bash
# 1. Ensure you're on your PR branch
git status

# 2. Generate new baseline
python scripts/ops/collect_docs_reference_targets_fullscan.py

# 3. Review the change
git diff docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json

# 4. Commit with clear message
git add docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json
git commit -m "docs: update reference targets baseline

Reason: [your justification]
- Previous: XXX missing targets
- Current: YYY missing targets
- Delta: [+/-Z]

[Explain what changed and why it's acceptable]"

# 5. Push and include in PR
git push
```

### Baseline File Format

```json
{
  "generated_at_utc": "2026-01-07T04:00:00Z",
  "git_sha": "abc123...",
  "tool_version": "1.0.0",
  "scan_stats": {
    "total_markdown_files": 690,
    "ignored_files": 9,
    "scanned_files": 681,
    "total_references": 4605
  },
  "missing_count": 118,
  "missing_items": [
    {
      "source_file": "docs/ARCHITECTURE_OVERVIEW.md",
      "line_number": 109,
      "target": "docs/Peak_Trade_Data_Layer_Doku.md",
      "link_text": "Data Layer Documentation"
    }
  ]
}
```

**Key fields:**
- `missing_count`: Trend gate compares this
- `missing_items`: Detailed list for analysis
- `git_sha`: Audit trail (what commit generated baseline)
- `tool_version`: Baseline format compatibility tracking

---

## Ignore Patterns

### File Ignores

Edit `docs/ops/DOCS_REFERENCE_TARGETS_IGNORE.txt`:

```
# Ignore test fixtures
tests/fixtures/**

# Ignore auto-generated docs
docs/api/autogen/**

# Example: ignore specific known-broken legacy doc
# docs/legacy/old_architecture.md
```

**When to use:**
- Test fixtures with intentional broken references
- Auto-generated docs you don't control
- Legacy docs scheduled for deletion

**When NOT to use:**
- To hide broken links in active documentation
- To bypass the gate for convenience

### Inline Ignores

```markdown
<!-- pt:ref-target-ignore -->
```

**Use on same line as reference:**
```markdown
See future: `src/feature.py` <!-- pt:ref-target-ignore -->
```

**When to use:**
- Forward-references to planned features
- Examples showing invalid paths
- TODOs with future file references

---

## Troubleshooting

### "Trend gate failing but I didn't change docs"

**Cause:** Someone else's merged PR increased debt, but baseline wasn't updated.

**Fix:**
```bash
# Check current state
scripts/ops/verify_docs_reference_targets_trend.sh --verbose

# If your PR didn't cause it:
# 1. Update baseline to current main
git checkout main
git pull
python scripts/ops/collect_docs_reference_targets_fullscan.py
git checkout -b docs/update-baseline-after-merge
git add docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json
git commit -m "docs: update baseline after PR #XXX merge"
gh pr create

# 2. Rebase your feature branch
git checkout your-feature-branch
git rebase main
```

### "Changed-Files gate passing but Trend gate failing"

**Cause:** Your PR's new docs reference files that are:
- Created in your PR (not yet in main)
- Will be added in a future PR

**Fix:**
```bash
# Option 1: Merge prerequisites first
# Option 2: Use pt:ref-target-ignore for forward-refs
# Option 3: Update baseline with justification
```

### "False positives - valid paths reported as missing"

**Cause:** Path normalization or pattern matching issue.

**Fix:**
1. Check if path uses wildcards, spaces, or special chars
2. Verify path is relative to repo root or doc file
3. Add inline ignore if genuinely valid but undetectable:
   ```markdown
   Complex path: `../../../src/file.py` <!-- pt:ref-target-ignore -->
   ```

---

## Local Testing Commands

### Check Changed Files (PR-style)

```bash
# Same as CI runs on PRs
scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

### Check Full-Scan Trend

```bash
# Same as Trend Gate
scripts/ops/verify_docs_reference_targets_trend.sh --verbose
```

### Generate New Baseline

```bash
# Create/update baseline
python scripts/ops/collect_docs_reference_targets_fullscan.py

# Custom output location
python scripts/ops/collect_docs_reference_targets_fullscan.py \
  --output /tmp/custom-baseline.json
```

### Inspect Baseline

```bash
# Show summary
jq '{missing_count, scan_stats}' docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json

# Show top 10 missing targets
jq -r '.missing_items[:10] | .[] | "\(.source_file):\(.line_number) → \(.target)"' \
  docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json

# Count by source file
jq -r '.missing_items | group_by(.source_file) | .[] | "\(length) \(.[0].source_file)"' \
  docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json | sort -rn | head -20
```

---

## Audit & Governance

### Baseline Changes Require Justification

All baseline updates MUST include:
1. **Quantitative change:** Previous count → New count
2. **Qualitative explanation:** What changed and why
3. **Approval:** PR review before merge

**Example commit message:**
```
docs: update reference targets baseline (debt reduced from 118→102)

Reason: Fixed broken links in docs/risk/ as part of Risk Layer v2 docs update.

Changes:
- Fixed 16 broken links to moved/renamed risk config files
- All references now point to canonical locations

Previous: 118 missing targets
Current: 102 missing targets
Improvement: -16 (13.5% reduction)

Related: PR #595 (Risk Layer v2 docs overhaul)
```

### Monitoring Debt Over Time

```bash
# Show baseline history
git log --oneline --follow docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json

# Show debt trend
git log -p docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json | \
  grep '"missing_count"' | \
  awk '{print $2}' | \
  sed 's/,$//'
```

### Quarterly Debt Review

**Recommended practice:**
1. Review baseline quarterly
2. Identify top debt sources (by file or directory)
3. Create targeted paydown PRs
4. Track progress in ops meeting

**Query for review:**
```bash
# Top 20 files with most broken links
jq -r '.missing_items | group_by(.source_file) |
  map({file: .[0].source_file, count: length}) |
  sort_by(-.count) |
  .[:20] |
  .[] | "\(.count)\t\(.file)"' \
  docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json
```

---

## FAQ

### Q: Should I fix every broken link I see?

**A:** No. Focus on:
1. Links you're actively using/referencing
2. High-traffic docs (README, getting started, runbooks)
3. Customer-facing docs

Leave low-priority debt for dedicated paydown sessions.

### Q: Can I temporarily disable the Trend Gate?

**A:** The Trend Gate is already **informational only** (not required for merge). But if it's failing, you should either:
1. Fix the new broken links (recommended)
2. Update baseline with justification

Don't ignore it completely - debt growth is a code smell.

### Q: What if I'm documenting a feature that's in a different PR?

**A:** Use `<!-- pt:ref-target-ignore -->` and cross-reference the other PR:

```markdown
See `src/new_feature.py` for implementation details. <!-- pt:ref-target-ignore -->
<!-- Will be added in PR #XXX -->
```

### Q: The baseline is huge (118 items). Is that bad?

**A:** It's historical debt. Not ideal, but manageable. The Trend Gate prevents it from growing. Pay it down incrementally:
- Fix 10-20 links per quarter
- Combine with related feature work
- Don't let it block new features

---

## Related Documentation

- Docs Reference Targets Gate (Changed Files): `scripts/ops/verify_docs_reference_targets.sh`
- Drift Guard Documentation: `docs/ops/DRIFT_GUARD_QUICK_START.md`
- Policy Critic Documentation: `docs/governance/POLICY_CRITIC_STATUS.md`

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-07  
**Maintained By:** Peak_Trade Ops Team
