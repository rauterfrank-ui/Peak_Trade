"""Failed current Core attempts cannot leave a retained Entry positively assessed."""

from dataclasses import replace
from pathlib import Path
import subprocess

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    current_core_entry_attempt_v1 as attempts,
)
from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_sidestate_confirmation_cursor_v1 as cursors,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1 import (
    addressing_join_v1 as durable,
)
from tests.ops.test_current_post_assessment_frame_v1 import seed_frame
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
    _clean_post_integrity,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    inspect_original_portfolio_execution_context_v1,
    FullCoreEnvelopeBoundSendSeamError,
)
from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    _FakeKeychainBackend,
)
from tests.ops.test_outer_entry_budget_policy_v1 import _bound
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1 import (
    _pair,
    _carry_kwargs,
    _lane_g17_producers,
    _seed_outgoing,
)


def begin(root, **kw):
    return attempts.begin_current_core_entry_attempt_v1(
        bound_instrument=_bound(), store_root=root, cycle_id="next-core-attempt", **kw
    )


def load(root):
    return cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)


def core_state(raw):
    body = cursors.parse_current_productive_sidestate_confirmation_cursor_v1(raw).to_dict()
    body.pop("entry_assessment_frame")
    return body


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("fault", ["invalid_input", "producer_exception"])
@pytest.mark.parametrize("fenced", [False, True])
def test_actual_durable_failed_cycle_vetoes_retained_plan_and_unfenced_control_does_not(
    tmp_path, monkeypatch, modern, fault, fenced
):
    host, args, root, captured = seed_frame(
        tmp_path, monkeypatch, modern, cursor_root=tmp_path / "LANE_1"
    )
    try:
        before = load(root)
        admitted = inspect_original_portfolio_execution_context_v1(**args)
        pairs = {"LANE_1": _pair(tmp_path, "LANE_1", bound=_bound(), lane_state_root=str(root))}
        if not fenced:
            # Causal control: remove only the new publication. Core still fails.
            monkeypatch.setattr(
                attempts,
                "begin_current_core_entry_attempt_v1",
                lambda **kw: cursors.current_productive_cursor_digest_v1(load(root)),
            )
        native = durable.run_current_productive_master_v2_runtime_cycle_v1
        observed = []

        def run(**kw):
            observed.append(True)
            if fault == "producer_exception":
                raise RuntimeError("SYNTHETIC_NATIVE_PRODUCER_FAILURE")
            result = native(**kw)
            assert result.replay is None and "mark_px" in result.input_blocker
            return result

        monkeypatch.setattr(durable, "run_current_productive_master_v2_runtime_cycle_v1", run)
        kwargs = _carry_kwargs(cycle_id_prefix="failed-current-core")
        kwargs["mark_px"] = float("nan")
        with pytest.raises((RuntimeError, ValueError)):
            durable.compose_occupied_lane_mv2_dp_durable_cycle_v1(
                pairs, g17_typed_vol_producers=_lane_g17_producers(pairs), **kwargs
            )
        assert observed == [True]
        assert core_state(load(root)) == core_state(before)
        if fenced:
            assert load(root)["entry_assessment_frame"]["status"] == "EVALUATION_NOT_COMMITTED"
            with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="ATTEMPT_NOT_COMMITTED"):
                inspect_original_portfolio_execution_context_v1(**args)
        else:
            assert load(root) == before
            assert inspect_original_portfolio_execution_context_v1(**args) == admitted
        assert host.owner.active_sum_v1() > 0
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("frame_bound", [False, True])
def test_explicit_negative_attempt_veto_also_applies_to_earlier_cursor_source(
    tmp_path, monkeypatch, modern, frame_bound
):
    seeded = (
        seed_frame(tmp_path, monkeypatch, modern)
        if frame_bound
        else seed_core(tmp_path, monkeypatch, modern)
    )
    host, args, root = seeded[:3]
    try:
        inspect_original_portfolio_execution_context_v1(
            **{k: v for k, v in args.items() if k != "post_pending_context"}
        )
        before, held = load(root), host.owner.active_sum_v1()
        token = begin(root)
        assert token == cursors.current_productive_cursor_digest_v1(load(root))
        assert core_state(load(root)) == core_state(before)
        with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="ATTEMPT_NOT_COMMITTED"):
            inspect_original_portfolio_execution_context_v1(**args)
        assert host.owner.active_sum_v1() == held > 0
    finally:
        host.close()


