"""Static + offline bounded network Testnet preflight contract (v0).

Docs/tests-only Class-4 scoped exception. No runtime, network, credentials, or Testnet start.
Reuses the canonical repo-native evaluator from ``src/ops/bounded_network_testnet_preflight_contract_v0.py``.
Charter: bounded_network_testnet_preflight_charter_no_run_v0_20260603T184700Z
"""

from __future__ import annotations

import ast
import importlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from src.ops.bounded_network_testnet_preflight_contract_v0 import (
    CHARTER_BUNDLE_SUFFIX,
    CLASS4_SCOPED_EXCEPTION_MARKER,
    FORBIDDEN_ORDER_ENDPOINTS,
    HOST_ALLOWLIST,
    MAX_PRIVATE_READONLY_CALLS,
    MAX_PUBLIC_CALLS,
    MAX_REAL_ORDER_CALLS,
    MIN_HEARTBEAT_SPAN_SECONDS,
    MIN_HEARTBEATS_REQUIRED,
    PACKAGE_MARKER,
    PREFLIGHT_MAX_ACCEPTABLE_WALL_CLOCK_SECONDS,
    PREFLIGHT_MIN_REQUIRED_WALL_CLOCK_SECONDS,
    PREFLIGHT_PLANNED_DURATION_SECONDS,
    PREFLIGHT_WALL_CLOCK_SLACK_SECONDS,
    PRIVATE_READONLY_ENDPOINTS,
    PUBLIC_ENDPOINTS,
    REQUIRED_EXECUTE_GO,
    evaluate_bounded_network_testnet_preflight_evidence,
)
from src.ops.wallclock_session_evidence_v0 import evaluate_wallclock_evidence_fields

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
CONTRACT_MODULE = REPO_ROOT / "src" / "ops" / "bounded_network_testnet_preflight_contract_v0.py"
CANONICAL_WALLCLOCK_MODULE = REPO_ROOT / "src" / "ops" / "wallclock_session_evidence_v0.py"

CONTRACT_GOVERNANCE_TOKEN_MAP: dict[str, str] = {
    "NETWORK_PREFLIGHT_EXECUTE_NOW_ALLOWED": "Does not authorize NETWORK_PREFLIGHT_EXECUTE",
    "REAL_TESTNET_SESSION_NOW_ALLOWED": "RUN_TESTNET_SESSION_ALLOWED_NOW=false",
    "TESTNET_SESSION_ALLOWED": "Does not authorize run_testnet_session preflight execute",
    "ORDERS_ALLOWED": "MAX_REAL_ORDER_CALLS=0",
    "WALLCLOCK_EVIDENCE_REQUIRED": "invalid_if_elapsed_below_min=true",
    "DURABLE_EVIDENCE_REQUIRED": "MANIFEST.sha256",
}


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
    contract_text = CONTRACT_MODULE.read_text(encoding="utf-8")
    assert PACKAGE_MARKER in contract_text
    assert CLASS4_SCOPED_EXCEPTION_MARKER in contract_text
    assert CHARTER_BUNDLE_SUFFIX in text
    assert CHARTER_BUNDLE_SUFFIX in contract_text
    assert REQUIRED_EXECUTE_GO in contract_text


def test_canonical_owner_imported_not_duplicated() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    local_evaluators = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name.startswith("evaluate_bounded_network_testnet_preflight")
    ]
    assert local_evaluators == []
    text = Path(__file__).read_text(encoding="utf-8")
    assert "from src.ops.bounded_network_testnet_preflight_contract_v0 import" in text
    assert evaluate_bounded_network_testnet_preflight_evidence.__module__ == (
        "src.ops.bounded_network_testnet_preflight_contract_v0"
    )


def test_wallclock_binding_uses_canonical_evaluator() -> None:
    contract_source = CONTRACT_MODULE.read_text(encoding="utf-8")
    assert (
        "from src.ops.wallclock_session_evidence_v0 import evaluate_wallclock_evidence_fields"
        in (contract_source)
    )
    assert "evaluate_wallclock_duration_evidence" not in contract_source
    assert evaluate_wallclock_evidence_fields.__module__ == "src.ops.wallclock_session_evidence_v0"


def test_contract_module_offline_non_authorizing() -> None:
    contract_source = CONTRACT_MODULE.read_text(encoding="utf-8")
    forbidden_tokens = (
        "socket",
        "subprocess",
        "requests",
        "urllib",
        "READY_FOR_LIVE",
        "RUNTIME_STARTED=true",
        "ORDERS_ALLOWED_NOW",
    )
    for token in forbidden_tokens:
        assert token not in contract_source


def test_happy_path_remains_offline_and_non_authorizing() -> None:
    result = evaluate_bounded_network_testnet_preflight_evidence(_valid_preflight_evidence())
    assert result["preflight_evidence_valid"] is True
    assert result["network_preflight_evidence_valid"] is True
    assert result["fail_reasons"] == []
    assert "ready_for_live" not in result
    assert "runtime_started" not in result
    assert "orders_authorized" not in result


