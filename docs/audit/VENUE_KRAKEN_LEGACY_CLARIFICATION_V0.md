# Venue Kraken Legacy Clarification v0

**Status:** audit note (doc-only)  
**Date:** 2026-07-08  
**Scope:** documentation and legacy-script wording only — no runtime rewire

## Machine-readable summary

```
KRAKEN_CURRENT_TARGET_VENUE=false
KRAKEN_REFERENCES_ARE_LEGACY_OR_GUARDED_INFRASTRUCTURE=true
NO_RUNTIME_AUTHORITY_FROM_VENUE_REFERENCES=true
CURRENT_CANONICAL_VENUE_SSOT=okx_europe_eea
```

## Operator read

- Production config default venue is **OKX EEA** (`config/config.toml`: `default_exchange = "okx_europe_eea"`).
- Kraken profiles in config are **DORMANT/DECOMMISSIONED** unless separately ratified.
- Kraken references in docs, comments, legacy scripts, guarded ops tooling, and negative test fixtures denote **historical/legacy** or **guarded infrastructure** only.
- No Kraken mention grants runtime, order, credential, scheduler, shadow, paper, testnet, canary, or live authority.

## Evidence chain

- Legacy audit: `venue_kraken_legacy_audit_v0_20260708T002338Z`
- Blocker refinement: `venue_kraken_blocker_refinement_v0_20260708T002605Z`
- Cleanup PR scope: doc/comments/legacy-script text only (`DOC_AND_LEGACY_SCRIPT_CLEANUP_ONLY_NO_RUNTIME_REWIRE`)

## Forbidden misreadings

Do **not** treat any of the following as current canonical venue SSOT:

- `CURRENT_TARGET_VENUE`
- `CURRENT_CANONICAL_VENUE_SSOT`
- stale project-docs Kraken pipeline summaries
- legacy demo scripts (`scripts/demo_kraken_simple.py`, registry backtest helpers)
- dormant Kraken config profile blocks
