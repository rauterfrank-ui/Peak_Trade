"""Original durable veto at real consumers; synthetic state, GET/K1/HTTP only."""

import json
from dataclasses import replace

import pytest

from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState
from tests.ops.test_n1_original_plan_origin_v1 import seed_with_origin
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from tests.ops.test_prepost_original_budget_context_v1 import execute, caller


def active_source(tmp_path, monkeypatch):
    path = tmp_path / "synthetic-safety/state.json"
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(path))
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    writer = StatePersistence(str(path))
    writer.save(KillSwitchState.ACTIVE)
    return path, writer


@pytest.mark.parametrize(
    "state", ["KILLED", "RECOVERING", "MISSING", "MALFORMED", "DISABLED", "CONTRADICTORY"]
)
def test_actual_original_durable_veto_blocks_before_go_attempt_or_http(
    tmp_path, monkeypatch, state
):
    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    path = tmp_path / "synthetic-safety/state.json"
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(path))
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    if state in {"KILLED", "RECOVERING", "DISABLED"}:
        StatePersistence(str(path)).save(KillSwitchState[state])
    elif state != "MISSING":
        path.parent.mkdir(parents=True)
        path.write_text(
            "{"
            if state == "MALFORMED"
            else json.dumps({"state": "ACTIVE", "status": "KILLED", "kill_switch": True})
        )
    context = host.owner.execution_plan_context_v1(rid, envelope)
    args = dict(
        envelope=envelope,
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=context,
    )
    sequence = host.owner._store.sequence
    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="POST_SAFETY"):
            execute(args, tmp_path)
        assert host.owner._store.sequence == sequence
        assert host.owner.execution_links_v1()[rid]["identity"] is None
        assert host.owner.active_sum_v1() > 0
        assert not (tmp_path / "send").exists()
    finally:
        host.close()


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
    ],
)
def test_current_veto_rechecks_actual_source_across_both_barriers_and_before_socket(
    tmp_path, monkeypatch, phase
):
    from tests.ops.test_prepost_original_budget_context_v1 import (
        AccountPort,
        _clean_post_integrity,
        lower,
    )
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        _FakeKeychainBackend,
    )
    from src.ops.full_core_live_path_composition_root_v1 import (
        envelope_bound_external_effect_send_seam_v1 as seam,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
        load_durable_post_owner_go_consume_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )
    from tests.ops.test_original_budget_send_permit_handoff_v1 import cold_owner

    path, writer = active_source(tmp_path, monkeypatch)
    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    context = host.owner.execution_plan_context_v1(rid, envelope)
    args = dict(
        envelope=envelope,
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=context,
    )
    calls = dict(k1=0, opener=0, http=0)

    def flip():
        writer.save(KillSwitchState.KILLED)

    port = AccountPort(args, after_last=flip if phase == "after_gets" else None)
    sequence, held = host.owner._store.sequence, host.owner.active_sum_v1()

    def wrap_after(target, name):
        original = getattr(target, name)

        def wrapped(*a, **kw):
            result = original(*a, **kw)
            flip()
            return result

        monkeypatch.setattr(target, name, wrapped)

    if phase == "after_go":
        wrap_after(caller, "persist_durable_post_owner_go_consume_v1")
    elif phase == "after_mint":
        wrap_after(lower, "issue_external_effect_permit_v1")
    elif phase == "after_budget":
        wrap_after(host.owner, "begin_execution_submit_v2")
    elif phase == "after_permit":
        wrap_after(seam, "persist_external_effect_durable_consume_v1")

    class Backend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kwargs):
            calls["k1"] += 1
            if phase == "during_k1":
                flip()
            return super().copy_matching_generic_password_value_data_v1(**kwargs)

    class Opener:
        def open(self, *a, **kw):
            calls["http"] += 1
            raise AssertionError("Original current veto must stop before fake HTTP")

    def factory():
        calls["opener"] += 1
        if phase == "opener_factory":
            flip()
        return Opener()

    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="POST_SAFETY"):
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
        assert calls["http"] == 0
        assert calls["k1"] == (1 if phase in {"during_k1", "opener_factory"} else 0)
        assert calls["opener"] == (1 if phase == "opener_factory" else 0)
        assert len(port.requests) == 10
        assert json.loads(path.read_text())["state"] == "KILLED"
        assert host.owner.active_sum_v1() == held > 0
        go = load_durable_post_owner_go_consume_v1(store_root=tmp_path / "send")
        permit = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")
        assert go["consumed"] is (phase != "after_gets")
        submitted = phase in {"after_budget", "after_permit", "during_k1", "opener_factory"}
        assert permit["durable_consumed"] is submitted
        link = host.owner.execution_links_v1()[rid]
        assert (link["identity"] is not None) is submitted
        assert host.owner._store.sequence == sequence + int(submitted)
        restored = cold_owner(host)
        try:
            assert restored.execution_links_v1()[rid] == link
            assert restored.active_sum_v1() == held
            assert restored.budget_state_v1().recovery_required
        finally:
            restored.close()
    finally:
        host.close()


