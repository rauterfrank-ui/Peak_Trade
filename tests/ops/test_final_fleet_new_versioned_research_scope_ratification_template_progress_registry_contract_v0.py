"""Contract tests for final fleet new versioned research scope ratification template v0."""

from __future__ import annotations

import re
from pathlib import Path

from src.governance.runbook_progress_registry_v1 import (
    duplicate_current_owner_fields,
    load_runbook_progress_registry_v1,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    global_summary_section,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RATIFICATION_TEMPLATE = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "FINAL_FLEET_NEW_VERSIONED_RESEARCH_SCOPE_RATIFICATION_TEMPLATE_V0.md"
)
CLOSEOUT_SECTION_PREFIX = "#### FINAL_FLEET_NEW_VERSIONED_RESEARCH_SCOPE_RATIFICATION_TEMPLATE_V0"
CURRENT_HEAD = "5d79b85800e39d345f185f224d68dab2d38d2066"
TEMPLATE_STATUS = "READY"
NEXT_CANONICAL_STEP = "OPERATOR_RATIFICATION_REQUIRED_FOR_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_VERSIONED_EVIDENCE_CLASS_V0"
ADMISSIBILITY_MATRIX = {
    "A_UNMODIFIED_STEP31F_REEXECUTION": "BLOCKED",
    "B_SAME_BINDINGS_NEW_SHA_ONLY": "BLOCKED",
    "C_GOVERNANCE_REWORDING_ONLY": "BLOCKED",
    "D_NEW_VERSIONED_RESEARCH_SCOPE_WITH_FULL_BINDINGS": "OPERATOR_RATIFICATION_REQUIRED",
    "E_NEW_VERSIONED_EVIDENCE_CLASS_WITH_FULL_CONTRACT": "OPERATOR_RATIFICATION_REQUIRED",
    "F_EVALUATION_WITHOUT_RATIFICATION": "BLOCKED",
    "G_RUNTIME_REWIRE": "BLOCKED",
}
RUNTIME_BOUND_FIELDS = (
    "RUNTIME_REWIRE_ALLOWED",
    "SHADOW_ALLOWED",
    "PAPER_ALLOWED",
    "TESTNET_ALLOWED",
    "SCHEDULER_ALLOWED",
    "ADAPTER_SUBMISSION_ALLOWED",
    "ORDERS_ALLOWED",
    "CREDENTIALS_ALLOWED",
    "ARMING_ALLOWED",
    "CANARY_ALLOWED",
    "LIVE_ALLOWED",
)
RATIFICATION_INPUT_KEYS = (
    "strategy_id",
    "strategy_version",
    "parameter_binding",
    "dataset_binding",
    "period_binding",
    "instrument_binding",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "implementation_digest",
    "config_digest",
    "data_digest",
    "evidence_class_id",
    "expected_output_contract",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return text[start:end]


def _read_template() -> str:
    assert RATIFICATION_TEMPLATE.is_file(), (
        f"missing ratification template: {RATIFICATION_TEMPLATE}"
    )
    return RATIFICATION_TEMPLATE.read_text(encoding="utf-8")


class TestFinalFleetNewVersionedResearchScopeRatificationTemplateDoc:
    def test_template_exists_and_declares_non_authorizing(self) -> None:
        body = _read_template()
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_FINAL_FLEET_NEW_VERSIONED_RESEARCH_SCOPE_RATIFICATION_TEMPLATE_V0"
            )
            in body
        )
        assert "STATUS: RATIFICATION_TEMPLATE" in body
        assert "non-authorizing" in body.lower()

    def test_verdict_and_blocking_flags(self) -> None:
        body = _read_template()
        assert "VERDICT` | `NEW_VERSIONED_RESEARCH_SCOPE_RATIFICATION_TEMPLATE_READY_V0" in body
        assert re.search(
            rf"\|\s*`CURRENT_HEAD_BINDING`\s*\|\s*`{CURRENT_HEAD}`\s*\|",
            body,
        )
        assert re.search(r"\|\s*`RATIFICATION_STATUS`\s*\|\s*`NOT_RATIFIED`\s*\|", body)
        assert re.search(r"\|\s*`OFFLINE_EVALUATION_ALLOWED`\s*\|\s*`false`\s*\|", body)
        assert re.search(
            r"\|\s*`UNMODIFIED_STEP31F_REEXECUTION_ALLOWED`\s*\|\s*`false`\s*\|",
            body,
        )
        assert re.search(r"\|\s*`FUTURES_ONLY`\s*\|\s*`true`\s*\|", body)
        assert re.search(
            r"\|\s*`BITCOIN_DIRECTION_ALLOWED`\s*\|\s*`false`\s*\|",
            body,
        )

    def test_runtime_and_execution_bounds_remain_false(self) -> None:
        body = _read_template()
        for field in RUNTIME_BOUND_FIELDS:
            assert re.search(rf"\|\s*`{field}`\s*\|\s*`false`\s*\|", body), field

    def test_admissibility_matrix_classes(self) -> None:
        body = _read_template()
        for decision_class, status in ADMISSIBILITY_MATRIX.items():
            assert decision_class in body
            assert f"| `{decision_class}` | `{status}` |" in body

    def test_ratification_input_matrix_has_required_keys_without_prefilled_values(self) -> None:
        body = _read_template()
        for key in RATIFICATION_INPUT_KEYS:
            assert f"| `{key}` |" in body
            assert (
                f"| `{key}` | Klasse" in body
                or f"| `{key}` | Klasse D" in body
                or (f"| `{key}` | Klasse D/E |" in body)
            )
            assert f"| `{key}` |" in body and "| `MISSING` |" in body


