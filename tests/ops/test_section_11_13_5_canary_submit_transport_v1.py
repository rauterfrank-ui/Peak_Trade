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
