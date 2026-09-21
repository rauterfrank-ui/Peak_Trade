"""P1 max evidence campaign tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from src.ops.governed_productive_account_equity_authority_producer_v1.p1_max_evidence_campaign_to_next_real_blocker_v1 import (
    AUTHORIZED_QUERY,
    EXPECTED_ORIGIN_MAIN_SHA,
    MAX_AUTHORIZED_GET_COUNT,
    OWNER_GO,
    P1MaxEvidenceCampaignError,
    build_p1_campaign_witness_adjudication_v1,
    execute_p1_max_evidence_campaign_to_next_real_blocker_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_primary_proof_bound_interest_accrued_get_acquisition_v1 import (
    AUTHORIZED_QUERY as CD_QUERY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GENESIS_STORE = (
    REPO_ROOT / "evidence/ops/full_core_d6_path_b_d4_d5_genesis_rebaseline_v1/2026-09-13T170318Z"
)
PERSIST_AS_OF = "2026-09-21T02:00:00Z"


def _canonical_store(tmp_path: Path) -> Path:
    return tmp_path / CANONICAL_PACK_RELPATH / CANONICAL_PACK_AS_OF_FOLDER


def test_campaign_query_matches_cd_unscoped() -> None:
    assert AUTHORIZED_QUERY == CD_QUERY
    assert MAX_AUTHORIZED_GET_COUNT == 1


def test_adjudication_zero_rows_fail_closed_currency() -> None:
    adjudication = build_p1_campaign_witness_adjudication_v1(
        cd_row_count=0,
        usdc_row_count=0,
        fresh_row_count=0,
        fresh_request_utc="2026-09-21T02:00:00Z",
        d5_window_start="2026-09-13T17:03:18Z",
        d5_window_end="2026-09-13T17:03:18Z",
        d5_event_completeness_from_window="false",
    )
    assert adjudication["APPLICABLE_LOAN_CURRENCY_DOMAIN_EXHAUSTION_PROVEN"] == "false"
    assert "ZERO_ROWS" in adjudication["CURRENCY_DOMAIN_MISSING_FACT"]


def test_non_canonical_store_path_fail_closed(tmp_path: Path) -> None:
    genesis = tmp_path / "genesis"
    shutil.copytree(GENESIS_STORE, genesis)
    with pytest.raises(P1MaxEvidenceCampaignError, match="CAMPAIGN_STORE_NOT_CANONICAL"):
        execute_p1_max_evidence_campaign_to_next_real_blocker_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "wrong_root",
            repo_root=REPO_ROOT,
            genesis_store_root=genesis,
            transport=RecordingFakeCanaryTransportV1(status_code=200, bodies_by_endpoint={}),
            persist_as_of=PERSIST_AS_OF,
        )
