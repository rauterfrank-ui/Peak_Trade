# src/live/web/__init__.py
"""
Peak_Trade: Web UI Package (Phase 34)
=====================================

Einfache Web-UI für das Monitoring von Shadow-/Paper-Runs.

Features:
- REST API für Run-Daten
- HTML-Dashboard
- JSON-Endpoints für Snapshots, Tail, Alerts

WICHTIG: Die Web-UI ist read-only und trifft keine Trading-Entscheidungen.
"""

from .app import create_app, WebUIConfig, load_web_ui_config

__all__ = [
    "create_app",
    "WebUIConfig",
    "load_web_ui_config",
]