@pytest.mark.parametrize(
    "fault",
    ["emergency", "source_switch", "context_path", "unreadable", "foreign_context", "changed_body"],
)
def test_pinned_original_safety_reference_never_grants_from_foreign_or_unknown_inputs(
    tmp_path, monkeypatch, fault
):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_post_safety_veto_v1 as safety,
    )
    from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
        _payload_from_envelope_v1,
    )

    path, _ = active_source(tmp_path, monkeypatch)
    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    context = safety.resolve_current_post_safety_context_v1(envelope, stage="INITIAL")
    before = host.owner._store.sequence
    try:
        if fault == "emergency":
            monkeypatch.setenv("PEAK_KILL_SWITCH", "1")
        elif fault == "source_switch":
            other = tmp_path / "other/state.json"
            StatePersistence(str(other)).save(KillSwitchState.ACTIVE)
            monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(other))
        elif fault == "context_path":
            context = replace(context, state_path=str(tmp_path / "foreign"))
        elif fault == "unreadable":

            def bad_read(**kwargs):
                raise OSError("Synthetic unreadable original source")

            monkeypatch.setattr(safety, "read_durable_filegate_join_evidence_v1", bad_read)
        with pytest.raises(safety.CurrentPostSafetyVetoError, match="POST_SAFETY"):
            if fault == "foreign_context":
                safety.resolve_current_post_safety_context_v1(envelope, object(), stage="FOREIGN")
            elif fault == "changed_body":
                context.inspect_wire_v1(
                    payload={**_payload_from_envelope_v1(envelope), "sz": "999"},
                    stage="FOREIGN_BODY",
                )
            else:
                context.inspect_v1(stage="CURRENT")
        assert host.owner._store.sequence == before
        assert host.owner.execution_links_v1()[rid]["identity"] is None
        assert host.owner.active_sum_v1() > 0
    finally:
        host.close()


def test_old_state_saved_at_does_not_expire_or_mutate_a_current_active_read(tmp_path, monkeypatch):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_safety_veto_v1 import (
        resolve_current_post_safety_context_v1,
    )

    path, _ = active_source(tmp_path, monkeypatch)
    raw = json.loads(path.read_text())
    raw["saved_at"] = "2000-01-01T00:00:00"
    path.write_text(json.dumps(raw))
    before = path.read_bytes()
    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    try:
        sequence = host.owner._store.sequence
        context = resolve_current_post_safety_context_v1(envelope, stage="READ_ONLY")
        assert context.inspect_v1(stage="CURRENT").state_name == "ACTIVE"
        assert path.read_bytes() == before
        assert host.owner._store.sequence == sequence
        assert host.owner.execution_links_v1()[rid]["identity"] is None
    finally:
        host.close()


def test_safety_change_after_possible_transport_neither_remints_nor_releases(tmp_path, monkeypatch):
    from tests.ops.test_prepost_original_budget_context_v1 import lower

    _, writer = active_source(tmp_path, monkeypatch)
    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    context = host.owner.execution_plan_context_v1(rid, envelope)
    args = dict(
        envelope=envelope,
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_plan_context=context,
    )
    minted, used = [], []
    issue = lower.issue_external_effect_permit_v1
    replay = caller.prove_follow_on_submit_isolated_v1

    def mint(*a, **kw):
        result = issue(*a, **kw)
        minted.append(result)
        return result

    def replay_actual(**kw):
        assert kw["permit"] is minted[0]
        return replay(**kw)

    class Opener:
        def open(self, *a, **kw):
            used.append(True)
            writer.save(KillSwitchState.KILLED)
            raise TimeoutError("Synthetic possible external effect")

    monkeypatch.setattr(lower, "issue_external_effect_permit_v1", mint)
    monkeypatch.setattr(caller, "prove_follow_on_submit_isolated_v1", replay_actual)
    try:
        result = execute(args, tmp_path, opener=Opener())
        assert len(used) == len(minted) == 1
        assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
        assert result.replay_attempt_blocked == "true"
        assert host.owner.active_sum_v1() > 0
        assert (
            host.owner.execution_links_v1()[rid]["external_effect_permit"]["permit_id"]
            == minted[0].permit_id
        )
    finally:
        host.close()


