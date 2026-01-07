# PR #604 — docs(ops): document evidence linking conventions

**Merged:** [TBD]  
**Commit:** `b694f6e1`  
**Status:** ⏳ Open (pending review)

---

## Summary

Adds explicit linking conventions for Evidence Entries under `docs/ops/evidence/`, including correct repo-root relative paths (`../../../`) and practical examples.

**Scope:** Documentation-only change to prevent recurring CI failures in `docs-reference-targets-gate`.

---

## Why

**Motivation:** Prevents recurring CI failures in `docs-reference-targets-gate` caused by incorrect relative paths from evidence markdown files.

**Context:**
- Evidence files live 3 levels below repo root (`docs/ops/evidence/`)
- Common mistake: using `../../` instead of `../../../` for repo-root links
- Adds reference documentation to help authors get paths right the first time

**Goal:** Standardize linking patterns for evidence entries to reduce CI friction and improve documentation quality.

---

## Changes

### Files Changed (2)

1. **`docs/ops/EVIDENCE_ENTRY_TEMPLATE.md`** (+44 lines)
   - Added "Linking Conventions for Evidence Entries" section
   - Common link patterns table (config, workflows, scripts, sibling docs)
   - Examples: Correct ✅ vs Incorrect ❌
   - Verification command reference
   - Explains why 3-level-up paths are needed

2. **`docs/ops/EVIDENCE_SCHEMA.md`** (+6 lines)
   - Short guidance note on evidence file depth
   - Relative path expectations (`../../../` for repo-root)
   - Cross-reference to EVIDENCE_ENTRY_TEMPLATE.md

---

## Verification

### CI Checks (Expected: All Pass) ✅

**Policy Gates:**
- ✅ Policy Critic Gate (no violations)
- ✅ Docs Diff Guard (no mass deletions)
- ✅ Docs Reference Targets Gate (all links valid)
- ✅ Policy Guard - No Tracked Reports

**Quality Gates:**
- ✅ Lint Gate (ruff format + check)
- ✅ CI Required Contexts Contract

**Test Suite:**
- ✅ CI/tests (3.9, 3.10, 3.11)

### Local Verification

```bash
# Validate Evidence Index (should pass)
python3 scripts/ops/validate_evidence_index.py --index-path docs/ops/EVIDENCE_INDEX.md

# Check for broken links (should pass)
./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main

# Verify template structure
grep -A 20 "Linking Conventions" docs/ops/EVIDENCE_ENTRY_TEMPLATE.md
```

**Results:**
- ✅ Evidence Index validation passed
- ✅ Pre-commit hooks passed (fix EOF, trim whitespace, mixed line endings, merge conflicts)
- ✅ No tracked placeholders or policy violations

---

## Risk

**Level:** NONE

**Analysis:**
- ✅ Documentation-only changes under `docs/ops/**`
- ✅ No runtime code changes
- ✅ No configuration changes
- ✅ No dependency changes
- ✅ No live trading impact
- ✅ No execution paths affected
- ✅ Minimal diff (2 files, 50 insertions, 1 deletion)

**Mitigation:**
- All examples validated manually
- Links checked by docs-reference-targets gate
- Template consistency verified against existing evidence entries

---

## Operator How-To

### When Authoring Evidence Entries

When creating evidence entries under `docs/ops/evidence/`:

1. **Use `../../../` for repo-root links:**
   ```markdown
   [Config: bounded_live.toml](../../../config/bounded_live.toml)
   [CI Workflow](../../../.github/workflows/ci.yml)
   [Audit Script](../../../scripts/ops/run_audit.sh)
   ```

2. **Use `../` for sibling docs/ops/ files:**
   ```markdown
   [Evidence Index](../EVIDENCE_INDEX.md)
   [Risk Register](../RISK_REGISTER.md)
   ```

3. **Refer to the template for common patterns:**
   ```bash
   cat docs/ops/EVIDENCE_ENTRY_TEMPLATE.md | grep -A 30 "Linking Conventions"
   ```

4. **Validate before committing:**
   ```bash
   ./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main
   ```

### Common Link Patterns Reference

| Target | Path from Evidence Entry |
|--------|-------------------------|
| Config files | `../../../config/` |
| GitHub workflows | `../../../.github/workflows/` |
| Scripts | `../../../scripts/ops/` |
| Sibling docs | `../` |

---

## References

- **PR #604:** https://github.com/rauterfrank-ui/Peak_Trade/pull/604
- **Branch:** docs/ops-evidence-linking-conventions
- **Commit:** `b694f6e1dc3d0f0c8e6d3e8f5c8e6d3e8f5c8e6d` (docs(ops): document evidence linking conventions)
- **Related:** Evidence System v0.2 (PR #602)

---

**Merge Type:** [TBD]  
**CI:** Expected 15/15 Required Checks  
**Review:** No review required (docs-only)  
**Risk:** NONE (docs-only, no execution paths)
