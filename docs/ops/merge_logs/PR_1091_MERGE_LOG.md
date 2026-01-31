# PR_1091 MERGE LOG — test(ci): harden pytest collection for optional deps + roll marker

## Summary
Pytest collection and marker-selected runs could fail in minimal environments due to optional dependencies (yaml/fastapi/requests) and import-time exits. This PR hardens test collection by skipping optional-dependency tests cleanly and stabilizes roll-marker execution.

## Why
- `pytest --collect-only` and `pytest -m roll` must not crash during collection.
- Optional dependencies should not be required for unrelated test selection.
- Import-time `sys.exit()` is incompatible with pytest collection.

## Changes
- `pytest.ini`: define `roll` marker.
- `scripts/ci/validate_required_checks_hygiene.py`: remove import-time hard-exit; make dependency handling import-safe.
- `tests/ci/test_required_checks_hygiene.py`: skip cleanly if PyYAML missing.
- `tests/data/continuous/test_continuous_contract.py`: add roll smoke test (ensures `-k roll` selects).
- `tests/markets/cme/test_contract_specs.py`: mark roll tests with `@pytest.mark.roll`.
- `tests/obs/test_ai_live_ops_*`: skip cleanly if PyYAML missing.
- `tests/webui/test_ops_ci_health_router.py`: skip cleanly if FastAPI missing.
- `tests/governance/policy_critic/test_critic.py`: skip cleanly if PyYAML missing.

## Verification
- CI: tests (3.9/3.10/3.11) PASS; lint gate PASS; expected health-check skips.
- Local (optional):
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q --collect-only`
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q -m roll`

## Merge Evidence (Truth)
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/1091
- state: MERGED
- mergedAt: 2026-01-31T18:44:34Z
- mergeCommit: dca5d01a0e7b41c300a80e92b3dee69ea15a8514
- matched headRefOid (guarded --match-head-commit): ed2db3e012276490005527350e1dd2b0366e8b0e

## Risk
LOW — tests/CI-infra only; no trading/execution logic changes.
