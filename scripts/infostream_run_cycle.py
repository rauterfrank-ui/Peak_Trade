#!/usr/bin/env python3
"""
InfoStream v1 – Zyklus-Runner Script.

Führt einen vollständigen InfoStream-Zyklus durch:
1. TestHealth-Runs entdecken und Events generieren
2. Events via KI auswerten (EVAL_PACKAGE + LEARNING_SNIPPET)
3. Learnings in das zentrale Learning-Log schreiben

Verwendung:
    # Standard-Ausführung
    python scripts/infostream_run_cycle.py

    # Oder als Modul
    python -m scripts.infostream_run_cycle

    # Dry-Run (keine Dateien schreiben)
    python scripts/infostream_run_cycle.py --dry-run

    # Ohne KI-Auswertung
    python scripts/infostream_run_cycle.py --skip-ai

Environment-Variablen:
    OPENAI_API_KEY:      API-Key für OpenAI (erforderlich für KI-Auswertung)
    INFOSTREAM_MODEL:    Modellname (default: gpt-4o-mini)
    INFOSTREAM_SKIP_AI:  Wenn "true", wird keine KI-Auswertung durchgeführt

Ausgabeverzeichnisse:
    reports/infostream/events/  - Generierte IntelEvents (JSON)
    reports/infostream/evals/   - KI-Auswertungen (JSON)
    docs/mindmap/INFOSTREAM_LEARNING_LOG.md - Learnings (Markdown)

Lokale Test-Checkliste:
    1. Sicherstellen, dass mindestens ein TestHealth-Report existiert:
       reports/test_health/<run_id>/summary.json

    2. Lokal testen:
       export OPENAI_API_KEY=DEIN_KEY  # falls echtes Modell genutzt wird
       python scripts/infostream_run_cycle.py

    3. Erwartete Ergebnisse:
       - reports/infostream/events/INF-<run_id>.json
       - reports/infostream/evals/INF-<run_id>.json
       - docs/mindmap/INFOSTREAM_LEARNING_LOG.md enthält neuen Abschnitt

Siehe: docs/infostream/README.md
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Ensure src is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.meta.infostream.run_cycle import run_infostream_cycle


def main() -> int:
    """
    Entry-Point für das InfoStream-Zyklus-Script.

    Returns
    -------
    int
        Exit-Code (0 = Erfolg, 1 = Fehler)
    """
    parser = argparse.ArgumentParser(
        description="InfoStream v1 – Vollautomatisierter Zyklus",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
    # Standard-Ausführung
    python scripts/infostream_run_cycle.py

    # Dry-Run (nur Discovery, keine Dateien schreiben)
    python scripts/infostream_run_cycle.py --dry-run

    # Ohne KI-Auswertung (z.B. wenn kein API-Key vorhanden)
    python scripts/infostream_run_cycle.py --skip-ai

    # Verbose-Modus
    python scripts/infostream_run_cycle.py -v

Environment-Variablen:
    OPENAI_API_KEY      - API-Key für OpenAI
    INFOSTREAM_MODEL    - Modellname (default: gpt-4o-mini)
    INFOSTREAM_SKIP_AI  - "true" um KI-Auswertung zu überspringen
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Discovery, keine Dateien schreiben",
    )

    parser.add_argument(
        "--skip-ai",
        action="store_true",
        help="Keine KI-Auswertung durchführen",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose-Logging aktivieren",
    )

    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Projekt-Root-Verzeichnis (default: auto-detect)",
    )

    args = parser.parse_args()

    # Logging konfigurieren
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Banner
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           InfoStream v1 – Automated Intelligence            ║")
    print("║              Peak_Trade Project © 2025                      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    try:
        result = run_infostream_cycle(
            project_root=args.project_root,
            dry_run=args.dry_run,
            skip_ai=args.skip_ai,
        )

        # Exit-Code bestimmen
        if result["errors"]:
            print(f"\n⚠️  Zyklus abgeschlossen mit {len(result['errors'])} Fehler(n)")
            return 1
        elif result["events_created"] == 0 and result["discovered_runs"] == 0:
            print("\nℹ️  Keine neuen Daten zu verarbeiten")
            return 0
        else:
            print("\n✅ InfoStream-Zyklus erfolgreich abgeschlossen")
            return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Abgebrochen durch Benutzer")
        return 130
    except Exception as e:
        print(f"\n❌ Kritischer Fehler: {e}")
        logging.exception("Kritischer Fehler im InfoStream-Zyklus")
        return 1


if __name__ == "__main__":
    sys.exit(main())
