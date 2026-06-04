"""Static + offline repo-native bounded order-cap contract (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
Closeout: bounded_normal_testnet_session_closeout_review_v0_20260603T215843Z
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.bounded_testnet_order_cap_contract_v0 import (
    CLI_WIRING_COMPLETE_MARKER,
    DEFAULT_ORDER_POLICY,
    DEFAULT_SESSION_CLASS,
    PACKAGE_MARKER,
    REQUIRED_BOUNDED_ORDER_CAP_CLI_FLAGS,
    REQUIRED_EVIDENCE_FIELD_NAMES,
    default_bounded_normal_v0_spec,
    evaluate_bounded_order_cap_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_TESTNET_SESSION = REPO_ROOT / "scripts" / "run_testnet_session.py"
CONTRACT_MODULE = REPO_ROOT / "src" / "ops" / "bounded_testnet_order_cap_contract_v0.py"
ENTRYPOINT_FAIL_CLOSED_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_run_testnet_session_entrypoint_fail_closed_contract_v0.py"
)
WALLCLOCK_EMITTER_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_runtime_wallclock_evidence_emitter_contract_v0.py"
)
SECTION5_GAP_OWNER_MAP = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)

TEST_PACKAGE_MARKER = "REPO_NATIVE_BOUNDED_ORDER_CAP_CONTRACT_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "REPO_NATIVE_BOUNDED_ORDER_CAP_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)
CLOSEOUT_BUNDLE_SUFFIX = "bounded_normal_testnet_session_closeout_review_v0_20260603T215843Z"

CONTRACT_GOVERNANCE_TOKEN_MAP: dict[str, str] = {
    "NORMAL_TESTNET_RUN_AUTHORIZED_NOW": "RUN_TESTNET_SESSION_ALLOWED_NOW=false",
    "REPO_NATIVE_ENTRYPOINT_CAP_WIRING_COMPLETE": CLI_WIRING_COMPLETE_MARKER,
    "BOUNDED_ORDER_CAP_CONTRACT_DEFINED": PACKAGE_MARKER,
}


def _run_testnet_source() -> str:
    return RUN_TESTNET_SESSION.read_text(encoding="utf-8")


def _accepted_archive_harness_evidence() -> dict:
    """Shape from bounded_normal_testnet_session_bounded_execute_v0_20260603T215200Z."""
    return {
        "session_class": DEFAULT_SESSION_CLASS,
        "order_policy": DEFAULT_ORDER_POLICY,
        "order_attempt_count": 1,
        "real_orders_created_count": 1,
        "cancel_or_close_attempt_count": 1,
        "cancel_or_close_attempted": True,
        "cancel_or_close_evidence_valid": True,
        "order_notional_eur": 2.8296,
        "order_notional_within_cap": True,
        "position_flattened_by_end": True,
        "risk_killswitch_scope_active": True,
        "risk_killswitch_scope_pass": True,
        "scheduler_started": False,
        "runtime_started": False,
        "live_env_present": False,
    }


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in CONTRACT_MODULE.read_text(encoding="utf-8")


def test_contract_governance_tokens_map_to_repo_native_markers() -> None:
    source = _run_testnet_source()
    for external_token, repo_marker in CONTRACT_GOVERNANCE_TOKEN_MAP.items():
        if repo_marker.startswith("BOUNDED"):
            assert repo_marker in CONTRACT_MODULE.read_text(encoding="utf-8")
        else:
            assert repo_marker in source, f"{external_token} -> missing {repo_marker!r}"


def test_section5_preflight_remains_blocked() -> None:
    gap_map = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    final_lines = gap_map.split("## Final Machine Lines", 1)[-1]
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in final_lines
    assert "PREFLIGHT_REMAINS_BLOCKED=false" not in final_lines


def test_entrypoint_fail_closed_guard_still_present() -> None:
    assert ENTRYPOINT_FAIL_CLOSED_TEST.is_file()
    assert "RUN_TESTNET_SESSION_ENTRYPOINT_FAIL_CLOSED_CONTRACT_V0=true" in (
        ENTRYPOINT_FAIL_CLOSED_TEST.read_text(encoding="utf-8")
    )


def test_wallclock_emitter_guard_still_present() -> None:
    assert WALLCLOCK_EMITTER_TEST.is_file()


def test_bounded_order_cap_cli_flags_present_on_entrypoint() -> None:
    """Repo-native entrypoint wires contract-required bounded cap CLI flags."""
    entrypoint = _run_testnet_source()
    contract_source = CONTRACT_MODULE.read_text(encoding="utf-8")
    assert "add_bounded_order_cap_cli_arguments(parser)" in entrypoint
    for flag in REQUIRED_BOUNDED_ORDER_CAP_CLI_FLAGS:
        assert flag in contract_source, f"missing CLI flag definition: {flag}"


def test_run_testnet_session_declares_entrypoint_cap_wiring_complete() -> None:
    source = _run_testnet_source()
    assert "RUN_TESTNET_SESSION_ALLOWED_NOW=false" in source
    assert CLI_WIRING_COMPLETE_MARKER in source
    assert "REPO_NATIVE_BOUNDED_ORDER_CAP_CLI_WIRING_PENDING=true" not in source


def test_default_spec_matches_bounded_normal_v0_charter() -> None:
    spec = default_bounded_normal_v0_spec()
    assert spec.session_class == DEFAULT_SESSION_CLASS
    assert spec.order_policy == DEFAULT_ORDER_POLICY
    assert spec.max_real_orders == 1
    assert spec.max_order_attempts == 1
    assert spec.max_cancel_attempts == 1
    assert spec.max_notional_eur == 10.0
    assert spec.max_position_hold_seconds == 60
    assert spec.position_must_be_flattened is True


def test_evaluator_accepts_archive_harness_evidence_shape() -> None:
    result = evaluate_bounded_order_cap_evidence(_accepted_archive_harness_evidence())
    assert result["bounded_order_cap_pass"] is True
    assert result["fail_reasons"] == []


def test_evaluator_rejects_cap_breach() -> None:
    evidence = _accepted_archive_harness_evidence()
    evidence["real_orders_created_count"] = 2
    result = evaluate_bounded_order_cap_evidence(evidence)
    assert result["bounded_order_cap_pass"] is False
    assert any("real_orders_created_count" in r for r in result["fail_reasons"])


def test_evaluator_rejects_missing_cancel_when_order_created() -> None:
    evidence = _accepted_archive_harness_evidence()
    evidence["cancel_or_close_attempted"] = False
    evidence["cancel_or_close_evidence_valid"] = False
    result = evaluate_bounded_order_cap_evidence(evidence)
    assert result["bounded_order_cap_pass"] is False


def test_required_evidence_field_names_documented() -> None:
    assert len(REQUIRED_EVIDENCE_FIELD_NAMES) >= 10
    assert "session_class" in REQUIRED_EVIDENCE_FIELD_NAMES
    assert "risk_killswitch_scope_pass" in REQUIRED_EVIDENCE_FIELD_NAMES


def test_closeout_bundle_suffix_documented_in_test() -> None:
    assert CLOSEOUT_BUNDLE_SUFFIX in Path(__file__).read_text(encoding="utf-8")
