"""
Generate WP1C Drift Evidence

Creates example daily report for evidence.
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from src.observability.drift.comparator import DriftComparator, DriftMetrics, SignalEvent
from src.observability.drift.daily_report import DailyReportGenerator


def generate_evidence():
    """Generate WP1C evidence artifacts."""
    # Create example drift metrics
    metrics = DriftMetrics(
        total_signals_shadow=150,
        total_signals_backtest=150,
        matched_signals=142,
        divergent_signals=8,
        match_rate=0.947,  # 94.7%
        avg_price_divergence=0.35,  # 0.35%
        avg_quantity_divergence=1.2,  # 1.2%
        details={
            "shadow_symbols": ["BTC/USD", "ETH/USD"],
            "backtest_symbols": ["BTC/USD", "ETH/USD"],
        },
    )

    # Generate daily report
    generator = DailyReportGenerator()
    output_path = Path("reports/drift/wp1c_daily_report_example.md")

    generator.generate_report(
        metrics=metrics,
        date=datetime(2025, 1, 1),
        output_path=output_path,
        session_id="shadow_session_001",
    )

    print(f"✅ Evidence generated: {output_path}")


if __name__ == "__main__":
    generate_evidence()
