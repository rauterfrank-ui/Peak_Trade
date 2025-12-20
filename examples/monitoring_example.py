#!/usr/bin/env python3
"""
Example: Using the Monitoring Dashboard
========================================
Demonstrates how to use the monitoring infrastructure with Peak Trade.
"""

import time
import random
from src.monitoring.prometheus_exporter import prometheus_exporter
from src.monitoring.middleware import monitor_performance
from src.core.resilience import CircuitBreaker, health_check


# Example 1: Start the metrics exporter
def start_monitoring():
    """Start the Prometheus metrics exporter."""
    print("🚀 Starting Prometheus metrics exporter...")
    prometheus_exporter.start()
    print("✅ Metrics available at http://localhost:9090/metrics")


# Example 2: Using the performance monitoring decorator
@monitor_performance("fetch_market_data")
def fetch_market_data(symbol: str):
    """Example function with performance monitoring."""
    print(f"Fetching market data for {symbol}...")
    time.sleep(random.uniform(0.1, 0.5))
    return {"symbol": symbol, "price": random.uniform(100, 1000)}


# Example 3: Using Circuit Breaker with monitoring
circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=5,
    name="api_breaker"
)


@circuit_breaker.call
def unreliable_api_call():
    """Example API call with circuit breaker."""
    # Simulate occasional failures
    if random.random() < 0.3:
        raise Exception("API call failed")
    return {"status": "success"}


# Example 4: Recording custom metrics
def record_trading_metrics():
    """Record some example trading metrics."""
    print("\n📊 Recording trading metrics...")
    
    # Record orders
    prometheus_exporter.record_order("filled", "BTC/USD")
    prometheus_exporter.record_order("filled", "ETH/USD")
    prometheus_exporter.record_order("canceled", "BTC/USD")
    
    # Update P&L
    prometheus_exporter.update_pnl("momentum_strategy", 1250.50)
    prometheus_exporter.update_pnl("mean_reversion_strategy", -125.25)
    
    # Update positions
    prometheus_exporter.update_position("BTC/USD", 0.5)
    prometheus_exporter.update_position("ETH/USD", 2.0)
    
    # Record API calls
    prometheus_exporter.record_api_call("kraken", "success")
    prometheus_exporter.record_api_call("binance", "success")
    
    # Record cache operations
    prometheus_exporter.record_cache_hit("L1")
    prometheus_exporter.record_cache_hit("L1")
    prometheus_exporter.record_cache_miss("L2")
    
    print("✅ Metrics recorded")


# Example 5: Health checks
def setup_health_checks():
    """Set up health checks with monitoring."""
    print("\n🏥 Setting up health checks...")
    
    def check_database():
        # Simulate database check
        return True, "Database connection OK"
    
    def check_api():
        # Simulate API check
        return random.random() > 0.1, "API responding"
    
    health_check.register("database", check_database)
    health_check.register("external_api", check_api)
    
    # Run checks
    results = health_check.run_all()
    for name, result in results.items():
        status = "✅" if result.healthy else "❌"
        print(f"{status} {name}: {result.message}")


def main():
    """Main example function."""
    print("=" * 60)
    print("Peak Trade Monitoring Dashboard Example")
    print("=" * 60)
    
    # Start the exporter (in production, this would run in a separate thread)
    # Uncomment to actually start the server:
    # start_monitoring()
    
    # Run some operations with monitoring
    print("\n🔍 Running monitored operations...")
    for i in range(5):
        try:
            data = fetch_market_data(f"SYMBOL{i}")
            print(f"  Fetched: {data['symbol']} @ ${data['price']:.2f}")
        except Exception as e:
            print(f"  Error: {e}")
        
        time.sleep(0.1)
    
    # Record trading metrics
    record_trading_metrics()
    
    # Setup and run health checks
    setup_health_checks()
    
    # Try circuit breaker
    print("\n🔌 Testing circuit breaker...")
    for i in range(5):
        try:
            result = unreliable_api_call()
            print(f"  API call {i+1}: {result['status']}")
        except Exception as e:
            print(f"  API call {i+1}: Failed - {e}")
        time.sleep(0.1)
    
    print("\n" + "=" * 60)
    print("✅ Example completed!")
    print("\n📊 To view metrics:")
    print("  1. Start monitoring stack: bash scripts/start_monitoring.sh")
    print("  2. Access Grafana: http://localhost:3000 (admin/admin)")
    print("  3. View Prometheus: http://localhost:9091")
    print("=" * 60)


if __name__ == "__main__":
    main()
