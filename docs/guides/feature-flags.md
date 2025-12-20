# Feature Flags Guide

Peak Trade uses a feature flag system for safe rollouts and experimentation.

## Overview

Feature flags allow you to:
- Enable/disable features without code changes
- Gradual rollouts (percentage-based)
- Environment-specific features
- A/B testing
- Runtime toggles for debugging

## Available Flags

```python
from src.core.feature_flags import FeatureFlag

# Available flags
FeatureFlag.ENABLE_REDIS_CACHE
FeatureFlag.ENABLE_AI_WORKFLOW
FeatureFlag.ENABLE_ADVANCED_METRICS
FeatureFlag.ENABLE_EXPERIMENTAL_STRATEGIES
FeatureFlag.ENABLE_BACKUP_RECOVERY
```

## Configuration

Edit `config/feature_flags.json`:

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
  "enable_advanced_metrics": {
    "enabled": true
  },
  "enable_experimental_strategies": {
    "enabled": false,
    "environments": ["development"]
  }
}
```

## Usage

### Check if Feature is Enabled

```python
from src.core.feature_flags import feature_flags, FeatureFlag

if feature_flags.is_enabled(FeatureFlag.ENABLE_REDIS_CACHE):
    # Use Redis cache
    cache = RedisCache()
else:
    # Use memory cache
    cache = MemoryCache()
```

### Decorator Pattern

```python
from src.core.feature_flags import requires_feature, FeatureFlag

@requires_feature(FeatureFlag.ENABLE_AI_WORKFLOW)
def run_ai_analysis():
    """This function only runs if AI workflow is enabled."""
    # AI analysis code
    pass
```

### Runtime Toggle

```python
from src.core.feature_flags import feature_flags, FeatureFlag

# Enable for testing
feature_flags.enable(FeatureFlag.ENABLE_EXPERIMENTAL_STRATEGIES)

# Run tests
run_experimental_tests()

# Reset overrides
feature_flags.reset_overrides()
```

## Rollout Strategies

### Environment-Based

```json
{
  "enable_new_feature": {
    "enabled": true,
    "environments": ["development", "staging"]
  }
}
```

Set environment:

```bash
export ENVIRONMENT=production
```

### Percentage-Based

```json
{
  "enable_beta_feature": {
    "enabled": true,
    "percentage": 25
  }
}
```

25% of users (based on user_id hash) will see the feature:

```python
is_enabled = feature_flags.is_enabled(
    FeatureFlag.ENABLE_BETA_FEATURE,
    user_id="user123"
)
```

### Simple Toggle

```json
{
  "enable_feature": {
    "enabled": true
  }
}
```

## Best Practices

1. **Default to Disabled**: New features should start disabled
2. **Use Descriptive Names**: `enable_redis_cache` not `flag1`
3. **Document Flags**: Comment what each flag controls
4. **Clean Up**: Remove flags when features are stable
5. **Monitor**: Track flag usage and performance impact

## Testing with Feature Flags

```python
def test_with_feature_enabled(tmp_path):
    """Test behavior with feature enabled."""
    config_file = tmp_path / "flags.json"
    config_file.write_text('{"enable_ai_workflow": {"enabled": true}}')

    flags = FeatureFlagManager(config_path=config_file)
    assert flags.is_enabled(FeatureFlag.ENABLE_AI_WORKFLOW)

    # Test feature behavior
    result = run_with_ai_workflow()
    assert result.success
```

## Debugging

Check current flag state:

```python
from src.core.feature_flags import feature_flags, FeatureFlag

# Check specific flag
print(f"Redis cache: {feature_flags.is_enabled(FeatureFlag.ENABLE_REDIS_CACHE)}")

# Check all flags
for flag in FeatureFlag:
    enabled = feature_flags.is_enabled(flag)
    print(f"{flag.value}: {enabled}")
```

## Migration Path

When a feature is stable:

1. Set `enabled: true` in all environments
2. Remove flag checks from code
3. Remove flag from `feature_flags.json`
4. Remove from `FeatureFlag` enum

## See Also

- [Configuration Guide](../getting-started/configuration.md)
- [API Reference: Feature Flags](../api/core.md#feature-flags)
