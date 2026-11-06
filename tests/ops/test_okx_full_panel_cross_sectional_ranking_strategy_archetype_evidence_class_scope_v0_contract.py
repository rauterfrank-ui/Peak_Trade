"""Contract tests for OKX full-panel cross-sectional ranking evidence class scope v0."""

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
    / "config/research/okx_full_panel_cross_sectional_ranking_strategy_archetype_evidence_class_scope_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVIDENCE_CLASS_SCOPE_V0.md"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVIDENCE_CLASS_SCOPE_V0"
)
EVIDENCE_CLASS_ID = "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_V0"
SCOPE_STATUS = "NEW_EVIDENCE_CLASS_SCOPE_DEFINED"
FAILED_STEP31F_DIGEST = "161d834e5153df78a0013b6e55c4c8bd4788c775811e3678f025104a307d78f1"
FAILED_FLEET_BINDING_DIGEST = "c5e3b5fe6b688b49dbd2b210fd63bdea79201d64820591f87091b4e20689a9dd"
FAILED_FLEET_SCOPE_DIGEST = "64da0eae56a70ad0661398db14d712f6d58d6ea9f6ad0dbb73f3de2b01d11d67"
EXCLUDED_CANDIDATES = ("trend_following/v1", "bollinger_bands/v1", "momentum_1h/v1")


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


class TestOkxFullPanelCrossSectionalRankingStrategyArchetypeEvidenceClassScopeV0Contract:
    def test_scope_config_identity_and_authority_gates(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["scope_defined"] is True
        assert payload["new_evidence_class_ratified_for_scope_definition"] is True
        assert payload["economic_evaluation_authorized"] is False
        assert payload["candidate_ratified"] is False
        assert payload["economic_validity_offline_gate_pass"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["promotion_authorized"] is False
        assert payload["runtime_authority"] is False
        assert payload["shadow_authorized"] is False
        assert payload["paper_authorized"] is False
        assert payload["testnet_authorized"] is False
        assert payload["orders_allowed"] is False
        assert payload["scheduler_runtime_allowed"] is False
        assert payload["live_authorized"] is False
        assert payload["further_same_binding_retry_allowed"] is False
        assert payload["requires_separate_operator_go_for_evaluation"] is True
        assert payload["requires_full_panel_binding"] is True
        assert payload["narrow_adapter_eth_only_binding_disallowed_for_this_scope"] is True

    def test_scope_config_excluded_failed_bindings(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        excluded = payload["excluded_failed_bindings"]
        for candidate in EXCLUDED_CANDIDATES:
            assert candidate in excluded["blocked_candidate_identifiers"]
        assert FAILED_STEP31F_DIGEST in excluded["blocked_completion_digests"]
        assert FAILED_FLEET_BINDING_DIGEST in excluded["blocked_completion_digests"]
        assert FAILED_FLEET_SCOPE_DIGEST in excluded["blocked_scope_digests"]

    def test_governance_doc_has_docs_token_and_verdict(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVIDENCE_CLASS_SCOPE_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{SCOPE_STATUS}`" in body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in body
        assert "`ECONOMIC_EVALUATION_AUTHORIZED` | `false`" in body
        assert FAILED_STEP31F_DIGEST in body
        assert FAILED_FLEET_BINDING_DIGEST in body
        assert FAILED_FLEET_SCOPE_DIGEST in body

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVIDENCE_CLASS_SCOPE_V0_STATUS",
            )
            == SCOPE_STATUS
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVIDENCE_CLASS_SCOPE_V0_CONFIG_REF",
            )
            == "config/research/okx_full_panel_cross_sectional_ranking_strategy_archetype_evidence_class_scope_v0.json"
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVIDENCE_CLASS_ID",
            )
            == EVIDENCE_CLASS_ID
        )
        assert _field_value(text, "NEXT_CANONICAL_STEP") == "NO_RUNTIME_OR_PROMOTION_ACTION"
        assert authoritative_field_value("FURTHER_SAME_BINDING_RETRY_ALLOWED") == "false"
        assert (
            authoritative_field_value(
                "FURTHER_ECONOMIC_EVALUATION_REQUIRES_NEW_EVIDENCE_CLASS_SCOPE_AND_EXPLICIT_OPERATOR_GO"
            )
            == "true"
        )
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == (
            "consumed_for_completed_offline_scope_only"
        )
        assert authoritative_field_value("RUNTIME_AUTHORITY") == "false"

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == SCOPE_STATUS
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "SCOPE_DEFINED") == "true"
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "CANDIDATE_RATIFIED") == "false"
        assert _field_value(section, "REQUIRES_SEPARATE_OPERATOR_GO_FOR_EVALUATION") == "true"
        assert _field_value(section, "REQUIRES_FULL_PANEL_BINDING") == "true"
        assert (
            _field_value(
                section,
                "NARROW_ADAPTER_ETH_ONLY_BINDING_DISALLOWED_FOR_THIS_SCOPE",
            )
            == "true"
        )
        assert _field_value(section, "FURTHER_SAME_BINDING_RETRY_ALLOWED") == "false"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == "NO_RUNTIME_OR_PROMOTION_ACTION"
