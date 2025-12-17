# src/analytics/__init__.py
"""
Analytics-Module für Auswertung der Experiment-Registry
(Leaderboards, Risiko-Analysen, Notebook-Helper, Experiment-Analyse, Explorer, etc.).
"""

from .experiments_analysis import (
    MarketScanSummary,
    PortfolioSummary,
    StrategySummary,
    SweepSummary,
    compare_strategies,
    filter_backtest_runs,
    filter_market_scans,
    filter_portfolio_backtest_runs,
    filter_sweeps,
    load_experiments_df_filtered,
    summarize_market_scans,
    summarize_portfolios,
    summarize_strategies,
    summarize_sweeps,
    top_runs_by_metric,
    write_markdown_report,
    write_portfolio_markdown_report,
    write_top_runs_markdown_report,
)

# Phase 22: Experiment & Metrics Explorer
from .explorer import (
    ExperimentExplorer,
    ExperimentFilter,
    ExperimentSummary,
    RankedExperiment,
    SweepOverview,
    get_explorer,
    quick_list,
    quick_rank,
    quick_sweep_summary,
)
from .leaderboard import (
    build_standard_leaderboards,
)
from .leaderboard import (
    load_experiments_df as load_experiments_df_leaderboard,
)
from .notebook_helpers import (
    describe_metric_distribution,
    filter_experiments,
    filter_portfolio_runs,
    load_experiments,
    load_sweep,
    print_headline,
    sweep_heatmap,
    sweep_scatter,
    top_portfolios,
)
from .portfolio_builder import (
    PortfolioCandidate,
    PortfolioComponentCandidate,
    build_multiple_portfolio_candidates,
    build_portfolio_candidates_from_sweeps_and_scans,
    format_portfolio_candidate_summary,
    select_top_market_scan_components,
    select_top_sweep_components,
    write_portfolio_candidate_to_toml,
)

# Phase 19: Regime-Analyse & Robustheits-Tools
from .regimes import (
    RegimeAnalysisResult,
    RegimeConfig,
    RegimeLabel,
    RegimeStats,
    SweepRobustnessResult,
    analyze_experiment_regimes,
    analyze_regimes_from_equity,
    compute_sweep_robustness,
    create_regime_summary_df,
    detect_regimes,
    format_regime_stats_table,
    get_regime_distribution,
    load_regime_config,
)
from .risk_monitor import (
    RiskPolicy,
    aggregate_portfolio_risk,
    aggregate_strategy_risk,
    annotate_runs_with_risk,
    filter_by_lookback,
)
from .risk_monitor import (
    load_experiments_df as load_experiments_df_risk,
)

__all__ = [
    "ExperimentExplorer",
    # Explorer (Phase 22)
    "ExperimentFilter",
    "ExperimentSummary",
    "MarketScanSummary",
    "PortfolioCandidate",
    # Portfolio Builder
    "PortfolioComponentCandidate",
    "PortfolioSummary",
    "RankedExperiment",
    "RegimeAnalysisResult",
    # Regimes (Phase 19)
    "RegimeConfig",
    "RegimeLabel",
    "RegimeStats",
    # Risk Monitor
    "RiskPolicy",
    # Experiments Analysis
    "StrategySummary",
    "SweepOverview",
    "SweepRobustnessResult",
    "SweepSummary",
    "aggregate_portfolio_risk",
    "aggregate_strategy_risk",
    "analyze_experiment_regimes",
    "analyze_regimes_from_equity",
    "annotate_runs_with_risk",
    "build_multiple_portfolio_candidates",
    "build_portfolio_candidates_from_sweeps_and_scans",
    "build_standard_leaderboards",
    "compare_strategies",
    "compute_sweep_robustness",
    "create_regime_summary_df",
    "describe_metric_distribution",
    "detect_regimes",
    "filter_backtest_runs",
    "filter_by_lookback",
    "filter_experiments",
    "filter_market_scans",
    "filter_portfolio_backtest_runs",
    "filter_portfolio_runs",
    "filter_sweeps",
    "format_portfolio_candidate_summary",
    "format_regime_stats_table",
    "get_explorer",
    "get_regime_distribution",
    # Notebook Helpers
    "load_experiments",
    "load_experiments_df_filtered",
    # Leaderboard
    "load_experiments_df_leaderboard",
    "load_experiments_df_risk",
    "load_regime_config",
    "load_sweep",
    "print_headline",
    "quick_list",
    "quick_rank",
    "quick_sweep_summary",
    "select_top_market_scan_components",
    "select_top_sweep_components",
    "summarize_market_scans",
    "summarize_portfolios",
    "summarize_strategies",
    "summarize_sweeps",
    "sweep_heatmap",
    "sweep_scatter",
    "top_portfolios",
    "top_runs_by_metric",
    "write_markdown_report",
    "write_portfolio_candidate_to_toml",
    "write_portfolio_markdown_report",
    "write_top_runs_markdown_report",
]
