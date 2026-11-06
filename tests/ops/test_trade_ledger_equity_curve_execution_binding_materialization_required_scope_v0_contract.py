"""Contract tests for trade ledger equity curve execution binding materialization required scope v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/trade_ledger_equity_curve_execution_binding_materialization_required_scope_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_REQUIRED_SCOPE_V0.md"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_REQUIRED_SCOPE_V0"
)
OPERATOR_GO = "GO_TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_SELECTION_SCOPE_PR_V0"
EVIDENCE_CLASS_ID = "TRADE_LEDGER_AND_EQUITY_CURVE_PERSISTENCE_V0"
SCOPE_STATUS = "BINDING_MATERIALIZATION_REQUIRED"
SCOPE_VERDICT = "EXECUTION_BINDING_SELECTION_SCOPE_FAIL_CLOSED_BINDING_MATERIALIZATION_REQUIRED"
ALLOWED_ARTIFACTS = ("TRADE_LEDGER_V1.jsonl", "EQUITY_CURVE_V1.jsonl")
PARTIAL_CANDIDATE = "trend_following/v1"
PARTIAL_CANDIDATE_DOCS = "trend_following&#47;v1"
PARTIAL_BINDING_DIGEST = "ea3bde558a2ffd903ed7b7f678cb0cf0a8a4b1f1bb7f5978f7b5bc8f69ab8478"
PREFLIGHT_BUNDLE_SUFFIX = (
    "trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0_20260705T075246Z"
)
FORBIDDEN_ACTIONS_MINIMUM = (
    "EVALUATION_EXECUTION",
    "BACKTEST_RERUN",
    "LEDGER_PERSISTENCE_EXECUTION",
    "EQUITY_CURVE_PERSISTENCE_EXECUTION",
    "SAME_BINDING_RETRY",
    "PARAMETER_OPTIMIZATION",
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
    "Keine Binding-Pins erfinden",
    "Primary Failure Class `NEGATIVE_RAW_EDGE` bleibt unverändert",
)
LARGE_EVIDENCE_GLOBS = (
    "**/TRADE_LEDGER_V1.jsonl",
    "**/EQUITY_CURVE_V1.jsonl",
)
REQUIRED_PARTIAL_FIELDS = (
    "candidate_id",
    "strategy_id",
    "strategy_version",
    "parameter_binding_ref",
    "dataset_binding_ref",
    "period_binding_ref",
    "instrument_binding_ref",
    "fee_model_binding_ref",
    "slippage_model_binding_ref",
    "funding_model_binding_ref",
    "execution_model_binding_ref",
    "economic_policy_binding_ref",
    "implementation_digest",
    "config_digest",
    "data_digest",
    "binding_digest",
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


class TestTradeLedgerEquityCurveExecutionBindingMaterializationRequiredScopeV0Contract:
    def test_scope_config_fail_closed_and_governance_gates(self) -> None:
        assert SCOPE_CONFIG.is_file()
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["offline_only"] is True
        assert payload["status"] == SCOPE_STATUS
        assert payload["verdict"] == SCOPE_VERDICT
        assert payload["binding_selection_status"] == SCOPE_STATUS
        assert payload["authority_effect"] == "NONE"
        assert payload["evaluation_execution"] is False
        assert payload["ledger_persistence_execution"] is False
        assert payload["equity_curve_persistence_execution"] is False
        assert payload["promotion_authorized"] is False
        assert payload["same_binding_retry_allowed"] is False
        assert payload["allowed_bundle_only"] is True
        assert payload["repo_evidence_files_allowed"] is False
        assert payload["primary_failure_class"] == "NEGATIVE_RAW_EDGE"
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["repo_mutation_scope"] == "GOVERNANCE_ONLY"

    def test_scope_config_partial_binding_and_missing_artifacts(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        partial = payload["discovered_partial_binding"]
        assert partial["candidate_id"] == PARTIAL_CANDIDATE
        assert partial["binding_digest"] == PARTIAL_BINDING_DIGEST
        for field in REQUIRED_PARTIAL_FIELDS:
            assert field in partial, f"missing partial binding field: {field}"
        missing = payload["missing_binding_artifacts"]
        assert "execution_owner_ref" in missing
        assert "execution_runner_ref" in missing
        assert payload["allowed_output_artifacts"] == list(ALLOWED_ARTIFACTS)
        forbidden = payload["forbidden_actions"]
        for action in FORBIDDEN_ACTIONS_MINIMUM:
            assert action in forbidden, f"missing forbidden action: {action}"

    def test_governance_doc_has_docs_token_and_boundary_phrases(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_REQUIRED_SCOPE_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{SCOPE_VERDICT}`" in body
        assert f"`candidate_id` | `{PARTIAL_CANDIDATE_DOCS}`" in body
        assert PREFLIGHT_BUNDLE_SUFFIX in body
        for artifact in ALLOWED_ARTIFACTS:
            assert f"`{artifact}`" in body
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body, f"missing boundary phrase: {phrase}"

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_REQUIRED_SCOPE_V0_STATUS",
            )
            == SCOPE_STATUS
        )
        assert (
            _field_value(
                text,
                "TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_REQUIRED_SCOPE_V0_VERDICT",
            )
            == SCOPE_VERDICT
        )
        assert (
            _field_value(
                text,
                "TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_REQUIRED_SCOPE_V0_GO_TOKEN",
            )
            == OPERATOR_GO
        )
        assert (
            _field_value(
                text,
                "TRADE_LEDGER_EQUITY_CURVE_EXECUTION_BINDING_MATERIALIZATION_REQUIRED_SCOPE_V0_PARTIAL_CANDIDATE",
            )
            == PARTIAL_CANDIDATE_DOCS
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == SCOPE_STATUS
        assert _field_value(section, "VERDICT") == SCOPE_VERDICT
        assert _field_value(section, "PARTIAL_CANDIDATE_ID") == PARTIAL_CANDIDATE_DOCS
        assert _field_value(section, "EVALUATION_EXECUTION") == "false"
        assert _field_value(section, "LEDGER_PERSISTENCE_EXECUTION") == "false"
        assert _field_value(section, "EQUITY_CURVE_PERSISTENCE_EXECUTION") == "false"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == "NO_RUNTIME_OR_PROMOTION_ACTION"

    def test_no_large_evidence_files_in_repo(self) -> None:
        for pattern in LARGE_EVIDENCE_GLOBS:
            matches = list(REPO_ROOT.glob(pattern))
            assert not matches, f"large evidence file must not be in repo: {pattern}"
