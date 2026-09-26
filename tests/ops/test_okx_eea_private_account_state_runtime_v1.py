"""Deterministic tests for OKX_EEA_PRIVATE_ACCOUNT_STATE_RUNTIME_V1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FRESHNESS_POLICY,
)
from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    CREDENTIAL_CLASS,
    DEDICATED_FILLS_WS_REQUIRED,
    EEA_PRIVATE_WS_BASE,
    EEA_REST_HOST,
    FRESH_PRETRADE_FRESHNESS_POLICY,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
    PRIVATE_STATE_GLOBAL_TTL_SECONDS,
    QUALITY_RECONCILIATION_REQUIRED,
)
from src.ops.okx_eea_private_account_state_runtime_v1.consumer_adapters_v1 import (
    balance_equity_observation_adapter_v1,
    wp_b_to_fresh_pretrade_observation_hint_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.credentials_v1 import (
    ObservationCredentialError,
    join_observation_credential_v1,
    redact_credential_payload_v1,
    validate_credential_class_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.durable_store_v1 import (
    append_private_state_v1,
    default_private_store_paths_v1,
    load_all_private_state_v1,
    load_known_fill_trade_ids_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.event_pipeline_v1 import (
    PrivateEventSequenceStateV1,
    process_private_ws_events_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.mutation_prohibition_v1 import (
    assert_no_ws_mutation_operations_in_public_api_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.ws_transport_v1 import (
    assert_ws_outbound_op_allowed_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.quality_v1 import (
    assert_no_global_private_state_ttl_v1,
    preserve_fresh_pretrade_policy_pin_v1,
    quality_after_disconnect_v1,
    quality_for_fresh_pretrade_surface_v1,
    quality_for_position_observation_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.reconciliation_v1 import (
    reconcile_rest_baseline_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.rest_baseline_v1 import (
    PrivateRestBaselineError,
    assert_get_path_allowlisted_v1,
    assert_no_rest_post_v1,
    collect_rest_baseline_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.runtime_orchestrator_v1 import (
    OkxEeaPrivateAccountStateRuntimeV1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.safety_boundary_v1 import (
    private_runtime_safety_attestation_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.state_contracts_v1 import (
    BalanceSnapshotV1,
    PrivateStateProvenanceV1,
    PrivateStateQualityV1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.ws_binding_v1 import (
    PrivateWsBindingError,
    forbid_wseeapap_as_production_authority_v1,
    load_ratified_eea_private_ws_binding_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.ws_transport_v1 import PrivateWsTransportV1

REPO = Path(__file__).resolve().parents[2]


def _fixture_rest(path: str, _params: Mapping[str, str]) -> dict[str, Any]:
    if path == "/api/v5/account/config":
        return {"code": "0", "data": [{"acctLv": "2", "posMode": "net_mode"}]}
    if path == "/api/v5/account/balance":
        return {
            "code": "0",
            "data": [{"totalEq": "100", "details": [{"ccy": "USDT", "availEq": "90"}]}],
        }
    if path == "/api/v5/account/positions":
        return {
            "code": "0",
            "data": [{"instId": "ETH-USDT-SWAP", "pos": "1", "posSide": "net", "avgPx": "100"}],
        }
    if path.endswith("orders-pending") or path.endswith("orders-history"):
        return {
            "code": "0",
            "data": [
                {
                    "instId": "ETH-USDT-SWAP",
                    "ordId": "1",
                    "clOrdId": "c1",
                    "state": "live",
                }
            ],
        }
    if path.endswith("fills"):
        return {
            "code": "0",
            "data": [
                {
                    "instId": "ETH-USDT-SWAP",
                    "tradeId": "t1",
                    "ordId": "1",
                    "clOrdId": "c1",
                    "fillSz": "1",
                    "fillPx": "100",
                }
            ],
        }
    if path.endswith("leverage-info") or path.endswith("max-size"):
        return {"code": "0", "data": [{}]}
    raise AssertionError(path)


class _FakePrivateConnector:
    def __init__(self, *, reject_fills: bool = False) -> None:
        self.reject_fills = reject_fills
        self.subscribed = False

    def connect(self, ws_base_url: str) -> None:
        assert ws_base_url == EEA_PRIVATE_WS_BASE

    def login(self, login_payload: Mapping[str, Any]) -> None:
        assert "apiKey" not in login_payload

    def subscribe(self, args: list) -> None:
        if self.reject_fills and any(a.get("channel") == "fills" for a in args):
            raise RuntimeError("fills rejected")
        self.subscribed = True

    def send_op(self, op: str, payload: Mapping[str, Any] | None = None) -> None:
        assert_ws_outbound_op_allowed_v1(op)

    def disconnect(self) -> None:
        self.subscribed = False


def test_policy_hosts_and_credential_class() -> None:
    cfg = json.loads(
        (
            REPO / "config/governance/okx_eea_private_account_state_runtime_v1_policy_v1.json"
        ).read_text()
    )
    assert cfg["eea_rest_host"] == "eea.okx.com"
    assert cfg["eea_private_ws_base"] == EEA_PRIVATE_WS_BASE
    assert cfg["credential_class"] == CREDENTIAL_CLASS
    assert cfg["private_state_global_ttl_seconds"] is None


def test_wseeapap_rejected_for_production() -> None:
    with pytest.raises(PrivateWsBindingError):
        forbid_wseeapap_as_production_authority_v1("wseeapap.okx.com")
    binding = load_ratified_eea_private_ws_binding_v1()
    assert "wseea" in binding.ws_base_url


def test_credential_fail_closed() -> None:
    with pytest.raises(ObservationCredentialError):
        join_observation_credential_v1(
            secretref_uri=None, secretref_bound=False, credential_class=CREDENTIAL_CLASS
        )
    with pytest.raises(ObservationCredentialError):
        validate_credential_class_v1("LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY")
    handle = join_observation_credential_v1(
        secretref_uri="secretref://unprovisioned/example",
        secretref_bound=True,
        credential_class=CREDENTIAL_CLASS,
    )
    assert handle.rest_post_authority is False
    redacted = redact_credential_payload_v1({"api_key": "x", "nested": {"passphrase": "y"}})
    assert redacted["api_key"] == "<REDACTED>"


def test_rest_allowlist_and_no_post() -> None:
    with pytest.raises(PrivateRestBaselineError):
        assert_get_path_allowlisted_v1("/api/v5/trade/order")
    with pytest.raises(PrivateRestBaselineError):
        assert_no_rest_post_v1("POST")
    snap = collect_rest_baseline_v1(_fixture_rest, captured_at="2026-09-26T00:00:00Z")
    assert snap.host == EEA_REST_HOST
    assert snap.balance is not None


def test_rest_auth_failure_fail_closed() -> None:
    def bad(_p: str, _q: Mapping[str, str]) -> dict[str, Any]:
        return {"code": "50113", "msg": "auth"}

    with pytest.raises(PrivateRestBaselineError):
        collect_rest_baseline_v1(bad, captured_at="2026-09-26T00:00:00Z")


def test_ws_login_subscribe_reconnect_optional_fills() -> None:
    transport = PrivateWsTransportV1.from_ratified_binding(
        connector=_FakePrivateConnector(reject_fills=True),
        message_source=lambda: iter(()),
        login_payload={"op": "login"},
    )
    transport.connect_login_subscribe(include_optional_fills=True)
    assert transport.state.subscribed is True
    assert transport.state.fills_channel_rejected is True
    transport.reconnect_resubscribe()
    assert transport.state.reconnect_count == 1


def test_ws_no_mutation_ops() -> None:
    att = assert_no_ws_mutation_operations_in_public_api_v1()
    assert att["PRIVATE_WS_ORDER_SEND_AUTHORIZED"] is False
    with pytest.raises(ValueError):
        assert_ws_outbound_op_allowed_v1("order")


def test_event_duplicate_out_of_order_and_gap() -> None:
    events = [
        {
            "channel": "positions",
            "instId": "ETH-USDT-SWAP",
            "pos": "1",
            "uTime": "2000",
            "event_id": "a",
        },
        {
            "channel": "positions",
            "instId": "ETH-USDT-SWAP",
            "pos": "1",
            "uTime": "2000",
            "event_id": "a",
        },
        {
            "channel": "positions",
            "instId": "ETH-USDT-SWAP",
            "pos": "1",
            "uTime": "1000",
            "event_id": "b",
        },
    ]
    envs, _, recon = process_private_ws_events_v1(
        events=events, state=PrivateEventSequenceStateV1()
    )
    assert envs[1].duplicate is True
    assert envs[2].out_of_order is True
    assert recon is True


def test_reconciliation_rest_ws_disagreement_no_silent_adopt() -> None:
    snap = collect_rest_baseline_v1(_fixture_rest, captured_at="2026-09-26T00:00:00Z")
    result = reconcile_rest_baseline_v1(
        reconciliation_id="r1",
        rest_baseline=snap,
        ws_positions=[{"instId": "ETH-USDT-SWAP", "pos": "2"}],
    )
    assert result.trusted is False
    assert result.snapshot.quality.state == QUALITY_RECONCILIATION_REQUIRED
    assert result.snapshot.safe_adopt_exchange_truth is False


def test_quality_preserves_external_freshness_rules() -> None:
    assert_no_global_private_state_ttl_v1()
    assert PRIVATE_STATE_GLOBAL_TTL_SECONDS is None
    assert preserve_fresh_pretrade_policy_pin_v1() == FRESH_PRETRADE_FRESHNESS_POLICY
    assert FRESHNESS_POLICY == "FRESH_GET_PER_PRETRADE_DECISION"
    hint = wp_b_to_fresh_pretrade_observation_hint_v1(endpoint_path="/api/v5/account/max-size")
    assert hint["fresh_pretrade_substitute_forbidden"] is True
    pos = quality_for_position_observation_v1(
        age_ms=POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS + 1, ws_trusted=True
    )
    assert pos.quality == "STALE"
    assert quality_after_disconnect_v1() == QUALITY_RECONCILIATION_REQUIRED
    cached = quality_for_fresh_pretrade_surface_v1(cached_only=True)
    assert cached.fresh_pretrade_substitute is False


def test_durable_restart_not_trusted_until_reconcile(tmp_path: Path) -> None:
    paths = default_private_store_paths_v1(tmp_path)
    append_private_state_v1(
        paths,
        {
            "fact_kind": "PositionStateV1",
            "instId": "ETH-USDT-SWAP",
            "pos": "9",
            "quality": {"state": "CURRENT"},
        },
    )
    runtime = OkxEeaPrivateAccountStateRuntimeV1(
        store_root=tmp_path,
        rest_fetch_json=_fixture_rest,
    )
    out = runtime.restart_sequence_v1(captured_at="2026-09-26T00:00:00Z")
    assert out["restored_count"] == 1
    assert runtime.trusted_current is False
    loaded = load_all_private_state_v1(paths)
    assert any(r.get("fact_kind") == "ReconciliationSnapshotV1" for r in loaded)


def test_fill_dedup_across_restart(tmp_path: Path) -> None:
    paths = default_private_store_paths_v1(tmp_path)
    append_private_state_v1(
        paths,
        {
            "fact_kind": "FillFactV1",
            "tradeId": "t1",
            "instId": "ETH-USDT-SWAP",
            "fillSz": "1",
            "fillPx": "1",
        },
    )
    assert "t1" in load_known_fill_trade_ids_v1(paths)


def test_safety_boundary_and_equity_mint_forbidden() -> None:
    att = private_runtime_safety_attestation_v1()
    assert att["WP_B_SELECTION_AUTHORITY"] is False
    assert att["MULTI_FUTURE_RUNTIME_AUTHORIZED"] is False
    assert att["MAX_POSITIONS_EFFECTIVE"] == 1
    assert att["K2_ABSENT"] is True
    assert att["RUNNING_ACCOUNT_EQUITY_MINT_ALLOWED"] is False
    assert att["private_runtime_may_post"] is False
    bal = BalanceSnapshotV1(
        total_eq="1",
        avail_eq="1",
        ccy="USDT",
        quality=PrivateStateQualityV1(state="CURRENT"),
        provenance=PrivateStateProvenanceV1(
            observation_source_class=CREDENTIAL_CLASS,
            transport="rest",
            endpoint_or_channel="/api/v5/account/balance",
            venue_host_family=EEA_REST_HOST,
            instrument=None,
            venue_timestamp_ms=None,
            captured_at="t",
            session_identity="s",
            body_digest="d",
            credential_class=CREDENTIAL_CLASS,
        ),
    )
    obs = balance_equity_observation_adapter_v1(bal)
    assert obs["running_account_equity_mint_allowed"] is False


def test_dedicated_fills_ws_not_required() -> None:
    assert DEDICATED_FILLS_WS_REQUIRED is False
