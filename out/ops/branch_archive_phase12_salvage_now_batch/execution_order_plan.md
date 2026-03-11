# Ordered Execution Plan — Phase 12 SALVAGE_NOW Batch

**Stand:** 2026-03-11  
**Mode:** Planning only; no implementation

---

## Wave 21a: recover/p22-roadmap-runbook-merge

| Field | Value |
|-------|-------|
| Target branch | recover/p22-roadmap-runbook-merge |
| Goal | Salvage roadmap runbook merge; governance alignment |
| Likely touched paths | docs/roadmap/PeakTrade_LevelUp_Roadmap_Evidence.md |
| Safety gates | No live execution; docs-only |
| Required validation | docs-token-policy, docs-reference-targets |
| Expected evidence | Merge commit, PR |

---

## Wave 21b: recover/p99-launchd-hard-guardrails-v1

| Field | Value |
|-------|-------|
| Target branch | recover/p99-launchd-hard-guardrails-v1 |
| Goal | Salvage launchd guardrails; safety-critical |
| Likely touched paths | docs/analysis/p99/README.md, launchd plist |
| Safety gates | No live execution; shadow/dry-run only |
| Required validation | Plist syntax; docs gates |
| Expected evidence | Merge commit, PR |

---

## Wave 21c: recover/p28-backtest-loop-positions-cash-v1

| Field | Value |
|-------|-------|
| Target branch | recover/p28-backtest-loop-positions-cash-v1 |
| Goal | Salvage backtest positions+cash accounting |
| Likely touched paths | src/backtest/p28/, tests/p28/ |
| Safety gates | No live execution; backtest only |
| Required validation | pytest tests/p28 -q |
| Expected evidence | Merge commit, PR |

---

## Wave 21d: recover/p29-accounting-v2-avgcost-realizedpnl

| Field | Value |
|-------|-------|
| Target branch | recover/p29-accounting-v2-avgcost-realizedpnl |
| Goal | Salvage avg cost + realized PnL; reporting core |
| Likely touched paths | src/backtest/p29/, tests/p29/ |
| Safety gates | No live execution; backtest only |
| Required validation | pytest tests/p29 -q |
| Expected evidence | Merge commit, PR |

---

## Wave 21e: recover/p111-execution-adapter-selector-v1

| Field | Value |
|-------|-------|
| Target branch | recover/p111-execution-adapter-selector-v1 |
| Goal | Salvage execution adapter registry; mocks only |
| Likely touched paths | src/execution/adapters/registry_v1.py, tests/p111/ |
| Safety gates | No live execution; mocks only |
| Required validation | pytest tests/p111 -q |
| Expected evidence | Merge commit, PR |

---

## Wave 21f: recover/ops-launchd-supervisor-subcommands-v1

| Field | Value |
|-------|-------|
| Target branch | recover/ops-launchd-supervisor-subcommands-v1 |
| Goal | Salvage supervisor start/stop/status subcommands |
| Likely touched paths | scripts/ops/*supervisor*, tests/p88/ |
| Safety gates | No live execution; ops tooling |
| Required validation | pytest tests/p88 -q |
| Expected evidence | Merge commit, PR |

---

## Recommended Order

1. **21a** — p22 (docs-only; lowest risk)
2. **21b** — p99 (launchd; safety)
3. **21c** — p28 (backtest)
4. **21d** — p29 (accounting)
5. **21e** — p111 (execution mocks)
6. **21f** — ops-launchd (supervisor)
