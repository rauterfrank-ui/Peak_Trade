# Monitoring Guide

## Overview

Peak Trade uses Prometheus for metrics collection, Grafana for visualization, and AlertManager for alert routing. This guide covers how to set up, configure, and use the monitoring stack.

## Quick Start

### Start the Monitoring Stack

```bash
# Start monitoring services
bash scripts/start_monitoring.sh
```

### Check Status

```bash
# Check if all services are running
python scripts/check_monitoring.py
```

## Access Dashboards

Once the monitoring stack is running, you can access:

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9091
- **AlertManager**: http://localhost:9093

## Available Dashboards

### 1. Peak Trade Overview

Located at: Grafana > Dashboards > Peak Trade - Overview

**Panels:**
- **Circuit Breaker Status**: Current state of all circuit breakers (0=CLOSED, 1=HALF_OPEN, 2=OPEN)
- **Request Latency (P95)**: 95th percentile of request durations
- **Cache Hit Rate**: Percentage of cache hits vs total cache operations
- **Orders per Second**: Order flow rate by status
- **P&L by Strategy**: Current profit/loss for each strategy
- **Health Check Status**: Health status of all registered services

### 2. System Metrics

Available through Node Exporter:
- CPU Usage
- Memory Usage
- Disk I/O
- Network Traffic

## Metrics Reference

### Resilience Metrics

- `peak_circuit_breaker_state{name}`: Circuit breaker state (0=closed, 1=half_open, 2=open)
- `peak_retry_attempts_total{operation}`: Total number of retry attempts
- `peak_health_check_status{service}`: Health check status (1=healthy, 0=unhealthy)

### Performance Metrics

- `peak_request_duration_seconds`: Histogram of request durations
- `peak_backtest_duration_seconds`: Histogram of backtest durations

### Trading Metrics

- `peak_orders_total{status,symbol}`: Total number of orders
- `peak_pnl_usd{strategy}`: Current P&L in USD
- `peak_position_size{symbol}`: Current position size

### Data Metrics

- `peak_cache_hits_total{level}`: Total cache hits
- `peak_cache_misses_total{level}`: Total cache misses
- `peak_api_calls_total{provider,status}`: Total API calls

### System Metrics

- `peak_cpu_usage_percent`: CPU usage percentage
- `peak_memory_usage_mb`: Memory usage in MB

## Alerts

Alerts are defined in `docker/prometheus/alerts/peak_trade.yml`.

### Active Alerts

1. **CircuitBreakerOpen**: Triggered when a circuit breaker is open for more than 1 minute
2. **ServiceUnhealthy**: Triggered when a health check fails for more than 2 minutes
3. **HighLatency**: Triggered when P95 latency exceeds 1 second for 5 minutes
4. **LowCacheHitRate**: Triggered when cache hit rate is below 50% for 10 minutes
5. **HighMemoryUsage**: Triggered when memory usage exceeds 2000 MB for 5 minutes

### Alert Configuration

Alerts are routed to Slack by default. To configure:

1. Edit `docker/alertmanager/alertmanager.yml`
2. Replace `YOUR_SLACK_WEBHOOK_URL` with your webhook URL
3. Restart the alertmanager service

## Using Metrics in Code

### Recording Custom Metrics

```python
from src.monitoring.prometheus_exporter import prometheus_exporter

# Record an order
prometheus_exporter.record_order("filled", "BTC/USD")

# Update P&L
prometheus_exporter.update_pnl("momentum_strategy", 1250.50)

# Update position
prometheus_exporter.update_position("BTC/USD", 0.5)

# Record API call
prometheus_exporter.record_api_call("kraken", "success")

# Record cache hit
prometheus_exporter.record_cache_hit("L1")
```

### Performance Monitoring

```python
from src.monitoring.middleware import monitor_performance

@monitor_performance("database_query")
def fetch_data():
    # Your operation
    pass
```

### Integration with Circuit Breaker

Circuit breaker state changes are automatically exported to Prometheus:

```python
from src.core.resilience import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=60,
    name="api_breaker"
)

@breaker.call
def call_api():
    # Your API call
    pass
```

### Integration with Health Checks

Health check results are automatically exported to Prometheus:

```python
from src.core.resilience import health_check

def check_database():
    # Check database connection
    return True, "Database is healthy"

health_check.register("database", check_database)
results = health_check.run_all()
```

## Starting the Metrics Exporter

To start the Prometheus metrics exporter in your application:

```python
from src.monitoring.prometheus_exporter import prometheus_exporter

# Start the metrics server
prometheus_exporter.start()
```

This will start an HTTP server on port 9090 (default) that Prometheus can scrape.

## Troubleshooting

### Services Not Starting

```bash
# Check Docker logs
docker-compose -f docker/docker-compose.monitoring.yml logs

# Check individual service
docker logs peak-prometheus
docker logs peak-grafana
docker logs peak-alertmanager
```

### Metrics Not Appearing

1. Check if the Prometheus exporter is running (port 9090)
2. Verify Prometheus is scraping the target:
   - Go to http://localhost:9091/targets
   - Check if 'peak-trade' target is UP
3. Check Prometheus logs for scraping errors

### Grafana Dashboard Not Loading

1. Verify Prometheus datasource is configured:
   - Grafana > Configuration > Data Sources
   - Should see 'Prometheus' as default
2. Check datasource connection:
   - Test the datasource connection
   - Should be able to reach http://prometheus:9090

### Alerts Not Firing

1. Check AlertManager configuration:
   - Edit `docker/alertmanager/alertmanager.yml`
   - Verify webhook URL is correct
2. Check Prometheus rules:
   - Go to http://localhost:9091/rules
   - Verify alert rules are loaded
3. Check AlertManager logs:
   - `docker logs peak-alertmanager`

## Stopping the Monitoring Stack

```bash
# Stop all monitoring services
cd docker
docker-compose -f docker-compose.monitoring.yml down

# Stop and remove volumes
docker-compose -f docker-compose.monitoring.yml down -v
```

## Advanced Configuration

### Custom Scrape Intervals

Edit `docker/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 10s  # Change from 15s to 10s
```

### Custom Alert Rules

Add new alert rules in `docker/prometheus/alerts/peak_trade.yml`:

```yaml
- alert: CustomAlert
  expr: your_metric > threshold
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Custom alert"
    description: "Alert description"
```

### Adding New Datasources

Create a new file in `docker/grafana/provisioning/datasources/`:

```yaml
apiVersion: 1
datasources:
  - name: MyDataSource
    type: influxdb
    url: http://influxdb:8086
```

## Production Considerations

1. **Security**: Change default Grafana password
2. **Persistence**: Ensure volumes are backed up
3. **Alerting**: Configure proper alert channels (Slack, PagerDuty, etc.)
4. **Scaling**: Consider remote storage for Prometheus in production
5. **High Availability**: Run multiple instances with federation
6. **Resource Limits**: Set appropriate memory/CPU limits for containers

## Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [AlertManager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
