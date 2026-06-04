"""Static + offline bounded Futures Testnet harness contract (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
Planning: futures_testnet_execute_harness_adapter_follow_up_pr_planning_v0
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_harness_contract_v0 import (
    FUTURES_EXECUTE_AUTHORITY_ADDED,
    HARNESS_EXECUTE_AUTHORIZED_NOW,
    HARNESS_PACKAGE_MARKER,
    default_offline_harness_config,
    evaluate_bounded_futures_testnet_harness_readiness,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    EVIDENCE_SOURCE_FUTURES_HARNESS,
    FUTURES_SESSION_AUTHORIZED_NOW,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_harness_contract_v0.py"
ADAPTER_TEST = REPO_ROOT / "tests" / "ops" / "test_bounded_futures_testnet_adapter_contract_v0.py"
FUTURES_CONTRACT_TEST = REPO_ROOT / "tests" / "ops" / "test_bounded_futures_testnet_contract_v0.py"

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_HARNESS_CONTRACT_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_FUTURES_TESTNET_HARNESS_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert HARNESS_PACKAGE_MARKER in HARNESS_MODULE.read_text(encoding="utf-8")


def test_harness_and_futures_session_not_authorized() -> None:
    assert HARNESS_EXECUTE_AUTHORIZED_NOW is False
    assert FUTURES_SESSION_AUTHORIZED_NOW is False
    assert FUTURES_EXECUTE_AUTHORITY_ADDED is False


def test_default_harness_readiness_passes_offline() -> None:
    config = default_offline_harness_config()
    result = evaluate_bounded_futures_testnet_harness_readiness(config)
    assert result["harness_contract_pass"] is True
    assert result["adapter_binding_pass"] is True
    assert result["evidence_template_pass"] is True
    assert result["fail_reasons"] == []
    assert result["harness_execute_authorized_now"] is False
    assert result["futures_testnet_instrument_exchange_proven"] is False


def test_operator_go_token_without_execute_go_fails() -> None:
    config = default_offline_harness_config()
    bad = type(config)(
        session_class=config.session_class,
        order_policy=config.order_policy,
        evidence_source=config.evidence_source,
        evidence_dir=config.evidence_dir,
        planned_duration_seconds=config.planned_duration_seconds,
        max_order_attempts=config.max_order_attempts,
        max_real_orders=config.max_real_orders,
        max_cancel_attempts=config.max_cancel_attempts,
        max_notional_eur=config.max_notional_eur,
        max_position_hold_seconds=config.max_position_hold_seconds,
        operator_go_token="GO_EXECUTE_FUTURES",
    )
    result = evaluate_bounded_futures_testnet_harness_readiness(bad)
    assert result["harness_contract_pass"] is False


def test_excessive_order_cap_fails() -> None:
    config = default_offline_harness_config()
    bad = type(config)(
        session_class=config.session_class,
        order_policy=config.order_policy,
        evidence_source=config.evidence_source,
        evidence_dir=config.evidence_dir,
        planned_duration_seconds=config.planned_duration_seconds,
        max_order_attempts=99,
        max_real_orders=config.max_real_orders,
        max_cancel_attempts=config.max_cancel_attempts,
        max_notional_eur=config.max_notional_eur,
        max_position_hold_seconds=config.max_position_hold_seconds,
        operator_go_token=None,
    )
    result = evaluate_bounded_futures_testnet_harness_readiness(bad)
    assert result["harness_contract_pass"] is False


def test_evidence_source_must_be_futures_harness() -> None:
    config = default_offline_harness_config()
    bad = type(config)(
        session_class=config.session_class,
        order_policy=config.order_policy,
        evidence_source="repo_native_session",
        evidence_dir=config.evidence_dir,
        planned_duration_seconds=config.planned_duration_seconds,
        max_order_attempts=config.max_order_attempts,
        max_real_orders=config.max_real_orders,
        max_cancel_attempts=config.max_cancel_attempts,
        max_notional_eur=config.max_notional_eur,
        max_position_hold_seconds=config.max_position_hold_seconds,
        operator_go_token=None,
    )
    result = evaluate_bounded_futures_testnet_harness_readiness(bad)
    assert result["harness_contract_pass"] is False


def test_adapter_and_futures_contract_tests_crosslink() -> None:
    assert ADAPTER_TEST.is_file()
    assert FUTURES_CONTRACT_TEST.is_file()


def test_harness_evidence_source_constant() -> None:
    config = default_offline_harness_config()
    assert config.evidence_source == EVIDENCE_SOURCE_FUTURES_HARNESS
