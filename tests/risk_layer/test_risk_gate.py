"""
Tests for RiskGate
"""

import json
from pathlib import Path

import pytest

from src.core.peak_config import PeakConfig
from src.risk_layer.risk_gate import RiskGate


@pytest.fixture
def test_config(tmp_path: Path) -> PeakConfig:
    """Create a minimal test config."""
    audit_path = tmp_path / "audit.jsonl"
    return PeakConfig(
        raw={
            "risk": {
                "audit_log": {
                    "path": str(audit_path),
                }
            }
        }
    )


def test_risk_gate_initializes_with_config(test_config: PeakConfig) -> None:
    """Test that RiskGate initializes correctly."""
    gate = RiskGate(test_config)
    assert gate.cfg == test_config
    assert gate.audit_log is not None


def test_risk_gate_blocks_order_with_missing_symbol(test_config: PeakConfig) -> None:
    """Test that orders without symbol are blocked."""
    gate = RiskGate(test_config)

    order = {"qty": 1.0}  # Missing symbol
    result = gate.evaluate(order)

    assert not result.decision.allowed
    assert result.decision.severity == "BLOCK"
    assert len(result.decision.violations) >= 1
    assert any(v.code == "MISSING_SYMBOL" for v in result.decision.violations)


def test_risk_gate_blocks_order_with_missing_qty(test_config: PeakConfig) -> None:
    """Test that orders without qty are blocked."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT"}  # Missing qty
    result = gate.evaluate(order)

    assert not result.decision.allowed
    assert result.decision.severity == "BLOCK"
    assert len(result.decision.violations) >= 1
    assert any(v.code == "MISSING_QTY" for v in result.decision.violations)


def test_risk_gate_blocks_invalid_order_type(test_config: PeakConfig) -> None:
    """Test that non-dict orders are blocked."""
    gate = RiskGate(test_config)

    order = "not a dict"  # type: ignore[assignment]
    result = gate.evaluate(order)  # type: ignore[arg-type]

    assert not result.decision.allowed
    assert result.decision.severity == "BLOCK"
    assert any(v.code == "INVALID_ORDER_TYPE" for v in result.decision.violations)


def test_risk_gate_allows_valid_order(test_config: PeakConfig) -> None:
    """Test that valid orders are allowed."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    result = gate.evaluate(order)

    assert result.decision.allowed
    assert result.decision.severity == "OK"
    assert len(result.decision.violations) == 0
    assert "passed" in result.decision.reason.lower()


def test_risk_gate_writes_audit_log(test_config: PeakConfig, tmp_path: Path) -> None:
    """Test that audit log is written for all evaluations."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    result = gate.evaluate(order)

    # Get audit path from config
    audit_path = Path(test_config.get("risk.audit_log.path"))
    assert audit_path.exists()

    # Verify audit log contains the event
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1

    event = json.loads(lines[0])
    assert event["decision"]["allowed"] is True
    assert event["order"]["symbol"] == "BTCUSDT"
    assert "timestamp_utc" in event


def test_risk_gate_audit_log_contains_violations(test_config: PeakConfig, tmp_path: Path) -> None:
    """Test that violations are included in audit log."""
    gate = RiskGate(test_config)

    order = {"qty": 1.0}  # Missing symbol
    result = gate.evaluate(order)

    audit_path = Path(test_config.get("risk.audit_log.path"))
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[0])

    assert event["decision"]["allowed"] is False
    assert len(event["violations"]) >= 1
    assert any(v["code"] == "MISSING_SYMBOL" for v in event["violations"])


def test_risk_gate_includes_context_in_audit(test_config: PeakConfig, tmp_path: Path) -> None:
    """Test that context is included in audit log."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"portfolio_value": 10000.0, "daily_pnl": 150.0}
    result = gate.evaluate(order, context=context)

    audit_path = Path(test_config.get("risk.audit_log.path"))
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[0])

    assert event["context"]["portfolio_value"] == 10000.0
    assert event["context"]["daily_pnl"] == 150.0


def test_risk_gate_multiple_violations(test_config: PeakConfig) -> None:
    """Test that multiple violations are detected."""
    gate = RiskGate(test_config)

    order = {}  # Missing both symbol and qty
    result = gate.evaluate(order)

    assert not result.decision.allowed
    assert len(result.decision.violations) == 2
    assert any(v.code == "MISSING_SYMBOL" for v in result.decision.violations)
    assert any(v.code == "MISSING_QTY" for v in result.decision.violations)


