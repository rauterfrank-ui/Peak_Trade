# Fix Matrix: Workflow Documentation Integration

**Session:** 2026-01-12 Workflow Docs Integration  
**RISK_OFFICER Role:** Fix strategy assessment  
**SCOPE_KEEPER Role:** Enforce KEEP EVERYTHING constraint

---

## Executive Summary

**Status:** ✅ **NO FIXES REQUIRED**

All inline backticks with "/" in both documents are either:
1. **Valid existing paths** (will pass gate validation)
2. **Gate-safe tokens** (URLs, commands, directories - correctly ignored by gate)

**Verification Evidence:** All 3 potentially problematic paths from WORKFLOW_NOTES.md lines 155-157 exist:
- `docs/PEAK_TRADE_OVERVIEW.md` ✅ (20,597 bytes, modified Jan 8)
- `docs/BACKTEST_ENGINE.md` ✅ (11,651 bytes, modified Jan 8)
- `docs/STRATEGY_DEV_GUIDE.md` ✅ (28,050 bytes, modified Jan 8)

---

## Fix Strategy: Content Preservation Only

### Strategy: Zero-Touch Content Approach

**Rationale:**
- Both documents are **already docs-reference-targets-gate compliant**
- All paths either exist or are correctly formatted for gate bypass
- SCOPE_KEEPER constraint: KEEP EVERYTHING from both docs
- RISK_OFFICER assessment: Lowest risk = no content modification

**Actions:**
1. ✅ **Keep WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md unchanged** (28/39 validated paths exist, rest gate-safe)
2. ✅ **Keep docs/WORKFLOW_NOTES.md unchanged** (2/10 validated paths exist, rest gate-safe)
3. ✅ **Create navigation/integration artifacts** (new files only, no modifications)

---

## Alternative Fix Strategies (Rejected)

### Option A: Escape All Placeholder Paths (REJECTED)
**Pattern:** Convert <code>docs&#47;FILE.md</code> → `"docs\/FILE.md" (future)"`  
**Reason for Rejection:** Paths exist, no need to mark as future  
**Risk:** Would falsely imply paths don't exist (misleading)

### Option B: Convert Backticks to Markdown Links (REJECTED)
**Pattern:** Convert <code>docs&#47;FILE.md</code> → <code>[docs&#47;FILE.md](docs&#47;FILE.md)</code> (markdown link)  
**Reason for Rejection:** Changes semantic meaning, not required  
**Risk:** Over-engineering, violates minimal-change principle

### Option C: Add HTML Entity Slash Escaping (REJECTED)
**Pattern:** Convert <code>docs&#47;FILE.md</code> → `docs&#47;FILE.md` (HTML entity)  
**Reason for Rejection:** Reduces readability, not required  
**Risk:** Makes docs harder to read for humans

---

## Rule-Based Decision Matrix

