# Peak_Trade Knowledge Base Index

> **Purpose:** Central index and navigation hub for all Peak_Trade documentation, knowledge, and learning resources
>
> **Target Audience:** All developers, operators, researchers, and stakeholders working with Peak_Trade
>
> **Last Updated:** 2025-12-19

---

## Quick Navigation

### 🚀 Getting Started
- [README](../README.md) - Main landing page
- [Getting Started](GETTING_STARTED.md) - First hour onboarding
- [First 7 Days](PEAK_TRADE_FIRST_7_DAYS.md) - First week onboarding
- [Dev Setup](DEV_SETUP.md) - Development environment setup

### 🏗️ Architecture & Design
- [Architecture Overview](ARCHITECTURE_OVERVIEW.md) - System architecture
- [Architecture Details](ARCHITECTURE.md) - Detailed architecture documentation
- ADR 0001: Tool Stack (archived) - Architecture decision record

### 📚 Core Concepts

#### Trading & Strategy
- [Backtest Engine](BACKTEST_ENGINE.md) - Backtesting system
- [Strategy Development Guide](DEV_GUIDE_ADD_STRATEGY.md) - How to add strategies
- [Strategy Library](PORTFOLIO_STRATEGY_LIBRARY.md) - Available strategies
- [Portfolio Recipes](PORTFOLIO_RECIPES_AND_PRESETS.md) - Portfolio configurations

#### Risk & Safety
- [Risk Management](LIVE_RISK_LIMITS.md) - Risk limits and controls
- [Governance & Safety](GOVERNANCE_AND_SAFETY_OVERVIEW.md) - Safety processes
- [Live Gating](PHASE_83_LIVE_GATING_AND_RISK_POLICIES.md) - Production gating

#### Research & Experimentation
- [Research Golden Paths](PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md) - Research workflows
- [Hyperparam Sweeps](HYPERPARAM_SWEEPS.md) - Parameter optimization
- [Monte Carlo Robustness](PHASE_45_MONTE_CARLO_ROBUSTNESS_AND_STRESS_TESTS.md) - Robustness testing
- [Walk Forward Testing](PHASE_44_WALKFORWARD_TESTING.md) - Walk-forward validation

### 🔧 Development Guides

#### How-To Guides
- [Add a Strategy](DEV_GUIDE_ADD_STRATEGY.md)
- [Add an Exchange](DEV_GUIDE_ADD_EXCHANGE.md)
- [Add Live Risk Limit](DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md)
- [Add Portfolio Recipe](DEV_GUIDE_ADD_PORTFOLIO_RECIPE.md)

#### Development Tools
- [CLI Cheatsheet](CLI_CHEATSHEET.md) - Command line reference
- [Dev Workflow Shortcuts](DEV_WORKFLOW_SHORTCUTS.md) - Productivity tips
- [Config Registry Usage](CONFIG_REGISTRY_USAGE.md) - Configuration system

### 🤖 AI Integration
- [AI Helper Guide](ai/PEAK_TRADE_AI_HELPER_GUIDE.md) - AI working agreements
- [Claude Guide](ai/CLAUDE_GUIDE.md) - Technical AI reference

### 🚦 Live Operations

#### Operations & Monitoring
- [Live Ops CLI](PHASE_51_LIVE_OPS_CLI.md) - Live operations tools
- [Live Status Reports](LIVE_STATUS_REPORTS.md) - Monitoring and reporting
- [Live Track Dashboard](PHASE_82_LIVE_TRACK_DASHBOARD.md) - Dashboard overview
- [Observability Plan](OBSERVABILITY_AND_MONITORING_PLAN.md) - Monitoring strategy

#### Incident Management
- [Incident Simulation & Drills](INCIDENT_SIMULATION_AND_DRILLS.md) - Practice incidents
- [Runbooks & Incident Handling](RUNBOOKS_AND_INCIDENT_HANDLING.md) - Response procedures
- [Incident Drill Log](INCIDENT_DRILL_LOG.md) - Historical drills

### 📊 Reporting & Visualization
- [Reporting V2](REPORTING_V2.md) - Reporting system
- [Execution Reporting](EXECUTION_REPORTING.md) - Trade execution reports
- [Experiment Explorer](EXPERIMENT_EXPLORER.md) - Research results explorer

### 🔒 Stability & Resilience
- [Resilience](RESILIENCE.md) - System resilience patterns
- [Stability Wave B Plan](stability/WAVE_B_PLAN.md) - Stability improvements
- [Performance Monitoring](../src/core/performance.py) - Performance tracking

---

## Documentation Categories

### By Role

#### For Researchers/Quants
1. [Research Golden Paths](PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md)
2. [Strategy Research Playbook](STRATEGY_RESEARCH_PLAYBOOK.md)
3. [Experiment Explorer](EXPERIMENT_EXPLORER.md)
4. [Hyperparam Sweeps](HYPERPARAM_SWEEPS.md)
5. [Portfolio Robustness](PHASE_47_PORTFOLIO_ROBUSTNESS_AND_STRESS_TESTING.md)

