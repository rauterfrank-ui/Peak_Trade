"""Source-specific Treasury transport and original CT/29P consumer effects."""

from dataclasses import replace

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_treasury_single_source_capital_handoff_v1 as handoff_module,
)
from src.ops.governed_productive_account_equity_authority_producer_v1 import (
    current_productive_free_margin_inputs_binding_v1 as margin_module,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_base_binding_v1 import (
    clear_current_productive_base_binding_state_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.non_forbidden_non_eq_non_stock_usdc_current_productive_observation_v1 import (
    NonForbiddenUsdcCurrentProductiveObservationError,
    build_non_forbidden_usdc_current_productive_observation_from_treasury_v1,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1 import (
    join_v1 as join_module,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryBalanceSourceV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.reconciliation_v1 import (
    clear_treasury_reconciliation_idempotency_cache_v1,
    evaluate_treasury_read_only_reconciliation_v1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.account_balance_usdc_avail_eq_adapter_v1 import (
    build_treasury_venue_observation_from_trusted_account_balance_usdc_avail_eq_v1,
)
from tests.ops.test_current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_v1 import (
    _host_inputs,
    _reconciled_obs,
    _witness,
)
from tests.ops.test_full_core_treasury_single_source_capital_handoff_v1 import (
    DEFAULT_INSTRUMENT_ID,
    _minimal_margin_observation_v1,
)


@pytest.fixture(autouse=True)
def isolated_owners():
    clear_current_productive_base_binding_state_v1()
    clear_treasury_reconciliation_idempotency_cache_v1()
    yield
    clear_current_productive_base_binding_state_v1()
    clear_treasury_reconciliation_idempotency_cache_v1()


def _treasury(original):
    return build_treasury_venue_observation_from_trusted_account_balance_usdc_avail_eq_v1(
        avail_eq_raw=original.value,
        account_identity=original.bound_account_identity,
        instrument_id=DEFAULT_INSTRUMENT_ID,
        observed_at_utc=original.observed_at_as_of,
        body_sha256=original.provenance_digest,
        decision_epoch=original.decision_epoch,
    )


def _join(original=None, *, treasury=None, host_inputs=None, **overrides):
    original = original or _minimal_margin_observation_v1()
    args = dict(
        expected_account_identity=original.bound_account_identity,
        expected_instrument_id=DEFAULT_INSTRUMENT_ID,
        usdc_row_status="PRESENT",
        u04_p01_eligibility_host_inputs=host_inputs or _host_inputs(),
        decision_epoch=original.decision_epoch,
        age_seconds=original.age_seconds,
        freshness_max_age=original.freshness_max_age,
        free_margin_observation=original,
    )
    args.update(overrides)
    return join_module.join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        treasury or _treasury(original), **args
    )


def test_free_margin_retains_account_source_and_never_becomes_funding_base():
    original = _minimal_margin_observation_v1()
    treasury = _treasury(original)
    assert treasury.balance_source == TreasuryBalanceSourceV1.ACCOUNT_FREE_MARGIN.value
    with pytest.raises(NonForbiddenUsdcCurrentProductiveObservationError, match="CT_BASE_REQUIRES"):
        build_non_forbidden_usdc_current_productive_observation_from_treasury_v1(
            observation=treasury,
            usdc_row_status="PRESENT",
            treasury_reconciliation_class="RECONCILED",
            bound_account_identity=original.bound_account_identity,
            bound_venue_identity="okx",
            bound_td_mode="cross",
            decision_epoch=original.decision_epoch,
            age_seconds="1",
            freshness_max_age="5",
        )


def test_margin_uses_original_29p_once_without_ct_or_base(monkeypatch):
    calls = []
    producer = margin_module.produce_current_productive_29p_risk_capital_v1

    def observed_produce(**kwargs):
        calls.append(kwargs)
        return producer(**kwargs)

    def forbidden_ct(**kwargs):
        pytest.fail("Free margin entered the funding BASE/CT branch")

    monkeypatch.setattr(
        margin_module, "produce_current_productive_29p_risk_capital_v1", observed_produce
    )
    monkeypatch.setattr(
        join_module,
        "bind_current_productive_available_for_sizing_base_from_treasury_host_v1",
        forbidden_ct,
    )
    original = _minimal_margin_observation_v1()
    result = handoff_module.execute_current_productive_treasury_single_source_capital_handoff_v1(
        margin_observation=original,
        instrument_id=DEFAULT_INSTRUMENT_ID,
        body_sha256=original.provenance_digest,
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        live_account_bound_status="TRUSTED_PRESENT",
        u04_p01_host_inputs=_host_inputs(),
    )
    assert not result.fail_closed, result.reason_codes
    assert result.free_margin_inputs_bound
    assert not result.ct_sizing_eligibility_inputs_bound
    assert result.base_bind_count == 0
    assert result.p01_application_count == result.step_29p_admissibility_count == 1
    assert result.producer_output.value == original.value
    assert result.producer_output.u04_applied == "false"
    assert result.step_29p_admissibility.risk_admissible
    assert len(calls) == 1
    assert calls[0]["observation"] is original
    assert calls[0]["u04"] is None


def test_funding_still_uses_ct_with_nonzero_u04_reduction():
    treasury = _reconciled_obs()
    host = join_module.join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        treasury,
        expected_account_identity=treasury.account_identity,
        expected_instrument_id=treasury.instrument_id,
        usdc_row_status="PRESENT",
        u04_p01_eligibility_host_inputs=_host_inputs(
            u04_evidence=_witness(reservation_value_raw="15", empty_reservation_proven="false")
        ),
    )
    assert host.free_margin_inputs_binding is None
    assert host.base_numeric_binding.numeric_base_bound
    assert host.base_numeric_binding.base_fact.already_net_of_u04 == "false"
    assert host.u04_p01_eligibility_binding.inputs_bound
    assert host.u04_p01_eligibility_binding.producer_output.value == "85.00"


@pytest.mark.parametrize("amount", ["1", "15", "2000"])
def test_nonempty_u04_without_venue_coverage_is_blocked_not_ignored_or_subtracted(amount):
    host = _join(
        host_inputs=_host_inputs(
            u04_evidence=_witness(reservation_value_raw=amount, empty_reservation_proven="false")
        )
    )
    assert host.base_numeric_binding is None
    binding = host.free_margin_inputs_binding
    assert binding.fail_closed
    assert binding.producer_output is None
    assert "U04_COVERAGE_UNRESOLVED_FOR_FREE_MARGIN" in binding.reason_codes


@pytest.mark.parametrize(
    "field,value",
    [
        ("venue_balance_raw", "1001"),
        ("account_identity", "another-account"),
        ("observed_at_utc", "2026-10-01T00:00:00Z"),
        ("evidence_fingerprint", "d" * 64),
        ("balance_freshness", "STALE"),
    ],
)
def test_treasury_transport_cannot_substitute_original_margin(field, value):
    original = _minimal_margin_observation_v1()
    host = _join(original, treasury=replace(_treasury(original), **{field: value}))
    assert host.free_margin_inputs_binding.fail_closed
    assert host.free_margin_inputs_binding.producer_output is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("decision_epoch", "other-decision"),
        ("age_seconds", "0"),
        ("freshness_max_age", "4"),
        ("free_margin_observation", None),
    ],
)
def test_transport_requires_original_scope_time_and_typed_observation(field, value):
    host = _join(**{field: value})
    assert host.free_margin_inputs_binding.fail_closed


@pytest.mark.parametrize(
    "field,value",
    [
        ("already_net_of_in_use", "false"),
        ("settlement_currency", "USD"),
        ("selected_ccy", "USDT"),
        ("fallback_chain_used", "true"),
        ("account_level_avail_eq_used", "true"),
        ("surface", "account.availEq"),
        ("age_seconds", "NaN"),
        ("age_seconds", "Infinity"),
        ("freshness_max_age", "NaN"),
        ("age_seconds", "999"),
    ],
)
def test_original_margin_owner_still_denies_invalid_inputs(field, value):
    host = _join(replace(_minimal_margin_observation_v1(), **{field: value}))
    assert host.free_margin_inputs_binding.fail_closed
    assert not host.free_margin_inputs_binding.inputs_bound


@pytest.mark.parametrize(
    "evidence",
    [
        _witness(empty_reservation_proven="false"),
        _witness(witness_digest=""),
        _witness(reservation_value_raw="NaN"),
    ],
)
def test_invalid_empty_reservation_witness_remains_blocked(evidence):
    host = _join(host_inputs=_host_inputs(u04_evidence=evidence))
    assert host.free_margin_inputs_binding.fail_closed


def test_reconciliation_cache_isolates_source_and_account_for_identical_bytes():
    original = _minimal_margin_observation_v1()
    margin = _treasury(original)
    assert not evaluate_treasury_read_only_reconciliation_v1(margin).fail_closed
    changed = replace(
        margin,
        balance_source=TreasuryBalanceSourceV1.FUNDING_AVAILABLE_BALANCE.value,
        balance_freshness="STALE",
    )
    assert evaluate_treasury_read_only_reconciliation_v1(changed).fail_closed
    other_account = replace(margin, account_identity="other", balance_freshness="STALE")
    assert evaluate_treasury_read_only_reconciliation_v1(other_account).fail_closed


def test_same_source_fingerprint_does_not_cache_away_new_staleness():
    original = _minimal_margin_observation_v1()
    treasury = _treasury(original)
    assert _join(original, treasury=treasury).free_margin_inputs_binding.inputs_bound
    stale = _join(original, treasury=replace(treasury, balance_freshness="STALE"))
    assert stale.host_evaluation.fail_closed
    assert stale.free_margin_inputs_binding.fail_closed


def test_funding_adapter_explicitly_retains_funding_surface():
    from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.producer_v1 import (
        build_treasury_venue_observation_from_funding_balance_v1,
    )
    from tests.ops.test_treasury_phase_2_read_only_venue_observation_binding_v1 import (
        _ctx,
        _funding,
    )

    observation = build_treasury_venue_observation_from_funding_balance_v1(_funding(), _ctx())
    assert observation.balance_source == TreasuryBalanceSourceV1.FUNDING_AVAILABLE_BALANCE.value


def test_funding_observation_report_rejects_margin_before_dereferencing_ct_base():
    from src.ops.treasury_productive_read_only_venue_observation_v1.chain_v1 import (
        execute_treasury_productive_reconciliation_chain_v1,
    )
    from src.ops.treasury_productive_read_only_venue_observation_v1.errors_v1 import (
        TreasuryProductiveReadOnlyVenueObservationError,
    )

    with pytest.raises(
        TreasuryProductiveReadOnlyVenueObservationError, match="FUNDING_SOURCE_REQUIRED"
    ):
        execute_treasury_productive_reconciliation_chain_v1(
            _treasury(_minimal_margin_observation_v1())
        )
    report = execute_treasury_productive_reconciliation_chain_v1(_reconciled_obs())
    assert report["BASE_NUMERIC_BINDING"]["numeric_base_bound"]
    assert report["RISK_ADMISSION_BINDING_STATUS"] == "NO_RISK_ADMISSIBLE_MINT"
