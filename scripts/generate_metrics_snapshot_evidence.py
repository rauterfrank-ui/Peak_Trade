"""
Generate Metrics Snapshot Evidence for WP0D

Creates a sample metrics snapshot for evidence/documentation purposes.
"""

from pathlib import Path
from src.observability.metrics import MetricsCollector, export_metrics_snapshot


def generate_evidence_snapshot():
    """Generate sample metrics snapshot for WP0D evidence."""
    collector = MetricsCollector()

    # Simulate some activity
    # Orders
    for i in range(15):
        collector.record_order(labels={"strategy": "ma_crossover"})

    for i in range(5):
        collector.record_order(labels={"strategy": "breakout"})

    # Errors
    collector.record_error(error_type="NetworkError")
    collector.record_error(error_type="TimeoutError")

    # Reconnects
    collector.record_reconnect(labels={"exchange": "kraken"})

    # Latencies (simulate distribution)
    latencies = [
        5.2, 7.3, 12.1, 8.9, 15.4, 6.7, 9.2, 11.3, 14.7, 7.8,
        10.5, 13.2, 8.4, 16.9, 9.7, 12.8, 7.1, 11.9, 14.2, 6.3,
        # Add more for percentile calculation
        *[float(i) for i in range(15, 100, 2)],
    ]
    for lat in latencies:
        collector.record_latency(lat)

    # Export snapshot
    output_path = Path("reports/observability/metrics_snapshot.json")
    export_metrics_snapshot(collector, output_path)
    print(f"✅ Metrics snapshot generated: {output_path}")


if __name__ == "__main__":
    generate_evidence_snapshot()
