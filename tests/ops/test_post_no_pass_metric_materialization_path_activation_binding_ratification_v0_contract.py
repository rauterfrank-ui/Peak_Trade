"""Contract tests for post-no-pass metric materialization path activation binding ratification v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.research.post_no_pass_metric_materialization_path_activation_binding_ratification_v0 import (
    BINDING_CLASS,
    CONFIRM_GO,
    MATERIALIZED_METRIC_SCHEMA_REF,
    METRIC_MATERIALIZATION_CONTRACT_REF,
    METRIC_MATERIALIZATION_PATH_REF,
    NEXT_EXECUTION_GO,
    PRIMARY_CAUSE,
    PROCESS_CLASSIFICATION,
    REQUIRED_BINDING_FIELDS,
    STRATEGY_VERSION,
    ValidationVerdict,
    materialize_post_no_pass_metric_materialization_path_activation_binding_ratification_v0,
    validate_post_no_pass_metric_materialization_path_activation_binding_ratification_v0,
)
from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (
    CONFIG_REL_PATH as SPARSE_V2_CONFIG_REL,
    RESEARCH_CANDIDATES,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BINDING_CONFIG = (
    REPO_ROOT
    / "config/research/post_no_pass_metric_materialization_path_activation_binding_ratification_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0.md"
)
SPARSE_V2_CONFIG = REPO_ROOT / SPARSE_V2_CONFIG_REL
CLOSEOUT_SECTION_PREFIX = (
    "#### POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0"
)
EVIDENCE_CLASS_ID = "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0"
SCOPE_STATUS = "PATH_ACTIVATION_BINDING_RATIFICATION_COMPLETE_NOT_EXECUTED"
CURRENT_STATE = (
    "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_COMPLETE_V0"
)
NEXT_CANONICAL_STEP = "REQUEST_OPERATOR_GO_FOR_POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
CURRENT_ADMISSIBLE_SCOPE = (
    "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
BASELINE_HEAD = "61c6b7dbbd2e4bf97c57c1ae08679c2f1aa2e4f4"
EVIDENCE_SUFFIX = (
    "post_no_pass_metric_materialization_path_activation_binding_ratification_v0_20260705T233631Z"
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
    "Path-Aktivierung/Binding-Ratifikation ≠ Evaluation-Autorisierung",
    "Keine Economic Evaluation",
    "PATH_PRESENT_BUT_NOT_EXECUTED",
    "metric materialization path activation",
    "no parameter rescue",
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
        "\n#### POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_V0"
    )
    return tail if next_heading == -1 else tail[:next_heading]


class TestPostNoPassMetricMaterializationPathActivationBindingRatificationV0Contract:
    def test_binding_config_exists_and_governance_gates(self) -> None:
        assert BINDING_CONFIG.is_file()
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert payload["status"] == SCOPE_STATUS
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["binding_class"] == BINDING_CLASS
        assert payload["process_classification"] == PROCESS_CLASSIFICATION
        assert payload["primary_cause"] == PRIMARY_CAUSE
        assert payload["path_activation_binding_ratified"] is True
        assert payload["authority_effect"] == "NONE"
        assert payload["runtime_effect"] == "NONE"
        assert payload["trading_effect"] == "NONE"
        assert payload["economic_evaluation_authorized"] is False
        assert payload["economic_evaluation_executed"] is False
        assert payload["evaluation_executed"] is False
        assert payload["backtest_executed"] is False
        assert payload["walk_forward_executed"] is False
        assert payload["monte_carlo_executed"] is False
        assert payload["stress_executed"] is False
        assert payload["promotion_eligible"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["same_binding_retry_allowed"] is False
        assert payload["parameter_rescue_allowed"] is False
        assert payload["threshold_lowering_allowed"] is False
        assert payload["no_evaluation_authority"] is True
        assert payload["no_runtime_authority"] is True
        assert payload["no_promotion_authority"] is True
        assert payload["required_next_go_for_execution"] == NEXT_EXECUTION_GO
        assert payload["futures_only"] is True
        assert payload["bitcoin_direction_allowed"] is False
        assert payload["baseline_head"] == BASELINE_HEAD
        assert payload["baseline_pr"] == "4886"
        assert payload["go_token"] == CONFIRM_GO
        assert payload["go_token_consumed"] is True
        assert payload["strategy_version"] == STRATEGY_VERSION
        assert payload["terminal_negative_evidence_unchanged"] is True
        assert payload["required_binding_fields"] == list(REQUIRED_BINDING_FIELDS)

    def test_binding_config_forbids_runtime_and_evaluation_execution(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
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
        ):
            assert action in forbidden, f"missing forbidden action: {action}"
        for action in FORBIDDEN_RUNTIME_ACTIONS:
            assert action in forbidden, f"missing forbidden runtime action: {action}"

    def test_all_candidates_have_required_bindings(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        candidates = payload["candidates"]
        assert len(candidates) == 3
        for candidate in candidates:
            for field in REQUIRED_BINDING_FIELDS:
                assert field in candidate, f"missing {field} for {candidate['strategy_id']}"
            assert candidate["strategy_version"] == STRATEGY_VERSION
            assert candidate["terminal_sparse_v2_verdict"] == "EXECUTION_FAILED_FAIL_CLOSED"
            assert candidate["substantially_differs_from_sparse_v2"] is True
            assert candidate["metric_materialization_path_ref"] == METRIC_MATERIALIZATION_PATH_REF
            assert (
                candidate["metric_materialization_contract_ref"]
                == METRIC_MATERIALIZATION_CONTRACT_REF
            )
            assert candidate["materialized_metric_schema_ref"] == MATERIALIZED_METRIC_SCHEMA_REF

    def test_binding_config_validates_against_materializer(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        sparse_v2 = json.loads(SPARSE_V2_CONFIG.read_text(encoding="utf-8"))
        validation = (
            validate_post_no_pass_metric_materialization_path_activation_binding_ratification_v0(
                payload,
                sparse_v2_completion=sparse_v2,
            )
        )
        assert validation.verdict == ValidationVerdict.ACCEPTED, validation.fail_reasons
        rematerialized = (
            materialize_post_no_pass_metric_materialization_path_activation_binding_ratification_v0(
                repo_root=REPO_ROOT,
                sparse_v2_completion=sparse_v2,
            )
        )
        assert rematerialized["completion_digest"] == payload["completion_digest"]

    def test_no_same_binding_retry_against_sparse_v2(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        sparse_v2 = json.loads(SPARSE_V2_CONFIG.read_text(encoding="utf-8"))
        for strategy_id in RESEARCH_CANDIDATES:
            sparse_v2_candidate = next(
                item for item in sparse_v2["candidates"] if item["strategy_id"] == strategy_id
            )
            path_candidate = next(
                item for item in payload["candidates"] if item["strategy_id"] == strategy_id
            )
            assert sparse_v2_candidate["strategy_version"] == "v2"
            assert path_candidate["strategy_version"] == "v3"
            assert (
                path_candidate["binding_semantic_digest"]
                != sparse_v2_candidate["binding_semantic_digest"]
            )

    def test_governance_doc_has_docs_token_and_boundary_phrases(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{SCOPE_STATUS}`" in body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in body
        assert f"`OPERATOR_GO` | `{CONFIRM_GO}`" in body
        assert "`GO_TOKEN_CONSUMED` | `true`" in body
        assert "`PATH_ACTIVATION_BINDING_RATIFIED` | `true`" in body
        assert f"`PRIMARY_CAUSE` | `{PRIMARY_CAUSE}`" in body
        assert "`ECONOMIC_EVALUATION_AUTHORIZED` | `false`" in body
        assert "`EVALUATION_EXECUTED` | `false`" in body
        assert "`BACKTEST_EXECUTED` | `false`" in body
        assert f"`REQUIRED_NEXT_GO_FOR_EXECUTION` | `{NEXT_EXECUTION_GO}`" in body
        for field in REQUIRED_BINDING_FIELDS:
            assert f"`{field}` | `BOUND`" in body
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body, f"missing boundary phrase: {phrase}"

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert authoritative_field_value("CURRENT_STATE") == CURRENT_STATE
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert (
            _field_value(
                text,
                "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0_STATUS",
            )
            == SCOPE_STATUS
        )
        assert _field_value(
            text,
            "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0_CONFIG_REF",
        ) == (
            "config/research/"
            "post_no_pass_metric_materialization_path_activation_binding_ratification_v0.json"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0_GO_TOKEN",
            )
            == CONFIRM_GO
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0_GO_TOKEN_CONSUMED",
            )
            == "true"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0_PRIMARY_CAUSE",
            )
            == PRIMARY_CAUSE
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0_PATH_ACTIVATION_BINDING_RATIFIED",
            )
            == "true"
        )
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert (
            authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == CURRENT_ADMISSIBLE_SCOPE
        )
        assert (
            authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == NEXT_EXECUTION_GO
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == SCOPE_STATUS
        assert _field_value(section, "VERDICT") == SCOPE_STATUS
        assert _field_value(section, "PROCESS_CLASSIFICATION") == PROCESS_CLASSIFICATION
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "GO_TOKEN") == CONFIRM_GO
        assert _field_value(section, "GO_TOKEN_CONSUMED") == "true"
        assert _field_value(section, "PATH_ACTIVATION_BINDING_RATIFIED") == "true"
        assert _field_value(section, "PRIMARY_CAUSE") == PRIMARY_CAUSE
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "EVALUATION_EXECUTED") == "false"
        assert _field_value(section, "REQUIRED_NEXT_GO_FOR_EXECUTION") == NEXT_EXECUTION_GO
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE") == CURRENT_ADMISSIBLE_SCOPE
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == NEXT_EXECUTION_GO
