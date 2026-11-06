# PR 1051 — MERGE LOG

## Summary
PR #1051 wurde als squash gemerged; Branch gelöscht; guarded merge via `--match-head-commit` eingehalten.

## Why
`prepare_once()` Semantik (Cache-Key per `id(data)` / Objektidentität) soll im Code explizit dokumentiert sein, um Missverständnisse (Fingerprint vs. Objekt) zu vermeiden.

## Changes
- src&#47;strategies&#47;base.py
  - Docstring/Kommentar-Klarstellung: `prepare_once()` nutzt Objektidentität (`id(data)`); neues DataFrame-Objekt (z.B. copy) triggert erneut `prepare()`.

## Verification
- PR Checks: alle required Checks PASS (inkl. Tests-Matrix, Lint, docs gates)

## Merge Evidence
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/1051
- state: MERGED
- mergedAt: 2026-01-28T10:37:09Z
- mergeCommit: df3092c74a822b2cf3f107aff824701345cbdf50

## Risk
Low (Docstring/Kommentar only, kein Behavior-Change).

## Operator How-To
- Keine Operator-Aktion notwendig.

## References
- PR #1051
