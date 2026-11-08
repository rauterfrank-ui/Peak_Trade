"""Actual later POST consumer of original current venue quantity sources."""

import pytest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

from tests.ops.test_n1_original_plan_origin_v1 import seed_with_origin
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
)
from tests.ops.test_prepost_original_budget_context_v1 import AccountPort, caller, execute
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_MAX_SIZE,
    ENDPOINT_PUBLIC_INSTRUMENTS,
)


@pytest.mark.parametrize("field", ["maxBuy", "maxMktSz"])
def test_actual_post_rejects_current_zero_quantity_limit_before_go_or_submit(
    tmp_path, monkeypatch, field
):
    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    args = dict(
        envelope=envelope,
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=host.owner.execution_plan_context_v1(rid, envelope),
    )
    port = AccountPort(args)
    endpoint = ENDPOINT_ACCOUNT_MAX_SIZE if field == "maxBuy" else ENDPOINT_PUBLIC_INSTRUMENTS
    row = next(
        row
        for row in port.base.payloads[endpoint]["data"]
        if row["instId"] == envelope.instrument_id
    )
    row[field] = "0"
    before = host.owner._store.sequence
    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="QUANTITY"):
            execute(args, tmp_path, port=port)
        assert host.owner._store.sequence == before
        assert host.owner.execution_links_v1()[rid]["identity"] is None
        assert host.owner.active_sum_v1() > 0
        assert not (tmp_path / "send/full_core_external_effect_permit_consume_v1.json").exists()
        assert not (
            tmp_path
            / "send/full_core_current_productive_actual_venue_post_owner_go_consume_v1.json"
        ).exists()
        assert len(port.requests) == 10
    finally:
        host.close()


@pytest.mark.parametrize("entry", ["public", "private"])
@pytest.mark.parametrize("source", ["missing", "foreign"])
def test_actual_http_cannot_bypass_current_quantity_context(tmp_path, entry, source):
    from tests.ops.test_original_permit_transport_abort_v1 import raw_claim
    from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
        _handle,
    )
    from tests.ops._current_post_safety_fixture_v1 import synthetic_current_post_quantity_context_v1
    from tests.ops.test_prepost_original_budget_context_v1 import rebuild
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
    context = (
        synthetic_current_post_quantity_context_v1(rebuild(order, quantity="2"))
        if source == "foreign"
        else None
    )
    http = FullCoreProductiveHttpTradeOrderTransportV1(
        handle=_handle(),
        signing_handle=object(),
        post_safety_context=resolve_current_post_safety_context_v1(order, stage="TEST"),
        transport_attempt=claim,
        post_quantity_context=context,
    )
    with pytest.raises(FullCoreProductiveHttpPostError, match="POST_QUANTITY"):
        if entry == "private":
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


@pytest.mark.parametrize("side", ["buy", "sell"])
@pytest.mark.parametrize("kind", ["market", "limit"])
@pytest.mark.parametrize("limit", ["2", "1.999", "0"])
def test_current_envelope_uses_exact_native_side_and_order_type_limits(side, kind, limit):
    from tests.ops.test_prepost_position_source_admission_v1 import envelope as make_envelope
    from tests.ops._current_post_safety_fixture_v1 import synthetic_current_post_quantity_context_v1
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_venue_quantity_v1 import (
        CurrentPostVenueQuantityError,
    )

    order = make_envelope(
        side=side, order_type=kind, quantity="2", price="10" if kind == "limit" else ""
    )
    context = synthetic_current_post_quantity_context_v1(order)
    public, private = (
        json.loads(context.public_source.payload_json),
        json.loads(context.private_source.payload_json),
    )
    p = next(r for r in public["data"] if r["instId"] == order.instrument_id)
    q = next(r for r in private["data"] if r["instId"] == order.instrument_id)
    p.update(maxMktSz="0", maxLmtSz="0")
    q.update(maxBuy="0", maxSell="0")
    public_field = "maxMktSz" if kind == "market" else "maxLmtSz"
    private_field = "maxBuy" if side == "buy" else "maxSell"
    p[public_field] = q[private_field] = limit
    context = replace(
        context,
        public_source=replace(context.public_source, payload_json=json.dumps(public)),
        private_source=replace(context.private_source, payload_json=json.dumps(private)),
    )
    before = order.to_runtime_json_v1()
    if limit == "2":
        proof = context.inspect_v1(envelope=order, stage="TEST")
        assert proof["selected_private_field"] == private_field
        assert proof["selected_public_field"] == public_field
        assert proof["final_native_quantity"] == "2"
    else:
        with pytest.raises(CurrentPostVenueQuantityError, match="EXCEEDS"):
            context.inspect_v1(envelope=order, stage="TEST")
    assert order.to_runtime_json_v1() == before


