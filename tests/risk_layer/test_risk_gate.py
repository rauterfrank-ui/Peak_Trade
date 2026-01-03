"""
Tests for RiskGate
"""

import json
from pathlib import Path

import pytest

from src.core.peak_config import PeakConfig
from src.execution_simple.types import Order, OrderSide, OrderType
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
    assert any(v.code == "ORDER_CONVERSION_FAILED" for v in result.decision.violations)
    assert any("symbol" in v.message for v in result.decision.violations)


def test_risk_gate_blocks_order_with_missing_qty(test_config: PeakConfig) -> None:
    """Test that orders without qty are blocked."""
    gate = RiskGate(test_config)

    order = {"symbol": "BTCUSDT"}  # Missing qty
    result = gate.evaluate(order)

    assert not result.decision.allowed
    assert result.decision.severity == "BLOCK"
    assert len(result.decision.violations) >= 1
    assert any(v.code == "ORDER_CONVERSION_FAILED" for v in result.decision.violations)
    assert any("qty or quantity" in v.message for v in result.decision.violations)


def test_risk_gate_blocks_invalid_order_type(test_config: PeakConfig) -> None:
    """Test that non-dict orders are blocked."""
    gate = RiskGate(test_config)

    order = "not a dict"  # type: ignore[assignment]
    result = gate.evaluate(order)  # type: ignore[arg-type]

    assert not result.decision.allowed
    assert result.decision.severity == "BLOCK"
    assert any(v.code == "ORDER_CONVERSION_FAILED" for v in result.decision.violations)
    assert any("must be Order or dict" in v.message for v in result.decision.violations)


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
    assert any(v["code"] == "ORDER_CONVERSION_FAILED" for v in event["violations"])
    assert any("symbol" in v["message"] for v in event["violations"])


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
    """Test that adapter catches first missing field (symbol checked first)."""
    gate = RiskGate(test_config)

    order = {}  # Missing both symbol and qty
    result = gate.evaluate(order)

    assert not result.decision.allowed
    assert len(result.decision.violations) >= 1
    assert any(v.code == "ORDER_CONVERSION_FAILED" for v in result.decision.violations)
    # Adapter will fail on first missing field (symbol)
    assert any("symbol" in v.message for v in result.decision.violations)


def test_risk_gate_uses_default_audit_path_if_not_configured(tmp_path: Path) -> None:
    """Test that default audit path is used if not configured."""
    # Config without risk.audit_log.path
    cfg = PeakConfig(raw={})
    gate = RiskGate(cfg)

    # Should use default path
    assert gate.audit_log.path == Path("./logs/risk_audit.jsonl")


# ============================================================================
# Order Object Tests (PR2: canonical Order model)
# ============================================================================


def test_risk_gate_allows_order_object(test_config: PeakConfig) -> None:
    """Test that RiskGate accepts Order objects."""
    gate = RiskGate(test_config)

    order = Order(symbol="BTCUSDT", side=OrderSide.BUY, quantity=1.0, price=50000.0)
    result = gate.evaluate(order)

    assert result.decision.allowed
    assert result.decision.severity == "OK"
    assert len(result.decision.violations) == 0


def test_risk_gate_audit_serializes_order_object(test_config: PeakConfig, tmp_path: Path) -> None:
    """Test that Order objects are serialized deterministically in audit log."""
    gate = RiskGate(test_config)

    order = Order(
        symbol="ETHUSDT",
        side=OrderSide.SELL,
        quantity=2.0,
        price=3000.0,
        order_type=OrderType.LIMIT,
    )
    result = gate.evaluate(order)

    # Check audit log
    audit_path = Path(test_config.get("risk.audit_log.path"))
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[0])

    # Check order is serialized correctly
    assert event["order"]["symbol"] == "ETHUSDT"
    assert event["order"]["side"] == "sell"
    assert event["order"]["quantity"] == 2.0
    assert event["order"]["price"] == 3000.0
    assert event["order"]["order_type"] == "limit"
    assert "notional" in event["order"]


def test_risk_gate_backward_compatible_with_dict(test_config: PeakConfig) -> None:
    """Test that dict input still works (backward compatibility)."""
    gate = RiskGate(test_config)

    # Old-style dict input
    order_dict = {"symbol": "BTCUSDT", "qty": 1.5, "side": "BUY"}
    result = gate.evaluate(order_dict)

    assert result.decision.allowed
    assert result.decision.severity == "OK"


def test_risk_gate_converts_dict_to_order_internally(test_config: PeakConfig) -> None:
    """Test that dict is converted to Order internally and serialized consistently."""
    gate = RiskGate(test_config)

    order_dict = {"symbol": "SOLUSDT", "qty": 10.0, "price": 100.0}
    result = gate.evaluate(order_dict)

    # Check audit log has deterministic serialization
    audit_path = Path(test_config.get("risk.audit_log.path"))
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    event = json.loads(lines[0])

    # Should have all Order fields
    assert event["order"]["symbol"] == "SOLUSDT"
    assert event["order"]["quantity"] == 10.0  # Note: normalized to "quantity"
    assert event["order"]["price"] == 100.0
    assert event["order"]["side"] == "buy"  # default
    assert event["order"]["order_type"] == "market"  # default


def test_risk_gate_blocks_invalid_dict_conversion(test_config: PeakConfig) -> None:
    """Test that invalid dict raises appropriate violation."""
    gate = RiskGate(test_config)

    # Missing qty
    order_dict = {"symbol": "BTCUSDT"}
    result = gate.evaluate(order_dict)

    assert not result.decision.allowed
    assert result.decision.severity == "BLOCK"
    assert any(v.code == "ORDER_CONVERSION_FAILED" for v in result.decision.violations)
    assert any("qty or quantity" in v.message for v in result.decision.violations)
