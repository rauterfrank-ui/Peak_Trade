#!/usr/bin/env python3
"""
Peak_Trade: Operator Meta Report Generator (Production)
========================================================

CLI zum Generieren von Operator-Meta-Reports aus gespeicherten Trigger-Training-Sessions.

Features:
    - Lädt Sessions aus dem Session-Store (JSONL)
    - Generiert aggregierten HTML-Report über mehrere Sessions
    - Unterstützt Filterung nach Session-IDs und Limit

Usage:
    # Alle Sessions
    python scripts/generate_operator_meta_report.py

    # Nur letzte 5 Sessions
    python scripts/generate_operator_meta_report.py --limit 5

    # Nur bestimmte Sessions
    python scripts/generate_operator_meta_report.py --session-ids SESSION_A SESSION_B

    # Custom Output-Pfad
    python scripts/generate_operator_meta_report.py --output reports/custom_meta_report.html
"""
import argparse
import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.trigger_training.operator_meta_report import build_operator_meta_report
from src.trigger_training.session_store import (
    load_sessions_from_store,
    list_session_ids,
)


def main():
    parser = argparse.ArgumentParser(
        description="Generiert Operator-Meta-Report aus Trigger-Training-Sessions"
    )
    parser.add_argument(
        "--store-path",
        type=str,
        default="live_runs/trigger_training_sessions.jsonl",
        help="Pfad zur Session-Store-Datei (default: live_runs/trigger_training_sessions.jsonl)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximale Anzahl an Sessions (neueste zuerst)",
    )
    parser.add_argument(
        "--session-ids",
        nargs="+",
        default=None,
        help="Nur diese Session-IDs laden (Space-separated)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="reports/trigger_training/meta/operator_stats_overview.html",
        help="Output-Pfad für HTML-Report (default: reports/trigger_training/meta/operator_stats_overview.html)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Nur Session-IDs auflisten, keinen Report generieren",
    )

    args = parser.parse_args()

    # List-Modus: Nur Session-IDs anzeigen
    if args.list:
        session_ids = list_session_ids(args.store_path)
        if not session_ids:
            print(f"[INFO] Keine Sessions im Store gefunden: {args.store_path}")
            return
        
        print(f"[INFO] {len(session_ids)} Sessions im Store:")
        for sid in session_ids:
            print(f"  - {sid}")
        return

    # Sessions laden
    print(f"[INFO] Lade Sessions aus {args.store_path}...")
    sessions = load_sessions_from_store(
        store_path=args.store_path,
        limit=args.limit,
        session_ids=args.session_ids,
    )

    if not sessions:
        print("[WARN] Keine Sessions gefunden. Store ist leer oder Filter zu restriktiv.")
        print("[INFO] Tipp: Verwende --list um verfügbare Session-IDs anzuzeigen.")
        return

    print(f"[INFO] {len(sessions)} Sessions geladen:")
    for session_id, events in sessions:
        print(f"  - {session_id}: {len(events)} Events")

    # Report generieren
    output_path = Path(args.output)
    print(f"[INFO] Generiere Meta-Report...")
    result_path = build_operator_meta_report(sessions, output_path)

    print(f"[SUCCESS] Meta-Report generiert: {result_path}")
    print(f"[INFO] Öffne im Browser: file://{result_path.absolute()}")


if __name__ == "__main__":
    main()

