# PR #116 — Merge Log

## PR
- Title: chore(ci): add Quarto no-exec guard
- URL: https://github.com/rauterfrank-ui/Peak_Trade/pull/116
- Base: main
- Head: zealous-hellman

## Merge
- Merge SHA: 959e1cbd23a398da1c5dd588fa9bc770803162ec
- Merged at: 2025-12-17T21:30:41Z
- Diffstat: +67 / -1 (files changed: 2)

## Summary
- Add CI guard to enforce Quarto **no-exec** policy:
  - Reject executable Python chunks (```{python})
  - Require `execute: enabled: false` in YAML front matter
- Ensures Quarto smoke remains **pure Markdown → HTML** in CI

## Verification
- CI: PR checks green
- Local: `bash scripts&#47;ci&#47;check_quarto_no_exec.sh`
- Post-merge: `scripts&#47;automation&#47;post_merge_verify.sh --expected-head <sha>` (if available)
