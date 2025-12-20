# Configuration

Peak Trade uses TOML configuration files for system settings.

## Configuration Files

- `config.toml` - Main configuration
- `config/feature_flags.json` - Feature flag settings
- `config/regimes.toml` - Market regime definitions
- `config/portfolio_recipes.toml` - Portfolio presets

## Main Configuration

Edit `config.toml`:

```toml
[backtest]
initial_capital = 10000.0
commission = 0.001        # 0.1% per trade
slippage = 0.0005        # 0.05% slippage

[risk]
max_position_size = 0.1   # 10% per position
max_portfolio_risk = 0.2  # 20% total portfolio risk
stop_loss_pct = 0.02      # 2% stop loss
take_profit_pct = 0.05    # 5% take profit

[data]
data_dir = "data/"
cache_dir = ".cache/"

[execution]
default_exchange = "kraken"
dry_run = true            # Paper trading mode
```

## Environment Variables

Set via `.env` file or shell:

```bash
# Environment (development, staging, production)
ENVIRONMENT=development

# Exchange API keys (for live trading)
EXCHANGE_API_KEY=your_key_here
EXCHANGE_API_SECRET=your_secret_here

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/peak_trade.log
```

## Feature Flags

Control feature rollouts in `config/feature_flags.json`:

```json
{
  "enable_redis_cache": {
    "enabled": true,
    "environments": ["production", "staging"]
  },
  "enable_ai_workflow": {
    "enabled": true,
    "percentage": 50
  },
  "enable_experimental_strategies": {
    "enabled": false,
    "environments": ["development"]
  }
}
```

See [Feature Flags Guide](../guides/feature-flags.md) for more details.

## Configuration Loading

```python
from src.core.config_simple import load_config

# Load default config
config = load_config()

# Load specific config file
config = load_config("config.test.toml")

# Access settings
print(config.backtest.initial_capital)
print(config.risk.max_position_size)
```

## Next Steps

- [Quick Start Tutorial](quickstart.md)
- [Feature Flags Guide](../guides/feature-flags.md)
- [Architecture Overview](../architecture/overview.md)
