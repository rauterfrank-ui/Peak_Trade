"""Offline tests for order_capability_private_endpoint_boundary_contract_v1.

Class-4 scoped: no network, credentials, orders, or Testnet execute.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.bounded_futures_private_readonly_contract_v0 import (
    DEMO_FUTURES_REST_BASE_URL,
    FUTURES_PRIVATE_READONLY_GET_ENDPOINTS,
    PACKAGE_MARKER as HARNESS_PACKAGE_MARKER,
    PRIVATE_READONLY_MODE,
)
from src.ops.order_capability_cancel_cleanup_failclosed_contract_v1 import (
    REASON_ENDPOINT_BOUNDARY_NOT_SATISFIED,
    evaluate_order_capability_cancel_cleanup,
)
from src.ops.order_capability_private_endpoint_boundary_contract_v1 import (
    FORBIDDEN_SERIALIZATION_KEYS,
    PACKAGE_MARKER,
    REASON_BOUNDED_FUTURES_PRIVATE_READONLY_CONTRACT_NOT_SATISFIED,
    REASON_CANCEL_ENDPOINT_PRESENT,
    REASON_HARNESS_POLICY_MISMATCH,
    REASON_LIVE_ENVIRONMENT_REJECTED,
    REASON_MANIFEST_NOT_VERIFIED,
    REASON_MISSING_CORRELATION,
    REASON_MISSING_EVIDENCE_SUMMARY,
    REASON_MODIFY_ENDPOINT_PRESENT,
    REASON_NETWORK_PERFORMED,
    REASON_ORDER_ENDPOINT_PRESENT,
    REASON_POSITION_MUTATION_ENDPOINT_PRESENT,
    REASON_READONLY_PROFILE_NOT_PROVEN,
    REASON_SECRET_MATERIAL_PRESENT,
    REASON_UNSUPPORTED_PROFILE,
    OrderCapabilityPrivateEndpointBoundaryError,
    OrderCapabilityPrivateEndpointBoundaryEvidenceSummary,
    OrderCapabilityPrivateEndpointBoundaryInput,
    OrderCapabilityPrivateEndpointBoundaryPolicy,
    OrderCapabilityPrivateEndpointBoundaryVerdict,
    OrderCapabilityPrivateEndpointBoundaryVerdictKind,
    evaluate_order_capability_private_endpoint_boundary,
    map_boundary_verdict_to_cleanup_input_flag,
    serialize_order_capability_private_endpoint_boundary_verdict,
    validate_order_capability_private_endpoint_boundary_verdict,
)
from tests.ops.test_order_capability_cancel_cleanup_failclosed_contract_v1 import (
    _valid_input as _valid_cleanup_input,
)

CONTRACT_MODULE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "ops"
    / "order_capability_private_endpoint_boundary_contract_v1.py"
)
HARNESS_MODULE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "ops"
    / "bounded_futures_private_readonly_contract_v0.py"
)

TEST_PACKAGE_MARKER = "ORDER_CAPABILITY_PRIVATE_ENDPOINT_BOUNDARY_CONTRACT_V1_TEST=true"
CORRELATION_ID = "ev-test-boundary-001"
VALID_ENDPOINTS = tuple(sorted(FUTURES_PRIVATE_READONLY_GET_ENDPOINTS))

DENIED_HARNESS_SYMBOLS = (
    "build_private_readonly_http_request",
    "compute_futures_private_authent",
    "run_private_readonly_reachability",
    "resolve_private_readonly_credentials_from_environ",
    "build_private_readonly_evidence_from_network",
)


def _valid_summary(**overrides: object) -> OrderCapabilityPrivateEndpointBoundaryEvidenceSummary:
    base = {
        "source_contract_marker": HARNESS_PACKAGE_MARKER,
        "source_kind": "injected_offline_fixture",
        "profile_mode": PRIVATE_READONLY_MODE,
        "environment": "demo_testnet_only",
        "evidence_correlation_id": CORRELATION_ID,
        "manifest_verified": True,
        "endpoint_profile_paths": VALID_ENDPOINTS,
        "http_methods_observed": ("GET",),
        "rest_base_url": DEMO_FUTURES_REST_BASE_URL,
        "private_readonly_policy_pass": True,
        "readonly_profile_proven": True,
        "no_secret_material": True,
        "no_network_performed": True,
        "no_order_submission": True,
        "no_cancel": True,
        "no_position_mutation": True,
    }
    base.update(overrides)
    return OrderCapabilityPrivateEndpointBoundaryEvidenceSummary(**base)


def _valid_input(**overrides: object) -> OrderCapabilityPrivateEndpointBoundaryInput:
    base = {
        "evidence_summary": _valid_summary(),
        "policy": OrderCapabilityPrivateEndpointBoundaryPolicy(),
        "expected_evidence_correlation_id": CORRELATION_ID,
    }
    base.update(overrides)
    if "evidence_summary" not in overrides and any(
        key in overrides for key in _valid_summary().__dataclass_fields__
    ):
        summary_overrides = {
            key: value
            for key, value in overrides.items()
            if key in _valid_summary().__dataclass_fields__
        }
        base["evidence_summary"] = _valid_summary(**summary_overrides)
    return OrderCapabilityPrivateEndpointBoundaryInput(**base)


def test_package_marker_present() -> None:
    assert TEST_PACKAGE_MARKER
    assert PACKAGE_MARKER in CONTRACT_MODULE.read_text(encoding="utf-8")


def test_happy_path_satisfied_for_dry_order_capability_only() -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(_valid_input())
    assert (
        verdict.verdict
        == OrderCapabilityPrivateEndpointBoundaryVerdictKind.SATISFIED_FOR_DRY_ORDER_CAPABILITY_ONLY
    )
    assert verdict.reason_codes == ()
    assert verdict.private_endpoint_boundary_satisfied is True
    assert verdict.execute_authorized is False
    assert verdict.cancel_authorized is False
    assert verdict.flatten_authorized is False
    assert verdict.preflight_remains_blocked is True


def test_map_boundary_verdict_to_cleanup_input_flag_true_only_when_satisfied() -> None:
    satisfied = evaluate_order_capability_private_endpoint_boundary(_valid_input())
    assert map_boundary_verdict_to_cleanup_input_flag(satisfied) is True

    failed = evaluate_order_capability_private_endpoint_boundary(
        _valid_input(evidence_summary=_valid_summary(manifest_verified=False))
    )
    assert map_boundary_verdict_to_cleanup_input_flag(failed) is False


def test_missing_evidence_summary_fail_closed() -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(
        _valid_input(evidence_summary=_valid_summary(source_kind=""))
    )
    assert verdict.verdict == OrderCapabilityPrivateEndpointBoundaryVerdictKind.FAIL_CLOSED
    assert REASON_MISSING_EVIDENCE_SUMMARY in verdict.reason_codes


def test_manifest_not_verified_fail_closed() -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(
        _valid_input(evidence_summary=_valid_summary(manifest_verified=False))
    )
    assert REASON_MANIFEST_NOT_VERIFIED in verdict.reason_codes


@pytest.mark.parametrize("environment", ["live", "prod", "mainnet", "production"])
def test_live_prod_mainnet_fail_closed(environment: str) -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(
        _valid_input(evidence_summary=_valid_summary(environment=environment))
    )
    assert REASON_LIVE_ENVIRONMENT_REJECTED in verdict.reason_codes


def test_secret_material_present_fail_closed() -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(
        _valid_input(evidence_summary=_valid_summary(no_secret_material=False))
    )
    assert REASON_SECRET_MATERIAL_PRESENT in verdict.reason_codes


def test_network_performed_fail_closed() -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(
        _valid_input(evidence_summary=_valid_summary(no_network_performed=False))
    )
    assert REASON_NETWORK_PERFORMED in verdict.reason_codes


def test_order_endpoint_present_fail_closed() -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(
        _valid_input(
            evidence_summary=_valid_summary(
                endpoint_profile_paths=("/derivatives/api/v3/sendorder",),
                private_readonly_policy_pass=False,
            )
        )
    )
    assert REASON_ORDER_ENDPOINT_PRESENT in verdict.reason_codes


def test_cancel_endpoint_present_fail_closed() -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(
        _valid_input(
            evidence_summary=_valid_summary(
                endpoint_profile_paths=("/derivatives/api/v3/cancelorder",),
                private_readonly_policy_pass=False,
            )
        )
    )
    assert REASON_CANCEL_ENDPOINT_PRESENT in verdict.reason_codes


def test_modify_endpoint_present_fail_closed() -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(
        _valid_input(
            evidence_summary=_valid_summary(
                endpoint_profile_paths=("/derivatives/api/v3/validate-order",),
                private_readonly_policy_pass=False,
            )
        )
    )
    assert REASON_MODIFY_ENDPOINT_PRESENT in verdict.reason_codes


def test_position_mutation_endpoint_present_fail_closed() -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(
        _valid_input(
            evidence_summary=_valid_summary(
                endpoint_profile_paths=("/derivatives/api/v3/withdraw",),
                private_readonly_policy_pass=False,
            )
        )
    )
    assert REASON_POSITION_MUTATION_ENDPOINT_PRESENT in verdict.reason_codes


def test_missing_correlation_fail_closed() -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(
        _valid_input(evidence_summary=_valid_summary(evidence_correlation_id=""))
    )
    assert REASON_MISSING_CORRELATION in verdict.reason_codes


def test_unsupported_profile_fail_closed() -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(
        _valid_input(evidence_summary=_valid_summary(profile_mode="live_execute"))
    )
    assert REASON_UNSUPPORTED_PROFILE in verdict.reason_codes


def test_readonly_profile_not_proven_fail_closed() -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(
        _valid_input(evidence_summary=_valid_summary(readonly_profile_proven=False))
    )
    assert REASON_READONLY_PROFILE_NOT_PROVEN in verdict.reason_codes


def test_bounded_private_readonly_contract_not_satisfied_fail_closed() -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(
        _valid_input(
            evidence_summary=_valid_summary(
                source_contract_marker="OTHER_CONTRACT=true",
                private_readonly_policy_pass=False,
            )
        )
    )
    assert REASON_BOUNDED_FUTURES_PRIVATE_READONLY_CONTRACT_NOT_SATISFIED in verdict.reason_codes


def test_harness_policy_mismatch_fail_closed() -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(
        _valid_input(
            evidence_summary=_valid_summary(
                private_readonly_policy_pass=True,
                http_methods_observed=("POST",),
            )
        )
    )
    assert REASON_HARNESS_POLICY_MISMATCH in verdict.reason_codes


def test_unsafe_authority_flags_fail_closed_on_validate() -> None:
    verdict = OrderCapabilityPrivateEndpointBoundaryVerdict(
        verdict=OrderCapabilityPrivateEndpointBoundaryVerdictKind.SATISFIED_FOR_DRY_ORDER_CAPABILITY_ONLY,
        reason_codes=(),
        evidence_correlation_id=CORRELATION_ID,
        private_endpoint_boundary_satisfied=True,
        no_network_performed=True,
        no_secret_read=True,
        no_order_submission=True,
        no_cancel=True,
        no_position_mutation=True,
        execute_authorized=True,
        cancel_authorized=False,
        flatten_authorized=False,
        preflight_remains_blocked=True,
        live_ready=False,
        dashboard_truth_granted=False,
        no_authority_change=True,
    )
    with pytest.raises(OrderCapabilityPrivateEndpointBoundaryError):
        validate_order_capability_private_endpoint_boundary_verdict(verdict)


def test_serialization_stable_and_secret_free() -> None:
    verdict = evaluate_order_capability_private_endpoint_boundary(_valid_input())
    data = serialize_order_capability_private_endpoint_boundary_verdict(verdict)
    for key in data:
        assert key.lower() not in FORBIDDEN_SERIALIZATION_KEYS
    assert data["execute_authorized"] is False
    assert data["cancel_authorized"] is False
    assert data["preflight_remains_blocked"] is True
    assert data["private_endpoint_boundary_satisfied"] is True


def test_no_imports_from_risk_layer_or_execution() -> None:
    source = CONTRACT_MODULE.read_text(encoding="utf-8")
    assert "from src.risk_layer.kill_switch" not in source
    assert "import src.risk_layer.kill_switch" not in source
    assert "from src.execution" not in source
    assert "import src.execution" not in source
    test_import_block = Path(__file__).read_text(encoding="utf-8").split("def ")[0]
    assert "from src.risk_layer.kill_switch" not in test_import_block
    assert "from src.execution" not in test_import_block


def test_dangerous_harness_functions_not_imported() -> None:
    source = CONTRACT_MODULE.read_text(encoding="utf-8")
    for symbol in DENIED_HARNESS_SYMBOLS:
        assert symbol not in source


def test_deterministic_stable_output_for_same_input() -> None:
    inp = _valid_input()
    first = evaluate_order_capability_private_endpoint_boundary(inp)
    second = evaluate_order_capability_private_endpoint_boundary(inp)
    assert first == second
    assert serialize_order_capability_private_endpoint_boundary_verdict(first) == (
        serialize_order_capability_private_endpoint_boundary_verdict(second)
    )


def test_cleanup_integration_mapping_clears_endpoint_boundary_blocker_only() -> None:
    boundary_verdict = evaluate_order_capability_private_endpoint_boundary(_valid_input())
    boundary_flag = map_boundary_verdict_to_cleanup_input_flag(boundary_verdict)
    assert boundary_flag is True

    cleanup_verdict = evaluate_order_capability_cancel_cleanup(
        _valid_cleanup_input(private_endpoint_boundary_satisfied=boundary_flag)
    )
    assert REASON_ENDPOINT_BOUNDARY_NOT_SATISFIED not in cleanup_verdict.reason_codes
    assert cleanup_verdict.execute_authorized is False
    assert cleanup_verdict.cancel_authorized is False
    assert cleanup_verdict.flatten_authorized is False

    blocked_cleanup = evaluate_order_capability_cancel_cleanup(
        _valid_cleanup_input(private_endpoint_boundary_satisfied=False)
    )
    assert REASON_ENDPOINT_BOUNDARY_NOT_SATISFIED in blocked_cleanup.reason_codes
