"""
InfoStream v1 – Zyklus-Orchestrierung.

Führt einen vollständigen InfoStream-Zyklus durch:
1. TestHealth-Runs entdecken und Events generieren
2. Events via KI auswerten (EVAL_PACKAGE + LEARNING_SNIPPET)
3. Learnings in das zentrale Learning-Log schreiben

Verwendung:
    from src.meta.infostream.run_cycle import run_infostream_cycle

    # Vollständiger Zyklus
    run_infostream_cycle(project_root=Path("."))

    # Nur Discovery (ohne KI-Auswertung)
    runs = discover_test_health_runs(project_root=Path("."))
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from .collector import (
    build_event_from_test_health_report,
    save_intel_event,
    load_intel_event,
)
from .evaluator import call_ai_for_event, save_intel_eval
from .models import IntelEvent, IntelEval, LearningSnippet
from .router import append_learnings_to_log

logger = logging.getLogger(__name__)


# =============================================================================
# Verzeichnisstruktur
# =============================================================================


def get_infostream_paths(project_root: Path) -> dict:
    """
    Gibt die Pfade für InfoStream-Verzeichnisse zurück.

    Parameters
    ----------
    project_root : Path
        Projekt-Root-Verzeichnis

    Returns
    -------
    dict
        Dict mit Keys: test_health_root, events_dir, evals_dir, learning_log
    """
    return {
        "test_health_root": project_root / "reports" / "test_health",
        "events_dir": project_root / "reports" / "infostream" / "events",
        "evals_dir": project_root / "reports" / "infostream" / "evals",
        "learning_log": project_root / "docs" / "mindmap" / "INFOSTREAM_LEARNING_LOG.md",
    }


# =============================================================================
# Discovery
# =============================================================================


def discover_test_health_runs(project_root: Path) -> List[Path]:
    """
    Durchsucht reports/test_health/ nach Unterordnern.

    Nur Ordner auswählen, für die noch KEIN
    reports/infostream/events/INF-<run_dir.name>.json existiert.

    Parameters
    ----------
    project_root : Path
        Projekt-Root-Verzeichnis

    Returns
    -------
    List[Path]
        Liste der noch nicht verarbeiteten Run-Verzeichnisse
    """
    paths = get_infostream_paths(project_root)
    test_health_root = paths["test_health_root"]
    events_dir = paths["events_dir"]

    if not test_health_root.exists():
        logger.info(f"TestHealth-Verzeichnis nicht gefunden: {test_health_root}")
        return []

    # Alle Run-Verzeichnisse finden
    all_runs = [d for d in test_health_root.iterdir() if d.is_dir() and not d.name.startswith(".")]

    # Bereits verarbeitete Events ermitteln
    processed_event_ids = set()
    if events_dir.exists():
        for event_file in events_dir.glob("*.json"):
            processed_event_ids.add(event_file.stem)  # z.B. "INF-20251211_143920_daily_quick"

    # Unverarbeitete Runs filtern
    unprocessed_runs = []
    for run_dir in all_runs:
        event_id = f"INF-{run_dir.name}"
        if event_id not in processed_event_ids:
            # Prüfe ob summary.json existiert
            if (run_dir / "summary.json").exists() or (run_dir / "summary_stats.json").exists():
                unprocessed_runs.append(run_dir)

    logger.info(
        f"Gefunden: {len(all_runs)} TestHealth-Runs, {len(unprocessed_runs)} noch nicht verarbeitet"
    )

    return unprocessed_runs


# =============================================================================
# AI Client Factory
# =============================================================================


def create_ai_client() -> Optional[Any]:
    """
    Erstellt einen KI-Client für die Auswertung.

    Returns
    -------
    Optional[Any]
        OpenAI-Client oder None wenn nicht konfiguriert

    Notes
    -----
    TODO: Saubere Konfiguration mit Environment-Variablen:
        - OPENAI_API_KEY: API-Key für OpenAI
        - INFOSTREAM_MODEL: Modellname (default: gpt-4o-mini)
        - INFOSTREAM_SKIP_AI: Wenn "true", wird kein KI-Aufruf gemacht
    """
    # Prüfe ob KI-Auswertung übersprungen werden soll
    if os.environ.get("INFOSTREAM_SKIP_AI", "").lower() == "true":
        logger.info("KI-Auswertung deaktiviert (INFOSTREAM_SKIP_AI=true)")
        return None

    # Prüfe ob API-Key vorhanden
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY nicht gesetzt - KI-Auswertung wird übersprungen")
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        logger.info("OpenAI-Client erfolgreich initialisiert")
        return client
    except ImportError:
        logger.warning("openai-Paket nicht installiert - KI-Auswertung wird übersprungen")
        return None
    except Exception as e:
        logger.error(f"Fehler beim Initialisieren des OpenAI-Clients: {e}")
        return None


# =============================================================================
# Haupt-Zyklus
# =============================================================================


def run_infostream_cycle(
    project_root: Path,
    dry_run: bool = False,
    skip_ai: bool = False,
) -> dict:
    """
    Führt einen vollständigen InfoStream-Zyklus durch.

    Ablauf:
    1. discover_test_health_runs(project_root)
    2. Für jeden Run:
        - IntelEvent via build_event_from_test_health_report(run_dir)
        - Event via save_intel_event(...) speichern
    3. Für jedes neue Event:
        - call_ai_for_event(event, client) aufrufen
        - Eval & Learning unter reports/infostream/evals/<event_id>.json speichern
    4. Alle LearningSnippets an docs/mindmap/INFOSTREAM_LEARNING_LOG.md anhängen.

    Parameters
    ----------
    project_root : Path
        Projekt-Root-Verzeichnis
    dry_run : bool
        Wenn True, werden keine Dateien geschrieben (nur Discovery)
    skip_ai : bool
        Wenn True, wird keine KI-Auswertung durchgeführt

    Returns
    -------
    dict
        Ergebnis mit Keys:
        - discovered_runs: int
        - events_created: int
        - evals_created: int
        - learnings_added: int
        - errors: List[str]
    """
    result = {
        "discovered_runs": 0,
        "events_created": 0,
        "evals_created": 0,
        "learnings_added": 0,
        "errors": [],
    }

    paths = get_infostream_paths(project_root)

    print("=" * 60)
    print("InfoStream Cycle v1")
    print("=" * 60)
    print(f"Project Root: {project_root}")
    print(f"Dry Run: {dry_run}")
    print(f"Skip AI: {skip_ai}")
    print()

    # 1. Discovery
    print("📂 Phase 1: Discovery...")
    unprocessed_runs = discover_test_health_runs(project_root)
    result["discovered_runs"] = len(unprocessed_runs)
    print(f"   Gefunden: {len(unprocessed_runs)} neue TestHealth-Runs")

    if not unprocessed_runs:
        print("   ℹ️  Keine neuen Runs zu verarbeiten")
        return result

    # 2. Events erstellen
    print("\n📋 Phase 2: Events erstellen...")
    events: List[IntelEvent] = []

    for run_dir in unprocessed_runs:
        try:
            event = build_event_from_test_health_report(run_dir)
            print(f"   ✓ Event erstellt: {event.event_id}")

            if not dry_run:
                save_intel_event(event, paths["events_dir"])

            events.append(event)
            result["events_created"] += 1

        except Exception as e:
            error_msg = f"Fehler bei {run_dir.name}: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            print(f"   ✗ {error_msg}")

    print(f"   Events erstellt: {result['events_created']}")

    # 3. KI-Auswertung
    print("\n🤖 Phase 3: KI-Auswertung...")
    learnings: List[LearningSnippet] = []

    if skip_ai or os.environ.get("INFOSTREAM_SKIP_AI", "").lower() == "true":
        print("   ⏭️  KI-Auswertung übersprungen")
    else:
        client = create_ai_client()

        if client is None:
            print("   ⚠️  Kein KI-Client verfügbar - Auswertung übersprungen")
            # Erstelle Dummy-Learnings für jeden Event
            for event in events:
                learning = LearningSnippet(
                    event_id=event.event_id,
                    lines=[
                        f"Event {event.event_id} wurde ohne KI-Auswertung erstellt.",
                        f"Severity: {event.severity}, Source: {event.source}",
                        "KI-Auswertung manuell nachholen oder OPENAI_API_KEY setzen.",
                    ],
                )
                learnings.append(learning)
        else:
            for event in events:
                try:
                    intel_eval, learning = call_ai_for_event(event, client)
                    print(f"   ✓ Eval erstellt: {event.event_id}")

                    if not dry_run:
                        save_intel_eval(intel_eval, paths["evals_dir"])

                        # Event-Status aktualisieren
                        event.status = "evaluated"
                        save_intel_event(event, paths["events_dir"])

                    learnings.append(learning)
                    result["evals_created"] += 1

                except Exception as e:
                    error_msg = f"KI-Fehler bei {event.event_id}: {e}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    print(f"   ✗ {error_msg}")

                    # Fallback-Learning
                    learning = LearningSnippet(
                        event_id=event.event_id,
                        lines=[f"KI-Auswertung fehlgeschlagen: {e}"],
                    )
                    learnings.append(learning)

    print(f"   Evals erstellt: {result['evals_created']}")

    # 4. Learnings ins Log schreiben
    print("\n📝 Phase 4: Learnings ins Log schreiben...")

    if learnings and not dry_run:
        try:
            append_learnings_to_log(learnings, paths["learning_log"])
            result["learnings_added"] = len(learnings)
            print(f"   ✓ {len(learnings)} Learnings hinzugefügt")
            print(f"   📄 Log: {paths['learning_log']}")
        except Exception as e:
            error_msg = f"Fehler beim Schreiben des Learning-Logs: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            print(f"   ✗ {error_msg}")
    elif dry_run:
        print(f"   ⏭️  Dry-Run: {len(learnings)} Learnings würden hinzugefügt")
        result["learnings_added"] = len(learnings)
    else:
        print("   ℹ️  Keine Learnings zum Hinzufügen")

    # Zusammenfassung
    print("\n" + "=" * 60)
    print("📊 Zusammenfassung:")
    print(f"   Discovered Runs:  {result['discovered_runs']}")
    print(f"   Events Created:   {result['events_created']}")
    print(f"   Evals Created:    {result['evals_created']}")
    print(f"   Learnings Added:  {result['learnings_added']}")
    if result["errors"]:
        print(f"   Errors:           {len(result['errors'])}")
        for err in result["errors"][:3]:
            print(f"     - {err}")
        if len(result["errors"]) > 3:
            print(f"     ... und {len(result['errors']) - 3} weitere")
    print("=" * 60)

    return result


# =============================================================================
# CLI Entry Point (für Modul-Aufruf)
# =============================================================================

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="InfoStream Zyklus-Orchestrierung",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Projekt-Root-Verzeichnis",
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

    args = parser.parse_args()

    result = run_infostream_cycle(
        project_root=args.project_root,
        dry_run=args.dry_run,
        skip_ai=args.skip_ai,
    )

    # Exit-Code basierend auf Errors
    sys.exit(1 if result["errors"] else 0)
