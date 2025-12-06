# src/analytics/__init__.py
"""
Analytics-Module für Auswertung der Experiment-Registry
(Leaderboards, Risiko-Analysen, Notebook-Helper, Experiment-Analyse, Explorer, etc.).
"""

from .leaderboard import (
    load_experiments_df as load_experiments_df_leaderboard,
    build_standard_leaderboards,
)

from .notebook_helpers import (
    load_experiments,
    filter_experiments,
    describe_metric_distribution,
    load_sweep,
    sweep_scatter,
    sweep_heatmap,
    filter_portfolio_runs,
    top_portfolios,
    print_headline,
)

from .risk_monitor import (
    RiskPolicy,
    load_experiments_df as load_experiments_df_risk,
    filter_by_lookback,
    annotate_runs_with_risk,
    aggregate_strategy_risk,
    aggregate_portfolio_risk,
)

from .experiments_analysis import (
    StrategySummary,
    PortfolioSummary,
    SweepSummary,
    MarketScanSummary,
    load_experiments_df_filtered,
    filter_backtest_runs,
    filter_portfolio_backtest_runs,
    filter_sweeps,
    filter_market_scans,
    summarize_strategies,
    summarize_portfolios,
    summarize_sweeps,
    summarize_market_scans,
    top_runs_by_metric,
    compare_strategies,
    write_markdown_report,
    write_portfolio_markdown_report,
    write_top_runs_markdown_report,
)

from .portfolio_builder import (
    PortfolioComponentCandidate,
    PortfolioCandidate,
    select_top_sweep_components,
    select_top_market_scan_components,
    build_portfolio_candidates_from_sweeps_and_scans,
    build_multiple_portfolio_candidates,
    write_portfolio_candidate_to_toml,
    format_portfolio_candidate_summary,
)

# Phase 22: Experiment & Metrics Explorer
from .explorer import (
    ExperimentFilter,
    ExperimentSummary,
    RankedExperiment,
    SweepOverview,
    ExperimentExplorer,
    get_explorer,
    quick_list,
    quick_rank,
    quick_sweep_summary,
)

# Phase 19: Regime-Analyse & Robustheits-Tools
from .regimes import (
    RegimeConfig,
    RegimeLabel,
    RegimeStats,
    RegimeAnalysisResult,
    SweepRobustnessResult,
    load_regime_config,
    detect_regimes,
    get_regime_distribution,
    analyze_regimes_from_equity,
    analyze_experiment_regimes,
    compute_sweep_robustness,
    format_regime_stats_table,
    create_regime_summary_df,
)

__all__ = [
    # Leaderboard
    "load_experiments_df_leaderboard",
    "build_standard_leaderboards",
    # Notebook Helpers
    "load_experiments",
    "filter_experiments",
    "describe_metric_distribution",
    "load_sweep",
    "sweep_scatter",
    "sweep_heatmap",
    "filter_portfolio_runs",
    "top_portfolios",
    "print_headline",
    # Risk Monitor
    "RiskPolicy",
    "load_experiments_df_risk",
    "filter_by_lookback",
    "annotate_runs_with_risk",
    "aggregate_strategy_risk",
    "aggregate_portfolio_risk",
    # Experiments Analysis
    "StrategySummary",
    "PortfolioSummary",
    "SweepSummary",
    "MarketScanSummary",
    "load_experiments_df_filtered",
    "filter_backtest_runs",
    "filter_portfolio_backtest_runs",
    "filter_sweeps",
    "filter_market_scans",
    "summarize_strategies",
    "summarize_portfolios",
    "summarize_sweeps",
    "summarize_market_scans",
    "top_runs_by_metric",
    "compare_strategies",
    "write_markdown_report",
    "write_portfolio_markdown_report",
    "write_top_runs_markdown_report",
    # Portfolio Builder
    "PortfolioComponentCandidate",
    "PortfolioCandidate",
    "select_top_sweep_components",
    "select_top_market_scan_components",
    "build_portfolio_candidates_from_sweeps_and_scans",
    "build_multiple_portfolio_candidates",
    "write_portfolio_candidate_to_toml",
    "format_portfolio_candidate_summary",
    # Explorer (Phase 22)
    "ExperimentFilter",
    "ExperimentSummary",
    "RankedExperiment",
    "SweepOverview",
    "ExperimentExplorer",
    "get_explorer",
    "quick_list",
    "quick_rank",
    "quick_sweep_summary",
    # Regimes (Phase 19)
    "RegimeConfig",
    "RegimeLabel",
    "RegimeStats",
    "RegimeAnalysisResult",
    "SweepRobustnessResult",
    "load_regime_config",
    "detect_regimes",
    "get_regime_distribution",
    "analyze_regimes_from_equity",
    "analyze_experiment_regimes",
    "compute_sweep_robustness",
    "format_regime_stats_table",
    "create_regime_summary_df",
]
