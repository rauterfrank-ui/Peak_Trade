# tests/test_research_cli.py
"""
Tests für scripts/research_cli.py (Unified Research-CLI)
========================================================

Testet die Unified Research-CLI ohne echte Sweeps/Reports auszuführen.
"""
import argparse

# Importiere research_cli
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import scripts.research_cli as research_cli

# =============================================================================
# PARSER TESTS
# =============================================================================


class TestBuildParser:
    """Tests für build_parser()."""

    def test_build_parser_creates_subparsers(self):
        """Parser enthält alle erwarteten Subcommands."""
        parser = research_cli.build_parser()

        # Prüfe dass Subparsers existieren
        assert hasattr(parser, "_subparsers")

        # Prüfe dass alle Commands vorhanden sind
        subparsers_action = None
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                subparsers_action = action
                break

        assert subparsers_action is not None
        assert "sweep" in subparsers_action.choices
        assert "report" in subparsers_action.choices
        assert "promote" in subparsers_action.choices
        assert "walkforward" in subparsers_action.choices
        assert "montecarlo" in subparsers_action.choices
        assert "stress" in subparsers_action.choices
        assert "portfolio" in subparsers_action.choices
        assert "pipeline" in subparsers_action.choices

    def test_sweep_subparser_has_required_args(self):
        """Sweep-Subparser hat erwartete Argumente."""
        parser = research_cli.build_parser()
        args = parser.parse_args(["sweep", "--sweep-name", "test", "--config", "config/config.toml"])

        assert args.command == "sweep"
        assert args.sweep_name == "test"
        assert args.config == "config/config.toml"

    def test_report_subparser_has_required_args(self):
        """Report-Subparser hat erwartete Argumente."""
        parser = research_cli.build_parser()
        args = parser.parse_args(["report", "--sweep-name", "test"])

        assert args.command == "report"
        assert args.sweep_name == "test"

    def test_promote_subparser_has_required_args(self):
        """Promote-Subparser hat erwartete Argumente."""
        parser = research_cli.build_parser()
        args = parser.parse_args(["promote", "--sweep-name", "test", "--top-n", "5"])

        assert args.command == "promote"
        assert args.sweep_name == "test"
        assert args.top_n == 5

    def test_walkforward_subparser_has_required_args(self):
        """Walk-Forward-Subparser hat erwartete Argumente."""
        parser = research_cli.build_parser()
        args = parser.parse_args([
            "walkforward",
            "--sweep-name", "test",
            "--train-window", "90d",
            "--test-window", "30d",
            "--use-dummy-data",
        ])

        assert args.command == "walkforward"
        assert args.sweep_name == "test"
        assert args.train_window == "90d"
        assert args.test_window == "30d"
        assert args.use_dummy_data is True

    def test_montecarlo_subparser_has_required_args(self):
        """Monte-Carlo-Subparser hat erwartete Argumente."""
        parser = research_cli.build_parser()
        args = parser.parse_args([
            "montecarlo",
            "--sweep-name", "test",
            "--config", "config/config.toml",
            "--top-n", "3",
            "--num-runs", "1000",
        ])

        assert args.command == "montecarlo"
        assert args.sweep_name == "test"
        assert args.config == "config/config.toml"
        assert args.top_n == 3
        assert args.num_runs == 1000

    def test_stress_subparser_has_required_args(self):
        """Stress-Test-Subparser hat erwartete Argumente."""
        parser = research_cli.build_parser()
        args = parser.parse_args([
            "stress",
            "--sweep-name", "test",
            "--config", "config/config.toml",
            "--top-n", "3",
            "--scenarios", "single_crash_bar", "vol_spike",
        ])

        assert args.command == "stress"
        assert args.sweep_name == "test"
        assert args.config == "config/config.toml"
        assert args.top_n == 3
        assert "single_crash_bar" in args.scenarios
        assert "vol_spike" in args.scenarios

    def test_pipeline_subparser_has_required_args(self):
        """Pipeline-Subparser hat erwartete Argumente."""
        parser = research_cli.build_parser()
        args = parser.parse_args([
            "pipeline",
            "--sweep-name", "test",
            "--config", "config/config.toml",
        ])

        assert args.command == "pipeline"
        assert args.sweep_name == "test"
        assert args.config == "config/config.toml"


