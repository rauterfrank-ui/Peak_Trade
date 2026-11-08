"""Current assessment outputs from today's producers through the original cursor."""

from dataclasses import replace
import json

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_sidestate_confirmation_cursor_v1 as cursors,
)
from src.ops.full_core_live_path_composition_root_v1 import (
    current_core_entry_assessment_frame_v1 as frames,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    inspect_original_portfolio_execution_context_v1,
    FullCoreEnvelopeBoundSendSeamError,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
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

NUMERIC_FAULTS = [
    "survival_nan",
    "survival_overflow",
    "survival_metric_bool",
    "survival_policy_inf",
]


def seed_frame(root, monkeypatch, modern):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_master_v2_runtime_cycle_v1 as runtime,
    )
    from trading.master_v2 import integrated_offline_trading_logic_replay_v1 as integrated

    captured = {}
    with monkeypatch.context() as patch:
        bind, outgoing = Owner.bind_execution_plan_v1, runtime._outgoing_cursor_from_replay_v1

        def bind_frame(*a, **kw):
            kw["entry_frame_required"] = True
            return bind(*a, **kw)

        def outgoing_frame(**kw):
            captured["replay"] = kw["replay"]
            return outgoing(**kw)

        patch.setattr(Owner, "bind_execution_plan_v1", bind_frame)
        patch.setattr(runtime, "_outgoing_cursor_from_replay_v1", outgoing_frame)
        for key, name in [
            ("c3", "evaluate_directional_assessment_with_confirmation_progress_v1"),
            ("survival", "evaluate_survival_assessment_v1"),
            ("survival_inputs", "_survival_input_for_assessment"),
            ("suitability", "evaluate_suitability_binding_v1"),
            ("composition", "evaluate_double_play_composition_matrix_v1"),
            ("entry", "evaluate_double_play_entry_exit_policy_v0"),
        ]:
            original = getattr(integrated, name)

            def capture(*a, _key=key, _original=original, **kw):
                captured[_key] = (a, kw, _original)
                if _key == "survival_inputs":
                    captured["input"] = a[0]
                return _original(*a, **kw)

            patch.setattr(integrated, name, capture)
        host, args, cursor_root = seed_core(root, monkeypatch, modern)
    assert "replay" in captured and captured["replay"].intermediate is not None
    return host, args, cursor_root, captured


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("fault", ["cost", "metric", "validity"])
def test_host_numeric_admission_restricts_entry_before_financial_handoff(
    tmp_path, monkeypatch, modern, fault
):
    from trading.master_v2 import integrated_offline_trading_logic_replay_v1 as integrated
    from trading.master_v2.double_play_entry_exit_policy_v0 import TradingGate
    from src.ops.full_core_live_path_composition_root_v1.current_productive_numeric_entry_admission_v1 import (
        prepare_current_productive_numeric_entry_v1,
    )

    host, args, root, captured = seed_frame(tmp_path, monkeypatch, modern)
    try:
        inp = captured["input"]
        original_builder = integrated._survival_input_for_assessment

        def invalid_input(*a, **kw):
            value = original_builder(*a, **kw)
            if fault == "cost":
                return replace(
                    value, cost_inputs=replace(value.cost_inputs, entry_fee=float("nan"))
                )
            if fault == "metric":
                return replace(
                    value,
                    metric_inputs=replace(value.metric_inputs, data_completeness_complete="False"),
                )
            return value

        if fault == "validity":
            inp = replace(
                inp,
                policies=replace(
                    inp.policies, survival=replace(inp.policies.survival, validity_epochs=0)
                ),
            )
        monkeypatch.setattr(integrated, "_survival_input_for_assessment", invalid_input)
        cursor_before = cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
        admitted, preview, reasons = prepare_current_productive_numeric_entry_v1(
            inp, replay_runner=integrated.run_integrated_offline_trading_logic_replay_v1
        )
        assert preview is None and reasons
        assert admitted.trading_gate is TradingGate.EXIT_ONLY
        assert admitted.input_digest != inp.input_digest
        assert admitted.directional_confirmation_progress is inp.directional_confirmation_progress
        assert admitted.observation_acceptance_result is inp.observation_acceptance_result
        if fault == "validity":
            assert admitted.policies.survival.validity_epochs == 1
        result = integrated.run_integrated_offline_trading_logic_replay_v1(admitted)
        assert result.intermediate is not None
        mid = result.intermediate
        side = "bull" if mid.bull_survival is not None else "bear"
        assert getattr(mid, side + "_assessment").status.value == "confirmed"
        assert (
            mid.directional_confirmation_progress_after
            == captured["replay"].intermediate.directional_confirmation_progress_after
        )
        assert mid.entry_exit_decision.decision_outcome.value not in {"enter_long", "enter_short"}
        assert (
            cursors.load_current_productive_sidestate_confirmation_cursor_v1(root) == cursor_before
        )
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
def test_valid_host_numeric_admission_reuses_exact_native_preview(tmp_path, monkeypatch, modern):
    from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
        DdoCaptureBindingV0,
        bind_capture_session_v0,
        current_capture_binding_v0,
        reset_capture_session_v0,
    )
    from trading.master_v2 import integrated_offline_trading_logic_replay_v1 as integrated
    from src.ops.full_core_live_path_composition_root_v1.current_productive_numeric_entry_admission_v1 import (
        prepare_current_productive_numeric_entry_v1,
    )

    host, args, root, captured = seed_frame(tmp_path, monkeypatch, modern)
    outer = DdoCaptureBindingV0(enabled=True, ledger_path=tmp_path / "outer-ddo.jsonl")
    token = bind_capture_session_v0(outer)
    try:
        calls = []

        def run(value):
            assert current_capture_binding_v0().enabled is False
            result = integrated.run_integrated_offline_trading_logic_replay_v1(value)
            calls.append(result)
            return result

        inp = captured["input"]
        admitted, preview, reasons = prepare_current_productive_numeric_entry_v1(
            inp, replay_runner=run
        )
        assert admitted is inp and not reasons and calls == [preview]
        assert preview.evidence == captured["replay"].evidence
        assert current_capture_binding_v0() is outer
        assert not outer.captured_records and not outer.ledger_path.exists()
    finally:
        reset_capture_session_v0(token)
        host.close()


