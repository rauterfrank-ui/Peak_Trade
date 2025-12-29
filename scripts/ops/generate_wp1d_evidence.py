"""
Generate WP1D Operator UX Evidence

Creates status snapshot for evidence.
"""

import json
import time
from datetime import datetime
from pathlib import Path

from src.live.ops.alerts import AlertPriority, OperatorAlerts
from src.live.ops.registry import SessionRegistry
from src.live.ops.status import StatusOverview


def generate_evidence():
    """Generate WP1D evidence artifacts."""
    # Create registry with example sessions
    registry = SessionRegistry()
    registry.create_session("shadow_001", metadata={"strategy": "ma_cross", "symbol": "BTC/USD"})
    registry.create_session("shadow_002", metadata={"strategy": "rsi_mean", "symbol": "ETH/USD"})
    registry.update_status("shadow_002", "running")

    # Create status overview
    overview = StatusOverview()
    overview.start()
    time.sleep(0.1)  # Simulate some uptime
    overview.update_metadata("active_symbols", ["BTC/USD", "ETH/USD"])
    overview.update_metadata("strategy_count", 2)

    # Create alerts
    alerts = OperatorAlerts()
    alerts.raise_p2("DRIFT_HIGH", "High drift detected on BTC/USD", metadata={"drift": 0.12})
    alerts.raise_p1("DATA_FEED_DOWN", "Connection lost to exchange", metadata={"exchange": "kraken"})

    # Build snapshot
    snapshot = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "registry": {
            "summary": registry.get_summary(),
            "sessions": [s.to_dict() for s in registry.list_sessions()],
        },
        "status": overview.get_status().to_dict(),
        "alerts": {
            "by_priority": alerts.get_by_priority(),
            "recent": [a.to_dict() for a in alerts.get_recent_alerts(hours=24)],
        },
    }

    # Write snapshot
    output_path = Path("reports/ops/wp1d_status_snapshot.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(snapshot, f, indent=2)

    print(f"✅ Evidence generated: {output_path}")


if __name__ == "__main__":
    generate_evidence()
