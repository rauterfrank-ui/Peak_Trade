"""Original N1 Core cursor lineage and its later KILL_ALL veto, offline only."""

import json
from pathlib import Path
from dataclasses import replace

import pytest

from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
)
from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_sidestate_confirmation_cursor_v1 as cursor_owner,
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


def seed_core(root, monkeypatch, modern):
    """Same actual Core/LIVE-29P producer; original cursor persisted in a temp root."""
    from tests.ops import test_portfolio_execution_recovery_v1 as source

    plan, cycle, bind = (
        source.try_bind_current_productive_venue_plan_v1,
        source._host_enter_cycle,
        Owner.bind_execution_plan_v1,
    )
    captured = {}
    cursor_root = root / "original-core-cursor"

    def original_cycle(*a, **kw):
        result = cycle(*a, **kw)
        assert result[1].outgoing_cursor is not None
        cursor_owner.persist_current_productive_sidestate_confirmation_cursor_v1(
            result[1].outgoing_cursor, store_root=cursor_root
        )
        return result

    def original_plan(**kw):
        result = plan(**kw)
        captured.update(replay=kw["replay"], plan=result[2])
        return result

    def original_bind(owner, rid, envelope):
        replay = captured["replay"]
        return bind(
            owner,
            rid,
            envelope,
            canonical_intent=replay.intermediate.canonical_order_intent,
            venue_plan=captured["plan"],
            core_parent=replay.evidence,
            core_cursor_root=cursor_root,
        )

    with monkeypatch.context() as patch:
        patch.setattr(source, "_host_enter_cycle", original_cycle)
        patch.setattr(source, "try_bind_current_productive_venue_plan_v1", original_plan)
        patch.setattr(Owner, "bind_execution_plan_v1", original_bind)
        host, rid, identity, envelope = source.seed(root / "budget")
    args = dict(envelope=envelope, portfolio_budget_owner=host.owner, portfolio_reservation_id=rid)
    args.update(
        execution_plan_context=host.owner.execution_plan_context_v1(rid, envelope)
    ) if modern else args.update(execution_identity=identity)
    return host, args, cursor_root


def change_cursor(root, fault):
    raw = cursor_owner.load_current_productive_sidestate_confirmation_cursor_v1(root)
    cursor = cursor_owner.parse_current_productive_sidestate_confirmation_cursor_v1(raw)
    if fault == "missing":
        (root / cursor_owner.CURSOR_FILENAME).unlink()
        return "CURRENT_CORE_CURSOR_MISSING"
    if fault == "corrupt":
        (root / cursor_owner.CURSOR_FILENAME).write_text("{invalid")
        return "CURSOR_FILE_CORRUPT"
    updates = dict(
        trading_epoch=cursor.trading_epoch + 1,
        last_evaluated_trading_epoch=cursor.last_evaluated_trading_epoch + 1,
        now_tick=cursor.now_tick + 1,
    )
    if fault == "kill":
        from trading.master_v2.double_play_state import SideState

        updates["side_state"] = SideState.KILL_ALL
        reason = "CURRENT_CORE_CURSOR_KILL_ALL"
    elif fault in {"instrument_id", "venue_native_id", "lineage_id", "schema_version"}:
        updates[fault] = "FOREIGN"
        reason = "CURRENT_CORE_CURSOR_IDENTITY_MISMATCH"
    elif fault == "epoch":
        updates["last_evaluated_trading_epoch"] = updates["trading_epoch"]
        reason = "CURRENT_CORE_CURSOR_STATE_UNPROVEN"
    elif fault == "advance":
        reason = ""
    else:
        raise AssertionError(fault)
    cursor_owner.persist_current_productive_sidestate_confirmation_cursor_v1(
        replace(cursor, **updates),
        store_root=root,
        expected_prior_digest=cursor_owner.current_productive_cursor_digest_v1(raw),
    )
    return reason


