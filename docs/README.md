# Peak_Trade Documentation – Frontdoor 🚪

> **Start here for navigating the Peak_Trade documentation landscape.**

---

## 📍 Start Here (30 seconds)

**New to Peak_Trade?**
1. Read: [PEAK_TRADE_OVERVIEW.md](PEAK_TRADE_OVERVIEW.md) – Architecture, Strategy Registry, Config, Quick Start
2. Run your first backtest: `python scripts/run_strategy_from_config.py --strategy ma_crossover`
3. Explore: [What changed recently?](DOCUMENTATION_UPDATE_SUMMARY.md)

**Coming back?**
- Jump to your [audience section](#by-audience) below
- Check [Recent Updates](DOCUMENTATION_UPDATE_SUMMARY.md)

---

## 🚀 Quick Start (Docs)

### Core Documentation (Start Here)

| Document | Purpose | Audience |
|----------|---------|----------|
| [PEAK_TRADE_OVERVIEW.md](PEAK_TRADE_OVERVIEW.md) | Architecture, modules, data flow, extensibility | Everyone |
| [BACKTEST_ENGINE.md](BACKTEST_ENGINE.md) | Engine contract, execution modes, extension hooks | Developers, Quants |
| [STRATEGY_DEV_GUIDE.md](STRATEGY_DEV_GUIDE.md) | Step-by-step: develop & test strategies | Strategy Developers |

### Getting Started Guides

| Document | Purpose |
|----------|---------|
| [PEAK_TRADE_FIRST_7_DAYS.md](PEAK_TRADE_FIRST_7_DAYS.md) | Onboarding guide (first week) |
| [PEAK_TRADE_V1_OVERVIEW_FULL.md](PEAK_TRADE_V1_OVERVIEW_FULL.md) | Complete v1.0 overview |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Quick start tutorial |
| [INSTALLATION_QUICKSTART.md](INSTALLATION_QUICKSTART.md) | Installation & setup |

---

## 👥 By Audience

### 🔬 Research / Quant

**Strategy Development:**
- [STRATEGY_DEV_GUIDE.md](STRATEGY_DEV_GUIDE.md) – Develop custom strategies
- [strategies_overview.md](strategies_overview.md) – Available strategies
- [STRATEGY_RESEARCH_PLAYBOOK.md](STRATEGY_RESEARCH_PLAYBOOK.md) – Research workflow

**Backtesting & Validation:**
- [BACKTEST_ENGINE.md](BACKTEST_ENGINE.md) – Engine details
- [REGISTRY_BACKTEST_API.md](REGISTRY_BACKTEST_API.md) – Registry API
- [HYPERPARAM_SWEEPS.md](HYPERPARAM_SWEEPS.md) – Parameter optimization

**Portfolio Research:**
- [PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) – Research → Live playbook
- [PORTFOLIO_RECIPES_AND_PRESETS.md](PORTFOLIO_RECIPES_AND_PRESETS.md) – Portfolio configs
- [REGIME_ANALYSIS.md](REGIME_ANALYSIS.md) – Regime-aware strategies

### 💻 Developer / Maintainer

**Architecture & System:**
- [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) – Deep dive architecture
- [ARCHITECTURE.md](ARCHITECTURE.md) – Technical architecture details
- [PEAK_TRADE_OVERVIEW.md](PEAK_TRADE_OVERVIEW.md) – High-level overview

**Development Workflow:**
- [DEVELOPER_WORKFLOW_GUIDE.md](DEVELOPER_WORKFLOW_GUIDE.md) – Workflows & automation
- [DEV_SETUP.md](DEV_SETUP.md) – Development environment
- [DEV_WORKFLOW_SHORTCUTS.md](DEV_WORKFLOW_SHORTCUTS.md) – Productivity tips

**Extending the System:**
- [BACKTEST_ENGINE.md](BACKTEST_ENGINE.md) – Extension hooks
- [ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md) – Error taxonomy
- [resilience_guide.md](resilience_guide.md) – Circuit breaker, rate limiting

### 🛰️ Ops / Live Trading

**Operations Hub:**
- [ops/README.md](ops/README.md) – **Ops operator center**
- [LIVE_OPERATIONAL_RUNBOOKS.md](LIVE_OPERATIONAL_RUNBOOKS.md) – Live ops runbooks
- [DISASTER_RECOVERY_RUNBOOK.md](DISASTER_RECOVERY_RUNBOOK.md) – DR procedures

**Live Deployment:**
- [LIVE_DEPLOYMENT_PLAYBOOK.md](LIVE_DEPLOYMENT_PLAYBOOK.md) – Deployment guide
- [LIVE_READINESS_CHECKLISTS.md](LIVE_READINESS_CHECKLISTS.md) – Pre-live checklist
- [LIVE_TESTNET_PREPARATION.md](LIVE_TESTNET_PREPARATION.md) – Testnet setup

**Monitoring & Alerts:**
- [OBSERVABILITY_AND_MONITORING_PLAN.md](OBSERVABILITY_AND_MONITORING_PLAN.md) – Monitoring architecture
- [LIVE_WORKFLOWS.md](LIVE_WORKFLOWS.md) – Live workflows
- [INCIDENT_SIMULATION_AND_DRILLS.md](INCIDENT_SIMULATION_AND_DRILLS.md) – Incident drills

### 🛡️ Governance / Safety

**Governance Hub:**
- [governance/README.md](governance/README.md) – **Governance center**
- [GOVERNANCE_AND_SAFETY_OVERVIEW.md](GOVERNANCE_AND_SAFETY_OVERVIEW.md) – Safety-first approach
- [SAFETY_POLICY_TESTNET_AND_LIVE.md](SAFETY_POLICY_TESTNET_AND_LIVE.md) – Safety policies

**AI Autonomy & Policies:**
- [governance/ai_autonomy/README.md](governance/ai_autonomy/README.md) – AI autonomy guardrails
- [governance/LLM_POLICY_CRITIC_CHARTER.md](governance/LLM_POLICY_CRITIC_CHARTER.md) – Policy critic
- [AUTONOMOUS_AI_WORKFLOW.md](AUTONOMOUS_AI_WORKFLOW.md) – Autonomous workflow

---

## 📚 Deeper Dives / Overlaps

### Architecture Deep Dives

| Document | Relation to Overview |
|----------|---------------------|
| [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) | **Deep dive** – Detailed system design, layer diagrams |
| [PEAK_TRADE_OVERVIEW.md](PEAK_TRADE_OVERVIEW.md) | **Entry point** – Quick architecture map, extensibility |

### Configuration & Setup

- [CONFIG_REGISTRY_USAGE.md](CONFIG_REGISTRY_USAGE.md) – Config system deep dive
- [REGISTRY_BACKTEST_IMPLEMENTATION.md](REGISTRY_BACKTEST_IMPLEMENTATION.md) – Registry internals

### Knowledge & AI Research

- [KNOWLEDGE_DB_ARCHITECTURE.md](KNOWLEDGE_DB_ARCHITECTURE.md) – Vector DB, time-series DB
- [KNOWLEDGE_SOURCES_GOVERNANCE_PLAYBOOK.md](KNOWLEDGE_SOURCES_GOVERNANCE_PLAYBOOK.md) – External knowledge sources
- [KNOWLEDGE_SOURCES_REGISTRY.md](KNOWLEDGE_SOURCES_REGISTRY.md) – Knowledge registry

### Execution & Order Flow

- [execution/README.md](execution/README.md) – Execution layer overview
- [ORDER_PIPELINE_INTEGRATION.md](ORDER_PIPELINE_INTEGRATION.md) – Order pipeline
- [EXECUTION_REPORTING.md](EXECUTION_REPORTING.md) – Execution reports

---

## 🆕 What Changed Recently?

**Latest Updates:**
- [DOCUMENTATION_UPDATE_SUMMARY.md](DOCUMENTATION_UPDATE_SUMMARY.md) – **Recent docs updates (2026-01-13)**
  - Extensibility points added to PEAK_TRADE_OVERVIEW.md
  - Extension hooks added to BACKTEST_ENGINE.md
  - Operational notes expanded

**Status & Roadmap:**
- [PEAK_TRADE_STATUS_OVERVIEW.md](PEAK_TRADE_STATUS_OVERVIEW.md) – Current project status
- [Peak_Trade_Roadmap.md](Peak_Trade_Roadmap.md) – Roadmap
- [PEAK_TRADE_V1_KNOWN_LIMITATIONS.md](PEAK_TRADE_V1_KNOWN_LIMITATIONS.md) – Known limitations

---

## 🗂️ Subdirectory Indexes

**Specialized Documentation Hubs:**

- **Ops / Operator Hub:** [ops/README.md](ops/README.md)
- **Audit & Compliance:** [audit/README.md](audit/README.md) *(if exists)*
- **Governance & AI Autonomy:** [governance/README.md](governance/README.md)
- **Risk Management:** [risk/](risk/) *(directory)*
- **Architecture Details:** [architecture/](architecture/) *(directory)*
- **Execution Layer:** [execution/README.md](execution/README.md)
- **Cleanup & Maintenance:** [ops/cleanup/](ops/cleanup/) *(directory)*

---

## 🔍 Finding What You Need

**By Topic:**
- **Strategy Development** → [STRATEGY_DEV_GUIDE.md](STRATEGY_DEV_GUIDE.md)
- **Backtest Setup** → [BACKTEST_ENGINE.md](BACKTEST_ENGINE.md)
- **Portfolio Research** → [PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md)
- **Live Operations** → [ops/README.md](ops/README.md)
- **Error Handling** → [ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md)
- **Resilience & Stability** → [resilience_guide.md](resilience_guide.md)

**By Workflow:**
- **First Time Setup** → [GETTING_STARTED.md](GETTING_STARTED.md)
- **Strategy Development** → [STRATEGY_DEV_GUIDE.md](STRATEGY_DEV_GUIDE.md) → [strategies_overview.md](strategies_overview.md)
- **Research Pipeline** → [STRATEGY_RESEARCH_PLAYBOOK.md](STRATEGY_RESEARCH_PLAYBOOK.md) → [HYPERPARAM_SWEEPS.md](HYPERPARAM_SWEEPS.md)
- **Go-Live Checklist** → [LIVE_READINESS_CHECKLISTS.md](LIVE_READINESS_CHECKLISTS.md) → [LIVE_DEPLOYMENT_PLAYBOOK.md](LIVE_DEPLOYMENT_PLAYBOOK.md)

---

## 📖 Additional Resources

- **Quick Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Knowledge Base Index:** [KNOWLEDGE_BASE_INDEX.md](KNOWLEDGE_BASE_INDEX.md)
- **CLI Cheatsheet:** [CLI_CHEATSHEET.md](CLI_CHEATSHEET.md)
- **AI Helper Guide:** [ai/PEAK_TRADE_AI_HELPER_GUIDE.md](ai/PEAK_TRADE_AI_HELPER_GUIDE.md)

---

**Last Updated:** 2026-01-13  
**Maintained By:** Peak_Trade Ops Team
