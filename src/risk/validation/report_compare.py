"""
VaR Backtest Suite Run Comparison Tool.

Compares two VaR suite runs (baseline vs candidate) and generates
deterministic compare.{json,md,html} reports for regression tracking.

Phase 8D: Report Index + Compare + HTML Summary
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional


@dataclass
class RunSummary:
    """Summary of a single VaR backtest suite run."""

    run_id: str
    run_path: str
    observations: int
    breaches: int
    confidence_level: float
    kupiec_pof_result: str
    kupiec_pof_pvalue: float
    basel_traffic_light: str
    christoffersen_ind_result: str
    christoffersen_ind_pvalue: float
    christoffersen_cc_result: str
    christoffersen_cc_pvalue: float
    overall_result: str


def load_run(run_dir: Path) -> RunSummary:
    """
    Load VaR suite run summary from JSON report.

    Args:
        run_dir: Directory containing suite_report.json

    Returns:
        RunSummary with extracted metrics

    Raises:
        FileNotFoundError: If suite_report.json not found
        ValueError: If JSON is invalid or missing required fields
    """
    run_dir = Path(run_dir)
    json_path = run_dir / "suite_report.json"

    if not json_path.exists():
        raise FileNotFoundError(f"suite_report.json not found in {run_dir}")

    with open(json_path, "r") as f:
        data = json.load(f)

    # Extract required fields with robust fallbacks
    return RunSummary(
        run_id=run_dir.name,
        run_path=str(run_dir),
        observations=data.get("observations", 0),
        breaches=data.get("breaches", 0),
        confidence_level=data.get("confidence_level", 0.0),
        kupiec_pof_result=data.get("kupiec_pof_result", "UNKNOWN"),
        kupiec_pof_pvalue=data.get("kupiec_pof_pvalue", 0.0),
        basel_traffic_light=data.get("basel_traffic_light", "UNKNOWN"),
        christoffersen_ind_result=data.get("christoffersen_ind_result", "UNKNOWN"),
        christoffersen_ind_pvalue=data.get("christoffersen_ind_pvalue", 0.0),
        christoffersen_cc_result=data.get("christoffersen_cc_result", "UNKNOWN"),
        christoffersen_cc_pvalue=data.get("christoffersen_cc_pvalue", 0.0),
        overall_result=data.get("overall_result", "UNKNOWN"),
    )


def compare_runs(baseline_dir: Path, candidate_dir: Path) -> Dict[str, Any]:
    """
    Compare two VaR suite runs and identify changes.

    Args:
        baseline_dir: Directory of baseline run
        candidate_dir: Directory of candidate run

    Returns:
        Dictionary with baseline, candidate, diff, regressions, improvements

    Example:
        {
            "schema_version": "1.0",
            "baseline": {"run_id": "...", ...},
            "candidate": {"run_id": "...", ...},
            "diff": {"breaches": {"baseline": 5, "candidate": 3, "delta": -2}, ...},
            "regressions": [...],
            "improvements": [...]
        }
    """
    baseline = load_run(baseline_dir)
    candidate = load_run(candidate_dir)

    # Compute deltas
    diff = {
        "observations": {
            "baseline": baseline.observations,
            "candidate": candidate.observations,
            "delta": candidate.observations - baseline.observations,
        },
        "breaches": {
            "baseline": baseline.breaches,
            "candidate": candidate.breaches,
            "delta": candidate.breaches - baseline.breaches,
        },
        "confidence_level": {
            "baseline": baseline.confidence_level,
            "candidate": candidate.confidence_level,
            "delta": round(candidate.confidence_level - baseline.confidence_level, 6),
        },
        "kupiec_pof_pvalue": {
            "baseline": baseline.kupiec_pof_pvalue,
            "candidate": candidate.kupiec_pof_pvalue,
            "delta": round(candidate.kupiec_pof_pvalue - baseline.kupiec_pof_pvalue, 6),
        },
        "christoffersen_ind_pvalue": {
            "baseline": baseline.christoffersen_ind_pvalue,
            "candidate": candidate.christoffersen_ind_pvalue,
            "delta": round(
                candidate.christoffersen_ind_pvalue - baseline.christoffersen_ind_pvalue,
                6,
            ),
        },
        "christoffersen_cc_pvalue": {
            "baseline": baseline.christoffersen_cc_pvalue,
            "candidate": candidate.christoffersen_cc_pvalue,
            "delta": round(
                candidate.christoffersen_cc_pvalue - baseline.christoffersen_cc_pvalue,
                6,
            ),
        },
    }

    # Identify regressions and improvements
    regressions = []
    improvements = []

    # Overall result change
    if baseline.overall_result == "PASS" and candidate.overall_result == "FAIL":
        regressions.append(
            {
                "type": "overall_result",
                "baseline": baseline.overall_result,
                "candidate": candidate.overall_result,
                "severity": "HIGH",
            }
        )
    elif baseline.overall_result == "FAIL" and candidate.overall_result == "PASS":
        improvements.append(
            {
                "type": "overall_result",
                "baseline": baseline.overall_result,
                "candidate": candidate.overall_result,
            }
        )

    # Individual test regressions
    tests = [
        ("kupiec_pof", baseline.kupiec_pof_result, candidate.kupiec_pof_result),
        ("basel_traffic_light", baseline.basel_traffic_light, candidate.basel_traffic_light),
        (
            "christoffersen_ind",
            baseline.christoffersen_ind_result,
            candidate.christoffersen_ind_result,
        ),
        (
            "christoffersen_cc",
            baseline.christoffersen_cc_result,
            candidate.christoffersen_cc_result,
        ),
    ]

    for test_name, base_result, cand_result in tests:
        if base_result == "PASS" and cand_result == "FAIL":
            regressions.append(
                {
                    "type": test_name,
                    "baseline": base_result,
                    "candidate": cand_result,
                    "severity": "MEDIUM",
                }
            )
        elif base_result == "FAIL" and cand_result == "PASS":
            improvements.append(
                {
                    "type": test_name,
                    "baseline": base_result,
                    "candidate": cand_result,
                }
            )

        # Basel traffic light special handling
        if test_name == "basel_traffic_light":
            if base_result == "GREEN" and cand_result in ("YELLOW", "RED"):
                regressions.append(
                    {
                        "type": "basel_traffic_light",
                        "baseline": base_result,
                        "candidate": cand_result,
                        "severity": "HIGH" if cand_result == "RED" else "MEDIUM",
                    }
                )
            elif base_result in ("YELLOW", "RED") and cand_result == "GREEN":
                improvements.append(
                    {
                        "type": "basel_traffic_light",
                        "baseline": base_result,
                        "candidate": cand_result,
                    }
                )

    # Sort for determinism
    regressions.sort(key=lambda x: (x["severity"], x["type"]))
    improvements.sort(key=lambda x: x["type"])

    return {
        "schema_version": "1.0",
        "baseline": {
            "run_id": baseline.run_id,
            "run_path": baseline.run_path,
            "overall_result": baseline.overall_result,
        },
        "candidate": {
            "run_id": candidate.run_id,
            "run_path": candidate.run_path,
            "overall_result": candidate.overall_result,
        },
        "diff": diff,
        "regressions": regressions,
        "improvements": improvements,
    }


def render_compare_json(payload: Dict[str, Any]) -> str:
    """
    Render comparison as deterministic JSON.

    Args:
        payload: Comparison payload from compare_runs

    Returns:
        JSON string (sorted keys, 2-space indent)
    """
    return json.dumps(payload, indent=2, sort_keys=True)


def render_compare_md(payload: Dict[str, Any]) -> str:
    """
    Render comparison as Markdown report.

    Args:
        payload: Comparison payload from compare_runs

    Returns:
        Markdown string with comparison details
    """
    lines = [
        "# VaR Backtest Suite Run Comparison",
        "",
        "## Summary",
        "",
        f"**Baseline:** `{payload['baseline']['run_id']}` → {payload['baseline']['overall_result']}",
        f"**Candidate:** `{payload['candidate']['run_id']}` → {payload['candidate']['overall_result']}",
        "",
    ]

    # Regressions
    if payload["regressions"]:
        lines.append("## ⚠️ Regressions")
        lines.append("")
        for reg in payload["regressions"]:
            lines.append(
                f"- **{reg['type']}**: {reg['baseline']} → {reg['candidate']} "
                f"(Severity: {reg['severity']})"
            )
        lines.append("")
    else:
        lines.append("## ✅ No Regressions")
        lines.append("")

    # Improvements
    if payload["improvements"]:
        lines.append("## 📈 Improvements")
        lines.append("")
        for imp in payload["improvements"]:
            lines.append(f"- **{imp['type']}**: {imp['baseline']} → {imp['candidate']}")
        lines.append("")
    else:
        lines.append("## No Improvements")
        lines.append("")

    # Detailed Metrics
    lines.append("## Detailed Metrics")
    lines.append("")
    lines.append("| Metric | Baseline | Candidate | Delta |")
    lines.append("|--------|----------|-----------|-------|")

    for metric, values in sorted(payload["diff"].items()):
        baseline_val = values["baseline"]
        candidate_val = values["candidate"]
        delta = values["delta"]

        # Format based on type
        if isinstance(baseline_val, float) and "pvalue" not in metric:
            baseline_str = f"{baseline_val:.4f}"
            candidate_str = f"{candidate_val:.4f}"
            delta_str = f"{delta:+.4f}"
        elif isinstance(baseline_val, float):
            baseline_str = f"{baseline_val:.6f}"
            candidate_str = f"{candidate_val:.6f}"
            delta_str = f"{delta:+.6f}"
        else:
            baseline_str = str(baseline_val)
            candidate_str = str(candidate_val)
            delta_str = str(delta) if delta != 0 else "—"

        lines.append(f"| {metric} | {baseline_str} | {candidate_str} | {delta_str} |")

    return "\n".join(lines) + "\n"


def render_compare_html(payload: Dict[str, Any]) -> str:
    """
    Render comparison as self-contained HTML.

    Args:
        payload: Comparison payload from compare_runs

    Returns:
        HTML string (single file, minimal CSS)
    """
    # Regressions HTML
    regressions_html = []
    if payload["regressions"]:
        for reg in payload["regressions"]:
            severity_class = reg["severity"].lower()
            regressions_html.append(
                f'<li class="regression {severity_class}">'
                f"<strong>{reg['type']}</strong>: "
                f"{reg['baseline']} → {reg['candidate']} "
                f'<span class="severity">({reg["severity"]})</span></li>'
            )
        regressions_section = f"<ul>{''.join(regressions_html)}</ul>"
    else:
        regressions_section = '<p class="pass">✅ No regressions detected</p>'

    # Improvements HTML
    improvements_html = []
    if payload["improvements"]:
        for imp in payload["improvements"]:
            improvements_html.append(
                f'<li class="improvement">'
                f"<strong>{imp['type']}</strong>: "
                f"{imp['baseline']} → {imp['candidate']}</li>"
            )
        improvements_section = f"<ul>{''.join(improvements_html)}</ul>"
    else:
        improvements_section = "<p>No improvements detected</p>"

    # Metrics table HTML
    metrics_rows = []
    for metric, values in sorted(payload["diff"].items()):
        baseline_val = values["baseline"]
        candidate_val = values["candidate"]
        delta = values["delta"]

        # Format based on type
        if isinstance(baseline_val, float) and "pvalue" not in metric:
            baseline_str = f"{baseline_val:.4f}"
            candidate_str = f"{candidate_val:.4f}"
            delta_str = f"{delta:+.4f}"
        elif isinstance(baseline_val, float):
            baseline_str = f"{baseline_val:.6f}"
            candidate_str = f"{candidate_val:.6f}"
            delta_str = f"{delta:+.6f}"
        else:
            baseline_str = str(baseline_val)
            candidate_str = str(candidate_val)
            delta_str = str(delta) if delta != 0 else "—"

        delta_class = "neutral"
        if isinstance(delta, (int, float)) and delta != 0:
            delta_class = "negative" if delta < 0 else "positive"

        metrics_rows.append(
            f"""
        <tr>
            <td>{metric}</td>
            <td>{baseline_str}</td>
            <td>{candidate_str}</td>
            <td class="{delta_class}">{delta_str}</td>
        </tr>
        """
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VaR Suite Run Comparison</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
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
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        .summary {{
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        li {{
            padding: 8px;
            margin: 5px 0;
            border-radius: 4px;
        }}
        .regression {{
            background-color: #f8d7da;
            border-left: 4px solid #dc3545;
        }}
        .regression.high {{
            background-color: #f5c6cb;
        }}
        .improvement {{
            background-color: #d4edda;
            border-left: 4px solid #28a745;
        }}
        .severity {{
            font-size: 0.85em;
            color: #6c757d;
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
        .positive {{
            color: #28a745;
        }}
        .negative {{
            color: #dc3545;
        }}
        .neutral {{
            color: #6c757d;
        }}
        .pass {{
            color: #28a745;
            font-weight: bold;
        }}
        .fail {{
            color: #dc3545;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>VaR Backtest Suite Run Comparison</h1>
        <div class="summary">
            <p><strong>Baseline:</strong> <code>{payload["baseline"]["run_id"]}</code> →
            <span class="{"pass" if payload["baseline"]["overall_result"] == "PASS" else "fail"}">{payload["baseline"]["overall_result"]}</span></p>
            <p><strong>Candidate:</strong> <code>{payload["candidate"]["run_id"]}</code> →
            <span class="{"pass" if payload["candidate"]["overall_result"] == "PASS" else "fail"}">{payload["candidate"]["overall_result"]}</span></p>
        </div>

        <h2>⚠️ Regressions</h2>
        {regressions_section}

        <h2>📈 Improvements</h2>
        {improvements_section}

        <h2>Detailed Metrics</h2>
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Baseline</th>
                    <th>Candidate</th>
                    <th>Delta</th>
                </tr>
            </thead>
            <tbody>
                {"".join(metrics_rows)}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    return html


def write_compare(
    out_dir: Path,
    baseline_dir: Path,
    candidate_dir: Path,
    formats: Tuple[str, ...] = ("json", "md", "html"),
    deterministic: bool = True,
) -> List[Path]:
    """
    Generate comparison reports in specified formats.

    Args:
        out_dir: Output directory for comparison reports
        baseline_dir: Baseline run directory
        candidate_dir: Candidate run directory
        formats: Output formats ("json", "md", "html")
        deterministic: Enforce deterministic output (no timestamps)

    Returns:
        List of created file paths

    Example:
        >>> write_compare(
        ...     Path("results/compare"),
        ...     Path("results/run_baseline"),
        ...     Path("results/run_candidate")
        ... )
        [Path("results/compare/compare.json"), ...]
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate comparison payload
    payload = compare_runs(baseline_dir, candidate_dir)

    # Write outputs
    created_files = []

    if "json" in formats:
        json_path = out_dir / "compare.json"
        with open(json_path, "w") as f:
            f.write(render_compare_json(payload))
        created_files.append(json_path)

    if "md" in formats:
        md_path = out_dir / "compare.md"
        with open(md_path, "w") as f:
            f.write(render_compare_md(payload))
        created_files.append(md_path)

    if "html" in formats:
        html_path = out_dir / "compare.html"
        with open(html_path, "w") as f:
            f.write(render_compare_html(payload))
        created_files.append(html_path)

    return created_files
