"""P1 completeness witness foundation tests (offline only)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.governed_productive_account_equity_authority_producer_v1.p1_completeness_witness_foundation_v1 import (
    BLOCKER_GOVERNANCE,
    DERIVED_PROVENANCE,
    DERIVED_TIME_DOMAIN,
    P1CompletenessWitnessFoundationError,
    P1SealedWitnessEvidenceV1,
    ROOT_CURRENCY_DOMAIN,
    ROOT_EVENT_ORDERING,
    ROOT_LIABILITY_EVENT_CLASS,
    ROOT_PAGINATION,
    WITNESS_COMPLETE,
    WITNESS_INCOMPLETE,
    compose_p1_completeness_witness_bundle_v1,
    derive_provenance_witness_v1,
    derive_time_domain_witness_v1,
    evaluate_currency_domain_witness_v1,
    evaluate_liability_event_class_witness_v1,
    evaluate_pagination_exhaustion_witness_v1,
    evaluate_sealed_p1_completeness_witness_bundle_v1,
    first_real_blocker_from_bundle_v1,
    load_sealed_p1_witness_evidence_v1,
    p1_conjunction_status_from_bundle_v1,
    root_by_id_v1,
    validate_witness_bundle_v1,
    witness_bundle_digest_v1,
    witness_bundle_to_mapping_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_negative_completeness_closeout_contract_v1 import (
    P1_CLOSEOUT_UNKNOWN,
    REQUIREMENT_CURRENCY_DOMAIN,
    REQUIREMENT_LIABILITY_EVENT_CLASS,
    evaluate_sealed_interest_accrued_p1_closeout_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_CURRENCY_WITNESS_PACK = (
    REPO_ROOT
    / "evidence/ops/full_core_p1_currency_domain_completeness_witness_v1/2026-09-21T031500Z"
)


def _sealed_evidence() -> P1SealedWitnessEvidenceV1:
    return load_sealed_p1_witness_evidence_v1(repo_root=REPO_ROOT)


def _currency_witness_pack_present() -> bool:
    return (_CURRENCY_WITNESS_PACK / "MANIFEST.sha256").is_file()


def test_sealed_currency_domain_witness_rejects_usdc_alone() -> None:
    evidence = _sealed_evidence()
    result = evaluate_currency_domain_witness_v1(evidence)
    if _currency_witness_pack_present():
        assert result.complete is True
        assert result.status == WITNESS_COMPLETE
    else:
        assert result.complete is False
        assert result.status == WITNESS_INCOMPLETE
        assert result.network_required is True


def test_liability_event_class_witness_governance_blocker() -> None:
    evidence = _sealed_evidence()
    result = evaluate_liability_event_class_witness_v1(evidence)
    assert result.complete is False
    assert result.governance_required is True
    assert result.blocker_class == BLOCKER_GOVERNANCE


def test_pagination_witness_max_pages_one_fail_closed() -> None:
    evidence = _sealed_evidence()
    result = evaluate_pagination_exhaustion_witness_v1(evidence)
    assert result.complete is False
    assert result.root_id == ROOT_PAGINATION


def test_derived_time_incomplete_when_pagination_incomplete() -> None:
    evidence = _sealed_evidence()
    pagination = evaluate_pagination_exhaustion_witness_v1(evidence)
    derived = derive_time_domain_witness_v1(pagination=pagination, evidence=evidence)
    assert derived.complete is False
    assert derived.predicate_id == DERIVED_TIME_DOMAIN


def test_derived_provenance_incomplete_without_domain_closure() -> None:
    evidence = _sealed_evidence()
    bundle = compose_p1_completeness_witness_bundle_v1(evidence)
    provenance = derive_provenance_witness_v1(
        evidence=evidence,
        currency=root_by_id_v1(bundle, ROOT_CURRENCY_DOMAIN),
        time_domain=bundle.time_domain,
        pagination=root_by_id_v1(bundle, ROOT_PAGINATION),
    )
    assert provenance.complete is False
    assert provenance.predicate_id == DERIVED_PROVENANCE


def test_sealed_witness_bundle_validate_and_digest_stable() -> None:
    bundle = evaluate_sealed_p1_completeness_witness_bundle_v1(repo_root=REPO_ROOT)
    validate_witness_bundle_v1(bundle)
    mapping = witness_bundle_to_mapping_v1(bundle)
    assert mapping["SCHEMA_CLASS"] == "P1_COMPLETENESS_WITNESS_FOUNDATION_V1"
    digest_a = witness_bundle_digest_v1(bundle)
    digest_b = witness_bundle_digest_v1(bundle)
    assert digest_a == digest_b
    assert len(digest_a) == 64


def test_sealed_bundle_first_blocker_follows_root_order() -> None:
    bundle = evaluate_sealed_p1_completeness_witness_bundle_v1(repo_root=REPO_ROOT)
    root_id, blocker_class, missing = first_real_blocker_from_bundle_v1(bundle)
    if _currency_witness_pack_present():
        assert root_id == ROOT_LIABILITY_EVENT_CLASS
        assert blocker_class == BLOCKER_GOVERNANCE
    else:
        assert root_id == ROOT_CURRENCY_DOMAIN
        assert blocker_class != "NONE"
    assert missing != ""


def test_p1_conjunction_stays_unknown_on_sealed_evidence() -> None:
    bundle = evaluate_sealed_p1_completeness_witness_bundle_v1(repo_root=REPO_ROOT)
    assert p1_conjunction_status_from_bundle_v1(bundle) == "UNKNOWN_INCOMPLETE"


def test_6665_consumer_sealed_closeout_still_unknown() -> None:
    evaluation = evaluate_sealed_interest_accrued_p1_closeout_v1(repo_root=REPO_ROOT)
    assert evaluation.closeout_decision == P1_CLOSEOUT_UNKNOWN
    if _currency_witness_pack_present():
        assert evaluation.first_missing_completeness_predicate == REQUIREMENT_LIABILITY_EVENT_CLASS
    else:
        assert evaluation.first_missing_completeness_predicate == REQUIREMENT_CURRENCY_DOMAIN


def test_event_ordering_witness_fail_closed_on_zero_rows() -> None:
    evidence = _sealed_evidence()
    bundle = compose_p1_completeness_witness_bundle_v1(evidence)
    ordering = root_by_id_v1(bundle, ROOT_EVENT_ORDERING)
    assert ordering.complete is False


def test_positive_pagination_complete_hypothesis_still_blocked_by_law() -> None:
    evidence = _sealed_evidence()
    patched = replace(
        evidence,
        reopen_adjudication={
            **dict(evidence.reopen_adjudication),
            "CD_EXHAUSTION_PROVEN": "true",
            "CD_PAGE_SCOPE": "multi_page",
        },
        surface_binding={
            **dict(evidence.surface_binding),
            "MAX_PAGES": "3",
        },
    )
    pagination = evaluate_pagination_exhaustion_witness_v1(patched)
    assert pagination.complete is False


def test_conflict_d5_event_completeness_from_window() -> None:
    evidence = replace(_sealed_evidence(), d5_event_completeness_from_window="true")
    bundle = compose_p1_completeness_witness_bundle_v1(evidence)
    freshness = root_by_id_v1(bundle, "OBSERVATION_FRESHNESS_COMPLETE")
    assert freshness.status == "CONFLICTED"


def test_loader_missing_file_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_sealed_p1_witness_evidence_v1(repo_root=tmp_path)


def test_validate_bundle_rejects_duplicate_roots() -> None:
    bundle = evaluate_sealed_p1_completeness_witness_bundle_v1(repo_root=REPO_ROOT)
    dup_roots = bundle.roots + (bundle.roots[0],)
    broken = replace(bundle, roots=dup_roots)
    with pytest.raises(P1CompletenessWitnessFoundationError):
        validate_witness_bundle_v1(broken)


def test_closeout_missing_set_includes_liability_class() -> None:
    evaluation = evaluate_sealed_interest_accrued_p1_closeout_v1(repo_root=REPO_ROOT)
    assert REQUIREMENT_LIABILITY_EVENT_CLASS in evaluation.minimal_missing_completeness_set


def test_campaign_witness_currency_incomplete_with_explicit_missing_fact() -> None:
    evidence = replace(
        _sealed_evidence(),
        currency_domain_witness={},
        campaign_witness={
            "APPLICABLE_LOAN_CURRENCY_DOMAIN_EXHAUSTION_PROVEN": "false",
            "CURRENCY_DOMAIN_MISSING_FACT": "TEST_MISSING_FACT",
        },
    )
    result = evaluate_currency_domain_witness_v1(evidence)
    assert result.complete is False
    assert "TEST_MISSING_FACT" in result.detail
