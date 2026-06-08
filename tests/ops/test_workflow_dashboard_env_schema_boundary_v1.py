"""Env/schema boundary for Workflow Dashboard V1."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_workflow_dashboard_env_constants_in_runtime_module() -> None:
    from src.webui.workflow_dashboard_runtime_v1 import ENV_ARCHIVE_ROOT, ENV_ENABLED

    assert ENV_ENABLED == "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED"
    assert ENV_ARCHIVE_ROOT == "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT"


def test_observability_hub_doc_documents_workflow_dashboard() -> None:
    doc = (PROJECT_ROOT / "docs/webui/observability/OBSERVABILITY_HUB_V0.md").read_text(
        encoding="utf-8"
    )
    assert "PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED" in doc
    assert "workflow_dashboard_readmodel.v1" in doc
    assert "UNIVERSE_SOURCE_NOT_PERSISTED" in doc


def test_universe_selection_contract_doc_exists() -> None:
    doc_path = PROJECT_ROOT / "docs/webui/observability/UNIVERSE_SELECTION_READMODEL_V1.md"
    assert doc_path.is_file()
    doc = doc_path.read_text(encoding="utf-8")
    assert "schema_name" in doc
    assert "universe_selection_readmodel.v1" in doc
    assert "readmodels&#47;universe_selection_readmodel.v1.json" in doc
    assert "BTC/USD" in doc
    assert "UNIVERSE_SOURCE_NOT_PERSISTED" in doc


def test_observability_hub_links_universe_selection_contract() -> None:
    doc = (PROJECT_ROOT / "docs/webui/observability/OBSERVABILITY_HUB_V0.md").read_text(
        encoding="utf-8"
    )
    assert "UNIVERSE_SELECTION_READMODEL_V1.md" in doc
    assert "universe_selection_readmodel.v1" in doc


REAL_SOURCE_CHARTER_DOC = (
    PROJECT_ROOT
    / "docs"
    / "webui"
    / "observability"
    / "FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md"
)
UNIVERSE_SELECTION_DOC = (
    PROJECT_ROOT / "docs" / "webui" / "observability" / "UNIVERSE_SELECTION_READMODEL_V1.md"
)


def test_futures_universe_real_source_charter_doc_exists_and_markers() -> None:
    assert REAL_SOURCE_CHARTER_DOC.is_file()
    doc = REAL_SOURCE_CHARTER_DOC.read_text(encoding="utf-8")
    assert "REAL_FUTURES_OBSERVABILITY_TRUTH_AVAILABLE=false" in doc
    assert "U2B_IMPLEMENTABLE_IMMEDIATELY=false" in doc
    assert "U2B_BLOCKED" in doc
    assert "Evidence != Approval/Lift/Live" in doc
    assert "market_ranking_funnel_readmodel.v0" in doc
    assert "FIXTURE_ONLY_AS_REAL_TRUTH_ALLOWED=false" in doc
    assert "MANIFEST_VERIFY_RC=0" in doc
    assert "SPOT_BTC_DUMMY_SELECTED_TRUTH_FORBIDDEN=true" in doc
    assert "FuturesProducerPacket" in doc
    assert "futures_universe_upstream_adapter_v1" in doc


def test_universe_selection_readmodel_links_real_source_charter() -> None:
    doc = UNIVERSE_SELECTION_DOC.read_text(encoding="utf-8")
    assert "FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md" in doc
    assert "Real-Source Charter" in doc
    assert "REAL_FUTURES_OBSERVABILITY_TRUTH_AVAILABLE=false" in doc
