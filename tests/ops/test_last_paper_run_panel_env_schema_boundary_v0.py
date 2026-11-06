"""Env/schema boundary for Last Paper Run panel v0."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_last_paper_run_panel_env_constants_in_runtime_module() -> None:
    from src.webui.last_paper_run_panel_runtime_v0 import ENV_BUNDLE_ROOT, ENV_ENABLED

    assert ENV_ENABLED == "PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED"
    assert ENV_BUNDLE_ROOT == "PEAK_TRADE_LAST_PAPER_RUN_BUNDLE_ROOT"


def test_observability_hub_doc_documents_panel() -> None:
    doc = (PROJECT_ROOT / "docs/webui/observability/OBSERVABILITY_HUB_V0.md").read_text(
        encoding="utf-8"
    )
    assert "PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED" in doc
    assert "last_paper_run_panel_readmodel.v0" in doc
    assert "NOT_PERSISTED" in doc
