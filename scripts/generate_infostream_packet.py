#!/usr/bin/env python3
"""
InfoStream v0 – Automatischer INFO_PACKET Generator

Generiert INFO_PACKETs automatisch aus verschiedenen Quellen:
- TestHealth-Reports (nach Nightly/CI-Runs)
- Trigger-Training-Sessions
- Offline-Realtime-Pipeline-Runs

Verwendung:
    # Aus TestHealth-Report generieren
    python scripts/generate_infostream_packet.py \\
        --source test_health \\
        --report-dir reports/test_health/20251211_143920_daily_quick

    # Aus Trigger-Training-Session generieren
    python scripts/generate_infostream_packet.py \\
        --source trigger_training \\
        --session-id SESSION_UUID

    # Auto-Detect aus letztem TestHealth-Report
    python scripts/generate_infostream_packet.py --source test_health --latest

Siehe: docs/infostream/README.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure src is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def generate_event_id(source: str, suffix: str = "") -> str:
    """Generiert eine Event-ID im Format INF-YYYYMMDD-HHMMSS-kurzer_name."""
    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    time_part = now.strftime("%H%M%S")
    short_name = suffix[:20] if suffix else source.split("_")[0][:10]
    return f"INF-{date_part}-{time_part}-{short_name}"


def find_latest_test_health_report(report_root: Path) -> Optional[Path]:
    """Findet den neuesten TestHealth-Report."""
    if not report_root.exists():
        return None

    # Finde alle Report-Verzeichnisse (nicht history.json)
    dirs = [d for d in report_root.iterdir() if d.is_dir() and not d.name.startswith(".")]

    if not dirs:
        return None

    # Sortiere nach Modifikationszeit (neueste zuerst)
    dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    return dirs[0]


def generate_from_test_health(report_dir: Path, output_dir: Optional[Path] = None) -> str:
    """
    Generiert ein INFO_PACKET aus einem TestHealth-Report.

    Parameters
    ----------
    report_dir : Path
        Pfad zum Report-Verzeichnis (z.B. reports/test_health/20251211_143920_daily_quick)
    output_dir : Path, optional
        Output-Verzeichnis für das INFO_PACKET

    Returns
    -------
    str
        Das generierte INFO_PACKET
    """
    summary_json = report_dir / "summary.json"

    if not summary_json.exists():
        raise FileNotFoundError(f"summary.json nicht gefunden in: {report_dir}")

    with open(summary_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Daten extrahieren
    profile_name = data.get("profile_name", "unknown")
    health_score = data.get("health_score", 0.0)
    passed_checks = data.get("passed_checks", 0)
    failed_checks = data.get("failed_checks", 0)
    skipped_checks = data.get("skipped_checks", 0)
    timestamp = data.get("timestamp", datetime.now().isoformat())

    # Trigger-Violations
    trigger_violations = data.get("trigger_violations", [])
    num_violations = len(trigger_violations)

    # Strategy-Coverage und Switch-Sanity
    strategy_coverage = data.get("strategy_coverage", {})
    switch_sanity = data.get("switch_sanity", {})

    # Severity bestimmen
    if failed_checks > 0:
        severity = "error"
    elif num_violations > 0:
        severity = "warning"
    else:
        severity = "info"

    # Summary erstellen
    summary_parts = [f"Health-Score {health_score:.1f}/100.0"]
    if failed_checks == 0:
        summary_parts.append("alle Core-Checks bestanden")
    else:
        summary_parts.append(f"{failed_checks} Check(s) fehlgeschlagen")

    if num_violations > 0:
        summary_parts.append(f"{num_violations} Trigger-Violation(s)")

    summary_text = ", ".join(summary_parts) + "."

    # Details erstellen
    details = [
        f"Profile: {profile_name}",
        f"Health-Score: {health_score:.1f}/100.0",
        f"Passed Checks: {passed_checks}",
        f"Failed Checks: {failed_checks}",
        f"Skipped Checks: {skipped_checks}",
    ]

    if num_violations > 0:
        details.append(f"Trigger Violations: {num_violations}")

    if strategy_coverage and strategy_coverage.get("enabled"):
        cov_healthy = strategy_coverage.get("is_healthy", True)
        details.append(f"Strategy-Coverage: {'✓ OK' if cov_healthy else '✗ Violations'}")

    if switch_sanity and switch_sanity.get("enabled"):
        sanity_ok = switch_sanity.get("is_ok", True)
        details.append(f"Switch-Sanity: {'✓ OK' if sanity_ok else '✗ Violations'}")

    # Links
    relative_dir = (
        report_dir.relative_to(PROJECT_ROOT)
        if report_dir.is_relative_to(PROJECT_ROOT)
        else report_dir
    )
    links = [
        f"{relative_dir}/summary.md",
        f"{relative_dir}/summary.html",
    ]

    # Tags
    tags = ["test_health", profile_name, "automation"]
    if num_violations > 0:
        tags.append("violations")
    if failed_checks == 0 and num_violations == 0:
        tags.append("healthy")

    # Event-ID
    event_id = generate_event_id("test_health", profile_name)

    # Timestamp parsen
    try:
        created_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone()
    except (ValueError, AttributeError):
        created_at = datetime.now().astimezone()

    # INFO_PACKET formatieren
    details_str = "\n".join(f"  - {d}" for d in details)
    links_str = "\n".join(f"  - {link}" for link in links)
    tags_str = "\n".join(f"  - {tag}" for tag in tags)

    packet = f"""=== INFO_PACKET ===