# =============================================================================
# MAIN FUNCTION TESTS
# =============================================================================


class TestMain:
    """Tests für main()."""

    @patch("scripts.research_cli.run_sweep_from_args")
    def test_main_sweep_calls_sweep_runner(self, mock_run_sweep):
        """Sweep-Command ruft run_sweep_from_args auf."""
        mock_run_sweep.return_value = 0

        exit_code = research_cli.main(["sweep", "--sweep-name", "dummy", "--config", "config/config.toml"])

        assert exit_code == 0
        assert mock_run_sweep.called
        call_args = mock_run_sweep.call_args[0][0]
        assert call_args.command == "sweep"
        assert call_args.sweep_name == "dummy"

    @patch("scripts.research_cli.run_report_from_args")
    def test_main_report_calls_report_runner(self, mock_run_report):
        """Report-Command ruft run_report_from_args auf."""
        mock_run_report.return_value = 0

        exit_code = research_cli.main(["report", "--sweep-name", "dummy"])

        assert exit_code == 0
        assert mock_run_report.called
        call_args = mock_run_report.call_args[0][0]
        assert call_args.command == "report"
        assert call_args.sweep_name == "dummy"

    @patch("scripts.research_cli.run_promote_from_args")
    def test_main_promote_calls_promote_runner(self, mock_run_promote):
        """Promote-Command ruft run_promote_from_args auf."""
        mock_run_promote.return_value = 0

        exit_code = research_cli.main(["promote", "--sweep-name", "dummy", "--top-n", "5"])

        assert exit_code == 0
        assert mock_run_promote.called
        call_args = mock_run_promote.call_args[0][0]
        assert call_args.command == "promote"
        assert call_args.sweep_name == "dummy"

    @patch("scripts.research_cli.run_walkforward_from_args")
    def test_main_walkforward_calls_walkforward_runner(self, mock_run_walkforward):
        """Walk-Forward-Command ruft run_walkforward_from_args auf."""
        mock_run_walkforward.return_value = 0

        exit_code = research_cli.main([
            "walkforward",
            "--sweep-name", "dummy",
            "--train-window", "90d",
            "--test-window", "30d",
            "--use-dummy-data",
        ])

        assert exit_code == 0
        assert mock_run_walkforward.called
        call_args = mock_run_walkforward.call_args[0][0]
        assert call_args.command == "walkforward"
        assert call_args.sweep_name == "dummy"

    @patch("scripts.research_cli.run_montecarlo_from_args")
    def test_main_montecarlo_calls_montecarlo_runner(self, mock_run_montecarlo):
        """Monte-Carlo-Command ruft run_montecarlo_from_args auf."""
        mock_run_montecarlo.return_value = 0

        exit_code = research_cli.main([
            "montecarlo",
            "--sweep-name", "dummy",
            "--config", "config/config.toml",
            "--top-n", "3",
        ])

        assert exit_code == 0
        assert mock_run_montecarlo.called
        call_args = mock_run_montecarlo.call_args[0][0]
        assert call_args.command == "montecarlo"
        assert call_args.sweep_name == "dummy"

    @patch("scripts.research_cli.run_stress_from_args")
    def test_main_stress_calls_stress_runner(self, mock_run_stress):
        """Stress-Test-Command ruft run_stress_from_args auf."""
        mock_run_stress.return_value = 0

        exit_code = research_cli.main([
            "stress",
            "--sweep-name", "dummy",
            "--config", "config/config.toml",
            "--top-n", "3",
        ])

        assert exit_code == 0
        assert mock_run_stress.called
        call_args = mock_run_stress.call_args[0][0]
        assert call_args.command == "stress"
        assert call_args.sweep_name == "dummy"

    @patch("scripts.research_cli.run_portfolio_robustness_from_args")
    def test_main_portfolio_calls_portfolio_runner(self, mock_run_portfolio):
        """Portfolio-Command ruft run_portfolio_robustness_from_args auf."""
        mock_run_portfolio.return_value = 0

        exit_code = research_cli.main([
            "portfolio",
            "--sweep-name", "dummy",
            "--config", "config/config.toml",
            "--top-n", "3",
            "--portfolio-name", "test_portfolio",
        ])

        assert exit_code == 0
        assert mock_run_portfolio.called
        call_args = mock_run_portfolio.call_args[0][0]
        assert call_args.command == "portfolio"
        assert call_args.sweep_name == "dummy"

    def test_portfolio_subparser_has_preset_args(self):
        """Portfolio-Subparser hat --portfolio-preset und --recipes-config Argumente."""
        parser = research_cli.build_parser()
        args = parser.parse_args([
            "portfolio",
            "--portfolio-preset", "rsi_reversion_balanced",
            "--recipes-config", "config/portfolio_recipes.toml",
            "--config", "config/config.toml",
        ])

        assert args.command == "portfolio"
        assert args.portfolio_preset == "rsi_reversion_balanced"
        assert args.recipes_config == "config/portfolio_recipes.toml"

    @patch("scripts.research_cli.run_portfolio_robustness_from_args")
    def test_main_portfolio_with_preset(self, mock_run_portfolio):
        """Portfolio-Command mit --portfolio-preset ruft Runner mit Preset auf."""
        mock_run_portfolio.return_value = 0

        exit_code = research_cli.main([
            "portfolio",
            "--portfolio-preset", "rsi_reversion_balanced",
            "--config", "config/config.toml",
        ])

        assert exit_code == 0
        assert mock_run_portfolio.called
        call_args = mock_run_portfolio.call_args[0][0]
        assert call_args.command == "portfolio"
        assert call_args.portfolio_preset == "rsi_reversion_balanced"

    @patch("scripts.research_cli.run_pipeline")
    def test_main_pipeline_calls_pipeline_runner(self, mock_run_pipeline):
        """Pipeline-Command ruft run_pipeline auf."""
        mock_run_pipeline.return_value = 0

        exit_code = research_cli.main([
            "pipeline",
            "--sweep-name", "dummy",
            "--config", "config/config.toml",
        ])

        assert exit_code == 0
        assert mock_run_pipeline.called

    def test_main_unknown_command_returns_error(self):
        """Unbekanntes Command gibt Fehler zurück."""
        with pytest.raises(SystemExit):
            research_cli.main(["unknown_command"])


