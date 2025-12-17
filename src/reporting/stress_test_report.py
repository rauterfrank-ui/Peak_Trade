# src/reporting/stress_test_report.py
"""
Peak_Trade Stress-Test Reporting (Phase 46)
============================================

Reporting-Funktionen fuer Stress-Test-Analysen.

Komponenten:
- build_stress_test_report: Erstellt kompletten Stress-Test-Report
- Integration mit bestehender Report-Infrastruktur (Report, ReportSection)

Usage:
    from src.reporting.stress_test_report import build_stress_test_report
    from src.experiments.stress_tests import StressTestSuiteResult

    suite = run_stress_test_suite(returns, scenarios, stats_fn)
    paths = build_stress_test_report(
        suite,
        title="RSI Reversion Stress-Tests",
        output_dir=Path("reports/stress/rsi_reversion"),
        format="both",
    )
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import pandas as pd

from .base import Report, ReportSection, df_to_markdown, dict_to_markdown_table

try:
    import matplotlib
    import matplotlib.pyplot as plt

    matplotlib.use("Agg")  # Non-interactive backend
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _format_scenario_type(scenario_type: str) -> str:
    """Formatiert den Szenario-Typ f�r bessere Lesbarkeit."""
    mapping = {
        "single_crash_bar": "Single Crash Bar",
        "vol_spike": "Volatility Spike",
        "drawdown_extension": "Drawdown Extension",
        "gap_down_open": "Gap-Down Open",
    }
    return mapping.get(scenario_type, scenario_type)


def _format_metric_value(value: float, metric_name: str) -> str:
    """Formatiert Metrik-Werte kontextabh�ngig."""
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


def _create_equity_comparison_plot(
    returns: pd.Series,
    stressed_returns: pd.Series,
    scenario_name: str,
    output_path: Path,
) -> Path | None:
    """
    Erstellt einen Equity-Kurven-Vergleich (Baseline vs. Stressed).

    Args:
        returns: Baseline-Returns
        stressed_returns: Gestresste Returns
        scenario_name: Name des Szenarios
        output_path: Pfad f�r das Bild

    Returns:
        Pfad zum Plot oder None bei Fehler
    """
    if not MATPLOTLIB_AVAILABLE:
        return None

    try:
        # Berechne Equity-Kurven
        equity_baseline = (1 + returns).cumprod() * 10000
        equity_stressed = (1 + stressed_returns).cumprod() * 10000

        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot beide Kurven
        ax.plot(
            range(len(equity_baseline)),
            equity_baseline.values,
            label="Baseline",
            color="#2196F3",
            linewidth=1.5,
        )
        ax.plot(
            range(len(equity_stressed)),
            equity_stressed.values,
            label=f"Stressed ({scenario_name})",
            color="#F44336",
            linewidth=1.5,
            linestyle="--",
        )

        ax.set_title(f"Equity Comparison: {scenario_name}")
        ax.set_xlabel("Bars")
        ax.set_ylabel("Equity")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Speichern
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close(fig)

        return output_path

    except Exception:
        # Plot-Fehler nicht fatal
        plt.close("all")
        return None


# =============================================================================
# REPORT BUILDING
# =============================================================================


def build_stress_test_report(
    suite: StressTestSuiteResult,  # Forward reference
    *,
    title: str,
    output_dir: Path,
    format: Literal["md", "html", "both"] = "both",
) -> dict[str, Path]:
    """
    Erzeugt einen Stress-Test-Report mit Baseline- und Szenario-Kennzahlen.

    Args:
        suite: StressTestSuiteResult aus run_stress_test_suite
        title: Report-Titel
        output_dir: Zielverzeichnis f�r Reports und Plots
        format: Output-Format ("md", "html", oder "both")

    Returns:
        Dict mit Pfaden, z.B. {"md": path_to_md, "html": path_to_html}

    Example:
        >>> from src.experiments.stress_tests import run_stress_test_suite, StressScenarioConfig
        >>> suite = run_stress_test_suite(returns, [StressScenarioConfig(...)], stats_fn)
        >>> paths = build_stress_test_report(
        ...     suite,
        ...     title="RSI Stress-Tests",
        ...     output_dir=Path("reports/stress"),
        ...     format="both",
        ... )
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Erstelle Report
    report = Report(
        title=title,
        metadata={
            "scenarios_count": len(suite.scenario_results),
            "baseline_bars": len(suite.returns),
        },
    )

    # 1. Overview Section
    overview_lines = [
        f"- **Anzahl Szenarien:** {len(suite.scenario_results)}",
        f"- **Baseline-L�nge:** {len(suite.returns)} Bars",
        "",
        "Dieser Report vergleicht Baseline-Kennzahlen mit Stress-Szenario-Ergebnissen. ",
        "Negative Differenzen (rot markiert) zeigen Verschlechterungen unter Stress.",
    ]
    report.add_section(ReportSection(
        title="Overview",
        content_markdown="\n".join(overview_lines),
    ))

    # 2. Baseline Metrics Section
    baseline_content = dict_to_markdown_table(
        suite.baseline_metrics,
        key_header="Metric",
        value_header="Baseline Value",
        float_format=".4f",
    )
    report.add_section(ReportSection(
        title="Baseline Metrics",
        content_markdown=baseline_content,
    ))

    # 3. Scenario Comparison Table
    if suite.scenario_results:
        # Erstelle Vergleichstabelle
        comparison_data: list[dict[str, Any]] = []

        # W�hle wichtige Metriken f�r die �bersicht
        key_metrics = ["sharpe", "max_drawdown", "total_return", "cagr", "volatility"]
        available_key_metrics = [
            m for m in key_metrics if m in suite.baseline_metrics
        ]

        for result in suite.scenario_results:
            row: dict[str, Any] = {
                "Scenario": _format_scenario_type(result.scenario.scenario_type),
                "Severity": f"{result.scenario.severity:.0%}",
            }

            # F�ge Metrik-Differenzen hinzu
            for metric in available_key_metrics:
                diff = result.diff_metrics.get(metric, 0.0)
                row[f"�_{metric}"] = _format_metric_value(diff, metric)

            comparison_data.append(row)

        if comparison_data:
            df_comparison = pd.DataFrame(comparison_data)
            comparison_content = df_to_markdown(df_comparison, float_format=".4f")
            report.add_section(ReportSection(
                title="Scenario Comparison (� = Stressed - Baseline)",
                content_markdown=comparison_content,
            ))

    # 4. Detailed Scenario Results
    detailed_lines: list[str] = []

    for i, result in enumerate(suite.scenario_results, 1):
        scenario_type = _format_scenario_type(result.scenario.scenario_type)
        detailed_lines.append(f"### {i}. {scenario_type}")
        detailed_lines.append("")
        detailed_lines.append("**Configuration:**")
        detailed_lines.append(f"- Severity: {result.scenario.severity:.0%}")
        detailed_lines.append(f"- Window: {result.scenario.window}")
        detailed_lines.append(f"- Position: {result.scenario.position}")
        detailed_lines.append("")

        # Tabelle mit Baseline | Stressed | Diff
        table_data: list[dict[str, str]] = []
        for metric in sorted(result.baseline_metrics.keys()):
            baseline_val = result.baseline_metrics.get(metric, 0.0)
            stressed_val = result.stressed_metrics.get(metric, 0.0)
            diff_val = result.diff_metrics.get(metric, 0.0)

            table_data.append({
                "Metric": metric,
                "Baseline": f"{baseline_val:.4f}",
                "Stressed": f"{stressed_val:.4f}",
                "� (Diff)": _format_metric_value(diff_val, metric),
            })

        if table_data:
            df_detail = pd.DataFrame(table_data)
            detailed_lines.append(df_to_markdown(df_detail, float_format=".4f"))
            detailed_lines.append("")

    if detailed_lines:
        report.add_section(ReportSection(
            title="Detailed Scenario Results",
            content_markdown="\n".join(detailed_lines),
        ))

    # 5. Visualizations (optional)
    charts_content: list[str] = []

    if MATPLOTLIB_AVAILABLE and suite.scenario_results:
        # Import here to avoid circular import
        from src.experiments.stress_tests import apply_stress_scenario_to_returns

        # Erstelle Equity-Vergleichs-Plots f�r bis zu 2 Szenarien
        for result in suite.scenario_results[:2]:
            scenario_type = result.scenario.scenario_type
            plot_name = f"equity_comparison_{scenario_type}.png"
            plot_path = output_dir / plot_name

            # Wende Szenario erneut an f�r Plot
            stressed_returns = apply_stress_scenario_to_returns(
                suite.returns, result.scenario
            )

            saved_path = _create_equity_comparison_plot(
                suite.returns,
                stressed_returns,
                _format_scenario_type(scenario_type),
                plot_path,
            )

            if saved_path:
                rel_path = plot_name  # Relativer Pfad im gleichen Verzeichnis
                charts_content.append(
                    f"### {_format_scenario_type(scenario_type)}\n\n"
                    f"![Equity Comparison]({rel_path})"
                )

    if charts_content:
        report.add_section(ReportSection(
            title="Equity Curve Comparisons",
            content_markdown="\n\n".join(charts_content),
        ))

    # 6. Interpretation Section
    interpretation_lines = [
        "### Interpretation der Ergebnisse",
        "",
        "**Schl�sselmetriken:**",
        "- **Sharpe Ratio:** Ein R�ckgang unter Stress zeigt erh�hte Risiko-/Return-Empfindlichkeit",
        "- **Max Drawdown:** Verst�rkung deutet auf Verletzlichkeit bei Extremereignissen hin",
        "- **CAGR:** Reduktion zeigt Auswirkung auf langfristige Performance",
        "",
        "**Robuste Strategie sollte haben:**",
        "- Moderate Sharpe-Reduktion (< 0.5 Punkte)",
        "- Max-Drawdown-Verschlechterung < 5 Prozentpunkte",
        "- Positive CAGR auch unter Stress",
        "",
        "**Warnsignale:**",
        "- Sharpe wird negativ unter Stress",
        "- Max-Drawdown �bersteigt -30%",
        "- CAGR wird negativ",
    ]

    report.add_section(ReportSection(
        title="Interpretation",
        content_markdown="\n".join(interpretation_lines),
    ))

    # Speichere Report
    paths: dict[str, Path] = {}

    if format in ("md", "both"):
        md_path = output_dir / "stress_test_report.md"
        md_path.write_text(report.to_markdown(), encoding="utf-8")
        paths["md"] = md_path

    if format in ("html", "both"):
        html_path = output_dir / "stress_test_report.html"
        html_path.write_text(report.to_html(), encoding="utf-8")
        paths["html"] = html_path

    return paths







