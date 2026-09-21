"""P1 negative / completeness closeout contract tests (offline only)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    RAW_EQ_SOURCE_AUTHORITY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_negative_completeness_closeout_contract_v1 import (
    P1NegativeCompletenessInputV1,
    P1_CLOSEOUT_CONFLICTED,
    P1_CLOSEOUT_DOES_NOT_APPLY,
    P1_CLOSEOUT_PROVEN_NEGATIVE,
    P1_CLOSEOUT_UNKNOWN,
    P1_STATUS_DOES_NOT_APPLY,
    P1_STATUS_PROVEN_FALSE,
    P1_STATUS_UNKNOWN,
    REQUIREMENT_CURRENCY_DOMAIN,
    REQUIREMENT_LIABILITY_EVENT_CLASS,
    REQUIREMENT_PAGINATION,
    ZERO_ROWS_ALONE_MAY_PROVE_NEGATIVE,
    evaluate_p1_negative_completeness_v1,
    evaluate_sealed_interest_accrued_p1_closeout_v1,
    load_sealed_interest_accrued_p1_input_v1,
    ratified_absence_laws_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _all_true_input(**overrides: object) -> P1NegativeCompletenessInputV1:
    base = P1NegativeCompletenessInputV1(
        qualifying_event_count=0,
        nonqualifying_event_count=0,
        cd_row_count=0,
        usdc_scoped_row_count=0,
        account_identity_bound=True,
        account_mode_futures_ratified=True,
        venue_binding_complete=True,
        currency_domain_complete=True,
        liability_event_class_complete=True,
        time_domain_complete=True,
        surface_coverage_complete=True,
        pagination_complete=True,
        event_ordering_complete=True,
        observation_freshness_complete=True,
        restart_durability_complete=True,
        independence_from_balance_snapshot=True,
        independence_from_raw_eq=True,
        provenance_complete=True,
        applicability_account_spot_only=False,
        applicability_surface_futures_incapable=False,
        applicability_reason="",
    )
    return replace(base, **overrides)


def test_ratified_absence_laws_fail_closed() -> None:
    laws = ratified_absence_laws_v1()
    assert laws["EMPTY_ROWS_PROVE_ZERO_EVENTS"] is False
    assert laws["EMPTY_ROWS_PROVE_KIND_ABSENCE"] is False
    assert laws["ZERO_ROWS_ALONE_MAY_PROVE_NEGATIVE"] is False
    assert RAW_EQ_SOURCE_AUTHORITY is False


def test_zero_rows_alone_with_incomplete_completeness_stays_unknown() -> None:
    payload = _all_true_input(
        currency_domain_complete=False,
        pagination_complete=False,
        cd_row_count=0,
        usdc_scoped_row_count=0,
    )
    result = evaluate_p1_negative_completeness_v1(payload)
    assert result.closeout_decision == P1_CLOSEOUT_UNKNOWN
    assert result.p1_status_after == P1_STATUS_UNKNOWN
    assert result.zero_rows_alone_used is True
    assert REQUIREMENT_CURRENCY_DOMAIN in result.minimal_missing_completeness_set


def test_incomplete_pagination_blocks_proven_negative() -> None:
    payload = _all_true_input(pagination_complete=False, time_domain_complete=False)
    result = evaluate_p1_negative_completeness_v1(payload)
    assert result.closeout_decision == P1_CLOSEOUT_UNKNOWN
    assert REQUIREMENT_PAGINATION in result.minimal_missing_completeness_set


def test_all_completeness_predicates_proven_yields_proven_negative() -> None:
    result = evaluate_p1_negative_completeness_v1(_all_true_input())
    assert result.closeout_decision == P1_CLOSEOUT_PROVEN_NEGATIVE
    assert result.p1_status_after == P1_STATUS_PROVEN_FALSE
    assert result.minimal_missing_completeness_set == ()


def test_qualifying_event_conflicts_negative_closeout() -> None:
    result = evaluate_p1_negative_completeness_v1(_all_true_input(qualifying_event_count=1))
    assert result.closeout_decision == P1_CLOSEOUT_CONFLICTED
    assert result.p1_status_after == P1_STATUS_UNKNOWN


def test_does_not_apply_distinct_from_negative() -> None:
    result = evaluate_p1_negative_completeness_v1(
        _all_true_input(
            applicability_account_spot_only=True,
            applicability_reason="SPOT_ONLY_ACCOUNT_MODE",
        )
    )
    assert result.closeout_decision == P1_CLOSEOUT_DOES_NOT_APPLY
    assert result.p1_status_after == P1_STATUS_DOES_NOT_APPLY
    assert result.negative_evaluation == P1_CLOSEOUT_UNKNOWN


def test_sealed_cd_and_usdc_evidence_stays_unknown() -> None:
    currency_witness_pack = (
        REPO_ROOT
        / "evidence/ops/full_core_p1_currency_domain_completeness_witness_v1/2026-09-21T031500Z"
    )
    payload = load_sealed_interest_accrued_p1_input_v1(repo_root=REPO_ROOT)
    assert payload.cd_row_count == 0
    assert payload.usdc_scoped_row_count == 0
    assert payload.qualifying_event_count == 0
    assert payload.pagination_complete is False
    currency_pack_present = (currency_witness_pack / "MANIFEST.sha256").is_file()
    assert payload.currency_domain_complete is currency_pack_present
    evaluation = evaluate_sealed_interest_accrued_p1_closeout_v1(repo_root=REPO_ROOT)
    assert evaluation.closeout_decision == P1_CLOSEOUT_UNKNOWN
    assert evaluation.p1_status_after == P1_STATUS_UNKNOWN
    if currency_pack_present:
        assert evaluation.first_missing_completeness_predicate == REQUIREMENT_LIABILITY_EVENT_CLASS
    else:
        assert evaluation.first_missing_completeness_predicate == REQUIREMENT_CURRENCY_DOMAIN
        assert evaluation.network_required is True
    assert evaluation.new_producer_required is False


def test_account_currency_mismatch_rejection_via_loader_identity() -> None:
    payload = load_sealed_interest_accrued_p1_input_v1(repo_root=REPO_ROOT)
    broken = replace(payload, account_identity_bound=False)
    evaluation = evaluate_p1_negative_completeness_v1(broken)
    assert evaluation.closeout_decision == P1_CLOSEOUT_UNKNOWN
    assert "ACCOUNT_IDENTITY_COMPLETE" in evaluation.minimal_missing_completeness_set
