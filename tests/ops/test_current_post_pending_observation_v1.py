"""Original observer session to actual POST; all ports explicitly synthetic."""

import pytest
from dataclasses import replace
from datetime import datetime, timezone, timedelta
import time
from tests.ops.test_n1_original_plan_origin_v1 import seed_with_origin
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
    synthetic_current_post_quantity_context_v1,
    synthetic_current_post_pending_context_v1,
)
from tests.ops.test_prepost_original_budget_context_v1 import (
    AccountPort,
    caller,
    lower,
    _clean_post_integrity,
)
from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    _FakeKeychainBackend,
    _TimeoutOpener,
)


@pytest.mark.parametrize("entry", ["upper", "lower"])
def test_actual_post_cannot_use_missing_pending_observation_as_a_clear_account(
    tmp_path, monkeypatch, entry
):
    from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
        _persist_post_go,
    )

    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    args = dict(
        envelope=envelope,
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=host.owner.execution_plan_context_v1(rid, envelope),
    )
    sequence = host.owner._store.sequence
    try:
        if entry == "upper":
            with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="POST_PENDING"):
                caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
                    **args,
                    owner_go=caller.OWNER_GO,
                    baseline_origin_main_sha=caller.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                    store_root=tmp_path / "send",
                    evidence_root=tmp_path / "evidence",
                    perform_real_venue_post=True,
                    k1_backend=_FakeKeychainBackend(),
                    opener_factory=lambda: _TimeoutOpener(),
                    read_only_get_transport=AccountPort(args),
                    execution_integrity_backend=_clean_post_integrity(),
                )
        else:
            _persist_post_go(tmp_path / "send")
            with pytest.raises(
                lower.CurrentProductiveOneShotFreshEnvelopeJoinError, match="POST_PENDING"
            ):
                lower.attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
                    **args,
                    post_owner_go=lower.POST_OWNER_GO,
                    store_root=tmp_path / "send",
                    k1_backend=_FakeKeychainBackend(),
                    opener_factory=lambda: _TimeoutOpener(),
                    post_quantity_context=synthetic_current_post_quantity_context_v1(envelope),
                )
        assert host.owner._store.sequence == sequence
        assert host.owner.execution_links_v1()[rid]["identity"] is None
        assert host.owner.active_sum_v1() > 0
        assert not (tmp_path / "send/full_core_external_effect_permit_consume_v1.json").exists()
    finally:
        host.close()


