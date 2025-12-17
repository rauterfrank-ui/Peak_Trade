# Health Check System

## Overview

The Peak Trade Health Check System provides centralized health monitoring for all critical components using a traffic light system (🟢 GREEN / 🟡 YELLOW / 🔴 RED).

## Architecture

### Components

The health check system consists of:

1. **HealthChecker** - Central coordinator for all health checks
2. **Component Checks** - Individual checks for each system component:
   - Backtest Engine
   - Exchange Connectivity
   - Portfolio Management
   - Risk Management
   - Live Trading

### Status Levels

| Status | Symbol | Meaning |
|--------|--------|---------|
| GREEN  | 🟢 | Component is fully operational |
| YELLOW | 🟡 | Component has warnings but is functional |
| RED    | 🔴 | Component has critical issues and is not operational |

### Overall Status Rules

The overall system status is calculated as:
- **RED** if any component is RED
- **YELLOW** if any component is YELLOW (and none are RED)
- **GREEN** if all components are GREEN

## Usage

### Command Line Interface

Run all health checks:
```bash
python -m src.infra.health.health_checker
```

Output as JSON:
```bash
python -m src.infra.health.health_checker --json
```

Check specific component:
```bash
python -m src.infra.health.health_checker --component "Backtest Engine"
```

### Using Makefile

```bash
# Run health checks
make health-check

# Get JSON output
make health-check-json
```

### Programmatic Usage

```python
from src.infra.health import HealthChecker

# Create checker and run all checks
checker = HealthChecker()
result = checker.check_all()

# Check overall status
print(f"Overall Status: {result.overall_status}")

# Print summary
result.print_summary()

# Get JSON
json_output = result.to_json()

# Check specific component
backtest_result = checker.check_component("Backtest Engine")
print(f"Backtest Status: {backtest_result.status}")
```

## Exit Codes

The CLI returns exit codes based on overall status:
- `0` - GREEN (all systems operational)
- `1` - YELLOW (warnings present)
- `2` - RED (critical issues)
- `3` - Error (e.g., component not found)

This makes it suitable for use in CI/CD pipelines:

```bash
#!/bin/bash
make health-check
if [ $? -ne 0 ]; then
    echo "Health check failed!"
    exit 1
fi
```

## Configuration

Health checks can be configured in `config.toml`:

```toml
[health_checks]
enabled = true
interval_seconds = 60              # Interval for automated checks
alert_on_failure = true            # Raise alerts on failures

[health_checks.components]
backtest_engine = true
exchange_connectivity = true
portfolio_management = true
risk_management = true
live_trading = true
```

## Adding New Health Checks

To add a new health check component:

1. Create a new check class inheriting from `BaseHealthCheck`:

```python
from src.infra.health.checks.base_check import BaseHealthCheck, CheckResult, HealthStatus

class MyComponentCheck(BaseHealthCheck):
    def __init__(self):
        super().__init__("My Component")
    
    def check(self) -> CheckResult:
        start_time = self._measure_time()
        details = {}
        
        try:
            # Perform your health checks here
            # ...
            
            response_time = self._measure_time() - start_time
            
            return self._create_result(
                status=HealthStatus.GREEN,
                message="Component is operational",
                details=details,
                response_time_ms=response_time,
            )
        except Exception as e:
            return self._create_result(
                status=HealthStatus.RED,
                message=f"Health check failed: {e}",
                details=details,
            )
```

2. Add it to the HealthChecker in `health_checker.py`:

```python
def __init__(self):
    self.checks = [
        # ... existing checks ...
        MyComponentCheck(),
    ]
```

## Monitoring Integration

Health check results can be integrated with monitoring systems:

```python
import json
from src.infra.health import HealthChecker

checker = HealthChecker()
result = checker.check_all()

# Send to monitoring system
monitoring_data = result.to_dict()
# send_to_monitoring_system(monitoring_data)
```

## Best Practices

1. **Regular Checks** - Run health checks at regular intervals (e.g., every 60 seconds)
2. **Alert Integration** - Configure alerts for YELLOW and RED statuses
3. **CI/CD Integration** - Use health checks as gates in deployment pipelines
4. **Response Time Monitoring** - Track response times for each component
5. **Historical Tracking** - Store health check results for trend analysis

## Troubleshooting

### YELLOW Status

YELLOW status indicates warnings that should be investigated but don't prevent operation:
- Missing optional components
- Non-critical configuration issues
- Import warnings for optional dependencies

Action: Review the details in the health check output and address as needed.

### RED Status

RED status indicates critical issues that prevent component operation:
- Module import failures
- Missing required files or directories
- Critical configuration errors

Action: Investigate immediately and fix the underlying issue.

## Example Output

```
======================================================================
Peak Trade Health Check Summary
======================================================================
Timestamp: 2025-12-17 16:14:28

Overall Status: 🟢 GREEN

Components: 5 GREEN / 0 YELLOW / 0 RED

----------------------------------------------------------------------
Component Details:
----------------------------------------------------------------------

[🟢 GREEN] Backtest Engine
  Message: Backtest engine is operational
  Response Time: 415.35ms
  Details: {
    "engine_import": "OK",
    "results_dir": "/path/to/results",
    "results_dir_writable": true,
    "backtest_engine_class": "Available"
  }

...
```

## See Also

- [Circuit Breaker](CIRCUIT_BREAKER.md) - Failure handling patterns
- [Monitoring](MONITORING.md) - Comprehensive monitoring setup
- [Backup & Recovery](BACKUP_RECOVERY.md) - Data backup and recovery
