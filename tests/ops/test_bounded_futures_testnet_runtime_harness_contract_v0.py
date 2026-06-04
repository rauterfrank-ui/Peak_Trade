"""Static + offline bounded Futures Testnet runtime harness contract (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
Planning: futures_runtime_harness_exchange_impl_follow_up_pr_planning_v0
"""

from __future__ import annotations

from pathlib import Path

from src.ops.bounded_futures_testnet_runtime_harness_contract_v0 import (
    ARCHIVE_FUTURES_HARNESS_FILENAME,
    RUNTIME_HARNESS_EXECUTE_AUTHORIZED_NOW,
    RUNTIME_HARNESS_PACKAGE_MARKER,
    default_offline_runtime_harness_descriptor,
    evaluate_bounded_futures_testnet_runtime_harness_readiness,
)
from src.ops.bounded_futures_testnet_harness_contract_v0 import HARNESS_EXECUTE_AUTHORIZED_NOW

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_runtime_harness_contract_v0.py"
)
HARNESS_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_harness_contract_v0.py"
EXCHANGE_IMPL_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_bounded_futures_testnet_exchange_impl_contract_v0.py"
)

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_RUNTIME_HARNESS_CONTRACT_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_FUTURES_TESTNET_RUNTIME_HARNESS_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert RUNTIME_HARNESS_PACKAGE_MARKER in RUNTIME_MODULE.read_text(encoding="utf-8")


def test_runtime_harness_not_authorized() -> None:
    assert RUNTIME_HARNESS_EXECUTE_AUTHORIZED_NOW is False
    assert HARNESS_EXECUTE_AUTHORIZED_NOW is False


def test_default_runtime_descriptor_passes() -> None:
    descriptor = default_offline_runtime_harness_descriptor()
    result = evaluate_bounded_futures_testnet_runtime_harness_readiness(descriptor)
    assert result["runtime_harness_contract_pass"] is True
    assert result["exchange_impl_contract_pass"] is True
    assert result["offline_harness_contract_pass"] is True


def test_archive_harness_filename_constant() -> None:
    assert ARCHIVE_FUTURES_HARNESS_FILENAME == "bounded_futures_testnet_session_harness.py"


def test_runtime_script_in_repo_fails() -> None:
    base = default_offline_runtime_harness_descriptor()
    bad = type(base)(
        harness_tier=base.harness_tier,
        archive_harness_filename=base.archive_harness_filename,
        evidence_dir_must_be_under_archive=base.evidence_dir_must_be_under_archive,
        exchange_impl=base.exchange_impl,
        harness_config=base.harness_config,
        runtime_script_present_in_repo=True,
        operator_go_token=None,
    )
    result = evaluate_bounded_futures_testnet_runtime_harness_readiness(bad)
    assert result["runtime_harness_contract_pass"] is False


def test_exchange_impl_and_harness_tests_crosslink() -> None:
    assert EXCHANGE_IMPL_TEST.is_file()
    assert HARNESS_MODULE.is_file()
