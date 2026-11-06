"""
VaR Backtest Suite Report Index Generator.

Discovers run artifacts from a report root directory and generates
deterministic index.{json,md,html} files for audit and navigation.

Phase 8D: Report Index + Compare + HTML Summary
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Tuple


@dataclass
class RunArtifact:
    """Metadata for a single VaR backtest suite run."""

    run_id: str
    path: str  # Relative to report root
    primary_json: str  # Relative to report root
    primary_md: str  # Relative to report root
    metrics: Dict[str, Any]  # Extracted key metrics


def discover_runs(report_root: Path) -> List[RunArtifact]:
    """
    Discover all VaR suite run artifacts in report_root.

    Looks for directories containing suite_report.json and extracts metadata.

    Args:
        report_root: Root directory containing run subdirectories

    Returns:
        List of RunArtifact, sorted by run_id (deterministic)

    Example:
        report_root/
            run_20260101_123000/
                suite_report.json
                suite_report.md
            run_20260102_140000/
                suite_report.json
                suite_report.md
    """
    runs = []
    report_root = Path(report_root)

    if not report_root.exists():
        return []

    # Find all suite_report.json files
    for json_path in sorted(report_root.rglob("suite_report.json")):
        # Get run directory (parent of suite_report.json)
        run_dir = json_path.parent
        run_id = run_dir.name

        # Relative paths from report_root
        rel_run_dir = run_dir.relative_to(report_root)
        rel_json = json_path.relative_to(report_root)

        # Check for companion MD file
        md_path = run_dir / "suite_report.md"
        rel_md = md_path.relative_to(report_root) if md_path.exists() else None

        # Load JSON and extract key metrics
        try:
            with open(json_path, "r") as f:
                data = json.load(f)

            metrics = {
                "observations": data.get("observations", 0),
                "breaches": data.get("breaches", 0),
                "confidence_level": data.get("confidence_level", 0.0),
                "kupiec_pof_result": data.get("kupiec_pof_result", "UNKNOWN"),
                "basel_traffic_light": data.get("basel_traffic_light", "UNKNOWN"),
                "christoffersen_ind_result": data.get("christoffersen_ind_result", "UNKNOWN"),
                "christoffersen_cc_result": data.get("christoffersen_cc_result", "UNKNOWN"),
                "overall_result": data.get("overall_result", "UNKNOWN"),
            }

            runs.append(
                RunArtifact(
                    run_id=run_id,
                    path=str(rel_run_dir),
                    primary_json=str(rel_json),
                    primary_md=str(rel_md) if rel_md else "",
                    metrics=metrics,
                )
            )
        except (json.JSONDecodeError, KeyError, IOError):
            # Skip invalid/incomplete runs
            continue

    # Sort by run_id for deterministic output
    runs.sort(key=lambda r: r.run_id)
    return runs


def build_index_payload(runs: List[RunArtifact]) -> Dict[str, Any]:
    """
    Build deterministic index payload from discovered runs.

    Args:
        runs: List of discovered runs (already sorted)

    Returns:
        Dictionary with schema_version and runs list
    """
    return {
        "schema_version": "1.0",
        "runs": [
            {
                "run_id": run.run_id,
                "path": run.path,
                "primary_json": run.primary_json,
                "primary_md": run.primary_md,
                "metrics": {
                    k: run.metrics[k]
                    for k in sorted(run.metrics.keys())  # Stable key order
                },
            }
            for run in runs
        ],
    }


def render_index_json(payload: Dict[str, Any]) -> str:
    """
    Render index payload as deterministic JSON.

    Args:
        payload: Index payload from build_index_payload

    Returns:
        JSON string (sorted keys, 2-space indent)
    """
    return json.dumps(payload, indent=2, sort_keys=True)


def render_index_md(payload: Dict[str, Any]) -> str:
    """
    Render index payload as Markdown table.

    Args:
        payload: Index payload from build_index_payload

    Returns:
        Markdown string with table of runs
    """
    lines = [
        "# VaR Backtest Suite Report Index",
        "",
        f"**Total Runs:** {len(payload['runs'])}",
        "",
        "## Run Summary",
        "",
        "| Run ID | Observations | Breaches | Confidence | Overall Result | Kupiec POF | Basel TL | Christoffersen IND | Christoffersen CC |",
        "|--------|--------------|----------|------------|----------------|------------|----------|---------------------|-------------------|",
    ]

    for run in payload["runs"]:
        m = run["metrics"]
        lines.append(
            f"| [{run['run_id']}]({run['primary_md'] or run['primary_json']}) "
            f"| {m['observations']} "
            f"| {m['breaches']} "
            f"| {m['confidence_level']:.2%} "
            f"| **{m['overall_result']}** "
            f"| {m['kupiec_pof_result']} "
            f"| {m['basel_traffic_light']} "
            f"| {m['christoffersen_ind_result']} "
            f"| {m['christoffersen_cc_result']} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**Artifacts:**")
    lines.append("")

    for run in payload["runs"]:
        lines.append(f"- **{run['run_id']}**")
        lines.append(f"  - JSON: `{run['primary_json']}`")
        if run["primary_md"]:
            lines.append(f"  - Markdown: `{run['primary_md']}`")

    return "\n".join(lines) + "\n"


def render_index_html(payload: Dict[str, Any]) -> str:
    """
    Render index payload as self-contained HTML.

    Args:
        payload: Index payload from build_index_payload

    Returns:
        HTML string (single file, minimal CSS)
    """
    runs_html = []
    for run in payload["runs"]:
        m = run["metrics"]
        overall_class = "pass" if m["overall_result"] == "PASS" else "fail"
        runs_html.append(
            f"""
        <tr>
            <td><a href="{run["primary_md"] or run["primary_json"]}">{run["run_id"]}</a></td>
            <td>{m["observations"]}</td>
            <td>{m["breaches"]}</td>
            <td>{m["confidence_level"]:.2%}</td>
            <td class="{overall_class}"><strong>{m["overall_result"]}</strong></td>
            <td>{m["kupiec_pof_result"]}</td>
            <td>{m["basel_traffic_light"]}</td>
            <td>{m["christoffersen_ind_result"]}</td>
            <td>{m["christoffersen_cc_result"]}</td>
        </tr>
        """
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaR Backtest Suite Report Index</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #007bff;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f1f1f1;
        }}
        .pass {{
            color: #28a745;
            font-weight: bold;
        }}
        .fail {{
            color: #dc3545;
            font-weight: bold;
        }}
        a {{
            color: #007bff;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .stats {{
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>VaR Backtest Suite Report Index</h1>
        <div class="stats">
            <strong>Total Runs:</strong> {len(payload["runs"])}
        </div>
        <table>
            <thead>
                <tr>
                    <th>Run ID</th>
                    <th>Observations</th>
                    <th>Breaches</th>
                    <th>Confidence</th>
                    <th>Overall Result</th>
                    <th>Kupiec POF</th>
                    <th>Basel TL</th>
                    <th>Christoffersen IND</th>
                    <th>Christoffersen CC</th>
                </tr>
            </thead>
            <tbody>
                {"".join(runs_html)}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    return html


def write_index(
    report_root: Path,
    formats: Tuple[str, ...] = ("json", "md", "html"),
    deterministic: bool = True,
) -> List[Path]:
    """
    Generate index files in specified formats.

    Args:
        report_root: Root directory containing run subdirectories
        formats: Output formats ("json", "md", "html")
        deterministic: Enforce deterministic output (no timestamps)

    Returns:
        List of created file paths

    Example:
        >>> write_index(Path("results/var_suite"), formats=("json", "md"))
        [Path("results/var_suite/index.json"), Path("results/var_suite/index.md")]
    """
    report_root = Path(report_root)
    report_root.mkdir(parents=True, exist_ok=True)

    # Discover runs
    runs = discover_runs(report_root)

    # Build payload
    payload = build_index_payload(runs)

    # Write outputs
    created_files = []

    if "json" in formats:
        json_path = report_root / "index.json"
        with open(json_path, "w") as f:
            f.write(render_index_json(payload))
        created_files.append(json_path)

    if "md" in formats:
        md_path = report_root / "index.md"
        with open(md_path, "w") as f:
            f.write(render_index_md(payload))
        created_files.append(md_path)

    if "html" in formats:
        html_path = report_root / "index.html"
        with open(html_path, "w") as f:
            f.write(render_index_html(payload))
        created_files.append(html_path)

    return created_files
