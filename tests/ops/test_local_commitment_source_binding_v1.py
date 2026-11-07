"""Original local obligations → margin handoff → original sizing/reserve consumer."""

from dataclasses import replace
from decimal import Decimal

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
    build_full_core_margin_inputs_from_budget_owner_v1,
    execute_current_productive_treasury_single_source_capital_handoff_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_base_binding_v1 import (
    clear_current_productive_base_binding_state_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1 import contract_v1 as budget_module
from src.ops.portfolio_capital_reservation_budget_v1.local_commitment_readback_v1 import (
    LOCAL_COMMITMENT_DOMAIN,
    VENUE_MARGIN_COVERAGE,
)
from tests.ops.test_durable_portfolio_budget_recovery_v1 import (
    ACCOUNT,
    BOUND,
    BINDINGS,
    EPOCH,
    NOW,
    _auto,
    _owner,
    _produce,
    _reserve,
)
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import (
    _obs,
    _p01,
    _eligibility,
    _sizing_input,
)


@pytest.fixture(autouse=True)
def isolated_capital_ordering():
    clear_current_productive_base_binding_state_v1()
    yield
    clear_current_productive_base_binding_state_v1()


def _admit(owner, readback, **overrides):
    args = dict(
        observation=_obs(value="1000", epoch=EPOCH),
        p01=_p01(EPOCH),
        eligibility=_eligibility(EPOCH),
        slot_id="LANE_1",
        decision_id="readback-entry",
        cycle_id="readback-cycle",
        instrument_id=BOUND.instrument_id,
        account_identity=ACCOUNT,
        sizing_input=_sizing_input(
            decision_id="readback-entry",
            account_equity=Decimal("1000"),
            scope_capital_limit=Decimal("20"),
        ),
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        live_account_bound_status="TRUSTED_PRESENT",
        fresh_evidence_fetched=True,
        fresh_evidence_validated=True,
        local_commitment_readback=readback,
    )
    args.update(overrides)
    return budget_module.admit_sized_slot_reservation_v1(owner, **args)


def test_real_local_hold_reaches_margin_and_sizing_without_becoming_venue_u04(tmp_path):
    owner = _owner(tmp_path)
    try:
        assert (
            _auto(owner, tmp_path, output=_produce(value="1000", epoch=EPOCH)).disposition.value
            == "ADMITTED"
        )
        _reserve(owner, amount="60")
        inputs = build_full_core_margin_inputs_from_budget_owner_v1(
            raw_acct_lv="2", budget_owner=owner
        )
        readback = inputs.local_commitment_readback
        assert inputs.u04_evidence is None
        assert readback.source_owner is owner
        assert readback.domain == LOCAL_COMMITMENT_DOMAIN
        assert readback.active_commitment_sum == 60
        assert readback.venue_margin_coverage == VENUE_MARGIN_COVERAGE
        assert readback.commitments[0].amount_basis == "CALLER_DECLARED_LOCAL_BUDGET_AMOUNT"
        obs = _obs(value="1000", epoch=EPOCH)
        handoff = execute_current_productive_treasury_single_source_capital_handoff_v1(
            margin_observation=obs,
            instrument_id=BOUND.instrument_id,
            body_sha256=obs.provenance_digest,
            fresh_pretrade_get_status="TRUSTED_PRESENT",
            live_account_bound_status="TRUSTED_PRESENT",
            u04_p01_host_inputs=inputs,
        )
        assert not handoff.fail_closed, handoff.reason_codes
        assert handoff.producer_output.value == "1000"
        assert handoff.producer_output.u04_applied == "false"
        seam = _admit(owner, readback)
        assert seam.disposition.value == "ADMITTED", seam.reason_codes
        assert seam.sizing_decision.scope_capital_envelope.available_capital == 940
        assert seam.sizing_decision.scope_capital_envelope.remaining_capital == 940
        assert owner.active_sum_v1() == 60 + seam.reservation.amount
        replay = _admit(owner, owner.local_commitment_readback_v1())
        assert replay.disposition.value == "IDEMPOTENT_REPLAY", replay.reason_codes
        assert replay.sizing_decision.final_quantity == seam.sizing_decision.final_quantity
        assert owner.active_sum_v1() == 60 + seam.reservation.amount
    finally:
        owner.close()


@pytest.mark.parametrize(
    "field,value",
    [
        ("active_commitment_sum", Decimal(0)),
        ("commitments", ()),
        ("domain", "VENUE_FROZEN_MARGIN"),
        ("venue_margin_coverage", "ALREADY_NETTED"),
        ("generation_digest", "0" * 64),
        ("account_identity", "foreign-account"),
    ],
)
def test_readback_cannot_be_relabelled_emptied_or_credited_as_margin(tmp_path, field, value):
    owner = _owner(tmp_path)
    try:
        _auto(owner, tmp_path, output=_produce(value="1000", epoch=EPOCH))
        _reserve(owner)
        bad = replace(owner.local_commitment_readback_v1(), **{field: value})
        result = _admit(owner, bad)
        assert result.disposition.value == "FAIL_CLOSED"
        assert owner.active_sum_v1() == 60
    finally:
        owner.close()


def test_identical_empty_book_from_another_owner_is_not_adopted():
    first = budget_module.PortfolioCapitalReservationBudgetOwnerV1()
    second = budget_module.PortfolioCapitalReservationBudgetOwnerV1()
    assert _admit(second, first.local_commitment_readback_v1()).disposition.value == "FAIL_CLOSED"
    assert second.stored_reservation_count_v1() == 0


def test_legacy_memory_first_use_is_explicitly_not_durable_recovery():
    owner = budget_module.PortfolioCapitalReservationBudgetOwnerV1()
    readback = owner.local_commitment_readback_v1()
    assert not readback.durable_state_enabled and readback.account_identity == ""
    assert readback.active_commitment_sum == 0
    result = _admit(owner, readback)
    assert result.disposition.value == "ADMITTED", result.reason_codes
    assert (
        owner.local_commitment_readback_v1().commitments[0].amount_basis
        == "CANONICAL_SIZING_RESULTING_NOTIONAL"
    )


def test_changed_obligations_are_fenced_atomically_after_sizing(tmp_path, monkeypatch):
    owner = _owner(tmp_path)
    try:
        _auto(owner, tmp_path, output=_produce(value="1000", epoch=EPOCH))
        readback = owner.local_commitment_readback_v1()
        evaluate = budget_module.evaluate_capital_risk_sizing_v1

        def concurrent_hold(inp):
            decision = evaluate(inp)
            assert (
                _reserve(owner, amount="1", decision="concurrent").disposition.value == "ADMITTED"
            )
            return decision

        monkeypatch.setattr(budget_module, "evaluate_capital_risk_sizing_v1", concurrent_hold)
        result = _admit(owner, readback)
        assert result.disposition.value == "FAIL_CLOSED"
        assert "LOCAL_COMMITMENT_GENERATION_CHANGED_BEFORE_RESERVE" in result.reason_codes
        assert owner.active_sum_v1() == 1
        assert owner.stored_reservation_count_v1() == 1
    finally:
        owner.close()


@pytest.mark.parametrize("filled", [False, True])
def test_original_plan_submit_reconciliation_and_release_keep_distinct_meaning(tmp_path, filled):
    from tests.ops.test_portfolio_execution_recovery_v1 import (
        seed,
        ReadPort,
        _host,
        _fetch,
        _bound,
        ACCOUNT as execution_account,
        NOW as execution_now,
    )

    host, rid, identity, envelope = seed(tmp_path)
    try:
        planned = host.owner.local_commitment_readback_v1()
        row = next(row for row in planned.commitments if row.reservation_id == rid)
        assert row.execution_phase == "PLAN_BOUND" and row.state == "COMMITTED"
        assert row.canonical_quantity == envelope.quantity
        assert row.amount_basis == "CANONICAL_SIZING_RESULTING_NOTIONAL"
        held = planned.active_commitment_sum
        host.owner.mark_execution_submit_boundary_v1(rid, identity)
        submitted = host.owner.local_commitment_readback_v1()
        assert submitted.active_commitment_sum == held
        assert submitted.commitments[0].execution_phase == "SUBMIT_MAY_HAVE_OCCURRED"
        assert submitted.venue_margin_coverage == VENUE_MARGIN_COVERAGE
        with pytest.raises(ValueError, match="GENERATION_OR_CONTENT_CHANGED"):
            host.owner.require_local_commitment_readback_v1(
                planned, account_identity=execution_account
            )
        host.close()
        sign = "" if identity.selected_side.upper() in {"LONG", "ENTER_LONG"} else "-"
        positions = (
            (
                {
                    "instId": identity.native_id,
                    "posSide": "net",
                    "pos": sign + identity.final_quantity,
                },
            )
            if filled
            else ()
        )
        host = _host(
            tmp_path,
            _fetch(uid=execution_account, positions=positions),
            clock=lambda: execution_now,
            expected_account=execution_account,
        )
        host.reconciliation_transport = ReadPort(
            identity,
            state="filled" if filled else "canceled",
            filled=identity.final_quantity if filled else "0",
        )
        context = host.observe_v1({"LANE_1": _bound()})
        assert context.execution_reconciliation[rid]["matched"]
        readback = host.owner.local_commitment_readback_v1()
        assert readback.active_commitment_sum == (held if filled else 0)
        assert readback.commitments[0].reconciliation_matched
        assert readback.venue_margin_coverage == VENUE_MARGIN_COVERAGE
        assert host.owner.budget_state_v1().recovery_required
        with pytest.raises(ValueError, match="ORIGINAL_OWNER_REQUIRED"):
            host.owner.require_local_commitment_readback_v1(
                submitted, account_identity=execution_account
            )
    finally:
        host.close()


@pytest.mark.parametrize("fault", ["closed", "commit-unproven"])
def test_failed_or_closed_writer_cannot_issue_an_empty_readback(tmp_path, monkeypatch, fault):
    owner = _owner(tmp_path)
    try:
        if fault == "closed":
            owner.close()
        else:
            _auto(owner, tmp_path)

            def failed_commit(state):
                raise OSError("synthetic lost acknowledgement")

            monkeypatch.setattr(owner._store, "save", failed_commit)
            with pytest.raises(budget_module.PortfolioCapitalBudgetError, match="COMMIT_UNPROVEN"):
                _reserve(owner)
        with pytest.raises(ValueError, match="SOURCE_UNAVAILABLE"):
            owner.local_commitment_readback_v1()
    finally:
        owner.close()


@pytest.mark.parametrize("fault", ["stale-generation", "mixed-u04", "untyped-readback"])
def test_margin_handoff_rejects_unproven_local_state_before_producing(tmp_path, fault):
    from tests.ops.test_current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_v1 import (
        _witness,
    )

    owner = _owner(tmp_path)
    try:
        _auto(owner, tmp_path, output=_produce(value="1000", epoch=EPOCH))
        inputs = build_full_core_margin_inputs_from_budget_owner_v1(
            raw_acct_lv="2", budget_owner=owner
        )
        if fault == "stale-generation":
            _reserve(owner)
        elif fault == "mixed-u04":
            inputs = replace(inputs, u04_evidence=_witness())
        else:
            inputs = replace(inputs, local_commitment_readback=object())
        obs = _obs(value="1000", epoch=EPOCH)
        result = execute_current_productive_treasury_single_source_capital_handoff_v1(
            margin_observation=obs,
            instrument_id=BOUND.instrument_id,
            body_sha256=obs.provenance_digest,
            fresh_pretrade_get_status="TRUSTED_PRESENT",
            live_account_bound_status="TRUSTED_PRESENT",
            u04_p01_host_inputs=inputs,
        )
        assert result.fail_closed and result.producer_output.produced == "false"
        assert result.step_29p_admissibility_count == 0
    finally:
        owner.close()


def test_actual_enter_uses_and_consumes_the_same_original_owner_readback(tmp_path, monkeypatch):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_enter_live_29p_join_v1 as entry,
    )
    from tests.ops.test_portfolio_budget_host_v1 import (
        test_actual_outer_entry_seam_recovers_host_before_reserving,
    )

    seen = []
    build = entry.build_full_core_margin_inputs_from_budget_owner_v1
    consume = entry.admit_sized_slot_reservation_v1

    def capture(**kwargs):
        result = build(**kwargs)
        assert result.u04_evidence is None
        seen.append(result.local_commitment_readback)
        return result

    def consuming(owner, **kwargs):
        assert kwargs["local_commitment_readback"] is seen[-1]
        assert seen[-1].source_owner is owner
        return consume(owner, **kwargs)

    monkeypatch.setattr(entry, "build_full_core_margin_inputs_from_budget_owner_v1", capture)
    monkeypatch.setattr(entry, "admit_sized_slot_reservation_v1", consuming)
    test_actual_outer_entry_seam_recovers_host_before_reserving(tmp_path, monkeypatch)
    assert seen and seen[0].durable_state_enabled
