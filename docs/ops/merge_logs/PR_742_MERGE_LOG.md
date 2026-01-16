# PR #742 — Merge Log

## Summary
- Scope: Watch-only dashboard UI v0.1B (observability) + read-only API v0 extensions + operator runbook.
- Token-Policy fix: `live_runs/` → `live_runs&#47;` (illustrative inline-code token encoding).
- Key operator doc: `docs/ops/runbooks/RUNBOOK_DASHBOARD_WATCH_ONLY_V01B.md`

## Why
- CI “Docs Token Policy Gate” classified `live_runs/` as an illustrative path token and requires `&#47;` encoding to avoid false positives / unsafe path parsing.

## Changes
- Added watch-only UI routes + server-rendered pages (read-only).
- Extended read-only API v0 for observability (no mutating endpoints).
- Added operator runbook for watch-only UI v0.1B.
- Applied minimal token-policy remediation in the runbook (single-token change, no semantic change intended).

## Verification
- CI snapshot (post-merge): `gh pr checks 742` → 0 failing, 0 pending.
- Local CI-equivalent (token policy): `python3 scripts/ops/validate_docs_token_policy.py --base origin/main --json docs-token-policy-report.json` → PASS.
- Local (operator snapshot):
  - `python3 -m ruff check .` → PASS
  - `python3 -m ruff format --check .` → PASS
  - `python3 -m pytest -q` → PASS

## Risk
- LOW — watch-only/read-only scope; docs token encoding is formatting-only.

## Operator How-To
- If the “Docs Token Policy Gate” reports: “Illustrative path token must use &#47; encoding”:
  - Treat inline-code tokens containing `/` as illustrative path tokens unless they are real repo targets.
  - Encode `/` as `&#47;` inside inline-code for illustrative paths (e.g., `live_runs&#47;`).

## References
- PR: #742
- Workflow: Docs Token Policy Gate (`docs-token-policy-gate`)
