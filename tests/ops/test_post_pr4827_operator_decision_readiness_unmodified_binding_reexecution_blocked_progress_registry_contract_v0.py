"""Contract tests for post-PR4827 operator decision readiness v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.governance.runbook_progress_registry_v1 import (
    duplicate_current_owner_fields,
    load_runbook_progress_registry_v1,
)
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    ACCEPTED_GO_TOKENS,
    EXPECTED_ORIGIN_MAIN_SHA,
    GO_TOKEN,
    GO_TOKEN_OPERATOR_ALIAS,
    HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST,
    PR4826_CREATES_NEW_EXECUTION_EVIDENCE_CLASS,
    REASON_NEW_EVIDENCE_CLASS_REQUIRED,
    REASON_UNMODIFIED_BINDING_RETRY_BLOCKED,
    is_accepted_go_token,
    verify_unmodified_retry_admissibility_v0,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    global_summary_section,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "POST_PR4827_OPERATOR_DECISION_READINESS_UNMODIFIED_BINDING_REEXECUTION_BLOCKED_V0.md"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### POST_PR4827_OPERATOR_DECISION_READINESS_UNMODIFIED_BINDING_REEXECUTION_BLOCKED_V0"
)
CURRENT_GLOBAL_NEXT_STEP = "OPERATOR_DECISION_REQUIRED_UNMODIFIED_BINDING_REEXECUTION_BLOCKED_V0"
PR4827_MERGE_COMMIT = "4fc405ca9281495ce10cf9b56e35e0ec0e4f6369"
PR4826_MERGE_COMMIT = "208ab96562f7750fb4dff43936b345a040d1cea4"
CS_TERMINAL_NEXT_STEP = "NO_FURTHER_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_ACTION_TERMINAL_FAIL"


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return text[start:end]


class TestPostPr4827AuthoritativeGlobalState:
    def test_global_next_step_operator_decision_required(self) -> None:
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == CURRENT_GLOBAL_NEXT_STEP
        assert authoritative_field_value("NEXT_CANONICAL_ACTION") == CURRENT_GLOBAL_NEXT_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == CURRENT_GLOBAL_NEXT_STEP

    def test_post_pr4827_operator_decision_readiness_flags(self) -> None:
        assert authoritative_field_value("PR4827_MERGE_COMMIT") == PR4827_MERGE_COMMIT
        assert (
            authoritative_field_value("POST_PR4827_OPERATOR_DECISION_READINESS_STATUS")
            == "COMPLETE"
        )
        assert (
            authoritative_field_value("POST_PR4827_UNMODIFIED_BINDING_REEXECUTION_BLOCKED")
            == "true"
        )
        assert authoritative_field_value("POST_PR4827_EXECUTION_START_BLOCKED") == "true"
        assert (
            authoritative_field_value("POST_PR4827_CREATES_NEW_EXECUTION_EVIDENCE_CLASS") == "false"
        )

    def test_execution_not_authorized_and_retry_blocked(self) -> None:
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("RETRY_UNCHANGED_BINDING_ALLOWED") == "false"
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == "NONE"
        assert (
            authoritative_field_value("FINAL_FLEET_OFFLINE_EVAL_EXECUTION_PREFLIGHT_STATUS")
            == "FAIL_CLOSED"
        )

    def test_cs_v0_terminal_fail_unchanged(self) -> None:
        assert authoritative_field_value("HYPOTHESIS_SUBSTRAND_NEXT_STEP") == CS_TERMINAL_NEXT_STEP


class TestPostPr4827CloseoutSection:
    def test_closeout_records_blocked_state_without_execution(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "COMPLETE"
        assert (
            _field_value(section, "VERDICT")
            == "POST_PR4827_OPERATOR_DECISION_READINESS_UNMODIFIED_BINDING_REEXECUTION_BLOCKED_RATIFIED"
        )
        assert _field_value(section, "PR4827_MERGE_COMMIT") == PR4827_MERGE_COMMIT
        assert _field_value(section, "CURRENT_ORIGIN_MAIN") == PR4827_MERGE_COMMIT
        assert _field_value(section, "EXPECTED_ORIGIN_MAIN_SHA_BINDING") == PR4826_MERGE_COMMIT
        assert (
            _field_value(section, "GO_TOKEN_BINDING_DECISION")
            == "OPERATOR_ALIAS_IS_PURE_ALIAS_ON_CANONICAL_GO_TOKEN"
        )
        assert (
            _field_value(section, "RETRY_ADMISSIBILITY_DECISION")
            == "UNMODIFIED_BINDING_REEXECUTION_BLOCKED"
        )
        assert _field_value(section, "PR4827_CREATES_NEW_EXECUTION_EVIDENCE_CLASS") == "false"
        assert _field_value(section, "EXECUTION_START_BLOCKED") == "true"
        assert _field_value(section, "EVALUATION_EXECUTED") == "false"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == CURRENT_GLOBAL_NEXT_STEP
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"


class TestPostPr4827ExecutionOwnerAdmissibility:
    def test_go_token_alias_registered_as_pure_alias(self) -> None:
        assert GO_TOKEN_OPERATOR_ALIAS in ACCEPTED_GO_TOKENS
        assert is_accepted_go_token(GO_TOKEN_OPERATOR_ALIAS)
        assert is_accepted_go_token(GO_TOKEN)

    def test_sha_rebind_to_pr4826_does_not_create_new_evidence_class(self) -> None:
        assert EXPECTED_ORIGIN_MAIN_SHA == PR4826_MERGE_COMMIT
        assert PR4826_CREATES_NEW_EXECUTION_EVIDENCE_CLASS is False

    def test_unmodified_step31f_retry_blocked_despite_go_alias_and_sha_rebind(self) -> None:
        repo_binding_path = (
            REPO_ROOT
            / "config"
            / "research"
            / "final_research_fleet_versioned_binding_completion_v0.json"
        )
        fleet_binding_completion = json.loads(repo_binding_path.read_text(encoding="utf-8"))
        assert (
            fleet_binding_completion.get("completion_digest")
            == HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST
        )
        ok, reasons = verify_unmodified_retry_admissibility_v0(
            fleet_binding_completion=fleet_binding_completion,
        )
        assert ok is False
        assert REASON_UNMODIFIED_BINDING_RETRY_BLOCKED in reasons
        assert REASON_NEW_EVIDENCE_CLASS_REQUIRED in reasons


class TestPostPr4827GovernanceDoc:
    def test_governance_doc_exists_and_declares_blocked_state(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "POST_PR4827_OPERATOR_DECISION_READINESS_UNMODIFIED_BINDING_REEXECUTION_BLOCKED" in (
            body
        )
        assert PR4827_MERGE_COMMIT in body
        assert "UNMODIFIED_BINDING_REEXECUTION_BLOCKED" in body
        assert "EXECUTION_START_BLOCKED" in body
        assert "PR4827_CREATES_NEW_EXECUTION_EVIDENCE_CLASS" in body


class TestRegistryResolverIntegrity:
    def test_no_duplicate_conflicting_authoritative_current_owners(self) -> None:
        registry = load_runbook_progress_registry_v1()
        ambiguous = duplicate_current_owner_fields(
            registry,
            fields=(
                "NEXT_CANONICAL_STEP",
                "GLOBAL_RUNBOOK_NEXT_STEP",
                "POST_PR4827_UNMODIFIED_BINDING_REEXECUTION_BLOCKED",
                "POST_PR4827_EXECUTION_START_BLOCKED",
            ),
        )
        assert ambiguous == {}

    def test_global_summary_reflects_post_pr4827_state(self) -> None:
        summary = global_summary_section()
        assert _field_value(summary, "NEXT_CANONICAL_STEP") == CURRENT_GLOBAL_NEXT_STEP
        assert _field_value(summary, "POST_PR4827_OPERATOR_DECISION_READINESS_STATUS") == "COMPLETE"
