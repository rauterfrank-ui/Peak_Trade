"""
Tests for Component VaR Report Generator
=========================================
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.reporting.component_var_report import (
    ComponentVaRReportData,
    ComponentVaRReportGenerator,
    run_sanity_checks,
)


@pytest.fixture
def sample_report_data():
    """Sample report data for testing."""
    return ComponentVaRReportData(
        run_id="test_20251225_120000",
        timestamp="2025-12-25T12:00:00",
        total_var=45678.90,
        portfolio_value=1_000_000.0,
        confidence=0.95,
        horizon=1,
        lookback_days=252,
        asset_symbols=["BTC", "ETH", "SOL"],
        weights=[0.6, 0.3, 0.1],
        component_var=[27407.34, 13703.67, 4567.89],
        contribution_pct=[60.0, 30.0, 10.0],
        marginal_var=[45678.90, 45678.90, 45678.90],
        sanity_checks={"all_pass": True},
        metadata={"num_assets": 3, "data_rows": 252},
    )


class TestComponentVaRReportData:
    """Test ComponentVaRReportData dataclass."""

    def test_creation(self, sample_report_data):
        """Test data creation."""
        assert sample_report_data.run_id == "test_20251225_120000"
        assert sample_report_data.total_var == 45678.90
        assert len(sample_report_data.asset_symbols) == 3

    def test_to_dict(self, sample_report_data):
        """Test dictionary conversion."""
        data_dict = sample_report_data.to_dict()
        assert isinstance(data_dict, dict)
        assert data_dict["run_id"] == "test_20251225_120000"
        assert data_dict["total_var"] == 45678.90
        assert "asset_symbols" in data_dict


class TestComponentVaRReportGenerator:
    """Test report generator."""

    def test_generator_initialization(self):
        """Test generator initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ComponentVaRReportGenerator(Path(tmpdir))
            assert generator.output_dir == Path(tmpdir)
            assert generator.output_dir.exists()

    def test_generate_json_report(self, sample_report_data):
        """Test JSON report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ComponentVaRReportGenerator(Path(tmpdir))
            outputs = generator.generate_reports(sample_report_data)

            # Check JSON file exists
            assert outputs["json"].exists()

            # Load and validate JSON
            with open(outputs["json"]) as f:
                data = json.load(f)

            assert data["run_id"] == "test_20251225_120000"
            assert data["total_var"] == 45678.90
            assert len(data["asset_symbols"]) == 3

    def test_generate_csv_report(self, sample_report_data):
        """Test CSV report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ComponentVaRReportGenerator(Path(tmpdir))
            outputs = generator.generate_reports(sample_report_data)

            # Check CSV file exists
            assert outputs["csv"].exists()

            # Load and validate CSV
            df = pd.read_csv(outputs["csv"])

            assert len(df) == 3
            assert list(df.columns) == [
                "symbol",
                "weight",
                "component_var",
                "contribution_pct",
                "marginal_var",
            ]
            assert df["symbol"].tolist() == ["BTC", "ETH", "SOL"]

            # Should be sorted by contribution_pct descending
            assert df["contribution_pct"].tolist() == [60.0, 30.0, 10.0]

    def test_generate_html_report(self, sample_report_data):
        """Test HTML report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ComponentVaRReportGenerator(Path(tmpdir))
            outputs = generator.generate_reports(sample_report_data)

            # Check HTML file exists
            assert outputs["html"].exists()

            # Read HTML content
            with open(outputs["html"]) as f:
                html = f.read()

            # Check key elements
            assert "test_20251225_120000" in html
            assert "$45,678.90" in html
            assert "BTC" in html
            assert "ETH" in html
            assert "SOL" in html

    def test_all_formats_generated(self, sample_report_data):
        """Test all three formats are generated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ComponentVaRReportGenerator(Path(tmpdir))
            outputs = generator.generate_reports(sample_report_data)

            assert "json" in outputs
            assert "csv" in outputs
            assert "html" in outputs

            for path in outputs.values():
                assert path.exists()