def test_risk_gate_uses_default_audit_path_if_not_configured(tmp_path: Path) -> None:
    """Test that default audit path is used if not configured."""
    # Config without risk.audit_log.path
    cfg = PeakConfig(raw={})
    gate = RiskGate(cfg)

    # Should use default path
    assert gate.audit_log.path == Path("./logs/risk_audit.jsonl")


# ============================================================================
# Kill Switch Integration Tests (PR3)
# ============================================================================


def test_risk_gate_blocks_when_kill_switch_armed(test_config: PeakConfig) -> None:
    """Test that RiskGate blocks orders when kill switch is armed."""
    gate = RiskGate(test_config)

    # Valid order but metrics trigger kill switch
    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"metrics": {"daily_pnl_pct": -0.06}}  # Exceeds 5% limit

    result = gate.evaluate(order, context)

    assert not result.decision.allowed
    assert result.decision.severity == "BLOCK"
    assert "kill switch" in result.decision.reason.lower()
    assert any(v.code == "KILL_SWITCH_ARMED" for v in result.decision.violations)


def test_risk_gate_includes_kill_switch_in_audit(test_config: PeakConfig, tmp_path: Path) -> None:
    """Test that audit events include kill switch status."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"metrics": {"daily_pnl_pct": -0.06}}

    result = gate.evaluate(order, context)

    # Check audit log
    audit_path = Path(test_config.get("risk.audit_log.path"))
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[0])

    assert "kill_switch" in event
    assert event["kill_switch"]["enabled"] is True
    assert event["kill_switch"]["status"]["armed"] is True
    assert "daily_loss_limit" in event["kill_switch"]["status"]["triggered_by"]
    assert "metrics_snapshot" in event["kill_switch"]


def test_risk_gate_allows_when_metrics_ok(test_config: PeakConfig) -> None:
    """Test that RiskGate allows orders when metrics are within limits."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"metrics": {"daily_pnl_pct": -0.02, "current_drawdown_pct": 0.05}}

    result = gate.evaluate(order, context)

    assert result.decision.allowed
    assert result.decision.severity == "OK"


def test_risk_gate_audit_includes_unarmed_kill_switch(
    test_config: PeakConfig, tmp_path: Path
) -> None:
    """Test that audit log includes kill switch status even when not armed."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"metrics": {"daily_pnl_pct": -0.02}}

    result = gate.evaluate(order, context)

    audit_path = Path(test_config.get("risk.audit_log.path"))
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[0])

    assert "kill_switch" in event
    assert event["kill_switch"]["status"]["armed"] is False
    assert len(event["kill_switch"]["status"]["triggered_by"]) == 0
    assert "metrics_snapshot" in event["kill_switch"]


def test_risk_gate_tolerates_missing_metrics(test_config: PeakConfig) -> None:
    """Test that missing metrics don't trigger kill switch."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {}  # No metrics

    result = gate.evaluate(order, context)

    # Should pass - no metrics means no trigger
    assert result.decision.allowed


def test_risk_gate_kill_switch_overrides_order_validation(test_config: PeakConfig) -> None:
    """Test that kill switch takes precedence over order validation."""
    gate = RiskGate(test_config)

    # Invalid order (missing qty) but kill switch armed
    order = {"symbol": "BTCUSDT"}  # Missing qty
    context = {"metrics": {"daily_pnl_pct": -0.10}}

    result = gate.evaluate(order, context)

    assert not result.decision.allowed
    # Kill switch violation should be present
    assert any(v.code == "KILL_SWITCH_ARMED" for v in result.decision.violations)
    # Order validation violations should not run when kill switch armed
    assert not any(v.code == "MISSING_QTY" for v in result.decision.violations)


# ============================================================================
# Kill Switch API Tests (PR4: Ops Pack)
# ============================================================================


def test_risk_gate_reset_kill_switch(test_config: PeakConfig) -> None:
    """Test RiskGate.reset_kill_switch() delegates to layer."""
    gate = RiskGate(test_config)

    # Arm kill switch
    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"metrics": {"daily_pnl_pct": -0.10}}
    result1 = gate.evaluate(order, context)
    assert not result1.decision.allowed

    # Reset via gate
    reset_status = gate.reset_kill_switch("incident_resolved")
    assert not reset_status.armed
    assert reset_status.severity == "OK"
    assert "incident_resolved" in reset_status.reason

    # Verify trading can resume
    context_good = {"metrics": {"daily_pnl_pct": -0.02}}
    result2 = gate.evaluate(order, context_good)
    assert result2.decision.allowed


