"""Current native contract constraints at original actual POST consumers."""

from dataclasses import replace
from decimal import Decimal, localcontext
from datetime import datetime, timezone
import json

import pytest

from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
    synthetic_current_post_quantity_context_v1,
)
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from tests.ops.test_prepost_original_budget_context_v1 import (
    AccountPort,
    caller,
    execute,
    no_network as no_network,
)
from tests.ops.test_prepost_position_source_admission_v1 import envelope
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_venue_quantity_v1 import (
    CurrentPostVenueQuantityError,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_PUBLIC_INSTRUMENTS,
)


def current_row(row):
    row.update(state="live", minSz="0.001", lotSz="0.001", tickSz="0.01", upcChg=[])
    return row


def context_with_row(order, **changes):
    context = synthetic_current_post_quantity_context_v1(order)
    payload = json.loads(context.public_source.payload_json)
    row = next(r for r in payload["data"] if r["instId"] == order.instrument_id)
    row["instType"] = "SWAP" if order.instrument_id.endswith("-SWAP") else "FUTURES"
    current_row(row).update(changes)
    return replace(
        context,
        public_source=replace(context.public_source, payload_json=json.dumps(payload)),
    )


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"minSz": "2"}, "BELOW_MINIMUM"),
        ({"lotSz": "2"}, "LOT_STEP"),
        ({"tickSz": "0.1"}, "PRICE_STEP"),
        ({"state": "suspend"}, "INSTRUMENT_NOT_LIVE"),
    ],
)
def test_current_constraints_reject_an_unchanged_order(change, reason):
    order = envelope(order_type="limit", price="10.03")
    context = context_with_row(order, **change)
    original = order.to_runtime_json_v1()
    with pytest.raises(CurrentPostVenueQuantityError, match=reason):
        context.inspect_v1(envelope=order, stage="CONSTRAINT_PROOF")
    assert order.to_runtime_json_v1() == original


@pytest.mark.parametrize("fault", ["minimum", "lot", "state"])
def test_actual_upper_entry_rejects_before_go_budget_or_permit(tmp_path, monkeypatch, fault):
    from tests.ops.test_n1_original_plan_origin_v1 import seed_with_origin

    host, rid, _, order, _, _ = seed_with_origin(tmp_path, monkeypatch)
    args = dict(
        envelope=order,
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=host.owner.execution_plan_context_v1(rid, order),
    )
    port = AccountPort(args)
    row = next(
        r
        for r in port.base.payloads[ENDPOINT_PUBLIC_INSTRUMENTS]["data"]
        if r["instId"] == order.instrument_id
    )
    current_row(row)
    if fault == "state":
        row["state"] = "suspend"
    else:
        row["minSz" if fault == "minimum" else "lotSz"] = str(Decimal(order.quantity) * 2)
    sequence = host.owner._store.sequence
    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="QUANTITY"):
            execute(args, tmp_path, port=port)
        assert host.owner._store.sequence == sequence
        assert host.owner.execution_links_v1()[rid]["identity"] is None
        assert host.owner.active_sum_v1() > 0
        assert len(port.requests) == 10
        assert not (tmp_path / "send/full_core_external_effect_permit_consume_v1.json").exists()
        assert not (
            tmp_path
            / "send/full_core_current_productive_actual_venue_post_owner_go_consume_v1.json"
        ).exists()
    finally:
        host.close()


@pytest.mark.parametrize("side", ["buy", "sell"])
@pytest.mark.parametrize("kind", ["market", "limit"])
@pytest.mark.parametrize("quantity", ["0.5", "1.50"])
def test_native_minimum_and_lattice_preserve_exact_wire_values(side, kind, quantity):
    order = envelope(
        side=side, order_type=kind, quantity=quantity, price="10.10" if kind == "limit" else ""
    )
    context = context_with_row(order, minSz="0.5", lotSz="0.25", tickSz="0.05")
    before = order.to_runtime_json_v1()
    result = context.inspect_v1(envelope=order, stage="EXACT_NATIVE_ORDER")
    assert result["final_native_quantity"] == quantity
    assert result["order_constraints"]["minimum_native_quantity"] == "0.5"
    assert result["order_constraints"]["native_quantity_step"] == "0.25"
    assert result["order_constraints"]["limit_price_step"] == (
        "0.05" if kind == "limit" else "NOT_APPLICABLE_MARKET"
    )
    assert order.to_runtime_json_v1() == before


