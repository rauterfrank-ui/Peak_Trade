# Strategy Development Guide

Learn how to create custom trading strategies in Peak Trade.

## Strategy Basics

All strategies inherit from `BaseStrategy`:

```python
from src.strategies.base import BaseStrategy
import pandas as pd

class MyStrategy(BaseStrategy):
    def __init__(self, param1: int, param2: float):
        super().__init__()
        self.param1 = param1
        self.param2 = param2

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.

        Args:
            data: OHLCV data with columns: open, high, low, close, volume

        Returns:
            Series of signals: 1 (buy), -1 (sell), 0 (hold)
        """
        # Your strategy logic here
        signals = pd.Series(0, index=data.index)

        # Example: Simple moving average crossover
        fast_ma = data['close'].rolling(10).mean()
        slow_ma = data['close'].rolling(30).mean()

        signals[fast_ma > slow_ma] = 1   # Buy signal
        signals[fast_ma < slow_ma] = -1  # Sell signal

        return signals
```

## Step-by-Step Development

### 1. Define Parameters

```python
class RSIStrategy(BaseStrategy):
    def __init__(
        self,
        period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0
    ):
        super().__init__()
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
```

### 2. Implement Signal Logic

```python
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Calculate RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Generate signals
        signals = pd.Series(0, index=data.index)
        signals[rsi < self.oversold] = 1    # Buy when oversold
        signals[rsi > self.overbought] = -1 # Sell when overbought

        return signals
```

### 3. Add Tests

```python
# tests/strategies/test_my_strategy.py
def test_rsi_strategy_signals():
    strategy = RSIStrategy(period=14, oversold=30, overbought=70)

    # Create test data
    data = create_test_ohlcv(
        dates=pd.date_range('2024-01-01', periods=100),
        close_prices=[100] * 100
    )

    # Generate signals
    signals = strategy.generate_signals(data)

    # Verify signal properties
    assert signals.isin([-1, 0, 1]).all()
    assert len(signals) == len(data)
```

### 4. Backtest

```python
from src.backtest.engine import BacktestEngine

# Create strategy instance
strategy = RSIStrategy(period=14, oversold=30, overbought=70)

# Run backtest
engine = BacktestEngine(initial_capital=10000.0)
results = engine.run(strategy, data)

# View results
print(f"Total Return: {results.total_return:.2%}")
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
```

## Advanced Features

### Position Sizing

```python
from src.core.position_sizing import VolatilityPositionSizer

class AdvancedStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.sizer = VolatilityPositionSizer(target_volatility=0.15)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Generate base signals
        signals = self._calculate_signals(data)

        # Adjust position sizes based on volatility
        position_sizes = self.sizer.calculate_size(data, signals)

        return signals
```

### Multiple Timeframes

```python
class MultiTimeframeStrategy(BaseStrategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Daily trend
        daily_trend = self._calculate_trend(data, period=50)

        # Hourly signals
        hourly_signals = self._calculate_hourly_signals(data)

        # Combine: only take hourly signals in direction of daily trend
        signals = hourly_signals.where(
            hourly_signals.sign() == daily_trend.sign(),
            0
        )

        return signals
```

### Risk Management

```python
class RiskAwareStrategy(BaseStrategy):
    def __init__(self, max_drawdown: float = 0.15):
        super().__init__()
        self.max_drawdown = max_drawdown

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        signals = self._base_signals(data)

        # Calculate current drawdown
        returns = data['close'].pct_change()
        cumulative = (1 + returns).cumprod()
        drawdown = (cumulative - cumulative.cummax()) / cumulative.cummax()

        # Stop trading if drawdown exceeds limit
        signals[drawdown < -self.max_drawdown] = 0

        return signals
```

## Best Practices

1. **Keep it Simple**: Start with simple logic, add complexity only if needed
2. **Validate Inputs**: Check data quality before generating signals
3. **Handle Edge Cases**: NaN values, insufficient data, etc.
4. **Document Parameters**: Explain what each parameter does
5. **Test Thoroughly**: Unit tests, backtests, robustness tests
6. **Avoid Lookahead Bias**: Don't use future data in signals
7. **Use Feature Flags**: Gate experimental strategies

## Example: Complete Strategy

```python
from src.strategies.base import BaseStrategy
from src.core.feature_flags import requires_feature, FeatureFlag
import pandas as pd

class BollingerBreakoutStrategy(BaseStrategy):
    """
    Bollinger Band breakout strategy.

    Buys when price breaks above upper band,
    sells when price breaks below lower band.
    """

    def __init__(
        self,
        period: int = 20,
        num_std: float = 2.0,
        min_volume: float = 1000.0
    ):
        super().__init__()
        self.period = period
        self.num_std = num_std
        self.min_volume = min_volume

    @requires_feature(FeatureFlag.ENABLE_EXPERIMENTAL_STRATEGIES)
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Validate input
        required_columns = ['close', 'volume']
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Data must contain {required_columns}")

        # Calculate Bollinger Bands
        ma = data['close'].rolling(self.period).mean()
        std = data['close'].rolling(self.period).std()
        upper = ma + (self.num_std * std)
        lower = ma - (self.num_std * std)

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Buy: price breaks above upper band with volume
        buy_condition = (
            (data['close'] > upper) &
            (data['volume'] > self.min_volume)
        )
        signals[buy_condition] = 1

        # Sell: price breaks below lower band
        sell_condition = data['close'] < lower
        signals[sell_condition] = -1

        return signals
```

## See Also

- [API Reference: Strategies](../api/strategies.md)
- [Backtest Engine](../architecture/backtest.md)
- [Risk Management](../architecture/risk.md)
