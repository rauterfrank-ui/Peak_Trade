"""OD_ACCOUNT_EQUITY_SIZING_SOURCE adjudication and INV-SIZE invariant contracts."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.od_account_equity_sizing_source_canonical_adjudication_v1 import (
    ADJUDICATION_CONFIG,
    INV_SIZE_KEYS,
    build_adjudication_report_v1,
    load_adjudication_v1,
    validate_adjudication_against_repo_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_SURFACE,
    CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_TRANSFORMATION,
)

REPO = Path(__file__).resolve().parents[2]


def test_adjudication_contract_loads_and_validates() -> None:
    adj = load_adjudication_v1(REPO)
    ok, reasons = validate_adjudication_against_repo_v1(repo_root=REPO, adjudication=adj)
    assert ok, reasons
    report = build_adjudication_report_v1(repo_root=REPO)
    assert report["VALIDATION_OK"] is True
    assert report["DECISION_CASE"] == "A"
    assert report["CANONICALLY_UNIQUE_CANDIDATE_COUNT"] == 1


def test_inv_size_invariants_indexed() -> None:
    assert len(INV_SIZE_KEYS) == 10
    payload = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))
    sizing = payload["available_for_sizing"]
    assert sizing["canonical_meaning"] == (
        "TYPED_SEMANTIC_DIMENSION_RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
    )
    assert sizing["transformation_id"] == CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_TRANSFORMATION
    assert sizing["observation_surface"] == CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_SURFACE
    assert sizing["transformation_id"] == CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_ALGEBRA
    assert "DO_NOT_SUBTRACT" in sizing["u04_application"]
    assert sizing["risk_fraction_applied_here"] is False


def test_constants_align_with_adjudicated_dimension() -> None:
    payload = json.loads((REPO / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))
    assert (
        payload["available_for_sizing"]["observation_surface"]
        == CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_OBSERVATION_SURFACE
    )
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION == (
        "RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING"
    )
    assert (
        CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_U04_APPLICATION
        == "DO_NOT_SUBTRACT_ALREADY_NETTED_IN_VENUE_FREE_MARGIN"
    )
