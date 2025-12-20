"""
Prometheus Metrics Exporter for Peak Trade
==========================================
Exports metrics to Prometheus for monitoring and alerting.

Metrics Categories:
- System Metrics (CPU, Memory, Disk)
- Trading Metrics (Orders, Fills, P&L)
- Resilience Metrics (Circuit Breaker, Retries)
- Performance Metrics (Latencies, Throughput)
- Data Metrics (Cache Hits, API Calls)
"""

from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class PrometheusExporter:
    """
    Prometheus metrics exporter for Peak Trade.
    
    Metrics Categories:
    - System Metrics (CPU, Memory, Disk)
    - Trading Metrics (Orders, Fills, P&L)
    - Resilience Metrics (Circuit Breaker, Retries)
    - Performance Metrics (Latencies, Throughput)
    - Data Metrics (Cache Hits, API Calls)
    """
    
    def __init__(self, port: int = 9090, registry=None):
        """
        Initialize Prometheus exporter.
        
        Args:
            port: Port to expose metrics on (default: 9090)
            registry: Custom Prometheus registry (default: REGISTRY)
        """
        self.port = port
        self.registry = registry
        
        # System Metrics
        self.cpu_usage = Gauge('peak_cpu_usage_percent', 'CPU usage percentage', registry=registry)
        self.memory_usage = Gauge('peak_memory_usage_mb', 'Memory usage in MB', registry=registry)
        
        # Trading Metrics
        self.orders_total = Counter('peak_orders_total', 'Total orders', ['status', 'symbol'], registry=registry)
        self.pnl_gauge = Gauge('peak_pnl_usd', 'Current P&L in USD', ['strategy'], registry=registry)
        self.position_size = Gauge('peak_position_size', 'Current position size', ['symbol'], registry=registry)
        
        # Resilience Metrics
        self.circuit_breaker_state = Gauge(
            'peak_circuit_breaker_state',
            'Circuit breaker state (0=closed, 1=half_open, 2=open)',
            ['name'],
            registry=registry
        )
        self.retry_attempts = Counter('peak_retry_attempts_total', 'Retry attempts', ['operation'], registry=registry)
        self.health_check_status = Gauge(
            'peak_health_check_status',
            'Health check status (1=healthy, 0=unhealthy)',
            ['service'],
            registry=registry
        )
        
        # Performance Metrics
        self.request_duration = Histogram(
            'peak_request_duration_seconds',
            'Request duration',
            ['endpoint', 'method'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
            registry=registry
        )
        self.backtest_duration = Histogram(
            'peak_backtest_duration_seconds',
            'Backtest duration',
            ['strategy'],
            buckets=[1, 5, 10, 30, 60, 120, 300],
            registry=registry
        )
        
        # Data Metrics
        self.cache_hits = Counter('peak_cache_hits_total', 'Cache hits', ['level'], registry=registry)
        self.cache_misses = Counter('peak_cache_misses_total', 'Cache misses', ['level'], registry=registry)
        self.api_calls = Counter('peak_api_calls_total', 'API calls', ['provider', 'status'], registry=registry)
        
        # Custom Metrics
        self.custom_metrics: Dict[str, Any] = {}
        
        logger.info(f"PrometheusExporter initialized on port {port}")
    
    def start(self):
        """Start Prometheus HTTP server."""
        try:
            start_http_server(self.port)
            logger.info(f"✅ Prometheus exporter started on port {self.port}")
            print(f"✅ Prometheus exporter started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start Prometheus exporter: {e}")
            raise
    
    def record_order(self, status: str, symbol: str):
        """
        Record order metric.
        
        Args:
            status: Order status (e.g., 'filled', 'canceled', 'rejected')
            symbol: Trading symbol (e.g., 'BTC/USD')
        """
        self.orders_total.labels(status=status, symbol=symbol).inc()
    
    def update_pnl(self, strategy: str, pnl: float):
        """
        Update P&L gauge.
        
        Args:
            strategy: Strategy name
            pnl: Profit/Loss value in USD
        """
        self.pnl_gauge.labels(strategy=strategy).set(pnl)
    
    def update_position(self, symbol: str, size: float):
        """
        Update position size.
        
        Args:
            symbol: Trading symbol
            size: Position size
        """
        self.position_size.labels(symbol=symbol).set(size)
    
    def record_circuit_breaker_state(self, name: str, state: int):
        """
        Record circuit breaker state.
        
        Args:
            name: Circuit breaker name
            state: State value (0=closed, 1=half_open, 2=open)
        """
        self.circuit_breaker_state.labels(name=name).set(state)
    
    def record_health_check(self, service: str, healthy: bool):
        """
        Record health check result.
        
        Args:
            service: Service name
            healthy: Whether the service is healthy
        """
        self.health_check_status.labels(service=service).set(1 if healthy else 0)
    
    def record_retry(self, operation: str):
        """
        Record retry attempt.
        
        Args:
            operation: Operation name
        """
        self.retry_attempts.labels(operation=operation).inc()
    
    def record_request(self, endpoint: str, method: str, duration_seconds: float):
        """
        Record request duration.
        
        Args:
            endpoint: API endpoint
            method: Request method or status (e.g., 'success', 'error')
            duration_seconds: Duration in seconds
        """
        self.request_duration.labels(endpoint=endpoint, method=method).observe(duration_seconds)
    
    def record_backtest(self, strategy: str, duration_seconds: float):
        """
        Record backtest duration.
        
        Args:
            strategy: Strategy name
            duration_seconds: Duration in seconds
        """
        self.backtest_duration.labels(strategy=strategy).observe(duration_seconds)
    
    def record_cache_hit(self, level: str):
        """
        Record cache hit.
        
        Args:
            level: Cache level (e.g., 'L1', 'L2')
        """
        self.cache_hits.labels(level=level).inc()
    
    def record_cache_miss(self, level: str):
        """
        Record cache miss.
        
        Args:
            level: Cache level (e.g., 'L1', 'L2')
        """
        self.cache_misses.labels(level=level).inc()
    
    def record_api_call(self, provider: str, status: str):
        """
        Record API call.
        
        Args:
            provider: API provider name (e.g., 'kraken', 'binance')
            status: Call status (e.g., 'success', 'error')
        """
        self.api_calls.labels(provider=provider, status=status).inc()
    
    def update_system_metrics(self, cpu_percent: float, memory_mb: float):
        """
        Update system resource metrics.
        
        Args:
            cpu_percent: CPU usage percentage
            memory_mb: Memory usage in MB
        """
        self.cpu_usage.set(cpu_percent)
        self.memory_usage.set(memory_mb)


# Global instance
prometheus_exporter = PrometheusExporter()
