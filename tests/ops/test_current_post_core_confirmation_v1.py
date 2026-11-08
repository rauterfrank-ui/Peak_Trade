"""Original C1/C2/C3 lineage and selected-side progress at retained-plan POST."""

from dataclasses import replace
import json

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_sidestate_confirmation_cursor_v1 as cursors,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    inspect_original_portfolio_execution_context_v1,
    FullCoreEnvelopeBoundSendSeamError,
)
from tests.ops.test_current_post_original_core_cursor_v1 import seed_core
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
    synthetic_current_post_pending_context_v1,
)
from tests.ops.test_prepost_original_budget_context_v1 import (
    no_network as no_network,
    AccountPort,
    caller,
    files,
    _clean_post_integrity,
)
from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    _FakeKeychainBackend,
)


def advance_confirmation(root, fault, *, short=False):
    from trading.market_state.directional_confirmation_progress_v1 import (
        ConfirmationAssessmentSignalV1 as Signal,
        ConfirmationProgressInputV1,
        ConfirmationSideV1,
        evaluate_confirmation_progress_v1,
    )
    from trading.market_state.distinct_market_observation_acceptor_v1 import (
        ObservationCandidateV1,
        commit_observation_acceptance_v1,
        evaluate_distinct_market_observation_v1,
    )

    raw = cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
    cursor = cursors.parse_current_productive_sidestate_confirmation_cursor_v1(raw)
    state = cursor.cap61_confirmation_state
    assert state is not None
    selected = ConfirmationSideV1.SHORT if short else ConfirmationSideV1.LONG
    carrier = state.confirmation_side_carrier
    observation = state.observation_acceptance_state
    if fault == "missing":
        state = None
    elif fault == "session":
        session = state.confirmation_session_id + "-other-session"
        carrier = replace(
            carrier,
            bull_confirmation_state=replace(carrier.bull_confirmation_state, session_id=session),
            bear_confirmation_state=replace(carrier.bear_confirmation_state, session_id=session),
        )
        state = replace(state, confirmation_session_id=session, confirmation_side_carrier=carrier)
    elif fault in {"venue", "config", "repository"}:
        key = {"venue": "venue", "config": "config_digest", "repository": "repository_sha"}[fault]
        state = replace(state, **{key: getattr(state, key) + "-other"})
    elif fault == "bad_count":
        name = "bear_confirmation_state" if short else "bull_confirmation_state"
        raw["cap61_confirmation_state"]["confirmation_side_carrier"][name][
            "distinct_confirmation_observation_count"
        ] = "2"
        (root / cursors.CURSOR_FILENAME).write_text(json.dumps(raw))
        return
    elif fault != "decision_only":
        signals = (
            [Signal.OBSERVE, Signal.CANDIDATE]
            if fault == "candidate"
            else [Signal.OBSERVE if fault == "reset" else Signal.CANDIDATE]
        )
        for signal in signals:
            identity = observation.last_accepted_observation_identity
            key = observation.bound_instrument_key
            assert identity is not None and key is not None
            candidate = ObservationCandidateV1(
                venue=key.venue,
                canonical_instrument_id=key.canonical_instrument_id,
                venue_instrument_id=key.venue_instrument_id,
                venue_event_time=identity.venue_event_time + (0 if fault == "duplicate" else 60),
                mark_price=identity.mark_price,
            )
            accepted = evaluate_distinct_market_observation_v1(observation, candidate)
            observation = commit_observation_acceptance_v1(
                current_state=observation, result=accepted
            )
            if fault != "lag":
                prior = carrier.for_side(selected)
                result = evaluate_confirmation_progress_v1(
                    ConfirmationProgressInputV1(
                        prior_state=prior,
                        observation_acceptance_result=accepted,
                        session_id=state.confirmation_session_id,
                        venue=state.venue,
                        instrument=key,
                        side=selected,
                        assessment_signal=signal,
                        confirmation_threshold=cursor.confirmation_epochs,
                    )
                )
                assert not result.fail_closed
                carrier = carrier.with_side_state(selected, result.state_after)
        state = replace(
            state, observation_acceptance_state=observation, confirmation_side_carrier=carrier
        )
    updated = replace(
        cursor,
        cap61_confirmation_state=state,
        trading_epoch=cursor.trading_epoch + 1,
        last_evaluated_trading_epoch=cursor.last_evaluated_trading_epoch + 1,
        now_tick=cursor.now_tick + 1,
    )
    cursors.persist_current_productive_sidestate_confirmation_cursor_v1(
        updated,
        store_root=root,
        expected_prior_digest=cursors.current_productive_cursor_digest_v1(raw),
    )


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize(
    "fault", ["reset", "candidate", "missing", "session", "venue", "lag", "config", "repository"]
)
def test_retained_c3_rejects_lost_confirmation_or_original_lineage(
    tmp_path, monkeypatch, modern, fault
):
    host, args, root = seed_core(tmp_path, monkeypatch, modern)
    try:
        inspect_original_portfolio_execution_context_v1(**args)
        advance_confirmation(root, fault)
        before, held = files(tmp_path), host.owner.active_sum_v1()
        with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="CURRENT_CORE_C3"):
            inspect_original_portfolio_execution_context_v1(**args)
        assert files(tmp_path) == before and host.owner.active_sum_v1() == held > 0
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("progress", ["hold", "duplicate", "decision_only"])
def test_original_confirmed_progress_is_not_generic_expiry(tmp_path, monkeypatch, modern, progress):
    host, args, root = seed_core(tmp_path, monkeypatch, modern)
    try:
        original = inspect_original_portfolio_execution_context_v1(**args)
        advance_confirmation(root, progress)
        before = files(tmp_path)
        assert inspect_original_portfolio_execution_context_v1(**args) == original
        assert files(tmp_path) == before
    finally:
        host.close()


