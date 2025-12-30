# Peak_Trade Audit Evidence Index

**Audit Baseline:** `fb829340dbb764a75c975d5bf413a4edb5e47107`  
**Last Updated:** 2025-12-30

---

## Purpose

This document catalogs all evidence artifacts collected during the audit. Each evidence item is assigned a unique ID and includes:
- Description of what was captured
- Location (file path or external link)
- Collection date/time
- Related findings (cross-reference to FND-XXXX)

---

## Evidence Categories

### EV-0000: Baseline & Setup

| ID | Description | Location | Date | Related Findings |
|----|-------------|----------|------|------------------|
| EV-0001 | Audit baseline commit hash | This document header | 2025-12-30 | N/A |
| EV-0002 | Repository structure snapshot | `evidence/snapshots/repo_tree_[date].txt` | TBD | |

---

### EV-1000: Inventory & Architecture (Phase A1)

| ID | Description | Location | Date | Related Findings |
|----|-------------|----------|------|------------------|
| EV-1001 | Source code directory tree | `evidence/snapshots/repo_subsystems_20251230.txt` | 2025-12-30 | FND-0002, FND-0003 |
| EV-1002 | Architecture overview & critical paths | `evidence/snapshots/architecture_overview_20251230.md` | 2025-12-30 | FND-0001, FND-0002, FND-0003 |
| EV-1003 | Live trading entry points | Code search: `src/live/shadow_session.py`, `src/live/testnet_orchestrator.py` | 2025-12-30 | FND-0001 |
| EV-1004 | Kill switch architecture | Code search: `src/risk_layer/kill_switch/core.py`, `execution_gate.py` | 2025-12-30 | FND-0001 |
| EV-1005 | Repository statistics | 42 subsystems, 396 Python files, 317 test files | 2025-12-30 | All |

---

### EV-2000: Build, CI, Reproducibility (Phase A2)

| ID | Description | Location | Date | Related Findings |
|----|-------------|----------|------|------------------|
| EV-2001 | Build & reproducibility overview | `evidence/snapshots/build_repro_20251230.md` | 2025-12-30 | FND-0004 |
| EV-2002 | Dependencies lockfile | `uv.lock` (6,377 lines) | 2025-12-30 | All |
| EV-2003 | Python version | Python 3.9.6, uv 0.9.18 | 2025-12-30 | All |
| EV-2004 | Policy pack configuration | `policy_packs/ci.yml`, `live_adjacent.yml`, `research.yml` | 2025-12-30 | FND-0004 |
| EV-2005 | Test infrastructure | pytest.ini, 276 test files, 5,340+ test functions | 2025-12-30 | All |
| EV-2006 | Makefile build automation | `Makefile` (audit, clean, report targets) | 2025-12-30 | All |
| EV-2007 | CI workflow files | **NOT FOUND** (no .github/workflows/) | 2025-12-30 | FND-0004 |

---

### EV-3000: Backtest Correctness (Phase A3)

| ID | Description | Location | Date | Related Findings |
|----|-------------|----------|------|------------------|
| EV-3001 | Backtest engine source review | `src/backtesting/` | TBD | |
| EV-3002 | Golden backtest snapshots | `results/backtest_*/` | TBD | |
| EV-3003 | Test coverage for backtest invariants | `tests/backtest/` | TBD | |
| EV-3004 | Fee/slippage model documentation | TBD | | |
| EV-3005 | Lookahead bias checks | TBD | | |

---

### EV-4000: Risk Layer & Limits (Phase A4)

| ID | Description | Location | Date | Related Findings |
|----|-------------|----------|------|------------------|
| EV-4001 | Risk configuration files | `config/risk/`, `config/*risk*.toml` | 2025-12-30 | |
| EV-4002 | Pre-trade check implementation | `src/risk/` | TBD | |
| EV-4003 | Runtime check implementation | `src/risk/` | TBD | |
| EV-4004 | Kill switch implementation | Search results, config | TBD | |
| EV-4005 | Risk gate unit tests | `tests/risk/` | TBD | |
| EV-4006 | Live allowlist configuration | `config/live_policies.toml` | TBD | |

