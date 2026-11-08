"""Current original Ops policy at retained-plan and actual POST consumers."""

from decimal import Decimal
import json

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_entry_budget_policy_v1 as policy_owner,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    FullCoreEnvelopeBoundSendSeamError,
    inspect_original_portfolio_execution_context_v1,
)
from tests.ops._current_post_safety_fixture_v1 import (
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
    synthetic_current_post_pending_context_v1,
)
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from tests.ops.test_prepost_original_budget_context_v1 import (
    no_network as no_network,
    AccountPort,
    caller,
    files,
    _clean_post_integrity,
)
from tests.ops.test_current_post_original_budget_admission_v1 import seeded, started
from tests.ops.test_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
    _FakeKeychainBackend,
)


@pytest.fixture
def policy_file(tmp_path, monkeypatch):
    original = policy_owner.load_entry_budget_policy_v1().to_dict_v1()
    path = tmp_path / "synthetic-current-entry-policy.json"
    path.write_text(json.dumps(original))
    monkeypatch.setattr(policy_owner, "POLICY_PATH", path)
    return path, original


def change_policy(policy_file, owner, fault):
    path, original = policy_file
    if fault == "missing":
        path.unlink()
        return "ENTRY_BUDGET_POLICY_UNAVAILABLE_OR_INVALID"
    payload = {**original, "revision": original["revision"] + 1}
    held = owner.active_sum_v1()
    if fault == "entry":
        payload["per_entry_notional_limit"] = str(held / 2)
        reason = "CURRENT_ENTRY_BUDGET_PER_ENTRY_LIMIT_EXCEEDED"
    elif fault in {"aggregate", "holds_only"}:
        amount = (
            held
            if fault == "aggregate"
            else Decimal(original["aggregate_reserved_notional_limit"]) - held + 1
        )
        result = owner.try_reserve_v1(
            slot_id="LANE_1",
            decision_id="other-original-hold",
            cycle_id="other-original-cycle",
            observation_id=owner.budget_state_v1().observation_id,
            amount=amount,
        )
        assert result.disposition.value == "ADMITTED"
        if fault == "aggregate":
            payload["per_entry_notional_limit"] = str(held)
            payload["aggregate_reserved_notional_limit"] = str(held * Decimal("1.5"))
        else:
            # No policy revision changes. Only an original additional hold does.
            payload = original
        reason = "CURRENT_ENTRY_BUDGET_AGGREGATE_LIMIT_EXCEEDED"
    elif fault == "invalid":
        payload["currency"] = "FOREIGN"
        reason = "ENTRY_BUDGET_POLICY_UNAVAILABLE_OR_INVALID"
    else:
        raise AssertionError(fault)
    path.write_text(json.dumps(payload))
    return reason


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("fault", ["entry", "aggregate", "holds_only", "missing", "invalid"])
def test_retained_plan_rechecks_current_policy_without_changing_original_state(
    tmp_path, monkeypatch, policy_file, modern, fault
):
    host, args = seeded(tmp_path / "budget", monkeypatch, modern)
    try:
        original = inspect_original_portfolio_execution_context_v1(**args)
        assert original["scope"] == "ORIGINAL_COMMITTED_PLAN_CONTEXT_ONLY"
        reason = change_policy(policy_file, host.owner, fault)
        before = files(tmp_path / "budget")
        sequence, held = host.owner._store.sequence, host.owner.active_sum_v1()
        with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match=reason):
            inspect_original_portfolio_execution_context_v1(**args)
        assert files(tmp_path / "budget") == before
        assert host.owner._store.sequence == sequence
        assert host.owner.active_sum_v1() == held > 0
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("fault", ["entry", "aggregate", "holds_only", "missing", "invalid"])
def test_started_attempt_rechecks_current_policy_without_advancing_or_releasing(
    tmp_path, monkeypatch, policy_file, modern, fault
):
    host, args, context = started(tmp_path / "case", monkeypatch, modern)
    try:
        context.inspect_v1(envelope=args["envelope"], stage="FIRST")
        reason = change_policy(policy_file, host.owner, fault)
        before = files(tmp_path / "case")
        with pytest.raises(ValueError, match=reason):
            context.inspect_v1(envelope=args["envelope"], stage="LATER")
        assert files(tmp_path / "case") == before
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("change", ["equal", "increase", "revision_only"])
def test_current_policy_accepts_unchanged_quantity_within_limits_and_adds_no_revision_veto(
    tmp_path, monkeypatch, policy_file, modern, change
):
    host, args = seeded(tmp_path / "budget", monkeypatch, modern)
    try:
        expected = inspect_original_portfolio_execution_context_v1(**args)
        before = files(tmp_path / "budget")
        path, original = policy_file
        held = host.owner.active_sum_v1()
        payload = {**original, "revision": original["revision"] + 1}
        if change != "revision_only":
            ceiling = held if change == "equal" else Decimal("100")
            payload.update(
                per_entry_notional_limit=str(ceiling),
                aggregate_reserved_notional_limit=str(ceiling),
            )
        path.write_text(json.dumps(payload))
        assert inspect_original_portfolio_execution_context_v1(**args) == expected
        assert files(tmp_path / "budget") == before
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
@pytest.mark.parametrize("fault", ["entry", "aggregate", "holds_only"])
@pytest.mark.parametrize("phase", ["before_get", "after_get", "during_k1", "opener_factory"])
def test_actual_post_consumes_later_policy_or_original_aggregate_change_before_socket(
    tmp_path, monkeypatch, policy_file, modern, fault, phase
):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, args = seeded(tmp_path / "budget", monkeypatch, modern)
    owner = host.owner
    wire = args["envelope"].to_runtime_json_v1()
    changed = []

    def change():
        if not changed:
            changed.append(change_policy(policy_file, owner, fault))

    class Port(AccountPort):
        def get(self, **kwargs):
            result = super().get(**kwargs)
            if phase == "after_get":
                change()
            return result

    class Backend(_FakeKeychainBackend):
        def copy_matching_generic_password_value_data_v1(self, **kwargs):
            result = super().copy_matching_generic_password_value_data_v1(**kwargs)
            if phase == "during_k1":
                change()
            return result

    calls = []

    class Opener:
        def open(self, *a, **kw):
            calls.append("socket")
            raise AssertionError("No socket after current policy denial")

    def factory():
        if phase == "opener_factory":
            change()
        return Opener()

    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )
    port = Port(args)
    if phase == "before_get":
        change()
    try:
        with pytest.raises(caller.CurrentProductiveActualVenuePostError, match="ENTRY_BUDGET"):
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
        assert changed and calls == []
        assert len(port.requests) == (0 if phase == "before_get" else 10)
        assert args["envelope"].to_runtime_json_v1() == wire
        assert owner.active_sum_v1() > 0
        record = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")["record"]
        if phase in {"before_get", "after_get"}:
            assert record is None
            assert (
                owner.execution_links_v1()[args["portfolio_reservation_id"]]["phase"]
                == "PLAN_BOUND"
            )
        else:
            assert record["durable_state"] == "ABORTED_BEFORE_TRANSPORT"
            assert record["transport_attempt"]["phase"] == "ABORTED"
            assert record["transport_attempt"]["reason_code"].startswith("POST_BUDGET")
            assert (
                owner.execution_links_v1()[args["portfolio_reservation_id"]]["phase"]
                == "SUBMIT_MAY_HAVE_OCCURRED"
            )
    finally:
        host.close()


