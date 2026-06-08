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
    assert "readmodels/universe_selection_readmodel.v1.json" in doc
    assert "BTC/USD" in doc
    assert "UNIVERSE_SOURCE_NOT_PERSISTED" in doc


def test_observability_hub_links_universe_selection_contract() -> None:
    doc = (PROJECT_ROOT / "docs/webui/observability/OBSERVABILITY_HUB_V0.md").read_text(
        encoding="utf-8"
    )
    assert "UNIVERSE_SELECTION_READMODEL_V1.md" in doc
    assert "universe_selection_readmodel.v1" in doc
