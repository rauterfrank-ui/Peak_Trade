# Theme Clusters — Phase 8 Review

**Stand:** 2026-03-10

## 1. recover-ops / supervisor / launchd

| Branch | Likely Active Value | Likely Historical | Duplication with main | Uncertainty |
|--------|---------------------|-------------------|------------------------|-------------|
| recover/ops-launchd-supervisor-subcommands-v1 | medium | high | possible | medium |
| recover/p102-launchd-templates-p93-p94-v1 | medium | high | possible | medium |
| recover/p80-supervisor-stop-idempotent-v1 | high | medium | low | low |
| recover/p81-supervisor-service-hardening-v1 | high | medium | low | low |
| recover/p87-supervisor-plus-ingest-v1 | medium | high | possible | medium |
| recover/p88-launchd-supervisor-smoke-script-v1 | medium | high | possible | medium |
| recover/p99-guarded-plist-workingdir-v1 | medium | high | possible | medium |
| recover/p99-launchd-hard-guardrails-v1 | high | medium | low | low |

**Theme summary:** Supervisor/launchd/plist work; likely overlap with feat/ops-launchagent-modes, feat/p78–p82. Conservative: preserve p80, p81, p99-launchd-hard-guardrails; archive others after diff proof.

---

## 2. execution-networked (p122–p132)

| Branch | Likely Active Value | Likely Historical | Duplication with main | Uncertainty |
|--------|---------------------|-------------------|------------------------|-------------|
| recover/p122-execution-runbook-v1 | low | high | high (cycle closed) | low |
| recover/p123-execution-networked-onramp-v1 | low | high | high | low |
| recover/p124-execution-networked-entry-contract-v1 | low | high | high | low |
| recover/p126-execution-networked-transport-stub-v1 | low | high | high | low |
| recover/p127-networked-provider-adapter-stub-v1 | low | high | high | low |
| recover/p128-execution-networked-transport-stub-v1 | low | high | high | low |
| recover/p130-networked-allowlist-stub-v1 | low | high | high | low |
| recover/p132-networked-transport-allow-handshake-v1 | low | high | high | low |

**Theme summary:** Execution-networked salvage cycle p122–p132 completed. High duplication with main. Archive after lightweight diff proof.

---

## 3. observability / reporting / accounting

| Branch | Likely Active Value | Likely Historical | Duplication with main | Uncertainty |
|--------|---------------------|-------------------|------------------------|-------------|
| recover/p29-accounting-v2-avgcost-realizedpnl | high | high | unknown | medium |
| recover/p33-report-artifacts-v1 | medium | high | unknown | medium |
| recover/p92-audit-snapshot-runner-v1 | medium | high | possible | medium |
| recover/p94-p93-status-dashboard-retention-v1 | medium | high | possible | medium |

**Theme summary:** Accounting, reporting, audit, dashboard. p29 likely high value; others need diff proof.

---

## 4. governance / docs

| Branch | Likely Active Value | Likely Historical | Duplication with main | Uncertainty |
|--------|---------------------|-------------------|------------------------|-------------|
| recover/p22-roadmap-runbook-merge | high | medium | unknown | low |
| recover/p51-ai-layer-guardrails-audit-v1 | medium | high | possible | medium |
| tmp/docs-runbook-to-finish-clean | medium | low | unknown | medium |

**Theme summary:** Roadmap, runbook, AI guardrails. p22 explicitly kept for future impl.

---

## 5. stash / restore / wip

| Branch | Likely Active Value | Likely Historical | Duplication with main | Uncertainty |
|--------|---------------------|-------------------|------------------------|-------------|
| recover/stash-2 | unknown | high | unknown | high |
| recover/stash-3 | unknown | high | unknown | high |
| wip/local-uncommitted-20260128 | low | low | unknown | high |
| wip/local-unrelated-20260127-205436 | low | low | unknown | high |
| wip/pausepoint-branch-cleanup-recovery-20260124T133039Z | medium | medium | unknown | high |
| wip/restore-stash-after-pr432 | unknown | high | unknown | high |
| wip/restore-stash-operator-pack | unknown | high | unknown | high |
| wip/salvage-code-tests-untracked-20251224_082521 | medium | high | unknown | high |
| wip/salvage-dirty-main-20260118 | low | low | unknown | high |
| wip/untracked-salvage-20251224_081737 | medium | high | unknown | high |

**Theme summary:** Stash/restore/salvage branches; high uncertainty. Manual deep review required before any disposal.

---

## 6. execution / exchange / adapter (non-networked)

| Branch | Likely Active Value | Likely Historical | Duplication with main | Uncertainty |
|--------|---------------------|-------------------|------------------------|-------------|
| recover/p27-execution-integration-v2 | medium | high | possible | medium |
| recover/p105-exchange-execution-research-v1 | medium | high | possible | medium |
| recover/p105-exchange-shortlist-v1 | medium | high | possible | medium |
| recover/p105-readme-pointer-pin-v1 | low | medium | possible | low |
| recover/p111-execution-adapter-selector-v1 | medium | high | possible | medium |

**Theme summary:** Exchange execution, adapter selector. Research/shortlist likely superseded; adapter selector may have value.

---

## 7. online-readiness / backtest / evidence

| Branch | Likely Active Value | Likely Historical | Duplication with main | Uncertainty |
|--------|---------------------|-------------------|------------------------|-------------|
| recover/fix-p76-result-path-in-ticks | medium | medium | possible | medium |
| recover/p28-backtest-loop-positions-cash-v1 | high | high | unknown | medium |
| recover/p64-online-readiness-runner-v1 | medium | high | possible | medium |
| recover/p65-online-readiness-loop-runner-v1 | medium | high | possible | medium |
| recover/p66-online-readiness-operator-entrypoint-v1 | medium | high | possible | medium |
| recover/p75-p72-env-contract-tests-v1 | medium | high | possible | medium |
| recover/p118-sha256sums-no-xargs-v1 | low | medium | possible | low |
| recover/p54-switch-layer-routing-v1 | medium | high | possible | low |

**Theme summary:** Online-readiness, backtest, evidence. p28 backtest likely high value.

---

## 8. workbook / ops / pr-ops

| Branch | Likely Active Value | Likely Historical | Duplication with main | Uncertainty |
|--------|---------------------|-------------------|------------------------|-------------|
| recover/p101-workbook-checklists-stop-playbook-v1 | high | high | low | low |
| recover/pr-ops-v1-closeout-ff-fix | medium | high | possible | medium |
| recover/pr-trigger-triage-v1 | medium | high | possible | medium |
| recover/ops_pr-drill-20260211T070830Z | medium | high | unknown | high |

**Theme summary:** Workbook, PR ops. p101 explicitly kept for future impl.

---

## 9. backup / tmp / unknown

| Branch | Likely Active Value | Likely Historical | Duplication with main | Uncertainty |
|--------|---------------------|-------------------|------------------------|-------------|
| recover/p13-kickoff | unknown | medium | unknown | high |
| backup/* (9 branches) | low | medium | high (snapshots) | low |
| tmp/stack-test | low | low | unknown | high |

**Theme summary:** Backup = historical snapshots; disposal candidates after proof. p13-kickoff needs manual review.
