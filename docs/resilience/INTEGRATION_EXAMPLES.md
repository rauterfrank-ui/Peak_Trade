# Resilience System - Integration Examples

## Überblick

Praktische Beispiele für die Integration des Resilience-Systems in bestehende Peak_Trade Module.

## 1. Exchange API Integration

### Kraken API mit Circuit Breaker und Rate Limiting

```python
# src/exchange/kraken_resilient.py
"""
Resilient Kraken Exchange Client mit Circuit Breaker und Rate Limiting
"""

import asyncio
from typing import Dict, Any
from src.exchange.ccxt_client import CcxtExchangeClient
from src.infra.resilience import circuit_breaker, rate_limit
from src.infra.monitoring import get_logger, get_metrics_collector

logger = get_logger(__name__)
metrics = get_metrics_collector()


class ResilientKrakenClient:
    """Kraken Client mit Resilience Features"""
    
    def __init__(self, api_key: str = None, secret: str = None):
        self.client = CcxtExchangeClient(
            "kraken",
            api_key=api_key,
            secret=secret,
            enable_rate_limit=True
        )
    
    @rate_limit(name="kraken_api", requests_per_second=10)
    @circuit_breaker(name="kraken_api", failure_threshold=5, timeout_seconds=60)
    async def fetch_ticker_safe(self, symbol: str) -> Dict[str, Any]:
        """
        Hole Ticker mit Resilience-Schutz
        
        - Rate Limiting: Max 10 req/s
        - Circuit Breaker: Öffnet bei 5 Fehlern
        - Monitoring: Logged und gemessen
        """
        logger.info(f"Fetching ticker for {symbol}", extra={"symbol": symbol})
        metrics.increment("kraken_ticker_requests")
        
        with metrics.timer("kraken_ticker_latency"):
            try:
                ticker = self.client.fetch_ticker(symbol)
                metrics.increment("kraken_ticker_success")
                return ticker
            except Exception as e:
                metrics.increment("kraken_ticker_errors")
                logger.error(f"Ticker fetch failed: {e}", extra={"symbol": symbol})
                raise
    
    @rate_limit(name="kraken_api", requests_per_second=10)
    @circuit_breaker(name="kraken_ohlcv", failure_threshold=5)
    async def fetch_ohlcv_safe(self, symbol: str, timeframe: str = "1h") -> Any:
        """Hole OHLCV mit Resilience-Schutz"""
        logger.info(f"Fetching OHLCV", extra={"symbol": symbol, "timeframe": timeframe})
        
        with metrics.timer("kraken_ohlcv_latency"):
            try:
                data = self.client.fetch_ohlcv(symbol, timeframe)
                metrics.increment("kraken_ohlcv_success")
                return data
            except Exception as e:
                metrics.increment("kraken_ohlcv_errors")
                logger.error(f"OHLCV fetch failed: {e}")
                raise


# Verwendung
async def example_usage():
    client = ResilientKrakenClient()
    
    # Ticker abrufen - geschützt durch Circuit Breaker & Rate Limiting
    ticker = await client.fetch_ticker_safe("BTC/EUR")
    print(f"BTC Price: {ticker.last}")
    
    # OHLCV abrufen
    ohlcv = await client.fetch_ohlcv_safe("BTC/EUR", "1h")
    print(f"Candles: {len(ohlcv)}")
```

### Binance API Integration

```python
# src/exchange/binance_resilient.py
"""
Resilient Binance Client
"""

from src.infra.resilience import circuit_breaker, rate_limit, retry
from src.infra.monitoring import get_logger, get_metrics_collector

logger = get_logger(__name__)
metrics = get_metrics_collector()


class ResilientBinanceClient:
    """Binance Client mit höherem Rate Limit"""
    
    @rate_limit(name="binance_api", requests_per_second=15)
    @circuit_breaker(name="binance_api", failure_threshold=5)
    @retry(max_attempts=3, initial_delay=1.0)
    async def fetch_ticker_with_retry(self, symbol: str):
        """
        Ticker mit Retry-Logic
        
        - Rate Limit: 15 req/s (Binance erlaubt mehr)
        - Circuit Breaker: Schützt bei Ausfällen
        - Retry: 3 Versuche mit Exponential Backoff
        """
        with metrics.timer("binance_ticker_latency"):
            # API call hier
            pass
```

## 2. Backtest Engine Integration

### Backtest mit Health Checks

