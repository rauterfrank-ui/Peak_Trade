"""Focused tests for §11.13.5 canary submit transport (mocks only; zero live requests)."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from src.core.environment import LIVE_CONFIRM_TOKEN
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    build_venue_native_order_body_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.config_v1 import (
    example_incomplete_config_dict_v1,
    load_live_canary_config_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    CANARY_SUBMIT_TRANSPORT_IMPLEMENTED,
    DEFAULT_INSTRUMENT_ID,
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.leverage_observation_v1 import (
    account_leverage_info_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_available_observation_v1 import (
    account_max_size_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.price_band_observation_v1 import (
    public_price_limit_query_path_v1,
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
            "instId": DEFAULT_INSTRUMENT_ID,
            "instType": "FUTURES",
            "ruleType": "xperp",
            "minSz": "1",
            "lotSz": "1",
            "tickSz": "0.0001",
            "ctVal": "1",
            "ctValCcy": "SUI",
            "settleCcy": "USDC",
            "state": "live",
            "maxLmtSz": "100000000",
            "maxMktSz": "100000",
        }
    ],
}
TICKER = {"code": "0", "data": [{"instId": DEFAULT_INSTRUMENT_ID, "last": "0.8209"}]}
EMPTY = {"code": "0", "data": []}
MAX_AVAILABLE = {
    "code": "0",
    "data": [{"instId": DEFAULT_INSTRUMENT_ID, "maxBuy": "100", "maxSell": "100"}],
}
PRICE_BAND = {
    "code": "0",
    "data": [
        {
            "instId": DEFAULT_INSTRUMENT_ID,
            "instType": "FUTURES",
            "buyLmt": "2.0000",
            "sellLmt": "0.0001",
            "ts": "1725000000000",
            "enabled": True,
        }
    ],
}
LEVERAGE = {
    "code": "0",
    "data": [
        {
            "instId": DEFAULT_INSTRUMENT_ID,
            "ccy": "",
            "mgnMode": "cross",
            "posSide": "net",
            "lever": "5",
        }
    ],
}
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


def _max_available_plan_kwargs(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "max_available_payload": MAX_AVAILABLE,
        "max_available_get_performed": True,
        "max_available_endpoint": account_max_size_query_path_v1(
            instrument_id=DEFAULT_INSTRUMENT_ID, td_mode="cross", px="0.8209"
        ),
        "max_available_http_status": 200,
        "max_available_auth_header_sent": True,
        "max_available_px_sent": "0.8209",
        "price_band_payload": PRICE_BAND,
        "price_band_get_performed": True,
        "price_band_endpoint": public_price_limit_query_path_v1(
            instrument_id=DEFAULT_INSTRUMENT_ID
        ),
        "price_band_http_status": 200,
        "price_band_auth_header_sent": False,
        "leverage_payload": LEVERAGE,
        "leverage_get_performed": True,
        "leverage_endpoint": account_leverage_info_query_path_v1(
            instrument_id=DEFAULT_INSTRUMENT_ID, mgn_mode="cross"
        ),
        "leverage_http_status": 200,
        "leverage_auth_header_sent": True,
        "leverage_mgn_mode": "cross",
    }
    body.update(overrides)
    return body


def _fake_transport() -> RecordingFakeCanaryTransportV1:
    return RecordingFakeCanaryTransportV1(
        bodies_by_endpoint={
            "/api/v5/public/instruments": json.dumps(INSTRUMENTS).encode(),
            "/api/v5/market/ticker": json.dumps(TICKER).encode(),
            "/api/v5/public/price-limit": json.dumps(PRICE_BAND).encode(),
            "/api/v5/account/positions": json.dumps(EMPTY).encode(),
            "/api/v5/account/max-size": json.dumps(MAX_AVAILABLE).encode(),
            "/api/v5/account/leverage-info": json.dumps(LEVERAGE).encode(),
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
            pretrade_decision_id="test-fresh-decision-empty",
        )


def test_order_plan_rejects_quantity_above_min_sz() -> None:
    bloated = {
        "code": "0",
        "data": [
            {
                "instId": DEFAULT_INSTRUMENT_ID,
                "instType": "FUTURES",
                "ruleType": "xperp",
                "minSz": "1",
                "lotSz": "2",
                "tickSz": "0.0001",
                "ctVal": "1",
            }
        ],
    }
    with pytest.raises(LiveCanaryOrderPlanError, match="UNSAFE_QUANTITY"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=bloated,
            ticker_payload=TICKER,
            owner_go=OWNER_GO_EXECUTE,
            origin_main_sha=ORIGIN_SHA,
            pretrade_decision_id="test-fresh-decision-bloated",
        )


def test_order_plan_reuses_proven_venue_native_body_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = {"sentinel": True}
    calls: list[dict[str, Any]] = []

    def _fake_builder(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return sentinel

    monkeypatch.setattr(
        "src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1.build_venue_native_order_body_v1",
        _fake_builder,
    )
    plan = build_minimum_valid_canary_order_plan_v1(
        instruments_payload=INSTRUMENTS,
        ticker_payload=TICKER,
        owner_go=OWNER_GO_EXECUTE,
        origin_main_sha=ORIGIN_SHA,
        pretrade_decision_id="test-fresh-decision-body-builder",
        **_max_available_plan_kwargs(),
    )
    assert len(calls) == 1
    assert calls[0]["client_order_id"] == plan.clordid
    assert calls[0]["instrument"] == DEFAULT_INSTRUMENT_ID
    assert calls[0]["order_type"] == "LIMIT"
    assert calls[0]["side"] == "BUY"
    assert calls[0]["quantity"] == plan.quantity == "1"
    assert calls[0]["td_mode"] == "cross"
    assert calls[0]["px"] == plan.limit_price
    source = inspect.getsource(build_minimum_valid_canary_order_plan_v1)
    assert "build_venue_native_order_body_v1(" in source
    assert '"instId"' not in source
    assert '"clOrdId"' not in source


def test_order_plan_body_equals_proven_builder_contract() -> None:
    plan = build_minimum_valid_canary_order_plan_v1(
        instruments_payload=INSTRUMENTS,
        ticker_payload=TICKER,
        owner_go=OWNER_GO_EXECUTE,
        origin_main_sha=ORIGIN_SHA,
        pretrade_decision_id="test-fresh-decision-body-equals",
        **_max_available_plan_kwargs(),
    )
    expected = build_venue_native_order_body_v1(
        client_order_id=plan.clordid,
        instrument=plan.instrument_id,
        order_type=plan.order_type,
        side=plan.side,
        quantity=plan.quantity,
        td_mode=plan.td_mode,
        px=plan.limit_price,
    )
    assert plan.venue_native_payload == expected
    assert set(plan.venue_native_payload) == {
        "instId",
        "tdMode",
        "side",
        "ordType",
        "sz",
        "px",
        "clOrdId",
    }
    assert plan.venue_native_payload["instId"] == DEFAULT_INSTRUMENT_ID
    assert plan.venue_native_payload["tdMode"] == "cross"
    assert plan.venue_native_payload["side"] == "buy"
    assert plan.venue_native_payload["ordType"] == "limit"
    assert plan.venue_native_payload["sz"] == "1"
    assert plan.quantity == "1"
    assert plan.venue_native_payload["px"] == plan.limit_price == "0.8209"
    assert plan.venue_native_payload["clOrdId"] == plan.clordid
    assert "posSide" not in plan.venue_native_payload
    assert "posMode" not in plan.venue_native_payload
    assert "reduceOnly" not in plan.venue_native_payload
    assert "x-simulated-trading" not in plan.venue_native_payload


def test_canary_submit_post_omits_pos_side_and_simulated_trading_header() -> None:
    transport = _fake_transport()
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    assert result["SIGNED_BODY_EQUALS_WIRE_BODY"] is True
    posts = [c for c in transport.calls if c.method == "POST"]
    assert len(posts) == 1
    body = json.loads(posts[0].body_text)
    assert "posSide" not in body
    assert "posMode" not in body
    header_keys = {str(k).lower() for k in posts[0].headers}
    assert "x-simulated-trading" not in header_keys
    expected = build_venue_native_order_body_v1(
        client_order_id=body["clOrdId"],
        instrument=body["instId"],
        order_type=body["ordType"],
        side=body["side"],
        quantity=body["sz"],
        td_mode=body["tdMode"],
        px=body["px"],
    )
    assert body == expected


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
        {"code": "0", "data": [{"instId": DEFAULT_INSTRUMENT_ID, "pos": "1"}]}
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
    assert result["plan"]["quantity"] == "1"
    assert result["plan"]["max_notional"] == result["plan"]["min_executable_notional"]
    assert result["SIGNED_BODY_EQUALS_WIRE_BODY"] is True
    assert result["ok"] is True
    posts = [c for c in transport.calls if c.method == "POST"]
    assert len(posts) == 1
    assert posts[0].endpoint == "/api/v5/trade/order"
    assert "withdraw" not in posts[0].endpoint.lower()
    instrument_gets = [
        c.endpoint for c in transport.calls if "public/instruments" in str(c.endpoint)
    ]
    assert instrument_gets
    assert all("instType=FUTURES" in ep for ep in instrument_gets)
    assert all("instType=SWAP" not in ep for ep in instrument_gets)
    assert all(DEFAULT_INSTRUMENT_ID in ep for ep in instrument_gets)
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
    body = '{"instId":"' + DEFAULT_INSTRUMENT_ID + '"}'
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
        "instId": DEFAULT_INSTRUMENT_ID,
        "tdMode": "cross",
        "side": "buy",
        "ordType": "limit",
        "sz": "1",
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


def test_order_plan_rejects_swap_and_demo_instrument_fallback() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        DEMO_XPERP_INSTRUMENT_ID,
        HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID,
        HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID,
        LiveCanaryInstrumentBindingError,
        assert_live_canary_instrument_binding_v1,
    )

    with pytest.raises(LiveCanaryInstrumentBindingError, match="REJECTED_CANARY_INSTRUMENT"):
        assert_live_canary_instrument_binding_v1(
            instrument_id=HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID
        )
    with pytest.raises(LiveCanaryInstrumentBindingError, match="REJECTED_CANARY_INSTRUMENT"):
        assert_live_canary_instrument_binding_v1(instrument_id=DEMO_XPERP_INSTRUMENT_ID)
    with pytest.raises(LiveCanaryInstrumentBindingError, match="INSTRUMENT_BINDING_MISMATCH"):
        assert_live_canary_instrument_binding_v1(
            instrument_id=HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID
        )
    with pytest.raises(LiveCanaryInstrumentBindingError, match="REJECTED_CANARY_INST_TYPE"):
        assert_live_canary_instrument_binding_v1(
            instrument_id=DEFAULT_INSTRUMENT_ID, inst_type="SWAP"
        )
    swap_payload = {
        "code": "0",
        "data": [
            {
                "instId": DEFAULT_INSTRUMENT_ID,
                "instType": "SWAP",
                "ruleType": "xperp",
                "minSz": "1",
                "lotSz": "1",
                "tickSz": "0.0001",
                "ctVal": "1",
            }
        ],
    }
    with pytest.raises(LiveCanaryOrderPlanError, match="REJECTED_CANARY_INST_TYPE"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=swap_payload,
            ticker_payload=TICKER,
            owner_go=OWNER_GO_EXECUTE,
            origin_main_sha=ORIGIN_SHA,
            pretrade_decision_id="test-fresh-decision-swap",
        )
    with pytest.raises(LiveCanaryOrderPlanError, match="REJECTED_CANARY_INSTRUMENT"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload={
                "code": "0",
                "data": [
                    {
                        "instId": "BTC-USDT-SWAP",
                        "instType": "FUTURES",
                        "ruleType": "xperp",
                        "minSz": "1",
                        "lotSz": "1",
                        "tickSz": "0.0001",
                        "ctVal": "1",
                    }
                ],
            },
            ticker_payload=TICKER,
            owner_go=OWNER_GO_EXECUTE,
            origin_main_sha=ORIGIN_SHA,
            instrument_id="BTC-USDT-SWAP",
            pretrade_decision_id="test-fresh-decision-rejected-instrument",
        )
    fractional = {
        "code": "0",
        "data": [
            {
                "instId": DEFAULT_INSTRUMENT_ID,
                "instType": "FUTURES",
                "ruleType": "xperp",
                "minSz": "0.01",
                "lotSz": "0.01",
                "tickSz": "0.0001",
                "ctVal": "0.01",
            }
        ],
    }
    with pytest.raises(LiveCanaryOrderPlanError, match="INTEGER_CONTRACT_REQUIRED"):
        build_minimum_valid_canary_order_plan_v1(
            instruments_payload=fractional,
            ticker_payload=TICKER,
            owner_go=OWNER_GO_EXECUTE,
            origin_main_sha=ORIGIN_SHA,
            pretrade_decision_id="test-fresh-decision-fractional",
        )


def test_xperp_economic_baseline_contract_does_not_inherit_swap_or_demo() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.xperp_310404_economic_baseline_contract_v1 import (
        live_eea_xperp_310404_economic_baseline_contract_v1,
    )

    contract = live_eea_xperp_310404_economic_baseline_contract_v1()
    assert contract["CANARY_INSTRUMENT"] == DEFAULT_INSTRUMENT_ID
    assert contract["CANARY_INSTRUMENT"] == "SUI-USD_UM_XPERP-310404"
    assert contract["CANARY_INST_TYPE"] == "FUTURES"
    assert contract["PRODUCT_RULE_TYPE"] == "xperp"
    assert contract["SETTLEMENT_ACCOUNT_TRUTH"] == "USDC"
    assert contract["INHERITED_FROM_BTC_USDT_SWAP"] is False
    assert contract["INHERITED_FROM_DEMO_310328"] is False
    assert contract["minSz"] == "1"
    assert contract["lotSz"] == "1"
    assert contract["tickSz"] == "0.0001"
    assert contract["ctVal"] == "1"
    assert contract["ctValCcy"] == "SUI"
    assert contract["ONE_CONTRACT_EQUALS_ONE_SUI"] is False
    assert contract["EXCHANGE_POSITION_VALUE_STATUS"] == "UNPROVEN"
    assert contract["EXECUTED"] is False
    assert contract["LIVE_AUTHORIZED"] is False
    assert contract["set_account_leverage"] == "3"
    assert contract["set_account_leverage_mgn_mode"] == "cross"
    assert contract["set_account_leverage_pos_side"] == "net"
    assert contract["HISTORICAL_BTC_SNAPSHOT_ISOLATED"] is True
    assert contract["HISTORICAL_BTC_SNAPSHOT_INSTRUMENT"] == "BTC-USD_UM_XPERP-310404"
    assert contract["snapshot_mark_px"] == "63043.7"
    assert contract["snapshot_ct_val"] == "0.0001"
    assert contract["snapshot_theoretical_initial_margin_usdc"] == ("2.101456666666666666666666667")
    assert contract["minimum_theoretical_initial_margin_proven"] is False
    assert contract["HISTORICAL_BTC_MINIMUM_THEORETICAL_INITIAL_MARGIN_PROVEN"] is True
    assert contract["snapshot_theoretical_funding_floor_proven"] is False
    assert contract["HISTORICAL_BTC_SNAPSHOT_THEORETICAL_FUNDING_FLOOR_PROVEN"] is True
    assert contract["canary_operational_minimum_proven"] is False
    assert contract["recommended_bounded_canary_funding_amount_proven"] is False
    assert contract["funding_amount_proven"] is False
    assert contract["tdMode_compatibility"] == ("cross_get_proven_leverage_setting_no_live_post")
    assert contract["tdMode_live_post_proven"] is False
    assert "instType=SWAP" not in str(contract["public_instruments_query"])
    assert DEFAULT_INSTRUMENT_ID in str(contract["public_instruments_query"])
    assert "BTC-USD_UM_XPERP-310404" not in str(contract["public_instruments_query"])
    assert "BTC-USD_UM_XPERP-310404" not in str(contract["mark_last_price_source"])
    assert contract["rejected_swap_instrument"] == "BTC-USDT-SWAP"
    assert contract["rejected_demo_instrument"] == "BTC-USD_UM_XPERP-310328"
    assert contract["CANARY_INSTRUMENT"] != contract["rejected_demo_instrument"]
    assert contract["CANARY_INSTRUMENT"] != contract["HISTORICAL_BTC_SNAPSHOT_INSTRUMENT"]


def _assert_no_post(transport: RecordingFakeCanaryTransportV1) -> None:
    assert all(call.method != "POST" for call in transport.calls)


def test_t11_leftover_other_instrument_rejects_before_post() -> None:
    leftover = "ETH-USD_UM_XPERP-999999"
    transport = _fake_transport()
    transport.bodies_by_endpoint["/api/v5/account/positions"] = json.dumps(
        {"code": "0", "data": [{"instId": leftover, "pos": "1"}]}
    ).encode()
    with pytest.raises(LiveCanarySubmitTransportError, match="DENY_OTHER_OPEN_INSTRUMENT_PRESENT"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)
    assert any("/api/v5/account/positions" in call.endpoint for call in transport.calls)


def test_t11_historical_btc_row_is_not_sui_target_row() -> None:
    leftover = "BTC-USD_UM_XPERP-310404"
    transport = _fake_transport()
    transport.bodies_by_endpoint["/api/v5/account/positions"] = json.dumps(
        {"code": "0", "data": [{"instId": leftover, "pos": "1"}]}
    ).encode()
    with pytest.raises(LiveCanarySubmitTransportError, match="DENY_OTHER_OPEN_INSTRUMENT_PRESENT"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)


def test_t12_no_open_positions_reaches_downstream_fake_post_without_real_network() -> None:
    transport = _fake_transport()
    assert transport.venue_live_contact is False
    result = run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    assert result["ok"] is True
    posts = [call for call in transport.calls if call.method == "POST"]
    assert len(posts) == 1
    assert posts[0].endpoint == "/api/v5/trade/order"
    assert transport.venue_live_contact is False
    position_gets = [
        call
        for call in transport.calls
        if call.method == "GET" and "/api/v5/account/positions" in call.endpoint
    ]
    assert len(position_gets) == 1


def test_t13_open_canonical_canary_instrument_still_open_position_present() -> None:
    transport = _fake_transport()
    transport.bodies_by_endpoint["/api/v5/account/positions"] = json.dumps(
        {"code": "0", "data": [{"instId": DEFAULT_INSTRUMENT_ID, "pos": "1"}]}
    ).encode()
    with pytest.raises(LiveCanarySubmitTransportError, match="OPEN_POSITION_PRESENT"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)


def test_t14_positions_fetch_failure_no_post() -> None:
    transport = _fake_transport()
    transport.bodies_by_endpoint["/api/v5/account/positions"] = b"not-json"
    with pytest.raises((LiveCanarySubmitTransportError, LiveCanaryHttpError)):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)


def test_t15_ambiguous_duplicate_rows_no_post() -> None:
    leftover = "ETH-USD_UM_XPERP-999999"
    transport = _fake_transport()
    transport.bodies_by_endpoint["/api/v5/account/positions"] = json.dumps(
        {
            "code": "0",
            "data": [
                {"instId": leftover, "pos": "1"},
                {"instId": leftover, "pos": "1"},
            ],
        }
    ).encode()
    with pytest.raises(LiveCanarySubmitTransportError, match="DENY_AMBIGUOUS_POSITION_ROWS"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)


def test_t16_pending_order_gate_still_rejects() -> None:
    transport = _fake_transport()
    transport.bodies_by_endpoint["/api/v5/trade/orders-pending"] = json.dumps(
        {"code": "0", "data": [{"instId": DEFAULT_INSTRUMENT_ID, "ordId": "pending-1"}]}
    ).encode()
    with pytest.raises(LiveCanarySubmitTransportError, match="OPEN_ORDER_PRESENT"):
        run_canary_submit_transport_v1(**_transport_kwargs(transport=transport))
    _assert_no_post(transport)


def test_t17_wrong_selected_instrument_still_rejects_binding() -> None:
    kwargs = _transport_kwargs()
    kwargs["cfg"].payload["instrument_id"] = "BTC-USDT-SWAP"
    transport = kwargs["transport"]
    with pytest.raises(LiveCanarySubmitTransportError, match="INSTRUMENT_BINDING"):
        run_canary_submit_transport_v1(**kwargs)
    _assert_no_post(transport)


def test_t17_superseded_btc_310404_as_current_target_fails_closed() -> None:
    kwargs = _transport_kwargs()
    kwargs["cfg"].payload["instrument_id"] = "BTC-USD_UM_XPERP-310404"
    transport = kwargs["transport"]
    with pytest.raises(LiveCanarySubmitTransportError, match="INSTRUMENT_BINDING_MISMATCH"):
        run_canary_submit_transport_v1(**kwargs)
    _assert_no_post(transport)