def observer_context(order, *, fault=None, account="injected-observer-account"):
    from tests.ops.test_account_observation_startup_source_v1 import InjectedTransport, credential
    from tests.ops.test_portfolio_budget_host_v1 import _fetch
    from src.ops.okx_eea_private_account_state_runtime_v1.startup_source_v1 import (
        AccountObservationSourceV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_pending_observation_v1 import (
        capture_current_post_pending_v1,
    )

    class Port(InjectedTransport):
        def get(self, **request):
            result = replace(
                super().get(**request),
                pretrade_decision_id=request["pretrade_decision_id"],
                acquired_at_utc=datetime.now(timezone.utc).isoformat(),
            )
            if fault in {"conditional", "oco", "trigger", "move_order_stop"} and request[
                "endpoint"
            ].endswith("ordType=" + fault):
                return replace(
                    result, payload={"code": "0", "data": [{"algoId": "synthetic-existing"}]}
                )
            if fault == "ordinary" and "/orders-pending?" in request["endpoint"]:
                return replace(
                    result, payload={"code": "0", "data": [{"ordId": "synthetic-existing"}]}
                )
            if fault == "continuation":
                return replace(result, payload={**result.payload, "hasMore": True})
            if fault == "missing_acquisition":
                return replace(result, acquired_at_utc="")
            if fault == "foreign_acquisition":
                return replace(result, pretrade_decision_id="foreign-session")
            if fault == "stale_acquisition":
                return replace(
                    result,
                    acquired_at_utc=(
                        datetime.now(timezone.utc) - timedelta(seconds=10)
                    ).isoformat(),
                )
            return result

    port = Port(fetch=_fetch(uid=account))
    source = AccountObservationSourceV1(
        credential=credential(),
        transport=port,
        expected_account_identity=account,
        session_id="current-pending-session",
        clock=(lambda: time.time() - 10) if fault == "stale_host" else time.time,
    )
    source.collect_v1(instrument_ids_by_native_id={order.instrument_id: "synthetic-instrument"})
    return capture_current_post_pending_v1(envelope=order, source=source), port


def test_original_observer_and_actual_post_keep_separate_existing_request_budgets(
    tmp_path, monkeypatch
):
    host, rid, _, order, _, _ = seed_with_origin(tmp_path, monkeypatch)
    account = host.owner.durable_scope_identity_v1()["account"]
    context, port = observer_context(order, account=account)
    args = dict(
        envelope=order,
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=host.owner.execution_plan_context_v1(rid, order),
        post_pending_context=context,
    )
    from tests.ops.test_prepost_original_budget_context_v1 import execute

    reads = AccountPort(args)
    try:
        result = execute(args, tmp_path, port=reads)
        assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
        assert len(port.calls) == 10  # original baseline six plus original four algo queries
        assert (
            len(reads.requests) == 11
        )  # ten pre-mutation reads plus original follow-on position snapshot
        assert reads.requests[-1][0].startswith("/api/v5/account/positions?")
        assert reads.requests[-1][1] == order.instrument_id
        proof = context.inspect_v1(envelope=order, stage="TEST", expected_account=account)
        assert len(proof["endpoints"]) == 6  # config plus ordinary and four supported algo types
        assert all("instId=" not in row["endpoint"] for row in port.calls)
        assert context.observation is context.source.pending_observation_v1()
    finally:
        context.source.close()
        host.close()


@pytest.mark.parametrize(
    "fault", ["ordinary", "conditional", "oco", "trigger", "move_order_stop", "continuation"]
)
def test_original_source_cannot_publish_a_clear_observation_with_pending_or_unknown_coverage(fault):
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        _envelope,
    )

    with pytest.raises(ValueError):
        observer_context(_envelope(), fault=fault)


@pytest.mark.parametrize(
    "fault",
    [
        "missing_acquisition",
        "foreign_acquisition",
        "stale_acquisition",
        "stale_host",
        "closed",
        "transport",
        "credential",
        "account",
        "session",
        "new_read",
        "new_observation",
        "foreign_envelope",
        "unsupported_future",
    ],
)
def test_same_original_observation_never_survives_foreign_stale_or_closed_inputs(fault):
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        _envelope,
    )
    from tests.ops.test_prepost_original_budget_context_v1 import rebuild
    from tests.ops.test_account_observation_startup_source_v1 import credential, InjectedTransport
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_pending_observation_v1 import (
        CurrentPostPendingObservationError,
    )

    order = _envelope()
    context, port = observer_context(order, fault=fault)
    try:
        if fault == "closed":
            context.source.close()
        elif fault == "transport":
            context.source.transport = InjectedTransport()
        elif fault == "credential":
            context.source.credential = credential()
        elif fault == "account":
            context.source.expected_account_identity = "foreign"
        elif fault == "session":
            context.source.session_id = "foreign"
        elif fault == "new_read":
            context.source("/api/v5/account/positions", {"instType": "SWAP"})
        elif fault == "new_observation":
            context.source.collect_v1(
                instrument_ids_by_native_id={order.instrument_id: "synthetic-instrument"}
            )
        elif fault == "foreign_envelope":
            order = rebuild(order, quantity="2")
        elif fault == "unsupported_future":
            order = rebuild(order, instrument_id="BTC-USDT-261225")
            context = replace(context, envelope=order)
        calls = len(port.calls)
        with pytest.raises(CurrentPostPendingObservationError):
            context.inspect_v1(envelope=order, stage="TEST")
        assert len(port.calls) == calls
    finally:
        context.source.close()


