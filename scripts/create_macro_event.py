#!/usr/bin/env python3
"""
InfoStream v0 – Makro/GeoRisk Event Creator

Schnelle Erfassung von Makro-Events und geopolitischen Risiken für den InfoStream.

Verwendung:
    # Interaktiver Modus (empfohlen)
    python scripts/create_macro_event.py --interactive

    # Quick-Mode für häufige Event-Typen
    python scripts/create_macro_event.py --quick fed_hike
    python scripts/create_macro_event.py --quick cpi_high
    python scripts/create_macro_event.py --quick regulation

    # Vollständig über CLI
    python scripts/create_macro_event.py \\
        --event "FED erhöht Zinsen um 25bp" \\
        --region us \\
        --impact bearish \\
        --severity warning \\
        --assets all

Siehe: docs/infostream/MACRO_GEORISK_PROMPT.md
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Quick-Templates für häufige Events
QUICK_TEMPLATES = {
    "fed_hike": {
        "event": "FED erhöht Zinsen",
        "region": "us",
        "impact": "bearish",
        "severity": "warning",
        "assets": "all",
        "tags": ["macro", "fed", "rates", "us", "bearish"],
    },
    "fed_cut": {
        "event": "FED senkt Zinsen",
        "region": "us",
        "impact": "bullish",
        "severity": "info",
        "assets": "all",
        "tags": ["macro", "fed", "rates", "us", "bullish"],
    },
    "cpi_high": {
        "event": "CPI-Inflation über Erwartungen",
        "region": "us",
        "impact": "bearish",
        "severity": "warning",
        "assets": "all",
        "tags": ["macro", "inflation", "cpi", "us"],
    },
    "cpi_low": {
        "event": "CPI-Inflation unter Erwartungen",
        "region": "us",
        "impact": "bullish",
        "severity": "info",
        "assets": "all",
        "tags": ["macro", "inflation", "cpi", "us", "bullish"],
    },
    "regulation": {
        "event": "Neue Crypto-Regulierung angekündigt",
        "region": "us",
        "impact": "uncertain",
        "severity": "warning",
        "assets": "all",
        "tags": ["macro", "regulation", "crypto"],
    },
    "exchange_issue": {
        "event": "Exchange-Problem gemeldet",
        "region": "global",
        "impact": "bearish",
        "severity": "error",
        "assets": "all",
        "tags": ["crypto_native", "exchange", "risk"],
    },
    "geopolitics": {
        "event": "Geopolitische Spannungen eskalieren",
        "region": "global",
        "impact": "bearish",
        "severity": "warning",
        "assets": "all",
        "tags": ["macro", "geopolitics", "risk_off"],
    },
    "black_swan": {
        "event": "KRITISCHES EVENT - Details eintragen",
        "region": "global",
        "impact": "bearish",
        "severity": "critical",
        "assets": "all",
        "tags": ["macro", "black_swan", "critical"],
    },
}

VALID_REGIONS = ["us", "eu", "asia", "global", "crypto_native"]
VALID_IMPACTS = ["bullish", "bearish", "neutral", "uncertain"]
VALID_SEVERITIES = ["info", "warning", "error", "critical"]
VALID_ASSETS = ["btc", "eth", "altcoins", "stablecoins", "all"]
VALID_HORIZONS = ["immediate", "short_term", "medium_term", "long_term"]
VALID_CONFIDENCE = ["low", "medium", "high"]


def generate_event_id(short_name: str = "macro") -> str:
    """Generiert eine Event-ID."""
    now = datetime.now()
    return f"INF-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}-macro_{short_name[:10]}"


def create_macro_info_packet(
    event: str,
    region: str,
    impact: str,
    severity: str,
    assets: str,
    summary: Optional[str] = None,
    horizon: str = "short_term",
    confidence: str = "medium",
    indicators: Optional[str] = None,
    precedent: Optional[str] = None,
    links: Optional[list[str]] = None,
    tags: Optional[list[str]] = None,
) -> str:
    """Erstellt ein INFO_PACKET für ein Makro-Event."""
    
    event_id = generate_event_id(event.split()[0].lower()[:10])
    created_at = datetime.now().astimezone().isoformat()
    
    # Summary generieren wenn nicht angegeben
    if not summary:
        impact_text = {
            "bullish": "positiv für Crypto",
            "bearish": "negativ für Crypto",
            "neutral": "neutral für Crypto",
            "uncertain": "unsichere Auswirkungen auf Crypto",
        }.get(impact, "")
        summary = f"{event}. {impact_text.capitalize()}."
    
    # Details
    details = [
        f"Event: {event}",
        f"Region: {region.upper()}",
        f"Asset-Impact: {assets.upper()}",
        f"Direction: {impact}",
        f"Time-Horizon: {horizon.replace('_', '-')}",
        f"Confidence: {confidence}",
    ]
    
    if indicators:
        details.append(f"Key Indicators: {indicators}")
    
    if precedent:
        details.append(f"Historical Precedent: {precedent}")
    
    # Tags
    if not tags:
        tags = ["macro", region, impact]
        if "fed" in event.lower():
            tags.append("fed")
        if "cpi" in event.lower() or "inflation" in event.lower():
            tags.append("inflation")
        if "regulat" in event.lower():
            tags.append("regulation")
    
    # Links
    if not links:
        links = ["[Quelle hier einfügen]"]
    
    # Formatieren
    details_str = "\n".join(f"  - {d}" for d in details)
    links_str = "\n".join(f"  - {link}" for link in links)
    tags_str = "\n".join(f"  - {tag}" for tag in tags)
    
    packet = f"""=== INFO_PACKET ===
