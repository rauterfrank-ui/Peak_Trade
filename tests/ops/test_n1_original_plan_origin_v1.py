"""Preserve the actual N1 decision/plan origin; never create execution authority."""

from dataclasses import asdict, replace
from decimal import Decimal

import pytest
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
)

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    invoke_join_v1 as n1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
)
from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import _encode
from src.governance.canonical_order_intent_v1 import compute_semantic_digest
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops.test_original_budget_send_permit_handoff_v1 import cold_owner
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)


@pytest.mark.parametrize("short", [False, True])
def test_actual_n1_keeps_original_intent_and_venue_plan_in_original_store(
    tmp_path, monkeypatch, short
):
    from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1

    original_plan = n1.try_bind_current_productive_venue_plan_v1
    original_bind = Owner.bind_execution_plan_v1
    produced = []
    stored = []

    def plan(**kwargs):
        result = original_plan(**kwargs)
        if result[2] is not None:
            produced.append((kwargs["replay"].intermediate.canonical_order_intent, result[2]))
        return result

    def bind(owner, rid, envelope, **kwargs):
        result = original_bind(owner, rid, envelope, **kwargs)
        stored.append((owner, rid, envelope, owner.risk_snapshot_v1()["state"]))
        return result

    monkeypatch.setattr(n1, "try_bind_current_productive_venue_plan_v1", plan)
    monkeypatch.setattr(Owner, "bind_execution_plan_v1", bind)
    result = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    assert result.ok
    assert len(produced) == len(stored) == 1
    intent, venue_plan = produced[0]
    owner, rid, envelope, snapshot = stored[0]
    link = owner.execution_links_v1()[rid]
    assert link["plan_origin"]["canonical_order_intent"] == _encode(intent)
    assert link["plan_origin"]["venue_plan"] == asdict(venue_plan)
    assert link["phase"] == "PLAN_BOUND" and link["identity"] is None
    assert "external_effect_permit" not in link
    assert link["plan_origin"]["canonical_order_intent"]["decision_id"] == (
        result.policy_result.orchestrator_result.cycle_records[
            -1
        ].pending_decision_context.canonical_decision_id
    )
    assert venue_plan.environment == "LIVE"
    assert envelope.instrument_id == venue_plan.instrument_id != intent.instrument_id
    assert owner.active_sum_v1() > 0
    assert result.trace.post_count == 0
    assert owner.budget_state_v1().admitted is False
    original_origin = link["plan_origin"]
    # Capture occurred while the real owner was admitted. The supervisor has
    # closed it; its risk readback must not be reopened by a test helper.
    restored = Owner(
        durable_root=owner.durable_scope_identity_v1()["root"],
        durable_account_identity=snapshot["account_identity"],
        durable_mode="recover",
        durable_lane_bindings={
            lane: BoundInstrumentV1(**row["bound"])
            for lane, row in snapshot["lane_bindings"].items()
        },
    )
    try:
        assert restored.execution_links_v1()[rid]["plan_origin"] == original_origin
        assert restored.active_sum_v1() == owner.active_sum_v1() > 0
        assert restored.budget_state_v1().recovery_required
        with pytest.raises(ValueError, match="EXECUTION_SUBMIT_OWNER_FENCED"):
            restored.inspect_execution_submit_context_v1(rid, envelope, None)
    finally:
        restored.close()


