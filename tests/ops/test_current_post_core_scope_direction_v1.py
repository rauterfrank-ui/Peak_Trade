"""Original direction and CHOP predicates at the retained entry consumer."""

from dataclasses import replace
import json

import pytest

from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
)
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


def advance_original_state(root, fault):
    from trading.master_v2.double_play_state import (
        ScopeEvent,
        DynamicScopeRules,
        RuntimeEnvelope,
        StaticHardLimits,
        transition_state,
    )
    from trading.master_v2.chop_scope_event_policy_binding_v1 import (
        apply_chop_scope_event_policy_v1,
    )

    raw = cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
    cursor = cursors.parse_current_productive_sidestate_confirmation_cursor_v1(raw)
    state, scope = cursor.side_state, cursor.runtime_scope_state
    assert scope is not None
    steps = 1
    if fault in {"chop", "clear"}:
        result = apply_chop_scope_event_policy_v1(
            event=ScopeEvent.CHOP_DETECTED if fault == "chop" else ScopeEvent.NOOP,
            scope_state=scope,
            now_tick=cursor.now_tick + 1,
        )
        scope = result.runtime_scope_state
        assert result.side_state_mutated is False and result.direction_created is False
        reason = "CURRENT_CORE_SCOPE_CHOP_BLOCK" if fault == "chop" else ""
    elif fault in {"active", "opposite", "candidate"}:
        first = (
            ScopeEvent.UPSCOPE_CONFIRMED
            if state.value.startswith("long")
            else ScopeEvent.DOWNSCOPE_CONFIRMED
        )
        events = (
            [ScopeEvent.UPSCOPE_CANDIDATE]
            if fault == "candidate"
            else [first] + ([ScopeEvent.DOWNSCOPE_CONFIRMED] * 3 if fault == "opposite" else [])
        )
        steps = len(events)
        for index, event in enumerate(events, 1):
            state, scope, result = transition_state(
                side_state=state,
                event=event,
                scope_state=scope,
                rules=DynamicScopeRules(),
                envelope=RuntimeEnvelope(static=StaticHardLimits()),
                now_tick=cursor.now_tick + index,
            )
            assert result.allowed and result.live_authorization_granted is False
        reason = (
            ""
            if fault == "candidate"
            else "CURRENT_CORE_ENTRY_DIRECTION_NOT_ARMED"
            if fault == "active"
            else "CURRENT_CORE_ENTRY_DIRECTION_MISMATCH"
        )
    elif fault == "scope_missing":
        scope = None
        reason = "CURRENT_CORE_SCOPE_POLICY_UNPROVEN"
    elif fault == "bad_latch":
        raw["runtime_scope_state"]["chop_latched"] = 0
        (root / cursors.CURSOR_FILENAME).write_text(json.dumps(raw))
        return "CURRENT_CORE_SCOPE_POLICY_UNPROVEN"
    else:
        raise AssertionError(fault)
    updated = replace(
        cursor,
        side_state=state,
        runtime_scope_state=scope,
        trading_epoch=cursor.trading_epoch + steps,
        last_evaluated_trading_epoch=cursor.last_evaluated_trading_epoch + steps,
        now_tick=cursor.now_tick + steps,
    )
    cursors.persist_current_productive_sidestate_confirmation_cursor_v1(
        updated,
        store_root=root,
        expected_prior_digest=cursors.current_productive_cursor_digest_v1(raw),
    )
    return reason


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("fault", ["chop", "opposite", "active", "scope_missing", "bad_latch"])
def test_retained_current_guard_rejects_original_scope_or_direction_veto(
    tmp_path, monkeypatch, modern, fault
):
    host, args, root = seed_core(tmp_path, monkeypatch, modern)
    try:
        before = inspect_original_portfolio_execution_context_v1(**args)
        assert before["scope"] == "ORIGINAL_COMMITTED_PLAN_CONTEXT_ONLY"
        reason = advance_original_state(root, fault)
        snapshot, held = files(tmp_path), host.owner.active_sum_v1()
        with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match=reason):
            inspect_original_portfolio_execution_context_v1(**args)
        assert files(tmp_path) == snapshot
        assert host.owner.active_sum_v1() == held > 0
    finally:
        host.close()


@pytest.mark.parametrize("short", [False, True])
@pytest.mark.parametrize("fault", ["chop", "opposite", "active"])
def test_actual_n1_source_and_original_state_producers_reach_current_entry_consumer(
    tmp_path, monkeypatch, short, fault
):
    from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1

    bind = Owner.bind_execution_plan_v1
    captured = []

    def observe(owner, rid, envelope, **kw):
        result = bind(owner, rid, envelope, **kw)
        root = kw["core_cursor_root"]
        reason = advance_original_state(root, fault)
        context = owner.execution_plan_context_v1(rid, envelope)
        with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match=reason):
            inspect_original_portfolio_execution_context_v1(
                envelope=envelope,
                portfolio_budget_owner=owner,
                portfolio_reservation_id=rid,
                execution_plan_context=context,
            )
        captured.append(True)
        return result

    monkeypatch.setattr(Owner, "bind_execution_plan_v1", observe)
    result = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    assert captured == [True] and result.ok and result.trace.post_count == 0