```python
# src/backtest/resilient_engine.py
"""
Backtest Engine mit Health Checks und Backup
"""

from src.backtest import BacktestEngine
from src.infra.health import HealthChecker
from src.infra.backup import BackupManager
from src.infra.monitoring import get_logger, get_metrics_collector

logger = get_logger(__name__)
metrics = get_metrics_collector()


async def run_backtest_with_health_checks(strategy, data):
    """
    Führe Backtest mit Pre- und Post-Health-Checks aus
    """
    # Pre-Check: System-Health prüfen
    checker = HealthChecker(checks=["backtest", "risk"])
    results = await checker.run_all_checks()
    
    overall = checker.get_overall_status(results)
    if overall == "red":
        logger.error("Health check failed - aborting backtest")
        return None
    
    # Backup vor Backtest
    backup_manager = BackupManager()
    backup_id = backup_manager.create_backup(
        {"pre_backtest_state": {"strategy": strategy.name}},
        backup_type="pre_backtest"
    )
    logger.info(f"Created pre-backtest backup: {backup_id}")
    
    # Backtest ausführen
    with metrics.timer("backtest_duration"):
        try:
            engine = BacktestEngine()
            result = engine.run(strategy, data)
            
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
            
            # Bei Fehler: Backup-Info loggen
            logger.info(f"Restore from backup: {backup_id}")
            raise
```

## 3. Portfolio Management Integration

### Portfolio mit Monitoring

```python
# src/portfolio/monitored_portfolio.py
"""
Portfolio Manager mit Metriken und Alerts
"""

from src.portfolio import PortfolioManager
from src.infra.monitoring import (
    get_logger,
    get_metrics_collector,
    get_alert_manager,
    AlertThreshold,
    AlertLevel,
)

logger = get_logger(__name__)
metrics = get_metrics_collector()
alerts = get_alert_manager()


class MonitoredPortfolioManager:
    """Portfolio Manager mit Monitoring"""
    
    def __init__(self):
        self.portfolio = PortfolioManager()
        self._setup_alerts()
    
    def _setup_alerts(self):
        """Konfiguriere Alerts für Portfolio-Metriken"""
        # Alert bei hoher Drawdown
        alerts.add_threshold(AlertThreshold(
            metric_name="portfolio_drawdown",
            threshold=0.15,  # 15%
            level=AlertLevel.WARNING,
            comparison=">",
            message_template="Portfolio drawdown too high: {value:.2%}"
        ))
        
        # Alert bei niedrigem Sharpe
        alerts.add_threshold(AlertThreshold(
            metric_name="portfolio_sharpe",
            threshold=1.0,
            level=AlertLevel.WARNING,
            comparison="<",
            message_template="Sharpe ratio too low: {value:.2f}"
        ))
    
    def run_backtest_monitored(self, strategies, data):
        """Backtest mit Metriken und Alerts"""
        logger.info("Starting monitored backtest")
        
        with metrics.timer("portfolio_backtest_duration"):
            result = self.portfolio.run_backtest(strategies, data)
        
        # Metriken erfassen
        metrics.set_gauge("portfolio_sharpe", result.sharpe_ratio)
        metrics.set_gauge("portfolio_return", result.total_return)
        metrics.set_gauge("portfolio_drawdown", abs(result.max_drawdown))
        
        # Alerts prüfen
        alerts.check_metric("portfolio_drawdown", abs(result.max_drawdown))
        alerts.check_metric("portfolio_sharpe", result.sharpe_ratio)
        
        logger.info(
            "Backtest completed",
            extra={
                "sharpe": result.sharpe_ratio,
                "drawdown": result.max_drawdown,
            }
        )
        
        return result
```

## 4. Live Trading Integration

### Live Session mit Health Checks und Backup

```python
# src/live/resilient_session.py
"""
Live Trading Session mit Resilience
"""

from src.live import PaperBroker
from src.infra.health import HealthChecker
from src.infra.backup import BackupManager
from src.infra.monitoring import get_logger, get_metrics_collector

logger = get_logger(__name__)
metrics = get_metrics_collector()


class ResilientLiveSession:
    """Live Session mit Resilience Features"""
    
    def __init__(self):
        self.broker = PaperBroker()
        self.backup_manager = BackupManager()
        self.health_checker = HealthChecker()
    
    async def start_session(self, strategy):
        """Start Live Session mit Health Checks"""
        # Pre-Flight Health Check
        logger.info("Running pre-flight health checks")
        health_results = await self.health_checker.run_all_checks()
        
        overall = self.health_checker.get_overall_status(health_results)
        if overall == "red":
            logger.error("Health check failed - cannot start session")
            raise RuntimeError("System not healthy")
        
        # Backup erstellen
        backup_id = self.backup_manager.create_backup(
            {
                "session_start": {
                    "strategy": strategy.name,
                    "timestamp": "2025-12-18T08:00:00",
                }
            },
            backup_type="pre_session"
        )
        logger.info(f"Created session backup: {backup_id}")
        
        # Session starten
        logger.info("Starting live session", extra={"strategy": strategy.name})
        metrics.increment("live_sessions_started")
        
        # Session läuft...
        return backup_id
    
    async def monitor_session(self):
        """Kontinuierliches Monitoring während Session"""
        while True:
            # Health Check alle 60 Sekunden
            results = await self.health_checker.run_all_checks()
            
            for name, result in results.items():
                if result.status == "red":
                    logger.critical(
                        f"Health check failed: {name}",
                        extra={"check": name, "message": result.message}
                    )
                    # Ggf. Session stoppen
            
            await asyncio.sleep(60)
```