@pytest.mark.parametrize(
    "fault",
    [
        "foreign_context",
        "missing_field",
        "negative",
        "nan",
        "boolean",
        "duplicate",
        "foreign_acquisition",
        "price",
        "stale",
    ],
)
def test_unknown_or_foreign_quantity_sources_never_supply_positive_admission(fault):
    from tests.ops.test_prepost_position_source_admission_v1 import envelope as make_envelope
    from tests.ops._current_post_safety_fixture_v1 import synthetic_current_post_quantity_context_v1
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_venue_quantity_v1 import (
        CurrentPostVenueQuantityError,
    )

    order = make_envelope(order_type="limit", price="10")
    context = synthetic_current_post_quantity_context_v1(order)
    private = json.loads(context.private_source.payload_json)
    row = next(r for r in private["data"] if r["instId"] == order.instrument_id)
    if fault == "foreign_context":
        context = replace(context, envelope=make_envelope(quantity="2"))
    elif fault == "missing_field":
        del row["maxSell"]
    elif fault in {"negative", "nan", "boolean"}:
        row["maxBuy"] = {"negative": "-1", "nan": "NaN", "boolean": True}[fault]
    elif fault == "duplicate":
        private["data"].append(dict(row))
    elif fault == "foreign_acquisition":
        context = replace(context, acquisition_decision_id="foreign")
    elif fault == "price":
        context = replace(
            context,
            private_source=replace(
                context.private_source,
                endpoint=context.private_source.endpoint.replace("px=10", "px=11"),
            ),
        )
    else:
        old = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        context = replace(
            context, public_source=replace(context.public_source, acquired_at_utc=old)
        )
    context = replace(
        context, private_source=replace(context.private_source, payload_json=json.dumps(private))
    )
    with pytest.raises(CurrentPostVenueQuantityError):
        context.inspect_v1(envelope=order, stage="TEST")


def test_lower_entry_cannot_mint_without_actual_current_quantity_sources(tmp_path):
    from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
        _envelope,
        _FakeKeychainBackend,
        _persist_post_go,
    )
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 as lower,
    )

    _persist_post_go(tmp_path)
    probe = lower.OneShotJoinProbeV1()
    with pytest.raises(
        lower.CurrentProductiveOneShotFreshEnvelopeJoinError, match="POST_QUANTITY_CONTEXT_REQUIRED"
    ):
        lower.attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
            envelope=_envelope(),
            post_owner_go=lower.POST_OWNER_GO,
            store_root=tmp_path,
            k1_backend=_FakeKeychainBackend(),
            probe=probe,
        )
    assert not probe.permit_minted and probe.http_post_attempts == 0
    assert not (tmp_path / "full_core_external_effect_permit_consume_v1.json").exists()


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
def test_same_original_acquisition_is_checked_again_at_real_later_consumers(
    tmp_path, monkeypatch, phase
):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_n1_venue_quantity_limit_admission_v1 as kernel,
        envelope_bound_external_effect_send_seam_v1 as seam,
    )
    from tests.ops.test_prepost_original_budget_context_v1 import lower, _clean_post_integrity
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        _FakeKeychainBackend,
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

    def expire():
        monkeypatch.setattr(
            kernel,
            "utc_now_iso_v1",
            lambda: (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        )

    def wrap(target, name):
        original = getattr(target, name)

        def wrapped(*a, **kw):
            result = original(*a, **kw)
            expire()
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
                expire()
            return super().copy_matching_generic_password_value_data_v1(**kw)

    class Opener:
        def open(self, *a, **kw):
            from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
                FullCoreCurrentPostQuantityVetoError,
            )

            calls.append("possible_socket")
            raise FullCoreCurrentPostQuantityVetoError("POST_QUANTITY_FORGED_AFTER_BOUNDARY")

    def factory():
        if phase == "opener_factory":
            expire()
        return Opener()

    port = AccountPort(args, after_last=expire if phase == "after_gets" else None)
    held = host.owner.active_sum_v1()
    sequence = host.owner._store.sequence
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
