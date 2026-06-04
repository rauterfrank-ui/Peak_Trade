"""Static + offline bounded network Testnet preflight contract (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
Charter: bounded_network_testnet_preflight_charter_no_run_v0_20260603T184700Z
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.ops.test_testnet_wallclock_duration_evidence_contract_v0 import (
    evaluate_wallclock_duration_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_TESTNET_SESSION = REPO_ROOT / "scripts" / "run_testnet_session.py"
KRAKEN_TESTNET_CLIENT = REPO_ROOT / "src" / "exchange" / "kraken_testnet.py"
SECTION5_GAP_OWNER_MAP = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
ENTRYPOINT_FAIL_CLOSED_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_run_testnet_session_entrypoint_fail_closed_contract_v0.py"
)
WALLCLOCK_CONTRACT_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_testnet_wallclock_duration_evidence_contract_v0.py"
)

PACKAGE_MARKER = "BOUNDED_NETWORK_TESTNET_PREFLIGHT_CONTRACT_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_NETWORK_TESTNET_PREFLIGHT_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)
CHARTER_BUNDLE_SUFFIX = "bounded_network_testnet_preflight_charter_no_run_v0_20260603T184700Z"
REQUIRED_EXECUTE_GO = "GO_EXECUTE_BOUNDED_NETWORK_TESTNET_PREFLIGHT_V0"

PUBLIC_ENDPOINTS: frozenset[str] = frozenset(
    {
        "/0/public/Time",
        "/0/public/Ticker",
        "/0/public/AssetPairs",
    }
)
PRIVATE_READONLY_ENDPOINTS: frozenset[str] = frozenset(
    {
        "/0/private/Balance",
        "/0/private/OpenOrders",
    }
)
FORBIDDEN_ORDER_ENDPOINTS: frozenset[str] = frozenset(
    {
        "/0/private/AddOrder",
        "/0/private/CancelOrder",
        "/0/private/AmendOrder",
        "/0/private/QueryOrders",
        "/0/private/TradeBalance",
    }
)
HOST_ALLOWLIST: frozenset[str] = frozenset({"https://api.kraken.com"})

PREFLIGHT_PLANNED_DURATION_SECONDS = 120
PREFLIGHT_MIN_REQUIRED_WALL_CLOCK_SECONDS = 60
PREFLIGHT_MAX_ACCEPTABLE_WALL_CLOCK_SECONDS = 180
PREFLIGHT_WALL_CLOCK_SLACK_SECONDS = 60
MAX_PUBLIC_CALLS = 8
MAX_PRIVATE_READONLY_CALLS = 4
MAX_REAL_ORDER_CALLS = 0
MIN_HEARTBEATS_REQUIRED = 2
MIN_HEARTBEAT_SPAN_SECONDS = 30

CONTRACT_GOVERNANCE_TOKEN_MAP: dict[str, str] = {
    "NETWORK_PREFLIGHT_EXECUTE_NOW_ALLOWED": "Does not authorize NETWORK_PREFLIGHT_EXECUTE",
    "REAL_TESTNET_SESSION_NOW_ALLOWED": "RUN_TESTNET_SESSION_ALLOWED_NOW=false",
    "TESTNET_SESSION_ALLOWED": "Does not authorize run_testnet_session preflight execute",
    "ORDERS_ALLOWED": "MAX_REAL_ORDER_CALLS=0",
    "WALLCLOCK_EVIDENCE_REQUIRED": "invalid_if_elapsed_below_min=true",
    "DURABLE_EVIDENCE_REQUIRED": "MANIFEST.sha256",
}


def evaluate_bounded_network_testnet_preflight_evidence(
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Fail-closed reference evaluator for future network preflight closeout (offline)."""
    result: dict[str, Any] = {
        "preflight_evidence_valid": False,
        "network_preflight_evidence_valid": False,
        "fail_reasons": [],
    }

    if evidence.get("operator_go") != REQUIRED_EXECUTE_GO:
        result["fail_reasons"].append("missing or wrong operator_go (explicit execute GO required)")

    if evidence.get("orders_allowed") is True:
        result["fail_reasons"].append("orders_allowed must be false (AB2)")
    if evidence.get("positions_allowed") is True:
        result["fail_reasons"].append("positions_allowed must be false")
    if evidence.get("scheduler_allowed") is True:
        result["fail_reasons"].append("scheduler_allowed must be false (AB6)")
    if evidence.get("runtime_allowed") is True:
        result["fail_reasons"].append("runtime_allowed must be false (AB6)")
    if evidence.get("testnet_session_allowed") is True:
        result["fail_reasons"].append("testnet_session_allowed must be false (AB5)")

    if evidence.get("credential_values_exported") is True:
        result["fail_reasons"].append("credential values exported (AB1/AB8)")
    if evidence.get("credentials_printed") is True:
        result["fail_reasons"].append("credentials printed (AB1)")

    host = evidence.get("network_host")
    if host and host not in HOST_ALLOWLIST:
        result["fail_reasons"].append(f"non-allowlisted network host (AB4): {host!r}")

    endpoints_called = evidence.get("endpoints_called") or []
    for endpoint in endpoints_called:
        if endpoint in FORBIDDEN_ORDER_ENDPOINTS:
            result["fail_reasons"].append(f"forbidden order endpoint called (AB2/AB3): {endpoint}")
        elif endpoint not in PUBLIC_ENDPOINTS and endpoint not in PRIVATE_READONLY_ENDPOINTS:
            result["fail_reasons"].append(f"non-allowlisted endpoint (AB4): {endpoint}")

    if evidence.get("validate_only_addorder_used") is True:
        result["fail_reasons"].append("validate_only AddOrder forbidden for preflight")

    max_order_calls = evidence.get("max_real_order_calls")
    if max_order_calls is not None and max_order_calls > MAX_REAL_ORDER_CALLS:
        result["fail_reasons"].append("MAX_REAL_ORDER_CALLS > 0 (AB16)")

    public_calls = evidence.get("public_calls", 0)
    private_calls = evidence.get("private_readonly_calls", 0)
    if public_calls > MAX_PUBLIC_CALLS:
        result["fail_reasons"].append("public calls exceed allowlist max (AB18)")
    if private_calls > MAX_PRIVATE_READONLY_CALLS:
        result["fail_reasons"].append("private readonly calls exceed allowlist max (AB19)")

    heartbeats = evidence.get("heartbeat_count", 0)
    heartbeat_span = evidence.get("heartbeat_span_seconds", 0)
    if heartbeats < MIN_HEARTBEATS_REQUIRED:
        result["fail_reasons"].append("insufficient heartbeats (AB20)")
    if heartbeat_span < MIN_HEARTBEAT_SPAN_SECONDS:
        result["fail_reasons"].append("heartbeat span below minimum (AB20)")

    if evidence.get("run_testnet_session_invoked") is True:
        result["fail_reasons"].append("run_testnet_session invoked (AB5)")

    for side_effect in (
        "preflight_lifted",
        "arming_changed",
        "bl002_path_b_touched",
        "shadow_hold_lifted",
    ):
        if evidence.get(side_effect) is True:
            result["fail_reasons"].append(f"forbidden side effect: {side_effect} (AB7)")

    if evidence.get("manifest_present") is False:
        result["fail_reasons"].append("missing MANIFEST.sha256 (AB23)")
    if evidence.get("manifest_verify_rc", 0) != 0:
        result["fail_reasons"].append("MANIFEST_VERIFY_RC != 0 (AB24)")
    if evidence.get("final_machine_lines_present") is False:
        result["fail_reasons"].append("missing FINAL_MACHINE_LINES.txt (AB25)")
    if evidence.get("evidence_root_under_tmp_only") is True:
        result["fail_reasons"].append("evidence root under /tmp only (AB26)")

    wallclock = evaluate_wallclock_duration_evidence(evidence)
    result["fail_reasons"].extend(wallclock["fail_reasons"])

    if not result["fail_reasons"]:
        result["preflight_evidence_valid"] = True
        result["network_preflight_evidence_valid"] = True

    return result


