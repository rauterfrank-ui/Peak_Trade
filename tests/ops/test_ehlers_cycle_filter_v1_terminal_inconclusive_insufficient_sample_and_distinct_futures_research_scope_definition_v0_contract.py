"""Contract tests for Ehlers v1 terminal inconclusive registration and distinct scope definition v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.research.ehlers_cycle_filter_v1_terminal_inconclusive_insufficient_sample_and_distinct_futures_research_scope_definition_v0 import (
    BASELINE_VERDICT,
    BINDING_DIGEST,
    CANONICAL_EVALUATION_DIR,
    CANONICAL_EVALUATION_TIMESTAMP,
    CANONICAL_MANIFEST_DIGEST,
    GOVERNANCE_REL_PATH,
    IMPLEMENTATION_DIGEST,
    OPERATOR_GO_TOKEN,
    PRE_MERGE_ORIGIN_MAIN,
    REGISTRATION_ID,
    RESEARCH_SCOPE,
    SELECTED_DISTINCT_SCOPE,
    SOURCE_CLASSIFICATION_EVIDENCE_DIR,
    TERMINAL_STATUS,
    TRADE_COUNT,
    apply_versioned_binding_registration_fields,
    compute_registration_digest,
    is_exact_binding_retry_blocked,
    is_materially_distinct_scope_admissible,
    materialize_registration_config,
    serialize_canonical_json,
    validate_registration_preconditions,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRATION_CONFIG = (
    REPO_ROOT / "config/research/"
    "ehlers_cycle_filter_v1_terminal_inconclusive_insufficient_sample_and_"
    "distinct_futures_research_scope_definition_v0.json"
)
GOVERNANCE_DOC = REPO_ROOT / GOVERNANCE_REL_PATH
BINDING_PATH = (
    REPO_ROOT / "config/research/ehlers_cycle_filter_v1_versioned_research_binding_v0.json"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### EHLERS_CYCLE_FILTER_V1_TERMINAL_INCONCLUSIVE_INSUFFICIENT_SAMPLE_AND_"
    "DISTINCT_FUTURES_RESEARCH_SCOPE_DEFINITION_V0"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
)


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


class TestTerminalInconclusiveRegistrationModule:
    def test_preconditions_and_deterministic_registration_digest(self) -> None:
        canonical = validate_registration_preconditions()
        first = materialize_registration_config(canonical=canonical)
        second = materialize_registration_config(canonical=canonical)
        assert first == second
        assert first["registration_digest"] == compute_registration_digest(first)
        assert first["canonical_manifest_digest"] == canonical.manifest_digest

    def test_no_runtime_or_scheduler_imports(self) -> None:
        module_path = (
            REPO_ROOT / "src/research/"
            "ehlers_cycle_filter_v1_terminal_inconclusive_insufficient_sample_and_"
            "distinct_futures_research_scope_definition_v0.py"
        )
        source = module_path.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source


class TestExactBindingRetryGuard:
    def test_exact_binding_retry_rejected(self) -> None:
        assert is_exact_binding_retry_blocked(
            research_scope=RESEARCH_SCOPE,
            binding_digest=BINDING_DIGEST,
            implementation_digest=IMPLEMENTATION_DIGEST,
        )

    def test_changed_binding_not_blocked(self) -> None:
        assert not is_exact_binding_retry_blocked(
            research_scope=RESEARCH_SCOPE,
            binding_digest="0" * 64,
            implementation_digest=IMPLEMENTATION_DIGEST,
        )

    def test_distinct_scope_not_falsely_rejected(self) -> None:
        assert is_materially_distinct_scope_admissible(SELECTED_DISTINCT_SCOPE)
        assert not is_materially_distinct_scope_admissible(RESEARCH_SCOPE)


class TestTerminalInconclusiveRegistrationConfig:
    def test_config_exists_and_required_fields(self) -> None:
        assert REGISTRATION_CONFIG.is_file()
        payload = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert payload["artifact_kind"] == REGISTRATION_ID
        assert payload["go_token"] == OPERATOR_GO_TOKEN
        assert payload["research_scope"] == RESEARCH_SCOPE
        assert payload["binding_digest"] == BINDING_DIGEST
        assert payload["implementation_digest"] == IMPLEMENTATION_DIGEST
        assert payload["terminal_status"] == TERMINAL_STATUS
        assert payload["baseline_verdict"] == BASELINE_VERDICT
        assert payload["terminal_economic_decision"] == BASELINE_VERDICT
        assert payload["accounting_reconciliation_pass"] is True
        assert payload["retry_allowed_same_binding"] is False
        assert payload["same_binding_retry_allowed"] is False
        assert payload["unchanged_retry_blocked"] is True
        assert payload["terminal_negative_evidence_for_unchanged_binding"] is False
        assert payload["terminal_inconclusive_evidence_for_unchanged_binding"] is True
        assert payload["selected_distinct_scope"] == SELECTED_DISTINCT_SCOPE
        assert payload["material_difference_proven"] is True
        assert payload["distinct_scope_ratified"] is True
        assert payload["trade_count"] == TRADE_COUNT
        assert payload["pre_merge_origin_main"] == PRE_MERGE_ORIGIN_MAIN
        assert str(CANONICAL_EVALUATION_DIR) in payload["canonical_evaluation_bundle"]
        assert (
            str(SOURCE_CLASSIFICATION_EVIDENCE_DIR) in payload["source_classification_evidence_dir"]
        )
        assert payload["registration_digest"] == compute_registration_digest(payload)

    def test_canonical_serialization_stable(self) -> None:
        payload = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert serialize_canonical_json(payload) == serialize_canonical_json(payload)


class TestTerminalInconclusiveVersionedBinding:
    def test_binding_terminal_inconclusive_and_retry_blocked(self) -> None:
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        registration = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert binding["economic_evaluation_executed"] is True
        assert binding["economic_evaluation_status"] == "COMPLETE_INCONCLUSIVE"
        assert binding["baseline_verdict"] == BASELINE_VERDICT
        assert binding["terminal_status"] == TERMINAL_STATUS
        assert binding["retry_unchanged_binding_allowed"] is False
        assert binding["re_evaluation_allowed"] is False
        assert binding["accounting_reconciliation_pass"] is True
        assert binding["terminal_negative_evidence_for_unchanged_binding"] is False
        assert binding["terminal_inconclusive_evidence_for_unchanged_binding"] is True
        assert binding["unchanged_retry_blocked"] is True
        assert binding["distinct_scope_required"] is True
        assert binding["selected_distinct_scope"] == SELECTED_DISTINCT_SCOPE
        assert binding["binding_changed"] is False
        assert binding["trade_count"] == TRADE_COUNT
        assert binding["canonical_evaluation_timestamp"] == CANONICAL_EVALUATION_TIMESTAMP
        assert str(CANONICAL_EVALUATION_DIR) in binding["canonical_evaluation_bundle"]
        assert binding["economic_viability_evidence_manifest_digest"] == CANONICAL_MANIFEST_DIGEST
        assert apply_versioned_binding_registration_fields(binding, registration)[
            "baseline_verdict"
        ] == (BASELINE_VERDICT)


class TestTerminalInconclusiveDistinctFromNegative:
    def test_inconclusive_not_labeled_terminal_negative(self) -> None:
        payload = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert payload["baseline_verdict"] == "INCONCLUSIVE"
        assert payload["terminal_negative_evidence_for_unchanged_binding"] is False
        assert payload["terminal_inconclusive_evidence_for_unchanged_binding"] is True
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        assert binding["terminal_negative_evidence_for_unchanged_binding"] is False
        assert binding["terminal_inconclusive_evidence_for_unchanged_binding"] is True


class TestTerminalInconclusiveProgressRegistry:
    def test_global_metadata_terminal_inconclusive(self) -> None:
        assert authoritative_field_value("LAST_VERIFIED_ORIGIN_MAIN") == PRE_MERGE_ORIGIN_MAIN
        assert authoritative_field_value("EHLERS_CYCLE_FILTER_V1_STATUS") == "COMPLETE_INCONCLUSIVE"
        assert (
            authoritative_field_value("EHLERS_CYCLE_FILTER_V1_ECONOMIC_EVALUATION_EXECUTED")
            == "true"
        )
        assert (
            authoritative_field_value("EHLERS_CYCLE_FILTER_V1_RETRY_UNCHANGED_BINDING_ALLOWED")
            == "false"
        )
        assert (
            authoritative_field_value(
                "EHLERS_CYCLE_FILTER_V1_TERMINAL_INCONCLUSIVE_EVIDENCE_FOR_UNCHANGED_BINDING"
            )
            == "true"
        )
        assert (
            authoritative_field_value(
                "EHLERS_CYCLE_FILTER_V1_TERMINAL_NEGATIVE_EVIDENCE_FOR_UNCHANGED_BINDING"
            )
            == "false"
        )
        assert authoritative_field_value("EHLERS_CYCLE_FILTER_V1_SELECTED_DISTINCT_SCOPE") in {
            SELECTED_DISTINCT_SCOPE,
            SELECTED_DISTINCT_SCOPE.replace("/", "&#47;"),
        }
        assert (
            authoritative_field_value("EHLERS_CYCLE_FILTER_V1_CANONICAL_EVALUATION_TIMESTAMP")
            == CANONICAL_EVALUATION_TIMESTAMP
        )

    def test_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert (
            _field_value(section, "STATUS")
            == "TERMINAL_INCONCLUSIVE_REGISTRATION_AND_DISTINCT_SCOPE_DEFINITION_COMPLETE"
        )
        assert _field_value(section, "VERDICT") == "PASS"
        assert _field_value(section, "BASELINE_VERDICT") == "INCONCLUSIVE"
        assert _field_value(section, "TERMINAL_STATUS") == TERMINAL_STATUS
        assert _field_value(section, "ACCOUNTING_RECONCILIATION_PASS") == "true"
        assert _field_value(section, "UNCHANGED_RETRY_ALLOWED") == "false"
        assert _field_value(section, "SELECTED_DISTINCT_SCOPE") in {
            SELECTED_DISTINCT_SCOPE,
            SELECTED_DISTINCT_SCOPE.replace("/", "&#47;"),
        }
        assert _field_value(section, "CANONICAL_MANIFEST_DIGEST") == CANONICAL_MANIFEST_DIGEST

    def test_governance_doc_present(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert OPERATOR_GO_TOKEN in body
        assert CANONICAL_MANIFEST_DIGEST in body
        assert (
            SELECTED_DISTINCT_SCOPE.replace("/", "&#47;") in body or SELECTED_DISTINCT_SCOPE in body
        )