source: test_health_automation
event_id: {event_id}
category: test_automation
severity: {severity}
created_at: {created_at.isoformat()}

summary:
  {summary_text}

details:
{details_str}

links:
{links_str}

tags:
{tags_str}

status: new
=== /INFO_PACKET ==="""

    # Optional speichern
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{event_id}.txt"
        output_file.write_text(packet, encoding="utf-8")
        print(f"✓ INFO_PACKET gespeichert: {output_file}")

    return packet


def generate_from_trigger_training(session_id: str, output_dir: Optional[Path] = None) -> str:
    """
    Generiert ein INFO_PACKET aus einer Trigger-Training-Session.

    Parameters
    ----------
    session_id : str
        Session-ID der Trigger-Training-Session
    output_dir : Path, optional
        Output-Verzeichnis für das INFO_PACKET

    Returns
    -------
    str
        Das generierte INFO_PACKET
    """
    # Versuche Session-Daten zu laden
    try:
        from src.trigger_training.session_store import TriggerTrainingSessionStore

        store = TriggerTrainingSessionStore()
        session = store.get_session(session_id)

        if session is None:
            raise ValueError(f"Session nicht gefunden: {session_id}")

        # Daten extrahieren
        operator_name = session.get("operator_name", "unknown")
        strategy_name = session.get("strategy_name", "unknown")
        total_triggers = session.get("total_triggers", 0)
        decisions_made = session.get("decisions_made", 0)
        correct_decisions = session.get("correct_decisions", 0)
        created_at_str = session.get("created_at", datetime.now().isoformat())

        # Accuracy berechnen
        accuracy = (correct_decisions / decisions_made * 100) if decisions_made > 0 else 0.0

    except ImportError:
        # Fallback wenn Module nicht verfügbar
        print("⚠️  Trigger-Training-Module nicht verfügbar, erstelle Template")
        operator_name = "unknown"
        strategy_name = "unknown"
        total_triggers = 0
        decisions_made = 0
        correct_decisions = 0
        accuracy = 0.0
        created_at_str = datetime.now().isoformat()

    # Severity bestimmen
    if accuracy >= 80:
        severity = "info"
    elif accuracy >= 60:
        severity = "warning"
    else:
        severity = "warning"

    # Summary
    summary_text = f"Trigger-Training-Session für {strategy_name} abgeschlossen. {decisions_made} Entscheidungen, {accuracy:.0f}% korrekt."

    # Details
    details = [
        f"Session-ID: {session_id}",
        f"Operator: {operator_name}",
        f"Strategy: {strategy_name}",
        f"Total Triggers: {total_triggers}",
        f"Decisions Made: {decisions_made}",
        f"Correct Decisions: {correct_decisions}",
        f"Accuracy: {accuracy:.1f}%",
    ]

    # Links
    links = [
        f"reports/trigger_training/session_{session_id}.html",
    ]

    # Tags
    tags = ["trigger_training", "operator_training", strategy_name]
    if accuracy < 70:
        tags.append("needs_improvement")

    # Event-ID
    event_id = generate_event_id("trigger", session_id[:8])

    # Timestamp
    try:
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).astimezone()
    except (ValueError, AttributeError):
        created_at = datetime.now().astimezone()

    # INFO_PACKET formatieren
    details_str = "\n".join(f"  - {d}" for d in details)
    links_str = "\n".join(f"  - {link}" for link in links)
    tags_str = "\n".join(f"  - {tag}" for tag in tags)

    packet = f"""=== INFO_PACKET ===
source: trigger_training_sessions
event_id: {event_id}
category: operator_training
severity: {severity}
created_at: {created_at.isoformat()}

summary:
  {summary_text}

details:
{details_str}

links:
{links_str}

tags:
{tags_str}

