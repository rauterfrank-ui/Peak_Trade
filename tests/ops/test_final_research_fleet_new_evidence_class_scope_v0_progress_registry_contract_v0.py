"""Contract tests for final research fleet new evidence class scope v0 progress registry."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = REPO_ROOT / "config/research/final_research_fleet_new_evidence_class_scope_v0.json"
GOVERNANCE_DOC = REPO_ROOT / "docs/governance/FINAL_RESEARCH_FLEET_NEW_EVIDENCE_CLASS_SCOPE_V0.md"
CLOSEOUT_SECTION_PREFIX = "#### FINAL_RESEARCH_FLEET_NEW_EVIDENCE_CLASS_SCOPE_V0"
SCOPE_STATUS = "NEW_EVIDENCE_CLASS_SCOPE_DEFINED"
NEXT_CANONICAL_STEP = (
    "REQUEST_OPERATOR_GO_FOR_BOUNDED_NEW_EVIDENCE_CLASS_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
PREVIOUS_DIGEST = "161d834e5153df78a0013b6e55c4c8bd4788c775811e3678f025104a307d78f1"
NEW_DIGEST = "c5e3b5fe6b688b49dbd2b210fd63bdea79201d64820591f87091b4e20689a9dd"


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


class TestFinalResearchFleetNewEvidenceClassScopeV0ProgressRegistryContract:
    def test_scope_config_is_valid_json_and_binding_ready(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["binding_ready"] is True
        assert payload["binding_spec_status"] == SCOPE_STATUS
        assert payload["previous_completion_digest"] == PREVIOUS_DIGEST
        assert payload["new_binding_completion_digest"] == NEW_DIGEST
        assert payload["retry_unchanged_binding_allowed"] is False
        assert payload["evidence_class"] == "NEW_VERSIONED_RESEARCH_SCOPE_NOT_UNCHANGED_RETRY"
        assert payload["class_d_owner_mixing_allowed"] is False
        assert payload["economic_evaluation_authorized"] is False
        assert payload["candidate_ratified"] is False
        assert payload["runtime_authority"] is False
        assert len(payload["new_binding_delta_dimensions"]) >= 1

    def test_governance_doc_has_docs_token_and_verdict(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker("DOCS_TOKEN_FINAL_RESEARCH_FLEET_NEW_EVIDENCE_CLASS_SCOPE_V0")
            in body
        )
        assert f"`VERDICT` | `{SCOPE_STATUS}`" in body
        assert "`BINDING_READY` | `true`" in body
        assert PREVIOUS_DIGEST in body
        assert NEW_DIGEST in body

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(text, "FINAL_RESEARCH_FLEET_NEW_EVIDENCE_CLASS_SCOPE_V0_STATUS")
            == SCOPE_STATUS
        )
        assert (
            _field_value(text, "FINAL_RESEARCH_FLEET_NEW_EVIDENCE_CLASS_SCOPE_V0_CONFIG_REF")
            == "config/research/final_research_fleet_new_evidence_class_scope_v0.json"
        )
        assert _field_value(text, "NEW_EVIDENCE_CLASS_BINDING_COMPLETION_DIGEST") == NEW_DIGEST
        assert _field_value(text, "HISTORICAL_STEP31F_BLOCKED_COMPLETION_DIGEST") == PREVIOUS_DIGEST
        assert _field_value(text, "NEW_EVIDENCE_CLASS_SCOPE_BINDING_READY") == "true"
        assert _field_value(text, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert authoritative_field_value("RETRY_UNCHANGED_BINDING_ALLOWED") == "false"
        assert (
            authoritative_field_value("EXIT_COMPANION_DRAFT_CANDIDATE_STATE")
            == "PARKED_COUNTS_ONLY_FAILED"
        )
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("RUNTIME_AUTHORITY") == "false"

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == SCOPE_STATUS
        assert _field_value(section, "BINDING_READY") == "true"
        assert (
            _field_value(section, "EVIDENCE_CLASS")
            == "NEW_VERSIONED_RESEARCH_SCOPE_NOT_UNCHANGED_RETRY"
        )
        assert _field_value(section, "PREVIOUS_COMPLETION_DIGEST") == PREVIOUS_DIGEST
        assert _field_value(section, "NEW_BINDING_COMPLETION_DIGEST") == NEW_DIGEST
        assert _field_value(section, "RETRY_UNCHANGED_BINDING_ALLOWED") == "false"
        assert _field_value(section, "EVALUATION_EXECUTED") == "false"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
