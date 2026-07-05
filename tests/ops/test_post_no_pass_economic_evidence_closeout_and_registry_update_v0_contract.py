"""Contract tests for post-no-pass economic evidence closeout and registry update v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLOSEOUT_CONFIG = (
    REPO_ROOT / "config/research/post_no_pass_economic_evidence_closeout_and_registry_update_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_AND_REGISTRY_UPDATE_V0.md"
)
CLOSEOUT_SECTION_PREFIX = "#### POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_AND_REGISTRY_UPDATE_V0"
GO_TOKEN = "GO_POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_AND_REGISTRY_UPDATE_V0"
PROCESS_CLASSIFICATION = (
    "BOUNDED_POST_NO_PASS_FUTURES_OFFLINE_ECONOMIC_EVALUATION_EVIDENCE_CLOSEOUT_AND_REGISTRY_UPDATE_V0"
)
SCOPE_CLASSIFICATION = "POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_AND_REGISTRY_UPDATE_V0"
CURRENT_STATE = "POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_COMPLETE_V0"
NEXT_CANONICAL_STEP = "NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED"
FLEET_VERDICT = "ROBUSTNESS_FAILED"
ORIGIN_MAIN = "a394c7debe41c3ca07773aa97425422d008e714f"
EVIDENCE_BUNDLE_SUFFIX = (
    "bounded_post_no_pass_futures_offline_economic_evaluation_execution_v0_20260705T192520Z"
)
CANDIDATE_VERDICTS = {
    "trend_following": "ROBUSTNESS_FAILED",
    "bollinger_bands": "ROBUSTNESS_FAILED",
    "momentum_1h": "ROBUSTNESS_FAILED",
}
AUTHORITY_TRUE_FLAGS = (
    "promotion_eligible",
    "runtime_rewire_admissible",
    "runtime_authority",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "canary_authorized",
    "live_authorized",
    "shadow_candidate_eligible",
    "paper_candidate_eligible",
    "testnet_candidate_eligible",
    "economic_evaluation_authorization",
    "immutable_binding_retry_allowed",
    "same_binding_retry_allowed",
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
    return tail if next_heading == -1 else tail[:next_heading]


class TestPostNoPassEconomicEvidenceCloseoutAndRegistryUpdateV0Contract:
    def test_closeout_config_exists_and_terminal_gates(self) -> None:
        assert CLOSEOUT_CONFIG.is_file()
        payload = json.loads(CLOSEOUT_CONFIG.read_text(encoding="utf-8"))
        assert payload["verdict"] == CURRENT_STATE
        assert payload["status"] == "POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_COMPLETE"
        assert payload["process_classification"] == PROCESS_CLASSIFICATION
        assert payload["scope_classification"] == SCOPE_CLASSIFICATION
        assert payload["go_token"] == GO_TOKEN
        assert payload["fleet_verdict"] == FLEET_VERDICT
        assert payload["pass_count"] == 0
        assert payload["fail_count"] == 3
        assert payload["inconclusive_count"] == 0
        assert payload["candidate_verdicts"] == CANDIDATE_VERDICTS
        assert payload["economic_validity_offline_gate_pass"] is False
        assert payload["promotion_eligible"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["immutable_binding_retry_allowed"] is False
        assert payload["same_binding_retry_allowed"] is False
        assert payload["new_evidence_class_required_for_further_evaluation"] is True
        assert payload["manifest_verify_rc"] == 0
        assert payload["authority_effect"] == "NONE"
        assert payload["runtime_effect"] == "NONE"
        assert payload["trading_effect"] == "NONE"
        assert payload["no_runtime_or_promotion_action"] is True
        assert payload["terminal_negative_evidence_for_unchanged_binding"] is True
        assert payload["historical_negative_evidence_mutated"] is False
        assert payload["next_canonical_step"] == NEXT_CANONICAL_STEP
        assert payload["pr4875_merge_commit"] == ORIGIN_MAIN
        assert EVIDENCE_BUNDLE_SUFFIX in payload["evidence_bundle_path"]
        for flag in AUTHORITY_TRUE_FLAGS:
            assert payload.get(flag) is not True, f"authority flag must not be true: {flag}"

    def test_governance_doc_has_docs_token_and_terminal_verdict(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker("DOCS_TOKEN_POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_AND_REGISTRY_UPDATE_V0")
            in body
        )
        assert f"`VERDICT` | `{CURRENT_STATE}`" in body
        assert f"`FLEET_VERDICT` | `{FLEET_VERDICT}`" in body
        assert "`PASS_COUNT` | `0`" in body
        assert "`FAIL_COUNT` | `3`" in body
        assert "`INCONCLUSIVE_COUNT` | `0`" in body
        assert "`ECONOMIC_VALIDITY_OFFLINE_GATE_PASS` | `false`" in body
        assert "`PROMOTION_ELIGIBLE` | `false`" in body
        assert "`RUNTIME_REWIRE_ADMISSIBLE` | `false`" in body
        assert "`ECONOMIC_EVALUATION_AUTHORIZED` | `false`" in body
        assert "`AUTHORITY_EFFECT` | `NONE`" in body
        assert "`RUNTIME_EFFECT` | `NONE`" in body
        assert "`TRADING_EFFECT` | `NONE`" in body
        for candidate, verdict in CANDIDATE_VERDICTS.items():
            assert f"`{candidate}` | `{verdict}`" in body
        assert (
            "NEXT_CANONICAL_STEP=NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED" in body
        )
        assert "NEW_EVALUATION_WITHOUT_OPERATOR_GO=FORBIDDEN" in body
        assert EVIDENCE_BUNDLE_SUFFIX in body

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert authoritative_field_value("CURRENT_STATE") == CURRENT_STATE
        assert authoritative_field_value("LAST_VERIFIED_ORIGIN_MAIN") == ORIGIN_MAIN
        assert authoritative_field_value("LAST_VERIFIED_PR") == "4875"
        assert authoritative_field_value("LAST_VERIFIED_SOURCE") == SCOPE_CLASSIFICATION
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert authoritative_field_value("NEXT_CANONICAL_ACTION") == NEXT_CANONICAL_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == NEXT_CANONICAL_STEP
        assert (
            _field_value(
                text,
                "POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_AND_REGISTRY_UPDATE_V0_STATUS",
            )
            == "POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_COMPLETE"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_AND_REGISTRY_UPDATE_V0_GO_TOKEN",
            )
            == GO_TOKEN
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_AND_REGISTRY_UPDATE_V0_GO_TOKEN_CONSUMED",
            )
            == "true"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_AND_REGISTRY_UPDATE_V0_GOVERNANCE_REF",
            )
            == "docs/governance/POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_AND_REGISTRY_UPDATE_V0.md"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_AND_REGISTRY_UPDATE_V0_CONFIG_REF",
            )
            == "config/research/post_no_pass_economic_evidence_closeout_and_registry_update_v0.json"
        )
        assert _field_value(text, "PR4875_MERGE_COMMIT") == ORIGIN_MAIN
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("PROMOTION_ELIGIBLE") == "false"

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_COMPLETE"
        assert _field_value(section, "VERDICT") == CURRENT_STATE
        assert _field_value(section, "PROCESS_CLASSIFICATION") == PROCESS_CLASSIFICATION
        assert _field_value(section, "SCOPE_CLASSIFICATION") == SCOPE_CLASSIFICATION
        assert _field_value(section, "GO_TOKEN") == GO_TOKEN
        assert _field_value(section, "FLEET_VERDICT") == FLEET_VERDICT
        assert _field_value(section, "PASS_COUNT") == "0"
        assert _field_value(section, "FAIL_COUNT") == "3"
        assert _field_value(section, "INCONCLUSIVE_COUNT") == "0"
        for candidate, verdict in CANDIDATE_VERDICTS.items():
            assert _field_value(section, candidate.upper()) == verdict
        assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert _field_value(section, "PROMOTION_ELIGIBLE") == "false"
        assert _field_value(section, "RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(section, "SHADOW_CANDIDATE_ELIGIBLE") == "false"
        assert _field_value(section, "PAPER_CANDIDATE_ELIGIBLE") == "false"
        assert _field_value(section, "TESTNET_CANDIDATE_ELIGIBLE") == "false"
        assert _field_value(section, "CANARY_CANDIDATE_ELIGIBLE") == "false"
        assert _field_value(section, "LIVE_CANDIDATE_ELIGIBLE") == "false"
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "IMMUTABLE_BINDING_RETRY_ALLOWED") == "false"
        assert _field_value(section, "SAME_BINDING_RETRY_ALLOWED") == "false"
        assert _field_value(section, "NEW_EVIDENCE_CLASS_REQUIRED_FOR_FURTHER_EVALUATION") == "true"
        assert _field_value(section, "HISTORICAL_NEGATIVE_EVIDENCE_MUTATED") == "false"
        assert _field_value(section, "NO_RUNTIME_OR_PROMOTION_ACTION") == "true"
        assert _field_value(section, "MANIFEST_VERIFY_RC") == "0"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "TRADING_EFFECT") == "NONE"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert EVIDENCE_BUNDLE_SUFFIX in _field_value(section, "DURABLE_EVIDENCE_REF")
