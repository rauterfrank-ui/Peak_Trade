# Peak_Trade Resilience System Examples

This directory contains practical examples demonstrating the Peak_Trade resilience system features.

## Overview

The resilience system provides:

1. **Circuit Breakers** - Prevent cascading failures
2. **Retry Logic** - Handle transient failures  
3. **Health Checks** - Monitor system health
4. **Backup/Recovery** - Disaster recovery capabilities

## Examples

### Circuit Breakers

- `01_circuit_breaker_basics.py` - Basic circuit breaker usage
- `02_circuit_breaker_exchange_api.py` - Protecting exchange API calls
- `03_circuit_breaker_advanced.py` - Advanced patterns and monitoring

### Retry Logic

- `04_retry_basics.py` - Basic retry with backoff
- `05_retry_network_operations.py` - Network operations with retry
- `06_combining_patterns.py` - Circuit breaker + retry together

### Health Checks

- `07_health_check_basics.py` - Basic health check setup
- `08_health_check_system.py` - Comprehensive system health monitoring
- `09_health_check_dashboard.py` - Health dashboard integration

### Backup & Recovery

- `10_backup_basics.py` - Basic backup operations
- `11_backup_config.py` - Configuration backup/restore
- `12_backup_automated.py` - Automated backup scheduling
- `13_disaster_recovery.py` - Complete disaster recovery workflow

### Complete Integration

- `14_resilient_trading_system.py` - Full resilience integration example
- `15_production_ready.py` - Production-ready patterns

## Quick Start

Each example is self-contained and can be run independently:

```bash
cd examples/resilience
python 01_circuit_breaker_basics.py
```

## Requirements

All examples require the Peak_Trade resilience module:

```python
from src.core.resilience import circuit_breaker, retry_with_backoff, health_check
from src.core.backup_recovery import RecoveryManager
```

## Testing Examples

All examples include test mode that doesn't require real external dependencies:

```bash
python 01_circuit_breaker_basics.py --test-mode
```

## Documentation

See `docs/RESILIENCE.md` for comprehensive documentation of all resilience features.