class TestFinalFleetNewVersionedResearchScopeRatificationTemplateRegistry:
    def test_authoritative_template_status_and_next_step(self) -> None:
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == NEXT_CANONICAL_STEP
        assert (
            authoritative_field_value(
                "FINAL_FLEET_NEW_VERSIONED_RESEARCH_SCOPE_RATIFICATION_TEMPLATE_STATUS"
            )
            == TEMPLATE_STATUS
        )
        assert authoritative_field_value("UNMODIFIED_BINDING_REEXECUTION_BLOCKED") == "true"
        assert authoritative_field_value("OFFLINE_ECONOMIC_EVALUATION_EXECUTION_ALLOWED") == "false"

    def test_execution_and_runtime_remain_blocked(self) -> None:
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("RETRY_UNCHANGED_BINDING_ALLOWED") == "false"
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == "NONE"

    def test_closeout_section_records_template_state(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "READY"
        assert (
            _field_value(section, "VERDICT")
            == "NEW_VERSIONED_RESEARCH_SCOPE_RATIFICATION_TEMPLATE_READY_V0"
        )
        assert _field_value(section, "RATIFICATION_STATUS") == "NOT_RATIFIED"
        assert _field_value(section, "OFFLINE_EVALUATION_ALLOWED") == "false"
        assert _field_value(section, "UNMODIFIED_STEP31F_REEXECUTION_ALLOWED") == "false"
        assert _field_value(section, "FUTURES_ONLY") == "true"
        assert _field_value(section, "BITCOIN_DIRECTION_ALLOWED") == "false"
        for decision_class, status in ADMISSIBILITY_MATRIX.items():
            assert _field_value(section, decision_class) == status
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"


class TestRegistryResolverIntegrity:
    def test_no_duplicate_conflicting_authoritative_current_owners(self) -> None:
        registry = load_runbook_progress_registry_v1()
        ambiguous = duplicate_current_owner_fields(
            registry,
            fields=(
                "NEXT_CANONICAL_STEP",
                "GLOBAL_RUNBOOK_NEXT_STEP",
                "FINAL_FLEET_NEW_VERSIONED_RESEARCH_SCOPE_RATIFICATION_TEMPLATE_STATUS",
                "UNMODIFIED_BINDING_REEXECUTION_BLOCKED",
            ),
        )
        assert ambiguous == {}

    def test_global_summary_reflects_template_ready_state(self) -> None:
        summary = global_summary_section()
        assert _field_value(summary, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert (
            _field_value(
                summary,
                "FINAL_FLEET_NEW_VERSIONED_RESEARCH_SCOPE_RATIFICATION_TEMPLATE_STATUS",
            )
            == TEMPLATE_STATUS
        )