#### For Developers
1. [Dev Setup](DEV_SETUP.md)
2. [Architecture Overview](ARCHITECTURE_OVERVIEW.md)
3. [Dev Guide: Add Strategy](DEV_GUIDE_ADD_STRATEGY.md)
4. [Dev Guide: Add Exchange](DEV_GUIDE_ADD_EXCHANGE.md)
5. [CLI Cheatsheet](CLI_CHEATSHEET.md)

#### For Operators
1. [Live Ops CLI](PHASE_51_LIVE_OPS_CLI.md)
2. [Live Status Reports](LIVE_STATUS_REPORTS.md)
3. [Incident Simulation & Drills](INCIDENT_SIMULATION_AND_DRILLS.md)
4. [Runbooks & Incident Handling](RUNBOOKS_AND_INCIDENT_HANDLING.md)
5. [Live Track Dashboard](PHASE_82_LIVE_TRACK_DASHBOARD.md)

#### For Risk Officers
1. [Governance & Safety](GOVERNANCE_AND_SAFETY_OVERVIEW.md)
2. [Risk Limits](LIVE_RISK_LIMITS.md)
3. [Live Gating](PHASE_83_LIVE_GATING_AND_RISK_POLICIES.md)
4. [Safety Policy](SAFETY_POLICY_TESTNET_AND_LIVE.md)
5. [Live Readiness Checklists](LIVE_READINESS_CHECKLISTS.md)

### By Topic

#### Configuration
- [Config Registry Usage](CONFIG_REGISTRY_USAGE.md)
- [Portfolio Recipes](PORTFOLIO_RECIPES_AND_PRESETS.md)
- [Strategy Config](strategy_config.md)
- [Live Overrides](LIVE_OVERRIDES_CONFIG_INTEGRATION.md)

#### Testing
- [Test Suite Overview](PHASE_36_TEST_SUITE_AND_CONFIG_HYGIENE.md)
- [Strategy Smoke Tests](PHASE_77_CI_STRATEGY_SMOKE_TESTS.md)
- [Real Market Strategy Smokes](PHASE_78_REAL_MARKET_STRATEGY_SMOKES.md)

#### Data & Exchange
- [Data Contracts](../tests/test_data_contracts.py)
- [Exchange Integration](DEV_GUIDE_ADD_EXCHANGE.md)
- [Kraken Cache Loader](../tests/test_kraken_cache_loader.py)

---

## Learning Paths

### Path 1: Complete Beginner → Production Ready
1. **Week 1: Foundation**
   - [ ] Read [README](../README.md)
   - [ ] Complete [Getting Started](GETTING_STARTED.md)
   - [ ] Follow [First 7 Days](PEAK_TRADE_FIRST_7_DAYS.md)
   - [ ] Setup [Dev Environment](DEV_SETUP.md)

2. **Week 2: Core Concepts**
   - [ ] Study [Architecture Overview](ARCHITECTURE_OVERVIEW.md)
   - [ ] Read [Backtest Engine](BACKTEST_ENGINE.md)
   - [ ] Understand [Risk Management](LIVE_RISK_LIMITS.md)
   - [ ] Review [Strategy Library](PORTFOLIO_STRATEGY_LIBRARY.md)

3. **Week 3: Hands-On Development**
   - [ ] Create a simple strategy using [Dev Guide](DEV_GUIDE_ADD_STRATEGY.md)
   - [ ] Run backtests with [CLI Cheatsheet](CLI_CHEATSHEET.md)
   - [ ] Experiment with [Portfolio Recipes](PORTFOLIO_RECIPES_AND_PRESETS.md)

4. **Week 4: Research & Testing**
   - [ ] Follow [Research Golden Paths](PEAK_TRADE_RESEARCH_GOLDEN_PATHS.md)
   - [ ] Run [Hyperparam Sweeps](HYPERPARAM_SWEEPS.md)
   - [ ] Perform [Walk Forward Testing](PHASE_44_WALKFORWARD_TESTING.md)

5. **Month 2+: Operations & Live**
   - [ ] Learn [Live Ops CLI](PHASE_51_LIVE_OPS_CLI.md)
   - [ ] Practice [Incident Drills](INCIDENT_SIMULATION_AND_DRILLS.md)
   - [ ] Study [Governance](GOVERNANCE_AND_SAFETY_OVERVIEW.md)
   - [ ] Review [Live Readiness](LIVE_READINESS_CHECKLISTS.md)

### Path 2: Strategy Developer Fast Track
1. [ ] [Dev Setup](DEV_SETUP.md)
2. [ ] [Architecture Overview](ARCHITECTURE_OVERVIEW.md) (sections on Strategy Layer)
3. [ ] [Dev Guide: Add Strategy](DEV_GUIDE_ADD_STRATEGY.md)
4. [ ] [Strategy Research Playbook](STRATEGY_RESEARCH_PLAYBOOK.md)
5. [ ] [CLI Cheatsheet](CLI_CHEATSHEET.md)
6. [ ] [Hyperparam Sweeps](HYPERPARAM_SWEEPS.md)