@pytest.mark.parametrize("short", [False, True])
def test_actual_original_n1_armed_direction_passes_without_creating_authority(
    tmp_path, monkeypatch, short
):
    from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1

    bind = Owner.bind_execution_plan_v1
    observed = []

    def capture(owner, rid, envelope, **kw):
        result = bind(owner, rid, envelope, **kw)
        proof = owner.inspect_current_core_cursor_v1(rid, envelope)
        assert proof["direction_state"] == ("short_armed" if short else "long_armed")
        assert proof["original_intent_side"] == kw["canonical_intent"].side
        assert proof["chop_guard_status"] == "none"
        assert proof["runtime_authorization_effect"] == "NONE"
        observed.append(proof)
        return result

    monkeypatch.setattr(Owner, "bind_execution_plan_v1", capture)
    result = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    assert result.ok and len(observed) == 1 and result.trace.post_count == 0


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("progress", ["candidate", "clear"])
def test_original_scope_progress_or_noop_clear_does_not_invent_plan_expiry(
    tmp_path, monkeypatch, modern, progress
):
    host, args, root = seed_core(tmp_path, monkeypatch, modern)
    try:
        original = inspect_original_portfolio_execution_context_v1(**args)
        state = cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)["side_state"]
        if progress == "clear":
            advance_original_state(root, "chop")
            with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="SCOPE_CHOP"):
                inspect_original_portfolio_execution_context_v1(**args)
        advance_original_state(root, progress)
        before = files(tmp_path)
        assert inspect_original_portfolio_execution_context_v1(**args) == original
        assert (
            cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)["side_state"]
            == state
        )
        assert files(tmp_path) == before
    finally:
        host.close()


@pytest.mark.parametrize("value", [None, 0, 1, "false", "true", {}, [], "MISSING"])
def test_untyped_or_missing_chop_latch_cannot_be_normalized_to_current_inactive(
    tmp_path, monkeypatch, value
):
    host, args, root = seed_core(tmp_path, monkeypatch, True)
    try:
        raw = cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
        if value == "MISSING":
            del raw["runtime_scope_state"]["chop_latched"]
        else:
            raw["runtime_scope_state"]["chop_latched"] = value
        (root / cursors.CURSOR_FILENAME).write_text(json.dumps(raw))
        with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="SCOPE_POLICY_UNPROVEN"):
            inspect_original_portfolio_execution_context_v1(**args)
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("fault", ["chop", "opposite", "active"])
@pytest.mark.parametrize("phase", ["before_get", "after_get", "during_k1", "opener_factory"])
def test_actual_post_consumes_current_scope_and_original_direction_before_socket(
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
            changed.append(advance_original_state(root, fault))

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
            raise AssertionError("No socket after original direction/scope veto")

    def factory():
        if phase == "opener_factory":
            change()
        return Opener()

    if phase == "before_get":
        change()
    port, held = Port(args), owner.active_sum_v1()
    wire = args["envelope"].to_runtime_json_v1()
    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="CURRENT_CORE"):
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
        assert changed and sockets == []
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


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("fault", ["chop", "active"])
def test_scope_or_direction_change_after_possible_socket_keeps_uncertainty_and_hold(
    tmp_path, monkeypatch, modern, fault
):
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
            advance_original_state(root, fault)
            raise TimeoutError("Injected after possible send")

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
def test_original_chop_clear_does_not_reopen_consumed_aborted_attempt(
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
            advance_original_state(root, "chop")
            return value

    common = dict(
        owner_go=caller.OWNER_GO,
        baseline_origin_main_sha=caller.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        store_root=tmp_path / "send",
        evidence_root=tmp_path / "evidence",
        perform_real_venue_post=True,
        opener_factory=lambda: (_ for _ in ()).throw(AssertionError("No opener after abort")),
        execution_integrity_backend=_clean_post_integrity(),
    )
    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="SCOPE_CHOP"):
            caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
                **args,
                **common,
                k1_backend=Backend(),
                read_only_get_transport=AccountPort(args),
            )
        advance_original_state(root, "clear")
        before = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")
        held = owner.active_sum_v1()
        retry = AccountPort(args)
        with pytest.raises(caller.CurrentProductiveActualVenuePostError):
            caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
                **args,
                **common,
                k1_backend=_FakeKeychainBackend(),
                read_only_get_transport=retry,
            )
        assert retry.requests == []
        assert load_external_effect_durable_consume_v1(store_root=tmp_path / "send") == before
        assert before["record"]["durable_state"] == "ABORTED_BEFORE_TRANSPORT"
        assert owner.active_sum_v1() == held > 0
    finally:
        host.close()