@pytest.mark.parametrize("short", [False, True])
@pytest.mark.parametrize("fault", ["reset", "candidate", "lag"])
def test_natural_n1_selected_c3_producer_reaches_retained_consumer(
    tmp_path, monkeypatch, short, fault
):
    from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    )

    bind = Owner.bind_execution_plan_v1
    observed = []

    def capture(owner, rid, envelope, **kw):
        result = bind(owner, rid, envelope, **kw)
        source = result["plan_origin"]["core_cursor_source"]
        assert source["schema"] == "portfolio_original_core_cursor_source.v2"
        observed.append((source, kw["core_cursor_root"], kw["canonical_intent"].side))
        return result

    monkeypatch.setattr(Owner, "bind_execution_plan_v1", capture)
    result = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    assert result.ok and len(observed) == 1 and result.trace.post_count == 0
    # The host has completed its original C1-cycle readback before a subsequent
    # observation is published. Publishing during planbind would correctly trip
    # the host's separate STALE_OR_EQUAL_C1_REJECTED guard.
    source, root, side = observed[0]
    advance_confirmation(root, fault, short=short)
    from src.ops.portfolio_capital_reservation_budget_v1.core_cursor_source_v1 import (
        inspect_current_core_cursor_v1,
    )

    with pytest.raises(ValueError, match="CURRENT_CORE_C3"):
        inspect_current_core_cursor_v1(source, intent_side=side)


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("fault", ["reset", "lag"])
@pytest.mark.parametrize("phase", ["before_get", "after_get", "during_k1", "opener_factory"])
def test_current_c3_veto_reaches_existing_post_barriers(
    tmp_path, monkeypatch, modern, fault, phase
):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, args, root = seed_core(tmp_path, monkeypatch, modern)
    owner = host.owner
    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )
    changed, sockets = [], []

    def change():
        if not changed:
            advance_confirmation(root, fault)
            changed.append(True)

    class Port(AccountPort):
        def get(self, **kw):
            result = super().get(**kw)
            if phase == "after_get":
                change()
            return result

    class Backend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kw):
            result = super().copy_matching_generic_password_value_data_v1(**kw)
            if phase == "during_k1":
                change()
            return result

    class Opener:
        def open(self, *a, **kw):
            sockets.append(True)
            raise AssertionError("C3 veto must stop before socket")

    def factory():
        if phase == "opener_factory":
            change()
        return Opener()

    if phase == "before_get":
        change()
    port, held = Port(args), owner.active_sum_v1()
    wire = args["envelope"].to_runtime_json_v1()
    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="CURRENT_CORE_C3"):
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
        assert changed and not sockets
        assert len(port.requests) == (0 if phase == "before_get" else 10)
        assert owner.active_sum_v1() == held > 0 and args["envelope"].to_runtime_json_v1() == wire
        record = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")["record"]
        if phase in {"before_get", "after_get"}:
            assert record is None
        else:
            assert record["durable_state"] == "ABORTED_BEFORE_TRANSPORT"
            assert record["transport_attempt"]["reason_code"].startswith("POST_BUDGET")
    finally:
        host.close()


def test_restore_number_coercion_is_not_proof_of_typed_c3_count(tmp_path, monkeypatch):
    host, args, root = seed_core(tmp_path, monkeypatch, True)
    try:
        advance_confirmation(root, "bad_count")
        with pytest.raises(
            FullCoreEnvelopeBoundSendSeamError, match="CURRENT_CORE_C3_STATE_UNPROVEN"
        ):
            inspect_original_portfolio_execution_context_v1(**args)
    finally:
        host.close()


