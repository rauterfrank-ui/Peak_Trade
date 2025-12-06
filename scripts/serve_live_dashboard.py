#!/usr/bin/env python3
"""
Peak_Trade: Live Dashboard Server (Phase 34)
=============================================

Startet den Web-Server für das Live-Monitoring-Dashboard.

Features:
- REST API für Run-Daten (Snapshots, Tail, Alerts)
- HTML-Dashboard mit Auto-Refresh
- Lokaler Zugriff (default: http://127.0.0.1:8000)

Usage:
    # Standard-Start:
    python -m scripts.serve_live_dashboard

    # Mit anderem Port:
    python -m scripts.serve_live_dashboard --port 8080

    # Auf allen Interfaces (Vorsicht!):
    python -m scripts.serve_live_dashboard --host 0.0.0.0

    # Mit anderem Runs-Verzeichnis:
    python -m scripts.serve_live_dashboard --base-runs-dir /path/to/runs

WICHTIG: Diese Web-UI ist read-only und trifft keine Trading-Entscheidungen.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Projekt-Root zum Path hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.peak_config import load_config
from src.live.web.app import create_app, WebUIConfig, load_web_ui_config


# =============================================================================
# Logging Setup
# =============================================================================


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Konfiguriert Logging für den Server."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("dashboard")


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> int:
    """
    Haupteinstiegspunkt für den Dashboard-Server.

    Returns:
        Exit-Code (0 = Success, 1 = Error)
    """
    parser = argparse.ArgumentParser(
        description="Start Peak_Trade Live Dashboard Server.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with defaults (127.0.0.1:8000):
  python -m scripts.serve_live_dashboard

  # Custom port:
  python -m scripts.serve_live_dashboard --port 8080

  # Custom runs directory:
  python -m scripts.serve_live_dashboard --base-runs-dir /path/to/runs

Open http://127.0.0.1:8000 in your browser to view the dashboard.
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Path to config file (default: config/config.toml)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host to bind to (default: from config or 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind to (default: from config or 8000)",
    )
    parser.add_argument(
        "--base-runs-dir",
        type=str,
        default=None,
        help="Base directory for run logs (default: from config)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )

    args = parser.parse_args()

    # Setup
    logger = setup_logging(args.log_level)

    # Config laden
    web_cfg = WebUIConfig()
    try:
        config_path = Path(args.config)
        if config_path.exists():
            cfg = load_config(config_path)
            web_cfg = load_web_ui_config(cfg)
        else:
            logger.warning(f"Config not found: {config_path}, using defaults")
    except Exception as e:
        logger.warning(f"Error loading config: {e}, using defaults")

    # Overrides anwenden
    host = args.host or web_cfg.host
    port = args.port or web_cfg.port
    base_runs_dir = args.base_runs_dir or web_cfg.base_runs_dir

    # Check uvicorn
    try:
        import uvicorn
    except ImportError:
        logger.error(
            "uvicorn is required to run the dashboard server.\n"
            "Install with: pip install uvicorn"
        )
        return 1

    # App erstellen
    app = create_app(config=web_cfg, base_runs_dir=base_runs_dir)

    # Server-Info ausgeben
    logger.info("=" * 60)
    logger.info("Peak_Trade Live Dashboard (Phase 34)")
    logger.info("=" * 60)
    logger.info(f"Host:      {host}")
    logger.info(f"Port:      {port}")
    logger.info(f"Runs Dir:  {base_runs_dir}")
    logger.info(f"Dashboard: http://{host}:{port}/")
    logger.info("=" * 60)
    logger.info("Press Ctrl+C to stop the server")
    logger.info("")

    # Server starten
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=args.log_level.lower(),
            reload=args.reload,
        )
        return 0

    except KeyboardInterrupt:
        logger.info("\nServer stopped by user.")
        return 0

    except Exception as e:
        logger.exception(f"Server error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