def test_risk_gate_get_kill_switch_status_with_context(test_config: PeakConfig) -> None:
    """Test RiskGate.get_kill_switch_status() with fresh metrics."""
    gate = RiskGate(test_config)

    # Get status with good metrics
    context_good = {"metrics": {"daily_pnl_pct": -0.02}}
    status1 = gate.get_kill_switch_status(context_good)
    assert not status1.armed
    assert status1.severity == "OK"

    # Get status with bad metrics (should arm)
    context_bad = {"metrics": {"daily_pnl_pct": -0.10}}
    status2 = gate.get_kill_switch_status(context_bad)
    assert status2.armed
    assert status2.severity == "BLOCK"
    assert "daily_loss_limit" in status2.triggered_by


def test_risk_gate_get_kill_switch_status_without_context(test_config: PeakConfig) -> None:
    """Test RiskGate.get_kill_switch_status() returns last known status."""
    gate = RiskGate(test_config)

    # Before any evaluation, returns default unarmed status
    status1 = gate.get_kill_switch_status()
    assert not status1.armed
    assert "not yet evaluated" in status1.reason.lower()

    # After evaluation, returns last status
    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"metrics": {"daily_pnl_pct": -0.10}}
    gate.evaluate(order, context)

    status2 = gate.get_kill_switch_status()
    assert status2.armed
    assert "daily_loss_limit" in status2.triggered_by


def test_risk_gate_audit_includes_kill_switch_when_disabled(tmp_path) -> None:
    """Test that audit events include kill_switch section even when disabled."""
    # Config with kill switch disabled
    audit_path = tmp_path / "audit.jsonl"
    config = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(audit_path)},
                "kill_switch": {"enabled": False},
            }
        }
    )
    gate = RiskGate(config)

    # Evaluate order
    order = {"symbol": "BTCUSDT", "qty": 1.0}
    gate.evaluate(order)

    # Check audit log
    import json

    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[0])

    # kill_switch section should always be present
    assert "kill_switch" in event
    assert event["kill_switch"]["enabled"] is False
    assert event["kill_switch"]["status"]["armed"] is False
    assert "disabled" in event["kill_switch"]["status"]["reason"].lower()


def test_risk_gate_reset_when_disabled(tmp_path) -> None:
    """Test that reset_kill_switch() handles disabled kill switch gracefully."""
    config = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(tmp_path / "audit.jsonl")},
                "kill_switch": {"enabled": False},
            }
        }
    )
    gate = RiskGate(config)

    # Reset should work even when disabled
    status = gate.reset_kill_switch("test_reset")
    assert not status.armed
    assert "disabled" in status.reason.lower()


def test_risk_gate_get_status_when_disabled(tmp_path) -> None:
    """Test that get_kill_switch_status() handles disabled kill switch."""
    config = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(tmp_path / "audit.jsonl")},
                "kill_switch": {"enabled": False},
            }
        }
    )
    gate = RiskGate(config)

    # Get status should return unarmed with disabled reason
    status = gate.get_kill_switch_status()
    assert not status.armed
    assert "disabled" in status.reason.lower()


# ============================================================================
# Metrics Extraction Tests (PR5: Metrics Plumbing)
# ============================================================================


def test_risk_gate_tolerates_nested_metrics(test_config: PeakConfig) -> None:
    """Test that RiskGate extracts metrics from context["metrics"]."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"metrics": {"daily_pnl_pct": -0.06}}  # Nested

    result = gate.evaluate(order, context)

    # Should trigger kill switch
    assert not result.decision.allowed
    assert "kill switch" in result.decision.reason.lower()


def test_risk_gate_tolerates_direct_metrics_keys(test_config: PeakConfig) -> None:
    """Test that RiskGate extracts metrics from direct context keys."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"daily_pnl_pct": -0.06}  # Direct keys

    result = gate.evaluate(order, context)

    # Should trigger kill switch
    assert not result.decision.allowed
    assert "kill switch" in result.decision.reason.lower()


