# Quick Start

Get up and running with Peak Trade in 5 minutes.

## 1. Installation

First, ensure you have Peak Trade installed. See [Installation Guide](installation.md).

## 2. Basic Configuration

Create or verify your `config.toml`:

```toml
[backtest]
initial_capital = 10000.0
commission = 0.001  # 0.1%

[risk]
max_position_size = 0.1  # 10% per position
stop_loss_pct = 0.02     # 2% stop loss
```

## 3. Run Your First Backtest

```python
from src.backtest.engine import BacktestEngine
from src.strategies.ma_crossover import MACrossoverStrategy
from src.data.loader import DataLoader

# Load historical data
data = DataLoader.load_csv("data/BTCUSDT.csv")

# Create strategy
strategy = MACrossoverStrategy(fast_period=10, slow_period=30)

# Run backtest
engine = BacktestEngine(initial_capital=10000.0)
results = engine.run(strategy, data)

# View results
print(f"Total Return: {results.total_return:.2%}")
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
print(f"Max Drawdown: {results.max_drawdown:.2%}")
```

## 4. Explore Strategy Library

Peak Trade includes several pre-built strategies:

- **MA Crossover**: Moving average crossover strategy
- **RSI Reversion**: RSI-based mean reversion
- **Bollinger Bands**: Bollinger band breakout
- **Momentum**: Momentum-based trading

Example:

```python
from src.strategies import RSIReversionStrategy

strategy = RSIReversionStrategy(
    period=14,
    oversold=30,
    overbought=70
)
```

## 5. Portfolio Management

Create a multi-strategy portfolio:

```python
from src.portfolio.manager import PortfolioManager

portfolio = PortfolioManager(
    strategies=[strategy1, strategy2, strategy3],
    weights=[0.4, 0.3, 0.3]
)

results = portfolio.backtest(data)
```

## Next Steps

- [Configuration Guide](configuration.md)
- [Strategy Development](../guides/strategy-development.md)
- [Architecture Overview](../architecture/overview.md)
- [API Reference](../api/core.md)
