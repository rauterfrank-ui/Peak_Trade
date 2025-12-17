# Feature Flags Guide

Feature flags enable safe deployment of new features through gradual rollouts, A/B testing, and runtime configuration without code changes.

## Overview

Peak Trade's feature flag system provides:

- ✅ **Runtime Toggles** - Enable/disable features without deployment
- ✅ **Gradual Rollouts** - Deploy to percentage of users/instances
- ✅ **A/B Testing** - Test features with specific user cohorts
- ✅ **Environment-Specific** - Different flags for dev/staging/prod
- ✅ **Safe Deployment** - Roll back instantly if issues occur

## Quick Start

### Using Feature Flags

```python
from src.core.feature_flags import FeatureFlags

# Simple boolean check
if FeatureFlags.is_enabled("new_risk_model"):
    use_new_risk_calculation()
else:
    use_legacy_risk_calculation()

# User-based rollout (for A/B testing)
if FeatureFlags.is_enabled_for_user("ai_signals", user_id):
    show_ai_signals()

# Environment-specific
if FeatureFlags.is_enabled_for_environment("debug_mode"):
    enable_debug_logging()
```

### Configuration

Feature flags are configured in `config.toml`:

```toml
[feature_flags]
# Boolean flags
enable_experimental_strategies = false
enable_ai_risk_advisor = true
enable_advanced_analytics = true

# Gradual rollouts (0.0 = 0%, 1.0 = 100%)
[feature_flags.rollout]
new_portfolio_optimizer = 0.1    # 10% rollout
ml_based_execution = 0.5         # 50% rollout
advanced_regime_detection = 0.0  # Disabled

# Environment-specific flags
[feature_flags.by_env.production]
debug_mode = false
mock_exchange = false

[feature_flags.by_env.development]
debug_mode = true
mock_exchange = true
```

## Use Cases

### 1. Feature Development

Deploy features gradually to minimize risk:

```python
# Phase 1: Development only
[feature_flags.by_env.development]
new_execution_engine = true

# Phase 2: 10% rollout in staging
[feature_flags.rollout]
new_execution_engine = 0.1

# Phase 3: 50% rollout in production
[feature_flags.rollout]
new_execution_engine = 0.5

# Phase 4: Full rollout
[feature_flags]
new_execution_engine = true
```

### 2. A/B Testing

Test new strategies with specific users:

```python
def generate_signals(user_id: str, market_data: pd.DataFrame):
    """Generate trading signals with A/B testing."""
    
    if FeatureFlags.is_enabled_for_user("ml_signals", user_id):
        # 50% of users get ML-based signals
        return ml_signal_generator.generate(market_data)
    else:
        # Other 50% get traditional signals
        return traditional_signal_generator.generate(market_data)
```

### 3. Kill Switch

Instantly disable problematic features:

```python
# In code
if FeatureFlags.is_enabled("new_risk_calculation"):
    result = new_risk_model.calculate(portfolio)
else:
    result = legacy_risk_model.calculate(portfolio)

# To disable instantly, set in environment:
# FEATURE_NEW_RISK_CALCULATION=false
```

### 4. Deprecation Path

Gradually migrate from old to new implementation:

```python
# Week 1: 10% new implementation
[feature_flags.rollout]
new_data_pipeline = 0.1

# Week 2: 25%
new_data_pipeline = 0.25

# Week 3: 50%
new_data_pipeline = 0.5

# Week 4: 100%, then remove old code
```

## API Reference

### FeatureFlags Class

#### `is_enabled(flag_name: str, default: bool = False) -> bool`

Check if a feature flag is enabled globally.

```python
if FeatureFlags.is_enabled("new_feature"):
    use_new_feature()
```

**Parameters:**
- `flag_name` - Name of the feature flag
- `default` - Default value if flag not configured

**Returns:** `True` if enabled, `False` otherwise

---

#### `is_enabled_for_user(flag_name: str, user_id: str, default: bool = False) -> bool`

Check if feature is enabled for specific user (consistent hashing).

```python
if FeatureFlags.is_enabled_for_user("ai_advisor", user_id):
    show_ai_recommendations()
```

**Parameters:**
- `flag_name` - Name of the feature flag
- `user_id` - User identifier for consistent hashing
- `default` - Default value if flag not configured

**Returns:** `True` if enabled for this user

**Note:** Same user always gets same result (consistent hashing ensures A/B test stability).

---

