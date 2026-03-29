#!/usr/bin/env python3
"""
Peak_Trade Test Health History
==============================

Speichert und lädt Health-Score-Historie für Trend-Analysen.

Features:
  - Append-only History-File (JSON)
  - Laden von Daten für bestimmte Profile/Zeiträume
  - Einfache Statistiken (Trend, Durchschnitt, etc.)
  - :func:`compute_test_health_stats_for_triggers` für Trigger-Evaluation im Runner

Stand: Dezember 2024
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

# Import from sibling module
from .test_health_runner import TestHealthStats, TestHealthSummary

_DEFAULT_TRIGGER_LOOKBACK_DAYS = 90


@dataclass
class HealthHistoryEntry:
    """Einzelner Eintrag in der Health-Historie."""

    profile_name: str
    timestamp: str  # ISO format
    health_score: float
    passed_checks: int
    failed_checks: int
    skipped_checks: int
    total_weight: int
    passed_weight: int
    duration_seconds: float
    report_dir: Optional[str] = None


def _get_default_history_path() -> Path:
    """Standard-Pfad für History-File."""
    return Path("reports/test_health/history.json")


def load_history(
    history_path: Optional[Path] = None,
    profile_name: Optional[str] = None,
    days: Optional[int] = None,
) -> list[HealthHistoryEntry]:
    """
    Lädt Health-Historie aus JSON-File.

    Parameters
    ----------
    history_path : Path, optional
        Pfad zur history.json (default: reports/test_health/history.json)
    profile_name : str, optional
        Filter nach Profil-Name (None = alle Profile)
    days : int, optional
        Nur Einträge der letzten X Tage (None = alle)

    Returns
    -------
    list[HealthHistoryEntry]
        Liste der Historie-Einträge, sortiert nach Timestamp (älteste zuerst)
    """
    if history_path is None:
        history_path = _get_default_history_path()

    if not history_path.exists():
        return []

    with open(history_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = []
    cutoff = None
    if days is not None:
        cutoff = dt.datetime.utcnow() - dt.timedelta(days=days)

    for entry_dict in data.get("entries", []):
        # Filter nach Profil
        if profile_name and entry_dict.get("profile_name") != profile_name:
            continue

        # Filter nach Zeitraum
        if cutoff:
            entry_ts = dt.datetime.fromisoformat(entry_dict["timestamp"].replace("Z", "+00:00"))
            if entry_ts.replace(tzinfo=None) < cutoff:
                continue

        entries.append(HealthHistoryEntry(**entry_dict))

    # Sortiere nach Timestamp (älteste zuerst)
    entries.sort(key=lambda e: e.timestamp)

    return entries


def append_to_history(
    summary: TestHealthSummary,
    report_dir: Optional[Path] = None,
    history_path: Optional[Path] = None,
) -> Path:
    """
    Fügt einen neuen Eintrag zur Health-Historie hinzu.

    Parameters
    ----------
    summary : TestHealthSummary
        Summary des aktuellen Runs
    report_dir : Path, optional
        Pfad zum Report-Verzeichnis
    history_path : Path, optional
        Pfad zur history.json

    Returns
    -------
    Path
        Pfad zur history.json
    """
    if history_path is None:
        history_path = _get_default_history_path()

    # Ensure parent directory exists
    history_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing data or create new
    if history_path.exists():
        with open(history_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {
            "version": "0.1",
            "created_at": dt.datetime.utcnow().isoformat() + "Z",
            "entries": [],
        }

    # Calculate duration
    duration_seconds = (summary.finished_at - summary.started_at).total_seconds()

    # Create new entry
    entry = HealthHistoryEntry(
        profile_name=summary.profile_name,
        timestamp=summary.finished_at.isoformat() + "Z",
        health_score=summary.health_score,
        passed_checks=summary.passed_checks,
        failed_checks=summary.failed_checks,
        skipped_checks=summary.skipped_checks,
        total_weight=summary.total_weight,
        passed_weight=summary.passed_weight,
        duration_seconds=duration_seconds,
        report_dir=str(report_dir) if report_dir else None,
    )

    # Append
    data["entries"].append(asdict(entry))
    data["updated_at"] = dt.datetime.utcnow().isoformat() + "Z"

    # Write back
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return history_path


def compute_test_health_stats_for_triggers(
    profile_name: str,
    current_summary: TestHealthSummary,
    history_path: Optional[Path] = None,
    lookback_days: int = _DEFAULT_TRIGGER_LOOKBACK_DAYS,
) -> TestHealthStats:
    """
    Leitet :class:`TestHealthStats` aus gespeicherter Historie + aktuellem Lauf ab.

    Wird für Trigger-Evaluierung genutzt (min_total_runs, max_fail_rate,
    max_consecutive_failures, max_hours_since_last_run). Die Historie enthält
    noch **nicht** den aktuellen Lauf (der typischerweise danach per
    ``append_to_history`` geschrieben wird).

    Parameters
    ----------
    profile_name:
        Profil-Name (Filter).
    current_summary:
        Aggregiertes Summary des gerade beendeten Laufs.
    history_path:
        Pfad zu ``history.json`` (Default: :func:`_get_default_history_path`).
    lookback_days:
        Nur Einträge in diesem Fenster (wie :func:`load_history`).
    """
    if history_path is None:
        history_path = _get_default_history_path()

    entries = load_history(history_path, profile_name, days=lookback_days)
    current_failed = current_summary.failed_checks > 0

    failed_flags = [e.failed_checks > 0 for e in entries]
    failed_flags.append(current_failed)

    total_runs = len(entries) + 1
    failed_runs = sum(1 for e in entries if e.failed_checks > 0) + (1 if current_failed else 0)

    max_consecutive = 0
    cur = 0
    for f in failed_flags:
        if f:
            cur += 1
            max_consecutive = max(max_consecutive, cur)
        else:
            cur = 0

    hours_since_last_run: Optional[float] = None
    if entries:
        last_ts = entries[-1].timestamp
        try:
            last_dt = dt.datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            if last_dt.tzinfo is not None:
                last_dt = last_dt.replace(tzinfo=None)
            delta = dt.datetime.utcnow() - last_dt
            hours_since_last_run = max(0.0, delta.total_seconds() / 3600.0)
        except (ValueError, TypeError):
            hours_since_last_run = None

    all_critical_green = current_summary.failed_checks == 0

    return TestHealthStats(
        total_runs=total_runs,
        failed_runs=failed_runs,
        max_consecutive_failures=max_consecutive,
        hours_since_last_run=hours_since_last_run,
        all_critical_groups_green=all_critical_green,
    )


def get_history_stats(
    profile_name: str,
    days: int = 14,
    history_path: Optional[Path] = None,
) -> dict:
    """
    Berechnet Statistiken über die Health-Historie.

    Parameters
    ----------
    profile_name : str
        Name des Profils
    days : int
        Zeitraum in Tagen (default: 14)
    history_path : Path, optional
        Pfad zur history.json

    Returns
    -------
    dict
        Statistiken: count, avg_score, min_score, max_score, trend, etc.
    """
    entries = load_history(history_path, profile_name, days)

    if not entries:
        return {
            "profile_name": profile_name,
            "days": days,
            "count": 0,
            "avg_score": None,
            "min_score": None,
            "max_score": None,
            "latest_score": None,
            "trend": None,  # "improving", "declining", "stable"
            "avg_duration_seconds": None,
            "total_passed": None,
            "total_failed": None,
        }

    scores = [e.health_score for e in entries]
    durations = [e.duration_seconds for e in entries]

    # Calculate trend (simple: compare first half vs second half average)
    trend = "stable"
    if len(scores) >= 4:
        mid = len(scores) // 2
        first_half_avg = sum(scores[:mid]) / mid
        second_half_avg = sum(scores[mid:]) / (len(scores) - mid)
        diff = second_half_avg - first_half_avg
        if diff > 5:
            trend = "improving"
        elif diff < -5:
            trend = "declining"

    return {
        "profile_name": profile_name,
        "days": days,
        "count": len(entries),
        "avg_score": sum(scores) / len(scores),
        "min_score": min(scores),
        "max_score": max(scores),
        "latest_score": scores[-1],
        "trend": trend,
        "avg_duration_seconds": sum(durations) / len(durations),
        "total_passed": sum(e.passed_checks for e in entries),
        "total_failed": sum(e.failed_checks for e in entries),
        "first_entry": entries[0].timestamp,
        "last_entry": entries[-1].timestamp,
    }


def print_history_summary(
    profile_name: str,
    days: int = 14,
    history_path: Optional[Path] = None,
) -> None:
    """
    Gibt eine formatierte Historie-Zusammenfassung aus.

    Parameters
    ----------
    profile_name : str
        Name des Profils
    days : int
        Zeitraum in Tagen
    history_path : Path, optional
        Pfad zur history.json
    """
    stats = get_history_stats(profile_name, days, history_path)

    print(f"\n{'=' * 60}")
    print(f"📊 Health History: {profile_name} (letzte {days} Tage)")
    print(f"{'=' * 60}")

    if stats["count"] == 0:
        print("Keine Daten vorhanden.")
        print("Tipp: Führe mehrere Runs aus, um Trend-Daten zu sammeln.")
        return

    # Trend-Emoji
    trend_emoji = {
        "improving": "📈",
        "declining": "📉",
        "stable": "➡️",
    }

    print(f"Runs:           {stats['count']}")
    print(f"Zeitraum:       {stats['first_entry'][:10]} bis {stats['last_entry'][:10]}")
    print(f"")
    print(f"Avg Score:      {stats['avg_score']:.1f}")
    print(f"Min Score:      {stats['min_score']:.1f}")
    print(f"Max Score:      {stats['max_score']:.1f}")
    print(f"Latest Score:   {stats['latest_score']:.1f}")
    print(f"Trend:          {trend_emoji.get(stats['trend'], '?')} {stats['trend']}")
    print(f"")
    print(f"Avg Duration:   {stats['avg_duration_seconds']:.2f}s")
    print(f"Total Passed:   {stats['total_passed']}")
    print(f"Total Failed:   {stats['total_failed']}")
    print(f"{'=' * 60}\n")
