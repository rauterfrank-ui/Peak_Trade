#!/usr/bin/env python3
# scripts/generate_market_outlook_daily.py
"""
MarketSentinel v0 – Daily Market Outlook Generator
====================================================

CLI-Script zur Generierung des täglichen Marktausblicks.

Lädt Marktdaten, berechnet Features und nutzt ein LLM für
die Erstellung einer umfassenden Marktanalyse mit Szenarien.

Usage:
    # Mit Defaults (benötigt OPENAI_API_KEY)
    python scripts/generate_market_outlook_daily.py

    # Mit eigener Config und Output-Verzeichnis
    python scripts/generate_market_outlook_daily.py \\
        --config-path config/market_outlook/daily_market_outlook.yaml \\
        --out-dir reports/market_outlook

    # Ohne LLM-Aufruf (für Tests)
    python scripts/generate_market_outlook_daily.py --skip-llm

    # Mit Verbose-Output
    python scripts/generate_market_outlook_daily.py -v

Environment Variables:
    OPENAI_API_KEY: API-Key für OpenAI-API (erforderlich für LLM)
    OPENAI_MODEL: Modell-Override (Default: aus Config oder "gpt-4o")

Stand: Dezember 2024
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Füge src zum Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.market_sentinel.v0_daily_outlook import run_daily_market_outlook


def setup_logging(verbose: bool = False) -> None:
    """Konfiguriert Logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """Parst Kommandozeilen-Argumente."""
    parser = argparse.ArgumentParser(
        description="MarketSentinel v0 – Daily Market Outlook Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Standard-Ausführung (benötigt OPENAI_API_KEY)
  python scripts/generate_market_outlook_daily.py

  # Ohne LLM-Aufruf (zum Testen)
  python scripts/generate_market_outlook_daily.py --skip-llm

  # Mit anderer Config
  python scripts/generate_market_outlook_daily.py \\
      --config-path config/market_outlook/my_custom.yaml

Environment Variables:
  OPENAI_API_KEY  API-Key für OpenAI-API (erforderlich für LLM)
  OPENAI_MODEL    Modell-Override (z.B. "gpt-4o-mini")
        """,
    )

    parser.add_argument(
        "--config-path",
        type=Path,
        default=Path("config/market_outlook/daily_market_outlook.yaml"),
        help="Pfad zur YAML-Config-Datei (Default: config/market_outlook/daily_market_outlook.yaml)",
    )

    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("reports/market_outlook"),
        help="Basis-Verzeichnis für Reports (Default: reports/market_outlook)",
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Verzeichnis für OHLCV-Daten (Default: data/ohlcv)",
    )

    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="LLM-Aufruf überspringen (verwendet Platzhalter-Text)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose Output (Debug-Logging)",
    )

    return parser.parse_args()


def main() -> int:
    """Hauptfunktion."""
    args = parse_args()
    setup_logging(args.verbose)

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("MarketSentinel v0 – Daily Market Outlook Generator")
    logger.info("=" * 60)

    # Prüfe Config-Existenz
    if not args.config_path.exists():
        logger.error(f"Config-Datei nicht gefunden: {args.config_path}")
        return 1

    logger.info(f"Config: {args.config_path}")
    logger.info(f"Output: {args.out_dir}")
    logger.info(f"Skip LLM: {args.skip_llm}")

    if args.skip_llm:
        logger.warning(
            "LLM-Aufruf wird übersprungen. Report enthält Platzhalter statt echter Analyse."
        )

    # Führe Daily Market Outlook aus
    try:
        result = run_daily_market_outlook(
            config_path=args.config_path,
            base_output_dir=args.out_dir,
            skip_llm=args.skip_llm,
            data_dir=args.data_dir,
        )

        if not result.success:
            logger.error(f"Fehler: {result.error_message}")
            return 1

        logger.info("=" * 60)
        logger.info("✅ Daily Market Outlook erfolgreich erstellt!")
        logger.info(f"📄 Report: {result.report_path}")
        logger.info(f"📊 Märkte analysiert: {len(result.snapshots)}")
        logger.info("=" * 60)

        # Ausgabe für Scripting
        print(f"\nREPORT_PATH={result.report_path}")
        return 0

    except Exception as e:
        logger.exception(f"Unerwarteter Fehler: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