def test_old_source_schema_is_not_implicitly_upgraded_to_c3_authority(tmp_path, monkeypatch):
    from src.ops.portfolio_capital_reservation_budget_v1 import core_cursor_source_v1 as sources
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest

    original = sources.bind_core_cursor_source_v1

    def old_source(*args, **kw):
        value = original(*args, **kw)
        del value["confirmation_lineage"]
        del value["digest"]
        value["schema"] = sources.SCHEMA
        return {**value, "digest": digest(value)}

    monkeypatch.setattr(sources, "bind_core_cursor_source_v1", old_source)
    host, args, root = seed_core(tmp_path, monkeypatch, True)
    try:
        advance_confirmation(root, "missing")
        result = host.owner.inspect_current_core_cursor_v1(
            args["portfolio_reservation_id"], args["envelope"]
        )
        assert result["confirmation"] == {"scope": "LEGACY_ORIGINAL_C3_NOT_ASSESSED"}
        assert (
            inspect_original_portfolio_execution_context_v1(**args)["scope"]
            == "ORIGINAL_COMMITTED_PLAN_CONTEXT_ONLY"
        )
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
def test_c3_reset_after_possible_socket_retains_uncertainty_and_hold(tmp_path, monkeypatch, modern):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, args, root = seed_core(tmp_path, monkeypatch, modern)
    owner = host.owner
    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )
    calls = []

    class Opener:
        def open(self, *a, **kw):
            calls.append(True)
            advance_confirmation(root, "reset")
            raise TimeoutError("Synthetic possible send")

    held = owner.active_sum_v1()
    try:
        result = caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
            **args,
            owner_go=caller.OWNER_GO,
            baseline_origin_main_sha=caller.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            store_root=tmp_path / "send",
            evidence_root=tmp_path / "evidence",
            perform_real_venue_post=True,
            k1_backend=_FakeKeychainBackend(),
            opener_factory=Opener,
            read_only_get_transport=AccountPort(args),
            execution_integrity_backend=_clean_post_integrity(),
        )
        assert calls == [True] and result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
        record = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")["record"]
        assert (
            record["durable_state"] == "SENT_INITIATED"
            and record["transport_attempt"]["phase"] == "MAY_HAVE_SENT"
        )
        assert owner.active_sum_v1() == held > 0
        assert (
            owner.release_plan_failure_v1(args["portfolio_reservation_id"]).disposition.value
            == "FAIL_CLOSED"
        )
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
def test_persisted_opposite_confirmation_does_not_invent_both_side_conflict(
    tmp_path, monkeypatch, modern
):
    host, args, root = seed_core(tmp_path, monkeypatch, modern)
    try:
        original = inspect_original_portfolio_execution_context_v1(**args)
        cursor = cursors.parse_current_productive_sidestate_confirmation_cursor_v1(
            cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
        )
        for short in [True, False]:
            for _ in range(cursor.confirmation_epochs):
                advance_confirmation(root, "hold", short=short)
        updated = cursors.parse_current_productive_sidestate_confirmation_cursor_v1(
            cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
        ).cap61_confirmation_state
        carrier = updated.confirmation_side_carrier
        assert carrier.bull_confirmation_state.assessment_state.value == "confirmed"
        assert carrier.bear_confirmation_state.assessment_state.value == "confirmed"
        assert (
            carrier.bear_confirmation_state.latest_accepted_market_observation_epoch.value
            < updated.observation_acceptance_state.market_observation_epoch.value
        )
        assert inspect_original_portfolio_execution_context_v1(**args) == original
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
def test_new_original_confirmation_cannot_reopen_aborted_consumed_attempt(
    tmp_path, monkeypatch, modern
):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, args, root = seed_core(tmp_path, monkeypatch, modern)
    owner = host.owner
    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )

    class Backend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kw):
            value = super().copy_matching_generic_password_value_data_v1(**kw)
            advance_confirmation(root, "reset")
            return value

    common = dict(
        owner_go=caller.OWNER_GO,
        baseline_origin_main_sha=caller.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        store_root=tmp_path / "send",
        evidence_root=tmp_path / "evidence",
        perform_real_venue_post=True,
        opener_factory=lambda: (_ for _ in ()).throw(
            AssertionError("No transport after original abort")
        ),
        execution_integrity_backend=_clean_post_integrity(),
    )
    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="CURRENT_CORE_C3"):
            caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
                **args, **common, k1_backend=Backend(), read_only_get_transport=AccountPort(args)
            )
        cursor = cursors.parse_current_productive_sidestate_confirmation_cursor_v1(
            cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
        )
        for _ in range(cursor.confirmation_epochs):
            advance_confirmation(root, "hold")
        proof = owner.inspect_current_core_cursor_v1(
            args["portfolio_reservation_id"], args["envelope"]
        )
        assert proof["confirmation"]["confirmation_status"] == "confirmed"
        before = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")
        retry, held = AccountPort(args), owner.active_sum_v1()
        with pytest.raises(caller.CurrentProductiveActualVenuePostError):
            caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
                **args, **common, k1_backend=_FakeKeychainBackend(), read_only_get_transport=retry
            )
        assert retry.requests == [] and owner.active_sum_v1() == held > 0
        assert load_external_effect_durable_consume_v1(store_root=tmp_path / "send") == before
        assert before["record"]["durable_state"] == "ABORTED_BEFORE_TRANSPORT"
    finally:
        host.close()
