"""Contract tests for post-no-pass sparse signal zero trade versioned binding ratification v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (
    BINDING_CLASS,
    CLASS_D_COMPLETION_REL_PATH,
    CONFIG_REL_PATH,
    CONFIRM_GO,
    NEXT_EXECUTION_GO,
    REQUIRED_BINDING_FIELDS,
    STRATEGY_VERSION,
    ValidationVerdict,
    materialize_post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0,
    validate_post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BINDING_CONFIG = REPO_ROOT / CONFIG_REL_PATH
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0.md"
)
CLASS_D_CONFIG = REPO_ROOT / CLASS_D_COMPLETION_REL_PATH
CLOSEOUT_SECTION_PREFIX = (
    "#### POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0"
)
EVIDENCE_CLASS_ID = "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0"
SCOPE_STATUS = "BINDING_RATIFICATION_COMPLETE_NOT_EXECUTED"
BINDING_RATIFICATION_STATUS = "BINDING_RATIFICATION_COMPLETE_NOT_EXECUTED"
PROCESS_CLASSIFICATION = "VERSIONED_BINDING_RATIFICATION_ONLY_V0"
CURRENT_STATE = "POST_PR4883_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_COMPLETE_V0"
NEXT_CANONICAL_STEP = "REQUEST_OPERATOR_GO_FOR_POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
CURRENT_ADMISSIBLE_SCOPE = (
    "POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_CLASS_V0"
)
ADMISSIBLE_EXECUTION_GO = (
    "GO_POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
)
BASELINE_HEAD = "a113c6bb667fc38da160637e47f018a5411365a3"
EVIDENCE_SUFFIX = (
    "post_no_pass_sparse_signal_zero_trade_versioned_binding_ratification_v0_20260705T210521Z"
)
RESEARCH_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
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
    "Binding-Ratifikation ≠ Evaluation-Autorisierung",
    "Keine Economic Evaluation",
    "ROBUSTNESS_FAILED",
    "panel-sequential signal-density",
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
        "\n#### POST_NO_PASS_ROBUSTNESS_FAILURE_NEXT_RESEARCH_SCOPE_DEFINITION_V0"
    )
    return tail if next_heading == -1 else tail[:next_heading]


class TestPostNoPassSparseSignalZeroTradeVersionedBindingRatificationV0Contract:
    def test_binding_config_exists_and_governance_gates(self) -> None:
        assert BINDING_CONFIG.is_file()
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert payload["status"] == SCOPE_STATUS
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["binding_class"] == BINDING_CLASS
        assert payload["process_classification"] == PROCESS_CLASSIFICATION
        assert payload["authority_effect"] == "NONE"
        assert payload["runtime_effect"] == "NONE"
        assert payload["trading_effect"] == "NONE"
        assert payload["economic_evaluation_authorized"] is False
        assert payload["economic_evaluation_executed"] is False
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
        assert payload["baseline_pr"] == "4879"
        assert payload["go_token"] == CONFIRM_GO
        assert payload["go_token_consumed"] is True
        assert payload["strategy_version"] == STRATEGY_VERSION
        assert payload["terminal_negative_evidence_unchanged"] is True

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
            assert candidate["terminal_class_d_v1_verdict"] == "ROBUSTNESS_FAILED"
            assert candidate["substantially_differs_from_class_d_v1"] is True
            assert candidate["parameter_binding"]["parameter_rescue_forbidden"] is True
            assert candidate["parameter_binding"]["unchanged_from_terminal_class_d_v1"] is True
            assert (
                candidate["instrument_binding"]["binding_mode"]
                == "panel_sequential_signal_density_research_v0"
            )
            assert (
                candidate["period_binding"]["period_binding_id"]
                == "extended_chronological_sparse_signal_research_v0"
            )

    def test_binding_config_validates_against_materializer(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        class_d = json.loads(CLASS_D_CONFIG.read_text(encoding="utf-8"))
        validation = validate_post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0(
            payload,
            class_d_completion=class_d,
        )
        assert validation.verdict == ValidationVerdict.ACCEPTED, validation.fail_reasons
        rematerialized = (
            materialize_post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0(
                repo_root=REPO_ROOT,
                class_d_completion=class_d,
            )
        )
        assert rematerialized["completion_digest"] == payload["completion_digest"]

    def test_no_same_binding_retry_against_class_d_v1(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        class_d = json.loads(CLASS_D_CONFIG.read_text(encoding="utf-8"))
        for strategy_id in RESEARCH_CANDIDATES:
            class_d_candidate = next(
                item for item in class_d["candidates"] if item["strategy_id"] == strategy_id
            )
            sparse_candidate = next(
                item for item in payload["candidates"] if item["strategy_id"] == strategy_id
            )
            assert class_d_candidate["strategy_version"] == "v1"
            assert sparse_candidate["strategy_version"] == "v2"
            assert (
                sparse_candidate["binding_semantic_digest"]
                != class_d_candidate["binding_semantic_digest"]
            )

    def test_governance_doc_has_docs_token_and_boundary_phrases(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{BINDING_RATIFICATION_STATUS}`" in body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in body
        assert f"`OPERATOR_GO` | `{CONFIRM_GO}`" in body
        assert "`GO_TOKEN_CONSUMED` | `true`" in body
        assert "`ECONOMIC_EVALUATION_AUTHORIZED` | `false`" in body
        assert f"`REQUIRED_NEXT_GO_FOR_EXECUTION` | `{NEXT_EXECUTION_GO}`" in body
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body, f"missing boundary phrase: {phrase}"

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0_STATUS",
            )
            == SCOPE_STATUS
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0_CONFIG_REF",
            )
            == CONFIG_REL_PATH
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0_GO_TOKEN",
            )
            == CONFIRM_GO
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0_GO_TOKEN_CONSUMED",
            )
            == "true"
        )
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert EVIDENCE_SUFFIX in _field_value(
            text,
            "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0_EVIDENCE_REF",
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == BINDING_RATIFICATION_STATUS
        assert _field_value(section, "VERDICT") == BINDING_RATIFICATION_STATUS
        assert _field_value(section, "PROCESS_CLASSIFICATION") == PROCESS_CLASSIFICATION
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "GO_TOKEN") == CONFIRM_GO
        assert _field_value(section, "GO_TOKEN_CONSUMED") == "true"
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "SAME_BINDING_RETRY_ALLOWED") == "false"
        assert _field_value(section, "PARAMETER_RESCUE_ALLOWED") == "false"
        assert _field_value(section, "THRESHOLD_LOWERING_ALLOWED") == "false"
        assert _field_value(section, "REQUIRED_NEXT_GO_FOR_EXECUTION") == NEXT_EXECUTION_GO
        assert _field_value(section, "NEXT_CANONICAL_STEP") == (
            "REQUEST_OPERATOR_GO_FOR_POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
        )
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE") == (
            "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
        )
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == NEXT_EXECUTION_GO
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "TRADING_EFFECT") == "NONE"
        assert _field_value(section, "FUTURES_ONLY") == "true"
        assert _field_value(section, "BITCOIN_DIRECTION_ALLOWED") == "false"
