# Phase 5 NO-LIVE Drill — Evidence Index

---

## 🚨 NO-LIVE DRILL ONLY 🚨
**All evidence relates to simulated/drill operations. No live trading occurred.**

---

## Metadata

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD HH:MM (local time) |
| **Drill Operator** | [Your Name] |
| **Repo SHA** | `git rev-parse HEAD` |
| **Branch** | `git branch --show-current` |
| **Run ID** | drill_YYYYMMDD_HHMMSS |
| **Environment** | SHADOW / PAPER / DRILL_ONLY |
| **Strategy Tested** | [e.g., ma_crossover_drill] |
| **Symbol(s)** | [e.g., BTC-EUR] |
| **Duration** | [e.g., 30 minutes] |

---

## Artifact Inventory

### 1. Configuration Files

| Artifact | Path (relative to repo root) | Description |
|----------|-------------------------------|-------------|
| Main Config | EXAMPLE: `config/<drill_test>.toml` | Primary config used (CONFIRM mode = shadow/paper) |
| Strategy Config | EXAMPLE: `config/strategies/<strategy_name>.toml` | Strategy-specific parameters |
| Risk Config | EXAMPLE: `config/risk/<drill_risk>.toml` | Risk limits for drill (if applicable) |

**Audit Note:** All configs verified to be NO-LIVE (no production API keys, no live mode enabled).

---

### 2. Log Files

| Artifact | Path | Size | Key Events |
|----------|------|------|------------|
| System Log | `logs/system.log` | [X KB] | Startup, shutdown, health checks |
| Strategy Log | `logs/strategy_drill.log` | [X KB] | Signal generation, simulated trades |
| Audit Log | `logs/audit.log` | [X KB] | Config loads, mode verification |
| Error Log | `logs/errors.log` | [X KB] | Any exceptions (should be empty or non-critical) |

**Search Tips:**  
- Grep for "ERROR" or "CRITICAL": `grep -i error logs/*.log`
- Verify NO live orders: `grep -i "live.*order" logs/*.log` (should return nothing)

---

### 3. Trade Data (Simulated)

| Artifact | Path | Description |
|----------|------|-------------|
| Trades CSV | `results/drill_<timestamp>/trades/simulated_trades.csv` | All simulated trades (NO real fills) |
| Positions | `results/drill_<timestamp>/trades/positions.json` | Final positions (paper/shadow) |
| Order Book Snapshots | `results/drill_<timestamp>/market_data/` | (if applicable) |

**Verification:**  
- [ ] CSV header confirms "simulated" or "paper" mode
- [ ] No real order IDs from live exchange (check format)
- [ ] P&L is for drill evaluation only

---

### 4. Performance Metrics

| Artifact | Path | Description |
|----------|------|-------------|
| Summary JSON | `results/drill_<timestamp>/metrics/performance_summary.json` | Win rate, Sharpe, max drawdown, etc. |
| Risk Report | `results/drill_<timestamp>/metrics/risk_report.json` | VaR, exposure, compliance checks |
| Plots (optional) | `results/drill_<timestamp>/plots/*.png` | Equity curve, trade distribution, etc. |

**Note:** Metrics are for drill assessment; not indicative of live performance.

---

### 5. Checklists & Decision Records

| Artifact | Path | Description |
|----------|------|-------------|
| Operator Checklist | `results/drill_<timestamp>/OPERATOR_CHECKLIST.md` | Completed step-by-step checklist |
| Go/No-Go Record | `results/drill_<timestamp>/GO_NO_GO_RECORD.md` | Final drill decision |
| Post-Run Review | `results/drill_<timestamp>/POST_RUN_REVIEW.md` | Debrief notes (if completed) |

---

### 6. Screenshots / Supplementary Evidence (Optional)

| Artifact | Path | Description |
|----------|------|-------------|
| [Example] | `results/drill_<timestamp>/screenshots/telemetry_dashboard.png` | Dashboard showing drill in progress |
| [Example] | `results/drill_<timestamp>/screenshots/config_verification.png` | Terminal showing mode = shadow |

**Guidelines:**  
- Only include if they add audit value
- Annotate with timestamp + description
- Redact any sensitive info (even in drill mode)

---

## Cross-Reference with Drill Pack Procedure

| Drill Step | Evidence Artifact(s) |
|------------|---------------------|
| Step 1: Environment Setup | `logs/audit.log` (config verification), config files |
| Step 2: Pre-Flight Check | EXAMPLE: System logs, health check output |
| Step 3: Strategy Dry-Run | EXAMPLE: Strategy logs, simulated trades CSV, metrics JSON |
| Step 4: Evidence Assembly | This document (EVIDENCE_INDEX.md) |
| Step 5: Go/No-Go | `GO_NO_GO_RECORD.md` |

---

## NO-LIVE Attestation

**I, [Operator Name], attest that:**
1. All evidence listed above was generated in SHADOW/PAPER/DRILL_ONLY mode
2. No live trading occurred during this drill
3. No production API keys were used or exposed
4. All artifacts are audit-ready and retained per governance policy

**Operator Signature:** ___________________________  
**Date:** ___________________________

**Peer Reviewer (if applicable):**  
**Name:** ___________________________  
**Review Date:** ___________________________  
**Findings:** [No issues / Issues listed in GO_NO_GO_RECORD]

---

## Retention & Archival

- **Retention Period:** [e.g., 1 year minimum per PT-GOV-AI-001]
- **Archive Location:** `results/drill_<timestamp>.tar.gz` or project governance folder
- **Access Control:** Operator + governance team only

---

**END OF EVIDENCE INDEX**
