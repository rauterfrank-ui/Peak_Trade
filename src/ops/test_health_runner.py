#!/usr/bin/env python3
"""
Peak_Trade Test Health Runner
==============================

Automatisiertes Test-Health-Check-System mit:
  - TOML-basierte Profile-Konfiguration
  - Gewichteter Health-Score (0-100)
  - JSON/Markdown/HTML Reports
  - CLI-Integration

Autor: Peak_Trade Ops Team
Stand: Dezember 2024
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, Optional

# Python 3.11+: tomllib ist built-in
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        raise ImportError(
            "Python <3.11 benötigt 'tomli' package: pip install tomli"
        )


# ============================================================================
# Type Definitions
# ============================================================================

HealthStatus = Literal["PASS", "FAIL", "SKIPPED"]


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class TestCheckConfig:
    """Konfiguration eines einzelnen Test-Checks."""

    id: str
    name: str
    cmd: str
    weight: int
    category: str


@dataclass
class TestCheckResult:
    """Ergebnis eines einzelnen Test-Checks."""

    id: str
    name: str
    category: str
    cmd: str
    status: HealthStatus
    weight: int
    started_at: dt.datetime
    finished_at: dt.datetime
    duration_seconds: float
    return_code: Optional[int] = None
    error_message: Optional[str] = None


@dataclass
class TestHealthSummary:
    """Aggregiertes Summary aller Test-Checks eines Profils."""

    profile_name: str
    started_at: dt.datetime
    finished_at: dt.datetime
    checks: list[TestCheckResult]
    health_score: float  # 0.0 - 100.0
    passed_checks: int
    failed_checks: int
    skipped_checks: int
    total_weight: int
    passed_weight: int


# ============================================================================
# Core Functions
# ============================================================================


def load_test_health_profile(
    config_path: Path, profile_name: str
) -> list[TestCheckConfig]:
    """
    Lädt ein Test-Health-Profil aus der TOML-Konfiguration.

    Parameters
    ----------
    config_path : Path
        Pfad zur test_health_profiles.toml
    profile_name : str
        Name des zu ladenden Profils (z.B. "weekly_core")

    Returns
    -------
    list[TestCheckConfig]
        Liste der Check-Konfigurationen

    Raises
    ------
    FileNotFoundError
        Wenn config_path nicht existiert
    ValueError
        Wenn Profil nicht gefunden oder ungültig konfiguriert
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config nicht gefunden: {config_path}")

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    # Profil finden
    profiles = config.get("profiles", {})
    if profile_name not in profiles:
        available = list(profiles.keys())
        raise ValueError(
            f"Profil '{profile_name}' nicht gefunden. "
            f"Verfügbar: {', '.join(available)}"
        )

    profile = profiles[profile_name]

    # Checks extrahieren
    checks_raw = profile.get("checks", [])
    if not checks_raw:
        raise ValueError(f"Profil '{profile_name}' hat keine Checks definiert.")

    checks = []
    for i, check_dict in enumerate(checks_raw):
        # Validierung
        for required_field in ["id", "name", "cmd", "weight", "category"]:
            if required_field not in check_dict:
                raise ValueError(
                    f"Check #{i} in Profil '{profile_name}' fehlt Feld '{required_field}'"
                )

        check_id = check_dict["id"]
        name = check_dict["name"]
        cmd = check_dict["cmd"]
        weight = check_dict["weight"]
        category = check_dict["category"]

        # Zusätzliche Validierungen
        if not isinstance(check_id, str) or not check_id.strip():
            raise ValueError(f"Check #{i}: 'id' muss nicht-leerer String sein.")
        if not isinstance(cmd, str) or not cmd.strip():
            raise ValueError(f"Check #{i}: 'cmd' muss nicht-leerer String sein.")
        if not isinstance(weight, int) or weight <= 0:
            raise ValueError(f"Check #{i}: 'weight' muss positiver Integer sein.")

        checks.append(
            TestCheckConfig(
                id=check_id,
                name=name,
                cmd=cmd,
                weight=weight,
                category=category,
            )
        )

    return checks