### Path 3: Operations Engineer Fast Track
1. [ ] [Getting Started](GETTING_STARTED.md)
2. [ ] [Architecture Overview](ARCHITECTURE_OVERVIEW.md) (sections on Live Layer)
3. [ ] [Live Ops CLI](PHASE_51_LIVE_OPS_CLI.md)
4. [ ] [Live Status Reports](LIVE_STATUS_REPORTS.md)
5. [ ] [Incident Simulation & Drills](INCIDENT_SIMULATION_AND_DRILLS.md)
6. [ ] [Runbooks](RUNBOOKS_AND_INCIDENT_HANDLING.md)

---

## Documentation Health & Maintenance

### Documentation Standards
- All new features must include documentation
- Developer guides for extensibility points
- Runbooks for operational procedures
- Tests for code examples
- Cross-references between related docs

### Documentation Review Checklist
- [ ] Accurate and up-to-date information
- [ ] Clear target audience identified
- [ ] Examples and code snippets tested
- [ ] Cross-references to related docs
- [ ] Navigation aids (TOC, links)
- [ ] Screenshots where appropriate
- [ ] Version/date information

### Contributing to Documentation
See [AI Helper Guide](ai/PEAK_TRADE_AI_HELPER_GUIDE.md) for documentation contribution guidelines.

---

## Search & Discovery

### Finding Information

#### By Keyword
Use repository search for:
- **Strategy**: DEV_GUIDE_ADD_STRATEGY.md, PORTFOLIO_STRATEGY_LIBRARY.md
- **Risk**: LIVE_RISK_LIMITS.md, GOVERNANCE_AND_SAFETY_OVERVIEW.md
- **Backtest**: BACKTEST_ENGINE.md, STRATEGY_RESEARCH_PLAYBOOK.md
- **Live**: LIVE_OPS_CLI.md, LIVE_STATUS_REPORTS.md
- **Monitoring**: OBSERVABILITY_AND_MONITORING_PLAN.md, LIVE_STATUS_REPORTS.md

#### By Phase Number
Phase documentation follows format: `PHASE_XX_DESCRIPTION.md`
- Phase 16-30: Core infrastructure
- Phase 31-50: Research & monitoring
- Phase 51-74: Live operations
- Phase 75-86: Advanced features

#### By File Type
- `docs&#47;*.md` - General documentation
- `docs&#47;ai&#47;*.md` - AI integration guides
- `docs&#47;runbooks&#47;*.md` - Operational runbooks
- `docs&#47;stability&#47;*.md` - Stability & performance
- `docs&#47;learning_promotion&#47;*.md` - Learning & promotion loop

---

## Quick Reference Cards

### Common Commands
```bash
# Research
python scripts/research_cli.py portfolio --config config/config.toml

# Backtest
python scripts/run_backtest.py --strategy ma_crossover

# Live Ops
python scripts/live_ops.py health --config config/config.toml
python scripts/live_ops.py portfolio --config config/config.toml

# Reports
python scripts/generate_live_status_report.py --format markdown
```

### Key Concepts
- **Strategy**: Trading logic for signals
- **Portfolio**: Collection of strategies with weights
- **Recipe**: Pre-configured portfolio template
- **Sweep**: Parameter optimization run
- **Walk-Forward**: Out-of-sample validation
- **Shadow**: Paper trading without real orders
- **Testnet**: Trading on test exchange
- **Live**: Production trading (gated)

### Safety Gates
- Research → Shadow: Code review required
- Shadow → Testnet: Governance approval
- Testnet → Live: Multi-level gating + checklist

---

## Additional Resources

### External References
- Peak Trade Tool Stack ADR (archived)
- [Makefile Commands](../Makefile)
- [Project Board Setup](PROJECT_BOARD_SETUP.md)

### Status & Progress
- [Peak Trade Status Overview](PEAK_TRADE_STATUS_OVERVIEW.md)
- [V1.0 Overview](PEAK_TRADE_V1_OVERVIEW_FULL.md)
- [Release Notes](PEAK_TRADE_V1_RELEASE_NOTES.md)
- [Known Limitations](PEAK_TRADE_V1_KNOWN_LIMITATIONS.md)

### Deep Dives
- [Research Backoffice Overview](DEEP_RESEARCH_BACKOFFICE_OVERVIEW.md)
- [Position Sizing](../src/core/position_sizing.py)
- [Regime Analysis](REGIME_ANALYSIS.md)

---

## Feedback & Improvements

### How to Improve This Index
1. Missing documentation? Add it to the appropriate section
2. Found broken links? Update the reference
3. Better organization ideas? Propose changes
4. New learning path? Document it

### Documentation Gaps
Known areas needing documentation:
- Advanced ML strategy integration
- Custom exchange adapters
- Performance tuning guide
- Debugging workflows

---

## Version History

| Date       | Version | Changes                                    |
|------------|---------|-------------------------------------------|
| 2025-12-19 | 1.0     | Initial knowledge base index created      |

---

**Navigation:** [⬆️ Back to Top](#peak_trade-knowledge-base-index) | [📖 README](../README.md)
