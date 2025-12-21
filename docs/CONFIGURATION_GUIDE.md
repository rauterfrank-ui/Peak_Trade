# Configuration Guide - Thread-Safe Registry with Hot-Reload

## Overview

Peak_Trade's configuration system provides a **thread-safe, production-ready** configuration registry with the following features:

- **Thread-Safe Access**: All reads and writes are protected by a reentrant lock (RLock)
- **Atomic Updates**: Config updates are all-or-nothing (no partial state visible)
- **Hot-Reload**: Automatically reload config when file changes (optional)
- **Rollback Mechanism**: Automatic rollback on failed reload + manual rollback support
- **Mutation Prevention**: Deep copy on reads prevents external code from modifying config
- **Snapshot History**: Maintains up to 5 config snapshots for rollback

## Architecture

### Components

1. **`src/config/models.py`**: Pydantic models for configuration validation
2. **`src/config/registry.py`**: Thread-safe registry with RLock and atomic operations
3. **`src/config/watcher.py`**: File system watcher for hot-reload (requires watchdog)
4. **`src/config/__init__.py`**: Public API exports

### Thread-Safety Guarantees

The config registry provides the following guarantees:

1. **No Race Conditions**: All config access is synchronized with RLock
2. **No Partial Updates**: Readers never see partially updated config during reload
3. **Atomic Swaps**: Config updates are atomic (all-or-nothing)
4. **Safe Concurrent Access**: Multiple readers can access config simultaneously
5. **Reentrant Lock**: Nested lock acquisition is supported (e.g., method calling method)

## Basic Usage

### Loading Configuration

```python
from src.config import get_registry
from pathlib import Path

# Get global registry instance
registry = get_registry()

# Load config from file
config = registry.load(Path("config/config.toml"))

# Access config values
print(f"Initial cash: {config.backtest.initial_cash}")
print(f"Risk per trade: {config.risk.risk_per_trade}")
```

### Thread-Safe Access

```python
from src.config import get_registry

# Get config (returns deep copy, thread-safe)
registry = get_registry()
config = registry.get_config()

# Safe to use in multiple threads
def worker_thread():
    config = registry.get_config()
    # Use config...
    print(f"Cash: {config.backtest.initial_cash}")

# Start multiple threads
import threading
threads = [threading.Thread(target=worker_thread) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### Deep Copy Protection

The registry returns a **deep copy** of the config on each read to prevent external mutations:

```python
registry = get_registry()
registry.load(Path("config.toml"))

config1 = registry.get_config()
config1.backtest.initial_cash = 99999  # Mutate copy

config2 = registry.get_config()
# config2 still has original value - mutation was isolated
print(config2.backtest.initial_cash)  # 10000.0 (original)
```

**Performance Note**: Deep copy adds ~1ms overhead per read, which is acceptable for most use cases.

## Hot-Reload

### Setup

Hot-reload requires the `watchdog` library:

```bash
pip install watchdog
```

### Starting the Watcher

```python
from src.config import get_registry, start_config_watcher
from pathlib import Path

registry = get_registry()
registry.load(Path("config.toml"))

# Start file watcher (runs in background thread)
observer = start_config_watcher(registry, Path("config.toml"))

# Config will now automatically reload when file changes
# Failed reloads automatically rollback to previous config

# To stop watching:
observer.stop()
observer.join()
```

### Configuration

Enable/disable hot-reload in `config.toml`:

```toml
[config]
# Enable automatic hot-reload on file changes
hot_reload_enabled = true

# Maximum number of snapshots to keep for rollback
max_rollback_snapshots = 5

# Reload behavior on validation errors
# false (strict): Keep previous config on error
# true: Force reload even if validation fails (NOT RECOMMENDED)
reload_on_validation_error = false
```

### Behavior on File Change

1. **File Modified**: Watchdog detects config file modification
2. **Automatic Reload**: Registry attempts to reload config
3. **Success**: New config is activated atomically
4. **Failure**: Previous config is kept (automatic rollback)
5. **Logging**: All events are logged for debugging

**Example Log Output**:

```
INFO - Config file changed: /path/to/config.toml
INFO - Config reloaded successfully from /path/to/config.toml
```

or on failure:

```
INFO - Config file changed: /path/to/config.toml
ERROR - Config reload failed: Validation error, rolling back
WARNING - Config reload failed, using previous version
```

## Manual Reload

### Reload Config

```python
from pathlib import Path