@pytest.mark.parametrize("short", [False, True])
def test_actual_n1_retains_its_actual_original_core_cursor_source(tmp_path, monkeypatch, short):
    from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1
    from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
        CURSOR_FILENAME,
        current_productive_cursor_digest_v1,
    )

    bind = Owner.bind_execution_plan_v1
    captured = []

    def observe(owner, rid, envelope, **kwargs):
        result = bind(owner, rid, envelope, **kwargs)
        captured.append((result, kwargs))
        return result

    monkeypatch.setattr(Owner, "bind_execution_plan_v1", observe)
    result = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    assert result.ok and len(captured) == 1
    link, supplied = captured[0]
    source = link["plan_origin"]["core_cursor_source"]
    root = Path(source["cursor_root"])
    payload = json.loads((root / CURSOR_FILENAME).read_text())
    assert root.is_relative_to((tmp_path / "lane_state").resolve())
    assert source["source_cursor_digest"] == current_productive_cursor_digest_v1(payload)
    assert source["decision_id"] == supplied["core_parent"].decision_id
    assert source["core_parent_digest"] == supplied["core_parent"].semantic_digest
    assert source["instrument_id"] == supplied["core_parent"].instrument_id
    assert source["native_id"] == link["envelope"]["instrument_id"]
    assert result.trace.post_count == 0


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize(
    "fault",
    [
        "kill",
        "missing",
        "corrupt",
        "instrument_id",
        "venue_native_id",
        "lineage_id",
        "schema_version",
        "epoch",
    ],
)
def test_current_original_cursor_veto_reaches_retained_plan_without_rewriting_hold(
    tmp_path, monkeypatch, modern, fault
):
    from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
        inspect_original_portfolio_execution_context_v1,
        FullCoreEnvelopeBoundSendSeamError,
    )

    host, args, root = seed_core(tmp_path, monkeypatch, modern)
    try:
        inspect_original_portfolio_execution_context_v1(**args)
        reason = change_cursor(root, fault)
        before, held = files(tmp_path), host.owner.active_sum_v1()
        with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match=reason):
            inspect_original_portfolio_execution_context_v1(**args)
        assert files(tmp_path) == before and host.owner.active_sum_v1() == held > 0
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
def test_newer_epoch_and_digest_alone_are_not_new_plan_expiry_or_core_admission(
    tmp_path, monkeypatch, modern
):
    from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
        inspect_original_portfolio_execution_context_v1,
    )

    host, args, root = seed_core(tmp_path, monkeypatch, modern)
    try:
        before = inspect_original_portfolio_execution_context_v1(**args)
        change_cursor(root, "advance")
        snapshot = files(tmp_path)
        assert inspect_original_portfolio_execution_context_v1(**args) == before
        current = host.owner.inspect_current_core_cursor_v1(
            args["portfolio_reservation_id"], args["envelope"]
        )
        assert current["cursor_digest"] != current["source_cursor_digest"]
        assert current["scope"] == "CURRENT_ORIGINAL_CORE_KILL_ALL_VETO_ONLY"
        assert current["runtime_authorization_effect"] == "NONE"
        assert files(tmp_path) == snapshot
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("fault", ["kill", "missing", "lineage_id"])
@pytest.mark.parametrize("phase", ["before_get", "after_get", "during_k1", "opener_factory"])
def test_actual_post_rechecks_original_cursor_before_possible_socket(
    tmp_path, monkeypatch, modern, fault, phase
):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, args, root = seed_core(tmp_path, monkeypatch, modern)
    owner = host.owner
    changed, sockets = [], []

    def change():
        if not changed:
            changed.append(change_cursor(root, fault))

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
            sockets.append("socket")
            raise AssertionError("No possible socket after original Core veto")

    def factory():
        if phase == "opener_factory":
            change()
        return Opener()

    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )
    if phase == "before_get":
        change()
    port, held = Port(args), owner.active_sum_v1()
    wire = args["envelope"].to_runtime_json_v1()
    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="CORE_CURSOR"):
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
        assert owner.active_sum_v1() == held > 0
        assert args["envelope"].to_runtime_json_v1() == wire
        record = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")["record"]
        if phase in {"before_get", "after_get"}:
            assert record is None
            assert (
                owner.execution_links_v1()[args["portfolio_reservation_id"]]["phase"]
                == "PLAN_BOUND"
            )
        else:
            assert record["transport_attempt"]["phase"] == "ABORTED"
            assert record["transport_attempt"]["reason_code"].startswith("POST_BUDGET")
            assert record["durable_state"] == "ABORTED_BEFORE_TRANSPORT"
    finally:
        host.close()


