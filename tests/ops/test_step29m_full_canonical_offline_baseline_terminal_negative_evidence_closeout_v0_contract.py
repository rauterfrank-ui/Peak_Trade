"""Contract tests for STEP29M full canonical offline baseline terminal negative evidence closeout v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
CLOSEOUT_CONFIG = (
    REPO_ROOT
    / "config/research/step29m_full_canonical_offline_baseline_terminal_negative_evidence_closeout_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/STEP29M_FULL_CANONICAL_OFFLINE_BASELINE_TERMINAL_NEGATIVE_EVIDENCE_CLOSEOUT_V0.md"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### STEP29M_FULL_CANONICAL_OFFLINE_BASELINE_TERMINAL_NEGATIVE_EVIDENCE_CLOSEOUT_V0"
)
GO_TOKEN = "GO_STEP29M_FULL_CANONICAL_OFFLINE_BASELINE_TERMINAL_NEGATIVE_EVIDENCE_CLOSEOUT_V0"
CURRENT_STATE = (
    "STEP29M_FULL_CANONICAL_OFFLINE_BASELINE_TERMINAL_NEGATIVE_EVIDENCE_CLOSEOUT_COMPLETE_V0"
)
PROCESS_CLASSIFICATION = (
    "PERSIST_TERMINAL_NEGATIVE_EVIDENCE_NO_POLICY_RESCUE_AND_CLOSE_RESEARCH_GENERATION_V0"
)
SCOPE_CLASSIFICATION = (
    "STEP29M_FULL_CANONICAL_OFFLINE_BASELINE_TERMINAL_NEGATIVE_EVIDENCE_CLOSEOUT_V0"
)
ORIGIN_MAIN = "71532a60a399e6394fee317abc1b3a8ab361215a"
FLEET_EXEC_SUFFIX = "bounded_offline_economic_evaluation_final_research_fleet_v0_20260710T055955Z"
ADJUDICATION_SUFFIX = (
    "step29m_full_canonical_system_offline_baseline_economic_evaluation_v0_20260710T060508Z"
)
CANDIDATE_VERDICTS = {
    "trend_following": "FAIL",
    "bollinger_bands": "FAIL",
    "momentum_1h": "FAIL",
}
AUTHORITY_TRUE_FLAGS = (
    "promotion_eligible",
    "runtime_rewire_admissible",
    "runtime_authority",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "live_authorized",
    "immutable_binding_retry_allowed",
    "same_binding_retry_allowed",
    "policy_rescue_allowed",
    "orders_allowed",
    "scheduler_runtime_allowed",
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
    next_heading = tail.find("\n---\n\n## Post-PR-4847 Verification Binding")
    assert next_heading != -1, "missing closeout section boundary"
    return tail[:next_heading]


class TestStep29mFullCanonicalOfflineBaselineTerminalNegativeEvidenceCloseoutV0Contract:
    def test_closeout_config_exists_and_terminal_gates(self) -> None:
        assert CLOSEOUT_CONFIG.is_file()
        payload = json.loads(CLOSEOUT_CONFIG.read_text(encoding="utf-8"))
        assert payload["verdict"] == CURRENT_STATE
        assert payload["status"] == "TERMINAL_NEGATIVE_EVIDENCE_CLOSEOUT_COMPLETE"
        assert payload["process_classification"] == PROCESS_CLASSIFICATION
        assert payload["scope_classification"] == SCOPE_CLASSIFICATION
        assert payload["go_token"] == GO_TOKEN
        assert payload["fleet_verdict"] == "FAIL_TERMINAL_NEGATIVE_BASELINE_EVIDENCE"
        assert payload["pass_count"] == 0
        assert payload["fail_count"] == 3
        assert payload["inconclusive_count"] == 0
        assert payload["candidate_results"] == CANDIDATE_VERDICTS
        assert payload["failed_bindings_are_negative_evidence"] is True
        assert payload["failed_bindings_may_not_be_retried_unchanged"] is True
        assert payload["current_research_generation_closed"] is True
        assert payload["economic_validity_offline_gate_pass"] is False
        assert payload["policy_rescue_allowed"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["terminal_negative_evidence_for_unchanged_binding"] is True
        assert payload["historical_negative_evidence_mutated"] is False
        assert payload["manifest_verify_rc"] == 0
        assert payload["baseline_head"] == ORIGIN_MAIN
        assert FLEET_EXEC_SUFFIX in payload["fleet_execution_evidence_path"]
        assert ADJUDICATION_SUFFIX in payload["fleet_adjudication_evidence_path"]
        registry = payload["terminal_negative_binding_registry"]
        assert set(registry) == {
            "trend_following/v1",
            "bollinger_bands/v1",
            "momentum_1h/v1",
        }
        assert (
            registry["bollinger_bands/v1"]["zero_trade_classification"]
            == "SPARSE_SIGNAL_ENTRY_THRESHOLD_NOT_MET"
        )
        for flag in AUTHORITY_TRUE_FLAGS:
            assert payload.get(flag) is not True, f"authority flag must not be true: {flag}"

    def test_governance_doc_has_docs_token_and_terminal_verdict(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_STEP29M_FULL_CANONICAL_OFFLINE_BASELINE_TERMINAL_NEGATIVE_EVIDENCE_CLOSEOUT_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{CURRENT_STATE}`" in body
        assert "`PASS_COUNT` | `0`" in body
        assert "`FAIL_COUNT` | `3`" in body
        assert "`FAILED_BINDINGS_ARE_NEGATIVE_EVIDENCE` | `true`" in body
        assert "`CURRENT_RESEARCH_GENERATION_CLOSED` | `true`" in body
        assert "`POLICY_RESCUE_ALLOWED` | `false`" in body
        assert "`COST_MODEL_BOUND` | `true`" in body
        assert "`SEPARATE_NUMERIC_FEE_SLIPPAGE_FUNDING_DECOMPOSITION_AVAILABLE` | `false`" in body
        assert (
            "NEXT_CANONICAL_STEP=NEW_DISTINCT_RESEARCH_GENERATION_HYPOTHESIS_AND_CANDIDATE_RANKING_READ_ONLY_V0"
            in body
        )
        assert FLEET_EXEC_SUFFIX in body
        assert ADJUDICATION_SUFFIX in body

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "STEP29M_FULL_CANONICAL_OFFLINE_BASELINE_TERMINAL_NEGATIVE_EVIDENCE_CLOSEOUT_V0_STATUS",
            )
            == "TERMINAL_NEGATIVE_EVIDENCE_CLOSEOUT_COMPLETE"
        )
        assert (
            _field_value(
                text,
                "STEP29M_FULL_CANONICAL_OFFLINE_BASELINE_TERMINAL_NEGATIVE_EVIDENCE_CLOSEOUT_V0_GO_TOKEN",
            )
            == GO_TOKEN
        )
        assert (
            _field_value(
                text,
                "STEP29M_FULL_CANONICAL_OFFLINE_BASELINE_TERMINAL_NEGATIVE_EVIDENCE_CLOSEOUT_V0_CONFIG_REF",
            )
            == "config/research/step29m_full_canonical_offline_baseline_terminal_negative_evidence_closeout_v0.json"
        )
        assert (
            _field_value(
                text,
                "STEP29M_FULL_CANONICAL_OFFLINE_BASELINE_CURRENT_RESEARCH_GENERATION_CLOSED",
            )
            == "true"
        )
        assert (
            _field_value(
                text,
                "STEP29M_FULL_CANONICAL_OFFLINE_BASELINE_FAILED_BINDINGS_REGISTERED",
            )
            == "true"
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "TERMINAL_NEGATIVE_EVIDENCE_CLOSEOUT_COMPLETE"
        assert _field_value(section, "VERDICT") == CURRENT_STATE
        assert _field_value(section, "PROCESS_CLASSIFICATION") == PROCESS_CLASSIFICATION
        assert _field_value(section, "GO_TOKEN") == GO_TOKEN
        assert _field_value(section, "PASS_COUNT") == "0"
        assert _field_value(section, "FAIL_COUNT") == "3"
        assert _field_value(section, "FAILED_BINDINGS_ARE_NEGATIVE_EVIDENCE") == "true"
        assert _field_value(section, "CURRENT_RESEARCH_GENERATION_CLOSED") == "true"
        assert _field_value(section, "POLICY_RESCUE_ALLOWED") == "false"
        assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert _field_value(section, "RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(section, "MANIFEST_VERIFY_RC") == "0"
        assert FLEET_EXEC_SUFFIX in _field_value(section, "FLEET_EXECUTION_EVIDENCE_REF")
        assert ADJUDICATION_SUFFIX in _field_value(section, "ADJUDICATION_EVIDENCE_REF")
