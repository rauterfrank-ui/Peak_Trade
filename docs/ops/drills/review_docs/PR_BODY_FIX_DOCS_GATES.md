## Scope
- Fix docs token policy violation in `docs/ops/merge_logs/PR_1091_MERGE_LOG.md` by encoding path separators (`&#47;`) inside inline code.
- Update docs reference targets gate workflow to run **only** when a PR actually changes Markdown files.

## Evidence
- Token policy validation (tracked docs):
  - `python3 scripts/ops/validate_docs_token_policy.py --tracked-docs`
- Changes:
  - `docs/ops/merge_logs/PR_1091_MERGE_LOG.md`
  - `.github/workflows/docs_reference_targets_gate.yml`

## Notes
- The docs reference targets verification step is now conditionally skipped when there are no `.md` changes, making the workflow "not applicable" instead of failing/noising.
- No runtime code changes.