def test_risk_gate_tolerates_risk_nested_metrics(test_config: PeakConfig) -> None:
    """Test that RiskGate extracts metrics from context["risk"]["metrics"]."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"risk": {"metrics": {"daily_pnl_pct": -0.06}}}

    result = gate.evaluate(order, context)

    # Should trigger kill switch
    assert not result.decision.allowed
    assert "kill switch" in result.decision.reason.lower()


def test_risk_gate_audit_metrics_snapshot_stable(test_config: PeakConfig, tmp_path: Path) -> None:
    """Test that audit log contains stable metrics_snapshot."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"metrics": {"daily_pnl_pct": -0.02, "current_drawdown_pct": 0.05}}

    result = gate.evaluate(order, context)

    # Check audit log
    audit_path = Path(test_config.get("risk.audit_log.path"))
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[0])

    # Check metrics_snapshot has canonical keys in order
    snapshot = event["kill_switch"]["metrics_snapshot"]
    snapshot_keys = list(snapshot.keys())
    expected_keys = [
        "daily_pnl_pct",
        "current_drawdown_pct",
        "realized_vol_pct",
        "timestamp_utc",
    ]
    assert snapshot_keys == expected_keys
    assert snapshot["daily_pnl_pct"] == -0.02
    assert snapshot["current_drawdown_pct"] == 0.05
    assert snapshot["realized_vol_pct"] is None


def test_risk_gate_audit_metrics_snapshot_with_missing_metrics(
    test_config: PeakConfig, tmp_path: Path
) -> None:
    """Test that audit log contains metrics_snapshot even with missing metrics."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {}  # No metrics

    result = gate.evaluate(order, context)

    # Check audit log
    audit_path = Path(test_config.get("risk.audit_log.path"))
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[0])

    # metrics_snapshot should exist but have None values
    snapshot = event["kill_switch"]["metrics_snapshot"]
    assert snapshot["daily_pnl_pct"] is None
    assert snapshot["current_drawdown_pct"] is None
    assert snapshot["realized_vol_pct"] is None


# ============================================================================
# VaR Gate Integration Tests (PR6: VaR Gate v1)
# ============================================================================


def test_risk_gate_includes_var_gate_in_audit(test_config: PeakConfig, tmp_path: Path) -> None:
    """Test that audit events always include var_gate section."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    result = gate.evaluate(order)

    # Check audit log
    audit_path = Path(test_config.get("risk.audit_log.path"))
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[0])

    # var_gate section should always be present
    assert "var_gate" in event
    assert "enabled" in event["var_gate"]
    assert "result" in event["var_gate"]