---

### EV-5000: Execution Pipeline (Phase A5)

| ID | Description | Location | Date | Related Findings |
|----|-------------|----------|------|------------------|
| EV-5001 | Order lifecycle state machine | `src/execution/` | TBD | |
| EV-5002 | Idempotency implementation | TBD | | |
| EV-5003 | Retry policy configuration | TBD | | |
| EV-5004 | Exchange integration tests | `tests/execution/` | TBD | |
| EV-5005 | Order reconciliation logic | TBD | | |

---

### EV-6000: Security & Secrets (Phase A6)

| ID | Description | Location | Date | Related Findings |
|----|-------------|----------|------|------------------|
| EV-6001 | Secrets scan results (gitleaks/detect-secrets) | `evidence/commands/secrets_scan_[date].txt` | TBD | |
| EV-6002 | Dependency vulnerability scan (pip-audit) | `evidence/commands/pip_audit_[date].txt` | TBD | |
| EV-6003 | .gitignore review (secrets exclusion) | `.gitignore` | 2025-12-30 | |
| EV-6004 | Logging policy review (no key leaks) | `src/*/logging` patterns | TBD | |
| EV-6005 | Secrets management approach | Documentation/code review | TBD | |

---

### EV-7000: Ops Readiness (Phase A7)

| ID | Description | Location | Date | Related Findings |
|----|-------------|----------|------|------------------|
| EV-7001 | Runbook inventory | `docs/runbooks/`, `scripts/ops/` | TBD | |
| EV-7002 | Monitoring/alerting configuration | `config/telemetry_alerting.toml` | 2025-12-30 | |
| EV-7003 | Dry-run drill logs | `evidence/commands/drill_[date].txt` | TBD | |
| EV-7004 | Incident response procedures | Documentation review | TBD | |
| EV-7005 | Rollback procedures | Documentation/scripts review | TBD | |

---

## Evidence Artifacts Storage

- **Snapshots:** `docs/audit/evidence/snapshots/`
- **Command Outputs:** `docs/audit/evidence/commands/`
- **CI Logs:** `docs/audit/evidence/ci/`
- **Screenshots:** `docs/audit/evidence/screenshots/`

---

---

### EV-9000: Remediation Evidence (Agent A-E)

| ID | Description | Location | Date | Related Findings |
|----|-------------|----------|------|------------------|
| EV-9001 | Bounded-live implementation (runbook, config, tests) | `docs/runbooks/LIVE_MODE_TRANSITION_RUNBOOK.md`, `config/bounded_live.toml`, `scripts/live/test_bounded_live_limits.py` | 2025-12-30 | FND-0001 |
| EV-9002 | Ops drills & procedures (kill switch drill, rollback) | `docs/runbooks/KILL_SWITCH_DRILL_PROCEDURE.md`, `docs/runbooks/ROLLBACK_PROCEDURE.md` | 2025-12-30 | FND-0005 |
| EV-9003 | CI policy enforcement documentation | `docs/ci/CI_POLICY_ENFORCEMENT.md` | 2025-12-30 | FND-0004 |
| EV-9004 | Risk module clarity (src/risk vs src/risk_layer) | `src/risk/README.md`, `src/risk_layer/README.md` | 2025-12-30 | FND-0002 |
| EV-9005 | Execution module clarity (src/execution vs src/execution_simple) | `src/execution/README.md`, `src/execution_simple/README.md` | 2025-12-30 | FND-0003 |

---

## Notes

- All evidence items must be timestamped and reference the audit baseline commit
- Redact any sensitive information (API keys, secrets, credentials)
- Evidence must be reproducible where possible (provide exact commands)
- Cross-reference to findings using FND-XXXX notation
