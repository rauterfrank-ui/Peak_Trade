"""Current plan composition must consume the actual original decision parent."""

from dataclasses import replace

import pytest

from src.governance.canonical_order_intent_v1 import compute_semantic_digest
from src.ops.full_core_live_path_composition_root_v1.models_v1 import CompositionStatusV1
from tests.ops.test_current_productive_venue_plan_td_mode_and_order_environment_authority_v1 import (
    _enter_replay,
    _bind,
)
from tests.ops.test_prepost_original_budget_context_v1 import no_network as no_network
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    finalize_offline_replay_decision_evidence_v1,
)


def changed_child(replay, **fields):
    old = replay.intermediate.canonical_order_intent
    intent = replace(old, **fields)
    intent = replace(intent, semantic_digest=compute_semantic_digest(intent))
    evidence = finalize_offline_replay_decision_evidence_v1(
        replace(replay.evidence, order_intent_ref=intent.semantic_digest)
    )
    return replace(
        replay,
        evidence=evidence,
        intermediate=replace(replay.intermediate, canonical_order_intent=intent),
    )


@pytest.mark.parametrize(
    "fault",
    [
        "decision",
        "epoch",
        "opposite_action",
        "intent_ref",
        "risk_ref",
        "quantity_ref",
        "parent_digest",
        "risk_effect",
        "intent_effect",
        "sizing_ref",
        "capital_ref",
        "post_risk_ref",
        "bad_child_digest",
    ],
)
def test_current_binder_denies_a_foreign_or_unbound_original_parent(monkeypatch, fault):
    replay = _enter_replay()
    intent = replay.intermediate.canonical_order_intent
    if fault == "decision":
        replay = changed_child(replay, decision_id="foreign-original-decision")
    elif fault == "epoch":
        replay = changed_child(replay, trading_epoch=str(int(intent.trading_epoch) + 1))
    elif fault == "opposite_action":
        short = intent.intent_action == "ENTER_LONG"
        side = "SHORT" if short else "LONG"
        replay = changed_child(
            replay, intent_action="ENTER_" + side, side=side, expected_position_side=side
        )
    elif fault in {"intent_ref", "risk_ref", "quantity_ref", "risk_effect", "intent_effect"}:
        field = {
            "intent_ref": "order_intent_ref",
            "risk_ref": "risk_sizing_ref",
            "quantity_ref": "quantity_provenance_ref",
            "risk_effect": "risk_sizing_effect",
            "intent_effect": "order_intent_effect",
        }[fault]
        replay = replace(
            replay,
            evidence=finalize_offline_replay_decision_evidence_v1(
                replace(replay.evidence, **{field: "foreign-or-unbound"})
            ),
        )
    elif fault == "parent_digest":
        replay = replace(replay, evidence=replace(replay.evidence, semantic_digest="f" * 64))
    elif fault == "bad_child_digest":
        bad = replace(intent, semantic_digest="f" * 64)
        replay = replace(
            replay,
            intermediate=replace(replay.intermediate, canonical_order_intent=bad),
            evidence=finalize_offline_replay_decision_evidence_v1(
                replace(replay.evidence, order_intent_ref=bad.semantic_digest)
            ),
        )
    else:
        field = {
            "sizing_ref": "sizing_result_ref",
            "capital_ref": "capital_envelope_ref",
            "post_risk_ref": "post_sizing_risk_ref",
        }[fault]
        replay = changed_child(replay, **{field: "foreign-source"})
    status, reasons, plan = _bind(monkeypatch, replay, execution_mode="LIVE")
    assert status is CompositionStatusV1.DENY, (fault, status, reasons, plan)
    assert plan is None


def test_actual_original_parent_remains_bound_without_replacing_its_epoch(monkeypatch):
    replay = _enter_replay()
    before = replay.evidence
    status, reasons, plan = _bind(
        monkeypatch, replay, execution_mode="LIVE", composed_epoch="2099-01-01T00:00:00Z"
    )
    assert status is CompositionStatusV1.PASS, reasons
    assert plan is not None
    assert replay.evidence == before
    assert replay.intermediate.canonical_order_intent.trading_epoch == str(before.trading_epoch)


@pytest.mark.parametrize(
    "field,value",
    [
        ("execution_eligible", True),
        ("adapter_compatible", True),
        ("authority_effect", "GRANT"),
        ("runtime_effect", "SEND"),
        ("order_effect", "SUBMIT"),
        ("trading_epoch", True),
        ("trading_epoch", "1"),
    ],
)
def test_parent_declaration_does_not_promote_authority_or_change_epoch_type(
    monkeypatch, field, value
):
    from trading.master_v2.canonical_trading_decision_evidence_v1 import (
        compute_canonical_trading_decision_evidence_semantic_digest,
    )

    replay = _enter_replay()
    evidence = replace(replay.evidence, **{field: value})
    # Use the exact original hash without the finalizer's deliberate reset of
    # authority flags: the malformed declaration itself must reach the consumer.
    evidence = replace(
        evidence,
        semantic_digest=compute_canonical_trading_decision_evidence_semantic_digest(evidence),
    )
    status, reasons, plan = _bind(
        monkeypatch, replace(replay, evidence=evidence), execution_mode="LIVE"
    )
    assert status is CompositionStatusV1.DENY
    assert plan is None and any(r.startswith("ENTRY_ORIGINAL") for r in reasons)


