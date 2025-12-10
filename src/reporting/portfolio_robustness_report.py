# src/reporting/portfolio_robustness_report.py
"""
Peak_Trade Portfolio-Robustness Reporting (Phase 47)
====================================================

Reporting-Funktionen fuer Portfolio-Level Robustness-Analysen.

Komponenten:
- build_portfolio_robustness_report: Erstellt kompletten Portfolio-Robustness-Report
- Integration mit bestehender Report-Infrastruktur (Report, ReportSection)

Usage:
    from src.reporting.portfolio_robustness_report import build_portfolio_robustness_report
    from src.experiments.portfolio_robustness import PortfolioRobustnessResult

    result = run_portfolio_robustness(config, returns_loader)
    paths = build_portfolio_robustness_report(
        result,
        title="RSI Portfolio Robustness",
        output_dir=Path("reports/portfolio_robustness"),
        format="both",
    )
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import pandas as pd

from .base import Report, ReportSection, df_to_markdown, dict_to_markdown_table

try:
    import matplotlib.pyplot as plt
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _format_metric_value(value: float, metric_name: str) -> str:
    """Formatiert Metrik-Werte kontextabhaengig."""
    metric_lower = metric_name.lower()

    # Prozent-Metriken
    if any(pm in metric_lower for pm in ["return", "drawdown", "cagr", "volatility"]):
        return f"{value * 100:+.2f}%"

    # Integer-Metriken
    if any(im in metric_lower for im in ["trades", "count", "winning", "losing"]):
        return f"{int(value):+d}" if value != int(value) else str(int(value))

    # Standard
    if abs(value) < 0.0001:
        return "~0"
    elif abs(value) >= 100:
        return f"{value:+.1f}"
    else:
        return f"{value:+.4f}"


def _create_portfolio_equity_plot(
    returns: pd.Series,
    output_path: Path,
    title: str = "Portfolio Equity Curve",
) -> Optional[Path]:
    """
    Erstellt einen Portfolio-Equity-Plot.

    Args:
        returns: Portfolio-Returns
        output_path: Pfad fuer das Bild
        title: Plot-Titel

    Returns:
        Pfad zum Plot oder None bei Fehler
    """
    if not MATPLOTLIB_AVAILABLE:
        return None

    try:
        equity = (1 + returns).cumprod() * 10000

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(range(len(equity)), equity.values, color="#2196F3", linewidth=1.5)
        ax.set_title(title)
        ax.set_xlabel("Bars")
        ax.set_ylabel("Equity")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close(fig)

        return output_path

    except Exception:
        plt.close("all")
        return None


# =============================================================================
# REPORT BUILDING
# =============================================================================


def build_portfolio_robustness_report(
    result: "PortfolioRobustnessResult",  # Forward reference  # noqa: F821
    *,
    title: str,
    output_dir: Path,
    format: Literal["md", "html", "both"] = "both",
) -> Dict[str, Path]:
    """
    Erzeugt einen Portfolio-Robustness-Report mit Baseline-, Monte-Carlo- und Stress-Test-Ergebnissen.

    Args:
        result: PortfolioRobustnessResult aus run_portfolio_robustness
        title: Report-Titel
        output_dir: Zielverzeichnis fuer Reports und Plots
        format: Output-Format ("md", "html", oder "both")

    Returns:
        Dict mit Pfaden, z.B. {"md": path_to_md, "html": path_to_html}

    Example:
        >>> from src.experiments.portfolio_robustness import run_portfolio_robustness
        >>> result = run_portfolio_robustness(config, returns_loader)
        >>> paths = build_portfolio_robustness_report(
        ...     result,
        ...     title="RSI Portfolio Robustness",
        ...     output_dir=Path("reports/portfolio_robustness"),
        ...     format="both",
        ... )
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    portfolio = result.portfolio

    # Erstelle Report
    report = Report(
        title=title,
        metadata={
            "portfolio_name": portfolio.name,
            "num_components": len(portfolio.components),
            "has_monte_carlo": result.mc_results is not None,
            "has_stress_tests": result.stress_results is not None,
        },
    )

    # 1. Overview Section
    overview_lines = [
        f"- **Portfolio-Name:** {portfolio.name}",
        f"- **Anzahl Komponenten:** {len(portfolio.components)}",
        f"- **Portfolio-Bars:** {len(result.portfolio_returns)}",
        "",
        "Dieser Report analysiert die Robustheit eines Multi-Strategy-Portfolios auf Basis von ",
        "Top-N-Konfigurationen aus Sweeps.",
    ]

    report.add_section(ReportSection(
        title="Overview",
        content_markdown="\n".join(overview_lines),
    ))

    # 2. Portfolio Composition Section
    component_data = []
    for component in portfolio.components:
        component_data.append({
            "Strategy": component.strategy_name,
            "Config ID": component.config_id,
            "Weight": f"{component.weight:.1%}",
        })

    if component_data:
        df_components = pd.DataFrame(component_data)
        components_content = df_to_markdown(df_components, float_format=".4f")
        report.add_section(ReportSection(
            title="Portfolio Composition",
            content_markdown=components_content,
        ))

    # 3. Baseline Metrics Section
    baseline_content = dict_to_markdown_table(
        result.baseline_metrics,
        key_header="Metric",
        value_header="Baseline Value",
        float_format=".4f",
    )
    report.add_section(ReportSection(
        title="Baseline Metrics",
        content_markdown=baseline_content,
    ))

    # 4. Monte-Carlo Results (optional)
    if result.mc_results:
        mc_lines = [
            f"- **Monte-Carlo Runs:** {result.mc_results['num_runs']}",
            f"- **Methode:** {result.mc_results['method']}",
            "",
        ]

        # Quantile-Tabelle
        quantile_data = []
        for metric_name, quantiles in result.mc_results.get("metric_quantiles", {}).items():
            quantile_data.append({
                "Metric": metric_name,
                "p5": f"{quantiles.get('p5', 0):.4f}",
                "p25": f"{quantiles.get('p25', 0):.4f}",
                "p50": f"{quantiles.get('p50', 0):.4f}",
                "p75": f"{quantiles.get('p75', 0):.4f}",
                "p95": f"{quantiles.get('p95', 0):.4f}",
            })

        if quantile_data:
            df_quantiles = pd.DataFrame(quantile_data)
            mc_lines.append("### Metric Quantiles")
            mc_lines.append("")
            mc_lines.append(df_to_markdown(df_quantiles, float_format=".4f"))

        report.add_section(ReportSection(
            title="Monte-Carlo Results",
            content_markdown="\n".join(mc_lines),
        ))

    # 5. Stress-Test Results (optional)
    if result.stress_results:
        stress_lines = [
            "### Stress-Scenario Comparison",
            "",
        ]

        scenario_data = []
        baseline_metrics = result.stress_results.get("baseline_metrics", {})
        for scenario in result.stress_results.get("scenarios", []):
            row = {
                "Scenario": scenario["scenario_type"],
                "Severity": f"{scenario['severity']:.0%}",
            }

            # Wichtige Metriken hinzufuegen
            for metric in ["sharpe", "max_drawdown", "total_return", "cagr"]:
                if metric in baseline_metrics:
                    diff = scenario["diff_metrics"].get(metric, 0.0)
                    row[f"Δ {metric}"] = _format_metric_value(diff, metric)

            scenario_data.append(row)

        if scenario_data:
            df_scenarios = pd.DataFrame(scenario_data)
            stress_lines.append(df_to_markdown(df_scenarios, float_format=".4f"))

        report.add_section(ReportSection(
            title="Stress-Test Results",
            content_markdown="\n".join(stress_lines),
        ))

    # 6. Visualizations (optional)
    charts_content: List[str] = []

    if MATPLOTLIB_AVAILABLE:
        # Portfolio-Equity-Plot
        plot_path = output_dir / "portfolio_equity.png"
        saved_path = _create_portfolio_equity_plot(
            result.portfolio_returns,
            plot_path,
            title=f"Portfolio Equity: {portfolio.name}",
        )

        if saved_path:
            rel_path = "portfolio_equity.png"
            charts_content.append(
                f"### Portfolio Equity Curve\n\n![Portfolio Equity]({rel_path})"
            )

    if charts_content:
        report.add_section(ReportSection(
            title="Visualizations",
            content_markdown="\n\n".join(charts_content),
        ))

    # 7. Interpretation Section
    interpretation_lines = [
        "### Interpretation der Ergebnisse",
        "",
        "**Portfolio-Level-Analyse:**",
        "- Portfolio-Returns sind gewichtete Summen der Einzel-Strategie-Returns",
        "- Diversifikation kann Risiko reduzieren, aber auch Rendite dämpfen",
        "",
        "**Monte-Carlo-Ergebnisse:**",
        "- Quantilen (p5, p50, p95) zeigen Unsicherheit in Portfolio-Kennzahlen",
        "- Robustes Portfolio sollte enge Quantilen-Bänder haben",
        "",
        "**Stress-Test-Ergebnisse:**",
        "- Delta-Metriken zeigen Auswirkung von Extremereignissen auf Portfolio",
        "- Portfolio sollte auch unter Stress noch akzeptable Metriken zeigen",
        "",
        "**Empfehlungen:**",
        "- Prüfe Korrelationen zwischen Portfolio-Komponenten",
        "- Diversifikation funktioniert nur, wenn Komponenten nicht zu stark korreliert sind",
        "- Stress-Tests helfen, Schwachstellen im Portfolio zu identifizieren",
    ]

    report.add_section(ReportSection(
        title="Interpretation",
        content_markdown="\n".join(interpretation_lines),
    ))

    # Speichere Report
    paths: Dict[str, Path] = {}

    if format in ("md", "both"):
        md_path = output_dir / "portfolio_robustness_report.md"
        md_path.write_text(report.to_markdown(), encoding="utf-8")
        paths["md"] = md_path

    if format in ("html", "both"):
        html_path = output_dir / "portfolio_robustness_report.html"
        html_path.write_text(report.to_html(), encoding="utf-8")
        paths["html"] = html_path

    return paths







