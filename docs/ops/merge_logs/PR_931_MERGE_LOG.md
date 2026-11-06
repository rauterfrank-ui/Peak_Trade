## PR #931 — MERGE LOG

## Summary
- PR: [#931](https://github.com/rauterfrank-ui/Peak_Trade/pull/931)
- Title: feat(execution): deterministic replay pack bundle v1 (Slice 3.1)
- Scope: code (execution)
- Risk: HIGH

## Why
Adds a deterministic Replay Pack bundle v1 contract and tooling to export, validate, and replay Slice-1 execution JSONL events reproducibly. This enables portable regression replay, tamper-detection (hashes), and invariant checks without changing any live execution behavior.

## Changes
- Introduces Replay Pack bundle contract v1 (manifest + hashes + deterministic file layout).
- Adds builder, validator, loader utilities and a replay runner CLI (replay-only).
- Adds hermetic tests covering contract shape, hashing/tamper detection, canonical JSON/JSONL, and replay smoke (incl. check-outputs).

## Verification

### Tests executed

```bash
python3 -m pytest -q tests/replay_pack tests/execution/test_replay_runner_smoke.py
```

### Verification result
- PASS: replay pack tests (contract + hash validation + canonicalization)
- PASS: replay runner smoke test (incl. check-outputs)

## Risk

### Primary risks
- New code under execution path could affect downstream imports or packaging assumptions if module names collide.
- Determinism regressions if timestamps, ordering, or canonicalization rules drift.

### Mitigations
- Additive-only change; no existing APIs modified.
- Contract enforces stable ordering + canonical JSON; floats forbidden (hard error).
- Hash validation detects tamper and drift deterministically.

## Operator How-To

### What changed operationally
- New replay-only CLI is available to build, validate, and replay deterministic bundles for Slice-1 JSONL events.
- No live execution is enabled or modified.

### How to validate locally

```bash
# PRE-FLIGHT (Ctrl-C if you are stuck in a continuation prompt)
cd "$HOME/Peak_Trade" 2>/dev/null || cd "$(pwd)"
pwd
git rev-parse --show-toplevel 2>/dev/null || true
git status -sb 2>/dev/null || true

# Tests
python3 -m pytest -q tests/replay_pack tests/execution/test_replay_runner_smoke.py

# CLI help
python3 scripts/execution/pt_replay_pack.py --help 2>/dev/null || true
```
