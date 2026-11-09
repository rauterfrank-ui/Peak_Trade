"""A failed actual N1 cycle withdraws the same original sender's budget owner."""

from pathlib import Path

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    invoke_join_v1 as n1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops.test_current_core_entry_attempt_v1 import (
    cursors,
    durable,
    load,
    seed_frame,
    _pair,
    _bound,
    _carry_kwargs,
    _lane_g17_producers,
    inspect_original_portfolio_execution_context_v1,
    FullCoreEnvelopeBoundSendSeamError,
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
    no_network as no_network,
    synthetic_current_post_pending_context_v1,
    AccountPort,
    caller,
    _clean_post_integrity,
    _FakeKeychainBackend,
)


def failed_next_n1(tmp_path, monkeypatch, owner, root):
    pairs = {"LANE_1": _pair(tmp_path, "LANE_1", bound=_bound(), lane_state_root=str(root))}
    base = {
        **_carry_kwargs(cycle_id_prefix="failed-original-n1"),
        "g17_typed_vol_producers": _lane_g17_producers(pairs),
    }
    writes, core_calls = [], []

    def unavailable(*args, **kwargs):
        writes.append(True)
        raise OSError("SYNTHETIC_CURSOR_PUBLICATION_UNAVAILABLE")

    def no_core(**kwargs):
        core_calls.append(True)
        raise AssertionError("Core cannot start before the negative publication")

    monkeypatch.setattr(
        cursors, "persist_current_productive_sidestate_confirmation_cursor_v1", unavailable
    )
    monkeypatch.setattr(durable, "run_current_productive_master_v2_runtime_cycle_v1", no_core)
    dispatch = n1._t2_from_s7(
        lane_pairs=pairs,
        native_id=_bound().venue_native_id,
        lane_id="LANE_1",
        s7_base=base,
        live_29p_injected=None,
        candles_payload={},
        portfolio_budget_owner=owner,
    )

    def fail():
        with pytest.raises(OSError, match="SYNTHETIC_CURSOR_PUBLICATION_UNAVAILABLE") as error:
            dispatch()
        assert writes == [True] and core_calls == []
        return error.value

    return fail


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("fenced", [False, True])
def test_failed_actual_n1_withdraws_old_owner_and_causal_control_keeps_old_plan(
    tmp_path, monkeypatch, modern, fenced
):
    host, args, root, _ = seed_frame(tmp_path, monkeypatch, modern, cursor_root=tmp_path / "LANE_1")
    owner = host.owner
    try:
        admitted = inspect_original_portfolio_execution_context_v1(**args)
        before, held = load(root), owner.active_sum_v1()
        snapshot = owner.risk_snapshot_v1()["state"]
        stable_root = Path(owner.durable_scope_identity_v1()["root"])
        fail = failed_next_n1(tmp_path, monkeypatch, owner, root)
        with monkeypatch.context() as control:
            if not fenced:
                # Remove only the new owner withdrawal; the real original
                # cursor publication still fails and Core still does not run.
                control.setattr(owner, "close", lambda: None)
            fail()
        assert load(root) == before
        assert owner.active_sum_v1() == held > 0
        assert owner.execution_links_v1() == snapshot["execution_links"]
        if not fenced:
            assert inspect_original_portfolio_execution_context_v1(**args) == admitted
            return
        assert not owner.budget_state_v1().admitted
        with pytest.raises(FullCoreEnvelopeBoundSendSeamError):
            inspect_original_portfolio_execution_context_v1(**args)
        # Cold reopen is not admission: exact holds and links survive, and the
        # original recovery gate still has to run. No fresh-Core recovery claim.
        bindings = {
            lane: BoundInstrumentV1(**row["bound"])
            for lane, row in snapshot["lane_bindings"].items()
        }
        recovered = Owner(
            durable_root=stable_root,
            durable_account_identity=snapshot["account_identity"],
            durable_mode="recover",
            durable_lane_bindings=bindings,
        )
        try:
            state = recovered.budget_state_v1()
            assert not state.admitted and state.recovery_required
            assert recovered.active_sum_v1() == held
            assert recovered.execution_links_v1() == snapshot["execution_links"]
        finally:
            recovered.close()
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("phase", ["before_get", "after_get", "during_k1", "opener_factory"])
def test_failed_actual_n1_at_original_post_boundaries_stops_before_socket(
    tmp_path, monkeypatch, modern, phase
):
    host, args, root, _ = seed_frame(tmp_path, monkeypatch, modern, cursor_root=tmp_path / "LANE_1")
    owner = host.owner
    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )
    fail = failed_next_n1(tmp_path, monkeypatch, owner, root)
    changed, sockets = [], []
    before, held = load(root), owner.active_sum_v1()

    def change():
        assert not changed
        fail()
        changed.append(True)

    class Port(AccountPort):
        def get(self, **kw):
            value = super().get(**kw)
            if phase == "after_get" and not changed:
                change()
            return value

    class Backend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kw):
            value = super().copy_matching_generic_password_value_data_v1(**kw)
            if phase == "during_k1":
                change()
            return value

    class Opener:
        def open(self, *args, **kwargs):
            sockets.append(True)
            raise AssertionError("Closed original owner cannot reach the socket")

    def factory():
        if phase == "opener_factory":
            change()
        return Opener()

    if phase == "before_get":
        change()
    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError):
            caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
                **args,
                owner_go=caller.OWNER_GO,
                baseline_origin_main_sha=caller.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
                store_root=tmp_path / "send",
                evidence_root=tmp_path / "evidence",
                perform_real_venue_post=True,
                k1_backend=Backend(),
                opener_factory=factory,
                read_only_get_transport=Port(args),
                execution_integrity_backend=_clean_post_integrity(),
            )
        assert changed == [True] and sockets == []
        assert load(root) == before and owner.active_sum_v1() == held > 0
        assert not owner.budget_state_v1().admitted
    finally:
        host.close()


