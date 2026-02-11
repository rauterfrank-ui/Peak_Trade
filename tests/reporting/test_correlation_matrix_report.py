# tests/reporting/test_correlation_matrix_report.py
"""
Tests für src/reporting/correlation_matrix_report.py (Parameter–Metrik-Korrelationsmatrix).

Unit-Tests für die Korrelationsberechnung auf synthetischen Daten (kein Netzwerk, keine externen Tools).
"""

from pathlib import Path

import pandas as pd
import pytest

from src.reporting.correlation_matrix_report import (
    build_param_metric_corr,
    correlation_matrix_report,
)


# =============================================================================
# build_param_metric_corr – synthetische Daten
# =============================================================================


class TestBuildParamMetricCorr:
    """Tests für build_param_metric_corr()."""

    def test_basic_synthetic_matrix_shape(self):
        """Matrix hat Zeilen = numerische Parameter, Spalten = Metriken."""
        df = pd.DataFrame({
            "param_a": [1.0, 2.0, 3.0, 4.0, 5.0],
            "param_b": [10.0, 20.0, 30.0, 40.0, 50.0],
            "metric_x": [0.1, 0.2, 0.3, 0.4, 0.5],
            "metric_y": [1.0, 1.0, 1.0, 1.0, 1.0],
        })
        result = build_param_metric_corr(df, method="spearman")
        assert result.index.tolist() == ["param_a", "param_b"]
        assert result.columns.tolist() == ["metric_x", "metric_y"]
        assert result.shape == (2, 2)

    def test_perfect_correlation_spearman(self):
        """Spearman-Korrelation: perfekte Monotonie ergibt 1.0."""
        n = 20
        x = list(range(n))
        df = pd.DataFrame({
            "param_p": x,
            "metric_m": [v * 2.0 + 1.0 for v in x],
        })
        result = build_param_metric_corr(df, method="spearman")
        assert result.loc["param_p", "metric_m"] == pytest.approx(1.0, abs=1e-9)

    def test_perfect_negative_correlation_spearman(self):
        """Spearman: perfekt negativ monoton ergibt -1.0."""
        n = 15
        df = pd.DataFrame({
            "param_p": list(range(n)),
            "metric_m": list(range(n, 0, -1)),
        })
        result = build_param_metric_corr(df, method="spearman")
        assert result.loc["param_p", "metric_m"] == pytest.approx(-1.0, abs=1e-9)

    def test_pearson_option(self):
        """Pearson-Methode wird unterstützt."""
        df = pd.DataFrame({
            "param_a": [1.0, 2.0, 3.0],
            "metric_m": [2.0, 4.0, 6.0],
        })
        result = build_param_metric_corr(df, method="pearson")
        assert result.loc["param_a", "metric_m"] == pytest.approx(1.0, abs=1e-9)

    def test_invalid_method_raises(self):
        """Ungültige method wirft ValueError."""
        df = pd.DataFrame({"param_a": [1, 2], "metric_m": [1, 2]})
        with pytest.raises(ValueError, match="spearman.*pearson"):
            build_param_metric_corr(df, method="kendall")

    def test_skips_non_numeric_params(self):
        """Nicht-numerische Parameter-Spalten werden ausgelassen; nur numerische bleiben."""
        df = pd.DataFrame({
            "param_numeric": [1.0, 2.0, 3.0],
            "param_str": ["a", "b", "c"],
            "metric_m": [0.5, 0.6, 0.7],
        })
        result = build_param_metric_corr(df, method="spearman")
        assert "param_numeric" in result.index
        assert "param_str" not in result.index
        assert result.shape[0] == 1 and result.shape[1] == 1

    def test_pairwise_complete_missing_values(self):
        """Fehlende Werte: pairwise complete – Korrelation wird trotzdem berechnet."""
        df = pd.DataFrame({
            "param_a": [1.0, 2.0, 3.0, 4.0, 5.0],
            "metric_m": [1.0, 2.0, float("nan"), 4.0, 5.0],
        })
        result = build_param_metric_corr(df, method="spearman")
        assert result.shape == (1, 1)
        # 4 Paare ohne NaN → Korrelation definiert
        assert result.loc["param_a", "metric_m"] == pytest.approx(1.0, abs=1e-9)

    def test_deterministic_ordering(self):
        """Zeilen- und Spaltenreihenfolge sind deterministisch (sortiert)."""
        df = pd.DataFrame({
            "param_z": [1, 2, 3],
            "param_a": [4, 5, 6],
            "metric_second": [0.1, 0.2, 0.3],
            "metric_first": [0.3, 0.2, 0.1],
        })
        result = build_param_metric_corr(df, method="spearman")
        assert result.index.tolist() == ["param_a", "param_z"]
        assert result.columns.tolist() == ["metric_first", "metric_second"]

    def test_empty_metrics_returns_empty_df(self):
        """Keine Metrik-Spalten → leeres DataFrame."""
        df = pd.DataFrame({
            "param_a": [1.0, 2.0, 3.0],
        })
        result = build_param_metric_corr(df, method="spearman")
        assert result.empty

    def test_no_numeric_params_returns_empty_df(self):
        """Keine numerischen Parameter → leeres DataFrame."""
        df = pd.DataFrame({
            "param_x": ["a", "b", "c"],
            "metric_m": [1.0, 2.0, 3.0],
        })
        result = build_param_metric_corr(df, method="spearman")
        assert result.empty

    def test_metric_cols_filter(self):
        """metric_cols begrenzt auf angegebene Metriken."""
        df = pd.DataFrame({
            "param_a": [1.0, 2.0, 3.0],
            "metric_x": [0.1, 0.2, 0.3],
            "metric_y": [1.0, 2.0, 3.0],
            "metric_z": [10.0, 20.0, 30.0],
        })
        result = build_param_metric_corr(df, metric_cols=["metric_x", "metric_z"], method="spearman")
        assert result.columns.tolist() == ["metric_x", "metric_z"]


