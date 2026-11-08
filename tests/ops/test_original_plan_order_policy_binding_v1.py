"""The original plan must preserve the canonical order's declared wire policy."""

from dataclasses import replace

import pytest

from src.governance.canonical_order_intent_v1 import compute_semantic_digest
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from tests.ops.test_n1_original_plan_origin_v1 import seed_with_origin
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
)
from tests.ops.test_prepost_original_budget_context_v1 import no_network as no_network
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)


def with_policy(intent, **changes):
    intent = replace(intent, **changes)
    return replace(intent, semantic_digest=compute_semantic_digest(intent))


def plan_and_order(plan, old, *, limit):
    payload = {**plan.venue_native_payload, "ordType": "limit" if limit else "market"}
    if limit:
        payload["px"] = "10.03"
    else:
        payload.pop("px", None)
    plan = replace(plan, order_type="limit" if limit else "market", venue_native_payload=payload)
    order = bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref=old.admission_ref,
        provenance_ref=old.provenance_ref,
        creation_epoch=old.creation_epoch,
    )
    return plan, order


@pytest.mark.parametrize(
    "fault",
    [
        "market_as_limit",
        "limit_as_market",
        "unknown_policy",
        "different_limit_price",
        "unbound_limit_price",
        "contradictory_side",
        "market_price_policy",
        "ioc",
        "fok",
        "unknown_tif",
        "post_only",
    ],
)
def test_original_writer_rejects_self_consistent_digest_with_contradictory_policy(
    tmp_path, monkeypatch, fault
):
    host, rid, _, order, intent, plan = seed_with_origin(tmp_path, monkeypatch, origin=None)
    try:
        before = host.owner.risk_snapshot_v1()
        sequence = host.owner._store.sequence
        if fault in {"market_as_limit", "different_limit_price", "unbound_limit_price"}:
            plan, order = plan_and_order(plan, order, limit=True)
        if fault == "limit_as_market":
            intent = with_policy(
                intent, order_type_policy="LIMIT_ONLY", price_policy="EXPLICIT_PRICE:10.03"
            )
        elif fault == "unknown_policy":
            intent = with_policy(intent, order_type_policy="UNKNOWN")
        elif fault == "different_limit_price":
            intent = with_policy(
                intent, order_type_policy="LIMIT_ONLY", price_policy="EXPLICIT_PRICE:9.99"
            )
        elif fault == "unbound_limit_price":
            intent = with_policy(intent, order_type_policy="LIMIT_ONLY")
        elif fault == "market_price_policy":
            intent = with_policy(intent, price_policy="EXPLICIT_PRICE:10.03")
        elif fault in {"ioc", "fok", "unknown_tif"}:
            intent = with_policy(
                intent,
                time_in_force_policy={"ioc": "IOC", "fok": "FOK", "unknown_tif": "DAY"}[fault],
            )
        elif fault == "post_only":
            intent = with_policy(intent, max_slippage_policy="POST_ONLY")
        elif fault == "contradictory_side":
            intent = with_policy(intent, side="SHORT" if intent.side == "LONG" else "LONG")
        with pytest.raises(ValueError, match="EXECUTION_PLAN_ORIGIN"):
            host.owner.bind_execution_plan_v1(rid, order, canonical_intent=intent, venue_plan=plan)
        assert host.owner.risk_snapshot_v1() == before
        assert host.owner._store.sequence == sequence
        assert host.owner.active_sum_v1() > 0
    finally:
        host.close()


@pytest.mark.parametrize(
    "raw", ["", "NaN", "sNaN", "Infinity", "-Infinity", "0", "-1", "not-a-price"]
)
def test_declared_limit_price_must_be_positive_finite_and_bound(tmp_path, monkeypatch, raw):
    host, rid, _, old, intent, plan = seed_with_origin(tmp_path, monkeypatch, origin=None)
    try:
        plan, order = plan_and_order(plan, old, limit=True)
        intent = with_policy(
            intent, order_type_policy="LIMIT_ONLY", price_policy="EXPLICIT_PRICE:" + raw
        )
        before = host.owner.risk_snapshot_v1()
        with pytest.raises(ValueError, match="EXECUTION_PLAN_ORIGIN_LIMIT_PRICE_POLICY"):
            host.owner.bind_execution_plan_v1(rid, order, canonical_intent=intent, venue_plan=plan)
        assert host.owner.risk_snapshot_v1() == before
    finally:
        host.close()


