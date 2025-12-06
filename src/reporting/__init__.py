# src/reporting/__init__.py
"""
Peak_Trade Reporting Module (Phase 16D + Phase 21 + Phase 30 + Phase 32)
=========================================================================

Bietet Reporting-Funktionen fuer Execution-Daten aus Backtests,
HTML-Report-Generierung und Markdown-Reports.

Module:
- execution_reports: ExecutionStats und Analyse-Funktionen (Phase 16D)
- execution_plots: Visualisierungen fuer Execution-Daten (optional)
- html_reports: HTML-Report-Generierung (Phase 21)
- base: Markdown Report-Typen und Helper (Phase 30)
- plots: Zentrale Plot-Funktionen (Phase 30)
- backtest_report: Backtest-Report-Generierung (Phase 30)
- experiment_report: Experiment/Sweep-Report-Generierung (Phase 30)
- live_run_report: Live/Shadow Run Report-Generierung (Phase 32)
"""
from .execution_reports import (
    ExecutionStats,
    from_execution_logs,
    from_execution_results,
    from_backtest_result,
    format_execution_stats,
)

# Phase 21: HTML Reporting v2
from .html_reports import (
    ReportFigure,
    ReportTable,
    ReportSection as HtmlReportSection,
    HtmlReport,
    HtmlReportBuilder,
    plot_equity_curve,
    plot_drawdown,
    plot_metric_distribution,
    plot_sweep_scatter,
    build_quick_experiment_report,
    build_quick_sweep_report,
)

# Phase 30: Markdown Reporting
from .base import (
    Report,
    ReportSection,
    df_to_markdown,
    dict_to_markdown_table,
    format_metric,
)

from .plots import (
    save_line_plot,
    save_equity_plot,
    save_drawdown_plot,
    save_heatmap,
    save_scatter_plot,
    save_histogram,
    save_equity_with_regimes,
)

from .backtest_report import (
    build_backtest_summary_section,
    build_trade_stats_section,
    build_parameters_section,
    build_equity_plot,
    build_drawdown_plot,
    build_backtest_report,
    save_backtest_report,
    build_quick_backtest_report,
)

from .experiment_report import (
    summarize_experiment_results,
    find_best_params,
    build_experiment_summary_section,
    build_top_runs_section,
    build_best_params_section,
    build_experiment_report,
    save_experiment_report,
    load_experiment_results,
)

# Phase 32: Live Run Reports
from .live_run_report import (
    build_live_run_report,
    load_and_build_report,
    save_report,
)

__all__ = [
    # Execution Reports (Phase 16D)
    "ExecutionStats",
    "from_execution_logs",
    "from_execution_results",
    "from_backtest_result",
    "format_execution_stats",
    # HTML Reports (Phase 21)
    "ReportFigure",
    "ReportTable",
    "HtmlReportSection",
    "HtmlReport",
    "HtmlReportBuilder",
    "plot_equity_curve",
    "plot_drawdown",
    "plot_metric_distribution",
    "plot_sweep_scatter",
    "build_quick_experiment_report",
    "build_quick_sweep_report",
    # Phase 30: Markdown Reporting - Base
    "Report",
    "ReportSection",
    "df_to_markdown",
    "dict_to_markdown_table",
    "format_metric",
    # Phase 30: Plots
    "save_line_plot",
    "save_equity_plot",
    "save_drawdown_plot",
    "save_heatmap",
    "save_scatter_plot",
    "save_histogram",
    "save_equity_with_regimes",
    # Phase 30: Backtest Reports
    "build_backtest_summary_section",
    "build_trade_stats_section",
    "build_parameters_section",
    "build_equity_plot",
    "build_drawdown_plot",
    "build_backtest_report",
    "save_backtest_report",
    "build_quick_backtest_report",
    # Phase 30: Experiment Reports
    "summarize_experiment_results",
    "find_best_params",
    "build_experiment_summary_section",
    "build_top_runs_section",
    "build_best_params_section",
    "build_experiment_report",
    "save_experiment_report",
    "load_experiment_results",
    # Phase 32: Live Run Reports
    "build_live_run_report",
    "load_and_build_report",
    "save_report",
]
