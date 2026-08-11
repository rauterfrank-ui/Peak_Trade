"""Focused suite for §11.13.4 LIVE_DRY_RUN_ORDER_PLAN."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.capability_11_8_live_dry_run_order_plan_parity_v1 import (
    constants_v1 as cap_11_8,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.authorization_v1 import (
    LiveDryRunOrderPlanAuthorizationError,
    default_authorization_is_false_v1,
    validate_live_dry_run_order_plan_authorization_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.config_v1 import (
    LiveDryRunOrderPlanConfigError,
    load_live_dry_run_order_plan_config_v1,
    require_execute_time_fields_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    LIVE_AUTHORIZED,
    LIVE_DRY_RUN_ORDER_PLAN_AUTHORIZED_DEFAULT,
    LIVE_DRY_RUN_ORDER_PLAN_PROVEN,
    OWNER_GO_EXECUTE,
    PACKAGE_MARKER,
    PRODUCTIVE_EXECUTE_PATH_READY,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.http_client_v1 import (
    LiveDryRunOrderPlanHttpError,
    ProductiveProofFakeTransportV1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.mutation_boundary_v1 import (
    LiveDryRunOrderPlanMutationBoundaryError,
    refuse_order_submit_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.order_plan_v1 import (
    build_live_dry_run_order_plan_record_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.runner_v1 import (
    LiveDryRunOrderPlanRunnerError,
    run_execute_with_injected_transport_for_tests_v1,
    run_section_11_13_4_live_dry_run_order_plan_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.secretref_v1 import (
    LiveDryRunOrderPlanSecretRefError,
    build_live_dry_run_order_plan_secretref_metadata_v1,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.verifier_v1 import (
    verify_live_dry_run_order_plan_evidence_v1,
)

ORIGIN_SHA = "7856761f1d3cdb7ea1eeb3d172393f2abeac72b4"


def _valid_config(**overrides: object) -> dict:
    base = {
        "environment": "LIVE",
        "venue": "OKX",
        "entity": "OKX Europe Limited",
        "region": "EEA/DE",
        "rest_host": "www.example-live-host.invalid",
        "rest_base": "https://www.example-live-host.invalid",
        "account_scope": "acct-owner-binding",
        "instrument_id": "BTC-USDT-SWAP",
        "side": "BUY",
        "order_type": "LIMIT",
        "quantity": "1",
        "secretref_uri": "secretref://vault/peak-trade/live-dry-run-order-plan/okx",
        "credential_class": "LIVE_DRY_RUN_ORDER_PLAN_READ_ONLY_API_KEY",
        "method_allowlist": ["GET"],
        "endpoint_allowlist": [
            "/api/v5/account/balance",
            "/api/v5/account/config",
            "/api/v5/account/positions",
            "/api/v5/trade/orders-pending",
            "/api/v5/market/ticker",
        ],
        "max_request_count": 5,
        "timeout_seconds": 10.0,
        "max_retries": 2,
        "evidence_root": "evidence/ops/section_11_13_4_live_dry_run_order_plan_proven_v1",
        "evidence_version": "section_11_13_4_live_dry_run_order_plan_proven_v1",
        "expected_live_marker": "LIVE",
        "expected_demo_marker_absent": True,
        "owner_declared_host_allowlist": ["www.example-live-host.invalid"],
        "config_version": "section_11_13_4_live_dry_run_order_plan_config.v1",
        "schema_version": "section_11_13_4_live_dry_run_order_plan.v1",
        "predecessor_shadow_evidence_root": (
            "evidence/ops/section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1/"
            "20260811T211828Z/"
        ),
    }
    base.update(overrides)
    return base


def test_package_defaults_and_cap_11_8_remain_fixture_only() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    assert LIVE_AUTHORIZED is False
    assert LIVE_DRY_RUN_ORDER_PLAN_PROVEN is False
    assert LIVE_DRY_RUN_ORDER_PLAN_AUTHORIZED_DEFAULT is False
    assert default_authorization_is_false_v1() is True
    assert PRODUCTIVE_EXECUTE_PATH_READY is True
    assert cap_11_8.LIVE_DRY_RUN_ORDER_PLAN_ACTIVATED is False


def test_authorization_rejects_wrong_go_and_scope() -> None:
    cfg = load_live_dry_run_order_plan_config_v1(_valid_config())
    digest = cfg.digest()
    with pytest.raises(LiveDryRunOrderPlanAuthorizationError, match="OWNER_GO_MISMATCH"):
        validate_live_dry_run_order_plan_authorization_v1(
            owner_go="OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
            authorization_scope=AUTHORIZATION_SCOPE,
            bound_origin_main_sha=ORIGIN_SHA,
            expected_origin_main_sha=ORIGIN_SHA,
            bound_config_digest=digest,
            expected_config_digest=digest,
            live_dry_run_order_plan_authorized=True,
        )
    with pytest.raises(LiveDryRunOrderPlanAuthorizationError, match="SCOPE_MISMATCH"):
        validate_live_dry_run_order_plan_authorization_v1(
            owner_go=OWNER_GO_EXECUTE,
            authorization_scope="LIVE_AUTHORIZED",
            bound_origin_main_sha=ORIGIN_SHA,
            expected_origin_main_sha=ORIGIN_SHA,
            bound_config_digest=digest,
            expected_config_digest=digest,
            live_dry_run_order_plan_authorized=True,
        )


def test_secretref_requires_dry_run_path_marker() -> None:
    with pytest.raises(LiveDryRunOrderPlanSecretRefError, match="DRY_RUN_PATH"):
        build_live_dry_run_order_plan_secretref_metadata_v1(
            secretref_uri="secretref://vault/peak-trade/live-shadow-recon/okx",
            credential_class="LIVE_DRY_RUN_ORDER_PLAN_READ_ONLY_API_KEY",
        )


def test_mutation_boundary_blocks_submit() -> None:
    with pytest.raises(LiveDryRunOrderPlanMutationBoundaryError, match="ORDER_SUBMIT"):
        refuse_order_submit_v1(claimed_action="unit_test")


def test_order_plan_blocked_by_divergence() -> None:
    plan = build_live_dry_run_order_plan_record_v1(
        venue="OKX",
        entity="OKX Europe Limited",
        region="EEA/DE",
        rest_host="eea.okx.com",
        account_scope="acct",
        instrument_id="BTC-USDT-SWAP",
        side="BUY",
        order_type="LIMIT",
        quantity="1",
        td_mode="cross",
        fee_bps_assumption="2.0",
        slippage_bps_assumption="5.0",
        reference_price="100000",
        pricing_basis="UNIT_TEST",
        balance_payload={"data": [{"totalEq": "10", "availEq": "10"}]},
        positions_payload={"data": []},
        reconciliation={
            "BLOCKS_NEW_ENTRY": True,
            "LIVE_RECONCILIATION_PROVEN": False,
            "UNRESOLVED_ECONOMIC_DIVERGENCE": True,
            "ALL_LAYERS_MATCH": False,
            "layers": [],
        },
        intent_id="intent-u",
        order_plan_id="plan-u",
        client_order_id="pt-coid-u",
        min_notional_usdt_assumption="5.0",
    )
    assert plan.execution_eligibility == "BLOCKED_NO_EXECUTE"
    assert plan.submitted is False
    assert plan.venue_native_dry_run_payload["submit"] is False
    assert "BLOCKS_NEW_ENTRY=true" in plan.execution_block_reasons
    assert "LIVE_RECONCILIATION_PROVEN=false" in plan.execution_block_reasons


def test_preflight_no_network(tmp_path: Path) -> None:
    result = run_section_11_13_4_live_dry_run_order_plan_v1(
        mode="preflight",
        config_payload=_valid_config(),
        origin_main_sha=ORIGIN_SHA,
        evidence_run_root=tmp_path / "preflight",
    )
    assert result.ok is True
    assert result.LIVE_DRY_RUN_ORDER_PLAN_PROVEN is False
    assert result.NETWORK_EFFECT == "NONE"
    assert result.CREDENTIAL_ACCESS == "NONE"
    assert result.ORDER_EFFECT == "NONE"


def test_execute_injected_transport_builds_blocked_plan(tmp_path: Path) -> None:
    vault = tmp_path / "vault.json"
    material = json.dumps(
        {"api_key": "k", "api_secret": "s", "passphrase": "p"},
        separators=(",", ":"),
    )
    vault.write_text(
        json.dumps(
            {"secretref://vault/peak-trade/live-dry-run-order-plan/okx": material},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    bodies = {
        "/api/v5/account/config": json.dumps(
            {"code": "0", "data": [{"uid": "acct-owner-binding"}]}
        ).encode(),
        "/api/v5/account/balance": json.dumps(
            {"code": "0", "data": [{"totalEq": "12.5", "availEq": "12.5"}]}
        ).encode(),
        "/api/v5/account/positions": json.dumps({"code": "0", "data": []}).encode(),
        "/api/v5/trade/orders-pending": json.dumps({"code": "0", "data": []}).encode(),
        "/api/v5/market/ticker?instId=BTC-USDT-SWAP": json.dumps(
            {"code": "0", "data": [{"instId": "BTC-USDT-SWAP", "last": "100000"}]}
        ).encode(),
    }
    transport = ProductiveProofFakeTransportV1(bodies_by_endpoint=bodies)
    evidence = tmp_path / "evidence"
    result = run_execute_with_injected_transport_for_tests_v1(
        config_payload=_valid_config(),
        origin_main_sha=ORIGIN_SHA,
        transport=transport,
        evidence_run_root=evidence,
        vault_file=vault,
    )
    assert result.ok is True
    assert result.ORDER_EFFECT == "NONE"
    assert result.ORDER_PLAN_RESULT == "BLOCKED_NO_EXECUTE"
    assert result.LIVE_AUTHORIZED is False
    # Injected transport with allows_productive_proven may claim proven for unit path.
    verify = verify_live_dry_run_order_plan_evidence_v1(evidence)
    assert verify["ok"] is True
    assert verify["LIVE_RECONCILIATION_PROVEN"] is False
    assert verify["BLOCKS_NEW_ENTRY"] is True
    plan = json.loads((evidence / "ORDER_PLAN.json").read_text(encoding="utf-8"))
    assert plan["submitted"] is False
    assert plan["execution_eligibility"] == "BLOCKED_NO_EXECUTE"


def test_post_hard_blocked_on_client() -> None:
    from src.ops.section_11_13_4_live_dry_run_order_plan_v1.binding_v1 import (
        build_live_dry_run_order_plan_venue_binding_v1,
    )
    from src.ops.section_11_13_4_live_dry_run_order_plan_v1.http_client_v1 import (
        LiveDryRunOrderPlanHttpClientV1,
        RecordingFakeTransportV1,
    )

    binding = build_live_dry_run_order_plan_venue_binding_v1(
        environment="LIVE",
        venue="OKX",
        entity="OKX Europe Limited",
        region="EEA/DE",
        rest_host="www.example-live-host.invalid",
        rest_base="https://www.example-live-host.invalid",
        account_scope="acct",
        instrument_scope="BTC-USDT-SWAP",
        owner_declared_host_allowlist=("www.example-live-host.invalid",),
    )
    client = LiveDryRunOrderPlanHttpClientV1(
        binding=binding,
        transport=RecordingFakeTransportV1(),
    )
    with pytest.raises(LiveDryRunOrderPlanHttpError, match="HTTP_METHOD_HARD_BLOCK"):
        client.post(endpoint="/api/v5/trade/order")


def test_config_rejects_post_method_allowlist() -> None:
    with pytest.raises(LiveDryRunOrderPlanConfigError, match="METHOD_ALLOWLIST"):
        load_live_dry_run_order_plan_config_v1(_valid_config(method_allowlist=["GET", "POST"]))


def test_missing_execute_fields_fail_closed() -> None:
    cfg = load_live_dry_run_order_plan_config_v1(_valid_config(venue=""))
    with pytest.raises(LiveDryRunOrderPlanConfigError, match="EXECUTE_TIME_FIELDS_MISSING"):
        require_execute_time_fields_v1(cfg)


def test_execute_without_auth_fails() -> None:
    with pytest.raises(LiveDryRunOrderPlanRunnerError, match="AUTHORIZED_FALSE|OWNER_GO"):
        run_section_11_13_4_live_dry_run_order_plan_v1(
            mode="execute",
            config_payload=_valid_config(),
            origin_main_sha=ORIGIN_SHA,
            live_dry_run_order_plan_authorized=False,
            allow_real_transport=True,
            evidence_run_root="/tmp/unused",
            vault_file="/tmp/unused",
        )