def test_overlapping_attempt_cannot_publish_over_newer_attempt_or_bypass_cas(tmp_path, monkeypatch):
    host, args, root, _ = seed_frame(tmp_path, monkeypatch, True)
    try:
        raw = load(root)
        actual_original = cursors.parse_current_productive_sidestate_confirmation_cursor_v1(raw)
        first = begin(root)
        first_body = load(root)
        second = begin(root)
        assert (
            first != second
            and first_body["entry_assessment_frame"]["attempt_id"]
            != load(root)["entry_assessment_frame"]["attempt_id"]
        )
        for predecessor, message in [
            (None, "PREDECESSOR_REQUIRED"),
            (first, "PUBLICATION_CONFLICT"),
        ]:
            with pytest.raises(cursors.CurrentProductiveCursorError, match=message):
                cursors.persist_current_productive_sidestate_confirmation_cursor_v1(
                    actual_original, store_root=root, expected_prior_digest=predecessor
                )
            assert cursors.current_productive_cursor_digest_v1(load(root)) == second
        # Original writer primitive: matched publication, never a new trade rule.
        cursors.persist_current_productive_sidestate_confirmation_cursor_v1(
            actual_original, store_root=root, expected_prior_digest=second
        )
        assert load(root) == raw
    finally:
        host.close()


def test_stale_eg_override_cannot_evaluate_over_newer_original_cursor(tmp_path, monkeypatch):
    host, args, root, _ = seed_frame(tmp_path, monkeypatch, True)
    try:
        old = load(root)
        begin(root)
        current = load(root)
        with pytest.raises(cursors.CurrentProductiveCursorError, match="PUBLICATION_CONFLICT"):
            begin(root, incoming_cursor_override=old)
        assert load(root) == current
    finally:
        host.close()


def test_initial_missing_cursor_does_not_invent_core_state(tmp_path):
    root = tmp_path / "new-root"
    assert begin(root) == "MISSING"
    assert not root.exists()


@pytest.mark.parametrize("short", [False, True])
def test_actual_successful_durable_cycle_replaces_marker_with_native_output(
    tmp_path, monkeypatch, short
):
    from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1

    native = attempts.begin_current_core_entry_attempt_v1
    pending = []

    def observe(**kw):
        token = native(**kw)
        raw = load(kw["store_root"])
        if raw is not None:
            assert raw["entry_assessment_frame"]["schema"] == attempts.UNCOMMITTED_ATTEMPT_SCHEMA
            pending.append(kw["store_root"])
        return token

    monkeypatch.setattr(attempts, "begin_current_core_entry_attempt_v1", observe)
    result = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    assert result.ok and pending and result.trace.post_count == 0
    for root in pending:
        assert load(root)["entry_assessment_frame"]["schema"] != attempts.UNCOMMITTED_ATTEMPT_SCHEMA


