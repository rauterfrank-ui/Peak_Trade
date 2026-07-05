"""Contract tests for OKX full-panel CSR signal diagnostics decomposition evidence class scope v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/okx_full_panel_cross_sectional_ranking_signal_diagnostics_decomposition_evidence_class_scope_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_SIGNAL_DIAGNOSTICS_DECOMPOSITION_EVIDENCE_CLASS_SCOPE_V0.md"
)
CLOSEOUT_SECTION_PREFIX = "#### OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_SIGNAL_DIAGNOSTICS_DECOMPOSITION_EVIDENCE_CLASS_SCOPE_V0"
GO_TOKEN = (
    "GO_OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_SIGNAL_DIAGNOSTICS_DECOMPOSITION_"
    "EVIDENCE_CLASS_SCOPE_V0"
)
EVIDENCE_CLASS_ID = (
    "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_SIGNAL_DIAGNOSTICS_DECOMPOSITION_EVIDENCE_CLASS_V0"
)
SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
AUTOPSY_BUNDLE_SUFFIX = (
    "okx_full_panel_cross_sectional_ranking_strategy_archetype_failure_attribution_"
    "economic_autopsy_read_only_v0_20260705T020905Z"
)
REQUIRED_DIAGNOSTICS_MINIMUM = (
    "regime_breakdown",
    "per_instrument_pnl_breakdown",
    "long_short_pnl_split",
    "turnover_distribution",
    "gross_to_net_bridge",
    "fee_slippage_funding_bridge",
    "drawdown_path_decomposition",
)
FORBIDDEN_ACTIONS_MINIMUM = (
    "SAME_BINDING_RETRY",
    "PROMOTION",
    "RUNTIME",
    "PARAMETER_OPTIMIZATION",
    "ORDERS",
    "SCHEDULER",
    "CREDENTIALS",
    "ARMING",
    "LIVE",
)
BOUNDARY_PHRASES = (
    "NO_EVALUATION_IN_THIS_PR",
    "NO_SAME_BINDING_RETRY",
    "NO_PROMOTION",
    "NO_RUNTIME",
    "NO_PARAMETER_OPTIMIZATION",
    "NO_RESULT_RESCUE",
    "Primary Failure Class `NEGATIVE_RAW_EDGE` bleibt terminale negative Evidence",
    "INCONCLUSIVE-Regel",
    "No-Inference-Regel",
)
LARGE_EVIDENCE_GLOBS = (
    "**/ECONOMIC_VIABILITY_EVIDENCE_V1.json",
    "**/METRICS.json",
    "**/FAILURE_ATTRIBUTION_MATRIX.json",
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


class TestOkxFullPanelCsrSignalDiagnosticsDecompositionEvidenceClassScopeV0Contract:
    def test_scope_config_exists_and_governance_gates(self) -> None:
        assert SCOPE_CONFIG.is_file()
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["status"] == SCOPE_STATUS
        assert payload["authority_effect"] == "NONE"
        assert payload["evaluation_authorized"] is False
        assert payload["economic_evaluation_executed"] is False
        assert payload["diagnostics_executed"] is False
        assert payload["diagnostics_execution_authorized"] is False
        assert payload["runtime_authority"] is False
        assert payload["promotion_authorized"] is False
        assert payload["retry_allowed"] is False
        assert payload["immutable_binding_retry_allowed"] is False
        assert payload["required_future_operator_go"] is True
        assert payload["repo_mutation_scope"] == "GOVERNANCE_ONLY"
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["source_negative_evidence_pr"] == 4852
        assert payload["source_governance_closeout_pr"] == 4853
        assert AUTOPSY_BUNDLE_SUFFIX in payload["source_autopsy_bundle"]

    def test_scope_config_required_diagnostics_and_forbidden_actions(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        required = payload["required_diagnostics"]
        forbidden = payload["forbidden_actions"]
        for diagnostic in REQUIRED_DIAGNOSTICS_MINIMUM:
            assert diagnostic in required, f"missing required diagnostic: {diagnostic}"
        for action in FORBIDDEN_ACTIONS_MINIMUM:
            assert action in forbidden, f"missing forbidden action: {action}"

    def test_governance_doc_has_docs_token_and_boundary_phrases(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_SIGNAL_DIAGNOSTICS_"
                "DECOMPOSITION_EVIDENCE_CLASS_SCOPE_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{SCOPE_STATUS}`" in body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in body
        assert "`EVALUATION_AUTHORIZED` | `false`" in body
        assert "`authority_effect` | `NONE`" in body
        assert "PR #4852" in body
        assert "PR #4853" in body
        assert AUTOPSY_BUNDLE_SUFFIX in body
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body, f"missing boundary phrase: {phrase}"

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_SIGNAL_DIAGNOSTICS_DECOMPOSITION_EVIDENCE_CLASS_SCOPE_V0_STATUS",
            )
            == SCOPE_STATUS
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_SIGNAL_DIAGNOSTICS_DECOMPOSITION_EVIDENCE_CLASS_SCOPE_V0_GO_TOKEN",
            )
            == GO_TOKEN
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_SIGNAL_DIAGNOSTICS_DECOMPOSITION_EVIDENCE_CLASS_ID",
            )
            == EVIDENCE_CLASS_ID
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_SIGNAL_DIAGNOSTICS_DECOMPOSITION_DIAGNOSTICS_EXECUTION_AUTHORIZED",
            )
            == "false"
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_SIGNAL_DIAGNOSTICS_DECOMPOSITION_REQUIRED_FUTURE_OPERATOR_GO",
            )
            == "true"
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == SCOPE_STATUS
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "DIAGNOSTICS_EXECUTION_AUTHORIZED") == "false"
        assert _field_value(section, "PROMOTION_AUTHORIZED") == "false"
        assert _field_value(section, "RUNTIME_AUTHORITY") == "false"
        assert _field_value(section, "RETRY_ALLOWED") == "false"
        assert _field_value(section, "IMMUTABLE_BINDING_RETRY_ALLOWED") == "false"
        assert _field_value(section, "REQUIRED_FUTURE_OPERATOR_GO") == "true"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == "NO_RUNTIME_OR_PROMOTION_ACTION"
        assert AUTOPSY_BUNDLE_SUFFIX in _field_value(section, "SOURCE_AUTOPSY_BUNDLE")

    def test_no_large_evidence_files_in_repo(self) -> None:
        for pattern in LARGE_EVIDENCE_GLOBS:
            matches = list(REPO_ROOT.glob(pattern))
            assert not matches, f"large evidence file must not be in repo: {pattern}"
