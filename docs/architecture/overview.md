# Architecture Overview

Peak Trade is a modular quantitative trading framework with a layered architecture.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   User Interface Layer                   │
│  (CLI Tools, Web Dashboard, Jupyter Notebooks)          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  Application Layer                       │
│  (Research, Backtest, Portfolio, Live Trading)          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                     Core Services                        │
│  (Strategy Engine, Risk Management, Feature Flags)      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                     Data Layer                           │
│  (Market Data, Caching, Exchange Integration)           │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Data Layer

**Purpose**: Handles data ingestion, storage, and access

**Components**:
- `data.loader`: Load historical market data
- `data.cache`: Efficient data caching
- `data.exchange_client`: Exchange API integration
- `data.kraken`: Kraken exchange support

**Key Features**:
- Multi-exchange support (Kraken, Binance, etc.)
- Efficient caching with atomic operations
- Data normalization and validation
- Real-time and historical data feeds

### 2. Strategy Engine

**Purpose**: Execute trading strategies and generate signals

**Components**:
- `strategies.base`: Base strategy interface
- `strategies.registry`: Strategy discovery and management
- Strategy implementations (MA, RSI, Momentum, etc.)

**Key Features**:
- Extensible strategy framework
- Pre-built strategy library
- Custom indicator support
- Signal generation and validation

### 3. Backtest Engine

**Purpose**: Historical strategy testing and analysis

**Components**:
- `backtest.engine`: Main backtest executor
- `backtest.result`: Performance metrics
- `backtest.stats`: Statistical analysis
- `backtest.walkforward`: Walk-forward validation

**Key Features**:
- Fast vectorized backtesting
- Realistic slippage and commissions
- Walk-forward analysis
- Monte Carlo simulation

### 4. Portfolio Management

**Purpose**: Multi-strategy portfolio construction and management

**Components**:
- `portfolio.manager`: Portfolio orchestration
- `experiments.portfolio_presets`: Pre-configured portfolios
- `experiments.portfolio_recipes`: Portfolio templates

**Key Features**:
- Multi-strategy allocation
- Dynamic rebalancing
- Risk-based position sizing
- Regime-aware portfolios

### 5. Risk Management

**Purpose**: Position sizing and risk controls

**Components**:
- `risk.position_sizer`: Position sizing algorithms
- `risk.limits`: Risk limit enforcement
- `core.risk`: Risk metrics and calculations

**Key Features**:
- Volatility-based sizing
- Maximum drawdown limits
- Stop-loss management
- Portfolio-level risk controls

### 6. Live Trading

**Purpose**: Production trading execution

**Components**:
- `live.shadow_session`: Paper trading
- `live.monitoring`: Real-time monitoring
- `live.alerts`: Alert system
- `live.portfolio_monitor`: Portfolio tracking

**Key Features**:
- Paper trading mode
- Real-time risk monitoring
- Alert system with notifications
- Audit logging

### 7. Observability

**Purpose**: Monitoring, logging, and metrics

**Components**:
- `obs.otel`: OpenTelemetry integration
- `reporting`: Report generation
- `infra.escalation`: Alert escalation

**Key Features**:
- Distributed tracing
- Performance metrics
- Custom dashboards
- Alert escalation

## Data Flow

### Research Workflow

```
Historical Data → Strategy → Backtest → Analysis → Optimization
                     ↓
                  Signals → Risk Management → Portfolio → Report
```

### Live Trading Workflow

```
Market Data → Strategy → Signals → Risk Check → Order → Exchange
                                       ↓
                                   Monitor → Alerts → Dashboard
```

## Configuration Management

Peak Trade uses a layered configuration system:

1. **Default Configuration**: `config.toml`
2. **Environment Variables**: Override defaults
3. **Feature Flags**: Runtime feature control
4. **Strategy Configs**: Per-strategy parameters

See [Configuration Guide](../getting-started/configuration.md).

## Extensibility

The framework is designed for easy extension:

- **Custom Strategies**: Inherit from `BaseStrategy`
- **Custom Indicators**: Implement in strategy
- **Custom Risk Rules**: Extend risk management
- **Custom Data Sources**: Implement data loader interface

## Performance Considerations

- **Vectorized Operations**: Uses NumPy/Pandas for speed
- **Caching**: Aggressive caching of market data
- **Lazy Loading**: Load data only when needed
- **Parallel Processing**: Strategy sweeps run in parallel

## Security

- **API Key Management**: Secure credential storage
- **Input Validation**: Pydantic models for validation
- **Security Scanning**: Bandit checks in CI/CD
- **Dependency Auditing**: Regular security updates

## Next Steps

- [Data Layer](data-layer.md)
- [Backtest Engine](backtest.md)
- [Portfolio Management](portfolio.md)
- [Risk Management](risk.md)
