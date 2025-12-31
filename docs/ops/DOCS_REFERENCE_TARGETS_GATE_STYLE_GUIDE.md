# Docs Reference Targets Gate – Style Guide (Peak_Trade)

Status: Active  
Owner: Ops / Docs Governance  
Scope: All Markdown under `docs\/` (and any CI-validated doc paths)

## Purpose

The **Docs Reference Targets Gate** validates that references to repo targets are not broken.
It may treat the following as "targets" that must exist:

- Markdown links: `[text](<repo-relative-path>)`
- Inline code blocks that look like paths
- "Bare paths" that resemble repo-relative paths inside normal prose

This guide defines **authoring rules** that avoid false positives while preserving useful operator guidance.

## Definitions

- **Existing target**: a file/anchor that exists on the current branch and is intended to be navigable.
- **Future target**: a planned file/anchor that does not exist yet.
- **Path-like token**: any string that resembles a repo-relative path (e.g. starts with `docs\/` or `src\/` patterns).

## Rules

### R1 — Only link to existing targets

Use Markdown links only when the target exists **now**.

Safe example pattern:
- `[WP0A completion report](docs\/execution\/WP0A_COMPLETION_REPORT.md)`

If the target does not exist, do **not** create a link.

### R2 — Never write future targets as "bare paths"

If a path-like token is **future**, it must not appear as a raw path.

Preferred future pattern:
- `"docs\/execution\/WP0X_IMPLEMENTATION_REPORT.md" (future)`

### R3 — Avoid backticks for future targets

Inline code formatting is frequently interpreted as an authoritative target reference.
For future targets:

- Do **not** use inline code formatting.
- Use **quotes** + `(future)` instead:
  - `"src\/orders\/router.py" (new, future)`

### R4 — Escape slashes for future path-like tokens

If you must mention a future path-like token, escape slashes:

- `docs\/...` instead of `docs/...`
- `src\/...` instead of `src/...`

Rationale: this prevents the gate's "bare target" parser from validating a non-existent file.

### R5 — Branch names that look like paths

Branch names frequently contain slashes and can be misread as targets.
Write branch names in **quotes** and explicitly label them as branches:

- Branch: `"docs\/phase0-foundation-prep"` (branch)

If quoting is insufficient in a given context, also apply slash escaping as above.

### R6 — Ownership / "Owns:" lists

Ownership matrices often list many files. Apply:

- Existing files: may be listed plainly if you are confident they exist.
- Future/new files: must be quoted + escaped + marked `(new)` and/or `(future)`.

Example:
- Existing: `src\/execution\/position_ledger.py` (existing)
- Future: `"src\/execution\/position_bridge.py" (new, future)`

### R7 — Anchors and section references

Do not reference anchors unless the anchor exists **and** is stable.
Prefer naming the section in text rather than using an anchor when uncertain:

- "See section 'Verification' in the WP0A packet."

If you do use anchors, ensure the header exists unchanged on the same branch.

## Quick Triage Checklist (when the gate fails)

1) Locate the first failing line in the CI job log (usually the root cause).  
2) Search for path-like tokens in changed docs:

```bash
rg -n '(^|[^\\])(docs|src)/' docs -S || true
```

3) For each reported target:

- If it should exist: create/fix the file or correct the link.
- If it is future/illustrative: convert to the future pattern:
  - quotes + `(future)` + escaped slashes (`\/`)

## Standard Future Pattern (copy/paste)

- `"docs\/<area>\/<name>.md" (future)`
- `"src\/<area>\/<name>.py" (new, future)`

## Notes

- This guide intentionally avoids unescaped bare path examples to remain gate-safe.
- If the gate's behavior changes, update this guide and align the docs authoring rules accordingly.