# =============================================================================
# correlation_matrix_report – CSV + Heatmap
# =============================================================================


class TestCorrelationMatrixReport:
    """Tests für correlation_matrix_report() – Artefakte auf Disk."""

    def test_produces_csv_and_heatmap(self):
        """Report erzeugt CSV und (bei Matplotlib) Heatmap mit deterministischen Namen."""
        df = pd.DataFrame({
            "param_a": [1.0, 2.0, 3.0, 4.0, 5.0],
            "metric_m": [0.1, 0.2, 0.3, 0.4, 0.5],
        })
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            artifacts = correlation_matrix_report(
                df=df,
                output_dir=out,
                sweep_name="test_sweep",
                with_heatmap=True,
            )
            assert "csv_path" in artifacts
            csv_path = artifacts["csv_path"]
            assert csv_path.name == "test_sweep_param_metric_correlation.csv"
            assert csv_path.exists()
            loaded = pd.read_csv(csv_path, index_col=0)
            assert loaded.shape == (1, 1)
            if "heatmap_path" in artifacts:
                assert artifacts["heatmap_path"].name == "test_sweep_param_metric_correlation_heatmap.png"
                assert artifacts["heatmap_path"].exists()

    def test_csv_content_matches_matrix(self):
        """Inhalt der CSV entspricht der berechneten Matrix."""
        df = pd.DataFrame({
            "param_p": [1.0, 2.0, 3.0],
            "metric_m": [2.0, 4.0, 6.0],
        })
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            artifacts = correlation_matrix_report(
                df=df,
                output_dir=out,
                sweep_name="s",
                with_heatmap=False,
            )
            csv_path = artifacts["csv_path"]
            loaded = pd.read_csv(csv_path, index_col=0)
            assert loaded.loc["param_p", "metric_m"] == pytest.approx(1.0, abs=1e-9)
