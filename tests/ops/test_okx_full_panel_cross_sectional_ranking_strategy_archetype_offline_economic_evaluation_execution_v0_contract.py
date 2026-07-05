"""Contract tests for OKX full-panel CSR archetype offline economic evaluation execution v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/"
    "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_BOUNDED_OFFLINE_ECONOMIC_EVALUATION_V0.md"
)
RUNNER_SCRIPT = (
    REPO_ROOT / "scripts/ops/"
    "run_okx_full_panel_cross_sectional_ranking_strategy_archetype_offline_economic_evaluation_execution_v0.py"
)
EXECUTION_MODULE = (
    REPO_ROOT / "src/research/"
    "okx_full_panel_cross_sectional_ranking_strategy_archetype_offline_economic_evaluation_execution_v0.py"
)
OPS_CONFIG = (
    REPO_ROOT
    / "config/ops/okx_full_panel_cross_sectional_ranking_strategy_archetype_economic_evaluation_v0.json"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_"
    "BOUNDED_OFFLINE_ECONOMIC_EVALUATION_V0"
)
GO_TOKEN = (
    "GO_OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_"
    "BOUNDED_OFFLINE_ECONOMIC_EVALUATION_V0"
)
EVIDENCE_CLASS_ID = "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_V0"
VERDICT = "ROBUSTNESS_FAILED"
EXPECTED_ORIGIN_MAIN = "4dd3e0155e7bbd6d5265b2b0dc334f7f7d71efda"
EVIDENCE_BUNDLE_SUFFIX = (
    "okx_full_panel_cross_sectional_ranking_strategy_archetype_"
    "bounded_offline_economic_evaluation_v0_20260705T014731Z"
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    tail = text[start + len(CLOSEOUT_SECTION_PREFIX) :]
    next_heading = tail.find("\n#### ")
    return tail if next_heading == -1 else tail[:next_heading]


class TestOkxFullPanelCsrArchetypeOfflineEconomicEvaluationExecutionV0Contract:
    def test_runner_and_execution_module_exist(self) -> None:
        assert RUNNER_SCRIPT.is_file()
        assert EXECUTION_MODULE.is_file()
        assert OPS_CONFIG.is_file()

    def test_execution_module_go_token_and_authority(self) -> None:
        from src.research.okx_full_panel_cross_sectional_ranking_strategy_archetype_offline_economic_evaluation_execution_v0 import (
            AUTHORITY_EFFECT,
            EXPECTED_ORIGIN_MAIN_SHA,
            GO_TOKEN as MODULE_GO_TOKEN,
            RUNTIME_EFFECT,
        )

        assert MODULE_GO_TOKEN == GO_TOKEN
        assert AUTHORITY_EFFECT == "NONE"
        assert RUNTIME_EFFECT == "NONE"
        assert EXPECTED_ORIGIN_MAIN_SHA == EXPECTED_ORIGIN_MAIN

    def test_ops_config_strategy_archetype_and_evidence_class(self) -> None:
        payload = json.loads(OPS_CONFIG.read_text(encoding="utf-8"))
        assert payload["strategy_archetype_id"] == "cross_sectional_ranking_selection"
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert (
            payload["cross_sectional_evaluation_binding_v0"]["parameter_binding"][
                "parameter_search_forbidden"
            ]
            is True
        )

    def test_governance_doc_has_docs_token_and_verdict(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_"
                "BOUNDED_OFFLINE_ECONOMIC_EVALUATION_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{VERDICT}`" in body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in body
        assert "`EVALUATION_EXECUTED` | `true`" in body
        assert "`ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` | `false`" in body
        assert "`RUNTIME_AUTHORITY` | `false`" in body
        assert "`authority_effect` | `NONE`" in body
        assert "`MANIFEST_VERIFY_RC` | `0`" in body

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_OFFLINE_ECONOMIC_EVALUATION_V0_STATUS",
            )
            == "OFFLINE_ECONOMIC_EVALUATION_COMPLETE"
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_OFFLINE_ECONOMIC_EVALUATION_V0_GO_TOKEN",
            )
            == GO_TOKEN
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_OFFLINE_ECONOMIC_EVALUATION_VERDICT",
            )
            == VERDICT
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_OFFLINE_ECONOMIC_EVALUATION_MANIFEST_VERIFY_RC",
            )
            == "0"
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "OFFLINE_ECONOMIC_EVALUATION_COMPLETE"
        assert _field_value(section, "VERDICT") == VERDICT
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "EVALUATION_EXECUTED") == "true"
        assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert _field_value(section, "CANDIDATE_RATIFIED") == "false"
        assert _field_value(section, "RUNTIME_AUTHORITY") == "false"
        assert _field_value(section, "MANIFEST_VERIFY_RC") == "0"
        assert EVIDENCE_BUNDLE_SUFFIX in _field_value(section, "EVIDENCE_BUNDLE_PATH")
        assert _field_value(section, "NEXT_CANONICAL_STEP") == "NO_RUNTIME_OR_PROMOTION_ACTION"
