"""
Tests for Stress Gate Layer
============================

Comprehensive tests for scenario-based stress testing gate.
"""

import pandas as pd
import numpy as np
import pytest

from src.core.peak_config import PeakConfig
from src.risk_layer.stress_gate import StressGate, StressGateStatus, status_to_dict


@pytest.fixture
def default_config():
    """Default config with stress gate enabled."""
    return PeakConfig(
        raw={
            "risk": {
                "stress_gate": {
                    "enabled": True,
                    "max_stress_loss_pct": 0.04,  # 4% block threshold
                    "warn_stress_loss_pct": 0.03,  # 3% warn threshold
                    "scenarios": [
                        {
                            "name": "equity_down_5pct",
                            "description": "5% equity decline",
                            "shock_type": "return_shift",
                            "shock_params": {"shift": -0.05},
                        },
                        {
                            "name": "equity_down_10pct",
                            "description": "10% equity decline",
                            "shock_type": "return_shift",
                            "shock_params": {"shift": -0.10},
                        },
                    ],
                }
            }
        }
    )


@pytest.fixture
def disabled_config():
    """Config with stress gate disabled."""
    return PeakConfig(
        raw={"risk": {"stress_gate": {"enabled": False, "max_stress_loss_pct": 0.04}}}
    )


@pytest.fixture
def sample_returns():
    """Sample returns DataFrame for testing."""
    return pd.DataFrame(
        {
            "BTC": [0.01, -0.02, 0.03, -0.01, 0.02],
            "ETH": [0.02, -0.01, 0.01, 0.00, 0.01],
        }
    )


@pytest.fixture
def sample_weights():
    """Sample portfolio weights."""
    return {"BTC": 0.6, "ETH": 0.4}


class TestStressGateInit:
    """Test Stress Gate initialization."""

    def test_init_default_config(self, default_config):
        """Test initialization with default config."""
        gate = StressGate(default_config)

        assert gate.enabled is True
        assert gate.max_stress_loss_pct == 0.04
        assert gate.warn_stress_loss_pct == 0.03
        assert len(gate.scenarios) == 2
        assert gate.scenarios[0].name == "equity_down_5pct"
        assert gate.scenarios[1].name == "equity_down_10pct"

    def test_init_disabled(self, disabled_config):
        """Test initialization with disabled gate."""
        gate = StressGate(disabled_config)

        assert gate.enabled is False
        assert gate.max_stress_loss_pct == 0.04

    def test_init_no_scenarios_uses_defaults(self):
        """Test that default scenarios are used if none configured."""
        cfg = PeakConfig(
            raw={"risk": {"stress_gate": {"enabled": True, "max_stress_loss_pct": 0.04}}}
        )
        gate = StressGate(cfg)

        # Should have default scenarios
        assert len(gate.scenarios) >= 3
        scenario_names = [s.name for s in gate.scenarios]
        assert "equity_down_5pct" in scenario_names
        assert "equity_down_10pct" in scenario_names
        assert "vol_spike" in scenario_names


class TestStressGateEvaluate:
    """Test Stress Gate evaluation."""

    def test_disabled_returns_ok(self, disabled_config, sample_returns, sample_weights):
        """Test that disabled gate returns OK."""
        gate = StressGate(disabled_config)
        context = {"returns_df": sample_returns, "weights": sample_weights}

        status = gate.evaluate(context)

        assert status.severity == "OK"
        assert status.reason == "Stress gate disabled"
        assert status.inputs_available is False

    def test_missing_returns_returns_ok(self, default_config, sample_weights):
        """Test that missing returns returns OK (not applicable)."""
        gate = StressGate(default_config)
        context = {"weights": sample_weights}

        status = gate.evaluate(context)

        assert status.severity == "OK"
        assert "missing returns" in status.reason.lower()
        assert status.inputs_available is False

    def test_missing_weights_returns_ok(self, default_config, sample_returns):
        """Test that missing weights returns OK (not applicable)."""
        gate = StressGate(default_config)
        context = {"returns_df": sample_returns}

        status = gate.evaluate(context)

        assert status.severity == "OK"
        assert "missing" in status.reason.lower()
        assert status.inputs_available is False

    def test_missing_context_returns_ok(self, default_config):
        """Test that missing context returns OK."""
        gate = StressGate(default_config)

        status = gate.evaluate(None)

        assert status.severity == "OK"
        assert "missing" in status.reason.lower()
        assert status.inputs_available is False

    def test_invalid_returns_type_returns_ok(self, default_config, sample_weights):
        """Test that invalid returns_df type returns OK."""
        gate = StressGate(default_config)
        context = {"returns_df": "not_a_dataframe", "weights": sample_weights}

        status = gate.evaluate(context)

        assert status.severity == "OK"
        assert "invalid" in status.reason.lower()
        assert status.inputs_available is False