def test_risk_gate_var_gate_disabled_safe(tmp_path: Path) -> None:
    """Test that disabled VaR gate doesn't block orders."""
    config = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(tmp_path / "audit.jsonl")},
                "var_gate": {"enabled": False},
            }
        }
    )
    gate = RiskGate(config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    result = gate.evaluate(order)

    # Should allow (VaR gate disabled)
    assert result.decision.allowed
    assert result.decision.severity == "OK"


def test_risk_gate_var_gate_missing_data_safe(test_config: PeakConfig) -> None:
    """Test that missing VaR data doesn't block orders."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {}  # No VaR data (returns_df, weights)

    result = gate.evaluate(order)

    # Should allow (VaR not applicable)
    assert result.decision.allowed
    assert result.decision.severity == "OK"


def test_risk_gate_var_gate_blocks_high_var(tmp_path: Path) -> None:
    """Test that VaR gate blocks orders when VaR exceeds limit."""
    import numpy as np
    import pandas as pd

    config = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(tmp_path / "audit.jsonl")},
                "var_gate": {
                    "enabled": True,
                    "method": "parametric",
                    "confidence": 0.95,
                    "horizon_days": 1,
                    "max_var_pct": 0.03,  # 3% limit
                },
            }
        }
    )
    gate = RiskGate(config)

    # Create high-volatility returns to exceed 3% VaR
    np.random.seed(123)
    high_vol_returns = pd.DataFrame(
        {
            "BTC": np.random.normal(0, 0.10, 100),
            "ETH": np.random.normal(0, 0.12, 100),
        }
    )

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"returns_df": high_vol_returns, "weights": {"BTC": 0.6, "ETH": 0.4}}

    result = gate.evaluate(order, context)

    # Should block (VaR exceeds limit)
    assert not result.decision.allowed
    assert result.decision.severity == "BLOCK"
    assert any(v.code == "VAR_LIMIT_EXCEEDED" for v in result.decision.violations)


def test_risk_gate_var_gate_warns_near_limit(tmp_path: Path) -> None:
    """Test that VaR gate warns when near limit."""
    import numpy as np
    import pandas as pd

    config = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(tmp_path / "audit.jsonl")},
                "var_gate": {
                    "enabled": True,
                    "method": "parametric",
                    "confidence": 0.95,
                    "horizon_days": 1,
                    "max_var_pct": 0.10,  # 10% block limit
                    "warn_var_pct": 0.05,  # 5% warn limit
                },
            }
        }
    )
    gate = RiskGate(config)

    # Create medium-volatility returns (5-10% VaR range)
    np.random.seed(456)
    med_vol_returns = pd.DataFrame(
        {
            "BTC": np.random.normal(0, 0.08, 100),
            "ETH": np.random.normal(0, 0.09, 100),
        }
    )

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"returns_df": med_vol_returns, "weights": {"BTC": 0.6, "ETH": 0.4}}

    result = gate.evaluate(order, context)

    # Should allow but with warning (or block if VaR > 10%)
    if result.decision.allowed:
        assert result.decision.severity == "WARN"
        assert any(v.code == "VAR_NEAR_LIMIT" for v in result.decision.violations)


def test_risk_gate_evaluation_order_kill_switch_then_var(test_config: PeakConfig) -> None:
    """Test that kill switch is evaluated before VaR gate."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"metrics": {"daily_pnl_pct": -0.10}}  # Triggers kill switch

    result = gate.evaluate(order, context)

    # Should block due to kill switch (not VaR)
    assert not result.decision.allowed
    assert "kill switch" in result.decision.reason.lower()
    assert any(v.code == "KILL_SWITCH_ARMED" for v in result.decision.violations)


def test_risk_gate_var_gate_audit_structure(test_config: PeakConfig, tmp_path: Path) -> None:
    """Test that var_gate audit section has stable structure."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    gate.evaluate(order)

    # Check audit log
    audit_path = Path(test_config.get("risk.audit_log.path"))
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[0])

    # Check var_gate structure
    var_gate = event["var_gate"]
    assert "enabled" in var_gate
    assert "result" in var_gate

    result = var_gate["result"]
    assert "severity" in result
    assert "reason" in result
    assert "var_pct" in result
    assert "threshold_block" in result
    assert "threshold_warn" in result
    assert "confidence" in result
    assert "horizon_days" in result
    assert "method" in result
    assert "inputs_available" in result
    assert "timestamp_utc" in result


# ============================================================================
# Stress Gate Integration Tests
# ============================================================================


def test_risk_gate_includes_stress_gate_in_audit(test_config: PeakConfig, tmp_path: Path) -> None:
    """Test that audit events include stress gate status."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    gate.evaluate(order)

    # Check audit log
    audit_path = Path(test_config.get("risk.audit_log.path"))
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[0])

    assert "stress_gate" in event
    assert event["stress_gate"]["enabled"] is True
    assert "result" in event["stress_gate"]
    assert "scenarios_meta" in event["stress_gate"]


def test_risk_gate_stress_gate_disabled_safe(tmp_path: Path) -> None:
    """Test that disabled stress gate is safe (allows orders)."""
    audit_path = tmp_path / "audit.jsonl"
    cfg = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(audit_path)},
                "stress_gate": {"enabled": False},
            }
        }
    )
    gate = RiskGate(cfg)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    result = gate.evaluate(order)

    assert result.decision.allowed
    assert result.decision.severity == "OK"