@pytest.mark.parametrize(
    "wire,declared",
    [
        ("10.03", "10.0300"),
        ("10.03", "1.003E1"),
        ("10.03000000000000000000000000000000001", "10.03000000000000000000000000000000001"),
    ],
)
def test_native_limit_price_preserves_exact_decimal_value_and_original_wire(
    tmp_path, monkeypatch, wire, declared
):
    from decimal import localcontext
    from tests.ops.test_original_budget_send_permit_handoff_v1 import cold_owner

    host, rid, _, old, intent, plan = seed_with_origin(tmp_path, monkeypatch, origin=None)
    try:
        plan, _ = plan_and_order(plan, old, limit=True)
        plan = replace(plan, venue_native_payload={**plan.venue_native_payload, "px": wire})
        order = bind_final_order_envelope_from_venue_plan_v1(
            plan,
            admission_ref=old.admission_ref,
            provenance_ref=old.provenance_ref,
            creation_epoch=old.creation_epoch,
        )
        intent = with_policy(
            intent, order_type_policy="LIMIT_ONLY", price_policy="EXPLICIT_PRICE:" + declared
        )
        with localcontext() as ctx:
            ctx.prec = 2
            host.owner.bind_execution_plan_v1(rid, order, canonical_intent=intent, venue_plan=plan)
            receipt = host.owner.execution_plan_context_v1(rid, order)
        stored = host.owner.execution_links_v1()[rid]
        assert (
            stored["envelope"]["price"]
            == stored["plan_origin"]["venue_plan"]["venue_native_payload"]["px"]
            == wire
        )
        assert (
            stored["plan_origin"]["canonical_order_intent"]["price_policy"]
            == "EXPLICIT_PRICE:" + declared
        )
        assert receipt.envelope_digest == order.envelope_digest
        assert stored["phase"] == "PLAN_BOUND" and stored["identity"] is None
        restored = cold_owner(host)
        try:
            assert restored.execution_links_v1()[rid] == stored
            assert restored.budget_state_v1().recovery_required
            assert restored.active_sum_v1() > 0
        finally:
            restored.close()
    finally:
        host.close()


@pytest.mark.parametrize("fault", ["policy", "price", "tif", "post_only"])
def test_cold_restore_rejects_rehashed_contradictory_policy(tmp_path, monkeypatch, fault):
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
    from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import _encode
    from tests.ops.test_original_budget_send_permit_handoff_v1 import cold_owner

    host, rid, _, _, intent, _ = seed_with_origin(tmp_path, monkeypatch)
    try:
        payload = host.owner.risk_snapshot_v1()["state"]
        origin = payload["execution_links"][rid]["plan_origin"]
        fields = {
            "policy": {"order_type_policy": "LIMIT_ONLY"},
            "price": {"price_policy": "EXPLICIT_PRICE:10.03"},
            "tif": {"time_in_force_policy": "IOC"},
            "post_only": {"max_slippage_policy": "POST_ONLY"},
        }[fault]
        origin["canonical_order_intent"] = _encode(with_policy(intent, **fields))
        origin["digest"] = digest({k: v for k, v in origin.items() if k != "digest"})
        # The original durable writer saves a structurally intact but semantically
        # inconsistent test input. Its original recovery consumer must reject it.
        host.owner._store.save(payload)
        with pytest.raises(ValueError, match="DURABLE_BUDGET_SEMANTIC_RESTORE_UNPROVEN"):
            cold_owner(host)
        assert host.owner.active_sum_v1() > 0
    finally:
        host.close()


@pytest.mark.parametrize("phase", ["before_get", "after_get", "during_k1", "during_opener"])
def test_actual_post_rechecks_the_original_retained_policy(tmp_path, monkeypatch, phase):
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
    from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import _encode
    from tests.ops.test_prepost_original_budget_context_v1 import AccountPort, execute, caller
    from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        _FakeKeychainBackend,
    )

    host, rid, identity, order, intent, _ = seed_with_origin(tmp_path, monkeypatch)
    try:
        args = dict(
            envelope=order,
            portfolio_budget_owner=host.owner,
            portfolio_reservation_id=rid,
            execution_plan_context=host.owner.execution_plan_context_v1(rid, order),
        )
        before_amount = host.owner.active_sum_v1()

        def change():
            origin = host.owner._execution_links[rid]["plan_origin"]
            origin["canonical_order_intent"] = _encode(
                with_policy(intent, order_type_policy="LIMIT_ONLY")
            )
            origin["digest"] = digest({k: v for k, v in origin.items() if k != "digest"})

        port = AccountPort(args, after_last=change if phase == "after_get" else None)
        if phase == "before_get":
            change()

        class DeniedOpener:
            def open(self, *args, **kwargs):
                pytest.fail("A contradictory retained policy must not reach a socket")

        class Backend(_FakeKeychainBackend):
            def copy_matching_generic_password_value_data_v1(self, **kwargs):
                result = super().copy_matching_generic_password_value_data_v1(**kwargs)
                if phase == "during_k1":
                    change()
                return result

        original_execute = caller.execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1

        def run(**kwargs):
            kwargs["k1_backend"] = Backend()
            if phase == "during_opener":
                kwargs["opener_factory"] = lambda: (change(), DeniedOpener())[1]
            return original_execute(**kwargs)

        monkeypatch.setattr(
            caller,
            "execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1",
            run,
        )
        with pytest.raises(
            (caller.CurrentProductiveActualVenuePostError, ValueError),
            match="EXECUTION_PLAN_ORIGIN|PREPOST|POST_BUDGET",
        ):
            execute(args, tmp_path, port=port, opener=DeniedOpener())
        assert len(port.requests) == (0 if phase == "before_get" else 10)
        assert host.owner.active_sum_v1() == before_amount
    finally:
        host.close()


def test_original_canonical_policy_owner_is_protected_at_actual_post():
    from src.ops.full_core_live_path_composition_root_v1.current_productive_actual_venue_post_baseline_v1 import (
        PROTECTED_CURRENT_PRODUCTIVE_POST_SLICE_SURFACE_PATHS,
    )

    assert (
        "src/governance/canonical_order_intent_v1.py"
        in PROTECTED_CURRENT_PRODUCTIVE_POST_SLICE_SURFACE_PATHS
    )
