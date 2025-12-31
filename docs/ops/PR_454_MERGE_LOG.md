# PR #454 — Merge Log

## Summary

Docs-only change to prevent repeated CI failures in **Docs Reference Targets Gate** by documenting robust authoring rules and adding operator-facing triage guidance to the Cursor frontdoor runbook.

## Why

The gate can interpret path-like tokens as reference targets (including links, inline-code, and "bare paths"). This PR standardizes safe patterns for:

- Linking only to existing targets
- Mentioning future targets without triggering false positives

## Changes

- Added: `docs/ops/DOCS_REFERENCE_TARGETS_GATE_STYLE_GUIDE.md`
  - Gate-safe authoring rules (quotes + `(future)` + escaped slashes for future tokens)
  - Triage checklist and standard patterns
- Updated: `docs/ops/CURSOR_MULTI_AGENT_RUNBOOK_FRONTDOOR.md`
  - Added a small "CI: Docs Reference Targets Gate" subsection under Maintenance/Ownership
  - Linked to the style guide and provided a quick triage command

## Verification

- CI: All checks passing (including `docs-reference-targets-gate`)
- Review: Diff limited to docs additions/edits; no code changes

## Risk

Low. Documentation-only update; no runtime impact.

## Operator How-To

When `Docs Reference Targets Gate` fails:

1) Find the first "missing target" in the job log.
2) Convert future path-like references to the safe pattern (quotes + `(future)` + escaped slashes).
3) Re-run CI.

## References

- PR #454 (docs-only): style guide + frontdoor runbook update
