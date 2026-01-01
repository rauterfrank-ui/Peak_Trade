## Summary
Implements/extends Shadow Track functionality for execution flow testing, with safety-first defaults and governance alignment.

## Why
- Enable realistic end-to-end rehearsal (shadow) without live exposure.
- Improve operator confidence via deterministic, auditable flows.

## What changed
- Shadow-only execution path improvements (no live enablement).
- Governance-lock aligned defaults (live remains blocked unless explicitly permitted elsewhere).
- Additional telemetry/logging to support auditability and incident drills.

## Verification
**Foundation**
- `uv run ruff format --check .`
- `uv run ruff check .`
- `pytest -q`
- Targeted smoke (if available): shadow / offline realtime feed / execution pipeline tests.

**Governance**
- Confirm default mode remains `LIVE_BLOCKED` (or equivalent).
- Policy Critic + governance checks green.
- No config path allows "silent live" activation; any override requires explicit operator action and documented gates.

**Shadow**
- Run a shadow drill (paper/sim):
  - Execute a minimal shadow session end-to-end.
  - Validate: idempotency keys, correlation IDs, audit log entries, recon handoff artifacts.

## Risk
Medium (code-path change; execution-adjacent).
Mitigations:
- Strict default-block behavior.
- Tests + shadow drill as release gate.

## Operator notes
- This PR is shadow-only: do not use for live execution.
- Follow runbooks for any session start; capture logs/artifacts for review.

## Rollback
Revert PR commit(s). If merged and issues found, disable shadow path usage and revert to previous stable release.
