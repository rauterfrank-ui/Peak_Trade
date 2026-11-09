"""Original reservation owner: per-slot test policy, atomic limits and recovery."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal as D
import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_entry_budget_policy_v1 import (
    EntryBudgetPolicyError,
    load_entry_budget_policy_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    ReserveDispositionV1 as Disposition,
    admit_sized_slot_reservation_v1,
)
from tests.ops.test_durable_portfolio_budget_recovery_v1 import (
    BOUND,
    ACCOUNT,
    EPOCH,
    _auto,
    _produce,
)
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import (
    _obs,
    _p01,
    _eligibility,
    _sizing_input,
    TRUSTED,
    BOUND as TRUSTED_BOUND,
)

REPO = Path(__file__).resolve().parents[2]
POLICY = REPO / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V1.json"


def policy():
    return load_slot_entry_budget_v1(POLICY)


def bindings(count=5):
    return {
        f"LANE_{i}": replace(BOUND, instrument_id=f"coin-{i}", venue_native_id=f"COIN{i}-USDC-SWAP")
        for i in range(1, count + 1)
    }


def owner_at(root, *, mode="create", declared_policy=None, count=5):
    return Owner(
        durable_root=root / "budget",
        durable_account_identity=ACCOUNT,
        durable_mode=mode,
        durable_lane_bindings=bindings(count),
        entry_budget_policy=policy()
        if mode == "create" and declared_policy is None
        else declared_policy,
    )


def recover(owner, root, capital="1000", count=5):
    result = _auto(
        owner, root, output=_produce(value=capital, epoch=EPOCH), bindings=bindings(count)
    )
    assert result.disposition is Disposition.ADMITTED, result.reason_codes
    return owner.budget_state_v1().observation_id


def reserve(owner, observed, *, slot="LANE_1", amount="25", decision="decision-1"):
    return owner.try_reserve_v1(
        slot_id=slot,
        decision_id=decision,
        cycle_id="cycle-1",
        observation_id=observed,
        amount=D(amount),
    )


def sized(owner, slot, decision):
    instrument = bindings()[slot].instrument_id
    request = _sizing_input(
        decision_id=decision,
        instrument_id=instrument,
        instrument=replace(_sizing_input().instrument, instrument_id=instrument),
    )
    return admit_sized_slot_reservation_v1(
        owner,
        observation=_obs(value="1000", epoch=EPOCH),
        p01=_p01(EPOCH),
        eligibility=_eligibility(EPOCH),
        slot_id=slot,
        decision_id=decision,
        cycle_id="sized-cycle",
        instrument_id=instrument,
        account_identity=ACCOUNT,
        sizing_input=request,
        fresh_pretrade_get_status=TRUSTED,
        live_account_bound_status=TRUSTED_BOUND,
        fresh_evidence_fetched=True,
        fresh_evidence_validated=True,
    )


def test_explicit_slot_policy_preserves_old_default_and_manual_transition():
    p = policy()
    assert p.per_entry_notional_limit == p.per_slot_reserved_notional_limit == 25
    assert p.aggregate_reserved_notional_limit == 125
    assert p.allowed_slot_ids == tuple(bindings())
    assert not p.automatic_increase_allowed and p.expiry == "UNTIL_EXPLICIT_POLICY_CHANGE"
    old = load_entry_budget_policy_v1()
    assert old.to_dict_v1()["schema"] == "entry_budget_policy.v1"
    assert not hasattr(old, "per_slot_reserved_notional_limit")
    assert old.per_entry_notional_limit == old.aggregate_reserved_notional_limit == 25


@pytest.mark.parametrize(
    "fault", ["number", "nan", "bool", "duplicate", "foreign", "unpaired", "auto", "overaggregate"]
)
def test_invalid_slot_policy_refuses_without_fallback(tmp_path, fault):
    data = policy().to_dict_v1()
    if fault == "number":
        data["per_slot_reserved_notional_limit"] = 25
    if fault == "nan":
        data["per_slot_reserved_notional_limit"] = "NaN"
    if fault == "bool":
        data["per_slot_reserved_notional_limit"] = True
    if fault == "duplicate":
        data["allowed_slot_ids"][1] = "LANE_1"
    if fault == "foreign":
        data["allowed_slot_ids"][1] = "LANE_6"
    if fault == "unpaired":
        data.pop("allowed_slot_ids")
    if fault == "auto":
        data["automatic_increase_allowed"] = True
    if fault == "overaggregate":
        data["aggregate_reserved_notional_limit"] = "126"
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(data))
    with pytest.raises(EntryBudgetPolicyError):
        load_slot_entry_budget_v1(path)


@pytest.mark.parametrize("count", [2, 5])
def test_each_slot_gets_own_limit_and_cannot_borrow_or_repeat(tmp_path, count):
    owner = owner_at(tmp_path, count=count)
    try:
        observed = recover(owner, tmp_path, count=count)
        for slot in bindings(count):
            first = reserve(owner, observed, slot=slot, decision="first:" + slot)
            assert first.disposition is Disposition.ADMITTED
            assert owner.active_slot_sum_v1(slot) == 25
            replay = reserve(owner, observed, slot=slot, decision="first:" + slot)
            assert replay.disposition is Disposition.IDEMPOTENT_REPLAY
            denied = reserve(owner, observed, slot=slot, amount="0.01", decision="extra:" + slot)
            assert denied.disposition is Disposition.DENIED
            assert "ENTRY_BUDGET_SLOT_LIMIT_EXCEEDED" in denied.reason_codes
        assert owner.active_sum_v1() == D(25) * count
        assert owner.stored_reservation_count_v1() == count
        assert owner.invariant_holds_v1()
    finally:
        owner.close()


def test_concurrent_reservations_preserve_slot_and_actual_account_limits(tmp_path):
    owner = owner_at(tmp_path)
    try:
        observed = recover(owner, tmp_path, capital="100")

        def request(i):
            return reserve(
                owner, observed, slot=f"LANE_{i % 5 + 1}", amount="7", decision=f"race-{i}"
            )

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(request, range(100)))
        assert sum(x.disposition is Disposition.ADMITTED for x in results) == 14
        assert owner.active_sum_v1() == 98
        assert all(owner.active_slot_sum_v1(slot) <= 25 for slot in bindings())
        assert owner.stored_reservation_count_v1() == 14
    finally:
        owner.close()


def test_original_sizer_consumes_remaining_slot_before_atomic_admission(tmp_path):
    owner = owner_at(tmp_path)
    try:
        observed = recover(owner, tmp_path)
        assert reserve(owner, observed, amount="20").disposition is Disposition.ADMITTED
        result = sized(owner, "LANE_1", "sized-first")
        assert result.disposition is Disposition.ADMITTED, result.reason_codes
        assert result.sizing_decision.canonical_position_sizing.resulting_notional == 5
        assert result.reservation.amount == 5 and owner.active_slot_sum_v1("LANE_1") == 25
        assert sized(owner, "LANE_1", "sized-second").disposition is not Disposition.ADMITTED
        other = sized(owner, "LANE_2", "sized-other")
        assert other.disposition is Disposition.ADMITTED and other.reservation.amount == 25
        assert owner.active_sum_v1() == 50
    finally:
        owner.close()


def test_cold_reopen_retains_policy_holds_and_requires_original_recovery(tmp_path):
    owner = owner_at(tmp_path)
    observed = recover(owner, tmp_path)
    held = reserve(owner, observed)
    owner.commit_internal_pre_external_effect_v1(held.reservation.reservation_id)
    owner.close()
    recovered = owner_at(tmp_path, mode="recover")
    try:
        assert recovered.entry_budget_policy_v1() == policy()
        assert (
            not recovered.budget_state_v1().admitted
            and recovered.budget_state_v1().recovery_required
        )
        assert recovered.active_slot_sum_v1("LANE_1") == 25
        observed = recover(recovered, tmp_path)
        assert reserve(recovered, observed, decision="new").disposition is Disposition.DENIED
        assert reserve(recovered, observed, slot="LANE_2").disposition is Disposition.ADMITTED
        assert recovered.active_sum_v1() == 50
    finally:
        recovered.close()
    with pytest.raises(ValueError, match="SEMANTIC_RESTORE_UNPROVEN"):
        owner_at(tmp_path, mode="recover", declared_policy=replace(policy(), revision=2))


def test_unlisted_slot_and_entry_oversize_do_not_consume_budget(tmp_path):
    one_slot = replace(
        policy(), allowed_slot_ids=("LANE_1",), aggregate_reserved_notional_limit=D(25)
    )
    owner = owner_at(tmp_path, declared_policy=one_slot)
    try:
        observed = recover(owner, tmp_path)
        assert (
            reserve(owner, observed, amount="25.01").reason_codes[0]
            == "ENTRY_BUDGET_PER_ENTRY_LIMIT_EXCEEDED"
        )
        assert (
            reserve(owner, observed, slot="LANE_2").reason_codes[0]
            == "ENTRY_BUDGET_SLOT_NOT_ALLOWED"
        )
        assert owner.active_sum_v1() == 0 and owner.stored_reservation_count_v1() == 0
    finally:
        owner.close()


def test_actual_29p_consumes_original_bound_slot_policy_in_simulated_host(tmp_path, monkeypatch):
    import socket
    from datetime import datetime
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
    from tests.ops.test_portfolio_budget_host_v1 import _fetch
    from tests.ops.test_outer_entry_budget_policy_v1 import (
        _bound,
        _host_enter_cycle,
        _enter_replay,
        _injected,
        _balance_payload,
        Slot,
        join,
    )
    from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import EPOCH as epoch
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        REUSED_BINDING_ACCOUNT_SCOPE as account,
    )

    def no_network(*a, **kw):
        raise AssertionError("Synthetic ports only")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    host = PortfolioBudgetHostV1(
        root=tmp_path / "host",
        private_rest_fetch=_fetch(uid=account),
        repository_sha="slot-policy-proof",
        session_id="slot-policy-proof",
        expected_account_identity=account,
        durable_mode="create",
        clock=lambda: datetime.fromisoformat(epoch.replace("Z", "+00:00")).timestamp(),
        execution_environment="INTERNAL_SIMULATED_EXECUTION",
        entry_budget_policy=policy(),
    )
    try:
        context = host.observe_v1({"LANE_1": _bound()})
        _, cycle, _ = _host_enter_cycle()
        replay = _enter_replay(cycle)
        kwargs = dict(
            replay=replay,
            bound_instrument=_bound(),
            decision_epoch=epoch,
            injected=_injected(payload=_balance_payload(avail_eq="1000.00")),
            portfolio_budget_owner=host.owner,
            portfolio_slot=Slot("LANE_1", replay.evidence.decision_id, "entry"),
            host_budget_recovery=context,
        )
        result = join(**kwargs)
        assert result.status == "PASS", result.reason_codes
        assert 0 < host.owner.active_slot_sum_v1("LANE_1") <= 25
        assert result.entry_budget_policy_digest == policy().digest_v1()
        assert (
            result.replay.intermediate.capital_risk_sizing_decision.scope_capital_envelope.total_capital_limit
            == 125
        )
        assert join(
            **{**kwargs, "entry_budget_policy": load_entry_budget_policy_v1()}
        ).first_blocker == ("ENTRY_BUDGET_ORIGINAL_OWNER_POLICY_MISMATCH")
        assert join(**{**kwargs, "host_budget_recovery": None}).first_blocker == (
            "SLOT_TEST_BUDGET_REQUIRES_ORIGINAL_SIMULATED_HOST"
        )
    finally:
        host.close()
