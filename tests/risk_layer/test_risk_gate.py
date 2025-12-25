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


def test_risk_gate_audit_log_contains_violations(
    test_config: PeakConfig, tmp_path: Path
) -> None:
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


def test_risk_gate_includes_context_in_audit(
    test_config: PeakConfig, tmp_path: Path
) -> None:
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

