# Phase 9C — Docs Graph Remediation (Waves 3–5) — Closeout Report

**Date:** 2026-01-14  
**Scope:** Docs-only, systematic broken targets remediation  
**Status:** ✅ **Mission Complete** — Goal achieved (Baseline: 39 targets, Gate PASS)

---

## Executive Summary

Phase 9C successfully reduced broken reference targets across three systematic waves, achieving the mission goal of establishing a sustainable baseline (≤40 targets) while maintaining the **KEEP EVERYTHING** principle.

**Key Outcomes:**
- **Total Reduction:** 114 → 39 targets (−75, −65.8%)
- **Method:** Mechanical escapes + semantic markers (no content deletions)
- **Token Policy:** 85 violations resolved across all waves
- **Gates:** All PRs passed (Token Policy, Reference Targets, Diff Guard)
- **Risk:** LOW (docs-only, semantic-preserving, fully reversible)

---

## Scope

### Mission Objective

Reduce broken reference targets in the docs graph from a high baseline (~114–142) to a sustainable level (≤40) without:
- Deleting content (KEEP EVERYTHING principle)
- Changing semantics (preserve historical references, illustrative examples)
- Breaking Token Policy compliance (mechanical escapes only)

### Approach

**Three-Wave Strategy:**
1. **Wave 3:** High-impact targets (historical scripts, illustrative paths, leading dots)
2. **Wave 4:** Cluster-based remediation (low-frequency targets grouped by theme)
3. **Wave 5:** Final cluster push (illustrative examples + historical branch names)

**Methodology:**
- Minimal-invasive escapes (`&#47;` for slashes in inline-code)
- Semantic markers (illustrative, historical) for clarity
- No link-ification of illustrative paths
- Snapshot-driven verification (local + CI)

---

## Outcomes

### Metrics Table