@pytest.mark.parametrize("modern", [False, True])
def test_current_frame_rejects_nonfinite_direct_native_legacy_output(tmp_path, monkeypatch, modern):
    host, args, root, captured = seed_frame(tmp_path, monkeypatch, modern)
    try:
        a, kw, native = captured["survival"]
        value = replace(a[0], cost_inputs=replace(a[0].cost_inputs, entry_fee=float("nan")))
        survival = native(value, a[1], **kw)
        assert survival.status.value == "pass"
        original = captured["replay"]
        prefix = "bull" if original.intermediate.bull_survival is not None else "bear"
        replay = replace(
            original,
            intermediate=replace(original.intermediate, **{prefix + "_survival": survival}),
        )
        cursor = cursors.parse_current_productive_sidestate_confirmation_cursor_v1(
            cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
        )
        frame = frames.build_current_core_entry_assessment_frame_v1(
            replay=replay, confirmation_state=cursor.cap61_confirmation_state
        )
        with pytest.raises(ValueError, match="CURRENT_CORE_ASSESSMENT_NUMERIC_OUTPUT_NONFINITE"):
            frames.read_current_core_entry_assessment_frame_v1(
                replace(cursor, entry_assessment_frame=frame)
            )
    finally:
        host.close()


def publish_frame(root, captured, fault):
    raw = cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
    cursor = cursors.parse_current_productive_sidestate_confirmation_cursor_v1(raw)
    original = captured["replay"]
    if fault in {"missing", "corrupt", "epoch", "c3_binding", "declaration", "eligibility"}:
        frame = json.loads(json.dumps(cursor.entry_assessment_frame))
        if fault == "missing":
            frame = None
        elif fault == "corrupt":
            frame["digest"] = "0" * 64
        elif fault in {"declaration", "eligibility"}:
            import hashlib

            component = frame["components"]["parent"]
            body = json.loads(component["canonical"])
            del body["runtime_effect" if fault == "declaration" else "execution_eligible"]
            component["canonical"] = json.dumps(body, sort_keys=True, separators=(",", ":"))
            component["semantic_digest"] = hashlib.sha256(
                component["canonical"].encode()
            ).hexdigest()
            frame["digest"] = frames._digest({k: v for k, v in frame.items() if k != "digest"})
        else:
            if fault == "epoch":
                frame["trading_epoch"] += 1
            else:
                frame["confirmation_state_digest"] = "0" * 64
            frame["digest"] = frames._digest({k: v for k, v in frame.items() if k != "digest"})
    elif fault in {"same", "new_identity"}:
        if fault == "new_identity":
            from trading.master_v2.canonical_trading_decision_evidence_v1 import (
                derive_decision_id,
                with_computed_evidence_semantic_digest,
            )

            parent = original.evidence
            parent = replace(
                parent,
                decision_id=derive_decision_id(
                    replay_id=parent.replay_id + "-next-assessment",
                    instrument_id=parent.instrument_id,
                    trading_epoch=parent.trading_epoch,
                    input_digest=parent.input_digest,
                ),
            )
            original = replace(original, evidence=with_computed_evidence_semantic_digest(parent))
        frame = frames.build_current_core_entry_assessment_frame_v1(
            replay=original, confirmation_state=cursor.cap61_confirmation_state
        )
    else:
        from trading.master_v2.canonical_trading_decision_evidence_v1 import (
            with_computed_evidence_semantic_digest,
        )
        from trading.master_v2.double_play_entry_exit_policy_v0 import (
            compute_entry_exit_policy_input_digest,
        )
        from trading.master_v2.double_play_composition_matrix_v1 import (
            build_single_lane_composition_candidate_v1,
            compute_composition_input_digest,
        )
        from trading.master_v2.suitability_binding_v1 import SuitabilityRegimeStatus

        mid = original.intermediate
        short = mid.entry_exit_decision.selected_side.value == "short"
        prefix = "bear" if short else "bull"
        assessment = getattr(mid, prefix + "_assessment")
        if fault == "c3":
            a, kw, evaluate = captured["c3"]
            inp = a[0]
            from trading.market_state.directional_confirmation_progress_v1 import ConfirmationSideV1

            side = ConfirmationSideV1.SHORT if short else ConfirmationSideV1.LONG
            inp = replace(
                inp,
                prior_confirmation_progress=cursor.cap61_confirmation_state.confirmation_side_carrier.for_side(
                    side
                ),
                directional_input=replace(inp.directional_input, trusted_data=False),
            )
            result = evaluate(inp, **kw)
            assert result.confirmation_progress_after.assessment_state.value == "confirmed"
            assert result.assessment.status.value in {"blocked", "invalid"}
            assessment = result.assessment
        a, kw, evaluate = captured["survival"]
        surv_inp = replace(a[0], directional_assessment=assessment)
        if fault == "survival":
            surv_inp = replace(
                surv_inp, cost_inputs=replace(surv_inp.cost_inputs, expected_gross_edge=None)
            )
        elif fault == "survival_nan":
            surv_inp = replace(
                surv_inp, cost_inputs=replace(surv_inp.cost_inputs, entry_fee=float("nan"))
            )
        elif fault == "survival_overflow":
            surv_inp = replace(
                surv_inp, cost_inputs=replace(surv_inp.cost_inputs, entry_fee=1e308, exit_fee=1e308)
            )
        elif fault == "survival_metric_bool":
            surv_inp = replace(
                surv_inp,
                metric_inputs=replace(surv_inp.metric_inputs, data_completeness_complete="False"),
            )
        survival_policy = a[1]
        if fault == "survival_policy_inf":
            survival_policy = replace(survival_policy, min_net_edge=float("inf"))
        from trading.master_v2.survival_numeric_admission_v1 import (
            evaluate_survival_with_numeric_admission_v1,
        )

        survival = evaluate_survival_with_numeric_admission_v1(surv_inp, survival_policy)
        if fault in NUMERIC_FAULTS:
            assert survival.status.value == "blocked"
        a, kw, evaluate = captured["suitability"]
        suit_inp = replace(a[0], directional_assessment=assessment, survival_result=survival)
        if fault == "suitability":
            suit_inp = replace(suit_inp, regime_status=SuitabilityRegimeStatus.UNKNOWN)
        suitability = evaluate(suit_inp, a[1], **kw)
        candidate = build_single_lane_composition_candidate_v1(
            long_assessment=None if short else assessment,
            long_survival=None if short else survival,
            long_suitability=None if short else suitability,
            short_assessment=assessment if short else None,
            short_survival=survival if short else None,
            short_suitability=suitability if short else None,
        )
        a, kw, evaluate = captured["composition"]
        comp_inp = replace(a[0], candidate=candidate, input_digest="")
        comp_inp = replace(comp_inp, input_digest=compute_composition_input_digest(comp_inp))
        composition = evaluate(comp_inp, a[1], **kw)
        a, kw, evaluate = captured["entry"]
        entry_inp = replace(a[0], composition_result=composition, input_digest="")
        if fault == "cooldown":
            entry_inp = replace(entry_inp, cooldown_pass=False)
        entry_inp = replace(
            entry_inp, input_digest=compute_entry_exit_policy_input_digest(entry_inp)
        )
        entry = evaluate(entry_inp, a[1], **kw)
        assert entry.decision_outcome.value not in {"enter_long", "enter_short"}
        parent = replace(
            original.evidence,
            **{
                prefix + "_assessment_ref": assessment.assessment_id,
                prefix + "_survival_ref": survival.survival_id,
                prefix + "_suitability_ref": suitability.suitability_id,
            },
            composition_result_ref=composition.composition_id,
            entry_exit_policy_ref=entry.policy_decision_id,
            entry_or_exit_policy_ref=entry.policy_decision_id,
            decision_outcome=entry.decision_outcome.value,
            selected_side=composition.selected_side.value,
            selected_strategy_ref=suitability.selected_strategy_id or "",
            reason_codes=entry.reason_codes,
            decision_precedence_trace=entry.decision_precedence_trace,
        )
        parent = with_computed_evidence_semantic_digest(parent)
        mid = replace(
            mid,
            **{
                prefix + "_assessment": assessment,
                prefix + "_survival": survival,
                prefix + "_suitability": suitability,
            },
            composition_result=composition,
            entry_exit_decision=entry,
        )
        frame = frames.build_current_core_entry_assessment_frame_v1(
            replay=replace(original, evidence=parent, intermediate=mid),
            confirmation_state=cursor.cap61_confirmation_state,
        )
    cursors.persist_current_productive_sidestate_confirmation_cursor_v1(
        replace(cursor, entry_assessment_frame=frame),
        store_root=root,
        expected_prior_digest=cursors.current_productive_cursor_digest_v1(raw),
    )


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize(
    "fault",
    [
        "c3",
        "survival",
        "suitability",
        "cooldown",
        "missing",
        "corrupt",
        "epoch",
        "c3_binding",
        "declaration",
        "eligibility",
        *NUMERIC_FAULTS,
    ],
)
def test_current_assessment_frame_vetoes_while_c3_progress_stays_confirmed(
    tmp_path, monkeypatch, modern, fault
):
    from src.ops.portfolio_capital_reservation_budget_v1.core_confirmation_source_v1 import (
        bind_core_confirmation_lineage_v1,
        inspect_current_core_confirmation_v1,
    )

    host, args, root, captured = seed_frame(tmp_path, monkeypatch, modern)
    try:
        inspect_original_portfolio_execution_context_v1(**args)
        publish_frame(root, captured, fault)
        raw = cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
        cursor = cursors.parse_current_productive_sidestate_confirmation_cursor_v1(raw)
        assert (
            inspect_current_core_confirmation_v1(
                bind_core_confirmation_lineage_v1(cursor),
                cursor=cursor,
                raw=raw,
                intent_side="LONG",
            )["confirmation_status"]
            == "confirmed"
        )
        before, held = files(tmp_path), host.owner.active_sum_v1()
        with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="CURRENT_CORE_ASSESSMENT"):
            inspect_original_portfolio_execution_context_v1(**args)
        assert files(tmp_path) == before and host.owner.active_sum_v1() == held > 0
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("progress", ["same", "new_identity"])
def test_valid_current_outputs_do_not_require_original_frame_digest_or_decision_identity(
    tmp_path, monkeypatch, modern, progress
):
    host, args, root, captured = seed_frame(tmp_path, monkeypatch, modern)
    try:
        original = inspect_original_portfolio_execution_context_v1(**args)
        publish_frame(root, captured, progress)
        assert inspect_original_portfolio_execution_context_v1(**args) == original
        proof = host.owner.inspect_current_core_cursor_v1(
            args["portfolio_reservation_id"], args["envelope"]
        )["assessment"]
        assert proof["scope"] == "CURRENT_ORIGINAL_ASSESSMENT_OUTPUT_VETO_ONLY"
        assert (
            proof["economic_input_provenance"] == "NOT_ASSESSED"
            and proof["runtime_authorization_effect"] == "NONE"
        )
    finally:
        host.close()


