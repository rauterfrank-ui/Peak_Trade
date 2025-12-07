#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/export_live_audit_snapshot.py
"""
Peak_Trade: Live-Config Audit & Export CLI (Phase 74)
======================================================

CLI zum Exportieren von Live-Audit-Snapshots für Governance, Audits und "Proof of Safety".

WICHTIG: Phase 74 - Read-Only
    - Keine Config-Dateien ändern
    - Keine State-Änderungen
    - Keine echten Orders
    - Keine Token-Werte exportieren (nur Boolean-Präsenz)

Usage:
    python scripts/export_live_audit_snapshot.py --stdout
    python scripts/export_live_audit_snapshot.py --output-json audit/live_audit_2025-12-07.json
    python scripts/export_live_audit_snapshot.py --output-markdown audit/live_audit_2025-12-07.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.environment import get_environment_from_config
from src.core.peak_config import PeakConfig, load_config, load_config_default
from src.live.audit import (
    build_live_audit_snapshot,
    live_audit_snapshot_to_dict,
    live_audit_snapshot_to_markdown,
)
from src.live.risk_limits import LiveRiskLimits
from src.live.safety import SafetyGuard

import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Baut den Argument-Parser."""
    parser = argparse.ArgumentParser(
        prog="export_live_audit_snapshot",
        description="Peak_Trade Live-Config Audit & Export CLI (Phase 74)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Snapshot auf STDOUT (Markdown)
  python scripts/export_live_audit_snapshot.py --stdout

  # JSON-Export
  python scripts/export_live_audit_snapshot.py --output-json audit/live_audit_2025-12-07.json

  # Markdown-Export
  python scripts/export_live_audit_snapshot.py --output-markdown audit/live_audit_2025-12-07.md

  # Beides (JSON + Markdown)
  python scripts/export_live_audit_snapshot.py \\
      --output-json audit/live_audit_2025-12-07.json \\
      --output-markdown audit/live_audit_2025-12-07.md

WICHTIG: Phase 74 - Read-Only
  • Keine Config-Dateien ändern
  • Keine State-Änderungen
  • Keine echten Orders
  • Keine Token-Werte exportieren (nur Boolean-Präsenz)
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Pfad zur Config-Datei (Default: config.toml oder Default-Config)",
    )

    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Pfad für JSON-Export (optional)",
    )

    parser.add_argument(
        "--output-markdown",
        type=str,
        default=None,
        help="Pfad für Markdown-Export (optional)",
    )

    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Zeigt Markdown-Zusammenfassung auf STDOUT",
    )

    parser.add_argument(
        "--environment-id",
        type=str,
        default=None,
        help="Optional Identifier für den Snapshot (z.B. Config-Name)",
    )

    return parser


def main() -> int:
    """Hauptfunktion."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        # Config laden
        if args.config:
            config_path = Path(args.config)
            if not config_path.exists():
                print(f"ERROR: Config-Datei nicht gefunden: {config_path}", file=sys.stderr)
                return 1
            peak_config = load_config(str(config_path))
            environment_id = args.environment_id or config_path.stem
        else:
            peak_config = load_config_default()
            environment_id = args.environment_id or "default"

        # EnvironmentConfig erstellen
        env_config = get_environment_from_config(peak_config)

        # SafetyGuard erstellen
        safety_guard = SafetyGuard(env_config=env_config)

        # LiveRiskLimits erstellen (optional)
        try:
            live_risk_limits = LiveRiskLimits.from_config(peak_config)
        except Exception as e:
            logger.warning(f"LiveRiskLimits konnte nicht geladen werden: {e}")
            live_risk_limits = None

        # Audit-Snapshot erstellen
        snapshot = build_live_audit_snapshot(
            env_config=env_config,
            safety_guard=safety_guard,
            live_risk_limits=live_risk_limits,
            environment_id=environment_id,
        )

        # JSON-Export
        if args.output_json:
            output_path = Path(args.output_json)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            snapshot_dict = live_audit_snapshot_to_dict(snapshot)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(snapshot_dict, f, indent=2, ensure_ascii=False)

            print(f"✓ JSON-Export erstellt: {output_path}", file=sys.stderr)

        # Markdown-Export
        if args.output_markdown:
            output_path = Path(args.output_markdown)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            markdown_text = live_audit_snapshot_to_markdown(snapshot)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_text)

            print(f"✓ Markdown-Export erstellt: {output_path}", file=sys.stderr)

        # STDOUT (wenn kein Export-Pfad angegeben oder explizit --stdout)
        if args.stdout or (not args.output_json and not args.output_markdown):
            markdown_text = live_audit_snapshot_to_markdown(snapshot)
            print(markdown_text)

        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

