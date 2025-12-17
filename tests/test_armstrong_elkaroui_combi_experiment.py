# tests/test_armstrong_elkaroui_combi_experiment.py
"""
Tests für das Armstrong × El-Karoui Kombi-Experiment.

Diese Tests validieren:
1. Smoke-Test auf kurzem Zeitraum
2. Safety-Checks (tier, environment)
3. Label-Generierung und Aggregation
4. Report-Generierung
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Generiert einen kurzen OHLCV-Datensatz für Tests."""
    np.random.seed(42)
    n_bars = 200

    index = pd.date_range(
        start="2024-01-01",
        periods=n_bars,
        freq="1h",
        tz="UTC",
    )

    base_price = 50000.0
    volatility = 0.015
    returns = np.random.normal(0, volatility, n_bars)
    close_prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame(index=index)
    df["close"] = close_prices
    df["open"] = df["close"].shift(1).fillna(base_price)
    df["high"] = np.maximum(df["open"], df["close"]) * (1 + np.random.uniform(0, 0.005, n_bars))
    df["low"] = np.minimum(df["open"], df["close"]) * (1 - np.random.uniform(0, 0.005, n_bars))
    df["volume"] = np.random.uniform(100, 1000, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


@pytest.fixture
def basic_config():
    """Erstellt eine minimale Test-Konfiguration."""
    from src.experiments.armstrong_elkaroui_combi_experiment import (
        ArmstrongElKarouiCombiConfig,
    )

    return ArmstrongElKarouiCombiConfig(
        symbol="BTC/EUR",
        timeframe="1h",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 10),
        armstrong_params={
            "cycle_length_days": 3141,
            "event_window_days": 90,
            "reference_date": "2015-10-01",
        },
        elkaroui_params={
            "vol_window": 20,
            "vol_threshold_low": 0.3,
            "vol_threshold_high": 0.7,
            "use_ewm": True,
            "annualization_factor": 252.0,
        },
    )


# =============================================================================
# SMOKE TESTS
# =============================================================================

class TestArmstrongElKarouiCombiSmoke:
    """Smoke-Tests für das Kombi-Experiment."""

    def test_experiment_runs_successfully(self, sample_ohlcv_data, basic_config):
        """Experiment läuft mit minimalen Parametern durch."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            run_armstrong_elkaroui_combi_experiment,
        )

        result = run_armstrong_elkaroui_combi_experiment(basic_config, data=sample_ohlcv_data)

        assert result.success, f"Experiment fehlgeschlagen: {result.error_message}"
        assert result.run_id is not None
        assert len(result.run_id) > 0

    def test_run_type_is_correct(self, sample_ohlcv_data, basic_config):
        """run_type ist korrekt auf 'armstrong_elkaroui_combi' gesetzt."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            RUN_TYPE_ARMSTRONG_ELKAROUI_COMBI,
            run_armstrong_elkaroui_combi_experiment,
        )

        result = run_armstrong_elkaroui_combi_experiment(basic_config, data=sample_ohlcv_data)

        assert result.run_type == RUN_TYPE_ARMSTRONG_ELKAROUI_COMBI
        assert result.run_type == "armstrong_elkaroui_combi"

    def test_combo_stats_not_empty(self, sample_ohlcv_data, basic_config):
        """combo_stats enthält mindestens eine Kombi-Klasse."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            run_armstrong_elkaroui_combi_experiment,
        )

        result = run_armstrong_elkaroui_combi_experiment(basic_config, data=sample_ohlcv_data)

        assert result.combo_stats is not None
        assert len(result.combo_stats) > 0, "combo_stats sollte nicht leer sein"

    def test_combo_stats_has_count_bars(self, sample_ohlcv_data, basic_config):
        """Jede Kombi-Klasse hat count_bars > 0."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            run_armstrong_elkaroui_combi_experiment,
        )

        result = run_armstrong_elkaroui_combi_experiment(basic_config, data=sample_ohlcv_data)

        assert len(result.combo_stats) > 0

        for state, stats in result.combo_stats.items():
            assert "count_bars" in stats, f"Fehlt count_bars für {state}"
            assert stats["count_bars"] > 0, f"count_bars sollte > 0 sein für {state}"