@pytest.mark.parametrize("short", [False, True])
def test_actual_current_n1_writer_publishes_and_binds_its_assessment_frame(
    tmp_path, monkeypatch, short
):
    from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1

    bind, observed = Owner.bind_execution_plan_v1, []

    def capture(owner, rid, envelope, **kw):
        assert kw["entry_frame_required"] is True
        result = bind(owner, rid, envelope, **kw)
        source = result["plan_origin"]["core_cursor_source"]
        assert source["schema"] == "portfolio_original_core_cursor_source.v3"
        cursor = cursors.parse_current_productive_sidestate_confirmation_cursor_v1(
            cursors.load_current_productive_sidestate_confirmation_cursor_v1(kw["core_cursor_root"])
        )
        assert (
            source["entry_frame_reference"]["initial_frame_digest"]
            == cursor.entry_assessment_frame["digest"]
        )
        bodies = frames.read_current_core_entry_assessment_frame_v1(cursor)
        assert bodies["parent"]["decision_id"] == kw["core_parent"].decision_id
        proof = owner.inspect_current_core_cursor_v1(rid, envelope)
        assert proof["assessment"]["economic_input_provenance"] == "NOT_ASSESSED"
        observed.append(True)
        return result

    monkeypatch.setattr(Owner, "bind_execution_plan_v1", capture)
    result = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    assert result.ok and observed == [True] and result.trace.post_count == 0


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("phase", ["before_get", "after_get", "during_k1", "opener_factory"])
@pytest.mark.parametrize("fault", ["c3", *NUMERIC_FAULTS])
def test_actual_post_rechecks_current_blocked_assessment_before_socket(
    tmp_path, monkeypatch, modern, phase, fault
):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, args, root, captured = seed_frame(tmp_path, monkeypatch, modern)
    owner = host.owner
    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )
    changed, sockets = [], []

    def change():
        if not changed:
            publish_frame(root, captured, fault)
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
            raise AssertionError("No socket after blocked current frame")

    def factory():
        if phase == "opener_factory":
            change()
        return Opener()

    if phase == "before_get":
        change()
    port, held = Port(args), owner.active_sum_v1()
    try:
        with pytest.raises(
            caller.CurrentProductiveActualVenuePostError, match="CURRENT_CORE_ASSESSMENT"
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
            assert record["durable_state"] == "ABORTED_BEFORE_TRANSPORT" and record[
                "transport_attempt"
            ]["reason_code"].startswith("POST_BUDGET")
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("fault", ["c3", *NUMERIC_FAULTS])
def test_blocked_assessment_after_possible_socket_retains_unknown_and_hold(
    tmp_path, monkeypatch, modern, fault
):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, args, root, captured = seed_frame(tmp_path, monkeypatch, modern)
    owner = host.owner
    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )
    calls = []

    class Opener:
        def open(self, *a, **kw):
            calls.append(True)
            publish_frame(root, captured, fault)
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
@pytest.mark.parametrize("fault", ["c3", *NUMERIC_FAULTS])
def test_republished_admissible_frame_cannot_reopen_consumed_abort(
    tmp_path, monkeypatch, modern, fault
):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, args, root, captured = seed_frame(tmp_path, monkeypatch, modern)
    owner = host.owner
    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )

    class Backend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kw):
            value = super().copy_matching_generic_password_value_data_v1(**kw)
            publish_frame(root, captured, fault)
            return value

    common = dict(
        owner_go=caller.OWNER_GO,
        baseline_origin_main_sha=caller.EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        store_root=tmp_path / "send",
        evidence_root=tmp_path / "evidence",
        perform_real_venue_post=True,
        opener_factory=lambda: (_ for _ in ()).throw(AssertionError("No transport after abort")),
        execution_integrity_backend=_clean_post_integrity(),
    )
    try:
        with pytest.raises(
            caller.CurrentProductiveActualVenuePostError, match="CURRENT_CORE_ASSESSMENT"
        ):
            caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
                **args, **common, k1_backend=Backend(), read_only_get_transport=AccountPort(args)
            )
        publish_frame(root, captured, "same")
        assert (
            owner.inspect_current_core_cursor_v1(
                args["portfolio_reservation_id"], args["envelope"]
            )["assessment"]["scope"]
            == "CURRENT_ORIGINAL_ASSESSMENT_OUTPUT_VETO_ONLY"
        )
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