@pytest.mark.parametrize("fake", [None, False, {"pending_orders": False}])
def test_clear_boolean_or_old_document_cannot_replace_original_live_source(fake):
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        _envelope,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_pending_observation_v1 import (
        inspect_current_post_pending_v1,
        CurrentPostPendingObservationError,
    )

    with pytest.raises(CurrentPostPendingObservationError, match="CONTEXT_REQUIRED"):
        inspect_current_post_pending_v1(fake, envelope=_envelope(), stage="TEST")


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
def test_original_session_lifetime_is_rechecked_at_actual_later_consumers(
    tmp_path, monkeypatch, phase
):
    from src.ops.full_core_live_path_composition_root_v1 import (
        envelope_bound_external_effect_send_seam_v1 as seam,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, rid, _, order, _, _ = seed_with_origin(tmp_path, monkeypatch)
    context, observer_port = observer_context(
        order, account=host.owner.durable_scope_identity_v1()["account"]
    )
    args = dict(
        envelope=order,
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=host.owner.execution_plan_context_v1(rid, order),
        post_pending_context=context,
    )

    def wrap(target, name):
        original = getattr(target, name)

        def wrapped(*a, **kw):
            result = original(*a, **kw)
            context.source.close()
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

    class Backend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kw):
            if phase == "during_k1":
                context.source.close()
            return super().copy_matching_generic_password_value_data_v1(**kw)

    calls = []

    class Opener:
        def open(self, *a, **kw):
            from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
                FullCoreCurrentPostPendingVetoError,
            )

            calls.append("possible_socket")
            context.source.close()
            raise FullCoreCurrentPostPendingVetoError("POST_PENDING_FORGED_AFTER_BOUNDARY")

    def factory():
        if phase == "opener_factory":
            context.source.close()
        return Opener()

    port = AccountPort(args, after_last=context.source.close if phase == "after_gets" else None)
    sequence, held = host.owner._store.sequence, host.owner.active_sum_v1()
    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="POST_PENDING"):
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
        assert len(port.requests) == 10 and len(observer_port.calls) == 10
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
            assert record["transport_attempt"]["phase"] == (
                "MAY_HAVE_SENT" if phase == "after_socket" else "ABORTED"
            )
        else:
            assert record is None
    finally:
        context.source.close()
        host.close()


@pytest.mark.parametrize("entry", ["public", "private"])
def test_actual_http_requires_pending_source_in_addition_to_quantity_and_claim(tmp_path, entry):
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        _envelope,
    )
    from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
        _handle,
        _permit,
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

    order = _envelope()
    permit = _permit(order)
    persist_external_effect_durable_consume_v1(
        store_root=tmp_path,
        permit=permit,
        envelope=order,
        durable_state="SENT_INITIATED",
        post_count=1,
        outcome="UNKNOWN",
    )
    claim = claim_original_permit_transport_attempt_v1(
        store_root=tmp_path,
        permit_id=permit.permit_id,
        envelope_id=order.envelope_id,
        envelope_digest=order.envelope_digest,
    )
    http = FullCoreProductiveHttpTradeOrderTransportV1(
        handle=_handle(),
        signing_handle=object(),
        post_safety_context=resolve_current_post_safety_context_v1(order, stage="TEST"),
        transport_attempt=claim,
        post_quantity_context=synthetic_current_post_quantity_context_v1(order),
    )
    with pytest.raises(FullCoreProductiveHttpPostError, match="POST_PENDING_CONTEXT_REQUIRED"):
        if entry == "private":
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


def test_original_host_return_keeps_same_concrete_observation_source(tmp_path):
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        _envelope,
    )
    from tests.ops.test_portfolio_budget_host_v1 import _host
    from tests.ops.test_prepost_position_source_admission_v1 import _bound
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_pending_observation_v1 import (
        capture_current_post_pending_v1,
        CurrentPostPendingObservationError,
    )

    order = _envelope()
    old, _ = observer_context(order)
    host = _host(
        tmp_path,
        fetch=old.source,
        clock=time.time,
        expected_account=old.source.expected_account_identity,
    )
    try:
        fresh = host.observe_v1({"LANE_1": _bound()})
        assert fresh.pending_source is old.source
        with pytest.raises(CurrentPostPendingObservationError):
            old.inspect_v1(envelope=order, stage="OLD")
        current = capture_current_post_pending_v1(envelope=order, source=fresh.pending_source)
        assert current.inspect_v1(envelope=order, stage="CURRENT")["account"] == host.account
    finally:
        old.source.close()
        host.close()


