"""Contract tests for OKX full-panel cross-sectional ranking strategy archetype bindings v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BINDINGS_CONFIG = (
    REPO_ROOT
    / "config/research/okx_full_panel_cross_sectional_ranking_strategy_archetype_bindings_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_BINDINGS_V0.md"
)
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/okx_full_panel_cross_sectional_ranking_strategy_archetype_evidence_class_scope_v0.json"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_BINDINGS_V0"
)
EVIDENCE_CLASS_ID = "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_V0"
BINDING_ID = "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_V0_BINDINGS_V0"
BINDING_STATUS = "VERSIONED_BINDINGS_MATERIALIZATION_COMPLETE"
FAILED_STEP31F_DIGEST = "161d834e5153df78a0013b6e55c4c8bd4788c775811e3678f025104a307d78f1"
FAILED_FLEET_BINDING_DIGEST = "c5e3b5fe6b688b49dbd2b210fd63bdea79201d64820591f87091b4e20689a9dd"
FAILED_FLEET_SCOPE_DIGEST = "64da0eae56a70ad0661398db14d712f6d58d6ea9f6ad0dbb73f3de2b01d11d67"
FAILED_FLEET_PERIOD_DIGEST = "950ac7f41d2eb3422cdbbd28a3ee5658a7a0a0ce5d6d55b9ddd3d387129fe5c5"
EXCLUDED_CANDIDATES = ("trend_following/v1", "bollinger_bands/v1", "momentum_1h/v1")
REQUIRED_BINDING_DIMENSIONS = (
    "evidence_class_id",
    "strategy_archetype_id",
    "strategy_archetype_version",
    "universe_binding",
    "instrument_panel_binding",
    "dataset_binding",
    "period_binding",
    "training_period",
    "validation_period",
    "out_of_sample_period",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "ranking_policy_binding",
    "selection_policy_binding",
    "implementation_digest_policy",
    "config_digest_policy",
    "data_digest_policy",
    "excluded_legacy_bindings",
    "blocked_shortcuts",
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
    return tail if next_heading == -1 else tail[:next_heading]


class TestOkxFullPanelCrossSectionalRankingStrategyArchetypeBindingsV0Contract:
    def test_bindings_config_identity_and_authority_gates(self) -> None:
        payload = json.loads(BINDINGS_CONFIG.read_text(encoding="utf-8"))
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["binding_id"] == BINDING_ID
        assert payload["binding_ready"] is True
        assert payload["binding_materialization_status"] == BINDING_STATUS
        assert payload["authority_effect"] is False
        assert payload["economic_evaluation_authorized"] is False
        assert payload["candidate_ratified"] is False
        assert payload["runtime_authority"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["promotion_authorized"] is False
        assert payload["shadow_authorized"] is False
        assert payload["paper_authorized"] is False
        assert payload["testnet_authorized"] is False
        assert payload["orders_allowed"] is False
        assert payload["live_authorized"] is False
        assert payload["further_economic_evaluation_requires_separate_operator_go"] is True
        assert payload["requires_separate_operator_go_for_evaluation"] is True
        assert payload["requires_full_panel_binding"] is True

    def test_bindings_config_required_dimensions_present(self) -> None:
        payload = json.loads(BINDINGS_CONFIG.read_text(encoding="utf-8"))
        for dimension in REQUIRED_BINDING_DIMENSIONS:
            assert dimension in payload, f"missing required binding dimension: {dimension}"

    def test_bindings_config_full_panel_and_constraints(self) -> None:
        payload = json.loads(BINDINGS_CONFIG.read_text(encoding="utf-8"))
        assert payload["strategy_archetype_id"] == "cross_sectional_ranking_selection"
        assert payload["strategy_archetype_version"] == "v0"
        assert payload["futures_only"] is True
        assert payload["bitcoin_direction_allowed"] is False
        assert payload["spot_allowed"] is False
        assert payload["synthetic_spot_allowed"] is False

        panel = payload["instrument_panel_binding"]
        assert panel["binding_mode"] == "lifecycle_admissible_complete_panel_v0"
        assert panel["eligible_instrument_count"] == 118
        assert panel["narrow_adapter_disallowed"] is True
        assert panel["single_instrument_evaluation_forbidden"] is True
        assert panel["evaluation_execution_path"] == "true_multi_instrument_cross_sectional_panel"
        assert len(panel["eligible_instrument_ids"]) == 118

        dataset = payload["dataset_binding"]
        assert dataset["dataset_id"] == "okx_full_panel_historical_funding_archive_v0"
        assert dataset["narrow_adapter_disallowed"] is True
        assert dataset["execution_path"] == "true_multi_instrument_cross_sectional_panel"
        assert dataset["evaluation_price_data_adapter"]["status"] == "BLOCKED"

        period = payload["period_binding"]
        assert period["coverage_period_start_utc"] == "2024-05-01T00:00:00Z"
        assert period["coverage_period_end_utc"] == "2024-09-01T00:00:00Z"
        assert period["seven_day_holdout_narrowing_forbidden"] is True
        assert period["full_panel_coverage_required"] is True

    def test_bindings_config_excluded_legacy_and_blocked_shortcuts(self) -> None:
        payload = json.loads(BINDINGS_CONFIG.read_text(encoding="utf-8"))
        excluded = payload["excluded_legacy_bindings"]
        for candidate in EXCLUDED_CANDIDATES:
            assert candidate in excluded["blocked_candidate_identifiers"]
        assert FAILED_STEP31F_DIGEST in excluded["blocked_completion_digests"]
        assert FAILED_FLEET_BINDING_DIGEST in excluded["blocked_completion_digests"]
        assert FAILED_FLEET_SCOPE_DIGEST in excluded["blocked_scope_digests"]

        shortcuts = payload["blocked_shortcuts"]
        assert shortcuts["eth_only_narrow_adapter_forbidden"] is True
        assert shortcuts["seven_day_holdout_narrowing_forbidden"] is True
        assert shortcuts["single_instrument_evaluation_forbidden"] is True
        assert shortcuts["full_panel_claim_requires_multi_instrument_execution"] is True
        assert "NARROW_ADAPTER_INST_ETH_USDT_PERP" in shortcuts["blocked_adapter_kinds"]
        assert FAILED_FLEET_PERIOD_DIGEST in shortcuts["blocked_period_digests"]
        assert shortcuts["blocked_evaluation_instrument_ids"] == ["inst-eth-usdt-perp"]

    def test_bindings_config_scope_cross_reference(self) -> None:
        bindings = json.loads(BINDINGS_CONFIG.read_text(encoding="utf-8"))
        scope = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert bindings["scope_config_ref"] == (
            "config/research/okx_full_panel_cross_sectional_ranking_strategy_archetype_evidence_class_scope_v0.json"
        )
        assert bindings["evidence_class_id"] == scope["evidence_class_id"]
        assert bindings["strategy_archetype_id"] == scope["strategy_archetype_id"]

    def test_governance_doc_has_docs_token_and_verdict(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_BINDINGS_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{BINDING_STATUS}`" in body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in body
        assert f"`BINDING_ID` | `{BINDING_ID}`" in body
        assert "`ECONOMIC_EVALUATION_AUTHORIZED` | `false`" in body
        assert "`RUNTIME_AUTHORITY` | `false`" in body
        assert "`authority_effect` | `false`" in body
        assert FAILED_STEP31F_DIGEST in body
        assert FAILED_FLEET_BINDING_DIGEST in body
        assert FAILED_FLEET_SCOPE_DIGEST in body

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_BINDINGS_V0_STATUS",
            )
            == BINDING_STATUS
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_BINDINGS_V0_CONFIG_REF",
            )
            == "config/research/okx_full_panel_cross_sectional_ranking_strategy_archetype_bindings_v0.json"
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_BINDINGS_V0_GOVERNANCE_REF",
            )
            == "docs/governance/OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_BINDINGS_V0.md"
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_BINDING_READY",
            )
            == "true"
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_BINDING_SPEC_STATUS",
            )
            == "VERSIONED_BINDINGS_MATERIALIZED"
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_ECONOMIC_EVALUATION_AUTHORIZED",
            )
            == "false"
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_REQUIRES_SEPARATE_OPERATOR_GO_FOR_EVALUATION",
            )
            == "true"
        )
        assert authoritative_field_value("PR4849_MERGE_COMMIT") == (
            "f21aadc36c0ee3f5b697ef426da25db5104b9b90"
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == BINDING_STATUS
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "BINDING_ID") == BINDING_ID
        assert _field_value(section, "BINDING_READY") == "true"
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "RUNTIME_AUTHORITY") == "false"
        assert (
            _field_value(
                section,
                "FURTHER_ECONOMIC_EVALUATION_REQUIRES_SEPARATE_OPERATOR_GO",
            )
            == "true"
        )
        assert _field_value(section, "REQUIRES_FULL_PANEL_BINDING") == "true"
        assert (
            _field_value(
                section,
                "NARROW_ADAPTER_ETH_ONLY_BINDING_DISALLOWED",
            )
            == "true"
        )
        assert _field_value(section, "NEXT_CANONICAL_STEP") == "NO_RUNTIME_OR_PROMOTION_ACTION"
