# Grouping Decision — Phase 12 SALVAGE_NOW Batch

**Stand:** 2026-03-11

## Decision: All STANDALONE_SALVAGE

| Branch | Decision | Rationale |
|--------|----------|-----------|
| recover/p22-roadmap-runbook-merge | STANDALONE_SALVAGE | Single file; docs-only; no path overlap |
| recover/p99-launchd-hard-guardrails-v1 | STANDALONE_SALVAGE | docs + plist; distinct from ops-launchd |
| recover/p28-backtest-loop-positions-cash-v1 | STANDALONE_SALVAGE | src/backtest/p28; distinct module |
| recover/p29-accounting-v2-avgcost-realizedpnl | STANDALONE_SALVAGE | src/backtest/p29; distinct module |
| recover/p111-execution-adapter-selector-v1 | STANDALONE_SALVAGE | src/execution/adapters; mocks only |
| recover/ops-launchd-supervisor-subcommands-v1 | STANDALONE_SALVAGE | scripts/ops; supervisor subcommands |

## Rationale

- **No safe grouping:** p28 and p29 both touch backtest but different subdirs (p28 vs p29); merging would mix two independent commits.
- **p99 vs ops-launchd:** Different scope (launchd guardrails vs supervisor subcommands); no path overlap.
- **Minimal blast radius:** Standalone salvage per branch reduces conflict risk and simplifies rollback.

## Safe Grouping Candidates

None identified. Prefer one branch per implementation wave.