class TestStressGateScenarios:
    """Test stress scenario evaluation."""

    def test_simple_scenario_ok(self, default_config, sample_returns, sample_weights):
        """Test simple scenario that passes."""
        gate = StressGate(default_config)
        context = {"returns_df": sample_returns, "weights": sample_weights}

        status = gate.evaluate(context)

        assert status.inputs_available is True
        assert status.worst_case_loss_pct is not None
        assert status.scenarios_evaluated == 2
        assert status.timestamp_utc != ""

    def test_deterministic_known_returns(self):
        """Test with known returns for deterministic result."""
        # Setup: Returns with known mean
        returns_df = pd.DataFrame(
            {
                "A": [0.10, 0.10, 0.10],  # Mean = 0.10
                "B": [0.05, 0.05, 0.05],  # Mean = 0.05
            }
        )
        weights = {"A": 0.5, "B": 0.5}  # Portfolio mean = 0.075

        # Config: Single scenario with -10% shock
        cfg = PeakConfig(
            raw={
                "risk": {
                    "stress_gate": {
                        "enabled": True,
                        "max_stress_loss_pct": 0.10,
                        "warn_stress_loss_pct": 0.05,
                        "scenarios": [
                            {
                                "name": "shock_down_10pct",
                                "description": "10% down",
                                "shock_type": "return_shift",
                                "shock_params": {"shift": -0.10},
                            }
                        ],
                    }
                }
            }
        )

        gate = StressGate(cfg)
        context = {"returns_df": returns_df, "weights": weights}
        status = gate.evaluate(context)

        # After -10% shock: mean becomes 0.075 - 0.10 = -0.025 (-2.5%)
        assert status.severity == "OK"
        assert status.worst_case_loss_pct is not None
        assert status.worst_case_loss_pct < 0  # Loss is negative
        assert abs(status.worst_case_loss_pct - (-0.025)) < 0.001  # ~-2.5%

    def test_scenario_triggers_warn(self):
        """Test scenario that triggers warning."""
        # Returns with mean = 0.01
        returns_df = pd.DataFrame({"A": [0.01, 0.01, 0.01]})
        weights = {"A": 1.0}

        # Config with warn at -3%, block at -5%
        cfg = PeakConfig(
            raw={
                "risk": {
                    "stress_gate": {
                        "enabled": True,
                        "max_stress_loss_pct": 0.05,
                        "warn_stress_loss_pct": 0.03,
                        "scenarios": [
                            {
                                "name": "shock_down_4pct",
                                "description": "4% down",
                                "shock_type": "return_shift",
                                "shock_params": {"shift": -0.04},
                            }
                        ],
                    }
                }
            }
        )

        gate = StressGate(cfg)
        context = {"returns_df": returns_df, "weights": weights}
        status = gate.evaluate(context)

        # Loss = 0.01 - 0.04 = -0.03 (exactly at warn threshold)
        assert status.severity == "WARN"
        assert "near limit" in status.reason.lower()
        assert abs(status.worst_case_loss_pct - (-0.03)) < 0.001

    def test_scenario_triggers_block(self):
        """Test scenario that triggers block."""
        # Returns with mean = 0.01
        returns_df = pd.DataFrame({"A": [0.01, 0.01, 0.01]})
        weights = {"A": 1.0}

        # Config with block at -4%
        cfg = PeakConfig(
            raw={
                "risk": {
                    "stress_gate": {
                        "enabled": True,
                        "max_stress_loss_pct": 0.04,
                        "scenarios": [
                            {
                                "name": "shock_down_6pct",
                                "description": "6% down",
                                "shock_type": "return_shift",
                                "shock_params": {"shift": -0.06},
                            }
                        ],
                    }
                }
            }
        )

        gate = StressGate(cfg)
        context = {"returns_df": returns_df, "weights": weights}
        status = gate.evaluate(context)

        # Loss = 0.01 - 0.06 = -0.05 (exceeds -0.04 threshold)
        assert status.severity == "BLOCK"
        assert "exceeds limit" in status.reason.lower()
        assert abs(status.worst_case_loss_pct - (-0.05)) < 0.001

    def test_multiple_scenarios_picks_worst_case(self):
        """Test that multiple scenarios picks worst case."""
        returns_df = pd.DataFrame({"A": [0.02, 0.02, 0.02]})
        weights = {"A": 1.0}

        cfg = PeakConfig(
            raw={
                "risk": {
                    "stress_gate": {
                        "enabled": True,
                        "max_stress_loss_pct": 0.10,
                        "scenarios": [
                            {
                                "name": "mild_shock",
                                "description": "2% down",
                                "shock_type": "return_shift",
                                "shock_params": {"shift": -0.02},
                            },
                            {
                                "name": "severe_shock",
                                "description": "8% down",
                                "shock_type": "return_shift",
                                "shock_params": {"shift": -0.08},
                            },
                        ],
                    }
                }
            }
        )

        gate = StressGate(cfg)
        context = {"returns_df": returns_df, "weights": weights}
        status = gate.evaluate(context)

        # Worst case should be severe_shock: 0.02 - 0.08 = -0.06
        assert status.worst_case_loss_pct is not None
        assert abs(status.worst_case_loss_pct - (-0.06)) < 0.001
        assert "severe_shock" in status.triggered_scenarios
        assert status.scenarios_evaluated == 2

    def test_vol_spike_scenario(self):
        """Test volatility spike scenario type."""
        # Returns with clear mean and volatility
        returns_df = pd.DataFrame(
            {"A": [0.10, -0.05, 0.08, -0.03, 0.05]}  # Mean ≈ 0.03
        )
        weights = {"A": 1.0}

        cfg = PeakConfig(
            raw={
                "risk": {
                    "stress_gate": {
                        "enabled": True,
                        "max_stress_loss_pct": 0.20,
                        "scenarios": [
                            {
                                "name": "vol_spike_2x",
                                "description": "2x volatility",
                                "shock_type": "vol_spike",
                                "shock_params": {"multiplier": 2.0},
                            }
                        ],
                    }
                }
            }
        )

        gate = StressGate(cfg)
        context = {"returns_df": returns_df, "weights": weights}
        status = gate.evaluate(context)

        # Vol spike should preserve mean but increase volatility
        # Result should still be computable
        assert status.inputs_available is True
        assert status.worst_case_loss_pct is not None