def seed_with_origin(tmp_path, monkeypatch, *, origin=True):
    from tests.ops import test_portfolio_execution_recovery_v1 as original

    plan_builder = original.try_bind_current_productive_venue_plan_v1
    plan_bind = Owner.bind_execution_plan_v1
    source = []

    def plan(**kwargs):
        result = plan_builder(**kwargs)
        source.append((kwargs["replay"].intermediate.canonical_order_intent, result[2]))
        return result

    def bind(owner, rid, envelope):
        if origin is None:
            return None
        kwargs = dict(canonical_intent=source[-1][0], venue_plan=source[-1][1]) if origin else {}
        return plan_bind(owner, rid, envelope, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(original, "try_bind_current_productive_venue_plan_v1", plan)
        patch.setattr(Owner, "bind_execution_plan_v1", bind)
        host, rid, identity, envelope = original.seed(tmp_path)
    assert len(source) == 1
    return host, rid, identity, envelope, *source[0]


@pytest.mark.parametrize(
    "fault",
    [
        "decision_id",
        "instrument_id",
        "quantity",
        "config_digest",
        "capital_envelope_ref",
        "pre_sizing_risk_ref",
        "sizing_result_ref",
        "post_sizing_risk_ref",
        "quantity_provenance",
        "instrument_metadata_ref",
        "semantic_digest",
        "submission_authorized",
        "plan",
        "body",
        "environment",
        "missing_intent",
        "missing_plan",
    ],
)
def test_foreign_origin_cannot_bind_or_mutate_the_committed_hold(tmp_path, monkeypatch, fault):
    host, rid, identity, envelope, intent, plan = seed_with_origin(
        tmp_path, monkeypatch, origin=None
    )
    try:
        before = host.owner.risk_snapshot_v1()
        sequence = host.owner._store.sequence
        if fault == "quantity":
            intent = replace(intent, quantity=intent.quantity + Decimal(1))
        elif fault == "submission_authorized":
            intent = replace(intent, submission_authorized=True)
        elif fault == "semantic_digest":
            intent = replace(intent, semantic_digest="f" * 64)
        elif fault == "plan":
            plan = replace(plan, clordid="foreign-plan")
        elif fault == "body":
            plan = replace(plan, venue_native_payload={**plan.venue_native_payload, "sz": "999"})
        elif fault == "environment":
            plan = replace(plan, environment="paper")
        elif fault == "missing_intent":
            intent = None
        elif fault == "missing_plan":
            plan = None
        else:
            intent = replace(intent, **{fault: "foreign-origin"})
        if intent is not None and fault != "semantic_digest":
            # Even a self-consistent new digest cannot authorize foreign
            # decision/sizing references against the actual original store.
            intent = replace(intent, semantic_digest=compute_semantic_digest(intent))
        with pytest.raises(ValueError, match="EXECUTION_PLAN_ORIGIN|ORDER_ENVIRONMENT"):
            host.owner.bind_execution_plan_v1(
                rid, envelope, canonical_intent=intent, venue_plan=plan
            )
        assert host.owner.risk_snapshot_v1() == before
        assert host.owner._store.sequence == sequence
        assert host.owner.active_sum_v1() > 0
    finally:
        host.close()


def test_origin_readback_is_detached_and_exact_rebind_is_idempotent(tmp_path, monkeypatch):
    host, rid, identity, envelope, intent, plan = seed_with_origin(tmp_path, monkeypatch)
    try:
        before = host.owner.risk_snapshot_v1()
        sequence = host.owner._store.sequence
        output = host.owner.bind_execution_plan_v1(
            rid, envelope, canonical_intent=intent, venue_plan=plan
        )
        assert host.owner._store.sequence == sequence
        output["plan_origin"]["venue_plan"]["environment"] = "TESTNET"
        assert host.owner.risk_snapshot_v1() == before
        proof = host.owner.inspect_execution_submit_context_v1(rid, envelope, identity)
        assert proof["order_environment"] == plan.environment == "LIVE"
        assert (
            proof["plan_origin_digest"]
            == before["state"]["execution_links"][rid]["plan_origin"]["digest"]
        )
        assert host.owner._store.sequence == sequence
        with pytest.raises(ValueError, match="EXECUTION_PLAN_ORIGIN_CHANGED"):
            host.owner.bind_execution_plan_v1(rid, envelope)
        assert host.owner.risk_snapshot_v1() == before
    finally:
        host.close()


@pytest.mark.parametrize("environment", ["SHADOW", "TESTNET", "PAPER"])
def test_submit_consumer_denies_environment_different_from_actual_plan(
    tmp_path, monkeypatch, environment
):
    host, rid, identity, envelope, intent, plan = seed_with_origin(tmp_path, monkeypatch)
    try:
        before = host.owner.risk_snapshot_v1()
        with pytest.raises(ValueError, match="EXECUTION_IDENTITY_MISMATCH"):
            host.owner.mark_execution_submit_boundary_v1(
                rid, replace(identity, execution_environment=environment)
            )
        assert host.owner.risk_snapshot_v1() == before
        assert host.owner.active_sum_v1() > 0
    finally:
        host.close()


@pytest.mark.parametrize("fault", ["null", "missing-field", "digest", "foreign-ref", "body"])
def test_cold_restore_rechecks_exact_origin_without_defaults(tmp_path, monkeypatch, fault):
    host, rid, identity, envelope, intent, plan = seed_with_origin(tmp_path, monkeypatch)
    try:
        payload = host.owner.risk_snapshot_v1()["state"]
        origin = payload["execution_links"][rid]["plan_origin"]
        if fault == "null":
            payload["execution_links"][rid]["plan_origin"] = None
        elif fault == "missing-field":
            del origin["canonical_order_intent"]["permission_required"]
        elif fault == "digest":
            origin["digest"] = "f" * 64
        elif fault == "foreign-ref":
            bad = replace(intent, pre_sizing_risk_ref="foreign")
            origin["canonical_order_intent"] = _encode(
                replace(bad, semantic_digest=compute_semantic_digest(bad))
            )
        else:
            origin["venue_plan"]["venue_native_payload"]["tdMode"] = "isolated"
        if fault not in {"null", "digest"}:
            origin["digest"] = digest({k: v for k, v in origin.items() if k != "digest"})
        host.owner._store.save(payload)
        with pytest.raises(ValueError, match="DURABLE_BUDGET_SEMANTIC_RESTORE_UNPROVEN"):
            cold_owner(host)
    finally:
        host.close()


def test_legacy_origin_stays_absent_and_cannot_be_added_retrospectively(tmp_path, monkeypatch):
    host, rid, identity, envelope, intent, plan = seed_with_origin(
        tmp_path, monkeypatch, origin=False
    )
    try:
        before = host.owner.risk_snapshot_v1()
        assert "plan_origin" not in before["state"]["execution_links"][rid]
        assert "plan_origin_digest" not in host.owner.inspect_execution_submit_context_v1(
            rid, envelope, identity
        )
        with pytest.raises(ValueError, match="EXECUTION_PLAN_ORIGIN_CHANGED"):
            host.owner.bind_execution_plan_v1(
                rid, envelope, canonical_intent=intent, venue_plan=plan
            )
        assert host.owner.risk_snapshot_v1() == before
        restored = cold_owner(host)
        try:
            assert "plan_origin" not in restored.execution_links_v1()[rid]
            assert restored.active_sum_v1() > 0
        finally:
            restored.close()
    finally:
        host.close()


def test_original_recovery_preserves_intent_plan_and_separate_permit(tmp_path, monkeypatch):
    from tests.ops.test_portfolio_execution_recovery_v1 import ReadPort, NOW, _bound
    from tests.ops.test_portfolio_budget_host_v1 import _host, _fetch
    from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
        _permit,
    )

    host, rid, identity, envelope, intent, plan = seed_with_origin(tmp_path, monkeypatch)
    try:
        host.owner.mark_execution_submit_boundary_v1(
            rid, identity, external_effect_permit=_permit(envelope)
        )
        origin = host.owner.execution_links_v1()[rid]["plan_origin"]
    finally:
        host.close()
    restored = _host(
        tmp_path,
        _fetch(uid=identity.account_identity),
        clock=lambda: NOW,
        expected_account=identity.account_identity,
    )
    restored.reconciliation_transport = ReadPort(identity, state="canceled", filled="0")
    try:
        context = restored.observe_v1({"LANE_1": _bound()})
        assert context.execution_reconciliation[rid]["matched"]
        assert context.execution_reconciliation[rid]["reservation_released"]
        link = restored.owner.execution_links_v1()[rid]
        assert link["plan_origin"] == origin
        assert link["identity"] == identity.to_dict()
        assert link["external_effect_permit"]["permit_id"] == _permit(envelope).permit_id
        assert restored.owner.budget_state_v1().recovery_required
    finally:
        restored.close()


def test_actual_wrappers_keep_original_plan_origin_at_both_submit_barriers(tmp_path, monkeypatch):
    from tests.ops.test_prepost_original_budget_context_v1 import execute

    host, rid, identity, envelope, intent, plan = seed_with_origin(tmp_path, monkeypatch)
    calls = []

    class Opener:
        def open(self, *_args, **_kwargs):
            link = host.owner.execution_links_v1()[rid]
            assert link["phase"] == "SUBMIT_MAY_HAVE_OCCURRED"
            assert link["plan_origin"]["canonical_order_intent"] == _encode(intent)
            assert link["plan_origin"]["venue_plan"] == asdict(plan)
            assert link["identity"] == identity.to_dict()
            calls.append("fake-http")
            raise TimeoutError("Synthetic uncertainty without a socket")

    try:
        result = execute(
            dict(
                envelope=envelope,
                portfolio_budget_owner=host.owner,
                portfolio_reservation_id=rid,
                execution_identity=identity,
            ),
            tmp_path,
            opener=Opener(),
        )
        assert calls == ["fake-http"]
        assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
        assert result.replay_attempt_blocked == "true"
        assert host.owner.active_sum_v1() > 0
    finally:
        host.close()
