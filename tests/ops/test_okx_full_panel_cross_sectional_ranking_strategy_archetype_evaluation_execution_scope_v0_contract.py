"""Contract tests for OKX full-panel cross-sectional ranking evaluation execution scope v0."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/okx_full_panel_cross_sectional_ranking_strategy_archetype_evaluation_execution_scope_v0.json"
)
BINDINGS_CONFIG = (
    REPO_ROOT
    / "config/research/okx_full_panel_cross_sectional_ranking_strategy_archetype_bindings_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVALUATION_EXECUTION_SCOPE_V0.md"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVALUATION_EXECUTION_SCOPE_V0"
)
EVIDENCE_CLASS_ID = "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_V0"
SCOPE_ID = "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVALUATION_EXECUTION_SCOPE_V0"
SCOPE_STATUS = "EVALUATION_EXECUTION_SCOPE_RATIFICATION_COMPLETE"
DATA_DIGEST = "0bfa4df4221a2ec27625c50e3675302ffa51e4b54cddcf81ca5ad13cc15cf8b7"
FORBIDDEN_EXECUTION_MARKERS = (
    "BACKTEST_EXECUTION_IN_THIS_SCOPE",
    "WALK_FORWARD_EXECUTION_IN_THIS_SCOPE",
    "MONTE_CARLO_EXECUTION_IN_THIS_SCOPE",
    "STRESS_EXECUTION_IN_THIS_SCOPE",
    "PARAMETER_SENSITIVITY_EXECUTION_IN_THIS_SCOPE",
    "ECONOMIC_EVALUATION_EXECUTION_IN_THIS_SCOPE",
)
REQUIRED_SCOPE_FIELDS = (
    "evidence_class_id",
    "binding_config_ref",
    "binding_config_digest",
    "implementation_refs",
    "implementation_digests",
    "config_refs",
    "config_digests",
    "data_refs",
    "data_digests",
    "data_digest_policy",
    "universe_binding_ref",
    "instrument_panel_binding_ref",
    "dataset_binding_ref",
    "period_binding_ref",
    "fee_model_binding_ref",
    "slippage_model_binding_ref",
    "funding_model_binding_ref",
    "execution_model_binding_ref",
    "economic_policy_binding_ref",
    "ranking_policy_binding_ref",
    "selection_policy_binding_ref",
    "allowed_future_execution_commands",
    "forbidden_execution_commands",
    "expected_output_bundle_contract",
    "manifest_policy",
    "fail_closed_conditions",
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


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_digest(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class TestOkxFullPanelCrossSectionalRankingStrategyArchetypeEvaluationExecutionScopeV0Contract:
    def test_scope_config_identity_and_authority_gates(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["scope_id"] == SCOPE_ID
        assert payload["evaluation_execution_scope_status"] == SCOPE_STATUS
        assert payload["evaluation_execution_scope_ratified"] is True
        assert payload["authority_effect"] == "NONE"
        assert payload["economic_evaluation_authorized"] is False
        assert payload["evaluation_execution_authorized"] is False
        assert payload["evaluation_execution_executed"] is False
        assert payload["economic_evaluation_executed"] is False
        assert payload["candidate_ratified"] is False
        assert payload["promotion_authorized"] is False
        assert payload["runtime_authority"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["further_economic_evaluation_requires_separate_operator_go"] is True
        assert payload["requires_separate_operator_go_for_evaluation_execution"] is True

    def test_scope_config_required_fields_present(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        for field in REQUIRED_SCOPE_FIELDS:
            assert field in payload, f"missing required scope field: {field}"

    def test_scope_config_binding_reference_and_digest_stable(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert (
            payload["binding_config_ref"]
            == "config/research/okx_full_panel_cross_sectional_ranking_strategy_archetype_bindings_v0.json"
        )
        assert payload["binding_config_digest"] == _file_sha256(BINDINGS_CONFIG)
        bindings = json.loads(BINDINGS_CONFIG.read_text(encoding="utf-8"))
        assert bindings["evidence_class_id"] == EVIDENCE_CLASS_ID

    def test_scope_config_digest_policies_and_materialized_values(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["data_digest_policy"]["status"] == "BOUND"
        assert (
            payload["data_digest_policy"]["final_materialization_required_before_execution"] is True
        )
        assert payload["data_digests"]["dataset_content_digest"] == DATA_DIGEST
        assert payload["implementation_digests"][
            "composite_implementation_digest"
        ] == _stable_digest(payload["implementation_refs"])
        assert payload["scope_ratification_digest"] == _stable_digest(
            {k: v for k, v in payload.items() if k != "scope_ratification_digest"}
        )
        for ref in payload["config_refs"].values():
            name = Path(ref).name
            assert name in payload["config_digests"]
            assert payload["config_digests"][name] == _file_sha256(REPO_ROOT / ref)

    def test_scope_config_execution_commands_not_executed(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["allowed_future_execution_commands"]
        for command in payload["allowed_future_execution_commands"]:
            assert command["execution_status"] == "NOT_EXECUTED"
            assert command["execution_authorized_in_this_scope"] is False
            assert command["runner_status"] == "PLANNED_NOT_MATERIALIZED"
        for marker in FORBIDDEN_EXECUTION_MARKERS:
            assert marker in payload["forbidden_execution_commands"]

    def test_scope_config_futures_only_constraints(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["futures_only"] is True
        assert payload["bitcoin_direction_allowed"] is False
        assert payload["spot_allowed"] is False
        assert payload["synthetic_spot_allowed"] is False

    def test_governance_doc_has_docs_token_and_verdict(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVALUATION_EXECUTION_SCOPE_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{SCOPE_STATUS}`" in body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in body
        assert "`ECONOMIC_EVALUATION_AUTHORIZED` | `false`" in body
        assert "`EVALUATION_EXECUTION_AUTHORIZED` | `false`" in body
        assert "`RUNTIME_AUTHORITY` | `false`" in body

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVALUATION_EXECUTION_SCOPE_V0_STATUS",
            )
            == SCOPE_STATUS
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVALUATION_EXECUTION_SCOPE_V0_CONFIG_REF",
            )
            == "config/research/okx_full_panel_cross_sectional_ranking_strategy_archetype_evaluation_execution_scope_v0.json"
        )
        assert (
            _field_value(
                text,
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_EVALUATION_EXECUTION_AUTHORIZED",
            )
            == "false"
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
                "OKX_FULL_PANEL_CROSS_SECTIONAL_RANKING_STRATEGY_ARCHETYPE_FURTHER_ECONOMIC_EVALUATION_REQUIRES_SEPARATE_OPERATOR_GO",
            )
            == "true"
        )
        assert _field_value(text, "PR4850_MERGE_COMMIT") == (
            "19126d80bce35927197e590789af62041c0f0773"
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == SCOPE_STATUS
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "SCOPE_ID") == SCOPE_ID
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "EVALUATION_EXECUTION_AUTHORIZED") == "false"
        assert _field_value(section, "RUNTIME_AUTHORITY") == "false"
        assert (
            _field_value(
                section,
                "FURTHER_ECONOMIC_EVALUATION_REQUIRES_SEPARATE_OPERATOR_GO",
            )
            == "true"
        )
        assert _field_value(section, "NEXT_CANONICAL_STEP") == "NO_RUNTIME_OR_PROMOTION_ACTION"
