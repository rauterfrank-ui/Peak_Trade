# Theme / Path Map — Phase 11 Top Value Review

**Stand:** 2026-03-10

## 1. ops / supervisor / launchd

| Branch | Classification | Likely Paths | Ready |
|--------|----------------|--------------|-------|
| recover/p80-supervisor-stop-idempotent-v1 | ALREADY_ON_MAIN | — | ✓ skip |
| recover/p99-launchd-hard-guardrails-v1 | SALVAGE_NOW | docs/analysis/p99/, launchd plist | ✓ |
| recover/ops-launchd-supervisor-subcommands-v1 | SALVAGE_NOW | scripts/ops/*supervisor*, tests/p88 | ✓ |

**Theme summary:** p99 and ops-launchd-subcommands ready for salvage. p80 net-diff zero.

---

## 2. governance / roadmap / runbook

| Branch | Classification | Likely Paths | Ready |
|--------|----------------|--------------|-------|
| recover/p22-roadmap-runbook-merge | SALVAGE_NOW | docs/roadmap/PeakTrade_LevelUp_Roadmap_Evidence.md | ✓ |

**Theme summary:** Single high-value doc; governance alignment.

---

## 3. backtest / accounting / reporting

| Branch | Classification | Likely Paths | Ready |
|--------|----------------|--------------|-------|
| recover/p28-backtest-loop-positions-cash-v1 | SALVAGE_NOW | src/backtest/p28/, tests/p28 | ✓ |
| recover/p29-accounting-v2-avgcost-realizedpnl | SALVAGE_NOW | src/backtest/p29/, tests/p29 | ✓ |

**Theme summary:** Core accounting; both ready for salvage.

---

## 4. execution / adapter

| Branch | Classification | Likely Paths | Ready |
|--------|----------------|--------------|-------|
| recover/p111-execution-adapter-selector-v1 | SALVAGE_NOW | src/execution/adapters/registry_v1.py, tests/p111 | ✓ |

**Theme summary:** Adapter registry; mocks only; low risk.

---

## 5. workbook / ops

| Branch | Classification | Likely Paths | Ready |
|--------|----------------|--------------|-------|
| recover/p101-workbook-checklists-stop-playbook-v1 | SALVAGE_LATER | scripts/ops/p101_stop_playbook_v1.sh | verify first |

**Theme summary:** Deletions in script; verify intent before salvage.

---

## 6. salvage-wip

| Branch | Classification | Likely Paths | Ready |
|--------|----------------|--------------|-------|
| wip/salvage-code-tests-untracked-20251224_082521 | MANUAL_DEEP_REVIEW | src/strategies/, tests/ | manual |
| wip/untracked-salvage-20251224_081737 | MANUAL_DEEP_REVIEW | docs/, scripts/, src/, tests/ | manual |

**Theme summary:** High volume; rescue remotes; manual diff review required.