#### `is_enabled_for_percentage(flag_name: str, percentage: float, seed: str = "") -> bool`

Check if feature should be enabled based on percentage.

```python
# Enable for random 20% of requests
if FeatureFlags.is_enabled_for_percentage("sampling", 0.2, seed=request_id):
    perform_expensive_logging()
```

**Parameters:**
- `flag_name` - Name of the feature flag
- `percentage` - Target percentage (0.0 to 1.0)
- `seed` - Optional seed for consistent hashing

**Returns:** `True` if within percentage threshold

---

#### `get_rollout_percentage(flag_name: str, default: float = 0.0) -> float`

Get configured rollout percentage for a feature.

```python
rollout = FeatureFlags.get_rollout_percentage("new_model")
print(f"Feature is at {rollout * 100}% rollout")
```

**Returns:** Percentage as float (0.0 to 1.0)

---

#### `is_enabled_for_environment(flag_name: str, default: bool = False) -> bool`

Check if feature is enabled for current environment.

```python
if FeatureFlags.is_enabled_for_environment("verbose_logging"):
    setup_verbose_logging()
```

**Environment** is determined by `ENVIRONMENT` variable:
- `development` (default)
- `staging`
- `production`

## Configuration Details

### Simple Boolean Flags

```toml
[feature_flags]
enable_feature_x = true
enable_feature_y = false
```

```python
FeatureFlags.is_enabled("enable_feature_x")  # True
FeatureFlags.is_enabled("enable_feature_y")  # False
```

### Percentage Rollouts

```toml
[feature_flags.rollout]
feature_name = 0.25  # 25% rollout
```

```python
# Automatically uses rollout percentage
FeatureFlags.is_enabled_for_user("feature_name", user_id)
```

**How it works:**
1. Consistent hash: `MD5(flag_name:user_id)`
2. Convert to float between 0.0-1.0
3. Compare with configured percentage
4. Same user always gets same result

### Environment-Specific Flags

```toml
[feature_flags.by_env.production]
debug_mode = false
experimental_features = false

[feature_flags.by_env.development]
debug_mode = true
experimental_features = true
```

```python
# Set environment
os.environ["ENVIRONMENT"] = "production"

FeatureFlags.is_enabled_for_environment("debug_mode")  # False
```

### Environment Variable Overrides

Override any flag via environment variables:

```bash
# Override boolean flag
export FEATURE_NEW_RISK_MODEL=true

# Override rollout percentage
export FEATURE_ROLLOUT_ML_SIGNALS=0.75

# Check environment-specific
export ENVIRONMENT=staging
```

```python
# These will use environment values
FeatureFlags.is_enabled("new_risk_model")  # True
FeatureFlags.get_rollout_percentage("ml_signals")  # 0.75
```

**Variable naming:**
- Boolean: `FEATURE_{FLAG_NAME}` (uppercase)
- Rollout: `FEATURE_ROLLOUT_{FLAG_NAME}`
- Environment: `ENVIRONMENT`

## Best Practices

### 1. Start Small, Scale Gradually

```toml
# Week 1: Internal testing
[feature_flags.by_env.development]
new_feature = true

# Week 2: Small production rollout
[feature_flags.rollout]
new_feature = 0.05  # 5%

# Week 3: Expand
new_feature = 0.25  # 25%

# Week 4: Full rollout
[feature_flags]
new_feature = true  # Remove rollout config
```

### 2. Monitor Feature Usage

```python
from src.core.feature_flags import FeatureFlags
import logging

logger = logging.getLogger(__name__)

def execute_strategy():
    if FeatureFlags.is_enabled("new_strategy"):
        logger.info("Using new strategy implementation")
        return new_strategy.execute()
    else:
        logger.info("Using legacy strategy implementation")
        return legacy_strategy.execute()
```

### 3. Clean Up Old Flags

Remove flags once features are fully rolled out:

```python
# Before: Feature flag controlled
if FeatureFlags.is_enabled("new_calculation"):
    return new_calculate()
else:
    return old_calculate()

# After: Feature fully deployed
return new_calculate()  # Remove old code and flag
```

### 4. Document Flag Purpose

```toml
[feature_flags]
# TEMP: Testing new ML-based risk model (Issue #123)
# Remove after: 2024-Q1
# Owner: @username
enable_ml_risk_model = false
```

### 5. Use Consistent Naming

**Good:**
```toml
enable_ai_signals
new_portfolio_optimizer
ml_based_execution
```

