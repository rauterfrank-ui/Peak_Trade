"""Contract tests for trend_following/v2 post-repair economic fail governance closeout v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
CLOSEOUT_CONFIG = (
    REPO_ROOT
    / "config/research/trend_following_v2_post_repair_economic_fail_governance_closeout_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/TREND_FOLLOWING_V2_POST_REPAIR_ECONOMIC_FAIL_GOVERNANCE_CLOSEOUT_V0.md"
)
CLOSEOUT_SECTION_PREFIX = "#### TREND_FOLLOWING_V2_POST_REPAIR_ECONOMIC_FAIL_GOVERNANCE_CLOSEOUT_V0"
CLOSEOUT_GO = "GO_TREND_FOLLOWING_V2_POST_REPAIR_ECONOMIC_FAIL_GOVERNANCE_CLOSEOUT_V0"
CURRENT_STATE = "TREND_FOLLOWING_V2_POST_REPAIR_ECONOMIC_FAIL_GOVERNANCE_CLOSEOUT_COMPLETE_V0"
PROCESS_CLASSIFICATION = (
    "PERSIST_TERMINAL_NEGATIVE_EVIDENCE_NO_POLICY_RESCUE_AND_CLOSE_RESEARCH_GENERATION_V0"
)
SCOPE_CLASSIFICATION = "TREND_FOLLOWING_V2_POST_REPAIR_ECONOMIC_FAIL_GOVERNANCE_CLOSEOUT_V0"
ORIGIN_MAIN = "967ba86a25170d730f0489329ef6eff708d3dd1a"
BINDING_DIGEST = "9c624a22506c905261e58c117923ea4c0f570968d54ddf5e91f2c56f88b0d966"
EVALUATION_BUNDLE_SUFFIX = (
    "trend_following_v2_post_repair_baseline_economic_reevaluation_v0_20260715T145755Z"
)
PR5219_SUFFIX = "pr5219_merge_closeout_trend_following_v2_baseline_e2e_test_runtime_bound_repair_v0_20260715T134243Z"
PR5220_IMPL_SUFFIX = (
    "trend_following_v2_mandatory_boundary_rewire_canonical_plan_freeze_v0_20260715T142233Z"
)
PR5220_CLOSEOUT_SUFFIX = "pr5220_merge_closeout_trend_following_v2_canonical_mandatory_boundary_rewire_v0_20260715T143605Z"
POST_MERGE_SUFFIX = "trend_following_v2_post_merge_full_canonical_system_chain_e2e_parity_reaudit_v0_20260715T144719Z"
REASON_CODES = (
    "METRIC_MISSING:parameter_neighbor_degradation;"
    "METRIC_MISSING:single_regime_profit_contribution;"
    "METRIC_MISSING:single_trade_profit_contribution;"
    "PROFIT_FACTOR_BELOW_THRESHOLD;"
    "TRADE_COUNT_BELOW_THRESHOLD;"
    "ZERO_TRADE_DEGENERATION"
)
AUTHORITY_TRUE_FLAGS = (
    "promotion_eligible",
    "runtime_rewire_admissible",
    "robustness_admissible",
    "runtime_authority",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "live_authorized",
    "immutable_binding_retry_allowed",
    "same_binding_retry_allowed",
    "unchanged_binding_retry_admissible",
    "policy_rescue_allowed",
    "parameter_tuning_authorized",
    "threshold_relaxation_authorized",
    "post_result_selection_authorized",
    "orders_allowed",
    "scheduler_runtime_allowed",
    "implementation_defect_classification",
    "infrastructure_retry_justification",
    "positive_or_inconclusive_research_status",
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
    next_heading = tail.find("\n---\n\n## PR #4629 Evidence-Drift")
    assert next_heading != -1, "missing closeout section boundary"
    return tail[:next_heading]


class TestTrendFollowingV2PostRepairEconomicFailGovernanceCloseoutV0Contract:
    def test_closeout_config_exists_and_terminal_gates(self) -> None:
        assert CLOSEOUT_CONFIG.is_file()
        payload = json.loads(CLOSEOUT_CONFIG.read_text(encoding="utf-8"))
        assert payload["verdict"] == CURRENT_STATE
        assert payload["status"] == "POST_REPAIR_ECONOMIC_FAIL_GOVERNANCE_CLOSEOUT_COMPLETE"
        assert payload["process_classification"] == PROCESS_CLASSIFICATION
        assert payload["scope_classification"] == SCOPE_CLASSIFICATION
        assert payload["go_token"] == CLOSEOUT_GO
        assert payload["binding"] == "trend_following/v2"
        assert payload["binding_semantic_digest"] == BINDING_DIGEST
        assert payload["terminal_verdict"] == "FAIL"
        assert payload["economic_result"] == "FAIL"
        assert payload["economic_evaluation_status"] == "COMPLETE"
        assert payload["primary_economic_failure_reason"] == "ZERO_TRADE_DEGENERATION"
        assert payload["zero_trade_classification"] == "NO_CANONICAL_MARKET_OPPORTUNITY"
        assert payload["economic_validity_offline_gate_pass"] is False
        assert payload["economic_evidence_valid"] is True
        assert payload["full_canonical_chain_verified"] is True
        assert payload["mandatory_boundary_chain_verified"] is True
        assert payload["baseline_contract_unchanged"] is True
        assert payload["robustness_admissible"] is False
        assert payload["robustness_not_started"] is True
        assert payload["no_automatic_robustness"] is True
        assert payload["no_unchanged_binding_retry"] is True
        assert payload["no_parameter_optimization"] is True
        assert payload["no_threshold_relaxation"] is True
        assert payload["no_policy_rescue"] is True
        assert payload["no_post_result_selection"] is True
        assert payload["no_runtime_rewire"] is True
        assert payload["no_promotion"] is True
        assert payload["inconclusive_reclassification_blocked"] is True
        assert payload["terminal_negative_evidence_for_unchanged_binding"] is True
        assert payload["historical_negative_evidence_mutated"] is False
        assert payload["manifest_verify_rc"] == 0
        assert payload["source_manifest_verify_rc"] == 0
        assert payload["baseline_head"] == ORIGIN_MAIN
        assert payload["repair_pr"] == 5220
        assert payload["post_merge_full_chain_revalidation_result"] == "PASS"
        assert payload["next_admissible_scope"] == "NONE_WITHOUT_NEW_OPERATOR_RATIFICATION"
        assert EVALUATION_BUNDLE_SUFFIX in payload["source_economic_evidence_path"]
        assert PR5219_SUFFIX in payload["source_pr5219_closeout_path"]
        assert PR5220_IMPL_SUFFIX in payload["source_pr5220_implementation_path"]
        assert PR5220_CLOSEOUT_SUFFIX in payload["source_pr5220_closeout_path"]
        assert POST_MERGE_SUFFIX in payload["source_post_merge_full_chain_reaudit_path"]
        assert payload["metrics"]["trade_count"] == 0
        assert payload["reason_codes"] == REASON_CODES.split(";")
        for flag in AUTHORITY_TRUE_FLAGS:
            assert payload.get(flag) is not True, f"authority flag must not be true: {flag}"

    def test_governance_doc_has_docs_token_and_terminal_verdict(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_TREND_FOLLOWING_V2_POST_REPAIR_ECONOMIC_FAIL_GOVERNANCE_CLOSEOUT_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{CURRENT_STATE}`" in body
        assert "trend_following&#47;v2" in body
        assert f"`STRATEGY_BINDING_DIGEST` | `{BINDING_DIGEST}`" in body
        assert "`ECONOMIC_RESULT` | `FAIL`" in body
        assert "`PRIMARY_ECONOMIC_FAILURE_REASON` | `ZERO_TRADE_DEGENERATION`" in body
        assert "`ZERO_TRADE_CLASSIFICATION` | `NO_CANONICAL_MARKET_OPPORTUNITY`" in body
        assert "`TRADE_COUNT` | `0`" in body
        assert "`ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` | `false`" in body
        assert "`PROMOTION_ELIGIBLE` | false" in body
        assert "`RUNTIME_REWIRE_ADMISSIBLE` | false" in body
        assert "`ROBUSTNESS_ADMISSIBLE` | false" in body
        assert "`INCONCLUSIVE_RECLASSIFICATION_BLOCKED` | `true`" in body
        assert "`IMPLEMENTATION_DEFECT_CLASSIFICATION` | `false`" in body
        assert "`CURRENT_PHASE` | `TERMINAL_ECONOMIC_FAIL_CLOSEOUT`" in body
        assert "`NEXT_ADMISSIBLE_SCOPE` | `NONE_WITHOUT_NEW_OPERATOR_RATIFICATION`" in body
        assert EVALUATION_BUNDLE_SUFFIX in body

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "TREND_FOLLOWING_V2_POST_REPAIR_ECONOMIC_FAIL_GOVERNANCE_CLOSEOUT_V0_STATUS",
            )
            == "POST_REPAIR_ECONOMIC_FAIL_GOVERNANCE_CLOSEOUT_COMPLETE"
        )
        assert (
            _field_value(
                text,
                "TREND_FOLLOWING_V2_POST_REPAIR_ECONOMIC_FAIL_GOVERNANCE_CLOSEOUT_V0_GO_TOKEN",
            )
            == CLOSEOUT_GO
        )
        assert (
            _field_value(
                text,
                "TREND_FOLLOWING_V2_POST_REPAIR_ECONOMIC_FAIL_GOVERNANCE_CLOSEOUT_V0_CONFIG_REF",
            )
            == "config/research/trend_following_v2_post_repair_economic_fail_governance_closeout_v0.json"
        )
        assert _field_value(text, "TREND_FOLLOWING_V2_ECONOMIC_EVALUATION_STATUS") == "COMPLETE"
        assert _field_value(text, "TREND_FOLLOWING_V2_HISTORICAL_ECONOMIC_RESULT") == "FAIL"
        assert (
            _field_value(text, "TREND_FOLLOWING_V2_ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        )
        assert (
            _field_value(text, "TREND_FOLLOWING_V2_PRIMARY_ECONOMIC_FAILURE_REASON")
            == "ZERO_TRADE_DEGENERATION"
        )
        assert (
            _field_value(text, "TREND_FOLLOWING_V2_ZERO_TRADE_CLASSIFICATION")
            == "NO_CANONICAL_MARKET_OPPORTUNITY"
        )
        assert _field_value(text, "TREND_FOLLOWING_V2_TRADE_COUNT") == "0"
        assert _field_value(text, "TREND_FOLLOWING_V2_PROMOTION_ELIGIBLE") == "false"
        assert _field_value(text, "TREND_FOLLOWING_V2_ROBUSTNESS_ADMISSIBLE") == "false"
        assert _field_value(text, "TREND_FOLLOWING_V2_RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert (
            _field_value(text, "TREND_FOLLOWING_V2_UNCHANGED_BINDING_RETRY_ADMISSIBLE") == "false"
        )
        assert _field_value(text, "TREND_FOLLOWING_V2_MANDATORY_BOUNDARY_REPAIR_COMPLETE") == "true"
        assert (
            _field_value(text, "TREND_FOLLOWING_V2_POST_MERGE_FULL_CHAIN_REVALIDATION_RESULT")
            == "PASS"
        )
        assert (
            _field_value(text, "TREND_FOLLOWING_V2_NEXT_ADMISSIBLE_SCOPE")
            == "NONE_WITHOUT_NEW_OPERATOR_RATIFICATION"
        )
        assert EVALUATION_BUNDLE_SUFFIX in _field_value(
            text, "TREND_FOLLOWING_V2_POST_REPAIR_BASELINE_ECONOMIC_REEVALUATION_EVIDENCE_REF"
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert (
            _field_value(section, "STATUS")
            == "POST_REPAIR_ECONOMIC_FAIL_GOVERNANCE_CLOSEOUT_COMPLETE"
        )
        assert _field_value(section, "VERDICT") == CURRENT_STATE
        assert _field_value(section, "PROCESS_CLASSIFICATION") == PROCESS_CLASSIFICATION
        assert _field_value(section, "GO_TOKEN") == CLOSEOUT_GO
        assert "trend_following&#47;v2" in _field_value(section, "BINDING")
        assert _field_value(section, "HISTORICAL_ECONOMIC_RESULT") == "FAIL"
        assert _field_value(section, "ECONOMIC_EVALUATION_STATUS") == "COMPLETE"
        assert _field_value(section, "PRIMARY_ECONOMIC_FAILURE_REASON") == "ZERO_TRADE_DEGENERATION"
        assert (
            _field_value(section, "ZERO_TRADE_CLASSIFICATION") == "NO_CANONICAL_MARKET_OPPORTUNITY"
        )
        assert _field_value(section, "INCONCLUSIVE_RECLASSIFICATION_BLOCKED") == "true"
        assert _field_value(section, "TRADE_COUNT") == "0"
        assert _field_value(section, "ROBUSTNESS_ADMISSIBLE") == "false"
        assert _field_value(section, "PROMOTION_ELIGIBLE") == "false"
        assert _field_value(section, "RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(section, "UNCHANGED_BINDING_RETRY_ADMISSIBLE") == "false"
        assert _field_value(section, "POLICY_RESCUE_ALLOWED") == "false"
        assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert _field_value(section, "MANIFEST_VERIFY_RC") == "0"
        assert _field_value(section, "REASON_CODES") == REASON_CODES
        assert EVALUATION_BUNDLE_SUFFIX in _field_value(
            section, "POST_REPAIR_BASELINE_ECONOMIC_REEVALUATION_EVIDENCE_REF"
        )
        assert (
            _field_value(section, "NEXT_ADMISSIBLE_SCOPE")
            == "NONE_WITHOUT_NEW_OPERATOR_RATIFICATION"
        )


class TestZeroTradeTerminalClassificationBound:
    def test_zero_trade_degeneration_does_not_map_to_pass(self) -> None:
        payload = json.loads(CLOSEOUT_CONFIG.read_text(encoding="utf-8"))
        assert payload["primary_economic_failure_reason"] == "ZERO_TRADE_DEGENERATION"
        assert payload["economic_result"] == "FAIL"
        assert payload["terminal_verdict"] == "FAIL"
        assert payload["economic_validity_offline_gate_pass"] is False
        assert payload["promotion_eligible"] is False

    def test_no_canonical_market_opportunity_not_inconclusive(self) -> None:
        payload = json.loads(CLOSEOUT_CONFIG.read_text(encoding="utf-8"))
        assert payload["zero_trade_classification"] == "NO_CANONICAL_MARKET_OPPORTUNITY"
        assert payload["inconclusive_reclassification_blocked"] is True
        assert payload["economic_result"] != "INCONCLUSIVE"
        assert payload["economic_evaluation_status"] == "COMPLETE"

    def test_zero_trade_count_does_not_enable_robustness(self) -> None:
        payload = json.loads(CLOSEOUT_CONFIG.read_text(encoding="utf-8"))
        assert payload["metrics"]["trade_count"] == 0
        assert payload["robustness_admissible"] is False
        assert payload["robustness_not_started"] is True
        assert payload["no_automatic_robustness"] is True

    def test_economic_fail_blocks_promotion_and_runtime_rewire(self) -> None:
        text = read_registry()
        assert _field_value(text, "TREND_FOLLOWING_V2_PROMOTION_ELIGIBLE") == "false"
        assert _field_value(text, "TREND_FOLLOWING_V2_RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert (
            _field_value(text, "TREND_FOLLOWING_V2_UNCHANGED_BINDING_RETRY_ADMISSIBLE") == "false"
        )

    def test_unchanged_contract_blocks_retry(self) -> None:
        payload = json.loads(CLOSEOUT_CONFIG.read_text(encoding="utf-8"))
        assert payload["baseline_contract_unchanged"] is True
        assert payload["no_unchanged_binding_retry"] is True
        assert payload["unchanged_binding_retry_admissible"] is False
        assert payload["same_binding_retry_allowed"] is False

    def test_source_evidence_manifest_required(self) -> None:
        payload = json.loads(CLOSEOUT_CONFIG.read_text(encoding="utf-8"))
        assert payload["source_manifest_verify_rc"] == 0
        assert payload["manifest_verify_rc"] == 0
        assert payload["economic_evidence_valid"] is True
