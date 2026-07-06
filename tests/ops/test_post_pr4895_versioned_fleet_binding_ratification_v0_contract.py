"""Contract tests for post-PR4895 versioned fleet binding ratification v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.research.post_pr4895_versioned_fleet_binding_ratification_v0 import (
    BINDING_CLASS,
    CONFIRM_GO,
    FAILED_CANDIDATE_VERDICT,
    NEXT_EXECUTION_GO,
    PROCESS_CLASSIFICATION,
    REQUIRED_BINDING_FIELDS,
    STRATEGY_VERSION,
    ValidationVerdict,
    materialize_post_pr4895_versioned_fleet_binding_ratification_v0,
    validate_post_pr4895_versioned_fleet_binding_ratification_v0,
)
from src.research.post_no_pass_metric_materialization_path_activation_binding_ratification_v0 import (
    CONFIG_REL_PATH as V3_CONFIG_REL,
)
from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (
    RESEARCH_CANDIDATES,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BINDING_CONFIG = (
    REPO_ROOT / "config/research/post_pr4895_versioned_fleet_binding_ratification_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/POST_PR4895_VERSIONED_FLEET_BINDING_RATIFICATION_V0.md"
)
V3_CONFIG = REPO_ROOT / V3_CONFIG_REL
EVIDENCE_CLASS_ID = "POST_PR4895_VERSIONED_FLEET_BINDING_RATIFICATION_V0"
SCOPE_STATUS = "FLEET_BINDINGS_RATIFIED_NOT_EVALUATED"
SCOPE_CLASSIFICATION = (
    "BOUNDED_VERSIONED_FINAL_RESEARCH_FLEET_BINDING_RATIFICATION_ONLY_AFTER_PR4895_V0"
)
BASELINE_HEAD = "64509cce36ec5316cbfe4f42427cf81ecf67bdae"
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
    "no parameter rescue",
    "FAILED_BINDINGS_RETRY_ALLOWED=false",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostPr4895VersionedFleetBindingRatificationV0Contract:
    def test_binding_config_core_fields(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert payload["status"] == SCOPE_STATUS
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["binding_class"] == BINDING_CLASS
        assert payload["process_classification"] == PROCESS_CLASSIFICATION
        assert payload["scope_classification"] == SCOPE_CLASSIFICATION
        assert payload["fleet_bindings_ratified"] is True
        assert payload["all_required_bindings_complete"] is True
        assert payload["blocked_missing_bindings"] == []
        assert payload["go_token"] == CONFIRM_GO
        assert payload["baseline_head"] == BASELINE_HEAD
        assert payload["required_next_go_for_execution"] == NEXT_EXECUTION_GO
        assert payload["strategy_version"] == STRATEGY_VERSION
        assert payload["failed_candidate_verdict"] == FAILED_CANDIDATE_VERDICT
        assert payload["economic_evaluation_authorized"] is False
        assert payload["economic_evaluation_executed"] is False
        assert payload["backtest_executed"] is False
        assert payload["runtime_authority"] == "NONE"
        assert payload["failed_bindings_retry_allowed"] is False
        assert payload["same_binding_retry_allowed"] is False
        assert payload["new_candidate_ratified"] is False
        assert payload["promotion_authority"] is False

    def test_binding_config_candidates_complete(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert len(payload["candidates"]) == len(RESEARCH_CANDIDATES)
        for candidate in payload["candidates"]:
            assert candidate["strategy_version"] == STRATEGY_VERSION
            assert candidate["substantially_differs_from_v3"] is True
            assert candidate["terminal_v3_verdict"] == FAILED_CANDIDATE_VERDICT
            assert "root_cause_decomposition_binding" in candidate
            for field in REQUIRED_BINDING_FIELDS:
                assert field in candidate
                assert candidate[field] not in (None, "", {})

    def test_binding_config_forbids_runtime_and_evaluation(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        blocked = set(payload["blocked_actions"])
        for action in (
            "ECONOMIC_EVALUATION_EXECUTION",
            "BACKTEST_RERUN",
            "SAME_BINDING_RETRY",
            "FAILED_BINDING_RETRY",
            "PARAMETER_RESCUE",
            "NEAR_DUPLICATE_BREAKOUT_MEAN_REVERSION_RETRY",
        ):
            assert action in blocked

    def test_materialization_validation_accepted(self) -> None:
        v3 = json.loads(V3_CONFIG.read_text(encoding="utf-8"))
        completion = materialize_post_pr4895_versioned_fleet_binding_ratification_v0(
            repo_root=REPO_ROOT,
            v3_completion=v3,
        )
        result = validate_post_pr4895_versioned_fleet_binding_ratification_v0(
            completion,
            v3_completion=v3,
        )
        assert result.verdict == ValidationVerdict.ACCEPTED

    def test_parameters_unchanged_from_v3(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        v3 = json.loads(V3_CONFIG.read_text(encoding="utf-8"))
        v3_by_id = {c["strategy_id"]: c for c in v3["candidates"]}
        for candidate in payload["candidates"]:
            sid = candidate["strategy_id"]
            assert candidate["parameter_binding"] == v3_by_id[sid]["parameter_binding"]

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker("DOCS_TOKEN_POST_PR4895_VERSIONED_FLEET_BINDING_RATIFICATION_V0")
            in body
        )
        assert f"`OPERATOR_GO` | `{CONFIRM_GO}`" in body
        assert "`ALL_REQUIRED_BINDINGS_COMPLETE` | `true`" in body
        assert "`BLOCKED_MISSING_BINDINGS` | `none`" in body
        assert "`ECONOMIC_EVALUATION_EXECUTED` | `false`" in body
        assert "`RUNTIME_AUTHORITY` | `NONE`" in body

    def test_governance_doc_boundary_phrases(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body

    def test_governance_doc_forbidden_runtime_actions(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for action in FORBIDDEN_RUNTIME_ACTIONS:
            assert action in body

    def test_governance_doc_next_execution_go(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert _field_value(body, "REQUIRED_NEXT_GO_FOR_EXECUTION") == NEXT_EXECUTION_GO

    def test_final_research_fleet_unchanged(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert payload["final_research_fleet"] == list(RESEARCH_CANDIDATES)

    def test_authority_flags_explicitly_false(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert payload["shadow_authorized"] is False
        assert payload["paper_authorized"] is False
        assert payload["testnet_authorized"] is False
        assert payload["live_authorized"] is False