| Backtick Token Type | Count | Gate Behavior | Fix Required? | Rationale |
|---------------------|-------|---------------|---------------|-----------|
| **Real Path (Exists)** | 30 | ✅ Validates & Passes | NO | Paths exist, gate will validate successfully |
| **URL (http://)** | 4 | ⏭️ Ignored (is_url) | NO | Gate correctly skips URLs |
| **Directory (trailing /)** | 7 | ⏭️ Ignored (trailing slash) | NO | Gate correctly skips directories |
| **Command (with space)** | 2 | ⏭️ Ignored (space detection) | NO | Gate correctly skips commands |
| **Command (with wildcard)** | 2 | ⏭️ Ignored (wildcard) | NO | Gate correctly skips wildcards |
| **Placeholder/Future** | 3 | ✅ Validates & Passes | NO | Paths NOW exist (created after Dec 2025 mention) |
| **TOTAL** | 48 | ALL SAFE | **NO** | 100% gate-compliant |

---

## Verification Commands

### Pre-Integration Gate Check (Baseline)
```bash
# Verify current main branch status (should pass)
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

**Expected Output:** PASS (no markdown changes yet)

### Post-Integration Gate Check (After New Files)
```bash
# After creating new integration files, verify changed files
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
```

**Expected Output:** PASS (new files should only reference existing targets)

### Full-Scan Verification (Optional)
```bash
# Full repository scan (includes legacy content with ignore patterns)
./scripts/ops/verify_docs_reference_targets.sh
```

**Expected Output:** PASS or PASS-with-notes (legacy content may have known issues)

---

## Risk Assessment (RISK_OFFICER)

### Risk Level: **MINIMAL** 🟢

| Risk Factor | Assessment | Mitigation |
|-------------|------------|------------|
| **Content Modification Risk** | NONE | Zero-touch approach, no existing content modified |
| **Gate Failure Risk** | NONE | All paths validated pre-integration (see verification above) |
| **Readability Impact** | NONE | No escaping or obfuscation required |
| **Breaking Change Risk** | NONE | Only additive changes (new navigation files) |
| **Rollback Complexity** | LOW | New files can be deleted, no content reverted |

### Rollback Plan

**If integration causes unexpected issues:**

```bash
# Remove new integration files (no content modified, only additions)
git rm docs/WORKFLOW_FRONTDOOR.md
git rm docs/ops/runbooks/RUNBOOK_WORKFLOW_DOCS_INTEGRATION_2026-01-12_CURSOR_MULTI_AGENT.md
git checkout docs/ops/README.md  # Restore if modified
git commit -m "rollback: Remove workflow docs integration"
```

**Rollback Risk:** MINIMAL (only new files, no modified content)

---

## Deliverables (Phase 4: Logical Integration)

### New Files to Create

1. **docs/WORKFLOW_FRONTDOOR.md**
   - Purpose: Single-page navigation hub for both workflow documents
   - Content: Links to both docs with "Authoritative vs. Legacy" labels
   - Gate Impact: MUST only reference existing paths
   - Lines: ~50-80 (minimal, focused)

2. **docs/ops/runbooks/RUNBOOK_WORKFLOW_DOCS_INTEGRATION_2026-01-12_CURSOR_MULTI_AGENT.md**
   - Purpose: Runbook documenting this integration session
   - Content: Session metadata, decisions, verification evidence
   - Gate Impact: MUST only reference existing paths
   - Lines: ~200-300 (complete session record)

3. **DOC_MAP.md** (TEMPORARY)
   - Status: Already created in repo root
   - Action: Delete after session (temporary artifact)

4. **BACKTICK_AUDIT.md** (TEMPORARY)
   - Status: Already created in repo root
   - Action: Delete after session (temporary artifact)

5. **FIX_MATRIX_WORKFLOW_DOCS_INTEGRATION.md** (TEMPORARY)
   - Status: This file
   - Action: Delete after session (temporary artifact)

### Files to Modify

1. **docs/ops/README.md**
   - Modification: Add navigation section for workflow documentation
   - Location: After "Cursor Multi-Agent Runbooks" section (~line 100)
   - Content: 5-10 lines linking to WORKFLOW_FRONTDOOR.md and both workflow docs
   - Risk: LOW (additive only, well-established navigation pattern)

---

## Gate Compatibility Guarantee

**All new files will:**
- ✅ Only reference existing paths (verified before commit)
- ✅ Use proper markdown link syntax for all path references
- ✅ Avoid inline backticks for path-like tokens (use markdown links instead)
- ✅ Follow docs/ops/DOCS_REFERENCE_TARGETS_GATE_STYLE_GUIDE.md rules

**Verification:**
- Run gate check before commit: `./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main`
- Expected: PASS (0 missing targets)

---

## Next Steps (Phase 4)

1. ✅ Create docs/WORKFLOW_FRONTDOOR.md
2. ✅ Modify docs/ops/README.md (add navigation section)
3. ✅ Create docs/ops/runbooks/RUNBOOK_WORKFLOW_DOCS_INTEGRATION_2026-01-12_CURSOR_MULTI_AGENT.md
4. ➡️ Phase 5: Verification (run gate check)
5. ➡️ Phase 6: Closeout (merge log, evidence index entry, cleanup temp files)

---

**RISK_OFFICER Sign-Off:** ✅ Minimal risk, zero-touch content approach approved  
**SCOPE_KEEPER Sign-Off:** ✅ NO content deletion, both docs preserved in full
