# Legacy Merge Log Violations Backlog

**Generated:** 2025-12-21 17:19:19  
**Status:** Forward-only policy active (CI guard non-blocking)  
**Total Logs:** 28  
**Compliant:** 1  
**With Violations:** 27

## Goal

- **Forward-only Policy:** New merge logs must comply with compact standard
- Legacy logs are migrated on-demand, prioritized by leverage
- CI guard is non-blocking to avoid workflow disruption

## Standard Requirements

All new `PR_*_MERGE_LOG.md` files must include:

### Required Headers
- `**Title:**` — PR title
- `**PR:**` — PR number (#XXX)
- `**Merged:**` — Merge date (YYYY-MM-DD)
- `**Merge Commit:**` — Commit hash (short)
- `**Branch:**` — Branch name (deleted/active)
- `**Change Type:**` — Change type (additive, breaking, etc.)

### Required Sections
- `## Summary` — Brief summary (2-3 sentences)
- `## Motivation` — Why this change?
- `## Changes` — What changed? (structured)
- `## Files Changed` — File list with checksums
- `## Verification` — CI checks, local tests
- `## Risk Assessment` — Risk evaluation

### Compactness
- **< 200 lines** (guideline)
- Focus on essentials, avoid verbose details

## Reference Implementation

✅ **`docs/ops/PR_206_MERGE_LOG.md`** — Use as template for new logs

## Prioritized Backlog

**Strategy:** Newest PRs first (highest leverage, likely more relevant)

### High Priority (≥10 violations)

- [ ] **PR #201** — `PR_201_MERGE_LOG.md` (10E, 0W)
- [ ] **PR #199** — `PR_199_MERGE_LOG.md` (9E, 1W)
- [ ] **PR #186** — `PR_186_MERGE_LOG.md` (10E, 1W)
- [ ] **PR #182** — `PR_182_MERGE_LOG.md` (9E, 1W)
- [ ] **PR #180** — `PR_180_MERGE_LOG.md` (9E, 1W)
- [ ] **PR #161** — `PR_161_MERGE_LOG.md` (9E, 1W)
- [ ] **PR #154** — `PR_154_MERGE_LOG.md` (11E, 0W)
- [ ] **PR #121** — `PR_121_MERGE_LOG.md` (10E, 0W)
- [ ] **PR #116** — `PR_116_MERGE_LOG.md` (10E, 0W)
- [ ] **PR #112** — `PR_112_MERGE_LOG.md` (11E, 0W)
- [ ] **PR #110** — `PR_110_MERGE_LOG.md` (10E, 0W)
- [ ] **PR #93** — `PR_93_MERGE_LOG.md` (11E, 0W)
- [ ] **PR #90** — `PR_90_MERGE_LOG.md` (11E, 1W)
- [ ] **PR #87** — `PR_87_MERGE_LOG.md` (12E, 0W)

### Medium Priority (5-9 violations)

- [ ] **PR #204** — `PR_204_MERGE_LOG.md` (9E, 0W)
- [ ] **PR #197** — `PR_197_MERGE_LOG.md` (7E, 1W)
- [ ] **PR #195** — `PR_195_MERGE_LOG.md` (7E, 1W)
- [ ] **PR #193** — `PR_193_MERGE_LOG.md` (9E, 0W)
- [ ] **PR #185** — `PR_185_MERGE_LOG.md` (8E, 1W)
- [ ] **PR #183** — `PR_183_MERGE_LOG.md` (6E, 1W)
- [ ] **PR #143** — `PR_143_MERGE_LOG.md` (8E, 0W)
- [ ] **PR #136** — `PR_136_MERGE_LOG.md` (9E, 0W)
- [ ] **PR #114** — `PR_114_MERGE_LOG.md` (9E, 0W)
- [ ] **PR #85** — `PR_85_MERGE_LOG.md` (9E, 0W)
- [ ] **PR #80** — `PR_80_MERGE_LOG.md` (9E, 0W)
- [ ] **PR #78** — `PR_78_MERGE_LOG.md` (9E, 0W)
- [ ] **PR #76** — `PR_76_MERGE_LOG.md` (9E, 0W)

## Tools & Resources

### Audit Tool
```bash
# Check all logs
python scripts/audit/check_ops_merge_logs.py

# Generate reports
python scripts/audit/check_ops_merge_logs.py \
  --report-md reports/ops/violations.md \
  --report-json reports/ops/violations.json
```

### Regenerate This Backlog
```bash
python scripts/ops/generate_legacy_merge_log_backlog.py
```

### CI Integration
- **Workflow:** `.github/workflows/audit.yml`
- **Status:** Non-blocking guard active
- **Future:** Can flip to blocking when legacy backlog is cleared

## Migration Strategy

1. **Forward-only:** All new PRs must be compliant (enforced by review)
2. **Legacy:** Migrate on-demand, starting with high-priority items
3. **Template:** Use `PR_206_MERGE_LOG.md` as reference
4. **Review:** Update this backlog after migrations

## Next Steps

1. New PRs: Use compliant format (see reference implementation)
2. Legacy: Pick items from backlog as needed/prioritized
3. CI Guard: Keep non-blocking until backlog is significantly reduced
4. Documentation: Keep this backlog up-to-date by re-running generator