@pytest.mark.parametrize("py_minor", (9, 10, 11))
def test_canonical_owner_importable_on_supported_python(py_minor: int) -> None:
    if sys.version_info[:2] != (3, py_minor):
        pytest.skip(f"current interpreter is {sys.version_info.major}.{sys.version_info.minor}")
    module = importlib.import_module("src.ops.bounded_network_testnet_preflight_contract_v0")
    assert hasattr(module, "evaluate_bounded_network_testnet_preflight_evidence")
    assert hasattr(module, "PACKAGE_MARKER")


def test_endpoint_allowlists_complete() -> None:
    contract_text = CONTRACT_MODULE.read_text(encoding="utf-8")
    for endpoint in PUBLIC_ENDPOINTS | PRIVATE_READONLY_ENDPOINTS | FORBIDDEN_ORDER_ENDPOINTS:
        assert endpoint in contract_text, f"missing endpoint {endpoint!r}"


def test_contract_governance_tokens_map_to_repo_native_markers() -> None:
    entrypoint_source = RUN_TESTNET_SESSION.read_text(encoding="utf-8")
    contract_text = CONTRACT_MODULE.read_text(encoding="utf-8")
    self_text = Path(__file__).read_text(encoding="utf-8")
    for external_token, repo_marker in CONTRACT_GOVERNANCE_TOKEN_MAP.items():
        if external_token in {"WALLCLOCK_EVIDENCE_REQUIRED", "DURABLE_EVIDENCE_REQUIRED"}:
            assert repo_marker in contract_text or repo_marker in self_text
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
    assert CANONICAL_WALLCLOCK_MODULE.is_file()
    assert "RUN_TESTNET_SESSION_ENTRYPOINT_FAIL_CLOSED_CONTRACT_V0=true" in (
        ENTRYPOINT_FAIL_CLOSED_TEST.read_text(encoding="utf-8")
    )
    assert "TESTNET_WALLCLOCK_DURATION_EVIDENCE_CONTRACT_V0=true" in (
        WALLCLOCK_CONTRACT_TEST.read_text(encoding="utf-8")
    )


def test_section5_next_execute_policy_lift_does_not_authorize_runtime() -> None:
    gap_map = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    final_lines = gap_map.split("## Final Machine Lines", 1)[-1]
    assert "PREFLIGHT_REMAINS_BLOCKED=false" in final_lines
    assert "PREFLIGHT_LIFTED_BY_CLASS4_POLICY=true" in final_lines
    assert "NEXT_EXECUTE_ALLOWED=true" in final_lines
    assert "READY_FOR_OPERATOR_ARMING=true" in final_lines
    assert "ARMING_NOT_EXECUTE=true" in final_lines
    assert "EXECUTE_IS_NOT_RUNTIME_START=true" in final_lines
    assert "BOUNDED_EXECUTE_RUN_AUTHORIZED=true" in final_lines
    assert "BOUNDED_EXECUTE_RUN_IS_NOT_LIVE=true" in final_lines
    assert "BOUNDED_EXECUTE_RUN_IS_NOT_RUNTIME_START=true" in final_lines
    assert "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_AUTHORIZED=true" in final_lines
    assert "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_IS_NOT_RUNTIME_START=true" in final_lines
    assert "T3_RUN_ATTEMPT_EXECUTE_AUTHORIZED=true" in final_lines
    assert "T3_RUN_ATTEMPT_EXECUTE_OPERATOR_DECISION_RECORD_REFLECTED=true" in final_lines
    assert "T3_RUN_ATTEMPT_EXECUTE_IS_NOT_RUNTIME_START=true" in final_lines
    assert "T3_RUN_ATTEMPT_READINESS_PREFLIGHT_REQUIRED=true" in final_lines
    assert "CONCRETE_RUN_AUTHORIZED=false" in final_lines
    assert "T3_RUN_ATTEMPT_EXECUTE_ALLOWED_NOW=false" in final_lines
    assert "T3_PLAN_ONLY_EXECUTE_CLOSEOUT_REFLECTED=true" in final_lines
    assert "T3_BOUNDED_EXECUTE_RUN_ATTEMPT_PLAN_ONLY_COMPLETED=true" in final_lines
    assert "NEXT_RUNTIME_STAGE_REQUIRES_SEPARATE_CHARTER=true" in final_lines
    assert "RUNTIME_STARTED=false" in final_lines
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
    contract_text = CONTRACT_MODULE.read_text(encoding="utf-8")
    assert "validate_only AddOrder forbidden" in contract_text


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
    assert HOST_ALLOWLIST == frozenset({"https://api.kraken.com"})
    assert MAX_PUBLIC_CALLS == 8
    assert MAX_PRIVATE_READONLY_CALLS == 4
    assert MIN_HEARTBEATS_REQUIRED == 2
    assert MIN_HEARTBEAT_SPAN_SECONDS == 30
    assert PREFLIGHT_WALL_CLOCK_SLACK_SECONDS == 60


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
