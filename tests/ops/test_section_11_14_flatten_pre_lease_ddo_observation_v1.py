"""§11.14 pre-lease DDO observation host-hook tests.

Hard-network-blocked. Observation runs after local pre-wire denies and
before `_consume_receipt_lease`. Tests stop before lease consume and
urllib. Capture failure must not change the productive deny.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    BLOCKED_CAPTURE_SEAMS_V0,
    DdoCaptureBindingV0,
    bind_capture_session_v0,
    reset_capture_session_v0,
)
from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    AuthenticatedGatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.bounded_activation_permit_v1 import (
    offline_contract_proof_bounded_activation_permit_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    REQUIRED_SECRETREF_URI,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
    FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
    FLATTEN_EXECUTE_PURPOSE_CANONICAL,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateInputV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    LiveCanaryFlattenProductiveTransportError,
    live_canary_http_request_from_flatten_receipt_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    build_file_secretref_vault_backend_v1,
    release_live_canary_ephemeral_material_v1,
    resolve_and_load_live_canary_secretref_ephemeral_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_ORIGIN_MAIN_SHA,
    INSTRUMENT_ID,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.hmac_generation_v1 import (
    generate_flatten_authenticated_headers_v1,
    hmac_signed_request_from_artifact_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.hmac_signed_network_session_bind_v1 import (
    bind_hmac_signed_productive_network_session_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.network_session_authority_v1 import (
    current_section_11_14_network_session_explicit_v1,
    issue_owner_network_session_authority_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_wire_send_authority_v1 import (
    productive_wire_send_authority_id_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_wire_send_owner_contract_schema_v1 import (
    AUTHORITY_SOURCE_CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND,
    AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND,
    PRODUCTIVE_WIRE_SEND_ACTION,
    PRODUCTIVE_WIRE_SEND_CONFIRM_TOKEN_EXPECTED,
    PRODUCTIVE_WIRE_SEND_PURPOSE_EXPECTED,
    PRODUCTIVE_WIRE_SEND_SCHEMA_VERSION,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.receipt_missing_v1 import (
    attach_flatten_pre_send_receipt_once_v1,
    mint_flatten_pre_send_attachable_receipt_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SEND_SRC = (
    REPO_ROOT
    / "src/ops/section_11_13_5_live_canary_minimum_exposure_v1"
    / "authenticated_productive_transport_v1.py"
)
SPEC = REPO_ROOT / "docs/ops/specs/SECTION_11_14_PRE_LEASE_DDO_OBSERVATION_V1.md"
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
_FX = FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL
HMAC_ORIGIN_SHA = "e14587a5b03a13963ffb7524f9c25f0cfea0dfc2"
HMAC_ENVELOPE_ID = "0a0133a3b82e4a15bf6986605a9a8e6b47b22665b485ff0f570200803f21cdbe"
TARGET = DEFAULT_INSTRUMENT_ID
QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
FIXTURE_KEY = "ns-bind-fixture-key-not-live"
FIXTURE_SECRET = "ns-bind-fixture-secret-not-live"
FIXTURE_PASS = "ns-bind-fixture-pass-not-live"
URLLIB_PATCH = (
    "src.ops.section_11_13_5_live_canary_minimum_exposure_v1."
    "flatten_productive_transport_v1.open_productive_flatten_urllib_post_v1"
)
CONSUME_PATCH = (
    "src.ops.section_11_13_5_live_canary_minimum_exposure_v1."
    "authenticated_productive_transport_v1._consume_receipt_lease"
)
STOP_BEFORE_LEASE = "TEST_STOP_BEFORE_LEASE_CONSUME"


def _boom_wire(*_a: Any, **_k: Any) -> Any:
    raise AssertionError("WIRE")


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_PRE_LEASE_DDO_TESTS")

    monkeypatch.setattr("urllib.request.urlopen", _blocked)
    monkeypatch.setattr("socket.create_connection", _blocked)
    monkeypatch.setattr(URLLIB_PATCH, _boom_wire)


def _positions(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _pending(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _price() -> FlattenPriceInputV1:
    return FlattenPriceInputV1(
        flatten_side="SELL",
        observed_signed_pos="1",
        bid="64805.6",
        ask="64805.7",
        quote_timestamp_ms=QUOTE_TS,
        evaluation_timestamp_ms=EVAL_TS,
        tick_sz="0.1",
        freshness_threshold_ms=str(FRESHNESS_THRESHOLD_MS),
    )


def _valid_gate(*, origin_main_sha: str = HMAC_ORIGIN_SHA) -> FlattenPreSendGateInputV1:
    return FlattenPreSendGateInputV1(
        live_authorized=False,
        live_enabled=True,
        live_armed=True,
        flatten_live_wire_enabled=True,
        allow_productive_wire_send=True,
        flatten_execute_token=_FX,
        flatten_execute_purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        flatten_execute_owner_go=FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        pending_orders_payload=_pending(),
        price_input=_price(),
        owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        origin_main_sha=origin_main_sha,
        flatten_execute_bound_origin_main_sha=origin_main_sha,
        instrument_id=TARGET,
        one_shot_no_retry=True,
        duplicate_post_protection=True,
        flatten_pre_send_decision_id="hmac-prelease-ddo-pre-send-1",
        position_observation_freshness_evidence=PositionObservationFreshnessEvidenceV1(
            response_received_monotonic_ms=0,
            decision_id="hmac-prelease-ddo-pre-send-1",
            evidence_kind=PRE_SEND_EVIDENCE_KIND,
        ),
        monotonic_ms_clock=(lambda: 0),
        bounded_activation_permit=offline_contract_proof_bounded_activation_permit_v1(
            origin_main_sha=origin_main_sha,
            instrument_id=TARGET,
        ),
    )


def _wire_send() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": PRODUCTIVE_WIRE_SEND_SCHEMA_VERSION,
        "authority_type": AUTHORITY_TYPE_OWNER_PRODUCTIVE_WIRE_SEND,
        "authority_source": AUTHORITY_SOURCE_CANONICAL_OWNER_PRODUCTIVE_WIRE_SEND,
        "issued": True,
        "issued_at": "2026-09-08T12:00:00Z",
        "section": "11.14",
        "purpose": PRODUCTIVE_WIRE_SEND_PURPOSE_EXPECTED,
        "action": PRODUCTIVE_WIRE_SEND_ACTION,
        "origin_main_sha": HMAC_ORIGIN_SHA,
        "exact_envelope_id": HMAC_ENVELOPE_ID,
        "instrument_id": TARGET,
        "confirm_token": PRODUCTIVE_WIRE_SEND_CONFIRM_TOKEN_EXPECTED,
        "single_use": True,
        "consumed": False,
        "retry_allowed": False,
        "second_submit_allowed": False,
        "network_session_grant_cannot_authorize_this": True,
        "flatten_grant_cannot_authorize_this": True,
        "live_flags_cannot_authorize_this": True,
        "session_arming_cannot_authorize_this": True,
    }
    payload["authority_id"] = productive_wire_send_authority_id_v1(payload)
    return payload


def _handle(tmp_path: Path):
    creds = {
        "api_key": FIXTURE_KEY,
        "api_secret": FIXTURE_SECRET,
        "passphrase": FIXTURE_PASS,
    }
    vault = tmp_path / "prelease-ddo-fixture-vault.json"
    vault.write_text(json.dumps({REQUIRED_SECRETREF_URI: creds}), encoding="utf-8")
    backend = build_file_secretref_vault_backend_v1(vault_file=vault)
    return resolve_and_load_live_canary_secretref_ephemeral_v1(
        secret_reference=REQUIRED_SECRETREF_URI,
        vault_backend=backend,
    )


def _session_artifact() -> dict[str, Any]:
    produced = issue_owner_network_session_authority_v1(
        explicit=current_section_11_14_network_session_explicit_v1(issued_at="2026-09-08T14:00:00Z")
    )
    artifact = produced["artifact"]
    assert artifact is not None
    return artifact


def _mint_hmac(tmp_path: Path):
    handle = _handle(tmp_path)
    receipt = mint_flatten_pre_send_attachable_receipt_v1(
        _valid_gate(),
        expected_origin_main_sha=HMAC_ORIGIN_SHA,
    )
    transport = AuthenticatedGatedProductiveFlattenTransportV1()
    attach_flatten_pre_send_receipt_once_v1(transport, receipt)
    request = live_canary_http_request_from_flatten_receipt_v1(receipt)
    wire = _wire_send()
    artifact = generate_flatten_authenticated_headers_v1(
        transport,
        receipt,
        request,
        handle=handle,
        wire_send=wire,
        origin_main_sha=HMAC_ORIGIN_SHA,
        instrument_id=TARGET,
        exact_envelope_id=HMAC_ENVELOPE_ID,
    )
    return handle, transport, receipt, artifact, wire


def _bind(transport: Any, receipt: Any, artifact: Any) -> None:
    result = bind_hmac_signed_productive_network_session_v1(
        transport=transport,
        receipt=receipt,
        artifact=artifact,
        network_session=_session_artifact(),
        origin_main_sha=BOUND_ORIGIN_MAIN_SHA,
        instrument_id=INSTRUMENT_ID,
        exact_envelope_id=BOUND_FROZEN_ENVELOPE_ID,
    )
    assert result["bound"] is True
    assert result["send_invoked"] is False


def _stop_before_lease(_receipt: Any) -> None:
    raise LiveCanaryFlattenProductiveTransportError(STOP_BEFORE_LEASE)


def _deny_text(exc: BaseException) -> str:
    return str(exc)


def test_standing_live_flags_remain_false() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert CANARY_AUTHORIZED is False


def test_hook_position_exact_in_source() -> None:
    text = SEND_SRC.read_text(encoding="utf-8")
    class_at = text.find("class AuthenticatedGatedProductiveFlattenTransportV1")
    send_at = text.find("def send(self, request: LiveCanaryHttpRequestV1)", class_at)
    post_at = text.find("assert_productive_flatten_post_request_v1(request)", send_at)
    observe_at = text.find("observe_flatten_pre_lease_send_intent_v1(", send_at)
    lease_at = text.find("_consume_receipt_lease(receipt)", send_at)
    urllib_at = text.find("open_productive_flatten_urllib_post_v1(request)", send_at)
    assert class_at >= 0
    assert send_at > class_at
    assert post_at > send_at
    assert observe_at > post_at
    assert lease_at > observe_at
    assert urllib_at > lease_at
    assert "venue_execution" not in text[observe_at : observe_at + 200]


def test_return_parity_and_no_capture_on_session_deny(tmp_path: Path) -> None:
    handle, transport, receipt, artifact, wire = _mint_hmac(tmp_path)
    signed = hmac_signed_request_from_artifact_v1(receipt, artifact)
    try:
        with pytest.raises(
            LiveCanaryFlattenProductiveTransportError,
            match="PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED",
        ) as without_exc:
            transport.send(signed)
        without = _deny_text(without_exc.value)
        binding = DdoCaptureBindingV0(enabled=True, ledger_path=None)
        capture_session = bind_capture_session_v0(binding)
        try:
            with pytest.raises(
                LiveCanaryFlattenProductiveTransportError,
                match="PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED",
            ) as with_exc:
                transport.send(signed)
        finally:
            reset_capture_session_v0(capture_session)
        assert _deny_text(with_exc.value) == without
        assert receipt.send_lease.consumed is False
        assert transport.last_wire_attempted is False
        assert transport._sent is False
        assert wire["consumed"] is False
        assert not binding.captured_records
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_hook_runs_before_lease_without_wire_and_preserves_identities(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(CONSUME_PATCH, _stop_before_lease)
    handle, transport, receipt, artifact, wire = _mint_hmac(tmp_path)
    signed = hmac_signed_request_from_artifact_v1(receipt, artifact)
    _bind(transport, receipt, artifact)
    binding = DdoCaptureBindingV0(
        enabled=True,
        ledger_path=None,
        capture_repository_sha="0bf4d93d33b1693bdf43cf176562b9b0cdc3b721",
    )
    capture_session = bind_capture_session_v0(binding)
    order: list[str] = []
    original_observe = __import__(
        "src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.flatten_pre_lease_ddo_observation_v1",
        fromlist=["observe_flatten_pre_lease_send_intent_v1"],
    ).observe_flatten_pre_lease_send_intent_v1

    def _observe(**kwargs: Any) -> None:
        order.append("observe")
        original_observe(**kwargs)

    monkeypatch.setattr(
        "src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1."
        "flatten_pre_lease_ddo_observation_v1.observe_flatten_pre_lease_send_intent_v1",
        _observe,
    )
    try:
        with pytest.raises(LiveCanaryFlattenProductiveTransportError, match=STOP_BEFORE_LEASE):
            transport.send(signed)
        assert order == ["observe"]
        assert receipt.send_lease.consumed is False
        assert transport.last_wire_attempted is False
        assert transport._sent is False
        assert wire["consumed"] is False
        observations = [
            item
            for item in binding.captured_records
            if item["schema_name"] == SCHEMA_NAME_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION
        ]
        assert len(observations) == 1
        observed = observations[0]
        assert observed["approved_request_identity"] == receipt.approved_request_identity
        assert observed["hmac_bind_request_identity"] == receipt.approved_request_identity
        assert observed["hmac_bind_exact_envelope_id"] == BOUND_FROZEN_ENVELOPE_ID
        assert observed["hmac_bind_origin_main_sha"] == BOUND_ORIGIN_MAIN_SHA
        assert observed["capture_repository_sha"] == "0bf4d93d33b1693bdf43cf176562b9b0cdc3b721"
        assert observed["hmac_bind_origin_main_sha"] != observed["capture_repository_sha"]
        assert observed["hmac_bind_exact_envelope_id"] != HMAC_ENVELOPE_ID
        assert observed["identity_relationship_approved_request_to_hmac_bind_request"] == (
            "EQUAL_OBSERVED"
        )
        assert (
            observed["identity_relationship_hmac_bind_origin_main_sha_to_capture_repository_sha"]
            == "UNPROVEN"
        )
        assert observed["singular_canonical_correlation_id_claimed"] == "false"
        assert observed["observation_only"] == "true"
        assert observed["lease_consumed"] == "false"
        assert observed["wire_send_executed"] == "false"
        assert observed["trading_authority"] == "NONE"
        assert observed["execution_authority"] == "NONE"
        assert observed["permission_authority"] == "NONE"
        assert observed["live_authority_changed"] == "false"
        assert observed["venue_execution_not_claimed"] == "true"
        assert observed["hmac_signing_input_digest"] != "UNKNOWN"
        assert len(observed["hmac_signing_input_digest"]) == 64
    finally:
        reset_capture_session_v0(capture_session)
        release_live_canary_ephemeral_material_v1(handle)


def test_return_parity_with_successful_capture_before_lease(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(CONSUME_PATCH, _stop_before_lease)
    handle, transport, receipt, artifact, _wire = _mint_hmac(tmp_path)
    signed = hmac_signed_request_from_artifact_v1(receipt, artifact)
    _bind(transport, receipt, artifact)
    try:
        with pytest.raises(LiveCanaryFlattenProductiveTransportError, match=STOP_BEFORE_LEASE) as (
            without_exc
        ):
            transport.send(signed)
        without = _deny_text(without_exc.value)
        binding = DdoCaptureBindingV0(enabled=True, ledger_path=None)
        capture_session = bind_capture_session_v0(binding)
        try:
            with pytest.raises(
                LiveCanaryFlattenProductiveTransportError, match=STOP_BEFORE_LEASE
            ) as with_exc:
                transport.send(signed)
        finally:
            reset_capture_session_v0(capture_session)
        assert _deny_text(with_exc.value) == without
        assert receipt.send_lease.consumed is False
        assert transport.last_wire_attempted is False
        assert transport._sent is False
        assert binding.captured_records
    finally:
        release_live_canary_ephemeral_material_v1(handle)


def test_capture_failure_does_not_change_productive_deny(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(CONSUME_PATCH, _stop_before_lease)

    def _boom_observe(*_a: Any, **_k: Any) -> None:
        raise RuntimeError("CAPTURE_INJECTED_FAILURE")

    monkeypatch.setattr(
        "src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1."
        "flatten_pre_lease_ddo_observation_v1.observe_producer_result_v0",
        _boom_observe,
    )
    handle, transport, receipt, artifact, wire = _mint_hmac(tmp_path)
    signed = hmac_signed_request_from_artifact_v1(receipt, artifact)
    _bind(transport, receipt, artifact)
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=None)
    capture_session = bind_capture_session_v0(binding)
    try:
        with pytest.raises(LiveCanaryFlattenProductiveTransportError, match=STOP_BEFORE_LEASE):
            transport.send(signed)
        assert receipt.send_lease.consumed is False
        assert transport.last_wire_attempted is False
        assert transport._sent is False
        assert wire["consumed"] is False
        assert binding.last_error is not None
        assert "CAPTURE_INJECTED_FAILURE" in binding.last_error
        assert binding.last_result is not None
        assert binding.last_result["decision_unchanged"] is True
        assert binding.last_result["capture_failure_may_enable_send"] is False
        assert binding.last_result["capture_failure_may_disable_an_otherwise_allowed_send"] is False
    finally:
        reset_capture_session_v0(capture_session)
        release_live_canary_ephemeral_material_v1(handle)


def test_blocked_seams_remain_blocked() -> None:
    assert "venue_execution" in BLOCKED_CAPTURE_SEAMS_V0
    assert "execution_permission_controller" in BLOCKED_CAPTURE_SEAMS_V0
    assert "real_outcome_horizon_engine" in BLOCKED_CAPTURE_SEAMS_V0
    src = SEND_SRC.read_text(encoding="utf-8")
    assert 'seam_id="venue_execution"' not in src
    assert "seam_id='venue_execution'" not in src


def test_docs_persist_is_observation_only() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    runbook = MASTER_RUNBOOK.read_text(encoding="utf-8")
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_PRE_LEASE_DDO_OBSERVATION_V1" in spec
    assert "DDO_OBSERVATION_ONLY=true" in spec
    assert "SEND_LEASE_CONSUME_NOT_AUTHORIZED_BY_THIS_GO=true" in spec
    assert "WIRE_SEND_NOT_AUTHORIZED_BY_THIS_GO=true" in spec
    assert "CURRENT_RUNTIME_GATE_REMAINS=SEND_LEASE_CONSUME" in spec
    assert "11.14 PRE_LEASE_DDO_OBSERVATION" in runbook
    assert "SEND_LEASE_CONSUME_NOT_AUTHORIZED_BY_THIS_GO=true" in runbook
    assert "CURRENT_RUNTIME_GATE_REMAINS=SEND_LEASE_CONSUME" in runbook
    assert "11.14 PRE_LEASE_DDO_OBSERVATION" in mot
    assert "SECTION_11_14_PRE_LEASE_DDO_OBSERVATION_V1.md" in mot
