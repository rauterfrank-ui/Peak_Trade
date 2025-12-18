#!/usr/bin/env python
"""
Resilience System Integration Demo

Demonstriert die Integration des Resilience-Systems in Peak_Trade.
Zeigt Circuit Breaker, Rate Limiting, Monitoring und Backups in Aktion.

Usage:
    python scripts/demo_resilience_integration.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infra.health import HealthChecker, HealthStatus
from src.infra.resilience import (
    circuit_breaker,
    rate_limit,
    get_circuit_breaker,
    get_rate_limiter,
)
from src.infra.monitoring import (
    get_logger,
    get_metrics_collector,
    setup_structured_logging,
)
from src.infra.backup import BackupManager


# Setup Logging
setup_structured_logging(level="INFO", json_format=False)
logger = get_logger(__name__)
metrics = get_metrics_collector()


# Demo: Exchange API mit Resilience
class DemoExchangeClient:
    """Demo Exchange Client mit Resilience Features"""
    
    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name
        self._call_count = 0
    
    @rate_limit(name="demo_exchange", requests_per_second=5)
    @circuit_breaker(name="demo_exchange", failure_threshold=3, timeout_seconds=5)
    async def fetch_ticker(self, symbol: str):
        """Simuliere API Call mit Resilience"""
        self._call_count += 1
        logger.info(
            f"Fetching ticker #{self._call_count}",
            extra={"exchange": self.exchange_name, "symbol": symbol}
        )
        metrics.increment("ticker_requests")
        
        # Simuliere gelegentliche Fehler
        if self._call_count % 4 == 0:
            metrics.increment("ticker_errors")
            raise Exception("Simulated API error")
        
        # Erfolgreicher Call
        metrics.increment("ticker_success")
        await asyncio.sleep(0.1)  # Simuliere Latenz
        return {"last": 50000 + self._call_count * 100, "symbol": symbol}


async def demo_circuit_breaker():
    """Demo: Circuit Breaker in Aktion"""
    print("\n" + "=" * 60)
    print("DEMO 1: Circuit Breaker")
    print("=" * 60)
    
    client = DemoExchangeClient("demo_exchange")
    
    print("\nFühre 10 API-Calls aus (jeder 4. schlägt fehl)...")
    print("Circuit Breaker öffnet bei 3 Fehlern.\n")
    
    for i in range(10):
        try:
            result = await client.fetch_ticker("BTC/USD")
            print(f"  ✓ Call {i+1}: Success - Price: {result['last']}")
        except Exception as e:
            print(f"  ✗ Call {i+1}: {e}")
        
        await asyncio.sleep(0.2)
    
    # Circuit Breaker Status
    cb = get_circuit_breaker("demo_exchange")
    state = cb.get_state()
    print(f"\nCircuit Breaker Status:")
    print(f"  State: {state['state']}")
    print(f"  Success Calls: {state['metrics']['success_calls']}")
    print(f"  Failed Calls: {state['metrics']['failure_calls']}")
    print(f"  Rejected Calls: {state['metrics']['rejected_calls']}")
    print(f"  Success Rate: {state['metrics']['success_rate']:.1%}")


async def demo_rate_limiting():
    """Demo: Rate Limiting"""
    print("\n" + "=" * 60)
    print("DEMO 2: Rate Limiting")
    print("=" * 60)
    
    print("\nRate Limit: 5 requests/second")
    print("Versuche 10 schnelle Requests...\n")
    
    @rate_limit(name="demo_rate_limit", requests_per_second=5)
    async def fast_api_call(i: int):
        logger.info(f"API Call {i}")
        return f"Result {i}"
    
    import time
    start = time.time()
    
    tasks = [fast_api_call(i) for i in range(10)]
    results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start
    print(f"10 Requests abgeschlossen in {elapsed:.2f}s")
    print(f"(Erwartet: ~2s bei 5 req/s)")
    
    # Rate Limiter Stats
    limiter = get_rate_limiter("demo_rate_limit")
    stats = limiter.get_stats()
    print(f"\nRate Limiter Stats:")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Throttled: {stats['throttled_requests']}")
    print(f"  Throttle Rate: {stats['throttle_rate']:.1%}")


async def demo_health_checks():
    """Demo: Health Checks"""
    print("\n" + "=" * 60)
    print("DEMO 3: Health Checks")
    print("=" * 60)
    
    print("\nFühre System Health Checks aus...\n")
    
    checker = HealthChecker()
    results = await checker.run_all_checks()
    
    # CLI Output
    print(checker.format_results_cli(results))
    
    # Overall Status
    overall = checker.get_overall_status(results)
    print(f"Overall System Health: {overall.value.upper()}")


def demo_backups():
    """Demo: Backups"""
    print("\n" + "=" * 60)
    print("DEMO 4: Backup & Recovery")
    print("=" * 60)
    
    manager = BackupManager()
    
    # Create Backup
    print("\nErstelle Demo-Backup...")
    data = {
        "demo_state": {
            "timestamp": "2025-12-18T09:00:00",
            "portfolio_value": 10000,
            "positions": ["BTC/USD", "ETH/USD"],
        }
    }
    
    backup_id = manager.create_backup(data, backup_type="demo")
    print(f"  ✓ Backup erstellt: {backup_id}")
    
    # List Backups
    print("\nVerfügbare Backups:")
    backups = manager.list_backups()
    for backup in backups[:3]:  # Zeige max 3
        print(f"  - {backup.backup_id} ({backup.size_bytes} bytes)")
    
    # Load Backup
    print(f"\nLade Backup {backup_id}...")
    restored_data = manager.load_backup(backup_id)
    print(f"  ✓ Backup geladen:")
    print(f"    Portfolio Value: {restored_data['demo_state']['portfolio_value']}")
    print(f"    Positions: {restored_data['demo_state']['positions']}")


def demo_monitoring():
    """Demo: Monitoring & Metrics"""
    print("\n" + "=" * 60)
    print("DEMO 5: Monitoring & Metrics")
    print("=" * 60)
    
    print("\nSammle Performance-Metriken...\n")
    
    # Counter
    metrics.increment("demo_operations")
    metrics.increment("demo_operations")
    metrics.increment("demo_operations")
    
    # Gauge
    metrics.set_gauge("demo_active_tasks", 5)
    
    # Timer
    import time
    for i in range(3):
        with metrics.timer("demo_operation_duration"):
            time.sleep(0.1)
    
    # Metriken abrufen
    all_metrics = metrics.get_metrics()
    
    print("Counters:")
    for name, value in all_metrics["counters"].items():
        if name.startswith("demo_"):
            print(f"  {name}: {value}")
    
    print("\nGauges:")
    for name, value in all_metrics["gauges"].items():
        if name.startswith("demo_"):
            print(f"  {name}: {value}")
    
    print("\nTimers:")
    for name, stats in all_metrics["timers"].items():
        if name.startswith("demo_"):
            print(f"  {name}:")
            print(f"    Mean: {stats['mean']:.3f}s")
            print(f"    P95: {stats['p95']:.3f}s")
            print(f"    Count: {stats['count']}")


async def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("PEAK_TRADE RESILIENCE SYSTEM - INTEGRATION DEMO")
    print("=" * 60)
    
    try:
        # Demo 1: Circuit Breaker
        await demo_circuit_breaker()
        
        # Demo 2: Rate Limiting
        await demo_rate_limiting()
        
        # Demo 3: Health Checks
        await demo_health_checks()
        
        # Demo 4: Backups (sync)
        demo_backups()
        
        # Demo 5: Monitoring
        demo_monitoring()
        
        print("\n" + "=" * 60)
        print("DEMO ABGESCHLOSSEN")
        print("=" * 60)
        print("\nAlle Resilience-Features erfolgreich demonstriert!")
        print("\nWeitere Infos:")
        print("  - docs/resilience/INTEGRATION_EXAMPLES.md")
        print("  - docs/resilience/CIRCUIT_BREAKER.md")
        print("  - docs/resilience/MONITORING.md")
        print("  - docs/resilience/BACKUP_RECOVERY.md")
        
    except KeyboardInterrupt:
        print("\n\nDemo abgebrochen.")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