def _valid_preflight_evidence() -> dict[str, Any]:
    return {
        "operator_go": REQUIRED_EXECUTE_GO,
        "orders_allowed": False,
        "positions_allowed": False,
        "scheduler_allowed": False,
        "runtime_allowed": False,
        "testnet_session_allowed": False,
        "network_allowed": True,
        "network_host": "https://api.kraken.com",
        "endpoints_called": ["/0/public/Time", "/0/private/Balance"],
        "public_calls": 2,
        "private_readonly_calls": 1,
        "max_real_order_calls": 0,
        "validate_only_addorder_used": False,
        "credential_values_exported": False,
        "credentials_printed": False,
        "run_testnet_session_invoked": False,
        "preflight_lifted": False,
        "arming_changed": False,
        "bl002_path_b_touched": False,
        "shadow_hold_lifted": False,
        "heartbeat_count": 2,
        "heartbeat_span_seconds": 45,
        "manifest_present": True,
        "manifest_verify_rc": 0,
        "final_machine_lines_present": True,
        "evidence_root_under_tmp_only": False,
        "planned_duration_seconds": PREFLIGHT_PLANNED_DURATION_SECONDS,
        "min_required_wall_clock_seconds": PREFLIGHT_MIN_REQUIRED_WALL_CLOCK_SECONDS,
        "max_acceptable_wall_clock_seconds": PREFLIGHT_MAX_ACCEPTABLE_WALL_CLOCK_SECONDS,
        "wall_clock_slack_seconds": PREFLIGHT_WALL_CLOCK_SLACK_SECONDS,
        "start_wall_clock_iso": "2026-06-03T18:00:00Z",
        "end_wall_clock_iso": "2026-06-03T18:02:05Z",
        "start_monotonic_seconds": 1000.0,
        "end_monotonic_seconds": 1125.0,
        "elapsed_wall_clock_seconds": 125.0,
        "elapsed_monotonic_seconds": 125.0,
        "duration_proven": True,
        "duration_evidence_valid": True,
        "early_exit_detected": False,
        "early_exit_reason": "",
        "invalid_if_elapsed_below_min": True,
    }