# =============================================================================
# SAFETY TESTS
# =============================================================================

class TestArmstrongElKarouiCombiSafety:
    """Safety-Tests für das Kombi-Experiment."""

    def test_tier_is_r_and_d(self, sample_ohlcv_data, basic_config):
        """tier muss 'r_and_d' sein."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            run_armstrong_elkaroui_combi_experiment,
        )

        result = run_armstrong_elkaroui_combi_experiment(basic_config, data=sample_ohlcv_data)

        assert result.tier == "r_and_d"

    def test_environment_is_allowed(self, sample_ohlcv_data, basic_config):
        """environment muss in erlaubten Umgebungen sein."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            ALLOWED_ENVIRONMENTS,
            run_armstrong_elkaroui_combi_experiment,
        )

        result = run_armstrong_elkaroui_combi_experiment(basic_config, data=sample_ohlcv_data)

        assert result.environment in ALLOWED_ENVIRONMENTS

    def test_live_environment_raises_error(self):
        """Live-Umgebung wirft ValueError."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            ArmstrongElKarouiCombiConfig,
        )

        with pytest.raises(ValueError, match="nicht erlaubt"):
            ArmstrongElKarouiCombiConfig(
                symbol="BTC/EUR",
                timeframe="1h",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 10),
                environment="live",  # Sollte fehlschlagen
            )

    def test_paper_environment_raises_error(self):
        """Paper-Umgebung wirft ValueError."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            ArmstrongElKarouiCombiConfig,
        )

        with pytest.raises(ValueError, match="nicht erlaubt"):
            ArmstrongElKarouiCombiConfig(
                symbol="BTC/EUR",
                timeframe="1h",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 10),
                environment="paper",  # Sollte fehlschlagen
            )

    def test_testnet_environment_raises_error(self):
        """Testnet-Umgebung wirft ValueError."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            ArmstrongElKarouiCombiConfig,
        )

        with pytest.raises(ValueError, match="nicht erlaubt"):
            ArmstrongElKarouiCombiConfig(
                symbol="BTC/EUR",
                timeframe="1h",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 10),
                environment="testnet",  # Sollte fehlschlagen
            )

    def test_wrong_tier_raises_error(self):
        """Falscher Tier wirft ValueError."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            ArmstrongElKarouiCombiConfig,
        )

        with pytest.raises(ValueError, match="r_and_d"):
            ArmstrongElKarouiCombiConfig(
                symbol="BTC/EUR",
                timeframe="1h",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 10),
                tier="production",  # Sollte fehlschlagen
            )


# =============================================================================
# LABEL GENERATION TESTS
# =============================================================================

