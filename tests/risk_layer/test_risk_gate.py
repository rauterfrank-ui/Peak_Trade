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
    assert event["kill_switch"]["armed"] is True
    assert "daily_loss_limit" in event["kill_switch"]["triggered_by"]


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
    assert event["kill_switch"]["armed"] is False
    assert len(event["kill_switch"]["triggered_by"]) == 0


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
