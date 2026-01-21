# Peak_Trade Architecture Overview

**Evidence ID:** EV-1002  
**Date:** 2025-12-30  
**Audit Baseline:** fb829340dbb764a75c975d5bf413a4edb5e47107

## System Inventory

### Repository Statistics
- **Total Subsystems:** 42 (in `src/`)
- **Total Python Files:** 396
- **Config Files:** 50+ TOML/YAML files in `config/`
- **Scripts:** 269 files (162 Python, 100 Shell)
- **Tests:** 317 files (307 Python)

### Core Subsystems

#### 1. Data Pipeline
- `src/data/` - Market data ingestion and validation
- `src/data/kraken_live.py` - Live exchange data source
- Exchange adapters in `src/exchange/`

#### 2. Strategy & Signal Generation
- `src/strategies/` - 31 strategy modules
- `src/backtest/` - Backtesting engine
- `src/research/` - ML and meta-labeling

#### 3. Portfolio & Position Management
- `src/portfolio/` - Portfolio tracking and accounting
- `src/orders/` - Order abstraction layer
- `src/execution/` - Execution pipeline
- `src/execution_simple/` - Simplified execution

#### 4. Risk Management (Critical)
- `src/risk/` - Legacy/core risk module
- `src/risk_layer/` - New risk layer
  - `kill_switch&#47;` - Emergency halt system (Layer 4)
  - `alerting&#47;` - Alert management
  - `var_backtest&#47;` - VaR backtesting (Kupiec POF, etc.)
- `src/governance/` - Trading governance policies

#### 5. Live Trading (Critical)
- `src/live/` - Live trading orchestration
  - `shadow_session.py` - Shadow/paper trading session
  - `testnet_orchestrator.py` - Testnet orchestration
  - `safety.py` - Safety guards and environment gates
  - `risk_limits.py` - Live risk limit checks
  - `drills.py` - Dry-run drill framework
  - `workflows.py` - Live risk check workflows
  - `web&#47;` - Live monitoring web UI

#### 6. Execution & Exchange Integration
- `src/execution/pipeline.py` - ExecutionPipeline (signals → orders)
- `src/orders/paper.py` - Paper executor
- `src/orders/shadow.py` - Shadow executor
- `src/exchange/` - Exchange API adapters

#### 7. Monitoring & Observability
- `src/observability/` - Observability framework
- `src/reporting/` - 29 reporting modules
- `src/ops/` - Operational tooling
- `src/notifications/` - Alert channels (Slack, email, etc.)

#### 8. Supporting Systems
- `src/analytics/` - Analysis tools
- `src/autonomous/` - Autonomous components
- `src/experiments/` - Experiment tracking
- `src/scheduler/` - Task scheduling
- `src/webui/` - Web interface

## Critical Data Flow Paths

### Path 1: Live Trading (Shadow/Paper Mode)
```
Market Data (Kraken/Exchange)
  ↓
LiveCandleSource (src/data/kraken_live.py)
  ↓
ShadowPaperSession (src/live/shadow_session.py)
  ↓
Strategy Signal Generation (src/strategies/)
  ↓
ExecutionPipeline (src/execution/pipeline.py)
  ↓
LiveRiskLimits Check (src/live/risk_limits.py)
  ↓
Kill Switch Gate (src/risk_layer/kill_switch/execution_gate.py)
  ↓
PaperOrderExecutor / ShadowOrderExecutor (src/orders/)
  ↓
Logging & Metrics (src/live/run_logger.py)
```

### Path 2: Risk Gate Check (Pre-Trade)
```
Order Request
  ↓
LiveRiskLimits.check_orders() (src/live/risk_limits.py)
  ↓
Pre-trade Checks:
  - Max notional per order
  - Max total notional
  - Position limits
  - Drawdown limits
  ↓
Kill Switch Check (src/risk_layer/kill_switch/)
  ↓
PASS → Order allowed
FAIL → Order blocked with violations
```