def test_failed_writer_lease_cleanup_still_disarms_and_preserves_original_error(
    tmp_path, monkeypatch
):
    host, args, root, _ = seed_frame(tmp_path, monkeypatch, True, cursor_root=tmp_path / "LANE_1")
    owner = host.owner
    try:
        before, held = load(root), owner.active_sum_v1()
        fail = failed_next_n1(tmp_path, monkeypatch, owner, root)

        def unavailable():
            raise OSError("SYNTHETIC_WRITER_LEASE_CLEANUP_FAILURE")

        with monkeypatch.context() as lease_failure:
            lease_failure.setattr(owner._store, "close", unavailable)
            error = fail()
        assert str(error.__cause__) == "SYNTHETIC_WRITER_LEASE_CLEANUP_FAILURE"
        assert load(root) == before and owner.active_sum_v1() == held > 0
        assert not owner.budget_state_v1().admitted
        with pytest.raises(FullCoreEnvelopeBoundSendSeamError):
            inspect_original_portfolio_execution_context_v1(**args)
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
def test_failed_actual_n1_after_possible_socket_preserves_uncertainty_and_hold(
    tmp_path, monkeypatch, modern
):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, args, root, _ = seed_frame(tmp_path, monkeypatch, modern, cursor_root=tmp_path / "LANE_1")
    owner = host.owner
    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )
    before, held = load(root), owner.active_sum_v1()
    fail = failed_next_n1(tmp_path, monkeypatch, owner, root)
    calls = []

    class Opener:
        def open(self, *args, **kwargs):
            calls.append(True)
            fail()
            raise TimeoutError("Synthetic uncertainty after possible socket effect")

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
        assert record["durable_state"] == "SENT_INITIATED"
        assert record["transport_attempt"]["phase"] == "MAY_HAVE_SENT"
        assert load(root) == before and owner.active_sum_v1() == held > 0
        assert not owner.budget_state_v1().admitted
        assert owner.release_plan_failure_v1(
            args["portfolio_reservation_id"]
        ).disposition.value == ("FAIL_CLOSED")
    finally:
        host.close()