@pytest.mark.parametrize("route", ["public", "private"])
def test_http_port_cannot_bypass_missing_original_safety_context(tmp_path, monkeypatch, route):
    from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
        FullCoreProductiveHttpTradeOrderTransportV1,
        FullCoreProductiveHttpPostError,
    )
    from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
        _handle,
    )

    http = FullCoreProductiveHttpTradeOrderTransportV1(handle=_handle(), signing_handle=object())
    with pytest.raises(FullCoreProductiveHttpPostError, match="POST_SAFETY_CONTEXT_REQUIRED"):
        if route == "public":
            http.post_trade_order(
                payload={},
                permit_id="no-permit",
                envelope_id="no-envelope",
                envelope_digest="no-digest",
                one_shot_real_post=True,
            )
        else:
            http._perform_http_post_v1(payload={})
    assert http.post_count == 0 and http.venue_live_contact is False


def test_cwd_change_cannot_retarget_a_pinned_relative_original_source(tmp_path, monkeypatch):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_post_safety_veto_v1 import (
        resolve_current_post_safety_context_v1,
        CurrentPostSafetyVetoError,
    )
    from src.ops.gates.risk_gate import DEFAULT_KILL_SWITCH_STATE_PATH

    host, rid, _, envelope, _, _ = seed_with_origin(tmp_path, monkeypatch)
    for key in [
        "PEAK_KILL_SWITCH_STATE_PATH",
        "PEAKTRADE_KILL_SWITCH_STATE_PATH",
        "PEAK_KILL_SWITCH",
    ]:
        monkeypatch.delenv(key, raising=False)
    one, two = tmp_path / "one", tmp_path / "two"
    StatePersistence(str(one / DEFAULT_KILL_SWITCH_STATE_PATH)).save(KillSwitchState.ACTIVE)
    StatePersistence(str(two / DEFAULT_KILL_SWITCH_STATE_PATH)).save(KillSwitchState.ACTIVE)
    try:
        monkeypatch.chdir(one)
        context = resolve_current_post_safety_context_v1(envelope, stage="FIRST")
        monkeypatch.chdir(two)
        with pytest.raises(CurrentPostSafetyVetoError, match="SOURCE_CHANGED"):
            context.inspect_v1(stage="SECOND")
        assert host.owner.execution_links_v1()[rid]["identity"] is None
    finally:
        host.close()


@pytest.mark.parametrize(
    "path",
    [
        "src/ops/full_core_live_path_composition_root_v1/current_productive_post_safety_veto_v1.py",
        "src/ops/full_core_live_path_composition_root_v1/durable_filegate_join_v1.py",
        "src/ops/gates/risk_gate.py",
    ],
)
def test_original_post_integrity_consumer_checks_the_new_veto_and_actual_readers(path):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
        resolve_and_assert_live_post_execution_baseline_v1,
        CurrentProductiveActualVenuePostBaselineError,
        EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
    )

    class Backend:
        def resolve_origin_main_sha_v1(self):
            return "6fe3d4e4c34b232790097988890daaf746614850"

        def resolve_head_sha_v1(self):
            return self.resolve_origin_main_sha_v1()

        def diff_origin_main_for_paths_v1(self, paths):
            return "SYNTHETIC_SOURCE_DRIFT:" + path if path in paths else ""

    with pytest.raises(
        CurrentProductiveActualVenuePostBaselineError, match="PROTECTED_POST_SLICE_SURFACE_DRIFT"
    ):
        resolve_and_assert_live_post_execution_baseline_v1(
            declared_baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            integrity_backend=Backend(),
        )