@pytest.mark.parametrize("field", ["minSz", "lotSz", "tickSz"])
@pytest.mark.parametrize("value", [None, "", "0", "-1", "NaN", "Infinity", True, 0.01, " 1"])
def test_unknown_current_numeric_contract_metadata_is_not_admitted(field, value):
    order = envelope(order_type="limit", price="10")
    context = context_with_row(order, **{field: value})
    with pytest.raises(CurrentPostVenueQuantityError, match="UNPROVEN"):
        context.inspect_v1(envelope=order, stage="UNKNOWN_METADATA")


@pytest.mark.parametrize("state", [None, "", "preopen", "rebase", "post_only", "pre_market"])
def test_normal_market_or_limit_entry_requires_original_live_instrument_state(state):
    order = envelope()
    with pytest.raises(CurrentPostVenueQuantityError, match="INSTRUMENT_NOT_LIVE"):
        context_with_row(order, state=state).inspect_v1(envelope=order, stage="STATE")


@pytest.mark.parametrize("extra_digit,allowed", [("", True), ("1", False)])
def test_lattice_check_does_not_round_to_decimal_context_precision(extra_digit, allowed):
    order = envelope(quantity="1.00000000000000000000000000001" + extra_digit)
    context = context_with_row(order, lotSz="0.00000000000000000000000000001")
    with localcontext() as precision:
        precision.prec = 6
        if allowed:
            context.inspect_v1(envelope=order, stage="EXACT_PRECISION")
        else:
            with pytest.raises(CurrentPostVenueQuantityError, match="LOT_STEP"):
                context.inspect_v1(envelope=order, stage="EXACT_PRECISION")


@pytest.mark.parametrize(
    "changes",
    [
        None,
        {},
        [None],
        [{}],
        [{"param": "unknown", "newValue": "1", "effTime": "1"}],
        [{"param": "minSz", "newValue": "0", "effTime": "1"}],
        [{"param": "minSz", "newValue": "1", "effTime": True}],
        [{"param": "minSz", "newValue": "1", "effTime": "-1"}],
        [{"param": "minSz", "newValue": "1", "effTime": "1.5"}],
    ],
)
def test_unknown_announced_rule_changes_require_source_clarification(changes):
    order = envelope()
    with pytest.raises(CurrentPostVenueQuantityError, match="UPCOMING_CHANGE"):
        context_with_row(order, upcChg=changes).inspect_v1(envelope=order, stage="UNKNOWN_CHANGE")


@pytest.mark.parametrize("param,new_value", [("minSz", "2"), ("tickSz", "0.1"), ("maxMktSz", "0")])
def test_announced_effective_time_invalidates_original_source_without_applying_future_values(
    monkeypatch, param, new_value
):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_n1_venue_quantity_limit_admission_v1 as source_owner,
    )

    order = envelope()
    context = context_with_row(order)
    now = datetime.now(timezone.utc)
    effective_ms = int(now.timestamp() * 1000) + 3000
    payload = json.loads(context.public_source.payload_json)
    row = next(r for r in payload["data"] if r["instId"] == order.instrument_id)
    row["upcChg"] = [{"param": param, "newValue": new_value, "effTime": str(effective_ms)}]
    context = replace(
        context, public_source=replace(context.public_source, payload_json=json.dumps(payload))
    )
    monkeypatch.setattr(source_owner, "utc_now_iso_v1", lambda: now.isoformat())
    assert context.inspect_v1(envelope=order, stage="BEFORE_CHANGE")["public_maximum"] == "1000000"
    boundary = datetime.fromtimestamp(effective_ms / 1000, timezone.utc)
    monkeypatch.setattr(source_owner, "utc_now_iso_v1", lambda: boundary.isoformat())
    with pytest.raises(CurrentPostVenueQuantityError, match="ANNOUNCED_CHANGE_EFFECTIVE"):
        context.inspect_v1(envelope=order, stage="AT_CHANGE")
    assert context.public_source.payload_json == json.dumps(payload)


@pytest.mark.parametrize("entry", ["public", "internal"])
def test_actual_http_port_cannot_bypass_current_lot_metadata(tmp_path, entry):
    from tests.ops.test_original_permit_transport_abort_v1 import raw_claim
    from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
        _handle,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_safety_veto_v1 import (
        resolve_current_post_safety_context_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
        _payload_from_envelope_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
        FullCoreProductiveHttpTradeOrderTransportV1,
        FullCoreProductiveHttpPostError,
    )

    claim, args, order = raw_claim(tmp_path)
    context = context_with_row(order, lotSz=str(Decimal(order.quantity) * 2))
    http = FullCoreProductiveHttpTradeOrderTransportV1(
        handle=_handle(),
        signing_handle=object(),
        transport_attempt=claim,
        post_safety_context=resolve_current_post_safety_context_v1(order, stage="TEST"),
        post_quantity_context=context,
    )
    with pytest.raises(FullCoreProductiveHttpPostError, match="POST_QUANTITY.*LOT_STEP"):
        if entry == "internal":
            http._perform_http_post_v1(payload=_payload_from_envelope_v1(order))
        else:
            http.post_trade_order(
                payload=_payload_from_envelope_v1(order),
                permit_id=args["permit_id"],
                envelope_id=order.envelope_id,
                envelope_digest=order.envelope_digest,
                one_shot_real_post=True,
            )
    assert http.post_count == 0
    claim.inspect_v1()


