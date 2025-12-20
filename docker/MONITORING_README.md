# Peak Trade Monitoring Dashboard

Complete monitoring infrastructure with Prometheus + Grafana for real-time metrics, alerts, and visualization.

## 🚀 Quick Start

### 1. Start the Monitoring Stack

```bash
# Start Prometheus, Grafana, AlertManager, and Node Exporter
bash scripts/start_monitoring.sh
```

### 2. Access Dashboards

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9091
- **AlertManager**: http://localhost:9093

### 3. Check Status

```bash
# Verify all services are running
python scripts/check_monitoring.py
```

## 📊 Features

### Metrics Categories

- **System Metrics**: CPU, Memory usage
- **Trading Metrics**: Orders, P&L, Positions
- **Resilience Metrics**: Circuit Breaker states, Health checks, Retries
- **Performance Metrics**: Request latencies, Backtest durations
- **Data Metrics**: Cache hit/miss rates, API calls

### Built-in Alerts

- **CircuitBreakerOpen**: Critical alert when circuit breaker opens
- **ServiceUnhealthy**: Warning when health checks fail
- **HighLatency**: Performance degradation detection
- **LowCacheHitRate**: Cache efficiency monitoring
- **HighMemoryUsage**: Resource usage alerts

### Grafana Dashboards

- **Peak Trade Overview**: Main dashboard with all key metrics
  - Circuit Breaker Status
  - Request Latency (P95)
  - Cache Hit Rate
  - Orders per Second
  - P&L by Strategy
  - Health Check Status

## 💻 Usage

### Basic Integration

```python
from src.monitoring.prometheus_exporter import prometheus_exporter

# Start the metrics exporter
prometheus_exporter.start()
```

### Performance Monitoring

```python
from src.monitoring.middleware import monitor_performance

@monitor_performance("database_query")
def fetch_data():
    # Your operation
    pass
```

### Recording Metrics

```python
# Record orders
prometheus_exporter.record_order("filled", "BTC/USD")

# Update P&L
prometheus_exporter.update_pnl("momentum_strategy", 1250.50)

# Update positions
prometheus_exporter.update_position("BTC/USD", 0.5)

# Record cache operations
prometheus_exporter.record_cache_hit("L1")

# Record API calls
prometheus_exporter.record_api_call("kraken", "success")
```

### Circuit Breaker Integration

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

### Health Check Integration

Health check results are automatically exported to Prometheus:

```python
from src.core.resilience import health_check

def check_database():
    return True, "Database is healthy"

health_check.register("database", check_database)
health_check.run_all()
```

## 🧪 Testing

```bash
# Run all monitoring tests
python -m pytest tests/test_prometheus_exporter.py -v
python -m pytest tests/test_monitoring_middleware.py -v
python -m pytest tests/test_monitoring_integration.py -v

# Run example
PYTHONPATH=. python examples/monitoring_example.py
```

## 📁 Project Structure

```
.
├── docker/
│   ├── prometheus/
│   │   ├── prometheus.yml              # Prometheus configuration
│   │   └── alerts/
│   │       └── peak_trade.yml         # Alert rules
│   ├── grafana/
│   │   ├── provisioning/
│   │   │   └── datasources/
│   │   │       └── prometheus.yml     # Datasource config
│   │   └── dashboards/
│   │       └── peak_trade_overview.json
│   ├── alertmanager/
│   │   └── alertmanager.yml           # Alert routing config
│   └── docker-compose.monitoring.yml  # Complete stack
│
├── src/monitoring/
│   ├── __init__.py
│   ├── prometheus_exporter.py         # Metrics exporter
│   └── middleware.py                  # Performance decorators
│
├── scripts/
│   ├── start_monitoring.sh            # Start stack
│   └── check_monitoring.py            # Health check
│
├── docs/
│   └── monitoring_guide.md            # Complete guide
│
├── tests/
│   ├── test_prometheus_exporter.py
│   ├── test_monitoring_middleware.py
│   └── test_monitoring_integration.py
│
└── examples/
    └── monitoring_example.py          # Usage example
```

## 🔧 Configuration

### Prometheus Scrape Interval

Edit `docker/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s  # Adjust as needed
```

### Alert Rules

Add custom rules in `docker/prometheus/alerts/peak_trade.yml`:

```yaml
- alert: CustomAlert
  expr: your_metric > threshold
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Alert summary"
    description: "Alert description"
```

### Slack Notifications

Edit `docker/alertmanager/alertmanager.yml`:

```yaml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#peak-trade-alerts'
```

## 🛑 Stopping the Stack

```bash
cd docker
docker-compose -f docker-compose.monitoring.yml down

# Remove volumes
docker-compose -f docker-compose.monitoring.yml down -v
```

## 📚 Documentation

For detailed documentation, see:
- [Monitoring Guide](docs/monitoring_guide.md)
- [Example Script](examples/monitoring_example.py)

## ✅ Acceptance Criteria

- [x] Prometheus exporter implemented
- [x] Grafana Dashboards created
- [x] Alert Rules configured
- [x] Docker Compose Setup
- [x] Integration with Circuit Breaker, Health Checks
- [x] Management Scripts
- [x] Documentation complete
- [x] Tests for Monitoring (21/21 passing)

## 🎯 Production Ready

This monitoring stack is production-ready with:
- Automatic metric collection from resilience patterns
- Real-time alerting
- Professional dashboards
- Easy Docker deployment
- Comprehensive testing
- Full documentation