@pytest.mark.parametrize("fault", ["other_observer_account", "current_get_account"])
def test_observer_expectation_and_actual_account_get_must_match_original_owner(
    tmp_path, monkeypatch, fault
):
    host, rid, _, order, _, _ = seed_with_origin(tmp_path, monkeypatch)
    account = host.owner.durable_scope_identity_v1()["account"]
    context, _ = observer_context(
        order, account="foreign-observer-account" if fault == "other_observer_account" else account
    )
    args = dict(
        envelope=order,
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=host.owner.execution_plan_context_v1(rid, order),
        post_pending_context=context,
    )
    port = AccountPort(
        args, uid="foreign-current-get-account" if fault == "current_get_account" else account
    )
    from tests.ops.test_prepost_original_budget_context_v1 import execute

    before = host.owner._store.sequence
    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError):
            execute(args, tmp_path, port=port)
        assert host.owner._store.sequence == before
        assert not (tmp_path / "send/full_core_external_effect_permit_consume_v1.json").exists()
    finally:
        context.source.close()
        host.close()


def test_bare_envelope_does_not_derive_expected_account_from_current_get(tmp_path):
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        _envelope,
        _TrustedReadTransport,
    )

    order = _envelope()
    context, _ = observer_context(order)

    class ForeignPort(_TrustedReadTransport):
        def get(self, **kw):
            result = super().get(**kw)
            if kw["endpoint"] == "/api/v5/account/config":
                return replace(
                    result,
                    payload={
                        "code": "0",
                        "data": [
                            {
                                "uid": "foreign-current-account",
                                "instId": order.instrument_id,
                                "tdMode": "cross",
                            }
                        ],
                    },
                )
            return result

    try:
        with pytest.raises(
            caller.CurrentProductiveActualVenuePostError, match="ACCOUNT_BINDING_NOT_TRUSTED"
        ):
            caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
                envelope=order,
                post_pending_context=context,
                owner_go=caller.OWNER_GO,
                baseline_origin_main_sha=caller.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                store_root=tmp_path / "send",
                evidence_root=tmp_path / "evidence",
                perform_real_venue_post=True,
                k1_backend=_FakeKeychainBackend(),
                opener_factory=lambda: _TimeoutOpener(),
                read_only_get_transport=ForeignPort(),
                execution_integrity_backend=_clean_post_integrity(),
            )
        assert not (tmp_path / "send/full_core_external_effect_permit_consume_v1.json").exists()
    finally:
        context.source.close()


def test_existing_k1_profile_retains_its_own_pair_quota_and_cleanup(tmp_path):
    from unittest.mock import patch
    from tests.ops.test_k1_account_observation_source_v1 import InjectedOpener, ACCOUNT
    from tests.ops.test_current_productive_governed_live_c1_get_only_fresh_pretrade_transport_bind_v1 import (
        _FakeKeychainBackend as Backend,
    )
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        _envelope,
    )
    from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
        open_k1_account_observation_source_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1 import (
        productive_read_only_get_transport_v1 as wire,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_pending_observation_v1 import (
        capture_current_post_pending_v1,
        CurrentPostPendingObservationError,
    )

    order = _envelope()
    opener = InjectedOpener()
    with patch.object(wire, "build_opener", return_value=opener):
        with open_k1_account_observation_source_v1(
            expected_account_identity=ACCOUNT,
            session_id="current-k1-observer",
            max_request_count=10,
            k1_lookup_backend=Backend(),
            clock=time.time,
        ) as source:
            observation = source.collect_v1(
                instrument_ids_by_native_id={order.instrument_id: "synthetic-instrument"}
            )
            assert observation.pending_source is source
            context = capture_current_post_pending_v1(envelope=order, source=source)
            assert (
                context.inspect_v1(envelope=order, stage="K1")["source_class"]
                == "K1AccountObservationSourceV1"
            )
            assert len(opener.requests) == 10
            source.transport._transport._handle = None
            with pytest.raises(CurrentPostPendingObservationError, match="HANDLE_BINDING_REQUIRED"):
                context.inspect_v1(envelope=order, stage="CHANGED_K1")
    with pytest.raises(CurrentPostPendingObservationError):
        context.inspect_v1(envelope=order, stage="CLOSED_K1")
    assert len(opener.requests) == 10
