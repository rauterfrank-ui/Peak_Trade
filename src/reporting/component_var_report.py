"""
Component VaR Report Generator
===============================

Generates HTML, JSON, and CSV reports for Component VaR analysis.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ComponentVaRReportData:
    """Data structure for Component VaR report."""

    run_id: str
    timestamp: str
    total_var: float
    portfolio_value: float
    confidence: float
    horizon: int
    lookback_days: int
    asset_symbols: List[str]
    weights: List[float]
    component_var: List[float]
    contribution_pct: List[float]
    marginal_var: List[float]
    sanity_checks: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ComponentVaRReportGenerator:
    """Generates Component VaR reports in multiple formats."""

    def __init__(self, output_dir: Path):
        """
        Initialize report generator.

        Args:
            output_dir: Directory for report outputs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_reports(self, report_data: ComponentVaRReportData) -> Dict[str, Path]:
        """
        Generate all report formats.

        Args:
            report_data: Report data

        Returns:
            Dictionary mapping format to file path
        """
        outputs = {}

        # JSON Report
        json_path = self.output_dir / "report.json"
        self._generate_json(report_data, json_path)
        outputs["json"] = json_path

        # CSV Table
        csv_path = self.output_dir / "table.csv"
        self._generate_csv(report_data, csv_path)
        outputs["csv"] = csv_path

        # HTML Report
        html_path = self.output_dir / "report.html"
        self._generate_html(report_data, html_path)
        outputs["html"] = html_path

        logger.info(f"Generated reports in: {self.output_dir}")
        return outputs

    def _generate_json(self, data: ComponentVaRReportData, output_path: Path):
        """Generate JSON report."""
        report_dict = data.to_dict()

        # Convert numpy types to Python natives for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj

        # Clean data for JSON
        cleaned = json.loads(json.dumps(report_dict, default=convert_numpy, indent=2))

        with open(output_path, "w") as f:
            json.dump(cleaned, f, indent=2)

        logger.info(f"JSON report: {output_path}")

    def _generate_csv(self, data: ComponentVaRReportData, output_path: Path):
        """Generate CSV table."""
        df = pd.DataFrame(
            {
                "symbol": data.asset_symbols,
                "weight": data.weights,
                "component_var": data.component_var,
                "contribution_pct": data.contribution_pct,
                "marginal_var": data.marginal_var,
            }
        )

        # Sort by contribution (descending)
        df = df.sort_values("contribution_pct", ascending=False)

        df.to_csv(output_path, index=False, float_format="%.6f")
        logger.info(f"CSV table: {output_path}")

    def _generate_html(self, data: ComponentVaRReportData, output_path: Path):
        """Generate HTML report."""
        # Create DataFrame for table
        df = pd.DataFrame(
            {
                "Symbol": data.asset_symbols,
                "Weight": [f"{w:.4f}" for w in data.weights],
                "Component VaR": [f"${cv:,.2f}" for cv in data.component_var],
                "Contribution %": [f"{cp:.2f}%" for cp in data.contribution_pct],
                "Marginal VaR": [f"${mv:,.2f}" for mv in data.marginal_var],
            }
        )

        # Sort by contribution
        df = df.sort_values(
            "Contribution %", key=lambda x: x.str.rstrip("%").astype(float), ascending=False
        )

        # Top contributors
        top_n = 5
        top_contributors = df.head(top_n)

        # Sanity checks status
        sanity_status = "✅ PASS" if data.sanity_checks.get("all_pass", False) else "⚠️ WARNINGS"
        sanity_details = []
        for check, result in data.sanity_checks.items():
            if check != "all_pass":
                status_icon = "✅" if result.get("pass", False) else "❌"
                sanity_details.append(f"{status_icon} {result.get('description', check)}")

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Component VaR Report - {data.run_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 1px solid #ecf0f1;
            padding-bottom: 5px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }}
        .metric-label {{
            font-size: 0.85em;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .sanity-check {{
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .sanity-warning {{
            background: #fff3e0;
            border-left: 4px solid #ff9800;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .highlight {{
            background: #fff9c4;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Component VaR Report</h1>

        <div class="metrics">
            <div class="metric">
                <div class="metric-label">Run ID</div>
                <div class="metric-value" style="font-size: 1em;">{data.run_id}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Portfolio VaR</div>
                <div class="metric-value">${data.total_var:,.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Portfolio Value</div>
                <div class="metric-value">${data.portfolio_value:,.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Confidence Level</div>
                <div class="metric-value">{data.confidence * 100:.1f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Horizon</div>
                <div class="metric-value">{data.horizon} day(s)</div>
            </div>
            <div class="metric">
                <div class="metric-label">Lookback</div>
                <div class="metric-value">{data.lookback_days} days</div>
            </div>
        </div>

        <h2>Top {top_n} Risk Contributors</h2>
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Weight</th>
                    <th>Component VaR</th>
                    <th>Contribution %</th>
                    <th>Marginal VaR</th>
                </tr>
            </thead>
            <tbody>
                {"".join([f'<tr class="highlight"><td>{row["Symbol"]}</td><td>{row["Weight"]}</td><td>{row["Component VaR"]}</td><td>{row["Contribution %"]}</td><td>{row["Marginal VaR"]}</td></tr>' for _, row in top_contributors.iterrows()])}
            </tbody>
        </table>

        <h2>All Assets</h2>
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Weight</th>
                    <th>Component VaR</th>
                    <th>Contribution %</th>
                    <th>Marginal VaR</th>
                </tr>
            </thead>
            <tbody>
                {"".join([f"<tr><td>{row.get('Symbol')}</td><td>{row.get('Weight')}</td><td>{row.get('Component VaR')}</td><td>{row.get('Contribution %')}</td><td>{row.get('Marginal VaR')}</td></tr>" for _, row in df.iterrows()])}
            </tbody>
        </table>

        <h2>Sanity Checks</h2>
        <div class="sanity-check {"sanity-warning" if not data.sanity_checks.get("all_pass", False) else ""}">
            <strong>{sanity_status}</strong>
            <ul>
                {"".join([f"<li>{detail}</li>" for detail in sanity_details])}
            </ul>
        </div>

        <div class="footer">
            <p>Generated: {data.timestamp}</p>
            <p>Peak_Trade Component VaR Report Generator v1.0</p>
        </div>
    </div>
</body>
</html>
"""

        with open(output_path, "w") as f:
            f.write(html_content)

        logger.info(f"HTML report: {output_path}")


def run_sanity_checks(
    weights: np.ndarray,
    component_var: np.ndarray,
    total_var: float,
    asset_symbols: List[str],
) -> Dict[str, Any]:
    """
    Run sanity checks on Component VaR results.

    Args:
        weights: Asset weights
        component_var: Component VaR values
        total_var: Total portfolio VaR
        asset_symbols: Asset symbols

    Returns:
        Dictionary with check results
    """
    checks = {}

    # Check 1: Weights sum to ~1
    weight_sum = np.sum(weights)
    checks["weights_sum"] = {
        "pass": bool(np.isclose(weight_sum, 1.0, atol=0.01)),
        "value": float(weight_sum),
        "description": f"Weights sum to 1.0: {weight_sum:.4f}",
    }

    # Check 2: No NaN values
    has_nan = np.any(np.isnan(component_var))
    checks["no_nans"] = {
        "pass": bool(not has_nan),
        "value": bool(not has_nan),
        "description": f"No NaN values: {'✓' if not has_nan else '✗'}",
    }

    # Check 3: Euler property (sum of components = total)
    component_sum = np.sum(component_var)
    euler_check = np.isclose(component_sum, total_var, rtol=0.01)
    checks["euler_property"] = {
        "pass": bool(euler_check),
        "value": float(component_sum),
        "description": f"Euler property: Σ CompVaR = Total VaR ({component_sum:.2f} vs {total_var:.2f})",
    }

    # Check 4: Sufficient data
    sufficient_data = len(asset_symbols) >= 2
    checks["sufficient_assets"] = {
        "pass": bool(sufficient_data),
        "value": len(asset_symbols),
        "description": f"Sufficient assets: {len(asset_symbols)} ≥ 2",
    }

    # Overall pass
    checks["all_pass"] = all(
        check["pass"] for check in checks.values() if isinstance(check, dict) and "pass" in check
    )

    return checks
