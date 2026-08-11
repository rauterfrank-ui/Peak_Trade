"""Focused positive/negative suite for §11.13.2 LIVE_PRIVATE_READ_ONLY preparation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1 import (
    constants_v1 as cap_11_7,
)
from src.ops.section_11_13_2_live_private_read_only_v1.authorization_v1 import (
    LivePrivateRoAuthorizationError,
    default_authorization_is_false_v1,
    validate_live_private_read_only_authorization_v1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.binding_v1 import (
    LivePrivateRoBindingError,
    build_live_private_ro_venue_binding_v1,
    reject_cross_binding_v1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.config_v1 import (
    LivePrivateRoConfigError,
    load_live_private_ro_config_v1,
    require_execute_time_fields_v1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    CANONICAL_NEXT_STEP_AFTER_PREPARATION_MERGE,
    CANONICAL_NEXT_STEP_AFTER_PROVEN,
    ENABLE_LIVE_TRADING,
    FULLY_AUTONOMOUS_LIVE_TRADING_READY,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_ORDER_AUTHORIZED,
    LIVE_PRIVATE_READ_ONLY_AUTHORIZED_DEFAULT,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    OWNER_GO_EXECUTE,
    PACKAGE_MARKER,
    REQUIRED_CREDENTIAL_CLASS,
)
from src.ops.section_11_13_2_live_private_read_only_v1.evidence_v1 import build_claims_v1
from src.ops.section_11_13_2_live_private_read_only_v1.http_client_v1 import (
    LivePrivateRoHttpClientV1,
    LivePrivateRoHttpError,
    RecordingFakeTransportV1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.owner_input_contract_v1 import (
    build_owner_execute_input_contract_v1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.response_assertions_v1 import (
    LivePrivateRoAssertionError,
    assert_authenticated_private_read_success_v1,
    redact_account_identity_v1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.runner_v1 import (
    LivePrivateRoRunnerError,
    run_execute_with_injected_transport_for_tests_v1,
    run_section_11_13_2_live_private_read_only_v1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.secretref_v1 import (
    LivePrivateRoSecretRefError,
    build_live_private_ro_secretref_metadata_v1,
    reject_cross_environment_secretref_use_v1,
)
from src.ops.section_11_13_2_live_private_read_only_v1.verifier_v1 import (
    LivePrivateRoVerifierError,
    refuse_fixture_proven_claim_v1,
    verify_live_private_read_only_evidence_v1,
)

ORIGIN_SHA = "0903b4ad6fdfc7eca9bc3db221580c125ba521a8"


def _valid_config(**overrides: object) -> dict:
    base = {
        "environment": "LIVE",
        "venue": "owner_live_venue",
        "entity": "owner_live_entity",
        "region": "owner_region",
        "rest_host": "www.example-live-host.invalid",
        "rest_base": "https://www.example-live-host.invalid",
        "account_scope": "acct-owner-binding",
        "instrument_scope": None,
        "secretref_uri": "secretref://vault/peak-trade/live-private-ro/owner-venue",
        "credential_class": REQUIRED_CREDENTIAL_CLASS,
        "method_allowlist": ["GET"],
        "endpoint_allowlist": [
            "/api/v5/account/config",
            "/api/v5/account/balance",
            "/api/v5/account/positions",
            "/api/v5/trade/orders-pending",
        ],
        "max_request_count": 4,
        "timeout_seconds": 10.0,
        "max_retries": 2,
        "evidence_root": "evidence/ops/section_11_13_2_live_private_read_only_proven_v1",
        "evidence_version": "section_11_13_2_live_private_read_only_proven_v1",
        "expected_live_marker": "LIVE",
        "expected_demo_marker_absent": True,
        "owner_declared_host_allowlist": ["www.example-live-host.invalid"],
    }
    base.update(overrides)
    return base


def test_package_marker_and_defaults() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    assert default_authorization_is_false_v1() is True
    assert LIVE_PRIVATE_READ_ONLY_AUTHORIZED_DEFAULT is False
    assert LIVE_PRIVATE_READ_ONLY_PROVEN is False
    assert LIVE_AUTHORIZED is False
    assert ENABLE_LIVE_TRADING is False
    assert FULLY_AUTONOMOUS_LIVE_TRADING_READY is False


def test_default_auth_false() -> None:
    assert LIVE_PRIVATE_READ_ONLY_AUTHORIZED_DEFAULT is False


def test_missing_go() -> None:
    cfg = load_live_private_ro_config_v1(_valid_config())
    with pytest.raises(LivePrivateRoAuthorizationError, match="OWNER_GO_MISSING"):
        validate_live_private_read_only_authorization_v1(
            owner_go="",
            authorization_scope=AUTHORIZATION_SCOPE,
            bound_origin_main_sha=ORIGIN_SHA,
            expected_origin_main_sha=ORIGIN_SHA,
            bound_config_digest=cfg.digest(),
            expected_config_digest=cfg.digest(),
            live_private_read_only_authorized=True,
        )


def test_wrong_go() -> None:
    cfg = load_live_private_ro_config_v1(_valid_config())
    with pytest.raises(LivePrivateRoAuthorizationError, match="OWNER_GO_MISMATCH"):
        validate_live_private_read_only_authorization_v1(
            owner_go="OWNER_GO_LIVE_SHADOW",
            authorization_scope=AUTHORIZATION_SCOPE,
            bound_origin_main_sha=ORIGIN_SHA,
            expected_origin_main_sha=ORIGIN_SHA,
            bound_config_digest=cfg.digest(),
            expected_config_digest=cfg.digest(),
            live_private_read_only_authorized=True,
        )


def test_go_scope_mismatch() -> None:
    cfg = load_live_private_ro_config_v1(_valid_config())
    with pytest.raises(LivePrivateRoAuthorizationError, match="AUTHORIZATION_SCOPE_MISMATCH"):
        validate_live_private_read_only_authorization_v1(
            owner_go=OWNER_GO_EXECUTE,
            authorization_scope="LIVE_AUTHORIZED",
            bound_origin_main_sha=ORIGIN_SHA,
            expected_origin_main_sha=ORIGIN_SHA,
            bound_config_digest=cfg.digest(),
            expected_config_digest=cfg.digest(),
            live_private_read_only_authorized=True,
        )


def test_sha_config_mismatch() -> None:
    cfg = load_live_private_ro_config_v1(_valid_config())
    with pytest.raises(LivePrivateRoAuthorizationError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        validate_live_private_read_only_authorization_v1(
            owner_go=OWNER_GO_EXECUTE,
            authorization_scope=AUTHORIZATION_SCOPE,
            bound_origin_main_sha=ORIGIN_SHA,
            expected_origin_main_sha="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            bound_config_digest=cfg.digest(),
            expected_config_digest=cfg.digest(),
            live_private_read_only_authorized=True,
        )
    with pytest.raises(LivePrivateRoAuthorizationError, match="CONFIG_DIGEST_MISMATCH"):
        validate_live_private_read_only_authorization_v1(
            owner_go=OWNER_GO_EXECUTE,
            authorization_scope=AUTHORIZATION_SCOPE,
            bound_origin_main_sha=ORIGIN_SHA,
            expected_origin_main_sha=ORIGIN_SHA,
            bound_config_digest=cfg.digest(),
            expected_config_digest="0" * 64,
            live_private_read_only_authorized=True,
        )


def test_missing_live_venue_binding() -> None:
    with pytest.raises(LivePrivateRoBindingError, match="VENUE_REQUIRED"):
        build_live_private_ro_venue_binding_v1(
            environment="LIVE",
            venue="",
            entity="e",
            region="r",
            rest_host="www.example-live-host.invalid",
            account_scope="a",
        )


def test_demo_venue_in_live_runner() -> None:
    with pytest.raises(LivePrivateRoRunnerError, match="ENVIRONMENT_MUST_BE_LIVE|FAIL_CLOSED"):
        run_section_11_13_2_live_private_read_only_v1(
            mode="preflight",
            config_payload=_valid_config(environment="DEMO"),
            origin_main_sha=ORIGIN_SHA,
        )


def test_testnet_credentials_in_live_runner() -> None:
    with pytest.raises(LivePrivateRoRunnerError, match="FORBIDDEN_CREDENTIAL_CLASS|CREDENTIAL"):
        run_section_11_13_2_live_private_read_only_v1(
            mode="preflight",
            config_payload=_valid_config(credential_class="OKX_DEMO_TRADING_API_KEY_ONLY"),
            origin_main_sha=ORIGIN_SHA,
        )


def test_live_credentials_in_demo_testnet_path() -> None:
    with pytest.raises(LivePrivateRoSecretRefError, match="CROSS_BIND_LIVE_REF_TO_DEMO"):
        reject_cross_environment_secretref_use_v1(
            secretref_uri="secretref://vault/peak-trade/live-private-ro/owner",
            requested_environment="DEMO",
        )
    with pytest.raises(LivePrivateRoSecretRefError, match="CROSS_BIND_LIVE_REF_TO_DEMO"):
        reject_cross_environment_secretref_use_v1(
            secretref_uri="secretref://vault/peak-trade/live-private-ro/owner",
            requested_environment="TESTNET",
        )


def test_missing_secretref() -> None:
    with pytest.raises(LivePrivateRoConfigError, match="MISSING:.*secretref"):
        require_execute_time_fields_v1(
            load_live_private_ro_config_v1(_valid_config(secretref_uri=""))
        )


def test_wrong_credential_class() -> None:
    with pytest.raises(LivePrivateRoSecretRefError, match="LIVE_PRIVATE_RO_CREDENTIAL_CLASS"):
        build_live_private_ro_secretref_metadata_v1(
            secretref_uri="secretref://vault/peak-trade/live-private-ro/x",
            credential_class="LIVE_TRADING_API_KEY",
        )


def test_wrong_host() -> None:
    binding = build_live_private_ro_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    client = LivePrivateRoHttpClientV1(
        binding=binding,
        transport=RecordingFakeTransportV1(),
    )
    # Force host mismatch by mutating binding base via alternate client construction.
    bad_binding = build_live_private_ro_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.other-live-host.invalid",
        account_scope="a",
    )
    with pytest.raises(LivePrivateRoHttpError, match="HOST_MISMATCH"):
        # Build request against other host by temporarily swapping.
        from src.ops.section_11_13_2_live_private_read_only_v1.http_client_v1 import (
            assert_host_matches_binding_v1,
        )

        assert_host_matches_binding_v1(binding=binding, request_host=bad_binding.rest_host)


def test_demo_simulation_header_present() -> None:
    binding = build_live_private_ro_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    client = LivePrivateRoHttpClientV1(binding=binding, transport=RecordingFakeTransportV1())
    with pytest.raises(LivePrivateRoHttpError, match="DEMO_SIMULATION_HEADER"):
        client.get(
            endpoint="/api/v5/account/balance",
            headers={"x-simulated-trading": "1"},
        )


def test_get_allowlisted_endpoint_pass() -> None:
    binding = build_live_private_ro_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    transport = RecordingFakeTransportV1()
    client = LivePrivateRoHttpClientV1(binding=binding, transport=transport)
    resp = client.get(endpoint="/api/v5/account/balance")
    assert resp.status_code == 200
    assert transport.calls[0].method == "GET"


def test_post_hard_block_before_transport() -> None:
    binding = build_live_private_ro_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    transport = RecordingFakeTransportV1()
    client = LivePrivateRoHttpClientV1(binding=binding, transport=transport)
    with pytest.raises(LivePrivateRoHttpError, match="HTTP_METHOD_HARD_BLOCK"):
        client.post(endpoint="/api/v5/account/balance")
    assert transport.calls == []


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/v5/trade/order",
        "/api/v5/trade/cancel-order",
        "/api/v5/trade/amend-order",
        "/api/v5/trade/batch-orders",
        "/api/v5/asset/withdrawal",
        "/api/v5/asset/transfer",
    ],
)
def test_mutation_endpoints_hard_block(endpoint: str) -> None:
    binding = build_live_private_ro_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    client = LivePrivateRoHttpClientV1(binding=binding, transport=RecordingFakeTransportV1())
    with pytest.raises(LivePrivateRoHttpError, match="MUTATION_ENDPOINT|NOT_ALLOWLISTED"):
        client.get(endpoint=endpoint)


def test_endpoint_not_allowlisted() -> None:
    binding = build_live_private_ro_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    client = LivePrivateRoHttpClientV1(binding=binding, transport=RecordingFakeTransportV1())
    with pytest.raises(LivePrivateRoHttpError, match="ENDPOINT_NOT_ALLOWLISTED"):
        client.get(endpoint="/api/v5/account/bills")


def test_retry_bounded_and_timeout() -> None:
    binding = build_live_private_ro_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    transport = RecordingFakeTransportV1(raise_timeout=True)
    client = LivePrivateRoHttpClientV1(
        binding=binding, transport=transport, max_retries=1, timeout_seconds=1.0
    )
    with pytest.raises(LivePrivateRoHttpError, match="TIMEOUT"):
        client.get(endpoint="/api/v5/account/balance")


@pytest.mark.parametrize("status", [401, 403])
def test_http_401_403_not_proven(status: int) -> None:
    binding = build_live_private_ro_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    transport = RecordingFakeTransportV1(status_code=status, body=b'{"msg":"denied"}')
    client = LivePrivateRoHttpClientV1(binding=binding, transport=transport)
    resp = client.get(endpoint="/api/v5/account/balance")
    with pytest.raises(LivePrivateRoAssertionError, match="AUTH_FAIL_NOT_PROVEN"):
        assert_authenticated_private_read_success_v1(
            response=resp,
            transport_class="LIVE_PRODUCTIVE_HTTP",
            venue_live_contact=True,
        )


def test_malformed_response() -> None:
    binding = build_live_private_ro_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    transport = RecordingFakeTransportV1(body=b"not-json")
    client = LivePrivateRoHttpClientV1(binding=binding, transport=transport)
    resp = client.get(endpoint="/api/v5/account/balance")
    with pytest.raises(LivePrivateRoAssertionError, match="MALFORMED_NON_JSON"):
        assert_authenticated_private_read_success_v1(
            response=resp,
            transport_class="LIVE_PRODUCTIVE_HTTP",
            venue_live_contact=True,
        )


def test_redaction() -> None:
    redacted, digest = redact_account_identity_v1("abcdef123456")
    assert "***" in redacted
    assert len(digest) == 64
    assert "abcdef123456" not in redacted


def test_evidence_schema_manifest_verify_and_fixture_cannot_set_proven(
    tmp_path: Path,
) -> None:
    result = run_execute_with_injected_transport_for_tests_v1(
        config_payload=_valid_config(),
        origin_main_sha=ORIGIN_SHA,
        transport=RecordingFakeTransportV1(),
        evidence_run_root=tmp_path / "run1",
    )
    assert result.LIVE_PRIVATE_READ_ONLY_PROVEN is False
    verified = verify_live_private_read_only_evidence_v1(tmp_path / "run1")
    assert verified["MANIFEST_VERIFY_RC"] == 0
    assert verified["LIVE_PRIVATE_READ_ONLY_PROVEN"] is False
    claims = json.loads((tmp_path / "run1" / "claims.json").read_text(encoding="utf-8"))
    with pytest.raises(LivePrivateRoVerifierError, match="FIXTURE_CANNOT_SET_LIVE_PROVEN"):
        refuse_fixture_proven_claim_v1({**claims, "LIVE_PRIVATE_READ_ONLY_PROVEN": True})


def test_build_claims_productive_true_only_when_all_invariants() -> None:
    claims = build_claims_v1(
        origin_main_sha=ORIGIN_SHA,
        config_digest="a" * 64,
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="h",
        account_identity_redacted="ab***56",
        secretref_log_safe_id="secretref-digest:abcd",
        secretref_credential_class=REQUIRED_CREDENTIAL_CLASS,
        authorization_scope=AUTHORIZATION_SCOPE,
        methods_used=["GET", "GET"],
        endpoints_used=["/api/v5/account/config", "/api/v5/account/balance"],
        request_count=2,
        http_result_classes=["HTTP_200_OK", "HTTP_200_OK"],
        authenticated_read_success=True,
        write_request_count=0,
        order_request_count=0,
        cancel_request_count=0,
        amend_request_count=0,
        withdraw_request_count=0,
        transfer_request_count=0,
        demo_simulation_marker_absent=True,
        cross_binding_checks_pass=True,
        redaction_check_pass=True,
        transport_class="LIVE_PRODUCTIVE_HTTP",
        venue_live_contact=True,
        fixture_or_demo_or_testnet=False,
        productive_live_transport=True,
        mode="execute",
        permission_attestation={"READ": True, "TRADE": False, "WITHDRAW": False},
        account_scope_match=True,
        okx_code_success=True,
    )
    assert claims["LIVE_PRIVATE_READ_ONLY_PROVEN"] is True
    fixture_claims = build_claims_v1(
        origin_main_sha=ORIGIN_SHA,
        config_digest="a" * 64,
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="h",
        account_identity_redacted="ab***56",
        secretref_log_safe_id="secretref-digest:abcd",
        secretref_credential_class=REQUIRED_CREDENTIAL_CLASS,
        authorization_scope=AUTHORIZATION_SCOPE,
        methods_used=["GET"],
        endpoints_used=["/api/v5/account/balance"],
        request_count=1,
        http_result_classes=["HTTP_200_OK"],
        authenticated_read_success=True,
        write_request_count=0,
        order_request_count=0,
        cancel_request_count=0,
        amend_request_count=0,
        withdraw_request_count=0,
        transfer_request_count=0,
        demo_simulation_marker_absent=True,
        cross_binding_checks_pass=True,
        redaction_check_pass=True,
        transport_class="LIVE_PRODUCTIVE_HTTP",
        venue_live_contact=True,
        fixture_or_demo_or_testnet=True,
        productive_live_transport=True,
        mode="fixture",
        permission_attestation={"READ": True, "TRADE": False, "WITHDRAW": False},
        account_scope_match=True,
        okx_code_success=True,
    )
    assert fixture_claims["LIVE_PRIVATE_READ_ONLY_PROVEN"] is False


def test_live_authorized_and_trading_gates_remain_false() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_ORDER_AUTHORIZED is False
    assert ENABLE_LIVE_TRADING is False
    assert FULLY_AUTONOMOUS_LIVE_TRADING_READY is False


def test_cap_11_7_remains_contracts_only() -> None:
    assert cap_11_7.LIVE_PRIVATE_READONLY_ACTIVATED is False
    assert cap_11_7.PRIVATE_READONLY_NETWORK_REACHABLE is False
    assert cap_11_7.LIVE_PRIVATE_READ_ONLY_PROVEN is False
    assert cap_11_7.NETWORK_SESSION_ALLOWED is False


def test_selector_governance_next_step_behavior() -> None:
    assert CANONICAL_NEXT_STEP_AFTER_PREPARATION_MERGE == OWNER_GO_EXECUTE
    assert "LIVE_SHADOW" in CANONICAL_NEXT_STEP_AFTER_PROVEN


def test_preflight_zero_network_and_no_credential_before_auth(tmp_path: Path) -> None:
    # Missing GO / auth false: still no credential material, no network.
    with pytest.raises(LivePrivateRoRunnerError):
        run_section_11_13_2_live_private_read_only_v1(
            mode="execute",
            config_payload=_valid_config(),
            origin_main_sha=ORIGIN_SHA,
            live_private_read_only_authorized=False,
            owner_go=OWNER_GO_EXECUTE,
        )
    result = run_section_11_13_2_live_private_read_only_v1(
        mode="preflight",
        config_payload=_valid_config(),
        origin_main_sha=ORIGIN_SHA,
        evidence_run_root=tmp_path / "preflight",
    )
    assert result.ok is True
    assert result.NETWORK_EFFECT == "NONE"
    assert result.CREDENTIAL_ACCESS == "NONE"
    assert result.details["credential_material_loaded"] is False
    assert result.details["wire_send_performed"] is False


def test_cross_binding_reject() -> None:
    with pytest.raises(LivePrivateRoBindingError, match="CROSS_BINDING"):
        reject_cross_binding_v1(
            live_environment="LIVE",
            peer_environment="DEMO",
            live_credential_class=REQUIRED_CREDENTIAL_CLASS,
            peer_credential_class="OKX_DEMO_TRADING_API_KEY_ONLY",
        )


def test_demo_secretref_rejected_for_live() -> None:
    with pytest.raises(LivePrivateRoSecretRefError, match="CROSS_BIND_DEMO_TESTNET_REF"):
        reject_cross_environment_secretref_use_v1(
            secretref_uri="secretref://vault/peak-trade/demo/okx",
            requested_environment="LIVE",
        )


def test_owner_input_contract_has_no_invented_values() -> None:
    contract = build_owner_execute_input_contract_v1()
    assert contract["LIVE_PRIVATE_READ_ONLY_PROVEN"] is False
    for field in contract["fields"]:
        if field["id"] in {"permission_attestation", "separate_execute_go"}:
            continue
        assert field["value"] is None


def test_auth_false_blocks_execute() -> None:
    with pytest.raises(LivePrivateRoRunnerError, match="AUTHORIZED_FALSE|OWNER_GO"):
        run_section_11_13_2_live_private_read_only_v1(
            mode="execute",
            config_payload=_valid_config(),
            origin_main_sha=ORIGIN_SHA,
            live_private_read_only_authorized=False,
            owner_go=OWNER_GO_EXECUTE,
            transport=RecordingFakeTransportV1(),
        )


def test_forbidden_host_marker() -> None:
    with pytest.raises(LivePrivateRoBindingError, match="FORBIDDEN_NON_LIVE_HOST"):
        build_live_private_ro_venue_binding_v1(
            environment="LIVE",
            venue="v",
            entity="e",
            region="r",
            rest_host="demo-futures.kraken.com",
            account_scope="a",
        )


def _write_vault(tmp_path: Path, *, secretref: str, uid: str = "acct-owner-binding") -> Path:
    vault = tmp_path / "vault.json"
    material = json.dumps(
        {
            "api_key": "fixture-live-ro-key-not-real",
            "api_secret": "fixture-live-ro-secret-not-real-xx",
            "passphrase": "fixture-pass",
        },
        separators=(",", ":"),
    )
    vault.write_text(json.dumps({secretref: material}), encoding="utf-8")
    return vault


def test_okx_code_not_zero_fails() -> None:
    binding = build_live_private_ro_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="acct-owner-binding",
    )
    client = LivePrivateRoHttpClientV1(
        binding=binding,
        transport=RecordingFakeTransportV1(body=b'{"code":"50001","data":[]}'),
    )
    response = client.get(endpoint="/api/v5/account/balance")
    with pytest.raises(LivePrivateRoAssertionError, match="OKX_CODE_NOT_SUCCESS"):
        assert_authenticated_private_read_success_v1(
            response=response,
            transport_class="LIVE_PRODUCTIVE_HTTP",
            venue_live_contact=True,
        )


def test_account_scope_mismatch_fails() -> None:
    binding = build_live_private_ro_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="acct-owner-binding",
    )
    client = LivePrivateRoHttpClientV1(
        binding=binding,
        transport=RecordingFakeTransportV1(body=b'{"code":"0","data":[{"uid":"other-uid"}]}'),
    )
    response = client.get(endpoint="/api/v5/account/config")
    with pytest.raises(LivePrivateRoAssertionError, match="ACCOUNT_SCOPE_MISMATCH"):
        assert_authenticated_private_read_success_v1(
            response=response,
            transport_class="LIVE_PRODUCTIVE_HTTP",
            venue_live_contact=True,
            expected_account_scope="acct-owner-binding",
            require_account_identity=True,
        )


def test_permission_attestation_validation() -> None:
    from src.ops.section_11_13_2_live_private_read_only_v1.response_assertions_v1 import (
        validate_permission_attestation_v1,
    )

    assert validate_permission_attestation_v1(
        {"READ": True, "TRADE": False, "WITHDRAW": False}
    ) == {"READ": True, "TRADE": False, "WITHDRAW": False}
    with pytest.raises(LivePrivateRoAssertionError, match="TRADE_MUST_BE_FALSE"):
        validate_permission_attestation_v1({"READ": True, "TRADE": True, "WITHDRAW": False})


def test_live_ephemeral_vault_borrow_release(tmp_path: Path) -> None:
    from src.ops.section_11_13_2_live_private_read_only_v1.live_credential_ephemeral_v1 import (
        borrow_live_ephemeral_material_for_session_auth_v1,
        build_file_secretref_vault_backend_v1,
        release_live_ephemeral_material_v1,
        resolve_and_load_live_secretref_ephemeral_v1,
    )

    secretref = "secretref://vault/peak-trade/live-private-ro/owner-venue"
    vault = _write_vault(tmp_path, secretref=secretref)
    backend = build_file_secretref_vault_backend_v1(vault_file=vault)
    handle = resolve_and_load_live_secretref_ephemeral_v1(
        secret_reference=secretref,
        vault_backend=backend,
    )
    material = borrow_live_ephemeral_material_for_session_auth_v1(handle)
    assert "api_key" in material
    release_live_ephemeral_material_v1(handle)
    with pytest.raises(Exception, match="EPHEMERAL_MATERIAL_GONE"):
        borrow_live_ephemeral_material_for_session_auth_v1(handle)


def test_live_ephemeral_rejects_testnet_runtime(tmp_path: Path) -> None:
    from src.ops.section_11_13_2_live_private_read_only_v1.live_credential_ephemeral_v1 import (
        LivePrivateRoCredentialError,
        build_file_secretref_vault_backend_v1,
        resolve_and_load_live_secretref_ephemeral_v1,
    )

    secretref = "secretref://vault/peak-trade/live-private-ro/owner-venue"
    vault = _write_vault(tmp_path, secretref=secretref)
    backend = build_file_secretref_vault_backend_v1(vault_file=vault)
    with pytest.raises(LivePrivateRoCredentialError, match="SECRETREF_SCOPE_MUST_BE_LIVE"):
        resolve_and_load_live_secretref_ephemeral_v1(
            secret_reference=secretref,
            vault_backend=backend,
            runtime_mode="TESTNET",
        )


def test_okx_live_ro_signer_get_only_and_no_simulation(tmp_path: Path) -> None:
    from src.ops.section_11_13_2_live_private_read_only_v1.live_credential_ephemeral_v1 import (
        build_file_secretref_vault_backend_v1,
        release_live_ephemeral_material_v1,
        resolve_and_load_live_secretref_ephemeral_v1,
    )
    from src.ops.section_11_13_2_live_private_read_only_v1.okx_live_ro_signer_v1 import (
        LivePrivateRoSignerError,
        auth_headers_presence_doc_v1,
        build_okx_live_ro_get_auth_headers_v1,
    )

    secretref = "secretref://vault/peak-trade/live-private-ro/owner-venue"
    vault = _write_vault(tmp_path, secretref=secretref)
    handle = resolve_and_load_live_secretref_ephemeral_v1(
        secret_reference=secretref,
        vault_backend=build_file_secretref_vault_backend_v1(vault_file=vault),
    )
    headers = build_okx_live_ro_get_auth_headers_v1(
        handle=handle,
        url="https://www.example-live-host.invalid/api/v5/account/config",
    )
    presence = auth_headers_presence_doc_v1(headers)
    assert presence["OK-ACCESS-SIGN_PRESENT"] is True
    assert presence["SIMULATION_HEADER_PRESENT"] is False
    with pytest.raises(LivePrivateRoSignerError, match="SIGNER_METHOD_FORBIDDEN"):
        build_okx_live_ro_get_auth_headers_v1(
            handle=handle,
            url="https://www.example-live-host.invalid/api/v5/account/config",
            method="POST",
        )
    with pytest.raises(LivePrivateRoSignerError, match="DEMO_SIMULATION_HEADER"):
        build_okx_live_ro_get_auth_headers_v1(
            handle=handle,
            url="https://www.example-live-host.invalid/api/v5/account/config",
            extra_headers={"x-simulated-trading": "1"},
        )
    release_live_ephemeral_material_v1(handle)


def test_productive_execute_injected_transport_can_prove(tmp_path: Path) -> None:
    from src.ops.section_11_13_2_live_private_read_only_v1.http_client_v1 import (
        ProductiveProofFakeTransportV1,
    )

    secretref = "secretref://vault/peak-trade/live-private-ro/owner-venue"
    vault = _write_vault(tmp_path, secretref=secretref)
    uid = "acct-owner-binding"
    transport = ProductiveProofFakeTransportV1(
        bodies_by_endpoint={
            "/api/v5/account/config": json.dumps({"code": "0", "data": [{"uid": uid}]}).encode(),
            "/api/v5/account/balance": json.dumps(
                {"code": "0", "data": [{"details": []}]}
            ).encode(),
        }
    )
    result = run_execute_with_injected_transport_for_tests_v1(
        config_payload=_valid_config(secretref_uri=secretref, account_scope=uid),
        origin_main_sha=ORIGIN_SHA,
        transport=transport,
        evidence_run_root=tmp_path / "prod",
        vault_file=vault,
        permission_attestation={"READ": True, "TRADE": False, "WITHDRAW": False},
    )
    assert result.NETWORK_EFFECT == "INJECTED_TRANSPORT_ONLY"
    assert result.LIVE_PRIVATE_READ_ONLY_PROVEN is True
    verified = verify_live_private_read_only_evidence_v1(tmp_path / "prod")
    assert verified["LIVE_PRIVATE_READ_ONLY_PROVEN"] is True
    assert verified["LIVE_AUTHORIZED"] is False


def test_productive_execute_recording_transport_cannot_prove(tmp_path: Path) -> None:
    secretref = "secretref://vault/peak-trade/live-private-ro/owner-venue"
    vault = _write_vault(tmp_path, secretref=secretref)
    uid = "acct-owner-binding"
    transport = RecordingFakeTransportV1(
        bodies_by_endpoint={
            "/api/v5/account/config": json.dumps({"code": "0", "data": [{"uid": uid}]}).encode(),
            "/api/v5/account/balance": json.dumps(
                {"code": "0", "data": [{"details": []}]}
            ).encode(),
        }
    )
    result = run_execute_with_injected_transport_for_tests_v1(
        config_payload=_valid_config(secretref_uri=secretref, account_scope=uid),
        origin_main_sha=ORIGIN_SHA,
        transport=transport,
        evidence_run_root=tmp_path / "notproven",
        vault_file=vault,
    )
    assert result.LIVE_PRIVATE_READ_ONLY_PROVEN is False


def test_execute_requires_vault_file() -> None:
    with pytest.raises(LivePrivateRoRunnerError, match="EXECUTE_REQUIRES_VAULT_FILE"):
        run_section_11_13_2_live_private_read_only_v1(
            mode="execute",
            config_payload=_valid_config(),
            origin_main_sha=ORIGIN_SHA,
            owner_go=OWNER_GO_EXECUTE,
            live_private_read_only_authorized=True,
            permission_attestation={"READ": True, "TRADE": False, "WITHDRAW": False},
            transport=RecordingFakeTransportV1(),
            evidence_run_root="/tmp/unused",
        )


def test_execute_rejects_trade_permission_attestation(tmp_path: Path) -> None:
    secretref = "secretref://vault/peak-trade/live-private-ro/owner-venue"
    vault = _write_vault(tmp_path, secretref=secretref)
    with pytest.raises(LivePrivateRoRunnerError, match="TRADE_MUST_BE_FALSE"):
        run_section_11_13_2_live_private_read_only_v1(
            mode="execute",
            config_payload=_valid_config(secretref_uri=secretref),
            origin_main_sha=ORIGIN_SHA,
            owner_go=OWNER_GO_EXECUTE,
            live_private_read_only_authorized=True,
            permission_attestation={"READ": True, "TRADE": True, "WITHDRAW": False},
            transport=RecordingFakeTransportV1(),
            vault_file=vault,
            evidence_run_root=tmp_path / "badperm",
        )


def test_put_patch_delete_hard_block() -> None:
    binding = build_live_private_ro_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    client = LivePrivateRoHttpClientV1(binding=binding, transport=RecordingFakeTransportV1())
    for method in ("PUT", "PATCH", "DELETE"):
        with pytest.raises(LivePrivateRoHttpError, match="HTTP_METHOD_HARD_BLOCK"):
            client.request(method=method, endpoint="/api/v5/account/balance")


def test_product_execute_path_ready_constant() -> None:
    from src.ops.section_11_13_2_live_private_read_only_v1.constants_v1 import (
        OWNER_GO_PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING,
        PRODUCTIVE_EXECUTE_PATH_READY,
    )

    assert PRODUCTIVE_EXECUTE_PATH_READY is True
    assert (
        OWNER_GO_PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING
        == "OWNER_GO_SECTION_11_13_2_PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING"
    )
    assert LIVE_PRIVATE_READ_ONLY_PROVEN is False
