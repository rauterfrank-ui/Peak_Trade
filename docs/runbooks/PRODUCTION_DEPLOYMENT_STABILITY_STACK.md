# Runbook — Production Deployment: Stability Stack (Wave A+B)

## Goal
Safely ship the Stability Stack to `main` with clear verification steps and an audit trail.

---

## Preconditions
- `main` is up-to-date
- All CI checks green
- No pending migration steps

---

## Deployment Steps

### 1) Verify main + CI
```bash
git checkout main
git pull --ff-only
gh pr checks <PR_NUMBER> --watch
```

**Expected:** All checks pass (tests, lint, audit, CI health gate)

### 2) Run Local Validation
```bash
# Full test suite
uv run pytest -q

# Specific stability smoke tests
uv run pytest tests/test_stability_smoke.py -v
uv run pytest tests/test_cache_manifest.py -v
uv run pytest tests/test_repro.py -v
```

**Expected:** All tests pass, no errors

### 3) Verify Key Components

#### Cache Manifest System
```bash
# Verify module imports
python -c "from src.data.cache_manifest import CacheManifest; print('✅ CacheManifest available')"
```

#### Reproducibility Helpers
```bash
# Verify repro utilities
python -c "from src.core.repro import get_git_sha, stable_hash_dict; print('✅ Repro tools available')"
```

### 4) Post-Deployment Verification
```bash
# Run validation scripts
bash scripts/validate_git_state.sh
bash scripts/automation/post_merge_verify.sh --expected-head "$(git rev-parse HEAD)"
```

**Expected:** Both scripts report "OK" or "✅"

---

## Rollback Plan

If critical issues are discovered post-merge:

### Option A: Hot Fix
1. Create a fix PR immediately
2. Fast-track through CI
3. Merge with priority review

### Option B: Revert
```bash
git revert <MERGE_SHA> -m 1
git push origin main
```

**Note:** Option A is preferred unless the issue is blocking production operations.

---

## Monitoring After Deployment

### First 24 Hours
- Monitor test suite stability
- Watch for any regressions in CI
- Check that cache manifest operations work as expected

### Key Metrics
- Test pass rate: Should remain 100%
- CI duration: Should not increase significantly
- No new warnings or errors in logs

---

## Emergency Contacts

If issues arise:
1. Check `docs/stability/STABILITY_STACK_COMPLETED.md` for context
2. Review `tests/test_stability_smoke.py` for validation patterns
3. Consult Wave A/B plan documents in `docs/stability/`

---

## Success Criteria

Deployment is successful when:
- ✅ All CI checks passing
- ✅ Full test suite passes locally
- ✅ Cache manifest system operational
- ✅ Reproducibility helpers available
- ✅ No new errors or warnings
- ✅ Documentation updated

---

## Post-Deployment Tasks

1. Update team on deployment status
2. Archive this runbook execution in ops log
3. Monitor for 24h
4. Mark as stable if no issues
5. Consider Wave C (optional hardening/UX/docs) if needed