class TestSanityChecks:
    """Test sanity check functions."""

    def test_sanity_checks_pass(self):
        """Test sanity checks with valid data."""
        weights = np.array([0.6, 0.3, 0.1])
        component_var = np.array([27407.34, 13703.67, 4567.89])
        total_var = 45678.90
        symbols = ["BTC", "ETH", "SOL"]

        checks = run_sanity_checks(weights, component_var, total_var, symbols)

        assert checks["all_pass"] is True
        assert checks["weights_sum"]["pass"] is True
        assert checks["no_nans"]["pass"] is True
        assert checks["euler_property"]["pass"] is True
        assert checks["sufficient_assets"]["pass"] is True

    def test_sanity_checks_weights_not_normalized(self):
        """Test sanity checks with non-normalized weights."""
        weights = np.array([0.5, 0.3, 0.1])  # Sum = 0.9
        component_var = np.array([27407.34, 13703.67, 4567.89])
        total_var = 45678.90
        symbols = ["BTC", "ETH", "SOL"]

        checks = run_sanity_checks(weights, component_var, total_var, symbols)

        # Should fail overall
        assert checks["all_pass"] is False
        # Weights check should fail
        assert checks["weights_sum"]["pass"] is False

    def test_sanity_checks_with_nans(self):
        """Test sanity checks with NaN values."""
        weights = np.array([0.6, 0.3, 0.1])
        component_var = np.array([27407.34, np.nan, 4567.89])
        total_var = 45678.90
        symbols = ["BTC", "ETH", "SOL"]

        checks = run_sanity_checks(weights, component_var, total_var, symbols)

        assert checks["all_pass"] is False
        assert checks["no_nans"]["pass"] is False

    def test_sanity_checks_euler_violation(self):
        """Test sanity checks with Euler property violation."""
        weights = np.array([0.6, 0.3, 0.1])
        component_var = np.array([20000.0, 15000.0, 5000.0])  # Sum = 40000
        total_var = 45678.90  # Doesn't match
        symbols = ["BTC", "ETH", "SOL"]

        checks = run_sanity_checks(weights, component_var, total_var, symbols)

        assert checks["all_pass"] is False
        assert checks["euler_property"]["pass"] is False

    def test_sanity_checks_insufficient_assets(self):
        """Test sanity checks with insufficient assets."""
        weights = np.array([1.0])
        component_var = np.array([45678.90])
        total_var = 45678.90
        symbols = ["BTC"]

        checks = run_sanity_checks(weights, component_var, total_var, symbols)

        assert checks["all_pass"] is False
        assert checks["sufficient_assets"]["pass"] is False


class TestReportStability:
    """Test report output stability (deterministic)."""

    def test_json_output_is_deterministic(self, sample_report_data):
        """Test JSON output is consistent across runs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ComponentVaRReportGenerator(Path(tmpdir))

            # Generate twice
            outputs1 = generator.generate_reports(sample_report_data)
            with open(outputs1["json"]) as f:
                data1 = json.load(f)

            # Clean directory
            for file in Path(tmpdir).glob("*"):
                file.unlink()

            outputs2 = generator.generate_reports(sample_report_data)
            with open(outputs2["json"]) as f:
                data2 = json.load(f)

            # Should be identical
            assert data1 == data2

    def test_csv_output_is_sorted(self, sample_report_data):
        """Test CSV output is always sorted by contribution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ComponentVaRReportGenerator(Path(tmpdir))
            outputs = generator.generate_reports(sample_report_data)

            df = pd.read_csv(outputs["csv"])

            # Should be sorted descending by contribution_pct
            contributions = df["contribution_pct"].tolist()
            assert contributions == sorted(contributions, reverse=True)


class TestEdgeCases:
    """Test edge cases."""

    def test_single_asset_report(self):
        """Test report with single asset (edge case)."""
        data = ComponentVaRReportData(
            run_id="single_asset_test",
            timestamp="2025-12-25T12:00:00",
            total_var=10000.0,
            portfolio_value=100000.0,
            confidence=0.95,
            horizon=1,
            lookback_days=100,
            asset_symbols=["BTC"],
            weights=[1.0],
            component_var=[10000.0],
            contribution_pct=[100.0],
            marginal_var=[10000.0],
            sanity_checks={"all_pass": False, "sufficient_assets": {"pass": False}},
            metadata={},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ComponentVaRReportGenerator(Path(tmpdir))
            outputs = generator.generate_reports(data)

            # Should generate all formats
            assert all(p.exists() for p in outputs.values())

            # Check CSV
            df = pd.read_csv(outputs["csv"])
            assert len(df) == 1

    def test_many_assets_report(self):
        """Test report with many assets."""
        n_assets = 50
        weights = np.ones(n_assets) / n_assets
        component_var = np.random.rand(n_assets) * 1000

        data = ComponentVaRReportData(
            run_id="many_assets_test",
            timestamp="2025-12-25T12:00:00",
            total_var=float(component_var.sum()),
            portfolio_value=1_000_000.0,
            confidence=0.95,
            horizon=1,
            lookback_days=252,
            asset_symbols=[f"ASSET_{i}" for i in range(n_assets)],
            weights=weights.tolist(),
            component_var=component_var.tolist(),
            contribution_pct=(component_var / component_var.sum() * 100).tolist(),
            marginal_var=component_var.tolist(),
            sanity_checks={"all_pass": True},
            metadata={},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ComponentVaRReportGenerator(Path(tmpdir))
            outputs = generator.generate_reports(data)

            # Should handle many assets gracefully
            df = pd.read_csv(outputs["csv"])
            assert len(df) == n_assets