@pytest.mark.parametrize("fault", ["bootstrap_failure", "newer_attempt"])
def test_native_success_cannot_clear_failed_bootstrap_or_newer_attempt(
    tmp_path, monkeypatch, fault
):
    pairs, _, _ = _seed_outgoing(tmp_path, ("LANE_1",))
    root = Path(pairs["LANE_1"][0].lane_state_root)
    before = core_state(load(root))
    native = durable.run_current_productive_master_v2_runtime_cycle_v1
    bootstrap = durable.ensure_productive_layered_core_episode_store_v1
    produced, pending = [], []

    def evaluate(**kwargs):
        result = native(**kwargs)
        assert result.outgoing_cursor is not None
        produced.append(True)
        return result

    def finalize(**kwargs):
        if fault == "bootstrap_failure":
            pending.append(load(root))
            return ("SYNTHETIC_BOOTSTRAP_FAILURE",)
        result = bootstrap(**kwargs)
        assert not result
        attempts.begin_current_core_entry_attempt_v1(
            bound_instrument=pairs["LANE_1"][1], store_root=root, cycle_id="newer-attempt"
        )
        pending.append(load(root))
        return result

    monkeypatch.setattr(durable, "run_current_productive_master_v2_runtime_cycle_v1", evaluate)
    monkeypatch.setattr(durable, "ensure_productive_layered_core_episode_store_v1", finalize)
    reason = (
        "SYNTHETIC_BOOTSTRAP_FAILURE" if fault == "bootstrap_failure" else "PUBLICATION_CONFLICT"
    )
    with pytest.raises(ValueError, match=reason):
        durable.compose_occupied_lane_mv2_dp_durable_cycle_v1(
            pairs, g17_typed_vol_producers=_lane_g17_producers(pairs), **_carry_kwargs()
        )
    assert produced == [True] and load(root) == pending[0]
    assert core_state(load(root)) == before
    assert load(root)["entry_assessment_frame"]["status"] == "EVALUATION_NOT_COMMITTED"


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("phase", ["before_get", "after_get", "during_k1", "opener_factory"])
def test_new_core_attempt_at_actual_post_barriers_aborts_before_socket(
    tmp_path, monkeypatch, modern, phase
):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, args, root, _ = seed_frame(tmp_path, monkeypatch, modern)
    owner = host.owner
    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )
    changed, sockets = [], []

    def change():
        if not changed:
            begin(root)
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
            raise AssertionError("No socket while current Core evaluation is uncommitted")

    def factory():
        if phase == "opener_factory":
            change()
        return Opener()

    if phase == "before_get":
        change()
    port, held = Port(args), owner.active_sum_v1()
    try:
        with pytest.raises(
            caller.CurrentProductiveActualVenuePostError, match="ATTEMPT_NOT_COMMITTED"
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
        assert not sockets and len(port.requests) == (0 if phase == "before_get" else 10)
        assert owner.active_sum_v1() == held > 0
        record = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")["record"]
        if phase in {"before_get", "after_get"}:
            assert record is None
        else:
            assert record["durable_state"] == "ABORTED_BEFORE_TRANSPORT"
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
def test_attempt_after_possible_socket_keeps_unknown_and_original_hold(
    tmp_path, monkeypatch, modern
):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, args, root, _ = seed_frame(tmp_path, monkeypatch, modern)
    owner = host.owner
    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )
    calls = []

    class Opener:
        def open(self, *a, **kw):
            calls.append(True)
            begin(root)
            raise TimeoutError("Synthetic possible send before new Core attempt")

    try:
        held = owner.active_sum_v1()
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


def test_original_writer_publication_cannot_reopen_a_consumed_negative_attempt(
    tmp_path, monkeypatch
):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, args, root, _ = seed_frame(tmp_path, monkeypatch, True)
    owner = host.owner
    original = cursors.parse_current_productive_sidestate_confirmation_cursor_v1(load(root))
    token = []
    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )

    class Backend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kw):
            result = super().copy_matching_generic_password_value_data_v1(**kw)
            token.append(begin(root))
            return result

    common = dict(
        owner_go=caller.OWNER_GO,
        baseline_origin_main_sha=caller.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        store_root=tmp_path / "send",
        evidence_root=tmp_path / "evidence",
        perform_real_venue_post=True,
        opener_factory=lambda: (_ for _ in ()).throw(AssertionError("No socket")),
        execution_integrity_backend=_clean_post_integrity(),
    )
    try:
        with pytest.raises(
            caller.CurrentProductiveActualVenuePostError, match="ATTEMPT_NOT_COMMITTED"
        ):
            caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
                **args, **common, k1_backend=Backend(), read_only_get_transport=AccountPort(args)
            )
        consumed = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")
        cursors.persist_current_productive_sidestate_confirmation_cursor_v1(
            original, store_root=root, expected_prior_digest=token[0]
        )
        with pytest.raises(
            FullCoreEnvelopeBoundSendSeamError, match="EXECUTION_SUBMIT_REPLAY_OR_UNBOUND"
        ):
            inspect_original_portfolio_execution_context_v1(
                **{k: v for k, v in args.items() if k != "post_pending_context"}
            )
        retry = AccountPort(args)
        with pytest.raises(caller.CurrentProductiveActualVenuePostError):
            caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
                **args, **common, k1_backend=_FakeKeychainBackend(), read_only_get_transport=retry
            )
        assert (
            not retry.requests
            and load_external_effect_durable_consume_v1(store_root=tmp_path / "send") == consumed
        )
    finally:
        host.close()


