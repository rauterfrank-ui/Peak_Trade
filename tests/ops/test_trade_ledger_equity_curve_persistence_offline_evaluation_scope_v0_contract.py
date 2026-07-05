"""Contract tests for trade ledger equity curve persistence offline evaluation scope v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/trade_ledger_equity_curve_persistence_offline_evaluation_scope_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_SCOPE_V0.md"
)
PARENT_EVIDENCE_CLASS_CLOSEOUT_SUFFIX = (
    "trade_ledger_equity_curve_evidence_class_scope_pr_squash_merge_closeout_v0_20260705T073804Z"
)
CLOSEOUT_SECTION_PREFIX = "#### TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_SCOPE_V0"
PARENT_CLOSEOUT_SECTION_PREFIX = "#### TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_SCOPE_V0"
OPERATOR_GO = "GO_TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_SCOPE_RATIFICATION_PR_V0"
EVIDENCE_CLASS_ID = "TRADE_LEDGER_AND_EQUITY_CURVE_PERSISTENCE_V0"
SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
SCOPE_VERDICT = (
    "TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_SCOPE_RATIFIED_NOT_EXECUTED"
)
ALLOWED_FUTURE_ARTIFACTS = ("TRADE_LEDGER_V1.jsonl", "EQUITY_CURVE_V1.jsonl")
FORBIDDEN_ACTIONS_MINIMUM = (
    "EVALUATION_EXECUTION_IN_THIS_SCOPE",
    "LEDGER_PERSISTENCE_EXECUTION_IN_THIS_SCOPE",
    "EQUITY_CURVE_PERSISTENCE_EXECUTION_IN_THIS_SCOPE",
    "BACKTEST_RERUN",
    "SIGNAL_RECALCULATION",
    "SAME_BINDING_RETRY",
    "PARAMETER_OPTIMIZATION",
    "THRESHOLD_LOWERING",
    "PROMOTION",
    "RUNTIME",
    "RUNTIME_REWIRE",
    "ORDERS",
    "CREDENTIALS",
)
BOUNDARY_PHRASES = (
    "NO_EVALUATION_IN_THIS_PR",
    "NO_LEDGER_PERSISTENCE_IN_THIS_PR",
    "NO_EQUITY_CURVE_PERSISTENCE_IN_THIS_PR",
    "NO_SAME_BINDING_RETRY",
    "NO_PROMOTION",
    "NO_RUNTIME",
    "NO_RUNTIME_REWIRE",
    "NO_PARAMETER_OPTIMIZATION",
    "NO_RESULT_RESCUE",
    "Scope ratification = Evaluation authorization",
    "Scope ratification = Ledger persistence execution",
    "Separates explizites Operator-GO",
    "Primary Failure Class `NEGATIVE_RAW_EDGE` bleibt unverändert terminal",
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


def _closeout_section(text: str, prefix: str) -> str:
    start = text.index(prefix)
    tail = text[start + len(prefix) :]
    next_heading = tail.find("\n#### ")
    return tail if next_heading == -1 else tail[:next_heading]


class TestTradeLedgerEquityCurvePersistenceOfflineEvaluationScopeV0Contract:
    def test_scope_config_exists_and_governance_gates(self) -> None:
        assert SCOPE_CONFIG.is_file()
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["offline_only"] is True
        assert payload["status"] == SCOPE_STATUS
        assert payload["verdict"] == SCOPE_VERDICT
        assert payload["authority_effect"] == "NONE"
        assert payload["evaluation_execution"] is False
        assert payload["evaluation_execution_authorized"] is False
        assert payload["ledger_persistence_execution"] is False
        assert payload["equity_curve_persistence_execution"] is False
        assert payload["no_evaluation_authority"] is True
        assert payload["no_runtime_authority"] is True
        assert payload["no_promotion_authority"] is True
        assert payload["no_same_binding_retry"] is True
        assert payload["no_runtime_rewire"] is True
        assert payload["primary_failure_class_unchanged"] == "NEGATIVE_RAW_EDGE"
        assert payload["persistence_execution_authorized"] is False
        assert payload["persistence_artifacts_persistable_in_this_scope"] is False
        assert (
            payload["persistence_artifacts_persistable_in_future_evaluation_execution_scope_only"]
            is True
        )
        assert payload["runtime_authority"] is False
        assert payload["promotion_authorized"] is False
        assert payload["promotion_eligible"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["same_binding_retry_allowed"] is False
        assert payload["parameter_optimization_allowed"] is False
        assert payload["threshold_lowering_allowed"] is False
        assert payload["result_rescue_allowed"] is False
        assert payload["repo_mutation_scope"] == "GOVERNANCE_ONLY"
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["offline_evaluation_scope_ratified"] is True
        assert payload["shadow_authorized"] is False
        assert payload["paper_authorized"] is False
        assert payload["testnet_authorized"] is False
        assert payload["scheduler_runtime_allowed"] is False
        assert payload["orders_allowed"] is False
        assert payload["credentials_allowed"] is False
        assert payload["arming_authorized"] is False
        assert payload["live_authorized"] is False
        assert payload["canary_authorized"] is False
        assert payload["adapter_submission_allowed"] is False

    def test_scope_config_allowed_future_artifacts_and_forbidden_actions(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["allowed_future_persistence_artifacts"] == list(ALLOWED_FUTURE_ARTIFACTS)
        forbidden = payload["forbidden_actions"]
        for action in FORBIDDEN_ACTIONS_MINIMUM:
            assert action in forbidden, f"missing forbidden action: {action}"

    def test_governance_doc_has_docs_token_and_boundary_phrases(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_SCOPE_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{SCOPE_VERDICT}`" in body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in body
        assert "`EVALUATION_EXECUTION` | `false`" in body
        assert "`LEDGER_PERSISTENCE_EXECUTION` | `false`" in body
        assert "`EQUITY_CURVE_PERSISTENCE_EXECUTION` | `false`" in body
        assert "`authority_effect` | `NONE`" in body
        assert PARENT_EVIDENCE_CLASS_CLOSEOUT_SUFFIX in body
        for artifact in ALLOWED_FUTURE_ARTIFACTS:
            assert f"`{artifact}`" in body
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body, f"missing boundary phrase: {phrase}"

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text, "TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_SCOPE_V0_STATUS"
            )
            == SCOPE_STATUS
        )
        assert (
            _field_value(
                text,
                "TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_SCOPE_V0_GO_TOKEN",
            )
            == OPERATOR_GO
        )
        assert (
            _field_value(
                text, "TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_SCOPE_V0_VERDICT"
            )
            == SCOPE_VERDICT
        )
        assert (
            _field_value(text, "TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        )
        assert (
            _field_value(
                text,
                "TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_NEXT_REQUIRES_RATIFIED_OFFLINE_EVALUATION_SCOPE",
            )
            == "true"
        )
        assert (
            _field_value(
                text, "TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_EVALUATION_EXECUTION_AUTHORIZED"
            )
            == "false"
        )
        assert (
            _field_value(text, "TRADE_LEDGER_EQUITY_CURVE_EVIDENCE_CLASS_AUTHORITY_EFFECT")
            == "NONE"
        )

    def test_registry_closeout_sections(self) -> None:
        text = read_registry()
        parent_section = _closeout_section(text, PARENT_CLOSEOUT_SECTION_PREFIX)
        assert _field_value(parent_section, "STATUS") == SCOPE_STATUS
        assert (
            _field_value(parent_section, "NEXT_REQUIRES_RATIFIED_OFFLINE_EVALUATION_SCOPE")
            == "true"
        )
        assert _field_value(parent_section, "EVALUATION_EXECUTION_AUTHORIZED") == "false"
        assert _field_value(parent_section, "AUTHORITY_EFFECT") == "NONE"

        section = _closeout_section(text, CLOSEOUT_SECTION_PREFIX)
        assert _field_value(section, "STATUS") == SCOPE_STATUS
        assert _field_value(section, "VERDICT") == SCOPE_VERDICT
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "EVALUATION_EXECUTION") == "false"
        assert _field_value(section, "LEDGER_PERSISTENCE_EXECUTION") == "false"
        assert _field_value(section, "EQUITY_CURVE_PERSISTENCE_EXECUTION") == "false"
        assert _field_value(section, "PROMOTION_AUTHORIZED") == "false"
        assert _field_value(section, "RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(section, "RUNTIME_AUTHORITY") == "false"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == "NO_RUNTIME_OR_PROMOTION_ACTION"

    def test_no_large_evidence_files_in_repo(self) -> None:
        for pattern in LARGE_EVIDENCE_GLOBS:
            matches = list(REPO_ROOT.glob(pattern))
            assert not matches, f"large evidence file must not be in repo: {pattern}"
