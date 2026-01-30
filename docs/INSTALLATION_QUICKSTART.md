# Peak_Trade – Installation Quickstart

**Purpose:** Entry point for all installation, setup, and getting started resources  
**Last Updated:** 2026-01-12  
**Target Audience:** New users, onboarding, setup verification

---

## 🎯 Quick Navigation

### 📘 Comprehensive Installation & Roadmap (2026-01-12)

**[INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md](../INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md)**

**Status:** ✅ AUTHORITATIVE, COMPLETE INSTALLATION & ROADMAP GUIDE  
**Version:** v1.0 (2026-01-12)  
**Size:** 1161 lines  
**Use Case:** Complete installation walkthrough (0→ready in 11 steps), verification, roadmap through 2026

**Key Content:**
- **Teil 1 (Current State):** Complete feature inventory (100+ features across 6 categories) – Phases 1-10 @ 100%
- **Teil 2 (Installation):** 11-step setup guide (system requirements → first research session)
- **Teil 3 (Verification):** Smoke-test matrix, troubleshooting, health checks
- **Teil 4 (Roadmap):** Phase 11-17 (2026+), including **Phase 13 Governance-Gate** (live trading)
- **Teil 5 (Next Steps):** Concrete action items (short/mid/long-term)
- **Teil 6 (Success Criteria):** Definition of Done, milestone matrix, risk register
- **Teil 7 (Resources):** Internal docs + external links (Python, Trading, Testing)
- **Teil 8 (Checklists):** Pre-flight, post-deployment, phase-completion, **governance-gate**

**When to Use:**
- First-time installation
- Onboarding new team members
- Understanding project roadmap (Phase 11-17)
- Governance-gate preparation (Phase 13 live trading)
- System verification after updates

---

### 📙 Quick Start (< 1 Hour)

**[GETTING_STARTED.md](./GETTING_STARTED.md)**

**Status:** ✅ OPERATIONAL, FAST-TRACK SETUP  
**Use Case:** Get running in under 1 hour (skip detailed explanations)

---

### 📕 First 7 Days Onboarding

**[PEAK_TRADE_FIRST_7_DAYS.md](./PEAK_TRADE_FIRST_7_DAYS.md)**

**Status:** ✅ OPERATIONAL, STRUCTURED ONBOARDING  
**Use Case:** Week-by-week learning path (Day 1: setup, Day 7: research)

---

## 🗺️ Related Documentation

### Setup & Configuration
- [Dev Setup Guide](./DEV_SETUP.md) – Developer-specific setup
- [README.md](../README.md) – Project overview + quick start
- [CLI Cheatsheet](./CLI_CHEATSHEET.md) – Complete CLI reference (18 sections)

### Architecture & Design
- [Architecture Overview](./ARCHITECTURE_OVERVIEW.md) – System architecture
- [Peak_Trade Overview](./PEAK_TRADE_OVERVIEW.md) – Feature overview
- [Backtest Engine](./BACKTEST_ENGINE.md) – Engine details

### Operations
- [Live Operational Runbooks](./LIVE_OPERATIONAL_RUNBOOKS.md) – 12+ runbooks
- [Workflow Frontdoor](./WORKFLOW_FRONTDOOR.md) – Workflow docs navigation

### Governance
- [Governance and Safety Overview](./GOVERNANCE_AND_SAFETY_OVERVIEW.md) – Governance framework
- [Safety Policy Testnet and Live](./SAFETY_POLICY_TESTNET_AND_LIVE.md) – Safety policies

---

## 📊 Installation Pathways

### For New Users (Zero to Ready)