status: new
=== /INFO_PACKET ==="""

    # Optional speichern
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{event_id}.txt"
        output_file.write_text(packet, encoding="utf-8")
        print(f"✓ INFO_PACKET gespeichert: {output_file}")

    return packet


def generate_from_offline_realtime(report_path: Path, output_dir: Optional[Path] = None) -> str:
    """
    Generiert ein INFO_PACKET aus einem Offline-Realtime-Pipeline-Report.

    Parameters
    ----------
    report_path : Path
        Pfad zum Report (HTML oder JSON)
    output_dir : Path, optional
        Output-Verzeichnis für das INFO_PACKET

    Returns
    -------
    str
        Das generierte INFO_PACKET
    """
    # Für v0: Einfaches Template, später mit echtem Parsing
    event_id = generate_event_id("offline_rt", report_path.stem[:10])
    created_at = datetime.now().astimezone()

    packet = f"""=== INFO_PACKET ===
source: offline_realtime_pipeline
event_id: {event_id}
category: system_health
severity: info
created_at: {created_at.isoformat()}

summary:
  Offline-Realtime-Pipeline-Run abgeschlossen. Siehe Report für Details.

details:
  - Report: {report_path}
  - [Weitere Details manuell ergänzen]

links:
  - {report_path}

tags:
  - offline_realtime
  - backtest
  - performance

status: new
=== /INFO_PACKET ==="""

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{event_id}.txt"
        output_file.write_text(packet, encoding="utf-8")
        print(f"✓ INFO_PACKET gespeichert: {output_file}")

    return packet


def main() -> int:
    parser = argparse.ArgumentParser(
        description="InfoStream INFO_PACKET Generator (automatisch aus Quellen)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Aus spezifischem TestHealth-Report
  python scripts/generate_infostream_packet.py \\
      --source test_health \\
      --report-dir reports/test_health/20251211_143920_daily_quick

  # Aus letztem TestHealth-Report
  python scripts/generate_infostream_packet.py --source test_health --latest

  # Aus Trigger-Training-Session
  python scripts/generate_infostream_packet.py \\
      --source trigger_training \\
      --session-id abc123

  # Mit Speicherung
  python scripts/generate_infostream_packet.py \\
      --source test_health --latest \\
      --output reports/infostream/events/
        """,
    )

    parser.add_argument(
        "--source",
        "-s",
        choices=["test_health", "trigger_training", "offline_realtime"],
        required=True,
        help="Quelle des INFO_PACKETs",
    )

    parser.add_argument("--report-dir", help="Pfad zum Report-Verzeichnis (für test_health)")

    parser.add_argument("--report-path", help="Pfad zum Report (für offline_realtime)")

    parser.add_argument("--session-id", help="Session-ID (für trigger_training)")

    parser.add_argument(
        "--latest", action="store_true", help="Verwende den neuesten Report (für test_health)"
    )

    parser.add_argument("--output", "-o", help="Output-Verzeichnis für das INFO_PACKET")

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Nur Paket ausgeben, keine zusätzlichen Meldungen",
    )

    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else None

    try:
        if args.source == "test_health":
            if args.latest:
                report_root = PROJECT_ROOT / "reports" / "test_health"
                report_dir = find_latest_test_health_report(report_root)
                if report_dir is None:
                    print("❌ Kein TestHealth-Report gefunden")
                    return 1
                if not args.quiet:
                    print(f"📄 Verwende neuesten Report: {report_dir.name}")
            elif args.report_dir:
                report_dir = Path(args.report_dir)
                if not report_dir.exists():
                    print(f"❌ Report-Verzeichnis nicht gefunden: {report_dir}")
                    return 1
            else:
                print("❌ --report-dir oder --latest erforderlich für test_health")
                return 1

            packet = generate_from_test_health(report_dir, output_dir)

        elif args.source == "trigger_training":
            if not args.session_id:
                print("❌ --session-id erforderlich für trigger_training")
                return 1

            packet = generate_from_trigger_training(args.session_id, output_dir)

        elif args.source == "offline_realtime":
            if not args.report_path:
                print("❌ --report-path erforderlich für offline_realtime")
                return 1

            report_path = Path(args.report_path)
            if not report_path.exists():
                print(f"❌ Report nicht gefunden: {report_path}")
                return 1

            packet = generate_from_offline_realtime(report_path, output_dir)

        else:
            print(f"❌ Unbekannte Quelle: {args.source}")
            return 1

        # Ausgabe
        if not args.quiet:
            print("\n" + "=" * 60)
        print(packet)
        if not args.quiet:
            print("=" * 60)
            if not output_dir:
                print("\nTipp: Mit --output reports/infostream/events/ speichern")

        return 0

    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