@pytest.mark.parametrize(
    "phase",
    [
        "after_gets",
        "after_go",
        "after_mint",
        "after_budget",
        "after_permit",
        "during_k1",
        "opener_factory",
        "after_socket",
    ],
)
def test_rule_change_during_same_call_preserves_original_transport_and_budget_boundaries(
    tmp_path, monkeypatch, phase
):
    from tests.ops.test_n1_original_plan_origin_v1 import seed_with_origin
    from tests.ops.test_prepost_original_budget_context_v1 import lower, _clean_post_integrity
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        _FakeKeychainBackend,
    )
    from tests.ops._current_post_safety_fixture_v1 import synthetic_current_post_pending_context_v1
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_n1_venue_quantity_limit_admission_v1 as source_owner,
        envelope_bound_external_effect_send_seam_v1 as seam,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, rid, _, order, _, _ = seed_with_origin(tmp_path, monkeypatch)
    args = dict(
        envelope=order,
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=host.owner.execution_plan_context_v1(rid, order),
    )
    effective_ms = int(datetime.now(timezone.utc).timestamp() * 1000) + 5000
    boundary = datetime.fromtimestamp(effective_ms / 1000, timezone.utc)

    def advance():
        monkeypatch.setattr(source_owner, "utc_now_iso_v1", lambda: boundary.isoformat())

    def wrap(target, name):
        original = getattr(target, name)

        def wrapped(*a, **kw):
            result = original(*a, **kw)
            advance()
            return result

        monkeypatch.setattr(target, name, wrapped)

    if phase == "after_go":
        wrap(caller, "persist_durable_post_owner_go_consume_v1")
    elif phase == "after_mint":
        wrap(lower, "issue_external_effect_permit_v1")
    elif phase == "after_budget":
        wrap(host.owner, "begin_execution_submit_v2")
    elif phase == "after_permit":
        wrap(seam, "persist_external_effect_durable_consume_v1")
    calls = []

    class Backend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kw):
            if phase == "during_k1":
                advance()
            return super().copy_matching_generic_password_value_data_v1(**kw)

    class Opener:
        def open(self, *a, **kw):
            from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
                FullCoreCurrentPostQuantityVetoError,
            )

            calls.append("possible_socket")
            advance()
            raise FullCoreCurrentPostQuantityVetoError("POST_QUANTITY_FORGED_AFTER_BOUNDARY")

    def factory():
        if phase == "opener_factory":
            advance()
        return Opener()

    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        order, account=host.owner.durable_scope_identity_v1()["account"]
    )
    port = AccountPort(args, after_last=advance if phase == "after_gets" else None)
    row = next(
        r
        for r in port.base.payloads[ENDPOINT_PUBLIC_INSTRUMENTS]["data"]
        if r["instId"] == order.instrument_id
    )
    current_row(row)["upcChg"] = [
        {
            "param": "minSz",
            "newValue": str(Decimal(order.quantity) * 2),
            "effTime": str(effective_ms),
        }
    ]
    held, sequence = host.owner.active_sum_v1(), host.owner._store.sequence
    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="POST_QUANTITY"):
            caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
                **args,
                owner_go=caller.OWNER_GO,
                baseline_origin_main_sha=caller.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                store_root=tmp_path / "send",
                evidence_root=tmp_path / "evidence",
                perform_real_venue_post=True,
                k1_backend=Backend(),
                opener_factory=factory,
                read_only_get_transport=port,
                execution_integrity_backend=_clean_post_integrity(),
            )
        assert calls == (["possible_socket"] if phase == "after_socket" else [])
        assert len(port.requests) == 10
        submitted = phase in {
            "after_budget",
            "after_permit",
            "during_k1",
            "opener_factory",
            "after_socket",
        }
        assert host.owner._store.sequence == sequence + int(submitted)
        assert host.owner.active_sum_v1() == held > 0
        record = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")["record"]
        if submitted:
            assert record["durable_state"] == (
                "SENT_INITIATED" if phase == "after_socket" else "ABORTED_BEFORE_TRANSPORT"
            )
            assert record["transport_attempt"]["phase"] == (
                "MAY_HAVE_SENT" if phase == "after_socket" else "ABORTED"
            )
        else:
            assert record is None
    finally:
        host.close()
