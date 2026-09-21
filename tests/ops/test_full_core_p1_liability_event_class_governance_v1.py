"""P1 liability event-class governance witness tests (offline)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.governed_productive_account_equity_authority_producer_v1.p1_liability_event_class_governance_and_ratified_query_class_set_v1 import (
    CANONICAL_PACK_AS_OF_FOLDER,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    GLOBAL_EQUITY_STOCK_KIND_SET_UPLIFT,
    RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET,
    RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET_RESOLVED,
    build_p1_liability_event_class_witness_adjudication_v1,
    execute_p1_liability_event_class_governance_witness_v1,
    verify_canonical_p1_liability_governance_pack_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_independent_liability_event_surface_or_embedding_witness_qualification_v1 import (
    SELECTED_SURFACE_ID,
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


def test_p1_ratified_query_class_pins_without_global_uplift() -> None:
    assert SELECTED_SURFACE_ID in RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET
    assert RATIFIED_P1_LIABILITY_EVENT_QUERY_CLASS_SET_RESOLVED is True
    assert GLOBAL_EQUITY_STOCK_KIND_SET_UPLIFT is False


def test_adjudication_positive_on_sealed_packs() -> None:
    import json

    binding = json.loads((USDC_PACK / "p1_surface_binding_v1.json").read_text(encoding="utf-8"))
    discovery = json.loads(
        (USDC_PACK / "futures_p1_surface_discovery_v1.json").read_text(encoding="utf-8")
    )
    cd_claims = json.loads((CD_PACK / "claims.json").read_text(encoding="utf-8"))
    usdc_claims = json.loads((USDC_PACK / "claims.json").read_text(encoding="utf-8"))
    adjudication = build_p1_liability_event_class_witness_adjudication_v1(
        surface_binding=binding,
        surface_discovery=discovery,
        cd_claims=cd_claims,
        usdc_claims=usdc_claims,
    )
    assert adjudication["P1_LIABILITY_EVENT_CLASS_COMPLETENESS_PROVEN"] == "true"
    assert adjudication["GLOBAL_KIND_SET_UNCHANGED"] == "true"
    assert adjudication["NOT_EQUITY_STOCK_U05_KIND_RATIFICATION"] == "true"


def test_adjudication_fail_closed_on_wrong_surface() -> None:
    import json

    binding = json.loads((USDC_PACK / "p1_surface_binding_v1.json").read_text(encoding="utf-8"))
    binding = {**binding, "P1_EVENT_SURFACE": "GET_/api/v5/account/balance"}
    discovery = json.loads(
        (USDC_PACK / "futures_p1_surface_discovery_v1.json").read_text(encoding="utf-8")
    )
    cd_claims = json.loads((CD_PACK / "claims.json").read_text(encoding="utf-8"))
    usdc_claims = json.loads((USDC_PACK / "claims.json").read_text(encoding="utf-8"))
    adjudication = build_p1_liability_event_class_witness_adjudication_v1(
        surface_binding=binding,
        surface_discovery=discovery,
        cd_claims=cd_claims,
        usdc_claims=usdc_claims,
    )
    assert adjudication["P1_LIABILITY_EVENT_CLASS_COMPLETENESS_PROVEN"] == "false"


def test_canonical_liability_governance_pack_manifest() -> None:
    pack = REPO_ROOT / CANONICAL_PACK_RELPATH / CANONICAL_PACK_AS_OF_FOLDER
    if not (pack / "MANIFEST.sha256").is_file():
        pytest.skip("canonical pack not materialized in this checkout")
    assert verify_canonical_p1_liability_governance_pack_v1(repo_root=REPO_ROOT) == 0


def test_execute_replay_skips_persist() -> None:
    result = execute_p1_liability_event_class_governance_witness_v1(
        repo_root=REPO_ROOT,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        owner_go="OWNER_GO=true",
        persist_as_of="2026-09-21T04:00:00Z",
        skip_persist=True,
    )
    assert result.p1_liability_event_class_completeness_proven == "true"
    assert result.global_kind_set_unchanged == "true"