def test_completed_marker_survives_producer_process_exit(tmp_path, monkeypatch):
    host, args, root, _ = seed_frame(tmp_path, monkeypatch, True)
    try:
        prior = core_state(load(root))
        code = """import os,sys,socket
def forbidden(*a,**k):raise AssertionError("No socket in negative publication probe")
socket.socket.connect=forbidden
socket.create_connection=forbidden
from tests.ops.test_outer_entry_budget_policy_v1 import _bound
from src.ops.full_core_live_path_composition_root_v1.current_core_entry_attempt_v1 import begin_current_core_entry_attempt_v1
begin_current_core_entry_attempt_v1(bound_instrument=_bound(),store_root=sys.argv[1],cycle_id="producer-process-exit")
os._exit(23)
"""
        result = subprocess.run(
            ["./scripts/pt", "-c", code, str(root)],
            cwd=Path(__file__).resolve().parents[2],
            capture_output=True,
        )
        assert result.returncode == 23, result.stdout.decode() + result.stderr.decode()
        assert core_state(load(root)) == prior
        with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="ATTEMPT_NOT_COMMITTED"):
            inspect_original_portfolio_execution_context_v1(**args)
    finally:
        host.close()


@pytest.mark.parametrize("fault", ["foreign", "invalid_sidestate", "corrupt"])
def test_begin_never_repairs_or_fabricates_invalid_original_state(tmp_path, monkeypatch, fault):
    import json

    host, args, root, _ = seed_frame(tmp_path, monkeypatch, True)
    try:
        path = root / cursors.CURSOR_FILENAME
        raw = load(root)
        if fault == "foreign":
            raw["instrument_id"] = "FOREIGN"
        else:
            raw["side_state"] = "INVALID"
        path.write_text("{" if fault == "corrupt" else json.dumps(raw))
        before = path.read_bytes()
        if fault == "corrupt":
            with pytest.raises(cursors.CurrentProductiveCursorError):
                begin(root)
        else:
            begin(root)
        assert path.read_bytes() == before
    finally:
        host.close()


def test_fence_write_failure_never_invokes_core_and_does_not_claim_publication(
    tmp_path, monkeypatch
):
    host, args, root, _ = seed_frame(tmp_path, monkeypatch, True, cursor_root=tmp_path / "LANE_1")
    try:
        before = load(root)
        calls = []

        def unavailable(*a, **kw):
            raise OSError("Synthetic fence storage unavailable")

        monkeypatch.setattr(
            cursors, "persist_current_productive_sidestate_confirmation_cursor_v1", unavailable
        )
        monkeypatch.setattr(
            durable,
            "run_current_productive_master_v2_runtime_cycle_v1",
            lambda **kw: calls.append(True),
        )
        pairs = {"LANE_1": _pair(tmp_path, "LANE_1", bound=_bound(), lane_state_root=str(root))}
        with pytest.raises(OSError, match="storage unavailable"):
            durable.compose_occupied_lane_mv2_dp_durable_cycle_v1(
                pairs, g17_typed_vol_producers=_lane_g17_producers(pairs), **_carry_kwargs()
            )
        assert not calls and load(root) == before
        # A failed durable write is NOT evidence of a negative published frame.
        # Independent sender/storage-outage coordination remains outside this proof.
        inspect_original_portfolio_execution_context_v1(**args)
    finally:
        host.close()