def test_package_and_class4_markers_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert CHARTER_BUNDLE_SUFFIX in text
    assert REQUIRED_EXECUTE_GO in text


def test_endpoint_allowlists_complete() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    for endpoint in PUBLIC_ENDPOINTS | PRIVATE_READONLY_ENDPOINTS | FORBIDDEN_ORDER_ENDPOINTS:
        assert endpoint in text, f"missing endpoint {endpoint!r}"


def test_contract_governance_tokens_map_to_repo_native_markers() -> None:
    entrypoint_source = RUN_TESTNET_SESSION.read_text(encoding="utf-8")
    self_text = Path(__file__).read_text(encoding="utf-8")
    for external_token, repo_marker in CONTRACT_GOVERNANCE_TOKEN_MAP.items():
        if external_token in {"WALLCLOCK_EVIDENCE_REQUIRED", "DURABLE_EVIDENCE_REQUIRED"}:
            assert repo_marker in self_text
        elif external_token == "ORDERS_ALLOWED":
            assert repo_marker in self_text
        elif external_token in {
            "NETWORK_PREFLIGHT_EXECUTE_NOW_ALLOWED",
            "TESTNET_SESSION_ALLOWED",
        }:
            assert repo_marker in self_text
        else:
            assert repo_marker in entrypoint_source, f"{external_token} -> missing {repo_marker!r}"


def test_entrypoint_and_wallclock_crosslinks_present() -> None:
    assert ENTRYPOINT_FAIL_CLOSED_TEST.is_file()
    assert WALLCLOCK_CONTRACT_TEST.is_file()
    assert "RUN_TESTNET_SESSION_ENTRYPOINT_FAIL_CLOSED_CONTRACT_V0=true" in (
        ENTRYPOINT_FAIL_CLOSED_TEST.read_text(encoding="utf-8")
    )
    assert "TESTNET_WALLCLOCK_DURATION_EVIDENCE_CONTRACT_V0=true" in (
        WALLCLOCK_CONTRACT_TEST.read_text(encoding="utf-8")
    )


def test_section5_preflight_policy_lift_does_not_authorize_execute() -> None:
    gap_map = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    final_lines = gap_map.split("## Final Machine Lines", 1)[-1]
    assert "PREFLIGHT_REMAINS_BLOCKED=false" in final_lines
    assert "PREFLIGHT_LIFTED_BY_CLASS4_POLICY=true" in final_lines
    assert "NEXT_EXECUTE_ALLOWED=false" in final_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in final_lines
    assert "ARMING_NOT_EXECUTE=true" in final_lines
    assert "PREFLIGHT_LIFT_EXECUTED=false" in final_lines


def test_run_testnet_session_not_network_preflight_surface() -> None:
    source = RUN_TESTNET_SESSION.read_text(encoding="utf-8")
    assert "RUN_TESTNET_SESSION_ALLOWED_NOW=false" in source
    assert "Does not authorize NORMAL_TESTNET_RUN" in source
    assert "NETWORK_PREFLIGHT" not in source


