"""
Shadow Pipeline Phase 2 — Quality Report HTML Generator.

Renders a minimal standalone HTML report from quality summary data.
No external dependencies required.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


def render_quality_html_report(summary: dict[str, Any]) -> str:
    """
    Render a standalone HTML report from a quality summary structure.

    Args:
        summary: Dictionary containing:
            - run_timestamp: ISO timestamp or datetime
            - symbol: str
            - timeframe: str
            - tick_count: int
            - bar_count: int
            - quality_events: list of event dicts with keys:
                - kind: str (e.g., "GAP", "SPIKE")
                - severity: str (e.g., "WARN", "ERROR")
                - ts_ms: int
                - details: dict

    Returns:
        HTML string (complete document)
    """
    # Normalize timestamp
    run_ts = summary.get("run_timestamp", datetime.utcnow())
    if isinstance(run_ts, datetime):
        run_ts_str = run_ts.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        run_ts_str = str(run_ts)

    symbol = summary.get("symbol", "N/A")
    timeframe = summary.get("timeframe", "N/A")
    tick_count = summary.get("tick_count", 0)
    bar_count = summary.get("bar_count", 0)
    quality_events = summary.get("quality_events", [])

    # Build events table rows
    event_rows = ""
    if quality_events:
        for event in quality_events:
            kind = event.get("kind", "UNKNOWN")
            severity = event.get("severity", "INFO")
            ts_ms = event.get("ts_ms", 0)
            details = event.get("details", {})

            # Format timestamp
            event_ts = datetime.utcfromtimestamp(ts_ms / 1000.0).strftime("%Y-%m-%d %H:%M:%S")

            # Format details as key-value
            details_str = ", ".join(f"{k}={v}" for k, v in details.items())

            # Color-code severity
            severity_color = {
                "ERROR": "#d32f2f",
                "WARN": "#f57c00",
                "INFO": "#1976d2",
            }.get(severity, "#757575")

            event_rows += f"""
                <tr>
                    <td>{kind}</td>
                    <td style="color: {severity_color}; font-weight: bold;">{severity}</td>
                    <td>{event_ts}</td>
                    <td style="font-size: 0.9em; color: #555;">{details_str}</td>
                </tr>
            """
    else:
        event_rows = """
            <tr>
                <td colspan="4" style="text-align: center; color: #4caf50;">
                    ✅ No quality issues detected
                </td>
            </tr>
        """

    # Build complete HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shadow Pipeline Quality Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #1976d2;
            margin-top: 0;
            border-bottom: 3px solid #1976d2;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #424242;
            margin-top: 30px;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 8px;
        }}
        .metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .metadata-item {{
            background: #f5f5f5;
            padding: 12px;
            border-radius: 4px;
        }}
        .metadata-label {{
            font-size: 0.85em;
            color: #757575;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .metadata-value {{
            font-size: 1.2em;
            font-weight: bold;
            color: #212121;
            margin-top: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th {{
            background: #1976d2;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e0e0e0;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 0.85em;
            color: #757575;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎭 Shadow Pipeline Quality Report</h1>

        <div class="metadata">
            <div class="metadata-item">
                <div class="metadata-label">Run Timestamp</div>
                <div class="metadata-value">{run_ts_str}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Symbol</div>
                <div class="metadata-value">{symbol}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Timeframe</div>
                <div class="metadata-value">{timeframe}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Ticks Processed</div>
                <div class="metadata-value">{tick_count}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Bars Created</div>
                <div class="metadata-value">{bar_count}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Quality Events</div>
                <div class="metadata-value">{len(quality_events)}</div>
            </div>
        </div>

        <h2>Quality Events</h2>
        <table>
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Severity</th>
                    <th>Timestamp</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
                {event_rows}
            </tbody>
        </table>

        <div class="footer">
            Peak Trade — Shadow Pipeline Phase 2 — Quality Monitoring
        </div>
    </div>
</body>
</html>
"""
    return html


def build_reports_index_html(
    report_files: list[str], title: str = "Shadow Pipeline Quality Reports", max_entries: int = 20
) -> str:
    """
    Build an index HTML page listing recent quality reports.

    Args:
        report_files: List of report filenames (relative paths), newest first
        title: Page title
        max_entries: Maximum number of reports to list

    Returns:
        HTML string (complete document)
    """
    # Limit to max_entries
    displayed_files = report_files[:max_entries]

    # Build table rows
    rows = ""
    if displayed_files:
        for idx, filename in enumerate(displayed_files, 1):
            # Extract timestamp from filename (format: quality_report_YYYYMMDD_HHMMSS.html)
            try:
                # Parse timestamp from filename
                parts = filename.replace("quality_report_", "").replace(".html", "").split("_")
                if len(parts) >= 2:
                    date_str = parts[0]  # YYYYMMDD
                    time_str = parts[1]  # HHMMSS
                    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
                    display_timestamp = f"{formatted_date} {formatted_time}"
                else:
                    display_timestamp = filename
            except Exception:
                display_timestamp = filename

            rows += f"""
                <tr>
                    <td>{idx}</td>
                    <td><a href="./{filename}">{display_timestamp}</a></td>
                    <td><a href="./{filename}">View Report</a></td>
                </tr>
            """
    else:
        rows = """
            <tr>
                <td colspan="3" style="text-align: center; color: #757575;">
                    No reports available
                </td>
            </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #1976d2;
            margin-top: 0;
            border-bottom: 3px solid #1976d2;
            padding-bottom: 10px;
        }}
        .info {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
            border-left: 4px solid #1976d2;
        }}
        .info-title {{
            font-weight: bold;
            color: #1976d2;
            margin-bottom: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background: #1976d2;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e0e0e0;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        a {{
            color: #1976d2;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 0.85em;
            color: #757575;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎭 {title}</h1>

        <div class="info">
            <div class="info-title">Quick Access</div>
            <div>
                <a href="./latest.html">📊 Latest Report</a> — Most recent smoke run result
            </div>
        </div>

        <h2>Recent Reports (Last {max_entries})</h2>
        <table>
            <thead>
                <tr>
                    <th style="width: 60px;">#</th>
                    <th>Timestamp</th>
                    <th style="width: 120px;">Action</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>

        <div class="footer">
            Peak Trade — Shadow Pipeline Phase 2 — Quality Monitoring
        </div>
    </div>
</body>
</html>
"""
    return html


def update_latest_and_index(
    output_dir: Path, newest_report_path: Path, max_entries: int = 20
) -> dict[str, Any]:
    """
    Update latest.html and index.html convenience files.

    Args:
        output_dir: Directory containing reports (e.g., reports/shadow/quality/)
        newest_report_path: Path to the newest timestamped report
        max_entries: Maximum number of reports to list in index

    Returns:
        Dictionary with status information:
            - latest_path: Path to latest.html
            - index_path: Path to index.html
            - report_count: Number of reports found
    """
    output_dir = Path(output_dir)
    newest_report_path = Path(newest_report_path)

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy newest report to latest.html
    latest_path = output_dir / "latest.html"
    shutil.copyfile(newest_report_path, latest_path)

    # Gather all timestamped reports (quality_report_*.html)
    report_files = sorted(
        [f.name for f in output_dir.glob("quality_report_*.html")],
        reverse=True,  # Newest first
    )

    # Build index.html
    index_html = build_reports_index_html(report_files, max_entries=max_entries)
    index_path = output_dir / "index.html"
    index_path.write_text(index_html, encoding="utf-8")

    return {
        "latest_path": str(latest_path),
        "index_path": str(index_path),
        "report_count": len(report_files),
    }
