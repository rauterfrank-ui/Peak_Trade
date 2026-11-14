"""Original pre-POST freshness consumer with synthetic ports; no venue access."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import socket

import pytest
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
    synthetic_current_post_pending_context_v1,
)

from src.data.safety import DataSourceKind

from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_actual_venue_post_immediate_pre_mutation_freshness_v1 as consumer,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    build_final_order_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_POSITIONS,
    GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
    GET_CACHE_POLICY_DECISION_BOUND_SNAPSHOT,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
    _bound,
    _productive_transport,
)
from tests.ops.test_full_core_fresh_pretrade_runtime_get_seam_v1 import (
    InjectedFreshGetTransportV1,
)

DECISION = "prepost-position-consumer-case"


def envelope(**kwargs):
    args = dict(
        instrument_id=_bound().venue_native_id,
        side="buy",
        order_type="market",
        quantity="1",
        quantity_unit="CONTRACTS",
        td_mode="cross",
        reduce_only=False,
        client_order_id="positionproof",
        path_kind="FULL_CORE_CURRENT_PRODUCTIVE",
        venue_plan_clordid="positionproof",
        quantity_source="SYNTHETIC",
        side_source="SYNTHETIC",
        instrument_source="SYNTHETIC",
        admission_ref="SYNTHETIC",
        provenance_ref="SYNTHETIC",
        creation_epoch="2026-11-07T12:00:00Z",
    )
    args.update(kwargs)
    return build_final_order_envelope_v1(**args)


def row(quantity="1", *, native=None, side="net"):
    return dict(
        instId=native or _bound().venue_native_id,
        pos=quantity,
        posSide=side,
        mgnMode="cross",
        ccy="USDT",
    )


class Port:
    """Explicit test double, even though original transport/DataSafety labels are exercised."""

    def __init__(self, *, global_rows=(), scoped_rows=(), fault=None, global_fault=None):
        payloads = _productive_transport().payloads
        payloads[ENDPOINT_ACCOUNT_POSITIONS] = {"code": "0", "data": list(global_rows)}
        self.base = InjectedFreshGetTransportV1(
            payloads=payloads,
            transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
            venue_live_contact=True,
        )
        self.scoped_rows = list(scoped_rows)
        self.fault, self.global_fault = fault, global_fault
        self.requests = []

    def get(
        self,
        *,
        endpoint,
        auth_required,
        pretrade_decision_id,
        get_cache_policy=GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
    ):
        self.requests.append((endpoint, pretrade_decision_id, get_cache_policy))
        result = replace(
            self.base.get(
                endpoint=endpoint,
                auth_required=auth_required,
                pretrade_decision_id=pretrade_decision_id,
                get_cache_policy=get_cache_policy,
            ),
            data_safety_source_kind=DataSourceKind.REAL.value,
        )
        scoped = endpoint.startswith(ENDPOINT_ACCOUNT_POSITIONS + "?")
        if scoped:
            result = replace(result, payload={"code": "0", "data": self.scoped_rows})
        fault = (
            self.fault
            if scoped
            else (self.global_fault if endpoint == ENDPOINT_ACCOUNT_POSITIONS else None)
        )
        if fault:
            result = fault(result)
        return result


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("Synthetic proof must not open sockets")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket, "create_connection", deny)


def prove(port, order=None):
    return consumer.prove_immediate_pre_mutation_freshness_for_actual_venue_post_v1(
        envelope=order or envelope(), read_only_get_transport=port, pretrade_decision_id=DECISION
    )


@pytest.mark.parametrize(
    "fault",
    [
        lambda r: replace(r, payload={"code": "51000", "data": []}),
        lambda r: replace(r, http_status=401),
        lambda r: replace(r, auth_header_sent=False),
        lambda r: replace(r, pretrade_decision_id="old-decision"),
        lambda r: replace(
            r, acquired_at_utc=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        ),
        lambda r: replace(
            r, acquired_at_utc=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        ),
        lambda r: replace(r, historical_reuse=True),
        lambda r: replace(r, endpoint=ENDPOINT_ACCOUNT_POSITIONS),
        lambda r: replace(r, method="POST"),
        lambda r: replace(r, payload={"code": "0", "data": [row("NaN")]}),
        lambda r: replace(r, payload={"code": "0", "data": [{"instId": _bound().venue_native_id}]}),
        lambda r: replace(r, payload={"code": "0", "data": [None]}),
        lambda r: replace(r, data_safety_source_kind=None),
    ],
)
def test_scoped_unknown_never_becomes_flat_or_pass(fault):
    proof = prove(Port(fault=fault))
    assert proof.all_required_pre_post_gates_pass is False
    assert proof.position_state_fresh is False
    assert proof.position_truth == "UNKNOWN"


@pytest.mark.parametrize(
    "side,quantity", [("net", "2"), ("net", "-2"), ("long", "2"), ("short", "2")]
)
def test_fresh_bound_position_is_not_new_entry_admission(side, quantity):
    rows = [row(quantity, side=side)]
    proof = prove(Port(global_rows=rows, scoped_rows=rows))
    assert proof.position_state_fresh is True
    assert proof.position_truth == "BOUND_INSTRUMENT_OPEN"
    assert proof.all_required_pre_post_gates_pass is False


def test_account_wide_foreign_open_cannot_be_hidden_by_scoped_flat():
    proof = prove(Port(global_rows=[row(native="BTC-USDT-SWAP")]))
    assert proof.position_truth == "FOREIGN_OPEN_POSITION_MAX_POSITIONS_1"
    assert proof.all_required_pre_post_gates_pass is False


def test_changed_observations_require_original_reconciliation_not_flat_guess():
    proof = prove(Port(global_rows=[row("2")], scoped_rows=[]))
    assert proof.all_required_pre_post_gates_pass is False
    assert proof.position_state_fresh is True
    assert proof.position_observations_consistent is False
    assert proof.position_truth == "UNKNOWN"


@pytest.mark.parametrize("rows", [[], [row("0")], [row("0", side="long"), row("0", side="short")]])
def test_valid_empty_or_zero_rows_preserve_flat_semantics(rows):
    port = Port(global_rows=rows, scoped_rows=rows)
    order = envelope()
    before = order.to_runtime_json_v1()
    proof = prove(port, order)
    assert proof.position_state_fresh is True
    assert proof.position_truth == "FLAT"
    assert proof.all_required_pre_post_gates_pass is True
    assert order.to_runtime_json_v1() == before
    assert len(port.requests) == 10
    assert all(mode == GET_CACHE_POLICY_DECISION_BOUND_SNAPSHOT for _, _, mode in port.requests)
    assert proof.new_entry_position_admissible is True
    assert proof.position_source_binding["account_wide"]["endpoint"] == ENDPOINT_ACCOUNT_POSITIONS
    assert proof.position_source_binding["bound_instrument"]["acquisition_decision_id"] == DECISION
    assert proof.position_source_binding["envelope_digest"] == order.envelope_digest


@pytest.mark.parametrize(
    "bad_row",
    [
        row(1),
        row(True),
        row(""),
        row(" 1"),
        row("Infinity"),
        row("-1", side="short"),
        {**row(), "posSide": "unknown"},
        {**row(), "mgnMode": "unknown"},
    ],
)
def test_malformed_account_wide_rows_are_not_ignored(bad_row):
    proof = prove(Port(global_rows=[bad_row]))
    assert proof.position_state_fresh is False
    assert proof.position_truth == "UNKNOWN"
    assert proof.all_required_pre_post_gates_pass is False


def test_duplicate_position_identity_is_unresolved():
    rows = [row("0"), row("0")]
    proof = prove(Port(global_rows=rows, scoped_rows=rows))
    assert "POSITION_DUPLICATE_IDENTITY" in proof.reason_codes
    assert proof.all_required_pre_post_gates_pass is False


def test_hedge_legs_do_not_cancel_into_flat():
    rows = [row("2", side="long"), row("2", side="short")]
    proof = prove(Port(global_rows=rows, scoped_rows=rows))
    assert proof.position_state_fresh is True
    assert proof.position_truth == "BOUND_INSTRUMENT_OPEN"
    assert proof.new_entry_position_admissible is False


def test_tenth_read_cannot_refresh_the_original_common_acquisition(monkeypatch):
    later = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    monkeypatch.setattr(consumer, "utc_now_iso_v1", lambda: later)
    proof = prove(Port())
    assert "ACQUISITION_STALE" in proof.reason_codes
    assert proof.full_pretrade_conjunction_pass is False
    assert proof.account_state_fresh is False
    assert proof.all_required_pre_post_gates_pass is False


def test_common_datasafety_is_its_own_predicate():
    port = Port(global_fault=lambda r: replace(r, data_safety_source_kind=None))
    proof = prove(port)
    assert "COMMON_DATASAFETY_NOT_SATISFIED" in proof.reason_codes
    assert proof.full_pretrade_conjunction_pass is False
    assert proof.all_required_pre_post_gates_pass is False


def test_close_keeps_its_original_separate_position_admission():
    proof = prove(Port(), envelope(reduce_only=True))
    assert proof.new_entry_position_admissible is False
    assert proof.all_required_pre_post_gates_pass is False
    assert "CLOSE_REQUIRES_ORIGINAL_POSITION_ADMISSION" in proof.reason_codes


def test_proof_scope_does_not_assert_original_account_identity():
    proof = prove(Port())
    assert proof.scope == "PREPOST_FRESHNESS_POSITION_AND_VENUE_QUANTITY_ONLY"
    assert proof.account_identity_binding_status == "NOT_ASSESSED"


def test_original_post_caller_preserves_reason_before_any_durable_go_or_send(tmp_path, monkeypatch):
    from src.ops.governed_productive_account_equity_authority_producer_v1 import (
        current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 as caller,
    )
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        _clean_post_integrity,
    )

    def forbid(*args, **kwargs):
        raise AssertionError("Admission deny must precede durable GO and send")

    monkeypatch.setattr(caller, "persist_durable_post_owner_go_consume_v1", forbid)
    monkeypatch.setattr(
        caller,
        "attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1",
        forbid,
    )
    rows = [row("2")]
    order = envelope()
    read_transport = Port(global_rows=rows, scoped_rows=rows)
    account = read_transport.base.payloads[ENDPOINT_ACCOUNT_CONFIG]["data"][0]["uid"]
    with pytest.raises(
        caller.CurrentProductiveActualVenuePostError, match="NEW_ENTRY_REQUIRES_ACCOUNT_FLAT"
    ):
        caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
            owner_go=caller.OWNER_GO,
            baseline_origin_main_sha=caller.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            envelope=order,
            store_root=tmp_path,
            perform_real_venue_post=True,
            k1_backend=object(),
            read_only_get_transport=read_transport,
            post_pending_context=synthetic_current_post_pending_context_v1(order, account=account),
            execution_integrity_backend=_clean_post_integrity(),
        )
    assert not list(tmp_path.glob("*.json"))
