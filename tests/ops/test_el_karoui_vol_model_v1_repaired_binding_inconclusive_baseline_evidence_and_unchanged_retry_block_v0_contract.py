"""Contract tests for el_karoui v1 repaired-binding inconclusive baseline evidence registration v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.research.el_karoui_vol_model_v1_repaired_binding_inconclusive_baseline_evidence_and_unchanged_retry_block_v0 import (
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
    TERMINAL_STATUS,
    TRADE_COUNT,
    apply_scope_ratification_registration_fields,
    apply_versioned_binding_registration_fields,
    compute_registration_digest,
    is_exact_binding_retry_blocked,
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
    "el_karoui_vol_model_v1_repaired_binding_inconclusive_baseline_evidence_and_"
    "unchanged_retry_block_v0.json"
)
GOVERNANCE_DOC = REPO_ROOT / GOVERNANCE_REL_PATH
BINDING_PATH = (
    REPO_ROOT / "config/research/el_karoui_vol_model_v1_versioned_research_binding_v0.json"
)
SCOPE_RATIFICATION_PATH = (
    REPO_ROOT
    / "config/research/el_karoui_vol_model_v1_offline_economic_evaluation_scope_ratification_v0.json"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### EL_KAROUI_VOL_MODEL_V1_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_AND_"
    "UNCHANGED_RETRY_BLOCK_V0"
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


class TestInconclusiveRegistrationModule:
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
            "el_karoui_vol_model_v1_repaired_binding_inconclusive_baseline_evidence_and_"
            "unchanged_retry_block_v0.py"
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


class TestInconclusiveRegistrationConfig:
    def test_config_exists_and_required_fields(self) -> None:
        assert REGISTRATION_CONFIG.is_file()
        payload = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert payload["artifact_kind"] == REGISTRATION_ID
        assert payload["go_token"] == OPERATOR_GO_TOKEN
        assert payload["research_scope"] == RESEARCH_SCOPE
        assert payload["binding_digest"] == BINDING_DIGEST
        assert payload["terminal_status"] == TERMINAL_STATUS
        assert payload["baseline_verdict"] == BASELINE_VERDICT
        assert payload["terminal_economic_decision"] == BASELINE_VERDICT
        assert payload["accounting_reconciliation_pass"] is True
        assert payload["economic_validity_offline_gate_pass"] is False
        assert payload["promotion_admissible"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["retry_allowed_same_binding"] is False
        assert payload["unchanged_retry_allowed"] is False
        assert payload["unchanged_retry_blocked"] is True
        assert payload["parameter_relaxation_authorized"] is False
        assert payload["policy_rescue_allowed"] is False
        assert payload["terminal_negative_evidence_for_unchanged_binding"] is False
        assert payload["terminal_inconclusive_evidence_for_unchanged_binding"] is True
        assert payload["new_distinct_research_scope_or_new_evidence_class_required"] is True
        assert payload["trade_count"] == TRADE_COUNT
        assert payload["pre_merge_origin_main"] == PRE_MERGE_ORIGIN_MAIN
        assert str(CANONICAL_EVALUATION_DIR) in payload["canonical_evaluation_bundle"]
        assert payload["registration_digest"] == compute_registration_digest(payload)

    def test_canonical_serialization_stable(self) -> None:
        payload = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert serialize_canonical_json(payload) == serialize_canonical_json(payload)


class TestInconclusiveVersionedBinding:
    def test_binding_inconclusive_and_retry_blocked(self) -> None:
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
        assert binding["unchanged_retry_allowed"] is False
        assert binding["binding_changed"] is False
        assert binding["trade_count"] == TRADE_COUNT
        assert binding["canonical_evaluation_timestamp"] == CANONICAL_EVALUATION_TIMESTAMP
        assert str(CANONICAL_EVALUATION_DIR) in binding["canonical_evaluation_bundle"]
        assert binding["economic_viability_evidence_manifest_digest"] == CANONICAL_MANIFEST_DIGEST
        assert (
            apply_versioned_binding_registration_fields(binding, registration)["baseline_verdict"]
            == BASELINE_VERDICT
        )


class TestInconclusiveScopeRatification:
    def test_scope_ratification_inconclusive_and_retry_blocked(self) -> None:
        scope = json.loads(SCOPE_RATIFICATION_PATH.read_text(encoding="utf-8"))
        registration = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert scope["economic_evaluation_executed"] is True
        assert scope["baseline_verdict"] == BASELINE_VERDICT
        assert scope["unchanged_retry_blocked"] is True
        assert scope["promotion_admissible"] is False
        assert (
            apply_scope_ratification_registration_fields(scope, registration)[
                "evaluation_authorization_status"
            ]
            == "COMPLETE_INCONCLUSIVE_BINDING_BLOCKED_RETRY"
        )


class TestInconclusiveDistinctFromNegative:
    def test_inconclusive_not_labeled_terminal_negative(self) -> None:
        payload = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert payload["baseline_verdict"] == "INCONCLUSIVE"
        assert payload["terminal_negative_evidence_for_unchanged_binding"] is False
        assert payload["terminal_inconclusive_evidence_for_unchanged_binding"] is True
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        assert binding["terminal_negative_evidence_for_unchanged_binding"] is False
        assert binding["terminal_inconclusive_evidence_for_unchanged_binding"] is True


class TestInconclusiveProgressRegistry:
    def test_global_metadata_inconclusive(self) -> None:
        assert authoritative_field_value("EL_KAROUI_VOL_MODEL_V1_STATUS") == "COMPLETE_INCONCLUSIVE"
        assert (
            authoritative_field_value("EL_KAROUI_VOL_MODEL_V1_ECONOMIC_EVALUATION_EXECUTED")
            == "true"
        )
        assert (
            authoritative_field_value("EL_KAROUI_VOL_MODEL_V1_RETRY_UNCHANGED_BINDING_ALLOWED")
            == "false"
        )
        assert (
            authoritative_field_value(
                "EL_KAROUI_VOL_MODEL_V1_TERMINAL_INCONCLUSIVE_EVIDENCE_FOR_UNCHANGED_BINDING"
            )
            == "true"
        )
        assert (
            authoritative_field_value(
                "EL_KAROUI_VOL_MODEL_V1_TERMINAL_NEGATIVE_EVIDENCE_FOR_UNCHANGED_BINDING"
            )
            == "false"
        )
        assert (
            authoritative_field_value("EL_KAROUI_VOL_MODEL_V1_CANONICAL_EVALUATION_TIMESTAMP")
            == CANONICAL_EVALUATION_TIMESTAMP
        )

    def test_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert (
            _field_value(section, "STATUS")
            == "REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_REGISTRATION_COMPLETE"
        )
        assert _field_value(section, "VERDICT") == "PASS"
        assert _field_value(section, "BASELINE_VERDICT") == "INCONCLUSIVE"
        assert _field_value(section, "TERMINAL_STATUS") == TERMINAL_STATUS
        assert _field_value(section, "ACCOUNTING_RECONCILIATION_PASS") == "true"
        assert _field_value(section, "UNCHANGED_RETRY_ALLOWED") == "false"
        assert _field_value(section, "CANONICAL_MANIFEST_DIGEST") == CANONICAL_MANIFEST_DIGEST

    def test_governance_doc_present(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert OPERATOR_GO_TOKEN in body
        assert CANONICAL_MANIFEST_DIGEST in body