@pytest.mark.parametrize("modern", [False, True])
def test_policy_change_after_possible_socket_keeps_original_uncertainty_and_capital(
    tmp_path, monkeypatch, policy_file, modern
):
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, args = seeded(tmp_path / "budget", monkeypatch, modern)
    owner = host.owner
    args["post_pending_context"] = synthetic_current_post_pending_context_v1(
        args["envelope"], account=owner.durable_scope_identity_v1()["account"]
    )
    calls = []

    class Opener:
        def open(self, *a, **kw):
            calls.append("possible_external_effect")
            change_policy(policy_file, owner, "entry")
            raise TimeoutError("injected after possible send")

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
        assert calls == ["possible_external_effect"]
        assert result.post_outcome == "UNKNOWN_EXTERNAL_EFFECT_POSSIBLE"
        assert owner.active_sum_v1() == held > 0
        assert (
            owner.release_plan_failure_v1(args["portfolio_reservation_id"]).disposition.value
            == "FAIL_CLOSED"
        )
        record = load_external_effect_durable_consume_v1(store_root=tmp_path / "send")["record"]
        assert record["post_count"] == 1
        assert record["durable_state"] == "SENT_INITIATED"
        assert record["transport_attempt"]["phase"] == "MAY_HAVE_SENT"
    finally:
        host.close()