**Recommended Path:**
1. [INSTALLATION_UND_ROADMAP Teil 2](../INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md#-teil-2-installation--setup) – 11-step complete guide
2. Verification: Smoke tests (< 1 min)
3. First backtest

**What You Get:**
- Complete system setup (Python 3.11+, venv, dependencies)
- Config file creation with examples
- Directory structure validation
- Import verification tests
- Health check confirmation

**Estimated Time:** 30-60 minutes

---

### For Developers (Fast Setup)

**Recommended Path:**
1. [GETTING_STARTED.md](./GETTING_STARTED.md) – Fast-track (< 1 hour)
2. [DEV_SETUP.md](./DEV_SETUP.md) – Developer tools + workflow
3. [CLI_CHEATSHEET.md](./CLI_CHEATSHEET.md) – Command reference

**What You Get:**
- Quick setup without detailed explanations
- Developer-specific tools (linting, type-checking, testing)
- CLI command reference (18 sections)

**Estimated Time:** 45 minutes

---

### For Operators (Operations Focus)

**Recommended Path:**
1. [INSTALLATION_UND_ROADMAP Teil 3](../INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md#-teil-3-verifikation--tests) – Verification matrix
2. [LIVE_OPERATIONAL_RUNBOOKS.md](./LIVE_OPERATIONAL_RUNBOOKS.md) – Operations guides (12+ runbooks)
3. [WORKFLOW_FRONTDOOR.md](./WORKFLOW_FRONTDOOR.md) – Daily workflow navigation

**What You Get:**
- Smoke-test matrix (6 verification tests)
- Troubleshooting guides (4 common problems)
- Health check procedures
- Live operations commands

**Estimated Time:** 60 minutes (including verification)

---

## 🚨 Governance-Gate Notice (Phase 13)

**Live Trading (Phase 13) requires explicit governance approval.**

See [INSTALLATION_UND_ROADMAP Teil 4 (Phase 13)](../INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md#phase-13-production-live-trading-q2-2026--️-governance-review-erforderlich) for details.

See [INSTALLATION_UND_ROADMAP Teil 8 (Governance-Gate Checklist)](../INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md#governance-gate-checklist-für-phase-13--live-trading) for requirements.

**Requirements (13-point checklist):**
- Two-Man-Rule für Live-Aktivierung
- Go/No-Go-Checklist vollständig abgearbeitet
- Incident-Drills durchgeführt (min. 5x)
- Insurance & Legal-Review abgeschlossen
- Kill-Switch getestet (min. 3x)
- Audit-Trail vollständig
- Risk-Limits konservativ konfiguriert
- Owner-Freigabe schriftlich erhalten
- Backup-Plan & Rollback-Strategie
- 24/7-Monitoring eingerichtet
- On-Call-Rotation definiert
- Incident-Response-Team bereit
- Alle Phasen 1-12 vollständig abgeschlossen

**Target Date:** Q2 2026 (estimated)

---

## ⚡ Verification Shortcuts

### Quick Health Check

Run this after installation:

```bash
python3 scripts/live_ops.py health --config config/config.toml
```

Expected output: Overall Status: OK

---

### Smoke Tests

Run this to verify core functionality:

```bash
python3 -m pytest -m smoke -q
```

Expected output: 28 passed in < 1s

---

### First Backtest

Run this to verify backtest engine:

```bash
python3 scripts/run_backtest.py --strategy ma_crossover --symbol BTC/USDT --bars 100 -v
```

Expected output: Stats displayed (Return, Sharpe, Max Drawdown, Win Rate)

---

## 📋 Quick Links

### Most Used Commands

**Health & Monitoring:**

```bash
python3 scripts/live_ops.py health --config config/config.toml
python3 scripts/live_ops.py portfolio --config config/config.toml
python3 scripts/live_monitor_cli.py overview --only-active
```

**Testing:**

```bash
python3 -m pytest -m smoke -q
python3 -m pytest -q
python3 -m pytest --cov=src --cov-report=html
```

**Backtesting:**

```bash
python3 scripts/run_backtest.py --strategy ma_crossover --symbol BTC/EUR
python3 scripts/run_portfolio_backtest.py
python3 scripts/research_cli.py portfolio --portfolio-preset rsi_reversion_conservative --format both
```

---

## 📞 Support & Next Steps

**If Installation Fails:**
1. Check system requirements (Python 3.11+, Git, 10GB free space)
2. Review troubleshooting section in [INSTALLATION_UND_ROADMAP Teil 3](../INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md#troubleshooting)
3. Verify directory structure and permissions

**After Successful Installation:**
1. Run smoke tests
2. Execute first backtest
3. Review roadmap [INSTALLATION_UND_ROADMAP Teil 4](../INSTALLATION_UND_ROADMAP_BIS_FINISH_2026-01-12.md#️-teil-4-roadmap-bis-finish)
4. Explore CLI commands ([CLI_CHEATSHEET.md](./CLI_CHEATSHEET.md))

**For Operations:**
- [LIVE_OPERATIONAL_RUNBOOKS.md](./LIVE_OPERATIONAL_RUNBOOKS.md) – 12+ runbooks
- [WORKFLOW_FRONTDOOR.md](./WORKFLOW_FRONTDOOR.md) – Workflow navigation

**For Development:**
- [DEV_SETUP.md](./DEV_SETUP.md) – Developer setup
- [STRATEGY_DEV_GUIDE.md](./STRATEGY_DEV_GUIDE.md) – Strategy development
- [DEV_GUIDE_ADD_STRATEGY.md](./DEV_GUIDE_ADD_STRATEGY.md) – Add new strategy

---

**Last Updated:** 2026-01-12  
**Next Review:** Q2 2026 or after Phase 11 completion
