# PR #974 — MERGE LOG

- PR: https:&#47;&#47;github.com&#47;rauterfrank-ui&#47;Peak_Trade&#47;pull&#47;974
- Merge commit (main): 46595f9a3dd2da0f18c82c80dc43911775eb370f
- Merged at (UTC): 2026-01-24T10:47:01Z
- Merge method: squash
- Risk: LOW (`docs&#47;**` + `scripts&#47;**` only; watch-only ops scripts)

## Summary
Adds a deterministic Python environment selection (`PY_CMD`) for AI Live ops scripts to avoid `prometheus_client` mismatches (e.g., `python3` vs `python`), improving reproducibility of local verification.

## Why
Local runs could pass/fail depending on which Python interpreter was used, causing the exporter to exit immediately when `prometheus_client` was unavailable. The update makes the chosen Python command explicit and deterministic, reducing false negatives in ops verification.

## Changes
- scripts&#47;obs&#47;ai_live_smoke_test.sh (deterministic `PY_CMD` selection + logging)
- scripts&#47;obs&#47;ai_live_verify.sh (same `PY_CMD` approach + clearer diagnostics)
- scripts&#47;obs&#47;ai_live_ops_verify.sh (same `PY_CMD` approach + operator output)
- docs&#47;webui&#47;observability&#47;README.md (documents python env contract / troubleshooting)

## Verification
- CI required checks: PASS (per PR gate at merge time).
- Local smoke/verify/ops checks executed in the PR context (per PR description), with explicit `PY_CMD` logging.

## Merge evidence
- PR: https:&#47;&#47;github.com&#47;rauterfrank-ui&#47;Peak_Trade&#47;pull&#47;974
- state: MERGED
- mergedAt: 2026-01-24T10:47:01Z
- mergeCommit: 46595f9a3dd2da0f18c82c80dc43911775eb370f

## Risk
LOW — `scripts&#47;**` + `docs&#47;**` only, watch-only; NO-LIVE unchanged. Port Contract v1 (`:9110`) unchanged. No `src&#47;**` touched.