class TestStressGateStatus:
    """Test StressGateStatus dataclass."""

    def test_status_immutable(self):
        """Test that status is immutable."""
        status = StressGateStatus(
            severity="OK",
            reason="Test",
            worst_case_loss_pct=-0.02,
            timestamp_utc="2025-12-25T12:00:00Z",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            status.severity = "BLOCK"

    def test_status_to_dict(self):
        """Test status_to_dict conversion."""
        status = StressGateStatus(
            severity="BLOCK",
            reason="Test block",
            worst_case_loss_pct=-0.045,
            threshold_block=0.04,
            threshold_warn=0.03,
            triggered_scenarios=["equity_down_10pct"],
            scenarios_evaluated=2,
            inputs_available=True,
            timestamp_utc="2025-12-25T12:00:00Z",
        )

        d = status_to_dict(status)

        assert d["severity"] == "BLOCK"
        assert d["reason"] == "Test block"
        assert d["worst_case_loss_pct"] == -0.045
        assert d["threshold_block"] == 0.04
        assert d["triggered_scenarios"] == ["equity_down_10pct"]
        assert d["scenarios_evaluated"] == 2
        assert d["inputs_available"] is True
        assert d["timestamp_utc"] == "2025-12-25T12:00:00Z"


class TestStressGateWeights:
    """Test weight handling."""

    def test_dict_weights(self):
        """Test with dict weights."""
        returns_df = pd.DataFrame({"BTC": [0.01], "ETH": [0.02]})
        weights = {"BTC": 0.6, "ETH": 0.4}

        cfg = PeakConfig(
            raw={
                "risk": {
                    "stress_gate": {
                        "enabled": True,
                        "max_stress_loss_pct": 0.10,
                        "scenarios": [
                            {
                                "name": "test",
                                "shock_type": "return_shift",
                                "shock_params": {"shift": -0.05},
                            }
                        ],
                    }
                }
            }
        )

        gate = StressGate(cfg)
        context = {"returns_df": returns_df, "weights": weights}
        status = gate.evaluate(context)

        assert status.severity == "OK"
        assert status.inputs_available is True

    def test_list_weights(self):
        """Test with list weights."""
        returns_df = pd.DataFrame({"BTC": [0.01], "ETH": [0.02]})
        weights = [0.6, 0.4]

        cfg = PeakConfig(
            raw={
                "risk": {
                    "stress_gate": {
                        "enabled": True,
                        "max_stress_loss_pct": 0.10,
                        "scenarios": [
                            {
                                "name": "test",
                                "shock_type": "return_shift",
                                "shock_params": {"shift": -0.05},
                            }
                        ],
                    }
                }
            }
        )

        gate = StressGate(cfg)
        context = {"returns_df": returns_df, "weights": weights}
        status = gate.evaluate(context)

        assert status.severity == "OK"
        assert status.inputs_available is True


class TestStressGateLastStatus:
    """Test last_status property."""

    def test_last_status_initially_none(self, default_config):
        """Test that last_status is None initially."""
        gate = StressGate(default_config)

        assert gate.last_status is None

    def test_last_status_updated_after_evaluate(
        self, default_config, sample_returns, sample_weights
    ):
        """Test that last_status is updated after evaluate."""
        gate = StressGate(default_config)
        context = {"returns_df": sample_returns, "weights": sample_weights}

        status = gate.evaluate(context)

        assert gate.last_status is not None
        assert gate.last_status.severity == status.severity
        assert gate.last_status.timestamp_utc == status.timestamp_utc
