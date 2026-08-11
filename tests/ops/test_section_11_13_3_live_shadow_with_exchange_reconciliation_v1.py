"""Focused positive/negative suite for §11.13.3 LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION preparation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1 import (
    constants_v1 as cap_11_7,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.authorization_v1 import (
    LiveShadowReconAuthorizationError,
    default_authorization_is_false_v1,
    validate_live_shadow_with_exchange_reconciliation_authorization_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.binding_v1 import (
    LiveShadowReconBindingError,
    build_live_shadow_recon_venue_binding_v1,
    reject_cross_binding_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.config_v1 import (
    LiveShadowReconConfigError,
    load_live_shadow_recon_config_v1,
    require_execute_time_fields_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    CANONICAL_NEXT_STEP_AFTER_PREPARATION_MERGE,
    CANONICAL_NEXT_STEP_AFTER_PROVEN,
    ENABLE_LIVE_TRADING,
    FULLY_AUTONOMOUS_LIVE_TRADING_READY,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_ORDER_AUTHORIZED,
    LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_AUTHORIZED_DEFAULT,
    LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN,
    OWNER_GO_EXECUTE,
    PACKAGE_MARKER,
    REQUIRED_CREDENTIAL_CLASS,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.evidence_v1 import (
    build_claims_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.http_client_v1 import (
    LiveShadowReconHttpClientV1,
    LiveShadowReconHttpError,
    RecordingFakeTransportV1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.owner_input_contract_v1 import (
    build_owner_execute_input_contract_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.response_assertions_v1 import (
    LiveShadowReconAssertionError,
    assert_authenticated_private_read_success_v1,
    redact_account_identity_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.runner_v1 import (
    LiveShadowReconRunnerError,
    run_execute_with_injected_transport_for_tests_v1,
    run_section_11_13_3_live_shadow_with_exchange_reconciliation_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.secretref_v1 import (
    LiveShadowReconSecretRefError,
    build_live_shadow_recon_secretref_metadata_v1,
    reject_cross_environment_secretref_use_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.verifier_v1 import (
    LiveShadowReconVerifierError,
    refuse_fixture_proven_claim_v1,
    verify_live_shadow_with_exchange_reconciliation_evidence_v1,
)

ORIGIN_SHA = "2bc4b337012b6e04180e76c95b803d2b4ec04153"


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
        "secretref_uri": "secretref://vault/peak-trade/live-shadow-recon/owner-venue",
        "credential_class": REQUIRED_CREDENTIAL_CLASS,
        "method_allowlist": ["GET"],
        "endpoint_allowlist": [
            "/api/v5/account/balance",
            "/api/v5/account/config",
            "/api/v5/account/positions",
            "/api/v5/trade/orders-pending",
        ],
        "max_request_count": 4,
        "timeout_seconds": 10.0,
        "max_retries": 2,
        "evidence_root": "evidence/ops/section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1",
        "evidence_version": "section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1",
        "expected_live_marker": "LIVE",
        "expected_demo_marker_absent": True,
        "owner_declared_host_allowlist": ["www.example-live-host.invalid"],
    }
    base.update(overrides)
    return base


def test_package_marker_and_defaults() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    assert default_authorization_is_false_v1() is True
    assert LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_AUTHORIZED_DEFAULT is False
    assert LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN is False
    assert LIVE_AUTHORIZED is False
    assert ENABLE_LIVE_TRADING is False
    assert FULLY_AUTONOMOUS_LIVE_TRADING_READY is False


def test_default_auth_false() -> None:
    assert LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_AUTHORIZED_DEFAULT is False


def test_missing_go() -> None:
    cfg = load_live_shadow_recon_config_v1(_valid_config())
    with pytest.raises(LiveShadowReconAuthorizationError, match="OWNER_GO_MISSING"):
        validate_live_shadow_with_exchange_reconciliation_authorization_v1(
            owner_go="",
            authorization_scope=AUTHORIZATION_SCOPE,
            bound_origin_main_sha=ORIGIN_SHA,
            expected_origin_main_sha=ORIGIN_SHA,
            bound_config_digest=cfg.digest(),
            expected_config_digest=cfg.digest(),
            live_shadow_with_exchange_reconciliation_authorized=True,
        )


def test_wrong_go() -> None:
    cfg = load_live_shadow_recon_config_v1(_valid_config())
    with pytest.raises(LiveShadowReconAuthorizationError, match="OWNER_GO_MISMATCH"):
        validate_live_shadow_with_exchange_reconciliation_authorization_v1(
            owner_go="OWNER_GO_LIVE_SHADOW",
            authorization_scope=AUTHORIZATION_SCOPE,
            bound_origin_main_sha=ORIGIN_SHA,
            expected_origin_main_sha=ORIGIN_SHA,
            bound_config_digest=cfg.digest(),
            expected_config_digest=cfg.digest(),
            live_shadow_with_exchange_reconciliation_authorized=True,
        )


def test_go_scope_mismatch() -> None:
    cfg = load_live_shadow_recon_config_v1(_valid_config())
    with pytest.raises(LiveShadowReconAuthorizationError, match="AUTHORIZATION_SCOPE_MISMATCH"):
        validate_live_shadow_with_exchange_reconciliation_authorization_v1(
            owner_go=OWNER_GO_EXECUTE,
            authorization_scope="LIVE_AUTHORIZED",
            bound_origin_main_sha=ORIGIN_SHA,
            expected_origin_main_sha=ORIGIN_SHA,
            bound_config_digest=cfg.digest(),
            expected_config_digest=cfg.digest(),
            live_shadow_with_exchange_reconciliation_authorized=True,
        )


def test_sha_config_mismatch() -> None:
    cfg = load_live_shadow_recon_config_v1(_valid_config())
    with pytest.raises(LiveShadowReconAuthorizationError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        validate_live_shadow_with_exchange_reconciliation_authorization_v1(
            owner_go=OWNER_GO_EXECUTE,
            authorization_scope=AUTHORIZATION_SCOPE,
            bound_origin_main_sha=ORIGIN_SHA,
            expected_origin_main_sha="deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            bound_config_digest=cfg.digest(),
            expected_config_digest=cfg.digest(),
            live_shadow_with_exchange_reconciliation_authorized=True,
        )
    with pytest.raises(LiveShadowReconAuthorizationError, match="CONFIG_DIGEST_MISMATCH"):
        validate_live_shadow_with_exchange_reconciliation_authorization_v1(
            owner_go=OWNER_GO_EXECUTE,
            authorization_scope=AUTHORIZATION_SCOPE,
            bound_origin_main_sha=ORIGIN_SHA,
            expected_origin_main_sha=ORIGIN_SHA,
            bound_config_digest=cfg.digest(),
            expected_config_digest="0" * 64,
            live_shadow_with_exchange_reconciliation_authorized=True,
        )


def test_missing_live_venue_binding() -> None:
    with pytest.raises(LiveShadowReconBindingError, match="VENUE_REQUIRED"):
        build_live_shadow_recon_venue_binding_v1(
            environment="LIVE",
            venue="",
            entity="e",
            region="r",
            rest_host="www.example-live-host.invalid",
            account_scope="a",
        )


def test_demo_venue_in_live_runner() -> None:
    with pytest.raises(LiveShadowReconRunnerError, match="ENVIRONMENT_MUST_BE_LIVE|FAIL_CLOSED"):
        run_section_11_13_3_live_shadow_with_exchange_reconciliation_v1(
            mode="preflight",
            config_payload=_valid_config(environment="DEMO"),
            origin_main_sha=ORIGIN_SHA,
        )


def test_testnet_credentials_in_live_runner() -> None:
    with pytest.raises(LiveShadowReconRunnerError, match="FORBIDDEN_CREDENTIAL_CLASS|CREDENTIAL"):
        run_section_11_13_3_live_shadow_with_exchange_reconciliation_v1(
            mode="preflight",
            config_payload=_valid_config(credential_class="OKX_DEMO_TRADING_API_KEY_ONLY"),
            origin_main_sha=ORIGIN_SHA,
        )


def test_live_credentials_in_demo_testnet_path() -> None:
    with pytest.raises(LiveShadowReconSecretRefError, match="CROSS_BIND_LIVE_REF_TO_DEMO"):
        reject_cross_environment_secretref_use_v1(
            secretref_uri="secretref://vault/peak-trade/live-shadow-recon/owner",
            requested_environment="DEMO",
        )
    with pytest.raises(LiveShadowReconSecretRefError, match="CROSS_BIND_LIVE_REF_TO_DEMO"):
        reject_cross_environment_secretref_use_v1(
            secretref_uri="secretref://vault/peak-trade/live-shadow-recon/owner",
            requested_environment="TESTNET",
        )


def test_missing_secretref() -> None:
    with pytest.raises(LiveShadowReconConfigError, match="MISSING:.*secretref"):
        require_execute_time_fields_v1(
            load_live_shadow_recon_config_v1(_valid_config(secretref_uri=""))
        )


def test_wrong_credential_class() -> None:
    with pytest.raises(LiveShadowReconSecretRefError, match="LIVE_SHADOW_RECON_CREDENTIAL_CLASS"):
        build_live_shadow_recon_secretref_metadata_v1(
            secretref_uri="secretref://vault/peak-trade/live-shadow-recon/x",
            credential_class="LIVE_TRADING_API_KEY",
        )


def test_wrong_host() -> None:
    binding = build_live_shadow_recon_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    client = LiveShadowReconHttpClientV1(
        binding=binding,
        transport=RecordingFakeTransportV1(),
    )
    # Force host mismatch by mutating binding base via alternate client construction.
    bad_binding = build_live_shadow_recon_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.other-live-host.invalid",
        account_scope="a",
    )
    with pytest.raises(LiveShadowReconHttpError, match="HOST_MISMATCH"):
        # Build request against other host by temporarily swapping.
        from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.http_client_v1 import (
            assert_host_matches_binding_v1,
        )

        assert_host_matches_binding_v1(binding=binding, request_host=bad_binding.rest_host)


def test_demo_simulation_header_present() -> None:
    binding = build_live_shadow_recon_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    client = LiveShadowReconHttpClientV1(binding=binding, transport=RecordingFakeTransportV1())
    with pytest.raises(LiveShadowReconHttpError, match="DEMO_SIMULATION_HEADER"):
        client.get(
            endpoint="/api/v5/account/balance",
            headers={"x-simulated-trading": "1"},
        )


def test_get_allowlisted_endpoint_pass() -> None:
    binding = build_live_shadow_recon_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    transport = RecordingFakeTransportV1()
    client = LiveShadowReconHttpClientV1(binding=binding, transport=transport)
    resp = client.get(endpoint="/api/v5/account/balance")
    assert resp.status_code == 200
    assert transport.calls[0].method == "GET"


def test_post_hard_block_before_transport() -> None:
    binding = build_live_shadow_recon_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    transport = RecordingFakeTransportV1()
    client = LiveShadowReconHttpClientV1(binding=binding, transport=transport)
    with pytest.raises(LiveShadowReconHttpError, match="HTTP_METHOD_HARD_BLOCK"):
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
    binding = build_live_shadow_recon_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    client = LiveShadowReconHttpClientV1(binding=binding, transport=RecordingFakeTransportV1())
    with pytest.raises(LiveShadowReconHttpError, match="MUTATION_ENDPOINT|NOT_ALLOWLISTED"):
        client.get(endpoint=endpoint)


def test_endpoint_not_allowlisted() -> None:
    binding = build_live_shadow_recon_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    client = LiveShadowReconHttpClientV1(binding=binding, transport=RecordingFakeTransportV1())
    with pytest.raises(LiveShadowReconHttpError, match="ENDPOINT_NOT_ALLOWLISTED"):
        client.get(endpoint="/api/v5/account/bills")


def test_retry_bounded_and_timeout() -> None:
    binding = build_live_shadow_recon_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    transport = RecordingFakeTransportV1(raise_timeout=True)
    client = LiveShadowReconHttpClientV1(
        binding=binding, transport=transport, max_retries=1, timeout_seconds=1.0
    )
    with pytest.raises(LiveShadowReconHttpError, match="TIMEOUT"):
        client.get(endpoint="/api/v5/account/balance")


@pytest.mark.parametrize("status", [401, 403])
def test_http_401_403_not_proven(status: int) -> None:
    binding = build_live_shadow_recon_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    transport = RecordingFakeTransportV1(status_code=status, body=b'{"msg":"denied"}')
    client = LiveShadowReconHttpClientV1(binding=binding, transport=transport)
    resp = client.get(endpoint="/api/v5/account/balance")
    with pytest.raises(LiveShadowReconAssertionError, match="AUTH_FAIL_NOT_PROVEN"):
        assert_authenticated_private_read_success_v1(
            response=resp,
            transport_class="LIVE_PRODUCTIVE_HTTP",
            venue_live_contact=True,
        )


def test_malformed_response() -> None:
    binding = build_live_shadow_recon_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    transport = RecordingFakeTransportV1(body=b"not-json")
    client = LiveShadowReconHttpClientV1(binding=binding, transport=transport)
    resp = client.get(endpoint="/api/v5/account/balance")
    with pytest.raises(LiveShadowReconAssertionError, match="MALFORMED_NON_JSON"):
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
    assert result.LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN is False
    verified = verify_live_shadow_with_exchange_reconciliation_evidence_v1(tmp_path / "run1")
    assert verified["MANIFEST_VERIFY_RC"] == 0
    assert verified["LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN"] is False
    claims = json.loads((tmp_path / "run1" / "claims.json").read_text(encoding="utf-8"))
    with pytest.raises(LiveShadowReconVerifierError, match="FIXTURE_CANNOT_SET_LIVE_PROVEN"):
        refuse_fixture_proven_claim_v1(
            {**claims, "LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN": True}
        )


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
        fixture_or_demo_or_testnet=False,
        productive_live_transport=True,
        mode="execute",
    )
    assert claims["LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN"] is True
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
    )
    assert fixture_claims["LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN"] is False


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
    assert cap_11_7.LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_ACTIVATED is False
    assert cap_11_7.LIVE_SHADOW_RECONCILIATION_ACTIVATED is False
    assert cap_11_7.NETWORK_SESSION_ALLOWED is False


def test_selector_governance_next_step_behavior() -> None:
    assert CANONICAL_NEXT_STEP_AFTER_PREPARATION_MERGE == OWNER_GO_EXECUTE
    assert "LIVE_DRY_RUN_ORDER_PLAN" in CANONICAL_NEXT_STEP_AFTER_PROVEN


def test_preflight_zero_network_and_no_credential_before_auth(tmp_path: Path) -> None:
    # Missing GO / auth false: still no credential material, no network.
    with pytest.raises(LiveShadowReconRunnerError):
        run_section_11_13_3_live_shadow_with_exchange_reconciliation_v1(
            mode="execute",
            config_payload=_valid_config(),
            origin_main_sha=ORIGIN_SHA,
            live_shadow_with_exchange_reconciliation_authorized=False,
            owner_go=OWNER_GO_EXECUTE,
        )
    result = run_section_11_13_3_live_shadow_with_exchange_reconciliation_v1(
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
    with pytest.raises(LiveShadowReconBindingError, match="CROSS_BINDING"):
        reject_cross_binding_v1(
            live_environment="LIVE",
            peer_environment="DEMO",
            live_credential_class=REQUIRED_CREDENTIAL_CLASS,
            peer_credential_class="OKX_DEMO_TRADING_API_KEY_ONLY",
        )


def test_demo_secretref_rejected_for_live() -> None:
    with pytest.raises(LiveShadowReconSecretRefError, match="CROSS_BIND_DEMO_TESTNET_REF"):
        reject_cross_environment_secretref_use_v1(
            secretref_uri="secretref://vault/peak-trade/demo/okx",
            requested_environment="LIVE",
        )


def test_owner_input_contract_has_no_invented_values() -> None:
    contract = build_owner_execute_input_contract_v1()
    assert contract["LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN"] is False
    for field in contract["fields"]:
        if field["id"] in {"permission_attestation", "separate_execute_go"}:
            continue
        assert field["value"] is None


def test_auth_false_blocks_execute() -> None:
    with pytest.raises(LiveShadowReconRunnerError, match="AUTHORIZED_FALSE|OWNER_GO"):
        run_section_11_13_3_live_shadow_with_exchange_reconciliation_v1(
            mode="execute",
            config_payload=_valid_config(),
            origin_main_sha=ORIGIN_SHA,
            live_shadow_with_exchange_reconciliation_authorized=False,
            owner_go=OWNER_GO_EXECUTE,
            transport=RecordingFakeTransportV1(),
        )


def test_forbidden_host_marker() -> None:
    with pytest.raises(LiveShadowReconBindingError, match="FORBIDDEN_NON_LIVE_HOST"):
        build_live_shadow_recon_venue_binding_v1(
            environment="LIVE",
            venue="v",
            entity="e",
            region="r",
            rest_host="demo-futures.kraken.com",
            account_scope="a",
        )


def test_reconciliation_match_and_divergence_policy() -> None:
    from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.reconciliation_v1 import (
        LiveShadowReconReconciliationError,
        build_matched_local_and_exchange_fixture_v1,
        evaluate_live_shadow_exchange_reconciliation_v1,
        refuse_automatic_stage_promotion_v1,
        refuse_live_order_side_effect_v1,
        refuse_silent_local_history_overwrite_v1,
    )

    local, exchange = build_matched_local_and_exchange_fixture_v1()
    matched = evaluate_live_shadow_exchange_reconciliation_v1(
        local_expected_state=local,
        exchange_snapshot=exchange,
    )
    assert matched.all_layers_match is True
    assert matched.order_effect == "NONE"
    assert matched.account_mutation_effect == "NONE"

    divergent_exchange = dict(exchange)
    divergent_exchange["positions"] = {"status": "open", "digest": "exchange-only"}
    halted = evaluate_live_shadow_exchange_reconciliation_v1(
        local_expected_state=local,
        exchange_snapshot=divergent_exchange,
    )
    assert halted.all_layers_match is False
    assert halted.blocks_new_entry is True

    adopted = evaluate_live_shadow_exchange_reconciliation_v1(
        local_expected_state=local,
        exchange_snapshot=divergent_exchange,
        exchange_truth_adoption_policy_id="policy-explicit-live-shadow-v1",
    )
    assert any(r.outcome == "SAFE_ADOPT_EXCHANGE_TRUTH" for r in adopted.layers)

    with pytest.raises(LiveShadowReconReconciliationError, match="SILENT_LOCAL_HISTORY"):
        refuse_silent_local_history_overwrite_v1(attempted_overwrite_of="decision_history")
    with pytest.raises(LiveShadowReconReconciliationError, match="AUTOMATIC_STAGE_PROMOTION"):
        refuse_automatic_stage_promotion_v1(claimed_target_stage="LIVE_DRY_RUN_ORDER_PLAN")
    with pytest.raises(LiveShadowReconReconciliationError, match="LIVE_ORDER_SIDE_EFFECT"):
        refuse_live_order_side_effect_v1(claimed_action="submit_order")


def test_orders_pending_get_not_mutation_blocked() -> None:
    binding = build_live_shadow_recon_venue_binding_v1(
        environment="LIVE",
        venue="v",
        entity="e",
        region="r",
        rest_host="www.example-live-host.invalid",
        account_scope="a",
    )
    client = LiveShadowReconHttpClientV1(
        binding=binding,
        transport=RecordingFakeTransportV1(),
        max_request_count=4,
    )
    resp = client.get(endpoint="/api/v5/trade/orders-pending")
    assert resp.status_code == 200
    assert client.counters.order_request_count == 0
    assert client.counters.write_request_count == 0