@pytest.mark.parametrize(
    "fault,expected",
    [
        ("missing_digest", "WRONG_IDENTITY"),
        ("seen_digest", "DUPLICATE_INTENT"),
        ("explicit_epoch", "STALE_CANONICAL_ORDER_INTENT"),
    ],
)
def test_existing_identity_replay_and_explicit_epoch_denials_keep_their_reason(
    monkeypatch, fault, expected
):
    replay = _enter_replay()
    intent = replay.intermediate.canonical_order_intent
    kwargs = dict(execution_mode="LIVE")
    if fault == "missing_digest":
        replay = replace(
            replay,
            intermediate=replace(
                replay.intermediate, canonical_order_intent=replace(intent, semantic_digest="")
            ),
        )
    elif fault == "explicit_epoch":
        # The old explicit caller contract is separate from the new actual
        # original-parent check and retains its earlier failure precedence.
        from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
            _bound,
        )
        from src.ops.full_core_live_path_composition_root_v1.composition_root_v1 import (
            compose_core_live_execution_intent_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.constants_v1 import MODE_LIVE

        status, reasons, plan = compose_core_live_execution_intent_v1(
            replay=replay,
            bound_instrument=_bound(),
            mode=MODE_LIVE,
            composed_epoch="unchanged-composition-reference",
            expected_trading_epoch="different-original-epoch",
        )
        assert status is CompositionStatusV1.DENY and plan is None and expected in reasons
        return
    else:
        from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
            _bound,
        )
        from src.ops.full_core_live_path_composition_root_v1.composition_root_v1 import (
            compose_core_live_execution_intent_v1,
        )
        from src.ops.full_core_live_path_composition_root_v1.constants_v1 import MODE_LIVE

        status, reasons, plan = compose_core_live_execution_intent_v1(
            replay=replay,
            bound_instrument=_bound(),
            mode=MODE_LIVE,
            composed_epoch="unchanged-composition-reference",
            seen_semantic_digests=frozenset({intent.semantic_digest}),
        )
        assert status is CompositionStatusV1.DENY and plan is None and expected in reasons
        return
    status, reasons, plan = _bind(monkeypatch, replay, **kwargs)
    assert status is CompositionStatusV1.DENY and plan is None and expected in reasons


@pytest.mark.parametrize("short", [False, True])
@pytest.mark.parametrize("fault", ["epoch", "decision", "opposite_action"])
def test_actual_n1_rejects_foreign_child_before_plan_commit_and_uses_original_release(
    tmp_path, monkeypatch, short, fault
):
    from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
        invoke_join_v1 as n1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    )

    original_bind = n1.try_bind_current_productive_venue_plan_v1
    original_release = Owner.release_plan_failure_v1
    original_plan_write = Owner.bind_execution_plan_v1
    calls, releases, plans = [], [], []

    def bind(**kwargs):
        replay = kwargs["replay"]
        intent = replay.intermediate.canonical_order_intent
        if fault == "epoch":
            replay = changed_child(replay, trading_epoch=str(int(intent.trading_epoch) + 1))
        elif fault == "decision":
            replay = changed_child(replay, decision_id="foreign-core-parent")
        else:
            side = "LONG" if short else "SHORT"
            replay = changed_child(
                replay, intent_action="ENTER_" + side, side=side, expected_position_side=side
            )
        result = original_bind(**{**kwargs, "replay": replay})
        calls.append(result)
        return result

    def release(owner, rid):
        before = owner.active_sum_v1()
        result = original_release(owner, rid)
        releases.append((before, owner.active_sum_v1(), owner.execution_links_v1()))
        return result

    def write(*args, **kwargs):
        plans.append(True)
        return original_plan_write(*args, **kwargs)

    monkeypatch.setattr(n1, "try_bind_current_productive_venue_plan_v1", bind)
    monkeypatch.setattr(Owner, "release_plan_failure_v1", release)
    monkeypatch.setattr(Owner, "bind_execution_plan_v1", write)
    result = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    assert len(calls) == len(releases) == 1 and plans == []
    status, reasons, plan = calls[0]
    assert status is CompositionStatusV1.DENY and plan is None
    assert "ENTRY_ORIGINAL_DECISION_PARENT_MISMATCH" in reasons
    held, remaining, links = releases[0]
    assert held > 0 and remaining == 0 and links == {}
    assert result.trace.post_count == 0 and result.policy_result.post_allowed is False


def test_parent_readback_is_visible_in_original_predicate_trace_and_stays_plan_only():
    from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
        _bound,
    )
    from src.ops.full_core_live_path_composition_root_v1.composition_root_v1 import (
        compose_core_live_execution_intent_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.constants_v1 import MODE_LIVE

    replay = _enter_replay()
    trace = []
    status, reasons, intent = compose_core_live_execution_intent_v1(
        replay=replay,
        bound_instrument=_bound(),
        mode=MODE_LIVE,
        composed_epoch="separate-composition-reference",
        predicate_trace_collector=trace,
    )
    assert status is CompositionStatusV1.PASS, reasons
    assert intent.source_decision_id == replay.evidence.decision_id
    assert intent.source_trading_epoch == str(replay.evidence.trading_epoch)
    assert intent.submission_authorized is False and intent.execution_eligible is False
    assert any(
        r["predicate_name"] == "original_decision_parent" and r["predicate_result"] == "PASS"
        for r in trace
    )


def test_original_parent_owners_are_integrity_protected_at_actual_post():
    from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
        PROTECTED_CURRENT_PRODUCTIVE_POST_SLICE_SURFACE_PATHS,
    )

    for path in [
        "src/ops/full_core_live_path_composition_root_v1/composition_root_v1.py",
        "src/trading/master_v2/canonical_trading_decision_evidence_v1.py",
        "src/trading/master_v2/canonical_order_intent_offline_replay_binding_adapter_v0.py",
        "src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py",
    ]:
        assert path in PROTECTED_CURRENT_PRODUCTIVE_POST_SLICE_SURFACE_PATHS
