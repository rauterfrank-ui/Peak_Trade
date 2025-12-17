# Monitoring & Logging

## Überblick

Das Monitoring-System bietet strukturiertes Logging, Performance-Metriken und ein Alert-System für Peak_Trade.

## Features

- **Strukturiertes JSON-Logging**: Machine-readable Logs
- **Performance-Metriken**: Latency, Throughput, Error-Rate
- **Alert-System**: Konfigurierbare Schwellwerte
- **Apple Silicon optimiert**: Efficient und performant

## Strukturiertes Logging

### Setup

```python
from src.infra.monitoring import setup_structured_logging

# Plain Text für Development
setup_structured_logging(level="INFO", json_format=False)

# JSON für Production
setup_structured_logging(
    level="INFO",
    json_format=True,
    log_file="logs/peak_trade.log"
)
```

### Verwendung

```python
from src.infra.monitoring import get_logger

logger = get_logger(__name__)

logger.info("Starting backtest", extra={"strategy": "ma_crossover"})
logger.warning("High volatility detected", extra={"vol": 0.45})
logger.error("API call failed", extra={"exchange": "kraken"})
```

### JSON-Format

```json
{
  "timestamp": "2025-12-17T21:45:00.123456",
  "level": "INFO",
  "logger": "src.backtest.engine",
  "message": "Starting backtest",
  "module": "engine",
  "function": "run_backtest",
  "line": 42,
  "strategy": "ma_crossover"
}
```

### Log-Levels

- **DEBUG**: Detaillierte Debug-Informationen
- **INFO**: Normale Operationen
- **WARNING**: Warnungen
- **ERROR**: Fehler
- **CRITICAL**: Kritische Fehler

## Performance-Metriken

### Metriken sammeln

```python
from src.infra.monitoring import get_metrics_collector

metrics = get_metrics_collector()

# Counter
metrics.increment("api_calls")
metrics.increment("api_errors")

# Gauge
metrics.set_gauge("queue_size", 42)
metrics.set_gauge("open_positions", 3)

# Timer (mit Context Manager)
with metrics.timer("backtest_duration"):
    result = run_backtest()

# Timer (manuell)
start = time.time()
result = run_backtest()
duration = time.time() - start
metrics.record_time("backtest_duration", duration)
```

### Metriken auslesen

```python
metrics = get_metrics_collector()
data = metrics.get_metrics()

print(f"API Calls: {data['counters']['api_calls']}")
print(f"Queue Size: {data['gauges']['queue_size']}")

# Timer-Statistiken
backtest_stats = data['timers']['backtest_duration']
print(f"Mean: {backtest_stats['mean']:.2f}s")
print(f"P95: {backtest_stats['p95']:.2f}s")
print(f"P99: {backtest_stats['p99']:.2f}s")
```

### Metriken-Types

1. **Counter**: Zähler (nur erhöhen/verringern)
   - API-Calls, Errors, Trades

2. **Gauge**: Aktueller Wert (beliebig setzen)
   - Queue-Size, Open-Positions, Memory-Usage

3. **Timer**: Zeitdauern mit Statistiken
   - Backtest-Duration, API-Latency, DB-Queries

## Alert-System

### Konfiguration

```python
from src.infra.monitoring import (
    get_alert_manager,
    AlertThreshold,
    AlertLevel,
)

alert_manager = get_alert_manager()

# Schwellwerte definieren
alert_manager.add_threshold(AlertThreshold(
    metric_name="error_rate",
    threshold=0.05,  # 5%
    level=AlertLevel.WARNING,
    comparison=">",
    message_template="Error rate too high: {value:.2%}"
))

alert_manager.add_threshold(AlertThreshold(
    metric_name="response_time",
    threshold=1.0,  # 1 Sekunde
    level=AlertLevel.ERROR,
    comparison=">",
    message_template="Response time too slow: {value:.2f}s"
))
```

### Metriken prüfen

```python
# Prüfe Metrik
alerts = alert_manager.check_metric("error_rate", 0.08)

if alerts:
    for alert in alerts:
        print(f"[{alert.level.upper()}] {alert.message}")
```

### Alert-Handler

```python
def log_alert(alert):
    logger.warning(f"Alert: {alert.message}", extra=alert.details)

def send_email_alert(alert):
    if alert.level == AlertLevel.CRITICAL:
        send_email(subject=alert.message, body=str(alert.details))

alert_manager.add_handler(log_alert)
alert_manager.add_handler(send_email_alert)
```

