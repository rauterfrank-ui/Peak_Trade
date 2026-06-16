"""Offline integration tests for order-capability payload/readiness chain (v1).

Class-4 scoped: no network, credentials, orders, adapter runs, or Testnet execute.
Validates full offline contract chain after Path-C without implying AddOrder/CancelOrder/DryOrder proof.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.bounded_futures_private_readonly_contract_v0 import (
    DEMO_FUTURES_REST_BASE_URL,
    FUTURES_ORDER_MUTATION_ENDPOINTS,
    FUTURES_PRIVATE_READONLY_FORBIDDEN_PATH_SUBSTRINGS,
    FUTURES_PRIVATE_READONLY_GET_ENDPOINTS,
    PACKAGE_MARKER as HARNESS_PACKAGE_MARKER,
    PRIVATE_READONLY_MODE,
    path_contains_forbidden_substring,
    validate_private_readonly_endpoint_path,
)
from src.ops.bounded_futures_testnet_contract_v0 import DEFAULT_INSTRUMENT
from src.ops.order_capability_cancel_cleanup_failclosed_contract_v1 import (
    ABORT_BINDING_PASS_VERDICT,
    DEFAULT_CLEANUP_PLACEHOLDER_MARKER,
    FORBIDDEN_SERIALIZATION_KEYS,
    REASON_CANCEL_CLEANUP_PLACEHOLDER_NOT_VALIDATED,
    OrderCapabilityAbortBindingSummary,
    OrderCapabilityCleanupInput,
    OrderCapabilityCleanupOrderStateSnapshot,
    OrderCapabilityCleanupPolicy,
    OrderCapabilityCleanupVerdictKind,
    OrderCapabilityPayloadCleanupSummary,
    evaluate_order_capability_cancel_cleanup,
    serialize_order_capability_cleanup_verdict,
)
from src.ops.order_capability_dry_validation_contract_v1 import (
    DEFAULT_MAX_SESSION_DURATION_SECONDS,
    DEFAULT_ORDER_TYPE,
    DEFAULT_VENUE_HOST,
    OrderCapabilityDryValidationInputs,
    evaluate_order_capability_dry_validation,
)
from src.ops.order_capability_killswitch_abort_binding_contract_v1 import (
    OrderCapabilityAbortBindingInput,
    OrderCapabilityBindingVerdict,
    OrderCapabilityKillSwitchSnapshot,
    OrderCapabilityPayloadSafetySummary,
    evaluate_order_capability_abort_binding,
)
from src.ops.order_capability_payload_builder_contract_v1 import (
    CANONICAL_VENUE,
    DEFAULT_ABORT_ACK_MARKER,
    DEFAULT_CLEANUP_CANCEL_CORRELATION_MARKER,
    DEFAULT_KILL_SWITCH_BINDING_MARKER,
    DEFAULT_MAX_LOSS_CAP_EUR,
    DEFAULT_MAX_NOTIONAL_EUR,
    DEFAULT_SESSION_DURATION_SECONDS,
    DEFAULT_STATUS,
    OrderCapabilityPayloadInput,
    build_order_capability_payload,
    serialize_order_capability_payload,
)
from src.ops.order_capability_private_endpoint_boundary_contract_v1 import (
    OrderCapabilityPrivateEndpointBoundaryEvidenceSummary,
    OrderCapabilityPrivateEndpointBoundaryInput,
    OrderCapabilityPrivateEndpointBoundaryPolicy,
    OrderCapabilityPrivateEndpointBoundaryVerdictKind,
    evaluate_order_capability_private_endpoint_boundary,
    map_boundary_verdict_to_cleanup_input_flag,
    serialize_order_capability_private_endpoint_boundary_verdict,
)
from src.ops.order_capability_side_price_qty_rules_contract_v1 import (
    REASON_EXECUTION_FIELDS_NOT_DRY_ONLY,
    REASON_UNSAFE_AUTHORITY_FLAGS,
    OrderCapabilityInstrumentRulesSummary,
    OrderCapabilitySidePriceQtyInput,
    OrderCapabilitySidePriceQtyPolicy,
    SidePriceQtyVerdictKind,
    evaluate_order_capability_side_price_qty_rules,
    map_side_price_qty_verdict_to_payload_builder_flag,
)

TEST_PACKAGE_MARKER = "ORDER_CAPABILITY_OFFLINE_PAYLOAD_READINESS_V1_TEST=true"
FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "ops"
    / "order_capability_offline_payload_readiness_v1"
    / "minimal_chain_inputs.json"
)
NOW_UTC = "2026-06-09T20:32:30Z"
OBSERVED_UTC = "2026-06-09T20:32:00Z"
OPERATOR_GO_BINDING = "GO_ORDER_CAPABILITY_OFFLINE_PAYLOAD_TESTS_ONLY_IMPLEMENTATION_NO_RUN_V1"


def _load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _instrument_rules() -> OrderCapabilityInstrumentRulesSummary:
    return OrderCapabilityInstrumentRulesSummary(
        instrument=DEFAULT_INSTRUMENT,
        price_tick=Decimal("0.5"),
        quantity_step=Decimal("0.001"),
        min_quantity=Decimal("0.001"),
        max_quantity=Decimal("100.0"),
        metadata_source="governed_metadata_snapshot_fixture",
        metadata_verified_offline=True,
    )


def _side_price_qty_input(**overrides: object) -> OrderCapabilitySidePriceQtyInput:
    fixture = _load_fixture()
    base = {
        "instrument_rules": _instrument_rules(),
        "policy": OrderCapabilitySidePriceQtyPolicy(),
        "environment": fixture["environment"],
        "side": fixture["side"],
        "limit_price": fixture["limit_price"],
        "quantity": fixture["quantity"],
        "time_in_force": "GTC",
        "post_only": False,
        "reduce_only": False,
        "max_notional_eur": fixture["max_notional_eur"],
        "max_loss_cap_eur": fixture["max_loss_cap_eur"],
        "evidence_correlation_id": fixture["evidence_correlation_id"],
        "execute_authorized": False,
        "cancel_authorized": False,
        "flatten_authorized": False,
    }
    base.update(overrides)
    return OrderCapabilitySidePriceQtyInput(**base)


def _payload_input(**overrides: object) -> OrderCapabilityPayloadInput:
    fixture = _load_fixture()
    side_price_qty_verdict = evaluate_order_capability_side_price_qty_rules(_side_price_qty_input())
    base = {
        "instrument": DEFAULT_INSTRUMENT,
        "venue": CANONICAL_VENUE,
        "environment": fixture["environment"],
        "side": fixture["side"],
        "order_type": DEFAULT_ORDER_TYPE,
        "limit_price": fixture["limit_price"],
        "quantity": fixture["quantity"],
        "max_notional_eur": fixture["max_notional_eur"],
        "max_loss_cap_eur": fixture["max_loss_cap_eur"],
        "session_duration_seconds": fixture["session_duration_seconds"],
        "operator_go_token_binding": fixture["operator_go_token_binding"],
        "abort_ack_marker": DEFAULT_ABORT_ACK_MARKER,
        "time_in_force": "GTC",
        "post_only": False,
        "reduce_only": False,
        "kill_switch_binding_marker": DEFAULT_KILL_SWITCH_BINDING_MARKER,
        "cleanup_cancel_correlation_marker": DEFAULT_CLEANUP_CANCEL_CORRELATION_MARKER,
        "evidence_correlation_id": fixture["evidence_correlation_id"],
        "side_price_qty_verdict": side_price_qty_verdict,
        "requires_side_price_qty_contract": True,
    }
    base.update(overrides)
    return OrderCapabilityPayloadInput(**base)


def _dry_validation_inputs(**overrides: object) -> OrderCapabilityDryValidationInputs:
    fixture = _load_fixture()
    base = {
        "instrument": DEFAULT_INSTRUMENT,
        "venue": f"Kraken Futures Demo / {DEFAULT_VENUE_HOST}",
        "max_loss_cap_eur": fixture["max_loss_cap_eur"],
        "max_notional_eur": fixture["max_notional_eur"],
        "order_type": DEFAULT_ORDER_TYPE,
        "session_duration_seconds": DEFAULT_MAX_SESSION_DURATION_SECONDS,
        "abort_ack_confirmed": True,
        "max_notional_confirmed": True,
    }
    base.update(overrides)
    return OrderCapabilityDryValidationInputs(**base)


def _path_c_readonly_boundary_input() -> OrderCapabilityPrivateEndpointBoundaryInput:
    fixture = _load_fixture()
    correlation_id = str(fixture["evidence_correlation_id"])
    summary = OrderCapabilityPrivateEndpointBoundaryEvidenceSummary(
        source_contract_marker=HARNESS_PACKAGE_MARKER,
        source_kind="path_c_private_readonly_offline_fixture",
        profile_mode=PRIVATE_READONLY_MODE,
        environment=str(fixture["environment"]),
        evidence_correlation_id=correlation_id,
        manifest_verified=True,
        endpoint_profile_paths=tuple(sorted(FUTURES_PRIVATE_READONLY_GET_ENDPOINTS)),
        http_methods_observed=("GET",),
        rest_base_url=DEMO_FUTURES_REST_BASE_URL,
        private_readonly_policy_pass=True,
        readonly_profile_proven=bool(fixture["path_c_private_readonly_proven"]),
        no_secret_material=True,
        no_network_performed=True,
        no_order_submission=True,
        no_cancel=True,
        no_position_mutation=True,
    )
    return OrderCapabilityPrivateEndpointBoundaryInput(
        evidence_summary=summary,
        policy=OrderCapabilityPrivateEndpointBoundaryPolicy(),
        expected_evidence_correlation_id=correlation_id,
    )


def _run_offline_payload_readiness_chain() -> dict[str, object]:
    fixture = _load_fixture()
    correlation_id = str(fixture["evidence_correlation_id"])

    side_price_qty_verdict = evaluate_order_capability_side_price_qty_rules(_side_price_qty_input())
    payload = build_order_capability_payload(_payload_input())
    dry_validation = evaluate_order_capability_dry_validation(_dry_validation_inputs())
    boundary = evaluate_order_capability_private_endpoint_boundary(
        _path_c_readonly_boundary_input()
    )

    binding = evaluate_order_capability_abort_binding(
        OrderCapabilityAbortBindingInput(
            payload_summary=OrderCapabilityPayloadSafetySummary(
                evidence_correlation_id=payload.evidence_correlation_id,
                no_submit=payload.no_submit,
                no_network=payload.no_network,
                execute_authorized=payload.execute_authorized,
                order_submission_executed=payload.order_submission_executed,
                cancel_executed=payload.cancel_executed,
                trade_position_mutation_executed=payload.trade_position_mutation_executed,
                abort_ack_marker=payload.abort_ack_marker,
                operator_go_token_binding=payload.operator_go_token_binding,
                environment=payload.environment,
            ),
            expected_operator_go_token_binding=payload.operator_go_token_binding,
            kill_switch_snapshot=OrderCapabilityKillSwitchSnapshot(
                source="offline_fixture",
                source_id="ks-offline-readiness-v1",
                source_kind="injected_offline_fixture",
                state="OK",
                observed_at_utc=OBSERVED_UTC,
                ttl_seconds=120,
                correlation_id=correlation_id,
                environment=str(fixture["environment"]),
            ),
            now_utc=NOW_UTC,
            expected_environment=str(fixture["environment"]),
        )
    )

    cleanup = evaluate_order_capability_cancel_cleanup(
        OrderCapabilityCleanupInput(
            payload_summary=OrderCapabilityPayloadCleanupSummary(
                evidence_correlation_id=payload.evidence_correlation_id,
                client_order_id=payload.client_order_id,
                idempotency_key=payload.idempotency_key,
                cleanup_cancel_correlation_marker=payload.cleanup_cancel_correlation_marker,
                operator_go_token_binding=payload.operator_go_token_binding,
                environment=payload.environment,
                no_submit=payload.no_submit,
                no_network=payload.no_network,
                execute_authorized=payload.execute_authorized,
                cancel_executed=payload.cancel_executed,
                trade_position_mutation_executed=payload.trade_position_mutation_executed,
            ),
            abort_binding_summary=OrderCapabilityAbortBindingSummary(
                verdict=ABORT_BINDING_PASS_VERDICT,
                evidence_correlation_id=correlation_id,
                reason_codes=(),
                execute_authorized=False,
                cancel_executed=False,
            ),
            order_state_snapshot=OrderCapabilityCleanupOrderStateSnapshot(
                source_id="order-state-offline-readiness-v1",
                source_kind="injected_offline_fixture",
                order_state="NONE",
                observed_at_utc=OBSERVED_UTC,
                ttl_seconds=120,
                environment=str(fixture["environment"]),
                instrument=DEFAULT_INSTRUMENT,
                client_order_id=payload.client_order_id,
                idempotency_key=payload.idempotency_key,
                evidence_correlation_id=correlation_id,
            ),
            cleanup_policy=OrderCapabilityCleanupPolicy(),
            operator_cleanup_go_token_binding=payload.operator_go_token_binding,
            expected_operator_cleanup_go_token_binding=payload.operator_go_token_binding,
            expected_environment=str(fixture["environment"]),
            now_utc=NOW_UTC,
            private_endpoint_boundary_satisfied=map_boundary_verdict_to_cleanup_input_flag(
                boundary
            ),
        )
    )

    return {
        "fixture": fixture,
        "side_price_qty_verdict": side_price_qty_verdict,
        "payload": payload,
        "payload_serialized": serialize_order_capability_payload(payload),
        "dry_validation": dry_validation,
        "boundary": boundary,
        "binding": binding,
        "cleanup": cleanup,
    }


def test_package_marker_and_fixture_loaded() -> None:
    assert TEST_PACKAGE_MARKER
    fixture = _load_fixture()
    assert fixture["schema_version"] == "order_capability_offline_payload_readiness_fixture.v1"
    assert fixture["credential_use_required"] is False
    assert fixture["official_dry_run_endpoint_present"] is False


def test_full_offline_chain_produces_inert_payload_without_execute_authority() -> None:
    chain = _run_offline_payload_readiness_chain()
    payload = chain["payload"]
    assert payload.status == DEFAULT_STATUS
    assert payload.no_submit is True
    assert payload.no_network is True
    assert payload.execute_authorized is False
    assert payload.preflight_remains_blocked is True


def test_payload_status_always_blocked_not_authorized() -> None:
    chain = _run_offline_payload_readiness_chain()
    assert chain["payload_serialized"]["status"] == "BLOCKED_NOT_AUTHORIZED"


def test_dry_validation_never_authorizes_execute() -> None:
    chain = _run_offline_payload_readiness_chain()
    dry = chain["dry_validation"]
    assert dry["verdict"] == "PASS"
    assert dry["execute_ready"] is False
    assert dry["safety_flags"]["dry_validation_authorized"] is False
    assert dry["safety_flags"]["order_capability_execute_authorized"] is False
    assert dry["safety_flags"]["network_api_called"] is False


def test_dry_order_semantics_do_not_mask_real_order_submit() -> None:
    chain = _run_offline_payload_readiness_chain()
    dry = chain["dry_validation"]
    binding = chain["binding"]
    assert dry["safety_flags"]["no_order"] is True
    assert dry["safety_flags"]["no_cancel"] is True
    assert binding.verdict == OrderCapabilityBindingVerdict.PASS_FOR_DRY_SUBMIT_CANDIDATE_ONLY
    assert binding.execute_authorized is False
    assert chain["payload"].order_submission_executed is False


@pytest.mark.parametrize(
    "endpoint",
    [
        "/derivatives/api/v3/sendorder",
        "/derivatives/api/v3/cancelorder",
        "/derivatives/api/v3/cancelallorders",
    ],
)
def test_mutation_endpoints_forbidden_in_executable_context(endpoint: str) -> None:
    assert endpoint in FUTURES_ORDER_MUTATION_ENDPOINTS
    assert path_contains_forbidden_substring(endpoint) is not None
    reasons = validate_private_readonly_endpoint_path(endpoint)
    assert reasons


def test_addorder_alias_maps_to_sendorder_blocklist() -> None:
    addorder_path = "/derivatives/api/v3/sendorder"
    assert "sendorder" in FUTURES_PRIVATE_READONLY_FORBIDDEN_PATH_SUBSTRINGS
    assert path_contains_forbidden_substring(addorder_path) == "sendorder"


def test_nonzero_notional_blocked_when_execute_authorized_flag_set() -> None:
    verdict = evaluate_order_capability_side_price_qty_rules(
        _side_price_qty_input(execute_authorized=True)
    )
    assert verdict.verdict == SidePriceQtyVerdictKind.FAIL_CLOSED
    assert REASON_UNSAFE_AUTHORITY_FLAGS in verdict.reason_codes
    assert REASON_EXECUTION_FIELDS_NOT_DRY_ONLY in verdict.reason_codes
    assert map_side_price_qty_verdict_to_payload_builder_flag(verdict) is False


def test_nonzero_notional_exceeding_cap_blocked_at_payload_builder() -> None:
    fixture = _load_fixture()
    side_price_qty_verdict = evaluate_order_capability_side_price_qty_rules(
        _side_price_qty_input(limit_price=1000.0, quantity=0.02)
    )
    with pytest.raises(Exception, match="notional|NOTIONAL|exceeds"):
        build_order_capability_payload(
            _payload_input(
                limit_price=1000.0,
                quantity=0.02,
                max_notional_eur=fixture["max_notional_eur"],
                side_price_qty_verdict=side_price_qty_verdict,
            )
        )


def test_no_official_dry_run_endpoint_means_network_dry_run_disallowed() -> None:
    fixture = _load_fixture()
    chain = _run_offline_payload_readiness_chain()
    assert fixture["official_dry_run_endpoint_present"] is False
    assert fixture["dry_run_network_scope_allowed"] is False
    assert chain["dry_validation"]["safety_flags"]["no_network"] is True
    assert chain["payload"].no_network is True


def test_path_c_private_readonly_does_not_imply_add_cancel_dry_order_proof() -> None:
    fixture = _load_fixture()
    chain = _run_offline_payload_readiness_chain()
    boundary = chain["boundary"]
    assert fixture["path_c_private_readonly_proven"] is True
    assert fixture["add_order_proven"] is False
    assert fixture["cancel_order_proven"] is False
    assert fixture["dry_order_proven"] is False
    assert (
        boundary.verdict
        == OrderCapabilityPrivateEndpointBoundaryVerdictKind.SATISFIED_FOR_DRY_ORDER_CAPABILITY_ONLY
    )
    assert boundary.execute_authorized is False
    assert boundary.cancel_authorized is False


def test_primary_evidence_required_before_any_future_run() -> None:
    fixture = _load_fixture()
    assert fixture["primary_evidence_required_for_future_run"] is True
    chain = _run_offline_payload_readiness_chain()
    assert chain["payload"].no_authority_change is True


def test_no_credential_keys_in_full_chain_serialization() -> None:
    chain = _run_offline_payload_readiness_chain()
    artifacts = [
        chain["payload_serialized"],
        serialize_order_capability_private_endpoint_boundary_verdict(chain["boundary"]),
        serialize_order_capability_cleanup_verdict(chain["cleanup"]),
    ]
    for artifact in artifacts:
        for key in artifact:
            assert key.lower() not in FORBIDDEN_SERIALIZATION_KEYS


def test_cleanup_remains_fail_closed_with_placeholder_marker() -> None:
    chain = _run_offline_payload_readiness_chain()
    cleanup = chain["cleanup"]
    assert cleanup.verdict == OrderCapabilityCleanupVerdictKind.FAIL_CLOSED
    assert REASON_CANCEL_CLEANUP_PLACEHOLDER_NOT_VALIDATED in cleanup.reason_codes
    assert cleanup.cancel_authorized is False
    assert cleanup.execute_authorized is False
    assert cleanup.preflight_remains_blocked is True
    assert chain["payload"].cleanup_cancel_correlation_marker == DEFAULT_CLEANUP_PLACEHOLDER_MARKER


def test_offline_readiness_requires_no_credentials() -> None:
    fixture = _load_fixture()
    chain = _run_offline_payload_readiness_chain()
    boundary_input = _path_c_readonly_boundary_input()
    assert fixture["credential_use_required"] is False
    assert chain["dry_validation"]["safety_flags"]["no_secret_read"] is True
    assert boundary_input.evidence_summary.no_secret_material is True
