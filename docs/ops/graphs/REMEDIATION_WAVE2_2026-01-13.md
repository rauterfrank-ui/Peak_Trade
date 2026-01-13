# Docs Graph Remediation — Wave 2 (Broken Targets)

**Date:** 2026-01-13  
**Baseline:** Post-Wave 1 snapshot (`docs_graph_snapshot_wave1_after.json`)  
**Phase:** 9C  
**Status:** In Progress

---

## Executive Summary

Wave 2 addresses **broken targets** identified after Wave 1's orphan remediation. Analysis reveals that **81% of broken targets (148/183) are false positives**: escaped paths (`&#47;`) in illustrative documentation that are correctly token-policy compliant but incorrectly parsed as link targets by the graph scanner.

**Strategy:** Fix the root cause (escaped paths in link context) + address genuine missing files.

**Targets:**
- **Broken targets:** Reduce from 183 to <=135 (goal: >= -48)
- **Broken anchors:** Reduce from 7 to <=2 (goal: >= -5)
- **Orphans:** Maintain or improve from 495

**Risk:** LOW — Docs-only scope, no runtime impact

---

## Triage Analysis (Post-Wave 1)

### Baseline Metrics
```bash
./scripts/ops/pt_docs_graph_triage.sh docs/ops/graphs/snapshots/2026-01-13/docs_graph_snapshot_wave1_after.json
```

**Output:**
- Broken targets: **183**
- Broken anchors: **7**
- Orphaned pages: **495**

### Root Cause Breakdown

| Category | Count | % | Fix Strategy |
|----------|-------|---|--------------|
| **Escaped paths (illustrative)** | 148 | 81% | Convert link syntax to non-link format (inline code or remove brackets) |
| **Real missing files** | 35 | 19% | Remove link or correct path |

---

## Problem: Escaped Paths as False Positives

**Issue:** Token Policy requires escaped slashes (`&#47;`) in illustrative paths to prevent false positives. However, when these escaped paths appear in **markdown link syntax** `[text](path&#47;with&#47;slashes)`, the graph scanner still treats them as link targets and reports them as broken.

**Examples:**

1. **In link context** (FALSE POSITIVE):
   ```markdown
   - [Link](.cursor&#47;rules&#47;peak-trade-governance.mdc)
   ```
   → Scanner tries to resolve `.cursor&#47;rules&#47;...` as a file path
   → Reports as broken target (even though correctly escaped per token policy)

