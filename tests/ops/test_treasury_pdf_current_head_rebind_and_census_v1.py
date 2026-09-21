"""Treasury PDF current-head rebind census tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.treasury_pdf_current_head_rebind_and_census_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    TreasuryPdfRebindCensusError,
    WP_ID,
    build_treasury_pdf_current_head_census_adjudication_v1,
    execute_treasury_pdf_current_head_rebind_v1,
    verify_canonical_treasury_pdf_rebind_pack_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PERSIST_AS_OF = "2026-09-21T01:00:00Z"


def test_adjudication_fail_closed_on_sha_mismatch() -> None:
    with pytest.raises(TreasuryPdfRebindCensusError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        build_treasury_pdf_current_head_census_adjudication_v1(
            repo_root=REPO_ROOT,
            origin_main_sha="0" * 40,
        )


def test_adjudication_covers_phases_and_blocker() -> None:
    adj = build_treasury_pdf_current_head_census_adjudication_v1(
        repo_root=REPO_ROOT,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert adj["PDF_AUTHORITY"] == "NONE"
    assert adj["CENSUS_COMPLETE"] == "true"
    assert adj["FULL_CORE_P1_STATUS"] == "CLOSED"
    assert adj["FULL_CORE_P2_P3_ON_CURRENT_HEAD"] == "NOT_CANONICALLY_DEFINED"
    matrix = adj["CURRENT_TREASURY_CAPABILITY_MATRIX"]
    assert matrix["TREASURY_PHASE_2_READ_ONLY_RECONCILIATION"]["classification"] == "IMPLEMENTED"
    assert matrix["TREASURY_PHASE_3_SHADOW_ENFORCEMENT"]["classification"] == "IMPLEMENTED"
    assert adj["TREASURY_INTERFERENCE_PROOF"]["TREASURY_INTERFERENCE_PROOF"] == "PASS"
    assert "C08_TREASURY_OBSERVED_OR_RECONCILED_CAPITAL" in adj["EARLIEST_REAL_TREASURY_BLOCKER"]
    assert (
        "E4_TREASURY_CAPITAL_ADMISSION_TO_ACCOUNT_EQUITY_ORCHESTRATION_PRODUCTIVE_HOST_JOIN"
        in adj["PDF_REQUIREMENTS_ALREADY_SATISFIED"]
    )
    at = adj["PDF_AUDIT_TESTS_AT01_AT15"]
    assert at["AT03"]["classification"] == "IMPLEMENTED"
    assert at["AT13"]["classification"] == "NOT_PROVEN"


def test_execute_persist_and_manifest_verify() -> None:
    result = execute_treasury_pdf_current_head_rebind_v1(
        repo_root=REPO_ROOT,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        owner_go=OWNER_GO,
        persist_as_of=PERSIST_AS_OF,
        skip_persist=False,
    )
    assert result.wp_id == WP_ID
    assert result.census_complete == "true"
    assert result.interference_proof == "PASS"
    assert verify_canonical_treasury_pdf_rebind_pack_v1(repo_root=REPO_ROOT) == 0


def test_owner_go_fail_closed() -> None:
    with pytest.raises(TreasuryPdfRebindCensusError, match="OWNER_GO_NOT_AUTHORIZED"):
        execute_treasury_pdf_current_head_rebind_v1(
            repo_root=REPO_ROOT,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            owner_go="NOT_AUTHORIZED",
            persist_as_of=PERSIST_AS_OF,
            skip_persist=True,
        )
