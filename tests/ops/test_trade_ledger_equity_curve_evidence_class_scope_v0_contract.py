"""Contract tests for trade ledger and equity curve evidence class scope v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = REPO_ROOT / "config/research/trade_ledger_equity_curve_evidence_class_scope_v0.json"
GOVERNANCE_DOC = REPO_ROOT / "docs/governance/TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_SCOPE_V0.md"
CLOSEOUT_SECTION_PREFIX = "#### TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_SCOPE_V0"
GO_TOKEN = "GO_TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_SCOPE_DEFINITION_PR_V0"
EVIDENCE_CLASS_ID = "TRADE_LEDGER_AND_EQUITY_CURVE_PERSISTENCE_V0"
SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
MATERIALIZATION_BUNDLE_SUFFIX = (
    "okx_full_panel_cross_sectional_ranking_trade_level_artifact_materialization_"
    "evidence_execution_read_only_v0_20260705T072422Z"
)
TRADE_LEDGER_FIELDS_MINIMUM = (
    "side",
    "net_pnl",
    "gross_pnl",
    "fees",
    "slippage",
    "funding",
    "regime_label",
    "ranking_score",
    "signal_bucket",
    "equity_before",
    "equity_after",
    "drawdown_after_trade",
)
EQUITY_CURVE_FIELDS_MINIMUM = (
    "equity",
    "drawdown",
    "cumulative_fees",
    "cumulative_slippage",
    "cumulative_funding",
    "exposure_notional",
)
FORBIDDEN_ACTIONS_MINIMUM = (
    "ECONOMIC_EVALUATION_REEXECUTION",
    "BACKTEST_RERUN",
    "SIGNAL_RECALCULATION",
    "SAME_BINDING_RETRY",
    "PARAMETER_OPTIMIZATION",
    "THRESHOLD_LOWERING",
    "PROMOTION",
    "RUNTIME",
    "ORDERS",
    "CREDENTIALS",
)
BOUNDARY_PHRASES = (
    "NO_EVALUATION_IN_THIS_PR",
    "NO_SAME_BINDING_RETRY",
    "NO_PROMOTION",
    "NO_RUNTIME",
    "NO_PARAMETER_OPTIMIZATION",
    "NO_RESULT_RESCUE",
    "Primary Failure Class `NEGATIVE_RAW_EDGE` bleibt terminale negative Evidence",
    "Scope definition = Evaluation authorization",
    "Ledger persistence = Result rescue",
    "Separates explizites Operator-GO",
)
LARGE_EVIDENCE_GLOBS = (
    "**/TRADE_LEDGER_V1.jsonl",
    "**/EQUITY_CURVE_V1.jsonl",
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


class TestTradeLedgerEquityCurveEvidenceClassScopeV0Contract:
    def test_scope_config_exists_and_governance_gates(self) -> None:
        assert SCOPE_CONFIG.is_file()
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["status"] == SCOPE_STATUS
        assert payload["authority_effect"] == "NONE"
        assert payload["no_evaluation_authority"] is True
        assert payload["no_runtime_authority"] is True
        assert payload["no_promotion_authority"] is True
        assert payload["no_same_binding_retry"] is True
        assert payload["primary_failure_class_unchanged"] == "NEGATIVE_RAW_EDGE"
        assert payload["persistence_authorized"] is False
        assert payload["persistence_executed"] is False
        assert payload["runtime_authority"] is False
        assert payload["promotion_authorized"] is False
        assert payload["same_binding_retry_allowed"] is False
        assert payload["parameter_optimization_allowed"] is False
        assert payload["threshold_lowering_allowed"] is False
        assert payload["result_rescue_allowed"] is False
        assert payload["required_future_operator_go"] is True
        assert payload["repo_mutation_scope"] == "GOVERNANCE_ONLY"
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert MATERIALIZATION_BUNDLE_SUFFIX in payload["source_materialization_bundle"]

    def test_scope_config_required_artifacts_and_fields(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        required = payload["required_artifacts"]
        forbidden = payload["forbidden_actions"]
        assert "TRADE_LEDGER_V1.jsonl" in required
        assert "EQUITY_CURVE_V1.jsonl" in required
        for field in TRADE_LEDGER_FIELDS_MINIMUM:
            assert field in payload["trade_ledger_required_fields"], (
                f"missing trade ledger field: {field}"
            )
        for field in EQUITY_CURVE_FIELDS_MINIMUM:
            assert field in payload["equity_curve_required_fields"], (
                f"missing equity curve field: {field}"
            )
        for action in FORBIDDEN_ACTIONS_MINIMUM:
            assert action in forbidden, f"missing forbidden action: {action}"

    def test_governance_doc_has_docs_token_and_boundary_phrases(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker("DOCS_TOKEN_TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_SCOPE_V0")
            in body
        )
        assert f"`VERDICT` | `{SCOPE_STATUS}`" in body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in body
        assert "`EVALUATION_AUTHORIZED` | `false`" in body
        assert "`authority_effect` | `NONE`" in body
        assert MATERIALIZATION_BUNDLE_SUFFIX in body
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body, f"missing boundary phrase: {phrase}"

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(text, "TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_SCOPE_V0_STATUS")
            == SCOPE_STATUS
        )
        assert (
            _field_value(text, "TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_SCOPE_V0_GO_TOKEN")
            == GO_TOKEN
        )
        assert (
            _field_value(text, "TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        )
        assert (
            _field_value(text, "TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_PRIMARY_FAILURE_UNCHANGED")
            == "NEGATIVE_RAW_EDGE"
        )
        assert (
            _field_value(
                text, "TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_REQUIRED_FUTURE_OPERATOR_GO"
            )
            == "true"
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == SCOPE_STATUS
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "PERSISTENCE_EXECUTION_AUTHORIZED") == "false"
        assert _field_value(section, "PROMOTION_AUTHORIZED") == "false"
        assert _field_value(section, "RUNTIME_AUTHORITY") == "false"
        assert _field_value(section, "SAME_BINDING_RETRY_ALLOWED") == "false"
        assert _field_value(section, "REQUIRED_FUTURE_OPERATOR_GO") == "true"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == "NO_RUNTIME_OR_PROMOTION_ACTION"
        assert MATERIALIZATION_BUNDLE_SUFFIX in _field_value(
            section, "SOURCE_MATERIALIZATION_BUNDLE"
        )

    def test_no_large_evidence_files_in_repo(self) -> None:
        for pattern in LARGE_EVIDENCE_GLOBS:
            matches = list(REPO_ROOT.glob(pattern))
            assert not matches, f"large evidence file must not be in repo: {pattern}"