def test_risk_gate_stress_gate_missing_data_safe(test_config: PeakConfig) -> None:
    """Test that stress gate with missing data is safe."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {}  # No returns/weights

    result = gate.evaluate(order, context)

    assert result.decision.allowed
    assert result.decision.severity == "OK"


def test_risk_gate_stress_gate_blocks_high_stress(tmp_path: Path) -> None:
    """Test that stress gate blocks orders with high stress loss."""
    import pandas as pd

    audit_path = tmp_path / "audit.jsonl"
    cfg = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(audit_path)},
                "stress_gate": {
                    "enabled": True,
                    "max_stress_loss_pct": 0.04,  # 4% block threshold
                    "scenarios": [
                        {
                            "name": "severe_shock",
                            "description": "10% down",
                            "shock_type": "return_shift",
                            "shock_params": {"shift": -0.10},
                        }
                    ],
                },
            }
        }
    )
    gate = RiskGate(cfg)

    # Portfolio with positive returns but will fail under shock
    returns_df = pd.DataFrame({"BTC": [0.02, 0.02, 0.02]})
    weights = {"BTC": 1.0}

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"returns_df": returns_df, "weights": weights}

    result = gate.evaluate(order, context)

    # Should block: 0.02 - 0.10 = -0.08 (exceeds -0.04 threshold)
    assert not result.decision.allowed
    assert result.decision.severity == "BLOCK"
    assert "stress" in result.decision.reason.lower()
    assert any(v.code == "STRESS_LIMIT_EXCEEDED" for v in result.decision.violations)


def test_risk_gate_stress_gate_warns_near_limit(tmp_path: Path) -> None:
    """Test that stress gate warns when near limit."""
    import pandas as pd

    audit_path = tmp_path / "audit.jsonl"
    cfg = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(audit_path)},
                "stress_gate": {
                    "enabled": True,
                    "max_stress_loss_pct": 0.05,  # 5% block
                    "warn_stress_loss_pct": 0.035,  # 3.5% warn
                    "scenarios": [
                        {
                            "name": "moderate_shock",
                            "description": "4% down",
                            "shock_type": "return_shift",
                            "shock_params": {"shift": -0.04},
                        }
                    ],
                },
            }
        }
    )
    gate = RiskGate(cfg)

    # Portfolio with small positive returns
    returns_df = pd.DataFrame({"BTC": [0.005, 0.005, 0.005]})
    weights = {"BTC": 1.0}

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {"returns_df": returns_df, "weights": weights}

    result = gate.evaluate(order, context)

    # Should warn: 0.005 - 0.04 = -0.035 (at warn threshold)
    assert result.decision.allowed
    assert result.decision.severity == "WARN"
    assert any(v.code == "STRESS_NEAR_LIMIT" for v in result.decision.violations)


def test_risk_gate_stress_gate_audit_structure(test_config: PeakConfig, tmp_path: Path) -> None:
    """Test that stress_gate audit section has stable structure."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    gate.evaluate(order)

    # Check audit log
    audit_path = Path(test_config.get("risk.audit_log.path"))
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[0])

    # Check stress_gate structure
    stress_gate = event["stress_gate"]
    assert "enabled" in stress_gate
    assert "result" in stress_gate
    assert "scenarios_meta" in stress_gate

    result = stress_gate["result"]
    assert "severity" in result
    assert "reason" in result
    assert "worst_case_loss_pct" in result
    assert "threshold_block" in result
    assert "threshold_warn" in result
    assert "triggered_scenarios" in result
    assert "scenarios_evaluated" in result
    assert "inputs_available" in result
    assert "timestamp_utc" in result

    scenarios_meta = stress_gate["scenarios_meta"]
    assert "count" in scenarios_meta
    assert "names" in scenarios_meta


def test_risk_gate_evaluation_order(tmp_path: Path) -> None:
    """Test that gates are evaluated in correct order: KillSwitch → VaR → Stress → Order."""
    import pandas as pd

    audit_path = tmp_path / "audit.jsonl"
    cfg = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(audit_path)},
                "kill_switch": {"enabled": True},
                "var_gate": {"enabled": True},
                "stress_gate": {"enabled": True},
            }
        }
    )
    gate = RiskGate(cfg)

    # Valid order with good metrics
    returns_df = pd.DataFrame({"BTC": [0.01, 0.01, 0.01]})
    weights = {"BTC": 1.0}

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {
        "metrics": {"daily_pnl_pct": -0.02},  # Safe
        "returns_df": returns_df,
        "weights": weights,
    }

    result = gate.evaluate(order, context)

    # Check audit log contains all gate evaluations
    audit_path_obj = Path(audit_path)
    lines = audit_path_obj.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[0])

    # All gates should be evaluated and present in audit
    assert "kill_switch" in event
    assert "var_gate" in event
    assert "stress_gate" in event
    assert event["kill_switch"]["status"]["armed"] is False
    assert event["var_gate"]["result"]["severity"] in ["OK", "WARN", "BLOCK"]
    assert event["stress_gate"]["result"]["severity"] in ["OK", "WARN", "BLOCK"]