def run_single_check(check: TestCheckConfig) -> TestCheckResult:
    """
    Führt einen einzelnen Test-Check aus.

    Parameters
    ----------
    check : TestCheckConfig
        Check-Konfiguration

    Returns
    -------
    TestCheckResult
        Ergebnis mit Status, Dauer, Returncode
    """
    started_at = dt.datetime.utcnow()
    status: HealthStatus = "FAIL"
    return_code: Optional[int] = None
    error_message: Optional[str] = None

    try:
        result = subprocess.run(
            check.cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600,  # 10 Minuten Timeout
        )
        return_code = result.returncode

        if return_code == 0:
            status = "PASS"
        else:
            status = "FAIL"
            error_message = (
                f"Command exited with code {return_code}.\n"
                f"STDOUT:\n{result.stdout[-500:]}\n"
                f"STDERR:\n{result.stderr[-500:]}"
            )

    except subprocess.TimeoutExpired:
        status = "FAIL"
        error_message = f"Command timeout nach 600s: {check.cmd}"

    except Exception as e:
        status = "FAIL"
        error_message = f"Fehler beim Ausführen von '{check.cmd}': {e}"

    finished_at = dt.datetime.utcnow()
    duration_seconds = (finished_at - started_at).total_seconds()

    return TestCheckResult(
        id=check.id,
        name=check.name,
        category=check.category,
        cmd=check.cmd,
        status=status,
        weight=check.weight,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        return_code=return_code,
        error_message=error_message,
    )


def aggregate_health(
    profile_name: str, results: list[TestCheckResult]
) -> TestHealthSummary:
    """
    Aggregiert Check-Resultate zu einem Health-Summary.

    Parameters
    ----------
    profile_name : str
        Name des Profils
    results : list[TestCheckResult]
        Liste der Check-Resultate

    Returns
    -------
    TestHealthSummary
        Summary mit Health-Score (0-100)
    """
    if not results:
        return TestHealthSummary(
            profile_name=profile_name,
            started_at=dt.datetime.utcnow(),
            finished_at=dt.datetime.utcnow(),
            checks=[],
            health_score=0.0,
            passed_checks=0,
            failed_checks=0,
            skipped_checks=0,
            total_weight=0,
            passed_weight=0,
        )

    passed_checks = sum(1 for r in results if r.status == "PASS")
    failed_checks = sum(1 for r in results if r.status == "FAIL")
    skipped_checks = sum(1 for r in results if r.status == "SKIPPED")

    total_weight = sum(r.weight for r in results)
    passed_weight = sum(r.weight for r in results if r.status == "PASS")

    # Health-Score: Gewichteter Anteil der erfolgreich bestandenen Checks
    if total_weight > 0:
        health_score = (passed_weight / total_weight) * 100.0
    else:
        health_score = 0.0

    # Zeitfenster bestimmen (nur nicht-None Werte)
    start_times = [r.started_at for r in results if r.started_at is not None]
    finish_times = [r.finished_at for r in results if r.finished_at is not None]
    started_at = min(start_times) if start_times else dt.datetime.utcnow()
    finished_at = max(finish_times) if finish_times else dt.datetime.utcnow()

    return TestHealthSummary(
        profile_name=profile_name,
        started_at=started_at,
        finished_at=finished_at,
        checks=results,
        health_score=health_score,
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        skipped_checks=skipped_checks,
        total_weight=total_weight,
        passed_weight=passed_weight,
    )


# ============================================================================
# Report Writers
# ============================================================================


def _datetime_to_iso(obj):
    """Helper: Konvertiert datetime zu ISO-String für JSON-Serialisierung."""
    if isinstance(obj, dt.datetime):
        return obj.isoformat()
    if isinstance(obj, TestCheckResult):
        d = asdict(obj)
        d["started_at"] = d["started_at"].isoformat() if d["started_at"] else None
        d["finished_at"] = d["finished_at"].isoformat() if d["finished_at"] else None
        return d
    if isinstance(obj, TestHealthSummary):
        d = asdict(obj)
        d["started_at"] = d["started_at"].isoformat() if d["started_at"] else None
        d["finished_at"] = d["finished_at"].isoformat() if d["finished_at"] else None
        d["checks"] = [_datetime_to_iso(c) for c in d["checks"]]
        return d
    return obj