def test_previous_explicit_source_version_is_not_implicitly_assessment_admitted(
    tmp_path, monkeypatch
):
    host, args, root = seed_core(tmp_path, monkeypatch, True)
    try:
        raw = cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
        cursor = cursors.parse_current_productive_sidestate_confirmation_cursor_v1(raw)
        cursors.persist_current_productive_sidestate_confirmation_cursor_v1(
            replace(cursor, entry_assessment_frame=None),
            store_root=root,
            expected_prior_digest=cursors.current_productive_cursor_digest_v1(raw),
        )
        proof = host.owner.inspect_current_core_cursor_v1(
            args["portfolio_reservation_id"], args["envelope"]
        )
        assert proof["assessment"] == {"scope": "LEGACY_ORIGINAL_ASSESSMENT_FRAME_NOT_ASSESSED"}
        assert (
            inspect_original_portfolio_execution_context_v1(**args)["scope"]
            == "ORIGINAL_COMMITTED_PLAN_CONTEXT_ONLY"
        )
    finally:
        host.close()


def test_existing_cursor_cas_publication_cannot_split_frame_and_confirmation(tmp_path, monkeypatch):
    host, args, root, captured = seed_frame(tmp_path, monkeypatch, True)
    try:
        raw = cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
        cursor = cursors.parse_current_productive_sidestate_confirmation_cursor_v1(raw)
        publish_frame(root, captured, "c3")
        current = cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
        with pytest.raises(
            cursors.CurrentProductiveCursorError, match="CURSOR_PUBLICATION_CONFLICT"
        ):
            cursors.persist_current_productive_sidestate_confirmation_cursor_v1(
                cursor,
                store_root=root,
                expected_prior_digest=cursors.current_productive_cursor_digest_v1(raw),
            )
        assert cursors.load_current_productive_sidestate_confirmation_cursor_v1(root) == current
        with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="CURRENT_CORE_ASSESSMENT"):
            inspect_original_portfolio_execution_context_v1(**args)
    finally:
        host.close()
