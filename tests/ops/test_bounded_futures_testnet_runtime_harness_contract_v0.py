"""Static + offline bounded Futures Testnet runtime harness impl contract (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
Planning: futures_runtime_harness_exchange_impl_follow_up_pr_planning_v0
"""

from __future__ import annotations

from pathlib import Path

from src.ops.bounded_futures_testnet_contract_v0 import FUTURES_SESSION_AUTHORIZED_NOW
from src.ops.bounded_futures_testnet_runtime_harness_contract_v0 import (
    ARCHIVE_HARNESS_SCRIPT_PRESENT,
    PACKAGE_MARKER,
    RUNTIME_HARNESS_EXECUTE_ALLOWED,
    RUNTIME_HARNESS_NETWORK_ALLOWED,
    default_offline_runtime_harness_impl_descriptor,
    validate_futures_testnet_runtime_harness_impl_descriptor,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_HARNESS_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_runtime_harness_contract_v0.py"
)
EXCHANGE_IMPL_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_bounded_futures_testnet_exchange_impl_contract_v0.py"
)
HARNESS_TEST = REPO_ROOT / "tests" / "ops" / "test_bounded_futures_testnet_harness_contract_v0.py"

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_RUNTIME_HARNESS_CONTRACT_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_FUTURES_TESTNET_RUNTIME_HARNESS_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in RUNTIME_HARNESS_MODULE.read_text(encoding="utf-8")


def test_runtime_harness_guards_not_authorized() -> None:
    assert RUNTIME_HARNESS_EXECUTE_ALLOWED is False
    assert RUNTIME_HARNESS_NETWORK_ALLOWED is False
    assert ARCHIVE_HARNESS_SCRIPT_PRESENT is False
    assert FUTURES_SESSION_AUTHORIZED_NOW is False


def test_default_runtime_harness_impl_passes() -> None:
    descriptor = default_offline_runtime_harness_impl_descriptor()
    result = validate_futures_testnet_runtime_harness_impl_descriptor(descriptor)
    assert result["runtime_harness_impl_pass"] is True
    assert result["pe9_harness_readiness_pass"] is True
    assert result["exchange_impl_pass"] is True
    assert result["fail_reasons"] == []


def test_archive_script_required_fails() -> None:
    descriptor = default_offline_runtime_harness_impl_descriptor()
    bad = type(descriptor)(
        impl_id=descriptor.impl_id,
        exchange_impl_id=descriptor.exchange_impl_id,
        harness_config=descriptor.harness_config,
        exchange_impl=descriptor.exchange_impl,
        archive_script_required=True,
        runtime_started_allowed=descriptor.runtime_started_allowed,
        scheduler_started_allowed=descriptor.scheduler_started_allowed,
    )
    result = validate_futures_testnet_runtime_harness_impl_descriptor(bad)
    assert result["runtime_harness_impl_pass"] is False


def test_runtime_started_allowed_fails() -> None:
    descriptor = default_offline_runtime_harness_impl_descriptor()
    bad = type(descriptor)(
        impl_id=descriptor.impl_id,
        exchange_impl_id=descriptor.exchange_impl_id,
        harness_config=descriptor.harness_config,
        exchange_impl=descriptor.exchange_impl,
        archive_script_required=descriptor.archive_script_required,
        runtime_started_allowed=True,
        scheduler_started_allowed=descriptor.scheduler_started_allowed,
    )
    result = validate_futures_testnet_runtime_harness_impl_descriptor(bad)
    assert result["runtime_harness_impl_pass"] is False


def test_pe9_and_exchange_impl_tests_crosslink() -> None:
    assert EXCHANGE_IMPL_TEST.is_file()
    assert HARNESS_TEST.is_file()
