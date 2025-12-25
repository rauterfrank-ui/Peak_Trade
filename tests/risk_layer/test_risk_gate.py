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
    assert "passed basic validation" in result.decision.reason


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
