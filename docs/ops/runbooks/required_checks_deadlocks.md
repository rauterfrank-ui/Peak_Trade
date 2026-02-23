# Required Checks Deadlocks

When a PR is **BLOCKED** because required status checks are "Expected" but never start (common with path-filtered workflows), use the CI trigger tool:

- `scripts&#47;ops&#47;ci_trigger_required_checks.sh`

## Why this is safe

- The tool creates a branch.
- It makes a one-line no-op change to a target file (default: `src&#47;__init__.py`).
- It immediately reverts that change in a second commit.
- The final tree (after squash merge) contains **no marker**, but required checks are triggered.

## Do

- Keep working tree clean before running.
- Ensure **no tracked files** exist under `reports&#47;` (guardrail).
- Prefer the default target or another stable file that matches the desired workflow path filters.

## Don't

- Don't add tracked files under `reports&#47;` to trigger CI.
- Don't leave CI marker lines in source or docs; use the tool instead.

## Example

```bash
scripts&#47;ops&#47;ci_trigger_required_checks.sh
```

Optional: pass a target file to match workflow path filters:

```bash
scripts&#47;ops&#47;ci_trigger_required_checks.sh docs&#47;ops&#47;README.md
```