### Path 3: Kill Switch Trigger (Emergency Halt)
```
Trigger Event:
  - Manual trigger (CLI)
  - Threshold breach (drawdown, loss, etc.)
  - External signal
  - Watchdog timeout
  ↓
KillSwitch.trigger() (src/risk_layer/kill_switch/core.py)
  ↓
State: ACTIVE → KILLED
  ↓
ExecutionGate.check_can_execute() raises TradingBlockedError
  ↓
All order execution blocked
  ↓
Recovery requires:
  1. request_recovery() with approval code
  2. Cooldown period (default 300s)
  3. complete_recovery()
```

### Path 4: Backtest (Offline Simulation)
```
Historical Data (CSV/DB)
  ↓
BacktestEngine (src/backtest/)
  ↓
Strategy Signal Generation
  ↓
Portfolio Accounting (fills, fees, ledger)
  ↓
Risk Metrics Calculation
  ↓
Report Generation (src/reporting/)
```

## Live-Critical Components (Audit Priority)

### P0 Components (Must be correct for live trading)
1. **Kill Switch** (`src/risk_layer/kill_switch/`) - Emergency halt
2. **Safety Guards** (`src/live/safety.py`) - Environment gating
3. **LiveRiskLimits** (`src/live/risk_limits.py`) - Pre-trade checks
4. **ExecutionGate** (`src/risk_layer/kill_switch/execution_gate.py`) - Order gate
5. **ShadowPaperSession** (`src/live/shadow_session.py`) - Live orchestration
6. **Exchange Integration** (`src/exchange/`, `src/data/kraken_live.py`) - Market data & orders

### P1 Components (Important for safe operation)
1. **ExecutionPipeline** (`src/execution/pipeline.py`) - Signal → Order pipeline
2. **Risk Alerting** (`src/risk_layer/alerting/`) - Alert dispatch
3. **Governance Policies** (`src/governance/`) - Policy enforcement
4. **Drill Framework** (`src/live/drills.py`) - Testing and validation
5. **Monitoring UI** (`src/live/web/`, `src/webui/`) - Operator visibility

### P2 Components (Supporting systems)
1. **Reporting** (`src/reporting/`) - Post-trade analysis
2. **Observability** (`src/observability/`) - Telemetry
3. **Scheduler** (`src/scheduler/`) - Task automation

## Environment Modes (Safety Model)

Based on `src/live/safety.py`:

### SHADOW Mode
- Real exchange data
- Paper orders (not submitted to exchange)
- No real money at risk
- Full risk checks active for testing

### PAPER Mode
- Similar to SHADOW
- May use different market data source
- Paper execution

### TESTNET Mode
- Exchange testnet API
- Testnet assets (not real money)
- Real API calls but test environment

### LIVE Mode (Phase 71+)
- **NOT IMPLEMENTED IN CURRENT CODE**
- Would require ALL gates to pass:
  1. `live_trading_gate_1="enabled"  # avoid boolean pattern` (Gate 1)
  2. `live_mode_state="prepared"  # boolean form intentionally avoided in docs` (Gate 2)
  3. `live_dry_run_mode=False` (Technical gate - currently always True)
  4. Valid confirm token
  5. Kill switch not triggered

**Current Status:** `live_dry_run_mode=True` is hardcoded in Phase 71, preventing real live orders.

## Configuration Architecture

### Config Files (Key Locations)
- `config/config.toml` - Main config
- `config/live_policies.toml` - Live allowlist and policies
- `config&#47;risk&#47;*.toml` - Risk layer configs
- `config&#47;portfolios&#47;*.toml` - Portfolio configs
- `config/regimes.toml` - Market regime definitions

### Environment Variables
- API keys loaded from environment (not in repo - verified via .gitignore)
- Secrets management via external vault or env vars

## Findings Summary (Architecture Phase)

See detailed findings in `docs/audit/findings/`:
- FND-0001: Live mode implementation gap (live_dry_run_mode hardcoded)
- FND-0002: Dual risk systems (risk/ vs risk_layer/) - potential confusion
- FND-0003: Multiple execution paths (execution/ vs execution_simple/) - clarity needed

## Next Steps for Detailed Review

1. **Build/CI** - Verify reproducibility, test coverage
2. **Backtest Correctness** - Lookahead bias, fee model, accounting
3. **Risk Layer** - Deep dive on kill switch, limits, gates
4. **Execution** - Order lifecycle, idempotency, retry logic
5. **Security** - Secrets scan, dependency audit
6. **Ops** - Runbooks, monitoring, incident response