2. **In inline code** (CORRECT):
   ```markdown
   - File: `.cursor&#47;rules&#47;peak-trade-governance.mdc`
   ```
   → Scanner ignores (not in link syntax)
   → No false positive

**Root Cause:** Escaped paths are token-policy compliant but incompatible with link syntax in the reference scanner context.

---

## Fix Strategy Patterns

### Pattern 1: Escaped Paths in Links → Inline Code (Primary)

**Before:**
```markdown
See [governance rules](.cursor&#47;rules&#47;peak-trade-governance.mdc) for details.
```

**After:**
```markdown
See governance rules (`.cursor&#47;rules&#47;peak-trade-governance.mdc`) for details.
```

**Impact:** Removes false positive, preserves information, maintains token policy compliance.

---

### Pattern 2: Escaped Paths in Links → Remove Brackets (If text is path)

**Before:**
```markdown
- [`.cursor&#47;rules&#47;peak-trade-governance.mdc`](.cursor&#47;rules&#47;peak-trade-governance.mdc)
```

**After:**
```markdown
- `.cursor&#47;rules&#47;peak-trade-governance.mdc`
```

**Impact:** Simplifies (text == target), removes false positive.

---

### Pattern 3: Real Missing Files → Remove Link

**Before:**
```markdown
See [Phase 4E Closeout Guide](PHASE4E_CLOSEOUT_OPERATOR_GUIDE.md) for details.
```

**After (if file genuinely missing):**
```markdown
See Phase 4E Closeout Guide (historical, file archived) for details.
```

**Impact:** Removes broken link, preserves context.

---

### Pattern 4: Real Missing Files → Correct Path

**Before:**
```markdown
- [Config](../config.toml)
```

**After (if file exists elsewhere):**
```markdown
- [Config](../../config.toml)
```

**Impact:** Fixes broken link, maintains navigation.

---

## Detailed Fix Plan

### Phase A: Escaped Path Cleanup (148 targets)

**Top Offenders (by file):**

1. **PHASE8_DOCS_INTEGRITY_HARDENING_IMPLEMENTATION_SUMMARY.md** (~8 escaped paths)
   - `.cursor&#47;rules&#47;*.mdc`
   - `.github&#47;workflows&#47;*.yml`
   - `docs&#47;ops&#47;runbooks&#47;*.md`
   - `scripts&#47;ops&#47;*.py`

2. **Root-level PHASE*.md files** (~50 escaped paths total)
   - Various `docs&#47;` and `src&#47;` references

3. **docs/*.md files** (~90 escaped paths total)
   - `..&#47;config.toml`, `..&#47;src&#47;*.py`, etc.

**Fix Action:** Apply Pattern 1 or Pattern 2 depending on context.

---

### Phase B: Real Missing Files (35 targets)

**Top Missing Files:**

| Missing File | References | Fix Action |
|--------------|------------|------------|
| `PHASE4E_CLOSEOUT_OPERATOR_GUIDE.md` | 1 | Remove link (file archived/renamed) |
| `RESEARCH_PIPELINE.md` | 2 | Remove link (superseded) |
| `SCHEDULER.md` | 1 | Remove link (superseded) |
| `KNOWLEDGE_BASE_INDEX.md` | 2 | Correct path or remove |
| `EXECUTION_PIPELINE_PHASE_16A_V2.md` | 1 | Remove link (historical) |

**Fix Action:** Apply Pattern 3 (remove link) or Pattern 4 (correct path) as appropriate.

---

### Phase C: Broken Anchors (7 targets)

**Identified Issues:**
- AN-001: Missing anchors in `INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md`
- AN-002: `#ev-20260113-runbooks-frontdoor` in EVIDENCE_INDEX (already fixed in Wave 1)

**Fix Action:**
- Verify anchor syntax in target files
- Add explicit `<a id="..."></a>` tags if missing
- Update linking files to match actual anchor IDs

---

## Validation Plan

### Pre-Fix Baseline (Post-Wave 1)
```bash
./scripts/ops/pt_docs_graph_triage.sh docs/ops/graphs/snapshots/2026-01-13/docs_graph_snapshot_wave1_after.json
```

**Metrics:**
- Broken targets: 183
- Broken anchors: 7
- Orphans: 495

### Post-Fix Verification
```bash
uv run python scripts/ops/docs_graph_snapshot.py --out /tmp/wave2_after.json
./scripts/ops/pt_docs_graph_triage.sh /tmp/wave2_after.json
```

**Expected Metrics:**
- Broken targets: <= 135 (reduction >= 48)
- Broken anchors: <= 2 (reduction >= 5)
- Orphans: <= 495 (maintain or improve)

### Gate Validation
```bash
# Token Policy Gate
python scripts/ops/validate_docs_token_policy.py --base origin/main

# Reference Targets Gate
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

**Expected:** All gates PASS

---

## Do Not Regress Checklist

- [ ] No new token policy violations introduced
- [ ] No illustrative paths in link syntax `[text](path&#47;with&#47;slashes)`
- [ ] All escaped paths outside link context (inline code, plain text, or code blocks)
- [ ] No content deleted (only link syntax adjusted or links removed with context preserved)
- [ ] All fixes maintain semantic meaning

---

## Success Criteria

- [x] Post-Wave 1 baseline established (183 broken targets)
- [x] Real missing file links cleaned up (35 → ~10 remaining)
- [x] Post-fix snapshot generated (`docs_graph_snapshot_wave2_after.json`)
- [x] Broken targets reduced by 40 (183 → 143)
- [ ] Escaped path false positives addressed (137 remaining - requires scanner fix)
- [ ] Broken anchors addressed (7 unchanged - deferred to Wave 3)
- [ ] All docs gates pass (pending PR validation)

## Wave 2 Results

**Baseline (Post-Wave 1):**
- Broken targets: 183
- Broken anchors: 7
- Orphaned pages: 496

**After Wave 2:**
- Broken targets: **143** (-40, target was -48)
- Broken anchors: 7 (unchanged, focus was on targets)
- Orphaned pages: 496 (stable)

**Analysis:**
- Fixed **~25 real missing file links** (removed or marked as archived/planned)
- Remaining **~143 broken targets** are mostly **escaped path false positives**
  - These are links to files that exist (e.g., Makefile, source files, test files with relative paths)
  - But scanner reports them as broken because HTML entities (`&#47;`) are in link targets
  - Root cause: Scanner behavior with escaped paths in markdown link syntax
  - Recommended fix: Update scanner to unescape HTML entities before resolving paths

---

## References

- **Post-Wave 1 Snapshot:** `docs&#47;ops&#47;graphs&#47;snapshots&#47;2026-01-13&#47;docs_graph_snapshot_wave1_after.json`
- **Wave 1 Report:** `docs&#47;ops&#47;graphs&#47;REMEDIATION_WAVE1_2026-01-13.md`
- **Triage Tool:** `scripts&#47;ops&#47;pt_docs_graph_triage.sh`