# =============================================================================
# PIPELINE TESTS
# =============================================================================


class TestRunPipeline:
    """Tests für run_pipeline()."""

    @patch("scripts.research_cli.run_sweep_from_args")
    @patch("scripts.research_cli.run_report_from_args")
    @patch("scripts.research_cli.run_promote_from_args")
    def test_pipeline_runs_sweep_and_report(self, mock_promote, mock_report, mock_sweep):
        """Pipeline führt Sweep, Report und Promote aus."""
        mock_sweep.return_value = 0
        mock_report.return_value = 0
        mock_promote.return_value = 0

        args = argparse.Namespace(
            sweep_name="test",
            config="config/config.toml",
            format="both",
            with_plots=False,
            top_n=5,
            run_walkforward=False,
            walkforward_train_window=None,
            walkforward_test_window=None,
            walkforward_step_size=None,
            walkforward_use_dummy_data=False,
            walkforward_dummy_bars=1000,
            run_montecarlo=False,
            run_stress_tests=False,
            verbose=False,
        )

        exit_code = research_cli.run_pipeline(args)

        assert exit_code == 0
        assert mock_sweep.called
        assert mock_report.called
        assert mock_promote.called

    @patch("scripts.research_cli.run_sweep_from_args")
    @patch("scripts.research_cli.run_report_from_args")
    @patch("scripts.research_cli.run_promote_from_args")
    def test_pipeline_runs_promotion_when_top_n_set(self, mock_promote, mock_report, mock_sweep):
        """Pipeline führt Promotion aus wenn --top-n gesetzt ist."""
        mock_sweep.return_value = 0
        mock_report.return_value = 0
        mock_promote.return_value = 0

        args = argparse.Namespace(
            sweep_name="test",
            config="config/config.toml",
            format="both",
            with_plots=False,
            top_n=5,
            run_walkforward=False,
            walkforward_train_window=None,
            walkforward_test_window=None,
            walkforward_step_size=None,
            walkforward_use_dummy_data=False,
            walkforward_dummy_bars=1000,
            run_montecarlo=False,
            run_stress_tests=False,
            verbose=False,
        )

        exit_code = research_cli.run_pipeline(args)

        assert exit_code == 0
        assert mock_promote.called

    @patch("scripts.research_cli.run_sweep_from_args")
    @patch("scripts.research_cli.run_report_from_args")
    @patch("scripts.research_cli.run_promote_from_args")
    @patch("scripts.research_cli.run_walkforward_from_args")
    def test_pipeline_runs_walkforward_when_flag_set(self, mock_wf, mock_promote, mock_report, mock_sweep):
        """Pipeline führt Walk-Forward aus wenn --run-walkforward gesetzt ist."""
        mock_sweep.return_value = 0
        mock_report.return_value = 0
        mock_promote.return_value = 0
        mock_wf.return_value = 0

        args = argparse.Namespace(
            sweep_name="test",
            config="config/config.toml",
            format="both",
            with_plots=False,
            top_n=5,
            run_walkforward=True,
            walkforward_train_window="90d",
            walkforward_test_window="30d",
            walkforward_step_size=None,
            walkforward_use_dummy_data=True,
            walkforward_dummy_bars=1000,
            run_montecarlo=False,
            run_stress_tests=False,
            verbose=False,
        )

        exit_code = research_cli.run_pipeline(args)

        assert exit_code == 0
        assert mock_wf.called

    @patch("scripts.research_cli.run_sweep_from_args")
    def test_pipeline_stops_on_sweep_failure(self, mock_sweep):
        """Pipeline bricht ab wenn Sweep fehlschlägt."""
        mock_sweep.return_value = 1  # Fehler

        args = argparse.Namespace(
            sweep_name="test",
            config="config/config.toml",
            format="both",
            with_plots=False,
            top_n=5,
            run_walkforward=False,
            walkforward_train_window=None,
            walkforward_test_window=None,
            walkforward_step_size=None,
            walkforward_use_dummy_data=False,
            walkforward_dummy_bars=1000,
            run_montecarlo=False,
            run_stress_tests=False,
            verbose=False,
        )

        exit_code = research_cli.run_pipeline(args)

        assert exit_code == 1
        assert mock_sweep.called

    @patch("scripts.research_cli.run_sweep_from_args")
    @patch("scripts.research_cli.run_report_from_args")
    def test_pipeline_stops_on_report_failure(self, mock_report, mock_sweep):
        """Pipeline bricht ab wenn Report fehlschlägt."""
        mock_sweep.return_value = 0
        mock_report.return_value = 1  # Fehler

        args = argparse.Namespace(
            sweep_name="test",
            config="config/config.toml",
            format="both",
            with_plots=False,
            top_n=5,
            run_walkforward=False,
            walkforward_train_window=None,
            walkforward_test_window=None,
            walkforward_step_size=None,
            walkforward_use_dummy_data=False,
            walkforward_dummy_bars=1000,
            run_montecarlo=False,
            run_stress_tests=False,
            verbose=False,
        )

        exit_code = research_cli.run_pipeline(args)

        assert exit_code == 1
        assert mock_sweep.called
        assert mock_report.called

    @patch("scripts.research_cli.run_sweep_from_args")
    @patch("scripts.research_cli.run_report_from_args")
    @patch("scripts.research_cli.run_promote_from_args")
    @patch("scripts.research_cli.run_montecarlo_from_args")
    def test_pipeline_runs_montecarlo_when_flag_set(
        self, mock_mc, mock_promote, mock_report, mock_sweep
    ):
        """Pipeline führt Monte-Carlo aus wenn --run-montecarlo gesetzt ist."""
        mock_sweep.return_value = 0
        mock_report.return_value = 0
        mock_promote.return_value = 0
        mock_mc.return_value = 0

        args = argparse.Namespace(
            sweep_name="test",
            config="config/config.toml",
            format="both",
            with_plots=False,
            top_n=5,
            run_walkforward=False,
            walkforward_train_window=None,
            walkforward_test_window=None,
            walkforward_step_size=None,
            walkforward_use_dummy_data=False,
            walkforward_dummy_bars=1000,
            run_montecarlo=True,
            mc_num_runs=500,
            mc_method="simple",
            mc_block_size=20,
            mc_seed=42,
            mc_use_dummy_data=True,
            mc_dummy_bars=300,
            run_stress_tests=False,
            verbose=False,
        )

        exit_code = research_cli.run_pipeline(args)

        assert exit_code == 0
        assert mock_mc.called

    @patch("scripts.research_cli.run_sweep_from_args")
    @patch("scripts.research_cli.run_report_from_args")
    @patch("scripts.research_cli.run_promote_from_args")
    @patch("scripts.research_cli.run_stress_from_args")
    def test_pipeline_runs_stress_tests_when_flag_set(
        self, mock_stress, mock_promote, mock_report, mock_sweep
    ):
        """Pipeline führt Stress-Tests aus wenn --run-stress-tests gesetzt ist."""
        mock_sweep.return_value = 0
        mock_report.return_value = 0
        mock_promote.return_value = 0
        mock_stress.return_value = 0

        args = argparse.Namespace(
            sweep_name="test",
            config="config/config.toml",
            format="both",
            with_plots=False,
            top_n=5,
            run_walkforward=False,
            walkforward_train_window=None,
            walkforward_test_window=None,
            walkforward_step_size=None,
            walkforward_use_dummy_data=False,
            walkforward_dummy_bars=1000,
            run_montecarlo=False,
            run_stress_tests=True,
            stress_scenarios=["single_crash_bar", "vol_spike"],
            stress_severity=0.2,
            stress_window=5,
            stress_position="middle",
            stress_seed=42,
            stress_use_dummy_data=True,
            stress_dummy_bars=300,
            verbose=False,
        )

        exit_code = research_cli.run_pipeline(args)

        assert exit_code == 0
        assert mock_stress.called

    @patch("scripts.research_cli.run_sweep_from_args")
    @patch("scripts.research_cli.run_report_from_args")
    @patch("scripts.research_cli.run_promote_from_args")
    @patch("scripts.research_cli.run_walkforward_from_args")
    @patch("scripts.research_cli.run_montecarlo_from_args")
    @patch("scripts.research_cli.run_stress_from_args")
    def test_pipeline_runs_all_optional_steps(
        self, mock_stress, mock_mc, mock_wf, mock_promote, mock_report, mock_sweep
    ):
        """Pipeline führt alle optionalen Schritte aus wenn aktiviert."""
        mock_sweep.return_value = 0
        mock_report.return_value = 0
        mock_promote.return_value = 0
        mock_wf.return_value = 0
        mock_mc.return_value = 0
        mock_stress.return_value = 0

        args = argparse.Namespace(
            sweep_name="test",
            config="config/config.toml",
            format="both",
            with_plots=True,
            top_n=3,
            run_walkforward=True,
            walkforward_train_window="90d",
            walkforward_test_window="30d",
            walkforward_step_size=None,
            walkforward_use_dummy_data=True,
            walkforward_dummy_bars=1000,
            run_montecarlo=True,
            mc_num_runs=100,
            mc_method="simple",
            mc_block_size=20,
            mc_seed=42,
            mc_use_dummy_data=True,
            mc_dummy_bars=200,
            run_stress_tests=True,
            stress_scenarios=["single_crash_bar"],
            stress_severity=0.15,
            stress_window=5,
            stress_position="middle",
            stress_seed=42,
            stress_use_dummy_data=True,
            stress_dummy_bars=200,
            verbose=False,
        )

        exit_code = research_cli.run_pipeline(args)

        assert exit_code == 0
        assert mock_sweep.called
        assert mock_report.called
        assert mock_promote.called
        assert mock_wf.called
        assert mock_mc.called
        assert mock_stress.called

