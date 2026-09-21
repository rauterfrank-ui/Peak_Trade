"""P1 bounded query traversal completeness witness tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.governed_productive_account_equity_authority_producer_v1.p1_bounded_query_traversal_completeness_witness_v1 import (
    CANONICAL_PACK_AS_OF_FOLDER,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    build_p1_bounded_query_traversal_witness_adjudication_v1,
    execute_p1_bounded_query_traversal_completeness_witness_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_completeness_witness_foundation_v1 import (
    ROOT_OBSERVATION_FRESHNESS,
    ROOT_PAGINATION,
    evaluate_sealed_p1_completeness_witness_bundle_v1,
    first_real_blocker_from_bundle_v1,
    root_by_id_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
USDC_PACK = (
    REPO_ROOT
    / "evidence/ops/full_core_u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1/2026-09-20T233000Z"
)
CD_PACK = (
    REPO_ROOT
    / "evidence/ops/full_core_u05_primary_proof_bound_interest_accrued_get_acquisition_v1/2026-09-15T010500Z"
)
LIABILITY_PACK = (
    REPO_ROOT
    / "evidence/ops/full_core_p1_liability_event_class_governance_witness_v1/2026-09-21T040000Z"
)
CURRENCY_PACK = (
    REPO_ROOT
    / "evidence/ops/full_core_p1_currency_domain_completeness_witness_v1/2026-09-21T031500Z"
)


def _pack_ready() -> bool:
    return (LIABILITY_PACK / "MANIFEST.sha256").is_file() and (
        CURRENCY_PACK / "MANIFEST.sha256"
    ).is_file()


def test_adjudication_proves_pagination_and_ordering_zero_rows() -> None:
    liability_adj = json.loads(
        (LIABILITY_PACK / "p1_liability_event_class_witness_adjudication_v1.json").read_text(
            encoding="utf-8"
        )
    )
    currency_adj = json.loads(
        (CURRENCY_PACK / "p1_currency_domain_witness_adjudication_v1.json").read_text(
            encoding="utf-8"
        )
    )
    binding = json.loads((USDC_PACK / "p1_surface_binding_v1.json").read_text(encoding="utf-8"))
    discovery = json.loads(
        (USDC_PACK / "futures_p1_surface_discovery_v1.json").read_text(encoding="utf-8")
    )
    cd_claims = json.loads((CD_PACK / "claims.json").read_text(encoding="utf-8"))
    usdc_claims = json.loads((USDC_PACK / "claims.json").read_text(encoding="utf-8"))
    offline = json.loads(
        (USDC_PACK / "p1_offline_qualification_v1.json").read_text(encoding="utf-8")
    )
    adjudication = build_p1_bounded_query_traversal_witness_adjudication_v1(
        surface_binding=binding,
        surface_discovery=discovery,
        cd_claims=cd_claims,
        usdc_claims=usdc_claims,
        usdc_offline=offline,
        liability_adjudication=liability_adj,
        currency_adjudication=currency_adj,
        d5_event_completeness_from_window="false",
        d5_binding_present=True,
    )
    assert adjudication["P1_PAGINATION_QUERY_TRAVERSAL_EXHAUSTION_PROVEN"] == "true"
    assert adjudication["P1_EVENT_ORDERING_COMPLETENESS_PROVEN"] == "true"
    assert adjudication["P1_OBSERVATION_FRESHNESS_COMPLETENESS_PROVEN"] == "false"
    assert adjudication["PAGINATION_DOMAIN_COMPLETENESS_CLAIMED"] == "false"


def test_sealed_bundle_pagination_complete_when_packs_present() -> None:
    if not _pack_ready():
        pytest.skip("witness packs not materialized")
    bundle = evaluate_sealed_p1_completeness_witness_bundle_v1(repo_root=REPO_ROOT)
    pagination = root_by_id_v1(bundle, ROOT_PAGINATION)
    assert pagination.complete is True
    root_id, _, _ = first_real_blocker_from_bundle_v1(bundle)
    assert root_id == ROOT_OBSERVATION_FRESHNESS


def test_canonical_traversal_pack_manifest() -> None:
    pack = REPO_ROOT / CANONICAL_PACK_RELPATH / CANONICAL_PACK_AS_OF_FOLDER
    if not (pack / "MANIFEST.sha256").is_file():
        pytest.skip("canonical pack not materialized")
    assert verify_manifest_sha256_v1(store_root=pack) == 0


def test_execute_skips_persist() -> None:
    if not _pack_ready():
        pytest.skip("liability pack required")
    result = execute_p1_bounded_query_traversal_completeness_witness_v1(
        repo_root=REPO_ROOT,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        owner_go="OWNER_GO=true",
        persist_as_of="2026-09-21T04:05:00Z",
        skip_persist=True,
    )
    assert result.pagination_proven == "true"
    assert result.event_ordering_proven == "true"
    assert result.observation_freshness_proven == "false"
