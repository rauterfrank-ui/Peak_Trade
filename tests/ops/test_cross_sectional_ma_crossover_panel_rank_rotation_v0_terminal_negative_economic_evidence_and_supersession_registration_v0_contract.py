"""Contract tests for CS MA-crossover v0 terminal-negative supersession registration v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_terminal_negative_economic_evidence_and_supersession_registration_v0 import (
    BINDING_DIGEST,
    CANONICAL_EVALUATION_TIMESTAMP,
    CANONICAL_MANIFEST_DIGEST,
    CONFIG_DIGEST,
    CORRECTED_EVALUATION_DIR,
    DATA_DIGEST,
    GOVERNANCE_REL_PATH,
    NET_RETURN,
    OPERATOR_GO_TOKEN,
    ORIGINAL_EVALUATION_DIR,
    PR5080_CLOSEOUT_DIR,
    REGISTRATION_ID,
    SOURCE_MERGE_COMMIT,
    SUPERSEDED_EVALUATION_TIMESTAMP,
    SUPERSEDED_MANIFEST_DIGEST,
    SUPERSESSION_REASON,
    TRADE_COUNT,
    UNIVERSE_DIGEST,
    VERSIONED_BINDING_CONFIG_REL_PATH,
    compute_registration_digest,
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
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_"
    "terminal_negative_economic_evidence_and_supersession_registration_v0.json"
)
GOVERNANCE_DOC = REPO_ROOT / GOVERNANCE_REL_PATH
BINDING_PATH = REPO_ROOT / VERSIONED_BINDING_CONFIG_REL_PATH
CLOSEOUT_SECTION_PREFIX = (
    "#### CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_"
    "TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_AND_SUPERSESSION_REGISTRATION_V0"
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
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return text[start:end]


class TestTerminalNegativeSupersessionRegistrationModule:
    def test_preconditions_and_deterministic_registration_digest(self) -> None:
        original, corrected = validate_registration_preconditions()
        first = materialize_registration_config(original=original, corrected=corrected)
        second = materialize_registration_config(original=original, corrected=corrected)
        assert first == second
        assert first["registration_digest"] == compute_registration_digest(first)
        assert first["canonical_manifest_digest"] == corrected.manifest_digest
        assert first["superseded_manifest_digest"] == original.manifest_digest
        assert first["canonical_manifest_digest"] != first["superseded_manifest_digest"]

    def test_no_runtime_or_scheduler_imports(self) -> None:
        module_path = (
            REPO_ROOT / "src/research/"
            "cross_sectional_ma_crossover_panel_rank_rotation_v0_"
            "terminal_negative_economic_evidence_and_supersession_registration_v0.py"
        )
        source = module_path.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source


class TestTerminalNegativeSupersessionRegistrationConfig:
    def test_config_exists_and_required_fields(self) -> None:
        assert REGISTRATION_CONFIG.is_file()
        payload = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert payload["artifact_kind"] == REGISTRATION_ID
        assert payload["go_token"] == OPERATOR_GO_TOKEN
        assert payload["research_scope"] == "cross_sectional_ma_crossover_panel_rank_rotation/v0"
        assert payload["binding_digest"] == BINDING_DIGEST
        assert payload["config_digest"] == CONFIG_DIGEST
        assert payload["data_digest"] == DATA_DIGEST
        assert payload["universe_digest"] == UNIVERSE_DIGEST
        assert payload["canonical_evaluation_timestamp"] == CANONICAL_EVALUATION_TIMESTAMP
        assert payload["superseded_evaluation_timestamp"] == SUPERSEDED_EVALUATION_TIMESTAMP
        assert payload["canonical_manifest_digest"] == CANONICAL_MANIFEST_DIGEST
        assert payload["superseded_manifest_digest"] == SUPERSEDED_MANIFEST_DIGEST
        assert payload["supersession_reason"] == SUPERSESSION_REASON
        assert payload["accounting_reconciliation_pass"] is True
        assert payload["baseline_verdict"] == "FAIL"
        assert payload["economic_validity_offline_gate_pass"] is False
        assert payload["retry_allowed_same_binding"] is False
        assert payload["terminal_negative_evidence_for_unchanged_binding"] is True
        assert payload["source_merge_commit"] == SOURCE_MERGE_COMMIT
        assert str(CORRECTED_EVALUATION_DIR) in payload["canonical_evaluation_bundle"]
        assert str(ORIGINAL_EVALUATION_DIR) in payload["superseded_evaluation_bundle"]
        assert str(PR5080_CLOSEOUT_DIR) in payload["pr5080_closeout_dir"]
        assert payload["net_return"] == NET_RETURN
        assert payload["trade_count"] == TRADE_COUNT
        assert payload["registration_digest"] == compute_registration_digest(payload)

    def test_canonical_serialization_stable(self) -> None:
        payload = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert serialize_canonical_json(payload) == serialize_canonical_json(payload)


class TestTerminalNegativeSupersessionVersionedBinding:
    def test_binding_terminal_fail_and_retry_blocked(self) -> None:
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        assert binding["economic_evaluation_executed"] is True
        assert binding["economic_evaluation_status"] == "COMPLETE_FAIL"
        assert binding["economic_validity_offline_gate_pass"] is False
        assert binding["retry_unchanged_binding_allowed"] is False
        assert binding["re_evaluation_allowed"] is False
        assert binding["accounting_reconciliation_pass"] is True
        assert binding["terminal_negative_evidence_for_unchanged_binding"] is True
        assert binding["binding_changed"] is False
        assert binding["trade_count"] == TRADE_COUNT
        assert binding["canonical_evaluation_timestamp"] == CANONICAL_EVALUATION_TIMESTAMP
        assert binding["superseded_evaluation_timestamp"] == SUPERSEDED_EVALUATION_TIMESTAMP
        assert str(CORRECTED_EVALUATION_DIR) in binding["canonical_evaluation_bundle"]
        assert binding["economic_viability_evidence_manifest_digest"] == CANONICAL_MANIFEST_DIGEST
        assert binding["superseded_evaluation_manifest_digest"] == SUPERSEDED_MANIFEST_DIGEST


class TestTerminalNegativeSupersessionProgressRegistry:
    def test_global_metadata_terminal_fail(self) -> None:
        assert authoritative_field_value("LAST_VERIFIED_ORIGIN_MAIN") == SOURCE_MERGE_COMMIT
        assert (
            authoritative_field_value("CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_STATUS")
            == "COMPLETE_FAIL"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_ECONOMIC_EVALUATION_EXECUTED"
            )
            == "true"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_RETRY_UNCHANGED_BINDING_ALLOWED"
            )
            == "false"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_PANEL_ARCHETYPE_EVIDENCE"
            )
            == "TERMINAL_NEGATIVE"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_CANONICAL_EVALUATION_TIMESTAMP"
            )
            == CANONICAL_EVALUATION_TIMESTAMP
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_SUPERSEDED_EVALUATION_TIMESTAMP"
            )
            == SUPERSEDED_EVALUATION_TIMESTAMP
        )

    def test_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert (
            _field_value(section, "STATUS")
            == "TERMINAL_NEGATIVE_EVIDENCE_AND_SUPERSESSION_REGISTRATION_COMPLETE"
        )
        assert _field_value(section, "VERDICT") == "PASS"
        assert _field_value(section, "BASELINE_VERDICT") == "FAIL"
        assert _field_value(section, "ACCOUNTING_RECONCILIATION_PASS") == "true"
        assert _field_value(section, "UNCHANGED_RETRY_ALLOWED") == "false"
        assert _field_value(section, "CANONICAL_MANIFEST_DIGEST") == CANONICAL_MANIFEST_DIGEST
        assert _field_value(section, "SUPERSEDED_MANIFEST_DIGEST") == SUPERSEDED_MANIFEST_DIGEST
        assert _field_value(section, "NEXT_CANONICAL_STEP") == (
            "NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED"
        )

    def test_governance_doc_present(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert OPERATOR_GO_TOKEN in body
        assert CANONICAL_MANIFEST_DIGEST in body
        assert SUPERSESSION_REASON in body
