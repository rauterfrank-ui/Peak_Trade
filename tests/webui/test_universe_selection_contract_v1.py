"""Static contract tests for universe_selection_readmodel.v1 (Slice 1)."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.webui.workflow_dashboard_readmodel_v1 import (
    SCHEMA_VERSION,
    UNIVERSE_SELECTION_SCHEMA_NAME,
    UNIVERSE_SELECTION_STORAGE_PATH,
    UniverseSelectionContractError,
    build_workflow_dashboard_readmodel_v1,
    load_universe_selection_contract,
    to_json_dict,
    validate_universe_selection_payload,
)

FIXTURE_ROOT = (
    project_root / "tests" / "fixtures" / "workflow_dashboard_readmodel_v1" / "universe_selection_readmodel_v1"
).resolve()
FIXTURE_MISSING = FIXTURE_ROOT / "missing_truth"
FIXTURE_COMPLETE = FIXTURE_ROOT / "complete_minimal"
FIXTURE_INVALID_BTC = FIXTURE_ROOT / "invalid_btc_usd_selected"
FIXTURE_ARCHIVE = (
    project_root
    / "tests"
    / "fixtures"
    / "workflow_dashboard_readmodel_v1"
    / "pipeline_minimal"
    / "archive_root"
).resolve()
CONTRACT_DOC = project_root / "docs" / "webui" / "observability" / "UNIVERSE_SELECTION_READMODEL_V1.md"
HUB_DOC = project_root / "docs" / "webui" / "observability" / "OBSERVABILITY_HUB_V0.md"


def test_contract_doc_exists_and_names_schema() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    assert "universe_selection_readmodel.v1" in text
    assert "readmodels/universe_selection_readmodel.v1.json" in text
    assert "BTC/USD" in text
    assert "UNIVERSE_SOURCE_NOT_PERSISTED" in text
    assert "live" in text.lower()
    assert "non_authorizing" in text


def test_observability_hub_references_universe_selection_contract() -> None:
    text = HUB_DOC.read_text(encoding="utf-8")
    assert "UNIVERSE_SELECTION_READMODEL_V1.md" in text
    assert "universe_selection_readmodel.v1" in text
    assert "UNIVERSE_SOURCE_NOT_PERSISTED" in text
    assert "readmodels/universe_selection_readmodel.v1.json" in text


def test_schema_constants() -> None:
    assert UNIVERSE_SELECTION_SCHEMA_NAME == "universe_selection_readmodel.v1"
    assert UNIVERSE_SELECTION_STORAGE_PATH == "readmodels/universe_selection_readmodel.v1.json"
    assert SCHEMA_VERSION == "workflow_dashboard_readmodel.v1"


def test_missing_truth_fixture_accepted() -> None:
    contract = load_universe_selection_contract(FIXTURE_MISSING)
    assert contract.schema_name == UNIVERSE_SELECTION_SCHEMA_NAME
    assert contract.universe == ()
    assert contract.ranking == ()
    assert contract.selected_future is None
    assert contract.missing_truth.universe == "UNIVERSE_SOURCE_NOT_PERSISTED"
    assert contract.missing_truth.selected_future == "SELECTED_FUTURE_NOT_PERSISTED"
    assert contract.fixture_marked is True


def test_complete_minimal_fixture_accepted() -> None:
    contract = load_universe_selection_contract(FIXTURE_COMPLETE)
    assert contract.fixture_marked is True
    assert len(contract.universe) == 3
    assert len(contract.ranking) == 2
    assert contract.selected_future is not None
    assert contract.selected_future.symbol == "SOLUSDT"
    assert contract.missing_truth.universe == "PERSISTED"
    assert contract.missing_truth.orders_fills_pnl == "NOT_PERSISTED"
    assert "BTC/USD" not in json.dumps(contract_to_safe_dict(contract))


def test_btc_usd_selected_truth_rejected() -> None:
    with pytest.raises(UniverseSelectionContractError, match="forbidden"):
        load_universe_selection_contract(FIXTURE_INVALID_BTC)


def test_live_source_stage_rejected() -> None:
    payload = json.loads(
        (FIXTURE_MISSING / "universe_selection_readmodel.v1.json").read_text(encoding="utf-8")
    )
    payload["source_stage"] = "live"
    with pytest.raises(UniverseSelectionContractError, match="forbidden"):
        validate_universe_selection_payload(payload)


def test_non_authorizing_required() -> None:
    payload = json.loads(
        (FIXTURE_MISSING / "universe_selection_readmodel.v1.json").read_text(encoding="utf-8")
    )
    payload["non_authorizing"] = False
    with pytest.raises(UniverseSelectionContractError, match="non_authorizing"):
        validate_universe_selection_payload(payload)


def test_forbidden_authority_field_in_row_rejected() -> None:
    payload = json.loads(
        (FIXTURE_COMPLETE / "universe_selection_readmodel.v1.json").read_text(encoding="utf-8")
    )
    payload["universe"][0]["live_authorized"] = True
    with pytest.raises(UniverseSelectionContractError, match="forbidden fields"):
        validate_universe_selection_payload(payload)


def test_missing_truth_inconsistent_with_rows_rejected() -> None:
    payload = json.loads(
        (FIXTURE_COMPLETE / "universe_selection_readmodel.v1.json").read_text(encoding="utf-8")
    )
    payload["missing_truth"]["universe"] = "UNIVERSE_SOURCE_NOT_PERSISTED"
    with pytest.raises(UniverseSelectionContractError, match="NOT_PERSISTED"):
        validate_universe_selection_payload(payload)


def test_dashboard_builder_unchanged_missing_truth() -> None:
    model = build_workflow_dashboard_readmodel_v1(FIXTURE_ARCHIVE)
    assert model.universe_missing.truth_status == "UNIVERSE_SOURCE_NOT_PERSISTED"
    assert model.top20_missing.truth_status == "TOP20_RANKING_NOT_PERSISTED"
    assert model.selected_future_missing.truth_status == "SELECTED_FUTURE_NOT_PERSISTED"
    assert model.future_detail_missing.truth_status == "FUTURE_DETAIL_NOT_AVAILABLE"
    dumped = to_json_dict(model)
    assert "SOLUSDT" not in str(dumped)
    assert "ETHUSDT" not in str(dumped)


def contract_to_safe_dict(contract: object) -> dict:
    from src.webui.workflow_dashboard_readmodel_v1.universe_selection_contract_v1 import (
        UniverseSelectionContractV1,
        contract_to_json_dict,
    )

    assert isinstance(contract, UniverseSelectionContractV1)
    return contract_to_json_dict(contract)


def test_market_surface_dummy_source_kind_rejected() -> None:
    payload = copy.deepcopy(
        json.loads((FIXTURE_COMPLETE / "universe_selection_readmodel.v1.json").read_text(encoding="utf-8"))
    )
    payload["selected_future"]["source_kind"] = "market_surface_dummy"
    with pytest.raises(UniverseSelectionContractError, match="source_kind forbidden"):
        validate_universe_selection_payload(payload)