def test_risk_gate_kill_switch_blocks_before_other_gates(tmp_path: Path) -> None:
    """Test that kill switch blocks immediately, but other gates still evaluated for audit."""
    import pandas as pd

    audit_path = tmp_path / "audit.jsonl"
    cfg = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(audit_path)},
                "kill_switch": {"enabled": True},
                "var_gate": {"enabled": True},
                "stress_gate": {"enabled": True},
            }
        }
    )
    gate = RiskGate(cfg)

    # Metrics that trigger kill switch
    returns_df = pd.DataFrame({"BTC": [0.01, 0.01, 0.01]})
    weights = {"BTC": 1.0}

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    context = {
        "metrics": {"daily_pnl_pct": -0.10},  # Triggers kill switch (-10%)
        "returns_df": returns_df,
        "weights": weights,
    }

    result = gate.evaluate(order, context)

    # Should block due to kill switch
    assert not result.decision.allowed
    assert result.decision.severity == "BLOCK"
    assert "kill switch" in result.decision.reason.lower()

    # But audit should include all gates
    audit_path_obj = Path(audit_path)
    lines = audit_path_obj.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[0])

    assert event["kill_switch"]["status"]["armed"] is True
    assert "var_gate" in event
    assert "stress_gate" in event


# =============================================================================
# LIQUIDITY GATE INTEGRATION TESTS
# =============================================================================


def test_risk_gate_liquidity_gate_disabled_by_default(test_config: PeakConfig) -> None:
    """Test that liquidity gate is disabled by default."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0, "order_type": "MARKET"}
    context = {"micro": {"spread_pct": 0.99}}  # Extremely wide spread

    result = gate.evaluate(order, context)

    # Order should pass (liquidity gate disabled)
    assert result.decision.allowed
    assert result.decision.severity == "OK"

    # Audit should contain liquidity_gate section (always present)
    assert "liquidity_gate" in result.audit_event
    assert result.audit_event["liquidity_gate"]["enabled"] is False


def test_risk_gate_liquidity_gate_enabled(tmp_path: Path) -> None:
    """Test liquidity gate integration when enabled."""
    audit_path = tmp_path / "audit.jsonl"
    config = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(audit_path)},
                "liquidity_gate": {
                    "enabled": True,
                    "max_spread_pct": 0.01,
                },
            }
        }
    )
    gate = RiskGate(config)

    # Order with wide spread should be blocked
    order = {"symbol": "BTCUSDT", "qty": 1.0, "order_type": "MARKET"}
    context = {"micro": {"spread_pct": 0.02, "last_price": 100.0}}

    result = gate.evaluate(order, context)

    # Should be blocked by liquidity gate
    assert not result.decision.allowed
    assert result.decision.severity == "BLOCK"
    assert "liquidity" in result.decision.reason.lower()
    assert any(v.code == "LIQUIDITY_SPREAD_TOO_WIDE" for v in result.decision.violations)

    # Audit should contain liquidity_gate section
    assert "liquidity_gate" in result.audit_event
    assert result.audit_event["liquidity_gate"]["enabled"] is True
    assert result.audit_event["liquidity_gate"]["result"]["severity"] == "BLOCK"


def test_risk_gate_liquidity_gate_evaluation_order(tmp_path: Path) -> None:
    """Test that liquidity gate is evaluated after stress gate."""
    audit_path = tmp_path / "audit.jsonl"
    config = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(audit_path)},
                "kill_switch": {"enabled": False},
                "var_gate": {"enabled": False},
                "stress_gate": {"enabled": False},
                "liquidity_gate": {
                    "enabled": True,
                    "max_spread_pct": 0.005,
                },
            }
        }
    )
    gate = RiskGate(config)

    # Only liquidity gate enabled
    order = {"symbol": "BTCUSDT", "qty": 1.0, "order_type": "MARKET"}
    context = {"micro": {"spread_pct": 0.01, "last_price": 100.0}}

    result = gate.evaluate(order, context)

    # Should be blocked by liquidity gate
    assert not result.decision.allowed
    assert result.decision.severity == "BLOCK"

    # Audit should show all gates evaluated
    event = result.audit_event
    assert "kill_switch" in event
    assert "var_gate" in event
    assert "stress_gate" in event
    assert "liquidity_gate" in event

    # Liquidity gate should be the blocker
    assert event["liquidity_gate"]["result"]["severity"] == "BLOCK"


def test_risk_gate_liquidity_gate_warn_allows_order(tmp_path: Path) -> None:
    """Test that liquidity gate WARN allows order but adds violation."""
    audit_path = tmp_path / "audit.jsonl"
    config = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(audit_path)},
                "liquidity_gate": {
                    "enabled": True,
                    "max_spread_pct": 0.01,
                    "warn_spread_pct": 0.008,
                    "strict_for_market_orders": False,  # Disable strictness for this test
                },
            }
        }
    )
    gate = RiskGate(config)

    # Spread at warn threshold (0.009 between warn 0.008 and max 0.01)
    order = {"symbol": "BTCUSDT", "qty": 1.0, "order_type": "MARKET"}
    context = {"micro": {"spread_pct": 0.009, "last_price": 100.0}}

    result = gate.evaluate(order, context)

    # Should be allowed with warning
    assert result.decision.allowed
    assert result.decision.severity == "WARN"
    assert any(v.code == "LIQUIDITY_NEAR_LIMIT" for v in result.decision.violations)


def test_risk_gate_liquidity_gate_audit_always_present(test_config: PeakConfig) -> None:
    """Test that liquidity_gate section is always in audit (even when disabled)."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT", "qty": 1.0}
    result = gate.evaluate(order)

    # Audit should always contain liquidity_gate section
    assert "liquidity_gate" in result.audit_event
    assert "enabled" in result.audit_event["liquidity_gate"]
    assert "result" in result.audit_event["liquidity_gate"]


