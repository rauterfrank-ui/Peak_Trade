#!/usr/bin/env python3
"""
InfoStream v0 – INFO_PACKET Generator

Erstellt strukturierte INFO_PACKETs für den InfoStream.

Verwendung:
    python scripts/create_info_packet.py \\
        --source test_health_automation \\
        --category test_automation \\
        --severity warning \\
        --summary "Health-Score 100.0/100.0, alle Checks bestanden." \\
        --links "reports/test_health/summary.md" \\
        --tags "test_health,nightly,monitoring"

    # Oder interaktiv:
    python scripts/create_info_packet.py --interactive

    # Output in Datei speichern:
    python scripts/create_info_packet.py ... --output reports/infostream/events/

Siehe: docs/infostream/README.md
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


VALID_SOURCES = [
    "test_health_automation",
    "offline_realtime_pipeline",
    "offline_synth_session",
    "trigger_training_sessions",
    "macro_georisk_specialist",
    "operator_notes",
]

VALID_CATEGORIES = [
    "test_automation",
    "operator_training",
    "market_analysis",
    "system_health",
    "incident",
    "performance",
]

VALID_SEVERITIES = ["info", "warning", "error", "critical"]


def generate_event_id(source: str) -> str:
    """Generiert eine Event-ID im Format INF-YYYYMMDD-HHMMSS-kurzer_name."""
    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    time_part = now.strftime("%H%M%S")
    
    # Kurzen Namen aus Source ableiten
    short_name = source.split("_")[0][:10]
    
    return f"INF-{date_part}-{time_part}-{short_name}"


def create_info_packet(
    source: str,
    category: str,
    severity: str,
    summary: str,
    details: Optional[list[str]] = None,
    links: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
    event_id: Optional[str] = None,
) -> str:
    """Erstellt ein INFO_PACKET im Text-Format."""
    
    if event_id is None:
        event_id = generate_event_id(source)
    
    now = datetime.now().astimezone()
    created_at = now.isoformat()
    
    # Details formatieren
    details_str = ""
    if details:
        details_str = "\n".join(f"  - {d}" for d in details)
    else:
        details_str = "  - [Details hier einfügen]"
    
    # Links formatieren
    links_str = ""
    if links:
        links_str = "\n".join(f"  - {link}" for link in links)
    else:
        links_str = "  - [Pfad zu Report/Log]"
    
    # Tags formatieren
    tags_str = ""
    if tags:
        tags_str = "\n".join(f"  - {tag}" for tag in tags)
    else:
        tags_str = "  - [tag1]\n  - [tag2]"
    
    packet = f"""=== INFO_PACKET ===
source: {source}
event_id: {event_id}
category: {category}
severity: {severity}
created_at: {created_at}

summary:
  {summary}

details:
{details_str}

links:
{links_str}

tags:
{tags_str}