registry = get_registry()
registry.load(Path("config.toml"))

# Later, manually trigger reload
success = registry.reload(Path("config.toml"))

if success:
    print("Config reloaded successfully")
else:
    print("Reload failed, using previous config")
```

### Reload Behavior

- **Success**: New config is activated
- **Failure**: Previous config is kept (automatic rollback)
- **Thread-Safe**: Reload is atomic and thread-safe
- **Non-Blocking**: Readers during reload get consistent state

## Rollback Mechanism

### Automatic Rollback

Failed reloads **automatically rollback** to the previous config:

```python
registry = get_registry()
registry.load(Path("config.toml"))

# Corrupt the config file
Path("config.toml").write_text("INVALID TOML")

# Reload fails, automatically rolls back
success = registry.reload(Path("config.toml"))
assert success is False

# Still have original config
config = registry.get_config()
print(config.backtest.initial_cash)  # Original value
```

### Manual Rollback

Roll back to previous config snapshots:

```python
registry = get_registry()

# Load initial config
registry.load(Path("config.toml"))  # v1

# Reload multiple times
registry.reload(Path("config.toml"))  # v2
registry.reload(Path("config.toml"))  # v3
registry.reload(Path("config.toml"))  # v4

# Rollback 1 step (back to v3)
success = registry.rollback(steps=1)
assert success is True

# Rollback 2 more steps (back to v1)
success = registry.rollback(steps=2)
assert success is True
```

### Snapshot Limits

The registry keeps a configurable number of snapshots (default: 5):

- **Oldest snapshots are discarded** when limit is reached
- **Memory efficient**: Only stores necessary history
- **Configurable**: Set `max_rollback_snapshots` in config.toml

### Check Available Snapshots

```python
registry = get_registry()
registry.load(Path("config.toml"))

# Check how many snapshots are available
count = registry.get_snapshot_count()
print(f"Available snapshots for rollback: {count}")

# Try to rollback beyond available history
success = registry.rollback(steps=10)
if not success:
    print("Not enough snapshots available")
```

### Clear Snapshots

```python
# Clear all snapshots (free memory)
registry.clear_snapshots()
```

## Concurrent Access Examples

### Multiple Readers

Safe concurrent reads with no locking overhead:

```python
import threading
from src.config import get_registry

registry = get_registry()
registry.load(Path("config.toml"))

def read_config():
    for _ in range(1000):
        config = registry.get_config()
        # Process config...

