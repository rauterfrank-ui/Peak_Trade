# CI Trigger Tool

## Purpose

Trigger required status checks for workflow-only changes without leaving markers on main.

## How it works

- Creates a branch off the current branch
- Adds a one-line CI trigger to a target file (default: `src/__init__.py`) with a clearly marked line
- Immediately reverts that commit
- Opens PR with both commits so the final tree is unchanged after merge

## Usage

```bash
scripts/ops/ci_trigger_required_checks.sh [target_file]
```

- `target_file` defaults to `src/__init__.py` if omitted.

## Guardrails

- Refuses if working tree is dirty
- Refuses if any files under `reports/` are tracked
