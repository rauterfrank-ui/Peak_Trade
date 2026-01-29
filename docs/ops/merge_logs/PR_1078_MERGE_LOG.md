# PR #1078 — Docs Token Policy Fix (Mode B metricsd Runbook)

## Summary
Docs Token Policy Fix: Inline Path Tokens im Mode-B metricsd Runbook so encoden, dass `docs-token-policy-gate (pull_request)` besteht.

## Why
Der Check `docs-token-policy-gate (pull_request)` ist fehlgeschlagen, weil zwei **illustrative** Inline-Pfad-Tokens `&#47;`-Encoding benötigen (Docs Token Policy).

## Changes
- Updated inline path tokens im Runbook auf `&#47;`-Encoding:
  - `.ops_local&#47;prom_multiproc` (vorher als raw Slash-Token geschrieben)
  - `.ops_local&#47;` (vorher als raw Slash-Token geschrieben)
- Keine Runtime-/Code-Behavior-Änderungen.

## Verification
- Lokal:
  - `PYENV_VERSION=3.11.14 python -m pytest -q tests/obs/test_metricsd_mode_b_smoke.py`
  - `PYENV_VERSION=3.11.14 python scripts/ops/validate_docs_token_policy.py --changed --base origin/main`
- CI (PR #1078):
  - `docs-token-policy-gate`: **PASS** nach Commit `0a4e4c5e`.

## Risk
LOW — docs-only Encoding-Fix; keine live/execution gates oder runtime logic verändert.

## Operator How-To
None. Diese Änderung betrifft nur Dokumentations-Formatierung/Policy-Compliance.

## References
- PR: [#1078](https://github.com/rauterfrank-ui/Peak_Trade/pull/1078)
- Gate: `docs-token-policy-gate (pull_request)`
- Affected doc: `docs/ops/runbooks/RUNBOOK_MODE_B_METRICSD_DASHBOARD_METRICS.md`
- Fix commit: `0a4e4c5e`