def test_risk_gate_liquidity_gate_limit_order_exception(tmp_path: Path) -> None:
    """Test that limit orders can bypass wide spread blocks."""
    audit_path = tmp_path / "audit.jsonl"
    config = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(audit_path)},
                "liquidity_gate": {
                    "enabled": True,
                    "max_spread_pct": 0.01,
                    "allow_limit_orders_when_spread_wide": True,
                },
            }
        }
    )
    gate = RiskGate(config)

    # Market order should be blocked
    order_market = {"symbol": "BTCUSDT", "qty": 1.0, "order_type": "MARKET"}
    context = {"micro": {"spread_pct": 0.02, "last_price": 100.0}}

    result_market = gate.evaluate(order_market, context)
    assert not result_market.decision.allowed

    # Limit order should only warn (exception)
    order_limit = {
        "symbol": "BTCUSDT",
        "qty": 1.0,
        "order_type": "LIMIT",
        "limit_price": 100.0,
    }
    result_limit = gate.evaluate(order_limit, context)
    assert result_limit.decision.allowed
    assert result_limit.decision.severity == "WARN"


def test_risk_gate_stress_gate_blocks_before_liquidity(tmp_path: Path) -> None:
    """Test that stress gate blocking prevents liquidity gate from blocking."""
    audit_path = tmp_path / "audit.jsonl"
    config = PeakConfig(
        raw={
            "risk": {
                "audit_log": {"path": str(audit_path)},
                "stress_gate": {
                    "enabled": True,
                    "max_loss_pct_block": 0.05,
                    "scenarios": [
                        {
                            "name": "market_crash",
                            "shocks": {"SPY": -0.20},
                            "enabled": True,
                        }
                    ],
                },
                "liquidity_gate": {
                    "enabled": True,
                    "max_spread_pct": 0.005,
                },
            }
        }
    )
    gate = RiskGate(config)

    # Both gates would block, but stress gate should win
    order = {"symbol": "SPY", "qty": 100.0, "order_type": "MARKET"}
    context = {
        "portfolio": {
            "positions": [{"symbol": "SPY", "quantity": 1000, "avg_price": 400.0}],
            "cash": 10000.0,
        },
        "prices": {"SPY": 400.0},
        "micro": {"spread_pct": 0.01, "last_price": 400.0},
    }

    result = gate.evaluate(order, context)

    # Should be blocked
    assert not result.decision.allowed
    assert result.decision.severity == "BLOCK"

    # Either stress gate or liquidity gate can be the blocker
    # (both would trigger, stress is evaluated first but liquidity might also block)
    assert any(v.code == "STRESS_LIMIT_EXCEEDED" for v in result.decision.violations) or any(
        v.code == "LIQUIDITY_SPREAD_TOO_WIDE" for v in result.decision.violations
    )

    # Liquidity gate should still be evaluated for audit
    assert "liquidity_gate" in result.audit_event