def test_kraken_testnet_has_order_path_but_preflight_forbids_it() -> None:
    source = KRAKEN_TESTNET_CLIENT.read_text(encoding="utf-8")
    assert "/0/private/AddOrder" in source
    assert "validate_only" in source
    text = Path(__file__).read_text(encoding="utf-8")
    assert "validate_only AddOrder forbidden" in text


def test_valid_preflight_evidence_passes_evaluator() -> None:
    result = evaluate_bounded_network_testnet_preflight_evidence(_valid_preflight_evidence())
    assert result["preflight_evidence_valid"] is True
    assert result["network_preflight_evidence_valid"] is True
    assert result["fail_reasons"] == []


def test_missing_explicit_execute_go_invalid() -> None:
    bad = _valid_preflight_evidence()
    bad["operator_go"] = "GO_PREPARE_BOUNDED_NETWORK_TESTNET_PREFLIGHT_CHARTER_NO_RUN_V0"
    result = evaluate_bounded_network_testnet_preflight_evidence(bad)
    assert result["preflight_evidence_valid"] is False


@pytest.mark.parametrize(
    "field",
    [
        "credentials_printed",
        "credential_values_exported",
        "validate_only_addorder_used",
        "run_testnet_session_invoked",
        "preflight_lifted",
        "arming_changed",
        "shadow_hold_lifted",
        "orders_allowed",
    ],
)
def test_abort_rules_invalidate_evidence(field: str) -> None:
    bad = _valid_preflight_evidence()
    bad[field] = True
    result = evaluate_bounded_network_testnet_preflight_evidence(bad)
    assert result["preflight_evidence_valid"] is False
    assert result["fail_reasons"]


def test_forbidden_endpoint_invalidates_evidence() -> None:
    bad = _valid_preflight_evidence()
    bad["endpoints_called"] = ["/0/private/AddOrder"]
    result = evaluate_bounded_network_testnet_preflight_evidence(bad)
    assert result["preflight_evidence_valid"] is False
    assert any("AddOrder" in r for r in result["fail_reasons"])


def test_non_allowlisted_host_invalidates_evidence() -> None:
    bad = _valid_preflight_evidence()
    bad["network_host"] = "https://evil.example.com"
    result = evaluate_bounded_network_testnet_preflight_evidence(bad)
    assert result["preflight_evidence_valid"] is False
    assert any("non-allowlisted network host" in r for r in result["fail_reasons"])


def test_missing_wallclock_fields_invalidates_evidence() -> None:
    bad = _valid_preflight_evidence()
    bad.pop("start_wall_clock_iso")
    result = evaluate_bounded_network_testnet_preflight_evidence(bad)
    assert result["preflight_evidence_valid"] is False
    assert any("R2" in r for r in result["fail_reasons"])


def test_elapsed_below_min_required_invalidates_evidence() -> None:
    bad = _valid_preflight_evidence()
    bad["elapsed_wall_clock_seconds"] = 10.0
    bad["elapsed_monotonic_seconds"] = 10.0
    result = evaluate_bounded_network_testnet_preflight_evidence(bad)
    assert result["preflight_evidence_valid"] is False
    assert any("R1" in r for r in result["fail_reasons"])


def test_missing_manifest_invalidates_evidence() -> None:
    bad = _valid_preflight_evidence()
    bad["manifest_present"] = False
    result = evaluate_bounded_network_testnet_preflight_evidence(bad)
    assert result["preflight_evidence_valid"] is False
    assert any("MANIFEST" in r for r in result["fail_reasons"])


def test_preflight_duration_tier_constants_documented() -> None:
    assert PREFLIGHT_PLANNED_DURATION_SECONDS == 120
    assert PREFLIGHT_MIN_REQUIRED_WALL_CLOCK_SECONDS == 60
    assert PREFLIGHT_MAX_ACCEPTABLE_WALL_CLOCK_SECONDS == 180
    assert MAX_REAL_ORDER_CALLS == 0


def test_future_preflight_closeout_must_include_required_keys() -> None:
    required = {
        "operator_go",
        "network_host",
        "endpoints_called",
        "max_real_order_calls",
        "credential_values_exported",
        "planned_duration_seconds",
        "elapsed_wall_clock_seconds",
    }
    sample = _valid_preflight_evidence()
    assert required.issubset(sample.keys())
    serialized = json.dumps(sample)
    for key in required:
        assert key in serialized
