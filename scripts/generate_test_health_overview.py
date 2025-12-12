#!/usr/bin/env python3
"""
generate_test_health_overview.py
================================
Meta-Overview Generator für TestHealth-Runs.

Scannt reports/test_health/ nach Run-Ordnern und generiert:
- reports/test_health/OVERVIEW.md
- reports/test_health/OVERVIEW.html

Usage
-----
Alle Profile, alle Runs:
    python3 scripts/generate_test_health_overview.py

Nur ein bestimmtes Profil:
    python3 scripts/generate_test_health_overview.py --only-profile daily_quick

Maximal N Runs pro Profil (neueste zuerst):
    python3 scripts/generate_test_health_overview.py --max-runs-per-profile 10

Kombiniert:
    python3 scripts/generate_test_health_overview.py --only-profile full_suite --max-runs-per-profile 5

Anderes Health-Verzeichnis:
    python3 scripts/generate_test_health_overview.py --health-dir /pfad/zu/reports/test_health

Exit-Codes
----------
- 0: Erfolg (auch wenn 0 Runs gefunden wurden)
- 1: Echter Fehler (I/O-Problem, ungültiger Pfad, etc.)
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Datenklassen
# ---------------------------------------------------------------------------

@dataclass
class RunData:
    """Daten eines einzelnen Health-Runs."""
    timestamp: datetime
    profile: str
    health_score_value: float | None
    health_score_max: float
    passed_checks: int | None
    failed_checks: int | None
    total_checks: int | None
    exit_code: int | None
    status: str  # OK, WARN, VIOLATION_EXPECTED, FAIL
    run_dir: str
    trigger_violations: list[dict] = field(default_factory=list)
    parsing_warnings: list[str] = field(default_factory=list)


@dataclass
class ProfileStats:
    """Aggregierte Stats pro Profil."""
    profile: str
    total_runs: int = 0
    ok_count: int = 0
    warn_count: int = 0
    violation_expected_count: int = 0
    fail_count: int = 0
    avg_health_score: float = 0.0
    last_run_timestamp: datetime | None = None


# ---------------------------------------------------------------------------
# Parsing-Logik
# ---------------------------------------------------------------------------

def parse_timestamp_from_dirname(dirname: str) -> tuple[datetime | None, str | None]:
    """
    Extrahiere Timestamp und Profilname aus Ordnernamen.
    Erwartetes Format: YYYYMMDD_HHMMSS_<profile_name>
    """
    # Pattern: 20251211_143920_daily_quick
    match = re.match(r"^(\d{8}_\d{6})_(.+)$", dirname)
    if match:
        ts_str = match.group(1)
        profile = match.group(2)
        try:
            ts = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
            return ts, profile
        except ValueError:
            pass
    return None, None


def load_json_summary(summary_path: Path) -> dict[str, Any] | None:
    """Lade summary.json falls vorhanden."""
    if summary_path.exists():
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


def parse_markdown_summary(md_path: Path) -> dict[str, Any]:
    """
    Parse summary.md als Fallback.
    Extrahiert Health-Score, Passed/Failed Checks etc. via Regex.
    """
    result: dict[str, Any] = {}
    if not md_path.exists():
        return result
    
    try:
        content = md_path.read_text(encoding="utf-8")
    except IOError:
        return result
    
    # Health-Score: **Health-Score**: 100.0 / 100.0
    match = re.search(r"\*\*Health-Score\*\*:\s*([\d.]+)\s*/\s*([\d.]+)", content)
    if match:
        result["health_score"] = float(match.group(1))
        result["health_score_max"] = float(match.group(2))
    
    # Passed/Failed Checks
    match = re.search(r"\*\*Passed Checks\*\*:\s*(\d+)", content)
    if match:
        result["passed_checks"] = int(match.group(1))
    
    match = re.search(r"\*\*Failed Checks\*\*:\s*(\d+)", content)
    if match:
        result["failed_checks"] = int(match.group(1))
    
    # Profil
    match = re.search(r"\*\*Profil\*\*:\s*`([^`]+)`", content)
    if match:
        result["profile_name"] = match.group(1)
    
    return result


def classify_status(
    health_score: float | None,
    health_score_max: float,
    failed_checks: int | None,
    trigger_violations: list[dict],
) -> str:
    """
    Klassifiziere den Run-Status basierend auf Health-Score und Violations.
    
    Kategorien:
    - OK: Health >= 90%, keine Failures
    - WARN: Health < 90% oder einige Failures
    - VIOLATION_EXPECTED: Hat Trigger-Violations (aber nur Warnings)
    - FAIL: Health < 50% oder kritische Failures
    """
    if health_score is None:
        return "UNKNOWN"
    
    health_pct = (health_score / health_score_max * 100) if health_score_max > 0 else 0
    
    # Check für FAIL (kritisch)
    if health_pct < 50:
        return "FAIL"
    
    # Check für Trigger-Violations (nur warnings = VIOLATION_EXPECTED)
    has_critical_violation = any(
        v.get("severity", "").lower() in ("critical", "error")
        for v in trigger_violations
    )
    has_warning_violation = any(
        v.get("severity", "").lower() == "warning"
        for v in trigger_violations
    )
    
    if has_critical_violation:
        return "FAIL"
    
    if has_warning_violation:
        return "VIOLATION_EXPECTED"
    
    # Check für WARN
    if health_pct < 90 or (failed_checks is not None and failed_checks > 0):
        return "WARN"
    
    return "OK"


def parse_run_directory(run_dir: Path) -> RunData | None:
    """
    Parse einen einzelnen Run-Ordner und extrahiere alle relevanten Daten.
    """
    dirname = run_dir.name
    ts, profile_from_dir = parse_timestamp_from_dirname(dirname)
    
    if ts is None or profile_from_dir is None:
        return None
    
    warnings: list[str] = []
    
    # Versuche JSON zu laden (bevorzugt)
    json_path = run_dir / "summary.json"
    data = load_json_summary(json_path)
    
    if data is None:
        # Fallback: Markdown
        md_path = run_dir / "summary.md"
        data = parse_markdown_summary(md_path)
        if not data:
            warnings.append(f"Keine summary.json oder summary.md gefunden in {dirname}")
    
    # Extrahiere Felder
    profile = data.get("profile_name", profile_from_dir)
    health_score = data.get("health_score")
    health_score_max = 100.0  # Default
    passed_checks = data.get("passed_checks")
    failed_checks = data.get("failed_checks", 0)
    skipped_checks = data.get("skipped_checks", 0)
    
    # Total Checks berechnen
    total_checks = None
    if passed_checks is not None and failed_checks is not None:
        total_checks = passed_checks + failed_checks + skipped_checks
    
    # Trigger Violations
    trigger_violations = data.get("trigger_violations", [])
    if trigger_violations is None:
        trigger_violations = []
    
    # Exit-Code: Nicht direkt gespeichert, aber wir können ihn aus dem Status ableiten
    # In diesem Kontext: failed_checks > 0 oder trigger_violations vorhanden -> exit_code = 1
    exit_code = 0
    if failed_checks and failed_checks > 0:
        exit_code = 1
    elif trigger_violations:
        exit_code = 1  # Violations führen typischerweise zu Exit-Code 1
    
    # Status klassifizieren
    status = classify_status(health_score, health_score_max, failed_checks, trigger_violations)
    
    return RunData(
        timestamp=ts,
        profile=profile,
        health_score_value=health_score,
        health_score_max=health_score_max,
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        total_checks=total_checks,
        exit_code=exit_code,
        status=status,
        run_dir=str(run_dir),
        trigger_violations=trigger_violations,
        parsing_warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate_by_profile(runs: list[RunData]) -> dict[str, ProfileStats]:
    """Aggregiere Runs pro Profil."""
    stats: dict[str, ProfileStats] = {}
    
    for run in runs:
        if run.profile not in stats:
            stats[run.profile] = ProfileStats(profile=run.profile)
        
        ps = stats[run.profile]
        ps.total_runs += 1
        
        if run.status == "OK":
            ps.ok_count += 1
        elif run.status == "WARN":
            ps.warn_count += 1
        elif run.status == "VIOLATION_EXPECTED":
            ps.violation_expected_count += 1
        elif run.status == "FAIL":
            ps.fail_count += 1
        
        # Letzter Run
        if ps.last_run_timestamp is None or run.timestamp > ps.last_run_timestamp:
            ps.last_run_timestamp = run.timestamp
    
    # Durchschnittlichen Health-Score berechnen
    for profile, ps in stats.items():
        profile_runs = [r for r in runs if r.profile == profile and r.health_score_value is not None]
        if profile_runs:
            ps.avg_health_score = sum(r.health_score_value for r in profile_runs) / len(profile_runs)
    
    return stats


# ---------------------------------------------------------------------------
# Report-Generierung: Markdown
# ---------------------------------------------------------------------------

def generate_markdown_report(runs: list[RunData], profile_stats: dict[str, ProfileStats]) -> str:
    """Generiere OVERVIEW.md Inhalt."""
    now = datetime.now()
    
    lines = [
        "# TestHealth Meta-Overview",
        "",
        f"**Generiert am:** {now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Anzahl Runs:** {len(runs)}",
        f"**Profile:** {', '.join(sorted(profile_stats.keys()))}",
        "",
        "---",
        "",
        "## Profil-Übersicht (Aggregiert)",
        "",
        "| Profil | Runs | OK | WARN | VIOLATION_EXPECTED | FAIL | Avg Health | Letzter Run |",
        "|--------|------|----|------|-------------------|------|----------:|-------------|",
    ]
    
    for profile in sorted(profile_stats.keys()):
        ps = profile_stats[profile]
        last_run = ps.last_run_timestamp.strftime("%Y-%m-%d") if ps.last_run_timestamp else "-"
        avg_health = f"{ps.avg_health_score:.1f}" if ps.avg_health_score else "-"
        lines.append(
            f"| {profile} | {ps.total_runs} | {ps.ok_count} | {ps.warn_count} | "
            f"{ps.violation_expected_count} | {ps.fail_count} | {avg_health} | {last_run} |"
        )
    
    lines.extend([
        "",
        "---",
        "",
        "## Detailed Run-Tabelle",
        "",
        "| Timestamp | Profil | Health | Checks | Exit | Status | Ordnerpfad |",
        "|-----------|--------|--------|--------|------|--------|------------|",
    ])
    
    # Sortiert nach Timestamp (neueste oben)
    sorted_runs = sorted(runs, key=lambda r: r.timestamp, reverse=True)
    
    for run in sorted_runs:
        ts_str = run.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        health_str = f"{run.health_score_value:.0f}/{run.health_score_max:.0f}" if run.health_score_value is not None else "-"
        checks_str = f"{run.passed_checks}/{run.total_checks}" if run.passed_checks is not None and run.total_checks is not None else "-"
        exit_str = str(run.exit_code) if run.exit_code is not None else "-"
        
        # Status-Emoji
        status_emoji = {
            "OK": "✅",
            "WARN": "⚠️",
            "VIOLATION_EXPECTED": "🔷",
            "FAIL": "❌",
            "UNKNOWN": "❓",
        }.get(run.status, "")
        
        # Relativer Pfad
        rel_path = run.run_dir.replace(str(Path.cwd()) + "/", "")
        
        lines.append(
            f"| {ts_str} | {run.profile} | {health_str} | {checks_str} | "
            f"{exit_str} | {status_emoji} {run.status} | `{rel_path}` |"
        )
    
    # Parsing-Warnungen
    all_warnings = []
    for run in runs:
        for w in run.parsing_warnings:
            all_warnings.append((run.run_dir, w))
    
    if all_warnings:
        lines.extend([
            "",
            "---",
            "",
            "## Parsing-Warnungen",
            "",
        ])
        for path, warning in all_warnings:
            lines.append(f"- **{path}**: {warning}")
    
    lines.extend([
        "",
        "---",
        "",
        "## Legende",
        "",
        "| Status | Bedeutung |",
        "|--------|-----------|",
        "| ✅ OK | Health ≥ 90%, keine Failures |",
        "| ⚠️ WARN | Health < 90% oder Failures vorhanden |",
        "| 🔷 VIOLATION_EXPECTED | Trigger-Violations (nur Warnings), erwartetes Verhalten |",
        "| ❌ FAIL | Health < 50% oder kritische Violations |",
        "",
    ])
    
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Report-Generierung: HTML
# ---------------------------------------------------------------------------

def generate_html_report(runs: list[RunData], profile_stats: dict[str, ProfileStats]) -> str:
    """Generiere OVERVIEW.html Inhalt."""
    now = datetime.now()
    
    # Status-Farben
    status_colors = {
        "OK": "#28a745",           # Grün
        "WARN": "#ffc107",         # Gelb
        "VIOLATION_EXPECTED": "#17a2b8",  # Blau
        "FAIL": "#dc3545",         # Rot
        "UNKNOWN": "#6c757d",      # Grau
    }
    
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang=\"de\">",
        "<head>",
        "    <meta charset=\"UTF-8\">",
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
        "    <title>TestHealth Meta-Overview</title>",
        "    <style>",
        "        * { box-sizing: border-box; }",
        "        body {",
        "            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;",
        "            margin: 0; padding: 20px;",
        "            background: #f5f5f5; color: #333;",
        "        }",
        "        .container { max-width: 1400px; margin: 0 auto; }",
        "        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }",
        "        h2 { color: #34495e; margin-top: 30px; }",
        "        .meta { background: #fff; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
        "        .meta span { margin-right: 20px; }",
        "        table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }",
        "        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #e0e0e0; }",
        "        th { background: #3498db; color: #fff; position: sticky; top: 0; }",
        "        tr:hover { background: #f8f9fa; }",
        "        .badge { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; color: #fff; }",
        f"        .badge-ok {{ background: {status_colors['OK']}; }}",
        f"        .badge-warn {{ background: {status_colors['WARN']}; color: #333; }}",
        f"        .badge-violation {{ background: {status_colors['VIOLATION_EXPECTED']}; }}",
        f"        .badge-fail {{ background: {status_colors['FAIL']}; }}",
        f"        .badge-unknown {{ background: {status_colors['UNKNOWN']}; }}",
        "        .path { font-family: 'Monaco', 'Menlo', monospace; font-size: 11px; color: #666; }",
        "        .health-good { color: #28a745; font-weight: 600; }",
        "        .health-warn { color: #ffc107; font-weight: 600; }",
        "        .health-bad { color: #dc3545; font-weight: 600; }",
        "        .legend { background: #fff; padding: 15px; border-radius: 8px; margin-top: 20px; }",
        "        .legend-item { display: inline-block; margin-right: 20px; }",
        "    </style>",
        "</head>",
        "<body>",
        "    <div class=\"container\">",
        "        <h1>🩺 TestHealth Meta-Overview</h1>",
        f"        <div class=\"meta\">",
        f"            <span><strong>Generiert:</strong> {now.strftime('%Y-%m-%d %H:%M:%S')}</span>",
        f"            <span><strong>Runs:</strong> {len(runs)}</span>",
        f"            <span><strong>Profile:</strong> {len(profile_stats)}</span>",
        "        </div>",
        "",
        "        <h2>📊 Profil-Übersicht</h2>",
        "        <table>",
        "            <thead>",
        "                <tr>",
        "                    <th>Profil</th>",
        "                    <th>Runs</th>",
        "                    <th>OK</th>",
        "                    <th>WARN</th>",
        "                    <th>VIOLATION_EXPECTED</th>",
        "                    <th>FAIL</th>",
        "                    <th>Avg Health</th>",
        "                    <th>Letzter Run</th>",
        "                </tr>",
        "            </thead>",
        "            <tbody>",
    ]
    
    for profile in sorted(profile_stats.keys()):
        ps = profile_stats[profile]
        last_run = ps.last_run_timestamp.strftime("%Y-%m-%d") if ps.last_run_timestamp else "-"
        avg_health = f"{ps.avg_health_score:.1f}" if ps.avg_health_score else "-"
        
        # Health-Klasse
        health_class = "health-good"
        if ps.avg_health_score and ps.avg_health_score < 90:
            health_class = "health-warn"
        if ps.avg_health_score and ps.avg_health_score < 50:
            health_class = "health-bad"
        
        html_parts.append(f"                <tr>")
        html_parts.append(f"                    <td><strong>{profile}</strong></td>")
        html_parts.append(f"                    <td>{ps.total_runs}</td>")
        html_parts.append(f"                    <td>{ps.ok_count}</td>")
        html_parts.append(f"                    <td>{ps.warn_count}</td>")
        html_parts.append(f"                    <td>{ps.violation_expected_count}</td>")
        html_parts.append(f"                    <td>{ps.fail_count}</td>")
        html_parts.append(f"                    <td class=\"{health_class}\">{avg_health}</td>")
        html_parts.append(f"                    <td>{last_run}</td>")
        html_parts.append(f"                </tr>")
    
    html_parts.extend([
        "            </tbody>",
        "        </table>",
        "",
        "        <h2>📋 Detailed Run-Tabelle</h2>",
        "        <table>",
        "            <thead>",
        "                <tr>",
        "                    <th>Timestamp</th>",
        "                    <th>Profil</th>",
        "                    <th>Health</th>",
        "                    <th>Checks</th>",
        "                    <th>Exit</th>",
        "                    <th>Status</th>",
        "                    <th>Ordnerpfad</th>",
        "                </tr>",
        "            </thead>",
        "            <tbody>",
    ])
    
    sorted_runs = sorted(runs, key=lambda r: r.timestamp, reverse=True)
    
    for run in sorted_runs:
        ts_str = run.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        health_str = f"{run.health_score_value:.0f}/{run.health_score_max:.0f}" if run.health_score_value is not None else "-"
        checks_str = f"{run.passed_checks}/{run.total_checks}" if run.passed_checks is not None and run.total_checks is not None else "-"
        exit_str = str(run.exit_code) if run.exit_code is not None else "-"
        
        # Badge-Klasse
        badge_class = {
            "OK": "badge-ok",
            "WARN": "badge-warn",
            "VIOLATION_EXPECTED": "badge-violation",
            "FAIL": "badge-fail",
            "UNKNOWN": "badge-unknown",
        }.get(run.status, "badge-unknown")
        
        # Health-Klasse
        health_class = "health-good"
        if run.health_score_value is not None:
            if run.health_score_value < 90:
                health_class = "health-warn"
            if run.health_score_value < 50:
                health_class = "health-bad"
        
        # Relativer Pfad
        rel_path = run.run_dir.replace(str(Path.cwd()) + "/", "")
        
        html_parts.append(f"                <tr>")
        html_parts.append(f"                    <td>{ts_str}</td>")
        html_parts.append(f"                    <td>{run.profile}</td>")
        html_parts.append(f"                    <td class=\"{health_class}\">{health_str}</td>")
        html_parts.append(f"                    <td>{checks_str}</td>")
        html_parts.append(f"                    <td>{exit_str}</td>")
        html_parts.append(f"                    <td><span class=\"badge {badge_class}\">{run.status}</span></td>")
        html_parts.append(f"                    <td class=\"path\">{rel_path}</td>")
        html_parts.append(f"                </tr>")
    
    html_parts.extend([
        "            </tbody>",
        "        </table>",
        "",
        "        <div class=\"legend\">",
        "            <h3>Legende</h3>",
        "            <div class=\"legend-item\"><span class=\"badge badge-ok\">OK</span> Health ≥ 90%, keine Failures</div>",
        "            <div class=\"legend-item\"><span class=\"badge badge-warn\">WARN</span> Health < 90% oder Failures</div>",
        "            <div class=\"legend-item\"><span class=\"badge badge-violation\">VIOLATION_EXPECTED</span> Trigger-Warnings (erwartet)</div>",
        "            <div class=\"legend-item\"><span class=\"badge badge-fail\">FAIL</span> Health < 50% oder kritisch</div>",
        "        </div>",
        "    </div>",
        "</body>",
        "</html>",
    ])
    
    return "\n".join(html_parts)


# ---------------------------------------------------------------------------
# CLI Argument Parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """
    Parse CLI-Argumente für den Meta-Overview-Generator.
    
    Returns:
        argparse.Namespace mit:
        - only_profile: Optional[str] - Nur dieses Profil auswerten
        - max_runs_per_profile: Optional[int] - Max N Runs pro Profil
        - health_dir: str - Pfad zum test_health Verzeichnis
    """
    parser = argparse.ArgumentParser(
        description="Generate meta overview for test health runs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python3 scripts/generate_test_health_overview.py
  python3 scripts/generate_test_health_overview.py --only-profile daily_quick
  python3 scripts/generate_test_health_overview.py --max-runs-per-profile 10
  python3 scripts/generate_test_health_overview.py --only-profile full_suite --max-runs-per-profile 5
        """,
    )
    parser.add_argument(
        "--only-profile",
        type=str,
        default=None,
        help="Wenn gesetzt, nur dieses Profil auswerten (z.B. 'daily_quick').",
    )
    parser.add_argument(
        "--max-runs-per-profile",
        type=int,
        default=None,
        help="Maximale Anzahl Runs pro Profil (neueste zuerst).",
    )
    parser.add_argument(
        "--health-dir",
        type=str,
        default="reports/test_health",
        help="Pfad zum test_health Verzeichnis (default: reports/test_health).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Filter-Logik
# ---------------------------------------------------------------------------

def filter_runs_by_profile(
    runs: list[RunData],
    only_profile: str | None,
) -> list[RunData]:
    """
    Filtert Runs auf ein bestimmtes Profil.
    
    Args:
        runs: Liste aller Runs
        only_profile: Wenn gesetzt, nur Runs dieses Profils behalten
        
    Returns:
        Gefilterte Liste
    """
    if only_profile is None:
        return runs
    return [r for r in runs if r.profile == only_profile]


def limit_runs_per_profile(
    runs: list[RunData],
    max_runs_per_profile: int | None,
) -> list[RunData]:
    """
    Begrenzt die Anzahl Runs pro Profil auf die neuesten N.
    
    Args:
        runs: Liste der Runs
        max_runs_per_profile: Wenn gesetzt, max N Runs pro Profil
        
    Returns:
        Begrenzte Liste (sortiert nach Timestamp absteigend, dann begrenzt)
    """
    if max_runs_per_profile is None:
        return runs
    
    # Gruppiere nach Profil
    by_profile: dict[str, list[RunData]] = defaultdict(list)
    for run in runs:
        by_profile[run.profile].append(run)
    
    # Pro Profil: sortiere absteigend nach Timestamp, nimm die ersten N
    result: list[RunData] = []
    for profile, profile_runs in by_profile.items():
        sorted_runs = sorted(profile_runs, key=lambda r: r.timestamp, reverse=True)
        result.extend(sorted_runs[:max_runs_per_profile])
    
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Hauptfunktion des Meta-Overview-Generators.
    
    Returns:
        Exit-Code:
        - 0: Erfolg (auch bei 0 Runs)
        - 1: Echter Fehler (I/O, ungültiger Pfad)
    """
    args = parse_args()
    
    health_dir = Path(args.health_dir)
    
    # Prüfe, ob Verzeichnis existiert
    if not health_dir.exists():
        print(f"⚠️  Verzeichnis nicht gefunden: {health_dir}")
        print("   Keine Health-Reports vorhanden. Overview wird mit 0 Runs erstellt.")
        # Kein Fehler - wir erstellen einen leeren Report
        runs: list[RunData] = []
        skipped_dirs: list[str] = []
    else:
        # Scanne alle Unterordner
        print(f"🔍 Scanne {health_dir} ...")
        
        runs = []
        skipped_dirs = []
        
        try:
            for item in sorted(health_dir.iterdir()):
                if not item.is_dir():
                    continue
                
                # Überspringe OVERVIEW-Dateien etc.
                if item.name.startswith("OVERVIEW") or item.name.startswith("."):
                    continue
                
                run_data = parse_run_directory(item)
                if run_data:
                    runs.append(run_data)
                else:
                    skipped_dirs.append(item.name)
        except PermissionError as e:
            print(f"❌ Keine Leseberechtigung: {e}")
            return 1
        except OSError as e:
            print(f"❌ I/O-Fehler beim Scannen: {e}")
            return 1
    
    # --- Filter anwenden ---
    
    # 1. Filter: nur bestimmtes Profil
    if args.only_profile:
        before_count = len(runs)
        runs = filter_runs_by_profile(runs, args.only_profile)
        print(f"   Filter: nur Profil '{args.only_profile}' → {len(runs)} von {before_count} Runs")
    
    # 2. Filter: max runs per profile
    if args.max_runs_per_profile:
        before_count = len(runs)
        runs = limit_runs_per_profile(runs, args.max_runs_per_profile)
        print(f"   Filter: max {args.max_runs_per_profile} pro Profil → {len(runs)} Runs")
    
    # Aggregation (auch bei 0 Runs)
    profile_stats = aggregate_by_profile(runs)
    
    # Reports generieren
    md_content = generate_markdown_report(runs, profile_stats)
    html_content = generate_html_report(runs, profile_stats)
    
    # Verzeichnis erstellen falls nötig
    health_dir.mkdir(parents=True, exist_ok=True)
    
    # Schreiben
    md_path = health_dir / "OVERVIEW.md"
    html_path = health_dir / "OVERVIEW.html"
    
    try:
        md_path.write_text(md_content, encoding="utf-8")
        html_path.write_text(html_content, encoding="utf-8")
    except PermissionError as e:
        print(f"❌ Keine Schreibberechtigung: {e}")
        return 1
    except OSError as e:
        print(f"❌ I/O-Fehler beim Schreiben: {e}")
        return 1
    
    # Zusammenfassung
    print()
    print("=" * 60)
    print("✅ TestHealth Meta-Overview generiert!")
    print("=" * 60)
    print(f"   Runs verarbeitet:    {len(runs)}")
    print(f"   Profile gefunden:    {len(profile_stats)}")
    if profile_stats:
        print(f"   Profile:             {', '.join(sorted(profile_stats.keys()))}")
    print()
    print(f"📄 Markdown: {md_path}")
    print(f"🌐 HTML:     {html_path}")
    print()
    
    if skipped_dirs:
        print(f"⚠️  Übersprungene Ordner (nicht parsebar): {len(skipped_dirs)}")
        for d in skipped_dirs[:5]:
            print(f"      - {d}")
        if len(skipped_dirs) > 5:
            print(f"      ... und {len(skipped_dirs) - 5} weitere")
    
    # Erfolg (auch bei 0 Runs)
    return 0


if __name__ == "__main__":
    exit(main())
