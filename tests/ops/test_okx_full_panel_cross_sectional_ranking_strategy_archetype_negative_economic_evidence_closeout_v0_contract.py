"""Contract tests for OKX full-panel CSR archetype negative economic evidence governance closeout v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
CLOSEOUT_CONFIG = (
    REPO_ROOT
    / "config/research/okx_full_panel_cross_sectional_ranking_strategy_archetype_negative_economic_evidence_closeout_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0.md"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_"
    "NEGATIVE_ECONOMIC_EVIDENCE_GOVERNANCE_CLOSEOUT_V0"
)
GO_TOKEN = (
    "GO_OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_"
    "NEGATIVE_ECONOMIC_EVIDENCE_GOVERNANCE_CLOSEOUT_V0"
)
VERDICT = "ROBUSTNESS_FAILED"
EVIDENCE_BUNDLE_SUFFIX = (
    "okx_full_panel_cross_sectional_ranking_strategy_archetype_"
    "bounded_offline_economic_evaluation_v0_20260705T014731Z"
)
CLOSEOUT_BUNDLE_SUFFIX = (
    "okx_full_panel_cross_sectional_ranking_strategy_archetype_"
    "bounded_offline_economic_evaluation_pr_squash_merge_closeout_v0_20260705T015740Z"
)
AUTHORITY_TRUE_FLAGS = (
    "promotion_authorized",
    "promotion_candidate_eligible",
    "runtime_authority",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "live_authorized",
    "candidate_ratified",
    "immutable_binding_retry_allowed",
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
    next_heading = tail.find("\n#### ")
    if next_heading == -1:
        next_heading = tail.find("\n---\n\n## Post-PR-4847 Verification Binding")
    return tail if next_heading == -1 else tail[:next_heading]


class TestOkxFullPanelCsrArchetypeNegativeEconomicEvidenceCloseoutV0Contract:
    def test_closeout_config_exists_and_terminal_gates(self) -> None:
        assert CLOSEOUT_CONFIG.is_file()
        payload = json.loads(CLOSEOUT_CONFIG.read_text(encoding="utf-8"))
        assert payload["verdict"] == VERDICT
        assert payload["economic_validity_offline_gate_pass"] is False
        assert payload["promotion_candidate_eligible"] is False
        assert payload["runtime_authority"] is False
        assert payload["immutable_binding_retry_allowed"] is False
        assert payload["new_evidence_class_required_for_further_evaluation"] is True
        assert payload["manifest_verify_rc"] == 0
        assert payload["authority_effect"] == "NONE"
        assert payload["runtime_effect"] == "NONE"
        assert payload["no_runtime_or_promotion_action"] is True
        assert payload["terminal_negative_evidence_for_unchanged_binding"] is True
        assert EVIDENCE_BUNDLE_SUFFIX in payload["evidence_bundle_path"]
        assert CLOSEOUT_BUNDLE_SUFFIX in payload["closeout_bundle_path"]
        for flag in AUTHORITY_TRUE_FLAGS:
            assert payload.get(flag) is not True, f"authority flag must not be true: {flag}"

    def test_governance_doc_has_docs_token_and_terminal_verdict(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_"
                "NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{VERDICT}`" in body
        assert "`economic_validity_offline_gate_pass` | `false`" in body
        assert "`promotion_candidate_eligible` | `false`" in body
        assert "`runtime_authority` | `false`" in body
        assert "`authority_effect` | `NONE`" in body
        assert "`PERIOD_BINDING_VERDICT` | `RATIFIED_BOUND_CONSISTENT`" in body
        assert (
            "NEXT_CANONICAL_STEP=NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED" in body
        )
        assert EVIDENCE_BUNDLE_SUFFIX in body
        assert CLOSEOUT_BUNDLE_SUFFIX in body

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0_STATUS",
            )
            == "NEGATIVE_ECONOMIC_EVIDENCE_GOVERNANCE_CLOSEOUT_COMPLETE"
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_NEGATIVE_ECONOMIC_EVIDENCE_CLOSEOUT_V0_GO_TOKEN",
            )
            == GO_TOKEN
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_PROMOTION_CANDIDATE_ELIGIBLE",
            )
            == "false"
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_NO_RUNTIME_OR_PROMOTION_ACTION",
            )
            == "true"
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_IMMUTABLE_BINDING_RETRY_ALLOWED",
            )
            == "false"
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_NEW_EVIDENCE_CLASS_REQUIRED_FOR_FURTHER_EVALUATION",
            )
            == "true"
        )
        assert (
            _field_value(text, "PR4852_MERGE_COMMIT") == "1a04805112a26986f3a659262b30f80005952850"
        )
        assert _field_value(text, "NEXT_CANONICAL_STEP") == (
            "NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED"
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert (
            _field_value(section, "STATUS")
            == "NEGATIVE_ECONOMIC_EVIDENCE_GOVERNANCE_CLOSEOUT_COMPLETE"
        )
        assert _field_value(section, "VERDICT") == VERDICT
        assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert _field_value(section, "PROMOTION_CANDIDATE_ELIGIBLE") == "false"
        assert _field_value(section, "RUNTIME_AUTHORITY") == "false"
        assert _field_value(section, "IMMUTABLE_BINDING_RETRY_ALLOWED") == "false"
        assert _field_value(section, "NEW_EVIDENCE_CLASS_REQUIRED_FOR_FURTHER_EVALUATION") == "true"
        assert _field_value(section, "NO_RUNTIME_OR_PROMOTION_ACTION") == "true"
        assert _field_value(section, "TERMINAL_NEGATIVE_EVIDENCE_FOR_UNCHANGED_BINDING") == "true"
        assert _field_value(section, "MANIFEST_VERIFY_RC") == "0"
        assert _field_value(section, "PERIOD_BINDING_VERDICT") == "RATIFIED_BOUND_CONSISTENT"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == (
            "NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED"
        )
        assert EVIDENCE_BUNDLE_SUFFIX in _field_value(section, "EVIDENCE_BUNDLE_PATH")
        assert CLOSEOUT_BUNDLE_SUFFIX in _field_value(section, "PR4852_CLOSEOUT_EVIDENCE_REF")