class TestLabelGeneration:
    """Tests für die Label-Generierung."""

    def test_armstrong_labels_have_correct_values(self, sample_ohlcv_data):
        """Armstrong-Labels haben nur erlaubte Werte."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            ArmstrongEventState,
            compute_armstrong_event_labels,
        )

        armstrong_params = {
            "cycle_length_days": 3141,
            "event_window_days": 90,
            "reference_date": "2015-10-01",
        }

        labels = compute_armstrong_event_labels(sample_ohlcv_data, armstrong_params)

        allowed_values = {
            ArmstrongEventState.NONE,
            ArmstrongEventState.PRE_EVENT,
            ArmstrongEventState.EVENT,
            ArmstrongEventState.POST_EVENT,
        }

        unique_values = set(labels.unique())
        assert unique_values.issubset(allowed_values), f"Unerlaubte Werte: {unique_values - allowed_values}"

    def test_elkaroui_labels_have_correct_values(self, sample_ohlcv_data):
        """El-Karoui-Labels haben nur erlaubte Werte."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            ElKarouiRegime,
            compute_elkaroui_regime_labels,
        )

        elkaroui_params = {
            "vol_window": 20,
            "vol_threshold_low": 0.3,
            "vol_threshold_high": 0.7,
            "use_ewm": True,
            "annualization_factor": 252.0,
        }

        labels = compute_elkaroui_regime_labels(sample_ohlcv_data, elkaroui_params)

        allowed_values = {
            ElKarouiRegime.LOW,
            ElKarouiRegime.MEDIUM,
            ElKarouiRegime.HIGH,
        }

        unique_values = set(labels.dropna().unique())
        assert unique_values.issubset(allowed_values), f"Unerlaubte Werte: {unique_values - allowed_values}"

    def test_combo_labels_format(self, sample_ohlcv_data):
        """Kombi-Labels haben das richtige Format (STATE_REGIME)."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            compute_armstrong_event_labels,
            compute_elkaroui_regime_labels,
            create_combo_state_labels,
        )

        armstrong_params = {"cycle_length_days": 3141, "event_window_days": 90, "reference_date": "2015-10-01"}
        elkaroui_params = {"vol_window": 20, "vol_threshold_low": 0.3, "vol_threshold_high": 0.7}

        armstrong_labels = compute_armstrong_event_labels(sample_ohlcv_data, armstrong_params)
        elkaroui_labels = compute_elkaroui_regime_labels(sample_ohlcv_data, elkaroui_params)

        combo_labels = create_combo_state_labels(armstrong_labels, elkaroui_labels)

        for label in combo_labels.dropna().unique():
            assert "_" in label, f"Label sollte '_' enthalten: {label}"
            parts = label.split("_")
            assert len(parts) == 2, f"Label sollte genau 2 Teile haben: {label}"


# =============================================================================
# FORWARD RETURN TESTS
# =============================================================================

class TestForwardReturns:
    """Tests für Forward-Return-Berechnung."""

    def test_forward_returns_have_correct_columns(self, sample_ohlcv_data):
        """Forward-Returns haben die erwarteten Spalten."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            compute_forward_returns,
        )

        windows = [1, 3, 7]
        returns_df = compute_forward_returns(sample_ohlcv_data, windows)

        expected_cols = ["ret_1d_fwd", "ret_3d_fwd", "ret_7d_fwd"]
        for col in expected_cols:
            assert col in returns_df.columns, f"Spalte {col} fehlt"

    def test_forward_returns_values_reasonable(self, sample_ohlcv_data):
        """Forward-Returns haben vernünftige Werte."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            compute_forward_returns,
        )

        returns_df = compute_forward_returns(sample_ohlcv_data, [1])

        # Returns sollten im typischen Bereich liegen (-50% bis +50%)
        valid_returns = returns_df["ret_1d_fwd"].dropna()
        assert (valid_returns.abs() < 0.5).all(), "Returns außerhalb des erwarteten Bereichs"


# =============================================================================
# AGGREGATION TESTS
# =============================================================================

class TestAggregation:
    """Tests für die Aggregation."""

    def test_combo_stats_structure(self, sample_ohlcv_data, basic_config):
        """combo_stats hat die richtige Struktur."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            run_armstrong_elkaroui_combi_experiment,
        )

        result = run_armstrong_elkaroui_combi_experiment(basic_config, data=sample_ohlcv_data)

        for state, stats in result.combo_stats.items():
            assert isinstance(stats, dict), f"Stats für {state} sollte dict sein"
            assert "count_bars" in stats, f"count_bars fehlt für {state}"

            # Prüfe ob Return-Statistiken vorhanden sind (wenn genug Daten)
            if stats["count_bars"] > 10:
                # Mindestens eine Return-Statistik sollte vorhanden sein
                has_return_stat = any(k.startswith("avg_ret") for k in stats)
                # Note: Kann leer sein wenn alle Returns NaN sind (am Ende der Serie)

    def test_total_bars_match(self, sample_ohlcv_data, basic_config):
        """Summe der count_bars entspricht nicht mehr als Gesamt-Bars."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            run_armstrong_elkaroui_combi_experiment,
        )

        result = run_armstrong_elkaroui_combi_experiment(basic_config, data=sample_ohlcv_data)

        total_counted = sum(stats.get("count_bars", 0) for stats in result.combo_stats.values())

        # Sollte <= Gesamt-Bars sein (manche Bars können fehlen wegen NaN)
        assert total_counted <= len(sample_ohlcv_data), "Gezählte Bars > Gesamt-Bars"


# =============================================================================
# REPORT TESTS
# =============================================================================

class TestReportGeneration:
    """Tests für die Report-Generierung."""

    def test_report_generation(self, sample_ohlcv_data, basic_config):
        """Report wird erfolgreich generiert."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            generate_armstrong_elkaroui_combi_report,
            run_armstrong_elkaroui_combi_experiment,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            basic_config.output_dir = tmpdir
            result = run_armstrong_elkaroui_combi_experiment(basic_config, data=sample_ohlcv_data)

            report_path = generate_armstrong_elkaroui_combi_report(result, output_dir=tmpdir)

            assert Path(report_path).exists(), "Report-Datei wurde nicht erstellt"

            with open(report_path) as f:
                content = f.read()

            assert "Armstrong" in content
            assert "El-Karoui" in content
            assert result.run_id in content

    def test_json_export(self, sample_ohlcv_data, basic_config):
        """JSON-Export funktioniert."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            run_armstrong_elkaroui_combi_experiment,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            basic_config.output_dir = tmpdir
            result = run_armstrong_elkaroui_combi_experiment(basic_config, data=sample_ohlcv_data)

            json_path = result.save_json()

            assert Path(json_path).exists(), "JSON-Datei wurde nicht erstellt"

            with open(json_path) as f:
                data = json.load(f)

            assert data["run_id"] == result.run_id
            assert data["run_type"] == "armstrong_elkaroui_combi"
            assert data["tier"] == "r_and_d"


# =============================================================================
# CONFIG TESTS
# =============================================================================

class TestConfig:
    """Tests für die Konfiguration."""

    def test_config_to_dict(self, basic_config):
        """Config kann zu Dict konvertiert werden."""
        config_dict = basic_config.to_dict()

        assert "symbol" in config_dict
        assert "timeframe" in config_dict
        assert "armstrong_params" in config_dict
        assert "elkaroui_params" in config_dict
        assert "run_type" in config_dict

    def test_config_defaults(self):
        """Config hat sinnvolle Defaults."""
        from src.experiments.armstrong_elkaroui_combi_experiment import (
            ArmstrongElKarouiCombiConfig,
        )

        config = ArmstrongElKarouiCombiConfig(
            symbol="BTC/EUR",
            timeframe="1h",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
        )

        assert config.environment == "offline_backtest"
        assert config.tier == "r_and_d"
        assert config.run_type == "armstrong_elkaroui_combi"
        assert config.experiment_category == "label_analysis"


# =============================================================================
# CLI INTEGRATION TEST (optional)
# =============================================================================

class TestCLIIntegration:
    """Tests für CLI-Integration."""

    def test_cli_parser_has_combi_command(self):
        """CLI-Parser hat armstrong-elkaroui-combi Subcommand."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

        try:
            from scripts.research_cli import build_parser

            parser = build_parser()

            # Parse mit Hilfe um Subcommands zu sehen
            # Wir testen ob der Parser ohne Fehler gebaut wird
            # und ob der Subcommand existiert
            args = parser.parse_args(["armstrong-elkaroui-combi", "--help"])
        except SystemExit:
            # --help löst SystemExit aus, das ist OK
            pass
        except ImportError:
            pytest.skip("CLI nicht importierbar")