| Wave | PR | Before | After | Delta | % Change | Goal | Result |
|------|----|--------|-------|-------|----------|------|--------|
| **3** | [#712](https://github.com/rauterfrank-ui/Peak_Trade/pull/712) | 114 | 89 | −25 | −21.9% | ≤135 | ✅ Exceeded by 46 |
| **4** | [#714](https://github.com/rauterfrank-ui/Peak_Trade/pull/714) | 87 | 65 | −22 | −25.3% | ≤68 | ✅ Exceeded by 3 |
| **5** | [#716](https://github.com/rauterfrank-ui/Peak_Trade/pull/716) | 58 | 39 | −19 | −32.8% | ≤40 | ✅ Exceeded by 1 |
| **Total** | 3 PRs | 114 | 39 | **−75** | **−65.8%** | ≤40 | ✅ **Goal Achieved** |

### Cumulative Impact

- **Broken Targets:** 114 → 39 (−65.8%)
- **Files Changed:** 56 total (13 + 14 + 18 per wave, some overlap)
- **Token Policy Violations Resolved:** 85 (48 + 38 + 27 per wave, includes pre-existing)
- **Commits:** 19 total (8 + 4 + 7 per wave)
- **CI Checks:** 74 total (27 + 23 + 10 + 14 required, all PASS)

### Baseline Status

**Current State (Post-Wave 5):**
- **Broken Targets:** 39 (Gate PASS as baseline)
- **Total References:** ~5806
- **Files Scanned:** 873 (9 ignored)
- **Snapshot:** [docs_graph_snapshot_wave5_after.txt](docs_graph_snapshot_wave5_after.txt)

---

## What Changed

### High-Level Summary

**Wave 3 (PR #712):**
- Targeted high-impact broken targets (historical scripts, illustrative paths, Docker volume syntax)
- Fixed Top-10 by reference count
- 25 files changed, 48 token-policy escapes applied
- Discovered and fixed 19 pre-existing violations in 8 files

**Wave 4 (PR #714):**
- Cluster-based approach (leading dots, relative paths, illustrative scripts)
- Institutionalized CI-Parity pre-PR scanning workflow (267-line operator guide)
- 14 files changed, 38 pre-existing violations resolved
- Created [PRE_PR_FULL_SCAN_CI_PARITY.md](../PRE_PR_FULL_SCAN_CI_PARITY.md) operator guide

**Wave 5 (PR #716):**
- Final cluster push (illustrative dev guides, historical merge log branch names)
- 18 files changed, 27 violations resolved (26 pre-existing + 1 CI follow-up)
- Auto-merge enabled (merged 21s after enablement)

### Key Patterns Fixed

1. **Historical Scripts:** Missing scripts referenced in docs → escaped as illustrative with semantic marker
2. **Leading Dots:** Relative paths like `.&#47;scripts&#47;...` → escaped or converted to repo-relative
3. **Docker Volume Syntax:** `.&#47;reports:&#47;reports` → escaped with semantic note
4. **Illustrative Paths:** Template paths like `{STRATEGY_ID}` → escaped + marker
5. **Historical Branches:** Old PR branch names like `origin&#47;phase-4b-m2` → escaped + (historical)
6. **Typos:** Minor typos in target paths → corrected where clear, escaped where ambiguous

### Deliverables (All Waves)

**Remediation Reports:**
- [REMEDIATION_WAVE3_2026-01-14.md](REMEDIATION_WAVE3_2026-01-14.md) (334 lines)
- [REMEDIATION_WAVE4_2026-01-14.md](REMEDIATION_WAVE4_2026-01-14.md) (265 lines)
- [REMEDIATION_WAVE5_2026-01-14.md](REMEDIATION_WAVE5_2026-01-14.md) (408 lines)

**Snapshots (Before/After):**
- Wave 3: [before](docs_graph_snapshot_wave3_before.txt) (116 lines) / [after](docs_graph_snapshot_wave3_after.txt) (91 lines)
- Wave 4: [before](docs_graph_snapshot_wave4_before.txt) (89 lines) / [after](docs_graph_snapshot_wave4_after.txt) (67 lines)
- Wave 5: [before](docs_graph_snapshot_wave5_before.txt) (60 lines) / [after](docs_graph_snapshot_wave5_after.txt) (41 lines)

**Merge Logs:**
- [PR_712_MERGE_LOG.md](../merge_logs/PR_712_MERGE_LOG.md)
- [PR_714_MERGE_LOG.md](../merge_logs/PR_714_MERGE_LOG.md)
- [PR_716_MERGE_LOG.md](../merge_logs/PR_716_MERGE_LOG.md)

**Process Documentation:**
- [PRE_PR_FULL_SCAN_CI_PARITY.md](../PRE_PR_FULL_SCAN_CI_PARITY.md) (267 lines, Wave 4)

---

## Verification

### Operator Commands (Snapshot Mode, No Watch)

To verify the current state of the docs graph:

```bash
# Comprehensive Docs Gates Snapshot (all 3 gates)
scripts/ops/pt_docs_gates_snapshot.sh

# Reference Targets only (current baseline)
scripts/ops/verify_docs_reference_targets.sh

# Token Policy (changed files, optional)
uv run python scripts/ops/validate_docs_token_policy.py --changed --base main

# CI-Parity Mode (full scan, mirrors CI)
uv run python scripts/ops/validate_docs_token_policy.py --all
```

### Expected Results

- **Docs Reference Targets Gate:** PASS (39 broken targets as baseline)
- **Docs Token Policy Gate:** PASS (no violations in changed files)
- **Docs Diff Guard Policy Gate:** PASS (docs-only changes)

### CI Verification

All PRs passed all required checks:
- Docs Token Policy Gate
- Docs Reference Targets Gate
- Docs Diff Guard Policy Gate
- Audit
- Lint Gate
- Policy Critic Gate
- Test Health Automation (CI Health Gate)
- Strategy Smoke
- Tests (3.9/3.10/3.11)
- Workflow Dispatch Guard

---

## Risk / Rollback

**Risk Level:** LOW

**Reasoning:**
- Docs-only changes (no code, config, or runtime logic)
- Mechanical escapes only (semantic-preserving)
- All gates passed (comprehensive verification)
- Fully reversible (revert merge commits)

### Rollback Instructions (if needed)

In case of unexpected issues, each wave can be individually reverted:

**Wave 3:**
```bash
git revert -m 1 02c271adda3f34ecf4d71658897d47f659f404f6
# Create PR with revert commit
```

**Wave 4:**
```bash
git revert -m 1 0162ce46f9a696804cfd21ff1ab5b11645d3e7b0
# Create PR with revert commit
```

**Wave 5:**
```bash
git revert -m 1 1a76f413612e0b69211966669c012d0a6c48bdc1
# Create PR with revert commit
```

**Full Rollback (all 3 waves):**
```bash
git revert -m 1 1a76f413612e0b69211966669c012d0a6c48bdc1
git revert -m 1 0162ce46f9a696804cfd21ff1ab5b11645d3e7b0
git revert -m 1 02c271adda3f34ecf4d71658897d47f659f404f6
# Create PR with all 3 revert commits
```

---

## Operator Playbook: Repeatable Wave N Workflow

For future docs graph remediation waves, follow this proven workflow:

### 1. Baseline Snapshot

```bash
# Generate snapshot
scripts/ops/verify_docs_reference_targets.sh > docs/ops/graphs/docs_graph_snapshot_waveN_before.txt

# Extract top candidates
grep "Missing targets:" docs/ops/graphs/docs_graph_snapshot_waveN_before.txt
```

**Analyze:** Group targets by theme (historical, illustrative, typos, moved files, etc.).

### 2. Target Selection

**Criteria:**
- High impact (multiple references) OR thematic cluster
- Clear remediation strategy (escape vs. correct path vs. add marker)
- Low risk (no semantic ambiguity)

**Avoid:**
- Ambiguous targets (unclear if typo or intentional)
- External URLs (different policy)
- Targets requiring code changes

### 3. Mechanical Fixes

**Apply patterns:**
- **Historical/Missing:** Escape slashes (`&#47;`) + add semantic marker (historical/illustrative)
- **Typos:** Correct path if obvious, escape + marker if ambiguous
- **Relative Paths:** Convert to repo-relative or escape
- **Illustrative Examples:** Escape + marker, never link-ify

**Rules:**
- KEEP EVERYTHING (no content deletions)
- Mechanical escapes only (no rewording)
- Preserve semantics (escape instead of delete)
- Token-Policy safe (always `&#47;` in inline-code)

### 4. Verification Loop

```bash
# Local scans (iterative)
uv run python scripts/ops/validate_docs_token_policy.py --changed --base main
scripts/ops/verify_docs_reference_targets.sh

# Pre-PR Full Scan (CI-Parity, mandatory)
uv run python scripts/ops/validate_docs_token_policy.py --all
scripts/ops/pt_docs_gates_snapshot.sh
```

**Fix any violations → repeat verification.**

### 5. After Snapshot + Report

```bash
# Generate after snapshot
scripts/ops/verify_docs_reference_targets.sh > docs/ops/graphs/docs_graph_snapshot_waveN_after.txt

# Create remediation report
# Template: REMEDIATION_WAVEN_YYYY-MM-DD.md (see Wave 3/4/5 for structure)
```

**Calculate deltas:** before → after, % change, goal achievement.

### 6. PR Creation

```bash
# Create branch
git switch -c docs/phase9c-broken-targets-waveN

# Commit changes
git add -A
git commit -m "docs(ops): remediation waveN broken targets + snapshots"

# Push + create PR
git push -u origin docs/phase9c-broken-targets-waveN
gh pr create --title "docs(ops): Phase 9C Wave N remediation (broken targets + token policy)" \
  --body "$(cat PHASE9C_WAVEN_PR_BODY.md)"
```

### 7. Post-Merge Docs (Optional)

```bash
# Create merge log (after PR merged)
# Location: docs/ops/merge_logs/PR_XXX_MERGE_LOG.md
# Template: See PR_712/714/716_MERGE_LOG.md

# Update Evidence Index
# Add new entry: EV-YYYYMMDD-PRXXX-WAVEN-DOCS-REMEDIATION

# Create PR for post-merge docs
git switch -c docs/prXXX-merge-log
# ... (commit + push + PR)
```

### 8. Gate Validation

**All PRs must pass:**
- Docs Token Policy Gate
- Docs Reference Targets Gate
- Docs Diff Guard Policy Gate
- Audit
- Lint Gate

**Auto-merge (if all green):**
```bash
gh pr merge XXX --squash --auto --delete-branch
```

---

## Next Candidates: Remaining 39 Broken Targets

Based on the [current snapshot](docs_graph_snapshot_wave5_after.txt), the remaining 39 targets fall into these categories:

### Category 1: Missing Core Docs (9 targets)

Missing documentation files that were referenced but never created or were moved:
- Architecture overviews (Data Layer, Registry Engine)
- Exchange integration guide template
- Live status notes
- Portfolio decision log
- Risk management summaries

**Remediation Strategy:** Escape + semantic marker (historical/moved), or create stub doc if high-value.

### Category 2: Missing Source Files (16 targets)

Source code references that are no longer valid (refactored, moved, or deleted):
- Data layer components (contracts, cache, lake schema)
- Backtest engine internals
- Strategy base classes
- Notification/health modules
- Execution/position sizing
- WebUI service layers

**Remediation Strategy:** Escape + (moved/refactored) marker. Do NOT create source files.

### Category 3: Typos / Misspellings (2 targets)

Minor typos in target paths:
- `docs&#47;PEAK_TRADE_STATUS_OVERVERVIEW.md` (double V)
- `docs&#47;ai&#47;…` (ellipsis reference)

**Remediation Strategy:** Correct typo if obvious, or escape + note.

### Category 4: Template/Illustrative Paths (4 targets)

Paths with placeholders or template syntax:
- `docs&#47;strategy_profiles&#47;{STRATEGY_ID}_PROFILE_v1.md`
- `src&#47;backtest&#47;engine.py:424-440` (line-range reference)
- `..&#47;POSITION_SIZING.md` (ambiguous relative)

**Remediation Strategy:** Escape + (illustrative/template) marker.

### Category 5: Historical/Moved Paths (6 targets)

Paths that were valid historically but no longer exist:
- Roadmap documents (moved to archive or deleted)
- Old phase reports (consolidated)
- Merge log templates (deprecated)

**Remediation Strategy:** Escape + (historical) marker, or link to archived version.

### Category 6: Ellipsis / Wildcards (2 targets)

References using ellipsis or wildcards as placeholders:
- `docs&#47;ai&#47;…`
- `docs&#47;…`

**Remediation Strategy:** Escape ellipsis (`&#47;` for slashes), add (illustrative) marker.

### Prioritization for Wave 6 (if needed)

If further reduction is desired (e.g., target ≤30):

**High Priority:** Category 1 (Missing Core Docs) + Category 3 (Typos) — Clear fixes, high clarity.  
**Medium Priority:** Category 4 (Templates) + Category 5 (Historical) — Mechanical escapes + markers.  
**Low Priority:** Category 2 (Source Files) + Category 6 (Ellipsis) — Already semantically clear, low user impact.

**Estimated Effort:** Wave 6 could target 10–15 targets (Category 1 + 3 + partial 4/5), reducing baseline to ~24–29.

---

## References

### Wave Reports
- [REMEDIATION_WAVE3_2026-01-14.md](REMEDIATION_WAVE3_2026-01-14.md) — Wave 3 detailed report
- [REMEDIATION_WAVE4_2026-01-14.md](REMEDIATION_WAVE4_2026-01-14.md) — Wave 4 detailed report
- [REMEDIATION_WAVE5_2026-01-14.md](REMEDIATION_WAVE5_2026-01-14.md) — Wave 5 detailed report

### Snapshots
- **Wave 3:** [before](docs_graph_snapshot_wave3_before.txt) / [after](docs_graph_snapshot_wave3_after.txt)
- **Wave 4:** [before](docs_graph_snapshot_wave4_before.txt) / [after](docs_graph_snapshot_wave4_after.txt)
- **Wave 5:** [before](docs_graph_snapshot_wave5_before.txt) / [after](docs_graph_snapshot_wave5_after.txt)

### Merge Logs
- [PR #712 Merge Log](../merge_logs/PR_712_MERGE_LOG.md) — Wave 3
- [PR #714 Merge Log](../merge_logs/PR_714_MERGE_LOG.md) — Wave 4
- [PR #716 Merge Log](../merge_logs/PR_716_MERGE_LOG.md) — Wave 5

### Pull Requests
- [PR #712](https://github.com/rauterfrank-ui/Peak_Trade/pull/712) — Wave 3 (Merged: 02c271ad)
- [PR #714](https://github.com/rauterfrank-ui/Peak_Trade/pull/714) — Wave 4 (Merged: 0162ce46)
- [PR #716](https://github.com/rauterfrank-ui/Peak_Trade/pull/716) — Wave 5 (Merged: 1a76f413)
- [PR #717](https://github.com/rauterfrank-ui/Peak_Trade/pull/717) — Post-Merge Docs for Wave 5 (Merged: 61224197)

### Process Documentation
- [PRE_PR_FULL_SCAN_CI_PARITY.md](../PRE_PR_FULL_SCAN_CI_PARITY.md) — CI-Parity operator guide (Wave 4)

### Evidence Index
- [EVIDENCE_INDEX.md](../EVIDENCE_INDEX.md) — Operational evidence registry (see entries for PR #712, #714, #716)

---

**Document Version:** 1.0  
**Created:** 2026-01-14  
**Author:** ops (Phase 9C closeout)  
**Status:** ✅ Mission Complete — Baseline 39 targets, Goal Achieved
