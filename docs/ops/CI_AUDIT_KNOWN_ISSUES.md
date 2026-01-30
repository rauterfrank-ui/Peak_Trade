# CI Audit — Known Issues

## Current status
- `audit` may fail due to a known pre-existing Black formatting/configuration issue.
- This is currently treated as **non-blocking** for docs/merge-log PRs, unless explicitly changed by policy.

## What to check
- Confirm `strategy-smoke`, `tests`, and health gates are green for merge readiness.
- If `audit` fails, cross-check whether the failure is related to the change set.

## Tracking
- Root cause and remediation are tracked in GitHub Issues: [Issue #252](https://github.com/rauterfrank-ui/Peak_Trade/issues/252)

## Local reproduction
```bash
ruff check .    # ✅ passes
black --check . # ❌ 61 files would be reformatted
```

## Next steps
1. Decide on policy: fix all files, adjust CI config, or keep as non-blocking
2. Document final decision in this file
3. Update CI workflow if needed