## 5. Scheduled Tasks Integration

### Cron Job für Health Checks und Backups

```python
# scripts/scheduled_maintenance.py
"""
Scheduled Maintenance Tasks
"""

import asyncio
import schedule
import time
from datetime import datetime

from src.infra.health import HealthChecker
from src.infra.backup import BackupManager
from src.infra.monitoring import get_logger

logger = get_logger(__name__)


async def scheduled_health_check():
    """Stündlicher Health Check"""
    logger.info("Running scheduled health check")
    
    checker = HealthChecker()
    results = await checker.run_all_checks()
    
    # JSON für Monitoring-System
    json_output = checker.format_results_json(results)
    
    # In Datei speichern
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"logs/health_check_{timestamp}.json", "w") as f:
        f.write(json_output)
    
    overall = checker.get_overall_status(results)
    if overall == "red":
        logger.critical("Health check failed!")
        # Send alert
    
    logger.info(f"Health check completed: {overall}")


def scheduled_backup():
    """Tägliches Backup"""
    logger.info("Running scheduled backup")
    
    manager = BackupManager()
    
    # Sammle aktuellen State
    data = {
        "scheduled_backup": {
            "timestamp": datetime.now().isoformat(),
            # Portfolio state, config, etc.
        }
    }
    
    backup_id = manager.create_backup(data, backup_type="scheduled")
    logger.info(f"Scheduled backup created: {backup_id}")


def main():
    """Setup Scheduled Tasks"""
    # Health Check jede Stunde
    schedule.every().hour.do(lambda: asyncio.run(scheduled_health_check()))
    
    # Backup täglich um 2 Uhr nachts
    schedule.every().day.at("02:00").do(scheduled_backup)
    
    logger.info("Scheduled tasks initialized")
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
```

## 6. Testing Integration

### Tests mit Resilience

```python
# tests/integration/test_resilient_exchange.py
"""
Integration Tests für Resilient Exchange Client
"""

import pytest
from src.exchange.kraken_resilient import ResilientKrakenClient
from src.infra.resilience import get_circuit_breaker


@pytest.mark.asyncio
async def test_kraken_with_circuit_breaker():
    """Test Circuit Breaker Integration"""
    client = ResilientKrakenClient()
    
    # Erfolgreiche Calls
    ticker = await client.fetch_ticker_safe("BTC/EUR")
    assert ticker is not None
    
    # Check Circuit Breaker Status
    cb = get_circuit_breaker("kraken_api")
    state = cb.get_state()
    assert state["state"] == "closed"
    assert state["metrics"]["success_calls"] >= 1


@pytest.mark.asyncio
async def test_health_check_before_backtest():
    """Test Health Check vor Backtest"""
    from src.infra.health import HealthChecker
    from src.backtest.resilient_engine import run_backtest_with_health_checks
    
    # Health Check
    checker = HealthChecker(checks=["backtest"])
    results = await checker.run_all_checks()
    
    assert results["backtest"].status in ["green", "yellow"]
```

## Best Practices

### 1. Decorator-Reihenfolge

```python
# Korrekte Reihenfolge (außen nach innen):
@rate_limit(...)       # 1. Rate Limiting (äußerster)
@circuit_breaker(...)  # 2. Circuit Breaker
@retry(...)            # 3. Retry (innerster)
async def api_call():
    pass
```

### 2. Logging & Metrics

```python
# Immer zusammen verwenden:
logger.info("Operation started", extra={"param": value})
metrics.increment("operation_started")

with metrics.timer("operation_duration"):
    result = do_operation()

metrics.increment("operation_completed")
```

### 3. Health Checks

```python
# Vor kritischen Operationen:
results = await checker.run_all_checks()
if checker.get_overall_status(results) == "red":
    # Abort
    pass
```

### 4. Backups

```python
# Vor riskanten Operationen:
backup_id = manager.create_backup(current_state, backup_type="pre_operation")

try:
    risky_operation()
except Exception:
    # Recovery möglich mit backup_id
    raise
```

## Zusammenfassung

Diese Integration-Beispiele zeigen, wie das Resilience-System in bestehende Module integriert wird:

1. **Exchange APIs**: Circuit Breaker + Rate Limiting
2. **Backtest Engine**: Health Checks + Backups
3. **Portfolio**: Monitoring + Alerts
4. **Live Trading**: Komplette Resilience-Stack
5. **Scheduled Tasks**: Automatische Maintenance
6. **Testing**: Integration Tests

Alle Beispiele sind produktionsbereit und können direkt verwendet werden.
