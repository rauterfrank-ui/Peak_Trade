"""P1 currency-domain completeness witness tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from src.ops.governed_productive_account_equity_authority_producer_v1.p1_completeness_witness_foundation_v1 import (
    ROOT_CURRENCY_DOMAIN,
    ROOT_LIABILITY_EVENT_CLASS,
    evaluate_sealed_p1_completeness_witness_bundle_v1,
    first_real_blocker_from_bundle_v1,
    root_by_id_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_currency_domain_completeness_witness_v1 import (
    AUTHORIZED_QUERY,
    CANONICAL_PACK_AS_OF_FOLDER,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    MAX_AUTHORIZED_GET_COUNT,
    OWNER_GO,
    P1CurrencyDomainCompletenessWitnessError,
    build_p1_currency_domain_witness_adjudication_v1,
    execute_p1_currency_domain_completeness_witness_v1,
    extract_applicable_market_loan_ccy_set_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GENESIS_STORE = (
    REPO_ROOT / "evidence/ops/full_core_d6_path_b_d4_d5_genesis_rebaseline_v1/2026-09-13T170318Z"
)
PERSIST_AS_OF = "2026-09-21T03:15:00Z"


def _sample_interest_limits_body(*, ccys: tuple[str, ...]) -> dict[str, object]:
    return {
        "code": "0",
        "msg": "",
        "data": [
            {
                "debt": "0",
                "records": [{"ccy": ccy, "rate": "0.0001"} for ccy in ccys],
            }
        ],
    }


def test_interest_limits_query_type2_only() -> None:
    assert AUTHORIZED_QUERY == "type=2"
    assert MAX_AUTHORIZED_GET_COUNT == 1


def test_extract_ccy_set_sorted_unique() -> None:
    body = _sample_interest_limits_body(ccys=("USDC", "BTC", "USDC"))
    assert extract_applicable_market_loan_ccy_set_v1(body=body) == ("USDC", "BTC")


def test_extract_rejects_empty_records() -> None:
    body = {"code": "0", "data": [{"records": []}]}
    with pytest.raises(P1CurrencyDomainCompletenessWitnessError, match="RECORDS_EMPTY"):
        extract_applicable_market_loan_ccy_set_v1(body=body)


def test_adjudication_positive_closed_world_and_zero_rows() -> None:
    adjudication = build_p1_currency_domain_witness_adjudication_v1(
        applicable_market_loan_ccy_set=("USDC", "BTC"),
        cd_row_count=0,
        usdc_row_count=0,
        campaign_row_count=0,
        settlement_ccy="USDC",
    )
    assert adjudication["P1_CURRENCY_DOMAIN_COMPLETENESS_PROVEN"] == "true"
    assert adjudication["CLOSED_WORLD_ENUMERATION_PROVEN"] == "true"
    assert adjudication["APPLICABLE_LOAN_CURRENCY_DOMAIN_EXHAUSTION_PROVEN"] == "true"


def test_adjudication_fail_zero_rows_without_enumeration() -> None:
    adjudication = build_p1_currency_domain_witness_adjudication_v1(
        applicable_market_loan_ccy_set=(),
        cd_row_count=0,
        usdc_row_count=0,
        campaign_row_count=0,
        settlement_ccy="USDC",
    )
    assert adjudication["P1_CURRENCY_DOMAIN_COMPLETENESS_PROVEN"] == "false"
    assert adjudication["CURRENCY_DOMAIN_MISSING_FACT"] != "NONE"


def test_adjudication_fail_usdc_scoped_zero_alone() -> None:
    adjudication = build_p1_currency_domain_witness_adjudication_v1(
        applicable_market_loan_ccy_set=(),
        cd_row_count=0,
        usdc_row_count=0,
        campaign_row_count=0,
        settlement_ccy="USDC",
    )
    assert adjudication["USDC_FILTER_NON_AUTHORITY"] == "true"
    assert adjudication["P1_CURRENCY_DOMAIN_COMPLETENESS_PROVEN"] == "false"


def test_execute_rejects_non_canonical_store(tmp_path: Path) -> None:
    genesis = tmp_path / "genesis"
    shutil.copytree(GENESIS_STORE, genesis)
    body = _sample_interest_limits_body(ccys=("USDC",))
    with pytest.raises(P1CurrencyDomainCompletenessWitnessError, match="NOT_CANONICAL"):
        execute_p1_currency_domain_completeness_witness_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "wrong",
            repo_root=REPO_ROOT,
            genesis_store_root=genesis,
            skip_network=True,
            interest_limits_body=body,
            persist_as_of=PERSIST_AS_OF,
        )


def test_sealed_repo_currency_domain_complete_when_witness_pack_present() -> None:
    store = REPO_ROOT / CANONICAL_PACK_RELPATH / CANONICAL_PACK_AS_OF_FOLDER
    if not (store / "MANIFEST.sha256").is_file():
        pytest.skip("canonical currency-domain witness pack not materialized")
    bundle = evaluate_sealed_p1_completeness_witness_bundle_v1(
        repo_root=REPO_ROOT, bound_origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA
    )
    assert root_by_id_v1(bundle, ROOT_CURRENCY_DOMAIN).complete is True
    blocker_id, blocker_class, _missing = first_real_blocker_from_bundle_v1(bundle)
    assert blocker_id == ROOT_LIABILITY_EVENT_CLASS
    assert blocker_class == "GOVERNANCE"
