"""Original current price-limit source at actual POST; injected ports only."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import pytest

from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
)
from tests.ops.test_prepost_position_source_admission_v1 import (
    Port,
    envelope,
    no_network as no_network,
)
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_PUBLIC_PRICE_LIMIT,
    collect_fresh_pretrade_runtime_get_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_venue_quantity_v1 import (
    CurrentPostVenueQuantityError,
    capture_current_post_venue_quantity_v1,
)


def capture(order, *, change=None, result_change=None):
    port = Port()
    row = dict(
        instId=order.instrument_id,
        instType="SWAP",
        enabled=True,
        buyLmt="10.03",
        sellLmt="10.03",
        ts="1597026383085",
    )
    row.update(change or {})
    port.base.payloads[ENDPOINT_PUBLIC_PRICE_LIMIT] = {"code": "0", "data": [row]}
    results = {}
    collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id="current-native-price-band",
        instrument_id=order.instrument_id,
        td_mode=order.td_mode,
        limit_px=order.price,
        inst_type="SWAP",
        transport=port,
        require_collection=True,
        collected_results=results,
    )
    if result_change:
        results["price_limit"] = replace(results["price_limit"], **result_change)
    return (
        capture_current_post_venue_quantity_v1(
            envelope=order, results=results, acquisition_decision_id="current-native-price-band"
        ),
        results,
        port,
    )


@pytest.mark.parametrize(
    "side,change,reason",
    [
        ("buy", {"buyLmt": "10.02"}, "BUYLMT"),
        ("sell", {"sellLmt": "10.04"}, "SELLLMT"),
        ("buy", {"enabled": False}, "NOT_ACTIVE"),
        ("buy", {"ts": ""}, "TIMESTAMP"),
    ],
)
def test_current_limit_order_requires_its_original_side_price_band(side, change, reason):
    order = envelope(side=side, order_type="limit", price="10.03")
    original = order.to_runtime_json_v1()
    with pytest.raises(CurrentPostVenueQuantityError, match=reason):
        context, _, _ = capture(order, change=change)
        context.inspect_v1(envelope=order, stage="PRICE_BAND_COUNTERPROOF")
    assert order.to_runtime_json_v1() == original


@pytest.mark.parametrize(
    "side,price,allowed",
    [
        ("buy", "10.03", True),
        ("buy", "10.02", True),
        ("buy", "10.04", False),
        ("sell", "10.03", True),
        ("sell", "10.04", True),
        ("sell", "10.02", False),
    ],
)
def test_side_specific_boundary_and_equality_preserve_original_wire(side, price, allowed):
    order = envelope(side=side, order_type="limit", price=price)
    context, _, port = capture(order)
    before = order.to_runtime_json_v1()
    if allowed:
        result = context.inspect_v1(envelope=order, stage="SIDE_BOUND")
        assert result["price_band"]["selected_field"] == ("buyLmt" if side == "buy" else "sellLmt")
        assert result["price_band"]["selected_value"] == "10.03"
        assert result["price_band"]["ts_raw"] == "1597026383085"
        assert result["price_band"]["venue_timestamp_age_bound"] == "UNBOUND"
    else:
        with pytest.raises(CurrentPostVenueQuantityError, match="BUYLMT|SELLLMT"):
            context.inspect_v1(envelope=order, stage="SIDE_BOUND")
    assert len(port.requests) == 9
    assert order.to_runtime_json_v1() == before


@pytest.mark.parametrize(
    "side,change",
    [
        ("buy", {"sellLmt": "10.04"}),
        ("sell", {"buyLmt": "10.02"}),
        ("sell", {"sellLmt": "0"}),
    ],
)
def test_other_side_is_not_an_interval_bound_and_zero_is_not_replaced(side, change):
    order = envelope(side=side, order_type="limit", price="10.03")
    context, _, _ = capture(order, change=change)
    result = context.inspect_v1(envelope=order, stage="ORIGINAL_SIDE_ONLY")
    if change.get("sellLmt") == "0":
        assert result["price_band"]["selected_value"] == "0"


@pytest.mark.parametrize("field", ["buyLmt", "sellLmt"])
@pytest.mark.parametrize(
    "value", [None, "", True, 10.03, "-1", "NaN", "Infinity", "1e2", " 10", "1" * 41]
)
def test_unknown_raw_limit_prices_never_supply_positive_admission(field, value):
    order = envelope(order_type="limit", price="10.03")
    context, _, _ = capture(order, change={field: value})
    with pytest.raises(CurrentPostVenueQuantityError, match="PRICE_BAND"):
        context.inspect_v1(envelope=order, stage="UNKNOWN_PRICE")


@pytest.mark.parametrize("value", [None, "", "yes", 1, False])
def test_inactive_or_unknown_enabled_is_not_unlimited(value):
    order = envelope(order_type="limit", price="10.03")
    context, _, _ = capture(order, change={"enabled": value})
    with pytest.raises(CurrentPostVenueQuantityError, match="PRICE_BAND"):
        context.inspect_v1(envelope=order, stage="ENABLED")


@pytest.mark.parametrize("value", [None, True, "0", "-1", "1.5", " 1", "１"])
def test_venue_timestamp_is_an_original_unix_millisecond_field(value):
    order = envelope(order_type="limit", price="10.03")
    context, _, _ = capture(order, change={"ts": value})
    with pytest.raises(CurrentPostVenueQuantityError, match="TIMESTAMP"):
        context.inspect_v1(envelope=order, stage="VENUE_TIME")


@pytest.mark.parametrize(
    "change",
    [
        {"get_performed": False},
        {"method": "POST"},
        {"historical_reuse": True},
        {"data_safety_source_kind": None},
        {"auth_header_sent": True},
        {"http_status": 503},
        {"pretrade_decision_id": "foreign-current-decision"},
    ],
)
def test_capture_retains_original_get_datasafety_and_unsigned_public_provenance(change):
    order = envelope(order_type="limit", price="10.03")
    with pytest.raises(CurrentPostVenueQuantityError):
        capture(order, result_change=change)


@pytest.mark.parametrize(
    "fault",
    ["absent", "decision", "native", "inst_type", "duplicate", "query", "stale", "future", "code"],
)
def test_later_consumer_rechecks_original_price_source(fault):
    order = envelope(order_type="limit", price="10.03")
    context, _, _ = capture(order)
    source = context.price_band_source
    payload = json.loads(source.payload_json)
    if fault == "absent":
        source = None
    elif fault == "decision":
        source = replace(source, acquisition_decision_id="foreign")
    elif fault == "query":
        source = replace(source, endpoint=source.endpoint + "&px=10.03")
    elif fault in {"stale", "future"}:
        source = replace(
            source,
            acquired_at_utc=(
                datetime.now(timezone.utc) + timedelta(seconds=-30 if fault == "stale" else 30)
            ).isoformat(),
        )
    else:
        if fault == "native":
            payload["data"][0]["instId"] = "foreign"
        elif fault == "inst_type":
            payload["data"][0]["instType"] = "FUTURES"
        elif fault == "duplicate":
            payload["data"].append(dict(payload["data"][0]))
        else:
            payload["code"] = "51006"
        source = replace(source, payload_json=json.dumps(payload))
    context = replace(context, price_band_source=source)
    with pytest.raises(CurrentPostVenueQuantityError):
        context.inspect_v1(envelope=order, stage="LATER_SOURCE")


def test_source_is_detached_and_current_post_does_not_manufacture_canary_observation(monkeypatch):
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1 import (
        price_band_observation_v1 as original,
    )

    def deny(**kwargs):
        raise AssertionError("Current POST must use original current GET, not canary acquisition")

    monkeypatch.setattr(original, "acquire_fresh_price_band_observation_from_payload_v1", deny)
    order = envelope(order_type="limit", price="10.03")
    context, results, _ = capture(order, result_change={"body_sha256": "1" * 64})
    before = context.price_band_source
    results["price_limit"].payload["data"][0]["buyLmt"] = "0"
    result = context.inspect_v1(envelope=order, stage="DETACHED")
    assert context.price_band_source == before
    assert result["price_band"]["selected_value"] == "10.03"
    assert result["sources"]["price_band"]["response_body_sha256"] == "1" * 64
    assert result["sources"]["price_band"]["acquired_at_utc"] == before.acquired_at_utc
    assert (
        result["sources"]["price_band"]["acquisition_decision_id"] == before.acquisition_decision_id
    )


def test_market_has_no_fabricated_limit_price_comparison():
    order = envelope()
    context, _, _ = capture(order, change={"enabled": False, "buyLmt": "", "sellLmt": "", "ts": ""})
    assert context.price_band_source is None
    result = context.inspect_v1(envelope=order, stage="MARKET")
    assert result["price_band"]["status"] == "NOT_APPLICABLE_MARKET"
    assert order.price == ""


def test_actual_post_source_integrity_protects_both_original_price_owners():
    from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
        PROTECTED_CURRENT_PRODUCTIVE_POST_SLICE_SURFACE_PATHS,
    )

    for name in ("price_band_consumer_v1.py", "price_band_observation_v1.py"):
        assert (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/" + name
            in PROTECTED_CURRENT_PRODUCTIVE_POST_SLICE_SURFACE_PATHS
        )


@pytest.mark.parametrize(
    "side,price,allowed",
    [
        ("buy", "10", True),
        ("buy", "11", True),
        ("buy", "11.01", False),
        ("sell", "10", True),
        ("sell", "9", True),
        ("sell", "8.99", False),
    ],
)
def test_original_canary_source_owner_and_scalar_comparison_remain_intact(side, price, allowed):
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        DEFAULT_INSTRUMENT_ID,
        DEFAULT_INST_TYPE,
    )
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.price_band_consumer_v1 import (
        apply_fresh_price_band_pretrade_gate_v1,
        LiveCanaryPriceBandConsumerError,
    )

    args = dict(
        pretrade_decision_id="original-price-consumer-proof",
        payload={
            "code": "0",
            "data": [
                dict(
                    instId=DEFAULT_INSTRUMENT_ID,
                    instType=DEFAULT_INST_TYPE,
                    enabled=True,
                    buyLmt="11",
                    sellLmt="9",
                    ts="1597026383085",
                )
            ],
        },
        instrument_id=DEFAULT_INSTRUMENT_ID,
        side=side,
        planned_limit_px=price,
        price_domain="VENUE_LIMIT_PRICE",
        http_status=200,
        endpoint=ENDPOINT_PUBLIC_PRICE_LIMIT + "?instId=" + DEFAULT_INSTRUMENT_ID,
    )
    if allowed:
        assert apply_fresh_price_band_pretrade_gate_v1(**args)["ok"]
    else:
        with pytest.raises(LiveCanaryPriceBandConsumerError, match="BUYLMT|SELLLMT"):
            apply_fresh_price_band_pretrade_gate_v1(**args)


def limit_seed(tmp_path, monkeypatch):
    """Explicit synthetic LIMIT plan, accepted by the original durable plan writer.

    Keeps original sizing/intent references. Does not claim the natural N1
    producer emitted LIMIT or refresh its risk decision.
    """
    from tests.ops.test_n1_original_plan_origin_v1 import seed_with_origin
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        bind_final_order_envelope_from_venue_plan_v1,
    )

    host, rid, _, original_order, intent, plan = seed_with_origin(
        tmp_path, monkeypatch, origin=None
    )
    plan = replace(
        plan,
        order_type="limit",
        venue_native_payload={**plan.venue_native_payload, "ordType": "limit", "px": "10.03"},
    )
    order = bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref=original_order.admission_ref,
        provenance_ref=original_order.provenance_ref,
        creation_epoch=original_order.creation_epoch,
    )
    host.owner.bind_execution_plan_v1(rid, order, canonical_intent=intent, venue_plan=plan)
    return host, dict(
        envelope=order,
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=host.owner.execution_plan_context_v1(rid, order),
    )


@pytest.mark.parametrize("invalid", [False, True])
def test_actual_upper_limit_entry_obeys_current_band_before_go_budget_and_mint(
    tmp_path, monkeypatch, invalid
):
    from tests.ops.test_prepost_original_budget_context_v1 import AccountPort, caller, execute

    host, args = limit_seed(tmp_path, monkeypatch)
    port = AccountPort(args)
    port.base.payloads[ENDPOINT_PUBLIC_PRICE_LIMIT]["data"][0]["buyLmt"] = (
        "10.02" if invalid else "10.03"
    )
    sequence, held = host.owner._store.sequence, host.owner.active_sum_v1()
    try:
        if invalid:
            with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="BUYLMT"):
                execute(args, tmp_path, port=port)
            assert host.owner._store.sequence == sequence
            assert not (
                tmp_path
                / "send/full_core_current_productive_actual_venue_post_owner_go_consume_v1.json"
            ).exists()
            assert not (tmp_path / "send/full_core_external_effect_permit_consume_v1.json").exists()
            assert len(port.requests) == 10
        else:
            result = execute(args, tmp_path, port=port)
            assert result.real_venue_post_attempted == "true"
            assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
            assert (
                len(port.requests) == 11
            )  # ten pre-mutation plus original subsequent position read
        assert host.owner.active_sum_v1() == held > 0
    finally:
        host.close()


@pytest.mark.parametrize("entry", ["public", "internal"])
@pytest.mark.parametrize("side", ["buy", "sell"])
def test_both_actual_http_entries_reject_original_limit_order_outside_its_side_band(
    tmp_path, entry, side
):
    from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
        _permit,
        _handle,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        persist_external_effect_durable_consume_v1,
        claim_original_permit_transport_attempt_v1,
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

    order = envelope(side=side, order_type="limit", price="10.03")
    context, _, _ = capture(order, change={"buyLmt": "10.02", "sellLmt": "10.04"})
    permit = _permit(order)
    persist_external_effect_durable_consume_v1(
        store_root=tmp_path,
        permit=permit,
        envelope=order,
        durable_state="SENT_INITIATED",
        post_count=1,
        outcome="UNKNOWN",
    )
    args = dict(
        store_root=tmp_path,
        permit_id=permit.permit_id,
        envelope_id=order.envelope_id,
        envelope_digest=order.envelope_digest,
    )
    claim = claim_original_permit_transport_attempt_v1(**args)
    http = FullCoreProductiveHttpTradeOrderTransportV1(
        handle=_handle(),
        signing_handle=object(),
        transport_attempt=claim,
        post_safety_context=resolve_current_post_safety_context_v1(order, stage="TEST"),
        post_quantity_context=context,
    )
    with pytest.raises(FullCoreProductiveHttpPostError, match="BUYLMT|SELLLMT"):
        if entry == "internal":
            http._perform_http_post_v1(payload=_payload_from_envelope_v1(order))
        else:
            http.post_trade_order(
                payload=_payload_from_envelope_v1(order),
                permit_id=permit.permit_id,
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
def test_price_source_age_at_later_original_consumers_preserves_budget_and_transport_uncertainty(
    tmp_path, monkeypatch, phase
):
    from tests.ops.test_prepost_original_budget_context_v1 import (
        AccountPort,
        caller,
        lower,
        _clean_post_integrity,
    )
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
    from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
        NUMERIC_EQUITY_TTL_SECONDS,
    )

    host, args = limit_seed(tmp_path, monkeypatch)
    order = args["envelope"]
    now = datetime.now(timezone.utc)

    def advance():
        monkeypatch.setattr(
            source_owner, "utc_now_iso_v1", lambda: (now + timedelta(seconds=2)).isoformat()
        )

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

    class PortWithOlderBand(AccountPort):
        def get(self, **kw):
            result = super().get(**kw)
            if kw["endpoint"].startswith(ENDPOINT_PUBLIC_PRICE_LIMIT + "?"):
                result = replace(
                    result,
                    acquired_at_utc=(
                        now - timedelta(seconds=NUMERIC_EQUITY_TTL_SECONDS - 1)
                    ).isoformat(),
                )
            return result

    class Backend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kw):
            if phase == "during_k1":
                advance()
            return super().copy_matching_generic_password_value_data_v1(**kw)

    calls = []

    class Opener:
        def open(self, *a, **kw):
            from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
                FullCoreCurrentPostQuantityVetoError,
            )

            calls.append("possible_socket")
            advance()
            raise FullCoreCurrentPostQuantityVetoError(
                "POST_QUANTITY_PRICE_BAND_FORGED_AFTER_SOCKET"
            )

    def factory():
        if phase == "opener_factory":
            advance()
        return Opener()

    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        order, account=host.owner.durable_scope_identity_v1()["account"]
    )
    port = PortWithOlderBand(args, after_last=advance if phase == "after_gets" else None)
    sequence, held = host.owner._store.sequence, host.owner.active_sum_v1()
    try:
        with pytest.raises(
            caller.CurrentProductiveActualVenuePostError, match="ACQUISITION_STALE|POST_QUANTITY"
        ):
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