## Integration in Code

### Backtest-Monitoring

```python
from src.infra.monitoring import get_logger, get_metrics_collector

logger = get_logger("backtest")
metrics = get_metrics_collector()

def run_backtest(strategy, data):
    logger.info("Starting backtest", extra={"strategy": strategy.name})
    metrics.increment("backtests_started")
    
    with metrics.timer("backtest_duration"):
        try:
            result = backtest_engine.run(strategy, data)
            metrics.increment("backtests_completed")
            logger.info(
                "Backtest completed",
                extra={
                    "sharpe": result.sharpe_ratio,
                    "return": result.total_return,
                }
            )
            return result
        except Exception as e:
            metrics.increment("backtests_failed")
            logger.error(f"Backtest failed: {e}")
            raise
```

### Exchange-API-Monitoring

```python
from src.infra.monitoring import get_logger, get_metrics_collector

logger = get_logger("exchange")
metrics = get_metrics_collector()

async def fetch_ohlcv(exchange, symbol):
    logger.debug(f"Fetching OHLCV", extra={"exchange": exchange, "symbol": symbol})
    metrics.increment(f"api_calls_{exchange}")
    
    with metrics.timer(f"api_latency_{exchange}"):
        try:
            result = await exchange_client.fetch_ohlcv(symbol)
            metrics.increment(f"api_success_{exchange}")
            return result
        except Exception as e:
            metrics.increment(f"api_errors_{exchange}")
            logger.error(
                f"API call failed",
                extra={"exchange": exchange, "symbol": symbol, "error": str(e)}
            )
            raise
```

## Konfiguration

In `config.toml`:

```toml
[monitoring]
log_level = "INFO"
structured_logging = true
metrics_enabled = true
log_format = "json"
```

### Config laden

```python
from src.core import load_config
from src.infra.monitoring import setup_structured_logging

cfg = load_config()

if hasattr(cfg, "monitoring"):
    setup_structured_logging(
        level=cfg.monitoring.log_level,
        json_format=(cfg.monitoring.log_format == "json"),
    )
```

## Dashboard-Integration

### Metriken-Export

```python
import json
from src.infra.monitoring import get_metrics_collector

metrics = get_metrics_collector()
data = metrics.get_metrics()

# Export als JSON
with open("metrics.json", "w") as f:
    json.dump(data, f, indent=2)
```

### Log-Aggregation

```bash
# Parse JSON-Logs
cat logs/peak_trade.log | jq '.level' | sort | uniq -c

# Fehler-Rate berechnen
cat logs/peak_trade.log | jq 'select(.level=="ERROR")' | wc -l
```

### Grafana/Prometheus

Metriken können an Prometheus exportiert werden:

```python
# Beispiel: Prometheus-Export (nicht implementiert)
from prometheus_client import Counter, Histogram

api_calls = Counter("api_calls_total", "Total API calls")
api_duration = Histogram("api_duration_seconds", "API call duration")
```

## Best Practices

1. **Strukturierte Logs**: Verwende JSON für Production
2. **Konsistente Keys**: Standardisiere extra-fields
3. **Nicht zu viel loggen**: DEBUG nur für Development
4. **Metriken aggregieren**: Timer statt einzelne Logs
5. **Alerts konfigurieren**: Für kritische Metriken

### Anti-Patterns

❌ **Nicht:**
```python
logger.info(f"Backtest result: sharpe={sharpe}, return={ret}")
```

✅ **Besser:**
```python
logger.info("Backtest completed", extra={"sharpe": sharpe, "return": ret})
```

## Troubleshooting

### Logs nicht sichtbar

- Prüfe Log-Level: `setup_structured_logging(level="DEBUG")`
- Prüfe Handler: `logging.getLogger().handlers`

### Metriken verloren

- Global Collector verwenden: `get_metrics_collector()`
- Nicht `MetricsCollector()` direkt instanziieren

### Performance-Probleme

- Timer nur für kritische Paths
- Metriken in Production aggregieren
- JSON-Logging nur für Production

## Siehe auch

- [Health Checks](HEALTH_CHECKS.md)
- [Circuit Breaker](CIRCUIT_BREAKER.md)
- [Backup & Recovery](BACKUP_RECOVERY.md)
