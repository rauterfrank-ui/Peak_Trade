"""Contract tests for post-no-pass metric materialization diagnostics derived next research scope definition v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_no_pass_metric_materialization_diagnostics_derived_next_research_scope_definition_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_V0.md"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_V0"
)
OPERATOR_GO = "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_V0"
EVIDENCE_CLASS_ID = (
    "POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_V0"
)
SCOPE_ID = (
    "POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_V0"
)
SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
PROCESS_CLASSIFICATION = "NEW_RATIFIED_RESEARCH_SCOPE_OR_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_V0"
SELECTED_CLASS = "D"
PRIMARY_CAUSE = "PATH_PRESENT_BUT_NOT_EXECUTED"
NEXT_BINDING_GO = "GO_POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0"
NEXT_EXECUTION_GO = (
    "GO_POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
AUTHORITATIVE_NEXT_CANONICAL_STEP = "REQUEST_OPERATOR_GO_FOR_POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
HISTORICAL_CLOSEOUT_NEXT_CANONICAL_STEP = "REQUEST_OPERATOR_GO_FOR_POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0"
AUTHORITATIVE_CURRENT_STATE = (
    "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_COMPLETE_V0"
)
AUTHORITATIVE_ADMISSIBLE_SCOPE = (
    "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
HISTORICAL_CLOSEOUT_ADMISSIBLE_SCOPE = (
    "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0"
)
BASELINE_HEAD = "f4709c51044a05c6dcc1c640d28c7567e33d71a7"
DIAGNOSTICS_EVIDENCE_SUFFIX = "post_no_pass_inconclusive_metric_materialization_path_diagnostics_evidence_execution_v0_20260705T230238Z"
REQUIRED_BINDING_FIELDS = (
    "strategy_id",
    "strategy_version",
    "parameter_binding",
    "dataset_binding",
    "period_binding",
    "instrument_binding",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "implementation_digest",
    "config_digest",
    "data_digest",
)
FORBIDDEN_RUNTIME_ACTIONS = (
    "RUNTIME",
    "SHADOW",
    "PAPER",
    "TESTNET",
    "SCHEDULER",
    "ORDERS",
    "CREDENTIALS",
    "ARMING",
    "LIVE",
)
BOUNDARY_PHRASES = (
    "Scope-Definition ≠ Binding-Ratifikation",
    "Keine Evaluation in diesem Scope",
    "PATH_PRESENT_BUT_NOT_EXECUTED",
    "Metric-Materialization-Path-Aktivierung/Binding",
    "NO_NEW_CANDIDATE_HOLD",
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
    next_heading = tail.find(
        "\n#### POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
    )
    return tail if next_heading == -1 else tail[:next_heading]


class TestPostNoPassMetricMaterializationDiagnosticsDerivedNextResearchScopeDefinitionV0Contract:
    def test_scope_config_exists_and_governance_gates(self) -> None:
        assert SCOPE_CONFIG.is_file()
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["status"] == SCOPE_STATUS
        assert payload["scope_id"] == SCOPE_ID
        assert payload["selected_class"] == SELECTED_CLASS
        assert payload["process_classification"] == PROCESS_CLASSIFICATION
        assert payload["primary_cause"] == PRIMARY_CAUSE
        assert payload["authority_effect"] == "NONE"
        assert payload["runtime_effect"] == "NONE"
        assert payload["trading_effect"] == "NONE"
        assert payload["economic_evaluation_authorized"] is False
        assert payload["promotion_eligible"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["same_binding_retry_allowed"] is False
        assert payload["parameter_rescue_allowed"] is False
        assert payload["threshold_lowering_allowed"] is False
        assert payload["live_authorized"] is False
        assert payload["core_system_mutation_allowed"] is False
        assert payload["canonical_trading_logic_mutation_allowed"] is False
        assert payload["master_v2_mutation_allowed"] is False
        assert payload["double_play_mutation_allowed"] is False
        assert payload["risk_sizing_mutation_allowed"] is False
        assert payload["safety_runtime_mutation_allowed"] is False
        assert payload["no_evaluation_authority"] is True
        assert payload["no_runtime_authority"] is True
        assert payload["no_promotion_authority"] is True
        assert payload["required_future_operator_go"] is True
        assert payload["required_next_go_for_binding_ratification"] == NEXT_BINDING_GO
        assert payload["required_next_go_for_execution"] == NEXT_EXECUTION_GO
        assert payload["required_versioned_binding_fields"] == list(REQUIRED_BINDING_FIELDS)
        assert payload["futures_only"] is True
        assert payload["bitcoin_direction_allowed"] is False
        assert payload["baseline_head"] == BASELINE_HEAD
        assert payload["baseline_pr"] == "4885"
        assert payload["operator_go"] == OPERATOR_GO
        assert payload["go_token_consumed"] is True
        assert payload["diagnostic_mapped_ratio"] == 1.0
        assert payload["diagnostics_manifest_verify_rc"] == 0
        assert DIAGNOSTICS_EVIDENCE_SUFFIX in payload["diagnostics_evidence_ref"]

    def test_scope_config_forbids_runtime_and_evaluation_execution(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        forbidden = payload["blocked_actions"]
        for action in (
            "ECONOMIC_EVALUATION_EXECUTION",
            "BACKTEST_RERUN",
            "WALK_FORWARD_EXECUTION",
            "MONTE_CARLO_EXECUTION",
            "STRESS_EXECUTION",
            "SAME_BINDING_RETRY",
            "PARAMETER_RESCUE",
            "THRESHOLD_LOWERING",
            "EVALUATION_EXECUTION_IN_THIS_SCOPE",
            "BINDING_RATIFICATION_IN_THIS_SCOPE",
        ):
            assert action in forbidden, f"missing forbidden action: {action}"
        for action in FORBIDDEN_RUNTIME_ACTIONS:
            assert action in forbidden, f"missing forbidden runtime action: {action}"

    def test_governance_doc_has_docs_token_and_boundary_phrases(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{SCOPE_STATUS}`" in body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in body
        assert f"`SELECTED_CLASS` | `{SELECTED_CLASS}`" in body
        assert f"`OPERATOR_GO` | `{OPERATOR_GO}`" in body
        assert "`GO_TOKEN_CONSUMED` | `true`" in body
        assert f"`PRIMARY_CAUSE` | `{PRIMARY_CAUSE}`" in body
        assert "`ECONOMIC_EVALUATION_AUTHORIZED` | `false`" in body
        assert "`RUNTIME_REWIRE_ADMISSIBLE` | `false`" in body
        assert "`CORE_SYSTEM_MUTATION_ALLOWED` | `false`" in body
        assert "`CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED` | `false`" in body
        assert "`MASTER_V2_MUTATION_ALLOWED` | `false`" in body
        assert "`DOUBLE_PLAY_MUTATION_ALLOWED` | `false`" in body
        assert "`RISK_SIZING_MUTATION_ALLOWED` | `false`" in body
        assert "`SAFETY_RUNTIME_MUTATION_ALLOWED` | `false`" in body
        assert "`authority_effect` | `NONE`" in body
        assert f"`REQUIRED_NEXT_GO_FOR_BINDING_RATIFICATION` | `{NEXT_BINDING_GO}`" in body
        assert f"`REQUIRED_NEXT_GO_FOR_EXECUTION` | `{NEXT_EXECUTION_GO}`" in body
        for field in REQUIRED_BINDING_FIELDS:
            assert f"`{field}` | `true`" in body
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body, f"missing boundary phrase: {phrase}"

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert authoritative_field_value("CURRENT_STATE") == AUTHORITATIVE_CURRENT_STATE
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == AUTHORITATIVE_NEXT_CANONICAL_STEP
        assert (
            _field_value(
                text,
                "POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_V0_STATUS",
            )
            == SCOPE_STATUS
        )
        assert _field_value(
            text,
            "POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_V0_CONFIG_REF",
        ) == (
            "config/research/post_no_pass_metric_materialization_diagnostics_derived_next_research_scope_definition_v0.json"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_V0_GO_TOKEN",
            )
            == OPERATOR_GO
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_V0_GO_TOKEN_CONSUMED",
            )
            == "true"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_V0_PRIMARY_CAUSE",
            )
            == PRIMARY_CAUSE
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_V0_REQUIRED_NEXT_GO_FOR_BINDING_RATIFICATION",
            )
            == NEXT_BINDING_GO
        )
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("NEW_CANDIDATES_RATIFIED") == "false"
        assert (
            authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE")
            == AUTHORITATIVE_ADMISSIBLE_SCOPE
        )
        assert (
            authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == NEXT_EXECUTION_GO
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == SCOPE_STATUS
        assert _field_value(section, "VERDICT") == SCOPE_STATUS
        assert _field_value(section, "PROCESS_CLASSIFICATION") == PROCESS_CLASSIFICATION
        assert _field_value(section, "SELECTED_CLASS") == SELECTED_CLASS
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "GO_TOKEN") == OPERATOR_GO
        assert _field_value(section, "GO_TOKEN_CONSUMED") == "true"
        assert _field_value(section, "PRIMARY_CAUSE") == PRIMARY_CAUSE
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "SAME_BINDING_RETRY_ALLOWED") == "false"
        assert _field_value(section, "PARAMETER_RESCUE_ALLOWED") == "false"
        assert _field_value(section, "THRESHOLD_LOWERING_ALLOWED") == "false"
        assert _field_value(section, "REQUIRED_NEXT_GO_FOR_BINDING_RATIFICATION") == NEXT_BINDING_GO
        assert _field_value(section, "REQUIRED_NEXT_GO_FOR_EXECUTION") == NEXT_EXECUTION_GO
        assert (
            _field_value(section, "NEXT_CANONICAL_STEP") == HISTORICAL_CLOSEOUT_NEXT_CANONICAL_STEP
        )
        assert (
            _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE")
            == HISTORICAL_CLOSEOUT_ADMISSIBLE_SCOPE
        )
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == NEXT_BINDING_GO
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "TRADING_EFFECT") == "NONE"
        assert _field_value(section, "FUTURES_ONLY") == "true"
        assert _field_value(section, "BITCOIN_DIRECTION_ALLOWED") == "false"