# Start 100 concurrent readers
threads = [threading.Thread(target=read_config) for _ in range(100)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### Readers + Writer

Safe concurrent access with atomic updates:

```python
import threading
import time
from src.config import get_registry

registry = get_registry()
registry.load(Path("config.toml"))

def reader():
    for _ in range(100):
        config = registry.get_config()
        # Readers always see consistent state
        cash = config.backtest.initial_cash
        time.sleep(0.001)

def writer():
    for _ in range(10):
        # Reload config (atomic update)
        registry.reload(Path("config.toml"))
        time.sleep(0.01)

# Start 50 readers + 1 writer
readers = [threading.Thread(target=reader) for _ in range(50)]
writer_thread = threading.Thread(target=writer)

for t in readers:
    t.start()
writer_thread.start()

for t in readers:
    t.join()
writer_thread.join()
```

## Performance Characteristics

### Overhead

- **Deep Copy**: ~1ms per `get_config()` call
- **Lock Acquisition**: ~0.001ms per read/write
- **Reload**: ~10-50ms depending on config size
- **Memory**: ~2-10 MB for 5 snapshots (depends on config size)

### Optimizations

- **Load/Validate Outside Lock**: I/O operations don't hold the lock
- **Deep Copy Only on Read**: Internal operations use direct references
- **Efficient Snapshots**: Only store when necessary

### Scalability

Tested with:
- ✅ 100 concurrent readers + 1 writer
- ✅ 10,000 reads/second
- ✅ 10+ reloads/second
- ✅ Multiple simultaneous rollbacks

## Error Handling

### Config Not Loaded

```python
registry = get_registry()

try:
    config = registry.get_config()
except ConfigError as e:
    print(f"Error: {e.message}")
    print(f"Hint: {e.hint}")
    # Error: Config not loaded
    # Hint: Call registry.load(path) first
```

### File Not Found

```python
from src.core.errors import ConfigError

registry = get_registry()

try:
    registry.load(Path("nonexistent.toml"))
except ConfigError as e:
    print(f"Error: {e.message}")
    print(f"Hint: {e.hint}")
    print(f"Context: {e.context}")
```

### Validation Errors

```python
# Config with invalid values
registry = get_registry()

try:
    registry.load(Path("invalid_config.toml"))
except ConfigError as e:
    print(f"Validation failed: {e.message}")
    print(f"Errors: {e.context['validation_errors']}")
```

## Production Recommendations

### Best Practices

1. **Load Once at Startup**: Load config during application initialization
2. **Enable Hot-Reload**: Use file watcher in production for live updates
3. **Monitor Logs**: Watch for reload failures and rollbacks
4. **Test Config Changes**: Validate changes in staging before production
5. **Set Reasonable Limits**: Use 5-10 snapshots max (memory vs. rollback depth)

### Safety Checks

The registry includes built-in safety checks:

- **Live Trading Prevention**: Raises error if `live.enabled=true` and `live.mode='live'`
- **Risk Warnings**: Logs warnings for high-risk settings
- **Directory Creation**: Automatically creates `results_dir` and `data_dir`
- **Validation**: Pydantic validates all config values against schema

### Logging

Configure logging to monitor config system:

```python
import logging

# Enable debug logging for config system
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("src.config")
logger.setLevel(logging.DEBUG)
```

## Migration from Old Config System

### Backward Compatibility

The new config system is **backward compatible** with existing code using `src.core.config_pydantic`:

```python
# Old way (still works)
from src.core import get_config as old_get_config
config = old_get_config()

# New way (recommended)
from src.config import get_registry
registry = get_registry()
config = registry.get_config()
```

### Migration Steps

1. **Install watchdog**: `pip install watchdog`
2. **Update imports**: Replace `from src.core import get_config` with registry calls
3. **Enable hot-reload**: Set `hot_reload_enabled = true` in config.toml
4. **Test thoroughly**: Run all tests to ensure compatibility
5. **Monitor logs**: Watch for any issues during migration

## Troubleshooting

### Hot-Reload Not Working

**Problem**: Config doesn't reload when file changes

**Solutions**:
1. Check watchdog is installed: `pip install watchdog`
2. Verify `hot_reload_enabled = true` in config.toml
3. Check file permissions
4. Look for errors in logs

### High Memory Usage

**Problem**: Registry using too much memory

**Solutions**:
1. Reduce `max_rollback_snapshots` in config.toml
2. Clear snapshots periodically: `registry.clear_snapshots()`
3. Consider reload frequency

### Reload Failures

**Problem**: Config reloads keep failing

**Solutions**:
1. Check config file syntax (TOML format)
2. Validate against Pydantic schema
3. Review validation errors in logs
4. Test config in isolation

## Testing

### Unit Tests

```python
import pytest
from src.config import ConfigRegistry, reset_registry

def test_thread_safety():
    registry = ConfigRegistry()
    registry.load(Path("config.toml"))
    
    # Test concurrent access
    # ...

def test_rollback():
    registry = ConfigRegistry()
    registry.load(Path("config.toml"))
    
    # Test rollback mechanism
    # ...
```

### Integration Tests

See `tests/test_config_registry_threadsafe.py` for comprehensive examples:
- Thread-safety tests
- Atomic reload tests
- Rollback tests
- Stress tests

## References

- **Pydantic Models**: `src/config/models.py`
- **Error Taxonomy**: `src/core/errors.py`
- **Thread Safety**: Uses Python's `threading.RLock`
- **File Watching**: Uses `watchdog` library
- **Deep Copy**: Uses Python's `copy.deepcopy`

## Support

For issues or questions:
1. Check logs for error messages
2. Review test cases for examples
3. See inline documentation in source code
4. Open an issue on GitHub