source: macro_georisk_specialist
event_id: {event_id}
category: market_analysis
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
    """Interaktive Eingabe für Makro-Events."""
    print("\n" + "=" * 60)
    print("🌍 Makro/GeoRisk Event Creator (Interaktiv)")
    print("=" * 60)
    
    # Event-Beschreibung
    event = input("\n📋 Event-Beschreibung: ").strip()
    if not event:
        event = "Unbekanntes Makro-Event"
    
    # Region
    print(f"\n🌐 Region: {', '.join(VALID_REGIONS)}")
    region = input("   Auswahl [global]: ").strip().lower() or "global"
    if region not in VALID_REGIONS:
        region = "global"
    
    # Impact
    print(f"\n📈 Impact: {', '.join(VALID_IMPACTS)}")
    impact = input("   Auswahl [uncertain]: ").strip().lower() or "uncertain"
    if impact not in VALID_IMPACTS:
        impact = "uncertain"
    
    # Severity
    print(f"\n⚠️  Severity: {', '.join(VALID_SEVERITIES)}")
    severity = input("   Auswahl [warning]: ").strip().lower() or "warning"
    if severity not in VALID_SEVERITIES:
        severity = "warning"
    
    # Assets
    print(f"\n💰 Assets: {', '.join(VALID_ASSETS)}")
    assets = input("   Auswahl [all]: ").strip().lower() or "all"
    if assets not in VALID_ASSETS:
        assets = "all"
    
    # Horizon
    print(f"\n⏱️  Time-Horizon: {', '.join(VALID_HORIZONS)}")
    horizon = input("   Auswahl [short_term]: ").strip().lower() or "short_term"
    if horizon not in VALID_HORIZONS:
        horizon = "short_term"
    
    # Confidence
    print(f"\n🎯 Confidence: {', '.join(VALID_CONFIDENCE)}")
    confidence = input("   Auswahl [medium]: ").strip().lower() or "medium"
    if confidence not in VALID_CONFIDENCE:
        confidence = "medium"
    
    # Optional: Erweiterte Details
    print("\n--- Optionale Details (Enter zum Überspringen) ---")
    
    summary = input("📝 Custom Summary: ").strip() or None
    indicators = input("📊 Key Indicators: ").strip() or None
    precedent = input("📜 Historical Precedent: ").strip() or None
    
    tags_input = input("🏷️  Zusätzliche Tags (kommagetrennt): ").strip()
    extra_tags = [t.strip() for t in tags_input.split(",") if t.strip()]
    
    # Basis-Tags
    tags = ["macro", region, impact]
    tags.extend(extra_tags)
    
    return {
        "event": event,
        "region": region,
        "impact": impact,
        "severity": severity,
        "assets": assets,
        "horizon": horizon,
        "confidence": confidence,
        "summary": summary,
        "indicators": indicators,
        "precedent": precedent,
        "tags": tags,
    }