@pytest.mark.parametrize("fault", ["kill", "missing"])
def test_cold_original_restore_keeps_hold_and_lineage_without_promoting_current_cursor(
    tmp_path, monkeypatch, fault
):
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

    host, args, root = seed_core(tmp_path, monkeypatch, True)
    owner, rid = host.owner, args["portfolio_reservation_id"]
    state = owner.risk_snapshot_v1()["state"]
    original = owner.execution_links_v1()[rid]
    identity = owner.durable_scope_identity_v1()
    held = owner.active_sum_v1()
    change_cursor(root, fault)
    host.close()
    cold = Owner(
        durable_root=identity["root"],
        durable_account_identity=state["account_identity"],
        durable_mode="recover",
        durable_lane_bindings={
            lane: BoundInstrumentV1(**row["bound"]) for lane, row in state["lane_bindings"].items()
        },
    )
    try:
        assert cold.execution_links_v1()[rid] == original
        assert cold.active_sum_v1() == held > 0
        assert cold.budget_state_v1().recovery_required
        with pytest.raises(ValueError, match="ORIGINAL_OWNER_FENCED"):
            cold.inspect_current_core_cursor_v1(rid, args["envelope"])
    finally:
        cold.close()


@pytest.mark.parametrize("fault", ["remove", "foreign_root", "downgrade"])
def test_original_plan_reference_cannot_drop_or_rebind_its_core_source(
    tmp_path, monkeypatch, fault
):
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest

    host, args, root = seed_core(tmp_path, monkeypatch, True)
    owner, rid = host.owner, args["portfolio_reservation_id"]
    try:
        origin = owner._execution_links[rid]["plan_origin"]
        if fault == "foreign_root":
            other = tmp_path / "other-cursor"
            raw = cursor_owner.load_current_productive_sidestate_confirmation_cursor_v1(root)
            cursor_owner.persist_current_productive_sidestate_confirmation_cursor_v1(
                cursor_owner.parse_current_productive_sidestate_confirmation_cursor_v1(raw),
                store_root=other,
            )
            source = origin["core_cursor_source"]
            source["cursor_root"] = str(other.resolve())
            source["digest"] = digest({k: v for k, v in source.items() if k != "digest"})
        else:
            del origin["core_cursor_source"]
            if fault == "downgrade":
                origin["schema"] = "portfolio_execution_plan_origin.v1"
        origin["digest"] = digest({k: v for k, v in origin.items() if k != "digest"})
        with pytest.raises(ValueError, match="ORIGIN_SHAPE|CONTEXT_MISMATCH"):
            owner.inspect_execution_plan_context_v1(
                rid, args["envelope"], args["execution_plan_context"]
            )
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
def test_core_kill_after_possible_socket_preserves_original_uncertainty_and_capital(
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
    calls = []

    class Opener:
        def open(self, *a, **kw):
            calls.append("possible_socket")
            change_cursor(root, "kill")
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
        assert (
            calls == ["possible_socket"]
            and result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
        )
        assert owner.active_sum_v1() == held > 0
        assert (
            owner.release_plan_failure_v1(args["portfolio_reservation_id"]).disposition.value
            == "FAIL_CLOSED"
        )
        record = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")["record"]
        assert record["durable_state"] == "SENT_INITIATED"
        assert record["transport_attempt"]["phase"] == "MAY_HAVE_SENT"
    finally:
        host.close()


@pytest.mark.parametrize("short", [False, True])
@pytest.mark.parametrize(
    "fault", ["decision_id", "trading_epoch", "semantic_digest", "authority_effect"]
)
def test_actual_n1_writer_refuses_foreign_core_parent_before_its_plan_write(
    tmp_path, monkeypatch, short, fault
):
    from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1
    from trading.master_v2.canonical_trading_decision_evidence_v1 import (
        with_computed_evidence_semantic_digest,
    )

    bind = Owner.bind_execution_plan_v1
    captured = []

    def refuse(owner, rid, envelope, **kw):
        parent = kw["core_parent"]
        value = (
            parent.trading_epoch + 1
            if fault == "trading_epoch"
            else "0" * 64
            if fault == "semantic_digest"
            else "FOREIGN"
        )
        kw["core_parent"] = replace(parent, **{fault: value})
        if fault != "semantic_digest":
            kw["core_parent"] = with_computed_evidence_semantic_digest(kw["core_parent"])
        sequence = owner._store.sequence
        with pytest.raises(ValueError, match="ORIGINAL_CORE_CURSOR_DECISION_PARENT_MISMATCH"):
            bind(owner, rid, envelope, **kw)
        assert rid not in owner.execution_links_v1()
        assert owner._store.sequence == sequence
        captured.append(True)
        raise ValueError("SYNTHETIC_WRITER_DENY_VERIFIED")

    monkeypatch.setattr(Owner, "bind_execution_plan_v1", refuse)
    result = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    assert captured == [True]
    assert not result.ok and result.trace.post_count == 0
