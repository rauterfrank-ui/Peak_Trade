"""Contract tests for post-no-pass sparse signal inconclusive failure classification v0."""

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
    / "config/research/post_no_pass_sparse_signal_inconclusive_failure_classification_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0.md"
)
CLOSEOUT_SECTION_PREFIX = "#### POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0"
EVIDENCE_CLASS_ID = "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0"
SELECTED_CLASS = "E"
EXECUTION_STATUS = "CLASSIFICATION_EXECUTION_COMPLETE_INCONCLUSIVE"
CLASSIFICATION_CURRENT_STATE = (
    "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_EXECUTION_COMPLETE_V0"
)
AUTHORITATIVE_CURRENT_STATE = "POST_PR4883_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_COMPLETE_V0"
PROCESS_CLASSIFICATION = (
    "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_EXECUTION_V0"
)
SCOPE_DEFINITION_GO = (
    "GO_POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_SCOPE_DEFINITION_ONLY_V0"
)
EXECUTION_GO = "GO_POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0"
HISTORICAL_NEXT_CANONICAL_STEP = (
    "NEW_VERSIONED_RESEARCH_SCOPE_SELECTION_REQUIRES_OPERATOR_RATIFICATION_V0"
)
HISTORICAL_ADMISSIBLE_SCOPE = "NEW_VERSIONED_RESEARCH_SCOPE_SELECTION_V0"
AUTHORITATIVE_NEXT_CANONICAL_STEP = (
    "REQUEST_OPERATOR_GO_FOR_POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
)
AUTHORITATIVE_ADMISSIBLE_SCOPE = (
    "POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_CLASS_V0"
)
RATIFICATION_GO = "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_V0"
PRIMARY_CLASSIFICATION = "INCONCLUSIVE_SPARSE_SIGNAL_ZERO_TRADE"
PARENT_EVIDENCE_SUFFIX = "post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_execution_v0_20260705T213529Z"
NEW_EVIDENCE_SUFFIX = (
    "post_no_pass_sparse_signal_inconclusive_failure_classification_execution_v0_20260705T222507Z"
)
FAILED_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
FORBIDDEN_NEXT_SCOPE_MARKERS = (
    "RUNTIME",
    "SHADOW",
    "PAPER",
    "TESTNET",
    "LIVE",
    "CANARY",
)
CLASSIFICATION_AXES = (
    "sparse_signal_vs_zero_trade_separation",
    "signal_trade_coverage_per_candidate",
    "economic_viability_metric_materialization_failure",
    "panel_adapter_runner_defect_classification",
    "schema_gate_threshold_failure_classification",
    "insufficient_trades_classification",
    "metric_materialization_path_failure",
    "walk_forward_gate_precondition_failure",
    "stress_monte_carlo_precondition_failure",
    "execution_model_assumption_exposure",
    "dataset_period_coverage_adequacy",
    "portfolio_contribution_diagnostics_research_only",
)
BOUNDARY_PHRASES = (
    "NO_EVALUATION_IN_THIS_SCOPE",
    "NO_SAME_BINDING_RETRY",
    "NO_PROMOTION",
    "NO_RUNTIME",
    "NO_PARAMETER_RESCUE",
    "TERMINAL_NEGATIVE_EVIDENCE_UNCHANGED",
    "NO_ECONOMIC_EVALUATION_EXECUTION_SCOPE=true",
)
AUTHORITY_TRUE_FLAGS = (
    "economic_evaluation_authorized",
    "promotion_eligible",
    "runtime_rewire_admissible",
    "runtime_authority",
    "same_binding_retry_allowed",
    "parameter_rescue_allowed",
    "threshold_lowering_allowed",
    "classification_execution_authorized",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "canary_authorized",
    "live_authorized",
    "orders_allowed",
    "scheduler_runtime_allowed",
)
RESULT_REQUIRED_KEYS = (
    "evidence_class",
    "process_classification",
    "consumed_go_token",
    "source_state",
    "primary_classification",
    "economic_evaluation_authorized",
    "economic_evaluation_executed",
    "backtests_executed",
    "runtime_rewire_admissible",
    "live_authorized",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "orders_allowed",
    "scheduler_runtime_allowed",
    "reason_codes",
    "source_evidence_refs",
    "manifest_digest",
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
        "\n#### POST_NO_PASS_ROBUSTNESS_FAILURE_NEXT_RESEARCH_SCOPE_DEFINITION_V0"
    )
    return tail if next_heading == -1 else tail[:next_heading]