status: new
=== /INFO_PACKET ==="""
    
    return packet


def interactive_mode() -> dict:
    """Interaktive Eingabe für INFO_PACKET."""
    print("\n=== InfoStream INFO_PACKET Generator (Interaktiv) ===\n")
    
    # Source
    print("Verfügbare Quellen:")
    for i, src in enumerate(VALID_SOURCES, 1):
        print(f"  {i}. {src}")
    choice = input("\nQuelle wählen (1-6): ").strip()
    try:
        source = VALID_SOURCES[int(choice) - 1]
    except (ValueError, IndexError):
        source = VALID_SOURCES[0]
    
    # Category
    print("\nVerfügbare Kategorien:")
    for i, cat in enumerate(VALID_CATEGORIES, 1):
        print(f"  {i}. {cat}")
    choice = input("\nKategorie wählen (1-6): ").strip()
    try:
        category = VALID_CATEGORIES[int(choice) - 1]
    except (ValueError, IndexError):
        category = VALID_CATEGORIES[0]
    
    # Severity
    print("\nSeverity: info, warning, error, critical")
    severity = input("Severity wählen [info]: ").strip().lower() or "info"
    if severity not in VALID_SEVERITIES:
        severity = "info"
    
    # Summary
    summary = input("\nSummary (1-3 Sätze): ").strip()
    if not summary:
        summary = "[Zusammenfassung hier einfügen]"
    
    # Details
    print("\nDetails (eine pro Zeile, leere Zeile zum Beenden):")
    details = []
    while True:
        detail = input("  - ").strip()
        if not detail:
            break
        details.append(detail)
    
    # Links
    print("\nLinks zu Reports/Logs (eine pro Zeile, leere Zeile zum Beenden):")
    links = []
    while True:
        link = input("  - ").strip()
        if not link:
            break
        links.append(link)
    
    # Tags
    tags_input = input("\nTags (kommagetrennt): ").strip()
    tags = [t.strip() for t in tags_input.split(",") if t.strip()]
    
    return {
        "source": source,
        "category": category,
        "severity": severity,
        "summary": summary,
        "details": details or None,
        "links": links or None,
        "tags": tags or None,
    }


def main():
    parser = argparse.ArgumentParser(
        description="InfoStream INFO_PACKET Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Einfaches Paket erstellen
  python scripts/create_info_packet.py \\
      --source test_health_automation \\
      --category test_automation \\
      --severity info \\
      --summary "Nightly run erfolgreich"

  # Mit Details und Tags
  python scripts/create_info_packet.py \\
      --source test_health_automation \\
      --category test_automation \\
      --severity warning \\
      --summary "Health-Score 100/100, 3 expected violations" \\
      --details "Profile: daily_quick" "Passed: 2/2" "Violations: 3" \\
      --links "reports/test_health/summary.md" \\
      --tags "test_health,nightly,monitoring"

  # Interaktiver Modus
  python scripts/create_info_packet.py --interactive

  # In Datei speichern
  python scripts/create_info_packet.py ... --output reports/infostream/events/
        """
    )
    
    parser.add_argument(
        "--source", "-s",
        choices=VALID_SOURCES,
        help="Quelle des Events"
    )
    parser.add_argument(
        "--category", "-c",
        choices=VALID_CATEGORIES,
        help="Kategorie des Events"
    )
    parser.add_argument(
        "--severity",
        choices=VALID_SEVERITIES,
        default="info",
        help="Severity-Level (default: info)"
    )
    parser.add_argument(
        "--summary",
        help="Zusammenfassung (1-3 Sätze)"
    )
    parser.add_argument(
        "--details", "-d",
        nargs="+",
        help="Detail-Punkte (mehrere möglich)"
    )
    parser.add_argument(
        "--links", "-l",
        nargs="+",
        help="Links zu Reports/Logs (mehrere möglich)"
    )
    parser.add_argument(
        "--tags", "-t",
        help="Tags (kommagetrennt)"
    )
    parser.add_argument(
        "--event-id",
        help="Eigene Event-ID (optional, wird sonst generiert)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output-Verzeichnis (speichert als Datei)"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interaktiver Modus"
    )
    parser.add_argument(
        "--clipboard",
        action="store_true",
        help="In Zwischenablage kopieren (benötigt pyperclip)"
    )
    
    args = parser.parse_args()
    
    # Interaktiver Modus
    if args.interactive:
        params = interactive_mode()
    else:
        # Validierung
        if not args.source:
            parser.error("--source ist erforderlich (oder --interactive verwenden)")
        if not args.category:
            parser.error("--category ist erforderlich (oder --interactive verwenden)")
        if not args.summary:
            parser.error("--summary ist erforderlich (oder --interactive verwenden)")
        
        # Tags parsen
        tags = None
        if args.tags:
            tags = [t.strip() for t in args.tags.split(",")]
        
        params = {
            "source": args.source,
            "category": args.category,
            "severity": args.severity,
            "summary": args.summary,
            "details": args.details,
            "links": args.links,
            "tags": tags,
            "event_id": args.event_id,
        }
    
    # Paket erstellen
    packet = create_info_packet(**params)
    
    # Output
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Event-ID für Dateinamen extrahieren
        event_id = params.get("event_id") or generate_event_id(params["source"])
        filename = f"{event_id}.txt"
        filepath = output_dir / filename
        
        filepath.write_text(packet, encoding="utf-8")
        print(f"\n✓ INFO_PACKET gespeichert: {filepath}")
    
    if args.clipboard:
        try:
            import pyperclip
            pyperclip.copy(packet)
            print("\n✓ INFO_PACKET in Zwischenablage kopiert")
        except ImportError:
            print("\n⚠ pyperclip nicht installiert, Zwischenablage nicht verfügbar")
    
    # Immer auf stdout ausgeben
    print("\n" + "=" * 60)
    print(packet)
    print("=" * 60)
    
    if not args.output:
        print("\nTipp: Mit --output reports/infostream/events/ speichern")
        print("Tipp: Mit --clipboard in Zwischenablage kopieren")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