def write_test_health_json(summary: TestHealthSummary, path: Path) -> None:
    """
    Schreibt TestHealthSummary als JSON-Datei.

    Parameters
    ----------
    summary : TestHealthSummary
        Summary-Objekt
    path : Path
        Ausgabepfad für JSON
    """
    # Konvertiere Summary zu dict und dann datetime zu ISO-Strings
    def json_serial(obj):
        """JSON serializer für datetime-Objekte."""
        if isinstance(obj, dt.datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    data = asdict(summary)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=json_serial)


def write_test_health_markdown(summary: TestHealthSummary, path: Path) -> None:
    """
    Schreibt TestHealthSummary als Markdown-Datei.

    Parameters
    ----------
    summary : TestHealthSummary
        Summary-Objekt
    path : Path
        Ausgabepfad für Markdown
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Ampel-Interpretation
    score = summary.health_score
    if score >= 80:
        ampel = "🟢 Grün (gesund)"
    elif score >= 50:
        ampel = "🟡 Gelb (teilweise gesund / genauer hinsehen)"
    else:
        ampel = "🔴 Rot (kritisch)"

    duration = (summary.finished_at - summary.started_at).total_seconds()

    md_lines = [
        f"# Test Health Report: {summary.profile_name}",
        "",
        f"**Health-Score**: {summary.health_score:.1f} / 100.0",
        f"**Ampel**: {ampel}",
        "",
        "## Übersicht",
        "",
        f"- **Profil**: `{summary.profile_name}`",
        f"- **Gestartet**: {summary.started_at.isoformat()}",
        f"- **Beendet**: {summary.finished_at.isoformat()}",
        f"- **Dauer**: {duration:.1f}s",
        "",
        f"- **Passed Checks**: {summary.passed_checks}",
        f"- **Failed Checks**: {summary.failed_checks}",
        f"- **Skipped Checks**: {summary.skipped_checks}",
        "",
        f"- **Passed Weight**: {summary.passed_weight} / {summary.total_weight}",
        "",
        "## Check-Details",
        "",
        "| ID | Name | Category | Status | Duration (s) | Weight |",
        "|----|----- |----------|--------|--------------|--------|",
    ]

    for check in summary.checks:
        status_icon = {
            "PASS": "✅",
            "FAIL": "❌",
            "SKIPPED": "⏭️",
        }.get(check.status, "❓")

        md_lines.append(
            f"| `{check.id}` | {check.name} | {check.category} | "
            f"{status_icon} {check.status} | {check.duration_seconds:.2f} | {check.weight} |"
        )

    md_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- **Grün (80-100)**: Alle kritischen Systeme laufen einwandfrei.",
            "- **Gelb (50-80)**: Teilweise Probleme, genauer hinsehen.",
            "- **Rot (<50)**: Kritische Probleme, sofortiges Handeln erforderlich.",
            "",
        ]
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))


def write_test_health_html(summary: TestHealthSummary, path: Path) -> None:
    """
    Schreibt TestHealthSummary als HTML-Datei.

    Parameters
    ----------
    summary : TestHealthSummary
        Summary-Objekt
    path : Path
        Ausgabepfad für HTML
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Ampel-Farbe bestimmen
    score = summary.health_score
    if score >= 80:
        color_class = "green"
        ampel_text = "Grün (gesund)"
    elif score >= 50:
        color_class = "yellow"
        ampel_text = "Gelb (teilweise gesund)"
    else:
        color_class = "red"
        ampel_text = "Rot (kritisch)"

    duration = (summary.finished_at - summary.started_at).total_seconds()

    # HTML-Template
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Health Report: {summary.profile_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .health-score {{
            font-size: 48px;
            font-weight: bold;
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .health-score.green {{ background-color: #d4edda; color: #155724; }}
        .health-score.yellow {{ background-color: #fff3cd; color: #856404; }}
        .health-score.red {{ background-color: #f8d7da; color: #721c24; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #007bff;
            color: white;
            font-weight: bold;
        }}
        .status-PASS {{ color: #28a745; font-weight: bold; }}
        .status-FAIL {{ color: #dc3545; font-weight: bold; }}
        .status-SKIPPED {{ color: #6c757d; font-weight: bold; }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <h1>🏥 Test Health Report: {summary.profile_name}</h1>
    
    <div class="health-score {color_class}">
        {summary.health_score:.1f} / 100.0
        <div style="font-size: 18px; margin-top: 10px;">{ampel_text}</div>
    </div>

    <div class="summary">
        <h2>Übersicht</h2>
        <p><strong>Profil:</strong> <code>{summary.profile_name}</code></p>
        <p><strong>Gestartet:</strong> {summary.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <p><strong>Beendet:</strong> {summary.finished_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <p><strong>Dauer:</strong> {duration:.1f}s</p>
        <hr>
        <p><strong>Passed Checks:</strong> {summary.passed_checks}</p>
        <p><strong>Failed Checks:</strong> {summary.failed_checks}</p>
        <p><strong>Skipped Checks:</strong> {summary.skipped_checks}</p>
        <p><strong>Passed Weight:</strong> {summary.passed_weight} / {summary.total_weight}</p>
    </div>

    <h2>Check-Details</h2>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Category</th>
                <th>Status</th>
                <th>Duration (s)</th>
                <th>Weight</th>
            </tr>
        </thead>
        <tbody>
"""

    for check in summary.checks:
        status_icon = {
            "PASS": "✅",
            "FAIL": "❌",
            "SKIPPED": "⏭️",
        }.get(check.status, "❓")

        html += f"""
            <tr>
                <td><code>{check.id}</code></td>
                <td>{check.name}</td>
                <td>{check.category}</td>
                <td class="status-{check.status}">{status_icon} {check.status}</td>
                <td>{check.duration_seconds:.2f}</td>
                <td>{check.weight}</td>
            </tr>
"""

    html += """
        </tbody>
    </table>

    <div class="footer">
        <p>Generated by Peak_Trade Test Health Automation v0</p>
    </div>
</body>
</html>
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


# ============================================================================
# Main Runner Function
# ============================================================================


def run_test_health_profile(
    profile_name: str, config_path: Path, report_root: Path
) -> tuple[TestHealthSummary, Path]:
    """
    Führt ein komplettes Test-Health-Profil aus und erzeugt Reports.

    Parameters
    ----------
    profile_name : str
        Name des Profils (z.B. "weekly_core")
    config_path : Path
        Pfad zur test_health_profiles.toml
    report_root : Path
        Basis-Verzeichnis für Reports (z.B. reports/test_health)

    Returns
    -------
    tuple[TestHealthSummary, Path]
        (summary, report_directory)
    """
    # 1) Profil laden
    checks = load_test_health_profile(config_path, profile_name)

    # 2) Checks ausführen
    results = []
    for i, check in enumerate(checks, start=1):
        print(f"[{i}/{len(checks)}] Führe Check aus: {check.name} ({check.id})")
        result = run_single_check(check)
        results.append(result)
        status_icon = "✅" if result.status == "PASS" else "❌"
        print(
            f"         {status_icon} {result.status} "
            f"(Duration: {result.duration_seconds:.2f}s)"
        )

    # 3) Summary aggregieren
    summary = aggregate_health(profile_name, results)

    # 4) Report-Verzeichnis erstellen
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = report_root / f"{timestamp}_{profile_name}"
    report_dir.mkdir(parents=True, exist_ok=True)

    # 5) Reports schreiben
    write_test_health_json(summary, report_dir / "summary.json")
    write_test_health_markdown(summary, report_dir / "summary.md")
    write_test_health_html(summary, report_dir / "summary.html")

    # 6) Historie aktualisieren
    try:
        from .test_health_history import append_to_history
        history_path = append_to_history(summary, report_dir)
        print(f"📊 Historie aktualisiert: {history_path}")
    except Exception as e:
        print(f"⚠️ Historie konnte nicht aktualisiert werden: {e}")

    print(f"\n✅ Reports erzeugt: {report_dir}")

    return summary, report_dir
