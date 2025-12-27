# PR #360 — fix(deps): uv constraint-dependencies + regenerated uv.lock (py3.9 onnxruntime)

## Summary
Healed `main` after an incomplete dependency fix: ensured `requirements.txt` and `uv.lock` are fully synchronized while preserving Python-version-specific `onnxruntime` resolution.

## Why
PR #359 updated `requirements.txt` only. The guard compares an export from `uv.lock` against `requirements.txt`, so `main` became inconsistent and the guard failed.

## Changes
- Added `[tool.uv] constraint-dependencies` in `pyproject.toml` to enforce compatible resolution across Python versions.
- Regenerated `uv.lock` so Python 3.9 resolves `onnxruntime==1.19.2` and Python 3.10+ resolves `onnxruntime==1.23.2`.
- Restored full sync: `uv.lock` ↔ exported `requirements.txt` (guard green).

## Verification
- CI: guard check ✅
- CI: tests ✅ (3.9 / 3.10 / 3.11)

## Risk
LOW — Dependency graph changes are lockfile-scoped and validated by guard + full test matrix.

## Operator How-To
If guard fails due to `uv.lock` drift:
1) `uv lock`
2) `uv export --format requirements.txt --all-extras --all-groups --locked --no-hashes -o requirements.txt`
3) `../../../scripts/ops/check_requirements_synced_with_uv.sh`

## References
- PR #359 (partial fix): requirements markers corrected, but lock not regenerated.
- PR #360 (full fix): constraint-dependencies + regenerated lockfile.