def quick_mode(template_name: str) -> dict:
    """Lädt ein Quick-Template."""
    if template_name not in QUICK_TEMPLATES:
        print(f"❌ Unbekanntes Template: {template_name}")
        print(f"   Verfügbar: {', '.join(QUICK_TEMPLATES.keys())}")
        sys.exit(1)
    
    template = QUICK_TEMPLATES[template_name].copy()
    
    # Ergänze Standard-Werte
    template.setdefault("horizon", "short_term")
    template.setdefault("confidence", "medium")
    template.setdefault("summary", None)
    template.setdefault("indicators", None)
    template.setdefault("precedent", None)
    
    print(f"📋 Quick-Template geladen: {template_name}")
    print(f"   Event: {template['event']}")
    
    # Optionale Anpassung
    custom_event = input("   Anpassen? (Enter für Standard): ").strip()
    if custom_event:
        template["event"] = custom_event
    
    return template


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Makro/GeoRisk Event Creator für InfoStream",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Quick-Templates:
  {', '.join(QUICK_TEMPLATES.keys())}

Beispiele:
  # Interaktiv
  python scripts/create_macro_event.py --interactive

  # Quick-Mode
  python scripts/create_macro_event.py --quick fed_hike
  python scripts/create_macro_event.py --quick cpi_high --output reports/infostream/events/

  # Vollständig
  python scripts/create_macro_event.py \\
      --event "FED erhöht Zinsen um 25bp" \\
      --region us --impact bearish --severity warning
        """
    )
    
    parser.add_argument("--interactive", "-i", action="store_true", help="Interaktiver Modus")
    parser.add_argument("--quick", "-q", choices=list(QUICK_TEMPLATES.keys()), help="Quick-Template verwenden")
    
    parser.add_argument("--event", "-e", help="Event-Beschreibung")
    parser.add_argument("--region", "-r", choices=VALID_REGIONS, default="global")
    parser.add_argument("--impact", choices=VALID_IMPACTS, default="uncertain")
    parser.add_argument("--severity", "-s", choices=VALID_SEVERITIES, default="warning")
    parser.add_argument("--assets", "-a", choices=VALID_ASSETS, default="all")
    parser.add_argument("--horizon", choices=VALID_HORIZONS, default="short_term")
    parser.add_argument("--confidence", choices=VALID_CONFIDENCE, default="medium")
    
    parser.add_argument("--summary", help="Custom Summary")
    parser.add_argument("--indicators", help="Key Indicators")
    parser.add_argument("--tags", help="Tags (kommagetrennt)")
    
    parser.add_argument("--output", "-o", help="Output-Verzeichnis")
    
    args = parser.parse_args()
    
    # Modus bestimmen
    if args.interactive:
        params = interactive_mode()
    elif args.quick:
        params = quick_mode(args.quick)
    elif args.event:
        tags = None
        if args.tags:
            tags = [t.strip() for t in args.tags.split(",")]
        
        params = {
            "event": args.event,
            "region": args.region,
            "impact": args.impact,
            "severity": args.severity,
            "assets": args.assets,
            "horizon": args.horizon,
            "confidence": args.confidence,
            "summary": args.summary,
            "indicators": args.indicators,
            "tags": tags,
        }
    else:
        parser.print_help()
        print("\n⚠️  Bitte --interactive, --quick oder --event angeben")
        return 1
    
    # INFO_PACKET erstellen
    packet = create_macro_info_packet(**params)
    
    # Output
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        event_id = generate_event_id(params["event"].split()[0].lower()[:10])
        filepath = output_dir / f"{event_id}.txt"
        filepath.write_text(packet, encoding="utf-8")
        print(f"\n✓ INFO_PACKET gespeichert: {filepath}")
    
    print("\n" + "=" * 60)
    print(packet)
    print("=" * 60)
    
    if not args.output:
        print("\nTipp: Mit --output reports/infostream/events/ speichern")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