class TestPostNoPassSparseSignalInconclusiveFailureClassificationV0Contract:
    def test_scope_config_exists_and_execution_gates(self) -> None:
        assert SCOPE_CONFIG.is_file()
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["selected_class"] == SELECTED_CLASS
        assert payload["status"] == EXECUTION_STATUS
        assert payload["process_classification"] == PROCESS_CLASSIFICATION
        assert payload["primary_classification"] == PRIMARY_CLASSIFICATION
        assert payload["offline_only"] is True
        assert payload["non_authorizing"] is True
        assert payload["classification_executed"] is True
        assert payload["execution_go_token"] == EXECUTION_GO
        assert payload["execution_go_token_consumed"] is True
        assert payload["scope_definition_go_token"] == SCOPE_DEFINITION_GO
        assert payload["scope_definition_go_token_consumed"] is True
        assert payload["go_token"] == EXECUTION_GO
        assert payload["go_token_consumed"] is True
        assert payload["next_required_go_token_for_execution_consumption"] == "CONSUMED"
        assert payload["next_canonical_step"] == HISTORICAL_NEXT_CANONICAL_STEP
        assert payload["current_admissible_next_scope"] == HISTORICAL_ADMISSIBLE_SCOPE
        assert payload["current_admissible_next_scope_go_token"] == RATIFICATION_GO
        assert payload["classification_execution_manifest_verify_rc"] == 0
        assert NEW_EVIDENCE_SUFFIX in payload["classification_execution_evidence_ref"]
        assert payload["failed_candidates"] == list(FAILED_CANDIDATES)
        assert payload["panel_zero_trade_refuted"] is True
        for flag in AUTHORITY_TRUE_FLAGS:
            assert payload.get(flag) is not True, f"authority flag must not be true: {flag}"

    def test_scope_config_classification_axes_present(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        axes = payload["classification_axes"]
        for axis in CLASSIFICATION_AXES:
            assert axis in axes, f"missing classification axis: {axis}"

    def test_governance_doc_has_docs_token_and_execution_verdict(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{CLASSIFICATION_CURRENT_STATE}`" in body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in body
        assert f"`EXECUTION_GO_TOKEN` | `{EXECUTION_GO}`" in body
        assert "`EXECUTION_GO_TOKEN_CONSUMED` | `true`" in body
        assert f"`SCOPE_DEFINITION_GO_TOKEN` | `{SCOPE_DEFINITION_GO}`" in body
        assert f"`PRIMARY_CLASSIFICATION` | `{PRIMARY_CLASSIFICATION}`" in body
        assert "`economic_evaluation_executed` | `false`" in body
        assert "`backtests_executed` | `false`" in body
        assert "`MANIFEST_VERIFY_RC` | `0`" in body
        assert PARENT_EVIDENCE_SUFFIX in body
        assert NEW_EVIDENCE_SUFFIX in body
        assert (
            "scripts/research/post_no_pass_sparse_signal_inconclusive_failure_classification_execution_v0.py"
            in body
        )
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body, f"missing boundary phrase: {phrase}"

    def test_classification_result_shape_in_durable_evidence(self) -> None:
        result_path = Path(
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
            f"/implementation/{NEW_EVIDENCE_SUFFIX}/CLASSIFICATION_EXECUTION_RESULT.json"
        )
        assert result_path.is_file()
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        assert payload["evidence_class"] == EVIDENCE_CLASS_ID
        assert payload["process_classification"] == PROCESS_CLASSIFICATION
        assert payload["consumed_go_token"] == EXECUTION_GO
        assert payload["primary_classification"] == PRIMARY_CLASSIFICATION
        admissibility = payload["admissibility_summary"]
        for key in RESULT_REQUIRED_KEYS:
            if key in admissibility:
                continue
            assert key in payload, f"missing result key: {key}"
        assert admissibility["economic_evaluation_executed"] is False
        assert admissibility["backtests_executed"] is False
        assert admissibility["walk_forward_executed"] is False
        assert admissibility["monte_carlo_executed"] is False
        assert admissibility["stress_executed"] is False
        assert admissibility["runtime_rewire_admissible"] is False
        assert payload["no_promotion_claim"] is True

    def test_classification_execution_does_not_authorize_runtime_or_trading(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["economic_evaluation_authorized"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["live_authorized"] is False
        assert payload["shadow_authorized"] is False
        assert payload["paper_authorized"] is False
        assert payload["testnet_authorized"] is False
        assert payload["orders_allowed"] is False
        assert payload["scheduler_runtime_allowed"] is False

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert authoritative_field_value("CURRENT_STATE") == AUTHORITATIVE_CURRENT_STATE
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == AUTHORITATIVE_NEXT_CANONICAL_STEP
        assert authoritative_field_value("NEXT_CANONICAL_ACTION") == AUTHORITATIVE_NEXT_CANONICAL_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == AUTHORITATIVE_NEXT_CANONICAL_STEP
        assert (
            authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE")
            == AUTHORITATIVE_ADMISSIBLE_SCOPE
        )
        assert (
            authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN")
            == "GO_POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_STATUS",
            )
            == EXECUTION_STATUS
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_GO_TOKEN",
            )
            == EXECUTION_GO
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_GO_TOKEN_CONSUMED",
            )
            == "true"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_REQUIRED_NEXT_GO_FOR_EXECUTION_CONSUMPTION",
            )
            == "CONSUMED"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_CLASSIFICATION_EXECUTED",
            )
            == "true"
        )
        assert NEW_EVIDENCE_SUFFIX in _field_value(
            text,
            "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_EVIDENCE_REF",
        )
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("PROMOTION_ELIGIBLE") == "false"
        for marker in FORBIDDEN_NEXT_SCOPE_MARKERS:
            assert marker not in authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE")

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == EXECUTION_STATUS
        assert _field_value(section, "VERDICT") == CLASSIFICATION_CURRENT_STATE
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "GO_TOKEN") == EXECUTION_GO
        assert _field_value(section, "GO_TOKEN_CONSUMED") == "true"
        assert _field_value(section, "SCOPE_DEFINITION_GO_TOKEN") == SCOPE_DEFINITION_GO
        assert _field_value(section, "SCOPE_DEFINITION_GO_TOKEN_CONSUMED") == "true"
        assert _field_value(section, "CLASSIFICATION_EXECUTED") == "true"
        assert _field_value(section, "economic_evaluation_executed") == "false"
        assert _field_value(section, "backtests_executed") == "false"
        assert _field_value(section, "RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == HISTORICAL_NEXT_CANONICAL_STEP
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE") == HISTORICAL_ADMISSIBLE_SCOPE
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == RATIFICATION_GO
        assert NEW_EVIDENCE_SUFFIX in _field_value(section, "NEW_EVIDENCE_DIR")

    def test_scope_definition_go_not_reconsumed_as_execution_go(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["scope_definition_go_token"] == SCOPE_DEFINITION_GO
        assert payload["execution_go_token"] == EXECUTION_GO
        assert payload["scope_definition_go_token"] != payload["execution_go_token"]
        assert payload["scope_definition_go_token_consumed"] is True
        assert payload["execution_go_token_consumed"] is True