**Bad:**
```toml
aiSignals  # Not snake_case
new_feature_1  # Not descriptive
temp_test  # Not clear purpose
```

### 6. Test Both Paths

```python
def test_feature_flag_enabled():
    """Test behavior when feature is enabled."""
    os.environ["FEATURE_NEW_MODEL"] = "true"
    FeatureFlags.reset_config()
    
    result = calculate_with_flag()
    assert result == expected_new_behavior

def test_feature_flag_disabled():
    """Test behavior when feature is disabled."""
    os.environ["FEATURE_NEW_MODEL"] = "false"
    FeatureFlags.reset_config()
    
    result = calculate_with_flag()
    assert result == expected_old_behavior
```

## Troubleshooting

### Flag Not Working

**Check configuration:**
```python
from src.core.feature_flags import FeatureFlags

# Check if flag is enabled
print(FeatureFlags.is_enabled("my_flag"))

# Check rollout percentage
print(FeatureFlags.get_rollout_percentage("my_flag"))

# Check environment
import os
print(os.getenv("ENVIRONMENT", "development"))
```

### Inconsistent Behavior

**Ensure consistent user IDs:**
```python
# Good: Use stable identifier
user_id = str(user.id)
FeatureFlags.is_enabled_for_user("feature", user_id)

# Bad: Use random/changing identifier
FeatureFlags.is_enabled_for_user("feature", str(random.random()))
```

### Environment Override Not Working

**Check variable name:**
```bash
# Correct
export FEATURE_MY_FLAG=true

# Incorrect (won't work)
export FEATURE_my_flag=true  # Lowercase
export MY_FLAG=true          # Missing FEATURE_ prefix
```

## Examples

### Strategy Selection

```python
def select_strategy(user_id: str, market_conditions: dict):
    """Select strategy based on feature flags."""
    
    # A/B test new ML strategy with 30% of users
    if FeatureFlags.is_enabled_for_user("ml_strategy", user_id):
        return MLStrategy(market_conditions)
    
    # Use regime-aware strategy for volatile markets
    if market_conditions["volatility"] > 0.5:
        if FeatureFlags.is_enabled("regime_aware_strategy"):
            return RegimeAwareStrategy(market_conditions)
    
    # Default strategy
    return DefaultStrategy(market_conditions)
```

### Risk Management

```python
def calculate_position_size(portfolio, signal):
    """Calculate position size with feature-gated risk models."""
    
    # New Kelly-based sizing (10% rollout)
    if FeatureFlags.is_enabled_for_percentage("kelly_sizing", 0.1):
        return calculate_kelly_position(portfolio, signal)
    
    # Advanced regime-based sizing
    if FeatureFlags.is_enabled("regime_based_sizing"):
        return calculate_regime_position(portfolio, signal)
    
    # Default fixed fractional
    return calculate_fixed_fractional(portfolio, signal)
```

### Debug Mode

```python
def setup_logging():
    """Configure logging based on environment flags."""
    
    if FeatureFlags.is_enabled_for_environment("debug_mode"):
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Debug mode enabled")
    else:
        logging.basicConfig(level=logging.INFO)
```

## Migration Guide

### Adding a New Feature Flag

1. **Add to config.toml:**
```toml
[feature_flags]
my_new_feature = false
```

2. **Implement feature:**
```python
if FeatureFlags.is_enabled("my_new_feature"):
    new_implementation()
else:
    old_implementation()
```

3. **Add tests:**
```python
def test_new_feature_enabled():
    os.environ["FEATURE_MY_NEW_FEATURE"] = "true"
    # Test new behavior

def test_new_feature_disabled():
    os.environ["FEATURE_MY_NEW_FEATURE"] = "false"
    # Test old behavior
```

4. **Roll out gradually:**
```toml
[feature_flags.rollout]
my_new_feature = 0.1  # Start with 10%
```

5. **Monitor and scale:**
```toml
my_new_feature = 0.5  # Increase to 50%
my_new_feature = 1.0  # Full rollout
```

6. **Remove flag and old code:**
```python
# After successful rollout, simplify
new_implementation()  # Remove flag check
```

---

**Related Documentation:**
- [Contributing Guide](contributing.md)
- [CI/CD Architecture](../architecture/ci-cd.md)
- [Strategy Development](../STRATEGY_DEV_GUIDE.md)

**Last Updated:** December 2024
