#!/usr/bin/env python3
"""
Peak_Trade: Live Web Server (Phase 67)
=======================================

Startet den Web-Server für das Live-Dashboard.

Usage:
    python scripts/live_web_server.py
    python scripts/live_web_server.py --host 0.0.0.0 --port 9000
    python scripts/live_web_server.py --base-runs-dir /path/to/runs
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    import uvicorn
except ImportError:
    print("ERROR: uvicorn not installed. Install with: pip install uvicorn")
    sys.exit(1)

from src.live.web.app import create_app, WebUIConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main-Funktion."""
    parser = argparse.ArgumentParser(
        description="Start Peak_Trade Live Web Dashboard\n\n"
                    "WICHTIG: Read-only Web-Dashboard für Shadow/Testnet-Runs.\n"
                    "Keine Order-Erzeugung, kein Start/Stop aus dem Web UI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    parser.add_argument(
        "--base-runs-dir",
        type=str,
        default="live_runs",
        help="Base directory for runs (default: live_runs)",
    )
    parser.add_argument(
        "--auto-refresh-seconds",
        type=int,
        default=5,
        help="Auto-refresh interval in seconds (default: 5)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development mode)",
    )

    args = parser.parse_args()

    # Config erstellen
    config = WebUIConfig(
        host=args.host,
        port=args.port,
        base_runs_dir=args.base_runs_dir,
        auto_refresh_seconds=args.auto_refresh_seconds,
    )

    # App erstellen
    app = create_app(config=config, base_runs_dir=args.base_runs_dir)

    logger.info(f"Starting Peak_Trade Live Web Dashboard")
    logger.info(f"  Host: {config.host}")
    logger.info(f"  Port: {config.port}")
    logger.info(f"  Base runs dir: {config.base_runs_dir}")
    logger.info(f"  Auto-refresh: {config.auto_refresh_seconds}s")
    logger.info(f"  Dashboard: http://{config.host}:{config.port}/")
    logger.info(f"  Health: http://{config.host}:{config.port}/health")
    logger.info(f"  API: http://{config.host}:{config.port}/runs")

    # Server starten
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()

