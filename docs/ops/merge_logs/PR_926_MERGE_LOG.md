# PR #926 — Merge Log

## Summary
Slice 3: Deterministische beta_events → LedgerBridge + kanonische JSON/JSONL Regression-Artefakte (byte-identisch). RISK: HIGH, operator approval required.

## Why
Determinismus-kritische Bridge + Regression-Artefakte; Korrektheit hängt an stabiler Sortierung, kanonischem JSON und integer-only Persistence.

## Changes
- Bridge Defaults: fixes event_type_rank, deterministische seq-Ableitung, replay-safe ordering/dedup
- Dokumentierter State Contract + Integer-Scales
- Tests: Byte-Identität (2x run), Shuffle-Invarianz, forbidden-import scan, float-reject
- Fixture: minimal JSONL (integer-only)

## Verification
- python3 -m pytest -q tests&#47;execution&#47;test_beta_event_bridge_determinism.py → PASS
- python3 -m pytest -q tests&#47;execution&#47;test_beta_event_bridge_ordering.py → PASS
- ruff format --check . → PASS
- ruff check . → PASS

## Risk
HIGH — Determinism/Artifact-Contract is regression-sensitive; requires explicit operator approval prior to merge.

## Operator How-To
- Für zukünftige Slice-3 Änderungen: determinism + ordering tests ausführen und sicherstellen, dass Artefakte bei gleichen Inputs byte-identisch bleiben.

## References
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/926
- Merge Commit: ec03fc95b9ec845894a53a0890de2888c08a0d3a
- mergedAt: 2026-01-22T01:08:19Z
- headRefName: feat/execution-slice2-ledger-pnl
- headRefOid: 1fd71892f6f6f7d24a8a6c2a1f0f5d3c704b5d77
