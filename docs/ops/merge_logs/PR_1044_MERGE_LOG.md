# PR 1044 — MERGE LOG

## Summary
PR #1044 wurde als squash gemerged; Branch gelöscht; guarded merge via `--match-head-commit` eingehalten.

## Why
Strategy-Lifecycle ist dokumentiert und implementiert: `prepare()` ist Hook; empfohlen ist `strategy.run(data)` bzw. `prepare_once()` vor `generate_signals()`.

## Changes
- docs&#47;STRATEGY_DEV_GUIDE.md
  - Lifecycle/Contract aktualisiert (`run → prepare_once → generate_signals`; `prepare` = Hook)
- src&#47;strategies&#47;base.py
  - `prepare_once()` + `run()` ergänzt (idempotent per DataFrame-Objekt via `id(data)`)
- tests&#47;strategies&#47;test_prepare_once.py
  - Unit-Test: `prepare_once()` ist idempotent pro DataFrame-Objekt

## Verification
- PR Checks: alle relevanten Checks PASS (inkl. docs-token-policy-gate)
- Lokal (wie im PR-Text): `python3 -m pytest -q tests&#47;strategies&#47;test_prepare_once.py` → PASS

## Merge Evidence
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/1044
- state: MERGED
- mergedAt: 2026-01-28T08:28:19Z
- mergeCommit: c72b5ae6bb4edd1339a182355e14960b5083134b

## Risk
Low (Docs + kleiner Unit-Test + BaseStrategy Lifecycle-Helfer; keine Live/Execution-Changes).

## Operator How-To
- Keine Operator-Aktion notwendig (Docs/Tests only).

## References
- PR #1044
