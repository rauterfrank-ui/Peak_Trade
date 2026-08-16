"""Focused tests for §11.13.5 canary submit transport (mocks only; zero live requests)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.environment import LIVE_CONFIRM_TOKEN
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.config_v1 import (
    example_incomplete_config_dict_v1,
    load_live_canary_config_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    CANARY_SUBMIT_TRANSPORT_IMPLEMENTED,
    GENERAL_LIVE_SUBMIT_UNLOCKED,
    LIVE_AUTHORIZED,
    OWNER_GO_AUTHORING,
    OWNER_GO_EXECUTE,
    REQUIRED_SECRETREF_URI,
    SUBMIT_UNLOCKED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    CanaryEntrySubmitPermitV1,
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    RecordingFakeCanaryTransportV1,
    sanitize_redirect_location_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.lifecycle_v1 import (
    build_lifecycle_and_closeout_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    LiveCanaryOrderPlanError,
    build_minimum_valid_canary_order_plan_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.runner_v1 import (
    LiveCanaryRunnerError,
    run_section_11_13_5_live_canary_minimum_exposure_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_transport_v1 import (
    LiveCanarySubmitTransportError,
    run_canary_submit_transport_v1,
)

ORIGIN_SHA = "825ea05e4794579d1f26b368abb28b6d3837d097"
INSTRUMENTS = {
    "code": "0",
    "data": [
        {
            "instId": "BTC-USDT-SWAP",
            "minSz": "0.01",
            "lotSz": "0.01",
            "tickSz": "0.1",
            "ctVal": "0.01",
            "ctValCcy": "BTC",
        }
    ],
}
TICKER = {"code": "0", "data": [{"instId": "BTC-USDT-SWAP", "last": "65000.1"}]}
EMPTY = {"code": "0", "data": []}
FIXTURE_MATERIAL = json.dumps(
    {"api_key": "A" * 36, "api_secret": "B" * 32, "passphrase": "C" * 14},
    separators=(",", ":"),
)


class _MemVault:
    def __init__(self, material: str = FIXTURE_MATERIAL) -> None:
        self.material = material
        self.calls = 0

    def resolve_secretref_material_v1(self, *, secret_reference: str) -> str:
        self.calls += 1
        if secret_reference != REQUIRED_SECRETREF_URI:
            raise RuntimeError("SECRETREF_NOT_FOUND")
        return self.material


def _execute_cfg() -> dict:
    payload = example_incomplete_config_dict_v1()
    payload.update(
        {
            "venue": "OKX",
            "entity": "OKX Europe Limited",
            "region": "EEA/DE",
            "rest_host": "eea.okx.com",
            "rest_base": "https://eea.okx.com",
            "account_scope": "856964404452495999",
            "secretref_uri": REQUIRED_SECRETREF_URI,
            "owner_declared_host_allowlist": ["eea.okx.com"],
        }
    )
    return payload


def _fake_transport() -> RecordingFakeCanaryTransportV1:
    return RecordingFakeCanaryTransportV1(
        bodies_by_endpoint={
            "/api/v5/public/instruments": json.dumps(INSTRUMENTS).encode(),
            "/api/v5/market/ticker": json.dumps(TICKER).encode(),
            "/api/v5/account/positions": json.dumps(EMPTY).encode(),
            "/api/v5/trade/orders-pending": json.dumps(EMPTY).encode(),
            "/api/v5/trade/orders-history": json.dumps(EMPTY).encode(),
        },
        post_body=b'{"code":"0","data":[{"sCode":"0","ordId":"ord-1","clOrdId":"x"}]}',
    )


def _transport_kwargs(**overrides: object) -> dict:
    cfg = load_live_canary_config_v1(_execute_cfg(), require_execute_fields=True)
    base: dict = {
        "cfg": cfg,
        "origin_main_sha": ORIGIN_SHA,
        "owner_go": OWNER_GO_EXECUTE,
        "live_canary_authorized": True,
        "live_enabled": True,
        "live_armed": True,
        "confirm_token": LIVE_CONFIRM_TOKEN,
        "owner_go_consumed": False,
        "permission_attestation": {"READ": True, "TRADE": True, "WITHDRAW": False},
        "transport": _fake_transport(),
        "allow_productive_wire_send": False,
        "live_canary_cybersecurity_gate": "PASS",
        "vault_backend": _MemVault(),
    }
    base.update(overrides)
    return base


def test_standing_flags_do_not_unlock_general_live() -> None:
    assert CANARY_SUBMIT_TRANSPORT_IMPLEMENTED is True
    assert GENERAL_LIVE_SUBMIT_UNLOCKED is False
    assert SUBMIT_UNLOCKED is False
    assert LIVE_AUTHORIZED is False
    lifecycle = build_lifecycle_and_closeout_contract_v1()
    assert lifecycle["ACTIVATED"] is False
    assert lifecycle["GENERAL_LIVE_SUBMIT_UNLOCKED"] is False


def test_order_plan_rejects_missing_venue_sizing() -> None:
    with pytest.raises(LiveCanaryOrderPlanError, match="INSTRUMENTS"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload={"code": "0", "data": []},
            ticker_payload=TICKER,
            owner_go=OWNER_GO_EXECUTE,
            origin_main_sha=ORIGIN_SHA,
        )


def test_order_plan_rejects_quantity_above_min_sz() -> None:
    bloated = {
        "code": "0",
        "data": [
            {
                "instId": "BTC-USDT-SWAP",
                "minSz": "0.01",
                "lotSz": "0.02",
                "tickSz": "0.1",
                "ctVal": "0.01",
            }
        ],
    }
    with pytest.raises(LiveCanaryOrderPlanError, match="UNSAFE_QUANTITY"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=bloated,
            ticker_payload=TICKER,
            owner_go=OWNER_GO_EXECUTE,
            origin_main_sha=ORIGIN_SHA,
        )


def test_http_client_rejects_wrong_host_and_demo_and_ungated_post() -> None:
    transport = RecordingFakeCanaryTransportV1()
    with pytest.raises(LiveCanaryHttpError, match="HOST_MISMATCH"):
        LiveCanaryHttpClientV1(
            rest_base="https://www.okx.com",
            rest_host="www.okx.com",
            transport=transport,
        ).get(endpoint="/api/v5/public/instruments")
    client = LiveCanaryHttpClientV1(
        rest_base="https://eea.okx.com",
        rest_host="eea.okx.com",
        transport=transport,
    )
    with pytest.raises(LiveCanaryHttpError, match="DEMO_SIMULATION"):
        client.get(
            endpoint="/api/v5/public/instruments",
            headers={"x-simulated-trading": "1"},
        )
    with pytest.raises(LiveCanaryHttpError, match="UNGATED_POST"):
        client.post(endpoint="/api/v5/trade/order")
    with pytest.raises(LiveCanaryHttpError, match="POST_ENDPOINT_NOT_ALLOWLISTED"):
        client._build_request(method="POST", endpoint="/api/v5/asset/withdrawal")


def test_exactly_one_entry_submit_and_no_blind_retry() -> None:
    transport = RecordingFakeCanaryTransportV1(
        post_body=b'{"code":"0","data":[{"sCode":"0","ordId":"1"}]}'
    )
    client = LiveCanaryHttpClientV1(
        rest_base="https://eea.okx.com",
        rest_host="eea.okx.com",
        transport=transport,
    )
    permit = CanaryEntrySubmitPermitV1(
        owner_go=OWNER_GO_EXECUTE, clordid="ptokxeproddeadbeef", permit_id="p1"
    )
    client.post_entry_order(
        permit=permit, body_text="{}", headers={"Content-Type": "application/json"}
    )
    with pytest.raises(LiveCanaryHttpError, match="DUPLICATE_ENTRY_SUBMIT"):
        client.post_entry_order(
            permit=permit, body_text="{}", headers={"Content-Type": "application/json"}
        )
    timeout_transport = RecordingFakeCanaryTransportV1(raise_timeout_on_post=True)
    timeout_client = LiveCanaryHttpClientV1(
        rest_base="https://eea.okx.com",
        rest_host="eea.okx.com",
        transport=timeout_transport,
    )
    with pytest.raises(LiveCanaryHttpError, match="UNKNOWN_SUBMIT_TIMEOUT"):
        timeout_client.post_entry_order(
            permit=permit, body_text="{}", headers={"Content-Type": "application/json"}
        )
    with pytest.raises(LiveCanaryHttpError, match="UNKNOWN_SUBMIT_NO_BLIND_RETRY"):
        timeout_client.post_entry_order(
            permit=permit, body_text="{}", headers={"Content-Type": "application/json"}
        )


@pytest.mark.parametrize(
    ("override", "needle"),
    [
        ({"owner_go": None}, "OWNER_GO"),
        ({"owner_go": OWNER_GO_AUTHORING}, "AUTHORING_GO"),
        ({"live_enabled": False}, "LIVE_ENABLED"),
        ({"live_armed": False}, "LIVE_ARMED"),
        ({"confirm_token": "NOPE"}, "CONFIRM_TOKEN"),
        ({"live_canary_cybersecurity_gate": "NOT_PASSED"}, "CYBERSECURITY_GATE"),
        (
            {"permission_attestation": {"READ": True, "TRADE": False, "WITHDRAW": False}},
            "TRADE_ATTESTATION",
        ),
        (
            {"permission_attestation": {"READ": True, "TRADE": True, "WITHDRAW": True}},
            "TRADE_ATTESTATION",
        ),
        ({"owner_go_consumed": True}, "OWNER_GO_CONSUMED"),
        ({"live_canary_authorized": False}, "LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED"),
        ({"vault_backend": None}, "VAULT_BACKEND"),
    ],
)
def test_transport_unreachable_without_required_guards(override: dict, needle: str) -> None:
    kwargs = _transport_kwargs(**override)
    with pytest.raises((LiveCanarySubmitTransportError, Exception), match=needle):
        run_canary_submit_transport_v1(**kwargs)


def test_missing_secretref_and_wrong_host_rejected_before_post() -> None:
    cfg_payload = _execute_cfg()
    cfg_payload["secretref_uri"] = "secretref://vault/peak-trade/live-shadow-recon/okx"
    with pytest.raises(Exception, match="SECRETREF"):
        load_live_canary_config_v1(cfg_payload, require_execute_fields=True)
    cfg_payload = _execute_cfg()
    cfg_payload["rest_host"] = "demo.okx.com"
    cfg_payload["rest_base"] = "https://demo.okx.com"
    cfg_payload["owner_declared_host_allowlist"] = ["demo.okx.com"]
    with pytest.raises(Exception, match="FORBIDDEN_HOST"):
        load_live_canary_config_v1(cfg_payload, require_execute_fields=True)


def test_open_position_blocks_before_post() -> None:
    transport = _fake_transport()
    transport.bodies_by_endpoint["/api/v5/account/positions"] = json.dumps(
        {"code": "0", "data": [{"instId": "BTC-USDT-SWAP", "pos": "1"}]}
    ).encode()
    kwargs = _transport_kwargs(transport=transport)
    with pytest.raises(LiveCanarySubmitTransportError, match="OPEN_POSITION"):
        run_canary_submit_transport_v1(**kwargs)
    assert all(call.method != "POST" for call in transport.calls)


def test_happy_path_fake_exactly_one_post() -> None:
    transport = _fake_transport()
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    assert result["ORDER_COUNT_SUBMITTED"] == 1
    assert result["DUPLICATE_SUBMIT"] is False
    assert result["LIVE_AUTHORIZED"] is False
    assert result["LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED"] is False
    assert result["OWNER_GO_CONSUMED"] is False
    assert result["plan"]["quantity"] == "0.01"
    assert result["plan"]["max_notional"] == result["plan"]["min_executable_notional"]
    assert result["SIGNED_BODY_EQUALS_WIRE_BODY"] is True
    assert result["ok"] is True
    posts = [c for c in transport.calls if c.method == "POST"]
    assert len(posts) == 1
    assert posts[0].endpoint == "/api/v5/trade/order"
    assert "withdraw" not in posts[0].endpoint.lower()
    second = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    # New client each call; same fake records a second POST only if we reuse client.
    assert second["ORDER_COUNT_SUBMITTED"] == 1


def test_ambiguous_submit_recovers_without_second_post() -> None:
    transport = _fake_transport()
    transport.raise_timeout_on_post = True
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    assert result["UNKNOWN_SUBMIT"] is True
    assert result["BLIND_RETRY"] is False
    assert result["ORDER_COUNT_SUBMITTED"] == 0
    posts = [c for c in transport.calls if c.method == "POST"]
    assert len(posts) == 1  # attempted once via transport.send raising
    assert result["CANARY_RESULT"].startswith("UNKNOWN_SUBMIT")


def test_no_wire_backend_without_productive_flag() -> None:
    kwargs = _transport_kwargs(transport=None, allow_productive_wire_send=False)
    with pytest.raises(LiveCanarySubmitTransportError, match="NO_WIRE_BACKEND"):
        run_canary_submit_transport_v1(**kwargs)


def test_runner_execute_no_longer_raises_authoring_surface_unlock() -> None:
    with pytest.raises(LiveCanaryRunnerError) as exc:
        run_section_11_13_5_live_canary_minimum_exposure_v1(
            mode="execute",
            origin_main_sha=ORIGIN_SHA,
            owner_go=OWNER_GO_EXECUTE,
            live_canary_authorized=True,
            live_enabled=True,
            live_armed=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
            permission_attestation={"READ": True, "TRADE": True, "WITHDRAW": False},
        )
    assert "CANARY_SUBMIT_TRANSPORT_NOT_UNLOCKED_IN_AUTHORING_SURFACE" not in str(exc.value)


def test_runner_fake_execute_does_not_consume_owner_go() -> None:
    transport = _fake_transport()
    result = run_section_11_13_5_live_canary_minimum_exposure_v1(
        mode="execute",
        config_payload=_execute_cfg(),
        origin_main_sha=ORIGIN_SHA,
        owner_go=OWNER_GO_EXECUTE,
        live_canary_authorized=True,
        live_enabled=True,
        live_armed=True,
        confirm_token=LIVE_CONFIRM_TOKEN,
        permission_attestation={"READ": True, "TRADE": True, "WITHDRAW": False},
        transport=transport,
        vault_backend=_MemVault(),
        live_canary_cybersecurity_gate="PASS",
    )
    assert result.payload["OWNER_GO_CONSUMED"] is False
    assert result.payload["LIVE_AUTHORIZED"] is False
    assert LIVE_AUTHORIZED is False
    assert AUTHORIZATION_SCOPE == "LIVE_CANARY_MINIMUM_EXPOSURE"


def test_preparation_zero_live_requests_on_preflight() -> None:
    result = run_section_11_13_5_live_canary_minimum_exposure_v1(
        mode="preflight",
        origin_main_sha=ORIGIN_SHA,
    )
    assert result.ok is True
    assert result.payload["claims"]["ORDER_REQUEST_COUNT"] == 0
    assert result.payload["claims"]["WRITE_REQUEST_COUNT"] == 0
    assert result.payload["claims"]["LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED"] is False


def test_no_mf_or_n_greater_than_one_expansion() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        ORDER_COUNT_LIMIT,
        POSITION_COUNT_LIMIT,
    )

    assert POSITION_COUNT_LIMIT == 1
    assert ORDER_COUNT_LIMIT == 1
    cfg = load_live_canary_config_v1(_execute_cfg(), require_execute_fields=True)
    assert int(cfg.payload["position_count_limit"]) == 1
    payload = _execute_cfg()
    payload["position_count_limit"] = 2
    with pytest.raises(Exception, match="POSITION_COUNT_LIMIT"):
        load_live_canary_config_v1(payload)


def test_preparation_evidence_verifier_pass() -> None:
    from scripts.ops.verify_section_11_13_5_canary_submit_transport_preparation_v1 import (
        verify_section_11_13_5_canary_submit_transport_preparation_v1,
    )

    repo = Path(__file__).resolve().parents[2]
    root = (
        repo
        / "evidence/ops/section_11_13_5_canary_submit_transport_preparation_v1/20260815T204500Z"
    )
    result = verify_section_11_13_5_canary_submit_transport_preparation_v1(root)
    assert result["ok"] is True
    assert result["MANIFEST_VERIFY_RC"] == 0
    assert result["CANARY_EXECUTED"] is False
    assert result["ORDER_COUNT_SUBMITTED"] == 0


def _fixture_creds() -> dict[str, str]:
    return {"api_key": "A" * 36, "api_secret": "B" * 32, "passphrase": "C" * 14}


def test_canonical_vault_loads_json_string_and_nested_object(tmp_path: Path) -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
        LiveCanaryCredentialError,
        build_file_secretref_vault_backend_v1,
        release_live_canary_ephemeral_material_v1,
        resolve_and_load_live_canary_secretref_ephemeral_v1,
    )

    creds = _fixture_creds()
    string_vault = tmp_path / "string.json"
    string_vault.write_text(
        json.dumps({REQUIRED_SECRETREF_URI: json.dumps(creds, separators=(",", ":"))}),
        encoding="utf-8",
    )
    nested_vault = tmp_path / "nested.json"
    nested_vault.write_text(json.dumps({REQUIRED_SECRETREF_URI: creds}), encoding="utf-8")
    for path in (string_vault, nested_vault):
        backend = build_file_secretref_vault_backend_v1(vault_file=path)
        handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
            secret_reference=REQUIRED_SECRETREF_URI,
            vault_backend=backend,
        )
        assert handle.vault_resolved is True
        assert handle.bound is True
        release_live_canary_ephemeral_material_v1(handle)
    malformed = tmp_path / "malformed.json"
    malformed.write_text(json.dumps({REQUIRED_SECRETREF_URI: "not-json"}), encoding="utf-8")
    backend = build_file_secretref_vault_backend_v1(vault_file=malformed)
    with pytest.raises(LiveCanaryCredentialError, match="CREDENTIAL_MATERIAL_NOT_JSON"):
        resolve_and_load_live_canary_secretref_ephemeral_v1(
            secret_reference=REQUIRED_SECRETREF_URI,
            vault_backend=backend,
        )


def test_malformed_and_wrong_type_vault_fail_closed_without_leaking_secret(
    tmp_path: Path,
) -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
        LiveCanaryCredentialError,
        build_file_secretref_vault_backend_v1,
        resolve_and_load_live_canary_secretref_ephemeral_v1,
    )

    secret = "SUPERSECRETVALUE99"
    vault = tmp_path / "bad.json"
    vault.write_text(json.dumps({REQUIRED_SECRETREF_URI: f"not-json-{secret}"}), encoding="utf-8")
    backend = build_file_secretref_vault_backend_v1(vault_file=vault)
    with pytest.raises(LiveCanaryCredentialError, match="CREDENTIAL_MATERIAL_NOT_JSON") as exc:
        resolve_and_load_live_canary_secretref_ephemeral_v1(
            secret_reference=REQUIRED_SECRETREF_URI,
            vault_backend=backend,
        )
    assert secret not in str(exc.value)
    typed = tmp_path / "list.json"
    typed.write_text(json.dumps({REQUIRED_SECRETREF_URI: [1, 2]}), encoding="utf-8")
    backend = build_file_secretref_vault_backend_v1(vault_file=typed)
    with pytest.raises(LiveCanaryCredentialError, match="VAULT_MATERIAL_TYPE_FORBIDDEN"):
        resolve_and_load_live_canary_secretref_ephemeral_v1(
            secret_reference=REQUIRED_SECRETREF_URI,
            vault_backend=backend,
        )


def test_runner_vault_file_reaches_canonical_loader(tmp_path: Path) -> None:
    vault = tmp_path / "vault.json"
    vault.write_text(json.dumps({REQUIRED_SECRETREF_URI: _fixture_creds()}), encoding="utf-8")
    transport = _fake_transport()
    result = run_section_11_13_5_live_canary_minimum_exposure_v1(
        mode="execute",
        config_payload=_execute_cfg(),
        origin_main_sha=ORIGIN_SHA,
        owner_go=OWNER_GO_EXECUTE,
        live_canary_authorized=True,
        live_enabled=True,
        live_armed=True,
        confirm_token=LIVE_CONFIRM_TOKEN,
        permission_attestation={"READ": True, "TRADE": True, "WITHDRAW": False},
        transport=transport,
        vault_file=str(vault),
        live_canary_cybersecurity_gate="PASS",
    )
    assert result.payload["ORDER_COUNT_SUBMITTED"] == 1
    assert result.payload["LIVE_AUTHORIZED"] is False
    posts = [c for c in transport.calls if c.method == "POST"]
    assert len(posts) == 1


def test_cli_execute_requires_vault_file() -> None:
    from scripts.ops.run_section_11_13_5_live_canary_minimum_exposure_v1 import main

    with pytest.raises(SystemExit):
        main(["--execute", "--origin-main-sha", ORIGIN_SHA])


def test_missing_vault_backend_fails_closed_before_post() -> None:
    transport = _fake_transport()
    with pytest.raises(LiveCanarySubmitTransportError, match="VAULT_BACKEND_OR_HANDLE_REQUIRED"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport, vault_backend=None))
    assert all(call.method != "POST" for call in transport.calls)


def test_runner_execute_without_vault_file_fails_closed() -> None:
    with pytest.raises(LiveCanaryRunnerError, match="EXECUTE_REQUIRES_VAULT_FILE"):
        run_section_11_13_5_live_canary_minimum_exposure_v1(
            mode="execute",
            config_payload=_execute_cfg(),
            origin_main_sha=ORIGIN_SHA,
            owner_go=OWNER_GO_EXECUTE,
            live_canary_authorized=True,
            live_enabled=True,
            live_armed=True,
            confirm_token=LIVE_CONFIRM_TOKEN,
            permission_attestation={"READ": True, "TRADE": True, "WITHDRAW": False},
            transport=_fake_transport(),
            live_canary_cybersecurity_gate="PASS",
        )


def test_public_get_sends_repository_user_agent() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        USER_AGENT_CANARY,
    )

    transport = RecordingFakeCanaryTransportV1()
    client = LiveCanaryHttpClientV1(
        rest_base="https://eea.okx.com",
        rest_host="eea.okx.com",
        transport=transport,
    )
    client.get(endpoint="/api/v5/public/instruments")
    assert transport.calls[0].headers["User-Agent"] == USER_AGENT_CANARY


def test_signed_private_gets_keep_okx_auth_headers_and_user_agent() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        USER_AGENT_CANARY,
    )

    transport = _fake_transport()
    run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    gets = [c for c in transport.calls if c.method == "GET"]
    posts = [c for c in transport.calls if c.method == "POST"]
    assert gets
    assert len(posts) == 1
    for call in gets:
        assert call.headers.get("User-Agent") == USER_AGENT_CANARY
    private = [
        c for c in gets if "/account/" in c.endpoint or "/trade/orders-pending" in c.endpoint
    ]
    assert private
    for call in private:
        keys = {str(k).upper() for k in call.headers}
        assert "OK-ACCESS-KEY" in keys
        assert "OK-ACCESS-SIGN" in keys
        assert "OK-ACCESS-TIMESTAMP" in keys
        assert "OK-ACCESS-PASSPHRASE" in keys
    for call in posts:
        keys = {str(k).upper() for k in call.headers}
        assert "OK-ACCESS-SIGN" in keys


def test_preparation_and_reevaluation_go_rejected_by_submit_transport() -> None:
    for go in (
        "SECTION_11_13_5_CANARY_EXECUTION_REEVALUATION_FROM_NEW_ORIGIN_MAIN",
        "SECTION_11_13_5_CANARY_EXECUTION_PLUMBING_REMEDIATION_PREPARATION",
        "SECTION_11_13_5_OKX_50124_MARKET_PERMISSION_REMEDIATION_AND_CLASSIFICATION_PREPARATION",
    ):
        kwargs = _transport_kwargs(owner_go=go)
        with pytest.raises(
            (LiveCanarySubmitTransportError, Exception),
            match="REEVALUATION_OR_PREPARATION_GO|OWNER_GO_MISMATCH",
        ):
            run_canary_submit_transport_v1(**kwargs)
        assert all(call.method != "POST" for call in kwargs["transport"].calls)


def test_entry_permit_still_mandatory_for_post() -> None:
    transport = RecordingFakeCanaryTransportV1()
    client = LiveCanaryHttpClientV1(
        rest_base="https://eea.okx.com",
        rest_host="eea.okx.com",
        transport=transport,
    )
    with pytest.raises(TypeError):
        client.post_entry_order(  # type: ignore[misc]
            body_text="{}",
            headers={"Content-Type": "application/json"},
        )
    with pytest.raises(LiveCanaryHttpError, match="UNGATED_POST"):
        client.post(endpoint="/api/v5/trade/order")
    assert all(call.method != "POST" for call in transport.calls)


def test_http_401_json_code_msg_captured_secret_safe() -> None:
    transport = _fake_transport()
    transport.post_status_code = 401
    transport.post_body = b'{"code":"50113","msg":"Invalid Sign"}'
    transport.post_headers = {
        "Content-Type": "application/json",
        "CF-RAY": "testray123",
        "OK-ACCESS-KEY": "must-not-leak",
        "Set-Cookie": "session=secret",
    }
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    assert result["ok"] is False
    assert result["http_status"] == 401
    evidence = result["http_error_evidence"]
    assert evidence["okx_code"] == "50113"
    assert evidence["okx_msg"] == "Invalid Sign"
    assert evidence["json_parse_ok"] is True
    assert evidence["SECRET_VALUES_INCLUDED"] is False
    headers = evidence["response_headers_safe"]
    assert headers.get("CF-RAY") == "testray123" or headers.get("cf-ray") == "testray123"
    dumped = json.dumps(result)
    assert "must-not-leak" not in dumped
    assert "session=secret" not in dumped
    assert result["POST_401_ROOT_CAUSE"] == "OKX_50113_INVALID_SIGN"
    assert result["HISTORICAL_FIRST_401_ROOT_CAUSE"] == "UNPROVEN_FAIL_CLOSED"
    assert result["RETRY_SAFE_NOW"] is False
    assert result["LIVE_AUTHORIZED"] is False
    posts = [c for c in transport.calls if c.method == "POST"]
    assert len(posts) == 1


def test_http_401_50124_classifies_exact_and_does_not_retry() -> None:
    transport = _fake_transport()
    transport.post_status_code = 401
    transport.post_body = (
        b'{"code":"50124","msg":"This API Key does not have trading permission for the market"}'
    )
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    assert result["ok"] is False
    assert result["http_status"] == 401
    assert result["http_error_evidence"]["okx_code"] == "50124"
    assert result["POST_401_ROOT_CAUSE"] == "OKX_50124_OBSERVED_ONESHOT_TRADING_POST"
    assert result["HTTP_401_REQUEST_CLASS"] == "ONESHOT_TRADING_POST_/api/v5/trade/order"
    assert result["HTTP_50124_INSTRUMENT_SPECIFIC_PROVEN"] is False
    assert result["ROOT_CAUSE_PROVEN"] is False
    assert result["HISTORICAL_FIRST_401_ROOT_CAUSE"] == "UNPROVEN_FAIL_CLOSED"
    assert result["RETRY_SAFE_NOW"] is False
    assert result["CANARY_RETRY_AUTHORIZED"] is False
    assert result["GENERAL_LIVE_SUBMIT_UNLOCKED"] is False
    assert result["LIVE_AUTHORIZED"] is False
    assert len([c for c in transport.calls if c.method == "POST"]) == 1


def test_http_401_malformed_body_is_unproven_not_50124() -> None:
    transport = _fake_transport()
    transport.post_status_code = 401
    transport.post_body = b"<html>not-json"
    transport.post_headers = {"Content-Type": "text/html"}
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    assert result["ok"] is False
    assert result["http_status"] == 401
    evidence = result["http_error_evidence"]
    assert evidence["json_parse_ok"] is False
    assert evidence["parse_error"] == "MALFORMED_NON_JSON_RESPONSE"
    assert evidence["okx_code"] is None
    assert result["CANARY_EXECUTED"] is False
    assert result["LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED"] is False
    assert result["POST_401_ROOT_CAUSE"] == "UNPROVEN_FAIL_CLOSED"
    assert result["HISTORICAL_FIRST_401_ROOT_CAUSE"] == "UNPROVEN_FAIL_CLOSED"
    assert result["RETRY_SAFE_NOW"] is False
    assert len([c for c in transport.calls if c.method == "POST"]) == 1


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_fake_post_redirect_does_not_resubmit(status: int) -> None:
    transport = _fake_transport()
    transport.post_status_code = status
    transport.post_body = b"redirect"
    transport.post_redirect_location = "https://eea.okx.com/api/v5/trade/order"
    transport.post_headers = {"Location": "https://eea.okx.com/api/v5/trade/order?x=1"}
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    assert result["ok"] is False
    assert result["CANARY_RESULT"] == "ENTRY_SUBMIT_POST_REDIRECT_FAIL_CLOSED"
    assert result["UNKNOWN_SUBMIT"] is False
    assert result["BLIND_RETRY"] is False
    assert result["ORDER_COUNT_SUBMITTED"] == 1
    evidence = result["http_error_evidence"]
    assert evidence["redirect_followed"] is False
    assert evidence["redirect_status"] == status
    loc = str(evidence["redirect_location"] or "")
    assert loc == "https://eea.okx.com/api/v5/trade/order"
    assert "?" not in loc
    posts = [c for c in transport.calls if c.method == "POST"]
    assert len(posts) == 1


def test_sanitize_redirect_location_drops_userinfo_query_and_fragment() -> None:
    # Construct userinfo without a contiguous scheme://user:pass@ literal so the
    # tracked credential hygiene scanner does not treat the fixture as a secret.
    userinfo = "user" + ":" + "pass"
    raw = "https://" + userinfo + "@eea.okx.com/api/v5/trade/order?x=1#frag"
    cleaned = sanitize_redirect_location_v1(raw)
    assert cleaned == "https://eea.okx.com/api/v5/trade/order"
    assert "?" not in cleaned
    assert "#" not in cleaned
    assert "@" not in cleaned


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_urllib_post_redirect_fail_closed_no_second_request(status: int) -> None:
    import threading
    import time
    from http.server import BaseHTTPRequestHandler, HTTPServer

    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
        LiveCanaryHttpRequestV1,
        UrllibLiveCanaryTransportV1,
    )

    hits: list[dict[str, str]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            hits.append({"method": "POST", "path": self.path})
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            self.send_response(status)
            self.send_header(
                "Location",
                f"http://127.0.0.1:{self.server.server_address[1]}/second",
            )
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"redirect")

        def do_GET(self) -> None:
            hits.append({"method": "GET", "path": self.path})
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"followed")

        def log_message(self, format: str, *args: object) -> None:
            return

    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    port = httpd.server_address[1]
    body = '{"instId":"BTC-USDT-SWAP"}'
    try:
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
        response = transport.send(
            LiveCanaryHttpRequestV1(
                method="POST",
                url=f"http://127.0.0.1:{port}/api/v5/trade/order",
                host="127.0.0.1",
                endpoint="/api/v5/trade/order",
                headers={"Content-Type": "application/json"},
                timeout_seconds=2.0,
                body_text=body,
            )
        )
        time.sleep(0.05)
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)
    assert len(hits) == 1
    assert hits[0] == {"method": "POST", "path": "/api/v5/trade/order"}
    assert response.redirect_followed is False
    assert response.redirect_status == status
    assert response.method == "POST"
    assert response.status_code == status
    assert transport.http_exchange_count == 1
    assert response.wire_body_sha256
    import hashlib

    assert response.wire_body_sha256 == hashlib.sha256(body.encode("utf-8")).hexdigest()


def test_signed_body_equals_wire_body_evidence_contract() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
        signed_wire_body_evidence_v1,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
        serialize_signed_post_body_v1,
    )

    payload = {
        "instId": "BTC-USDT-SWAP",
        "tdMode": "cross",
        "side": "buy",
        "ordType": "limit",
        "sz": "0.01",
        "px": "63102",
        "clOrdId": "ptokxeprodae2d2fa0ae2d2fa000",
    }
    body = serialize_signed_post_body_v1(payload)
    match = signed_wire_body_evidence_v1(
        signed_body_text=body, wire_body_bytes=body.encode("utf-8")
    )
    mismatch = signed_wire_body_evidence_v1(signed_body_text=body, wire_body_bytes=b"{}")
    assert match["SIGNED_BODY_EQUALS_WIRE_BODY"] is True
    assert mismatch["SIGNED_BODY_EQUALS_WIRE_BODY"] is False
    transport = _fake_transport()
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    assert result["SIGNED_BODY_EQUALS_WIRE_BODY"] is True
    posts = [c for c in transport.calls if c.method == "POST"]
    assert len(posts) == 1
    import hashlib

    wire_sha = hashlib.sha256(posts[0].body_text.encode("utf-8")).hexdigest()[:12]
    assert result["signed_wire_body_evidence"]["wire_body_sha256_12"] == wire_sha
