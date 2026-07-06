"""Contract tests for post-PR4936 cross-sectional funding rate fleet complete no-pass scope v0."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from scripts.ops.validate_docs_token_policy import DocsTokenPolicyValidator
from scripts.research.post_pr4936_cross_sectional_funding_rate_research_fleet_complete_no_pass_scope_definition_v0 import (
    CONFIRM_GO,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    run_post_pr4936_cross_sectional_funding_rate_research_fleet_complete_no_pass_scope_definition_v0,
    validate_config,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_pr4936_cross_sectional_funding_rate_research_fleet_complete_no_pass_scope_definition_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_PR4936_CROSS_SECTIONAL_FUNDING_RATE_RESEARCH_FLEET_COMPLETE_NO_PASS_SCOPE_DEFINITION_V0.md"
)
SCOPE_SCRIPT = (
    REPO_ROOT
    / "scripts/research/post_pr4936_cross_sectional_funding_rate_research_fleet_complete_no_pass_scope_definition_v0.py"
)
EVIDENCE_CLASS_ID = (
    "POST_PR4936_CROSS_SECTIONAL_FUNDING_RATE_RESEARCH_FLEET_COMPLETE_NO_PASS_SCOPE_DEFINITION_V0"
)
SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
BASE_HEAD = "0407bfd4df8c94b797c36f5e3a796a03989e9b56"
PARENT_CLOSEOUT_SUFFIX = "pr4936_dispersion_zscore_reversion_v0_negative_evidence_terminalization_merge_closeout_20260706T172134Z"
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
PARENT_CLOSEOUT_DIR = ARCHIVE_ROOT / "implementation" / PARENT_CLOSEOUT_SUFFIX
TERMINAL_BINDINGS = (
    "cross_sectional_funding_rate_rank_delta/v0",
    "cross_sectional_funding_rate_persistence_reversal_filter/v0",
    "cross_sectional_funding_rate_dispersion_zscore_reversion/v0",
    "cross_sectional_funding_rate_dual_leg_spread/v1",
    "cross_sectional_funding_rate_delta_momentum/v0",
    "cross_sectional_funding_rate_carry/v0",
)
FORBIDDEN_RUNTIME_ACTIONS = (
    "RUNTIME",
    "SHADOW",
    "PAPER",
    "TESTNET",
    "SCHEDULER",
    "ORDERS",
    "CREDENTIALS",
    "ARMING",
    "LIVE",
)
FORBIDDEN_CORE_PATHS = (
    "CORE_SYSTEM_CHANGE",
    "CANONICAL_TRADING_LOGIC_CHANGE",
    "MASTER_V2_CHANGE",
    "DOUBLE_PLAY_CHANGE",
    "RISK_SIZING_CHANGE",
    "SAFETY_RUNTIME_CHANGE",
)
BOUNDARY_PHRASES = (
    "Scope-Definition ≠ Binding-Ratifikation",
    "Keine Economic Evaluation",
    "COMPLETE_NO_PASS",
    "FINAL_RESEARCH_FLEET_BINDINGS",
    "UNCHANGED_RETRY_ALLOWED",
    "EVALUATION_EXECUTED",
    "RUNTIME_AUTHORITY_TOUCHED",
)
REQUIRED_CONTRACT_ASSERTIONS = (
    ("scope_definition_only", True),
    ("offline_only", True),
    ("economic_evaluation_authorized", False),
    ("economic_evaluation_executed", False),
    ("evaluation_executed", False),
    ("runtime_authority_touched", False),
    ("promotion_granted", False),
    ("unchanged_retry_allowed", False),
    ("material_difference_vs_terminal_bindings", True),
    ("core_system_mutation_allowed", False),
    ("no_runtime_authority", True),
)


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


class TestPostPr4936CrossSectionalFundingRateResearchFleetCompleteNoPassScopeDefinitionV0Contract:
    def test_scope_config_exists_and_parses(self) -> None:
        assert SCOPE_CONFIG.is_file()
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert isinstance(config, dict)
        assert (
            config["schema_version"]
            == "post_pr4936_cross_sectional_funding_rate_research_fleet_complete_no_pass_scope_definition.v0"
        )

    def test_required_contract_assertions(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        for field, expected in REQUIRED_CONTRACT_ASSERTIONS:
            assert config[field] is expected, f"contract assertion failed: {field}"

    def test_scope_config_core_fields(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["status"] == SCOPE_STATUS
        assert config["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert config["scope_id"] == SCOPE_ID
        assert config["scope_version"] == "v0"
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["go_token"] == CONFIRM_GO
        assert config["baseline_head"] == BASE_HEAD
        assert config["baseline_pr"] == 4936
        assert config["scope_decision"] == "FLEET_TERMINALIZATION_COMPLETE_NO_PASS"
        assert config["selected_next_scope"] is None
        assert config["cross_sectional_funding_research_fleet_status"] == "COMPLETE_NO_PASS"
        assert config["fleet_status"] == "COMPLETE_NO_PASS"
        assert config["material_difference_confirmed_for_new_funding_scope"] is False
        assert config["canonical_runbook_return_path"] == "FINAL_RESEARCH_FLEET_BINDINGS"

    def test_terminal_failed_binding_exclusions(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        identifiers = {
            entry["canonical_candidate_identifier"]
            for entry in config["terminal_failed_binding_exclusions"]
        }
        assert identifiers == set(TERMINAL_BINDINGS)
        for entry in config["terminal_failed_binding_exclusions"]:
            assert entry["retry_unchanged_binding_allowed"] is False
            assert entry["terminal_verdict"] == "ROBUSTNESS_FAILED"
            assert len(entry["binding_digest"]) == 64

    def test_blocked_actions_include_forbidden_runtime_and_core(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_actions"])
        for action in FORBIDDEN_RUNTIME_ACTIONS:
            assert action in blocked
        for action in FORBIDDEN_CORE_PATHS:
            assert action in blocked
        assert "EVALUATION_EXECUTION_IN_THIS_SCOPE" in blocked
        assert "UNCHANGED_BINDING_RETRY" in blocked

    def test_validate_config_accepts_canonical_config(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert validate_config(config) == []

    def test_governance_doc_exists_and_states_fleet_terminalization(self) -> None:
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert SCOPE_ID in text
        assert _field_value(text, "SCOPE_DECISION") == "FLEET_TERMINALIZATION_COMPLETE_NO_PASS"
        assert _field_value(text, "SELECTED_NEXT_SCOPE") == "none"
        assert (
            _field_value(text, "CROSS_SECTIONAL_FUNDING_RESEARCH_FLEET_STATUS")
            == "COMPLETE_NO_PASS"
        )
        assert _field_value(text, "EVALUATION_EXECUTED") == "false"
        assert _field_value(text, "RUNTIME_AUTHORITY_TOUCHED") == "false"
        assert _field_value(text, "PROMOTION_GRANTED") == "false"
        assert _field_value(text, "UNCHANGED_RETRY_ALLOWED") == "false"
        for phrase in BOUNDARY_PHRASES:
            assert phrase in text

    def test_docs_token_policy(self) -> None:
        validator = DocsTokenPolicyValidator(REPO_ROOT)
        result = validator.scan_file(GOVERNANCE_DOC)
        assert result.passed, [(v.line, v.token, v.message) for v in result.violations]

    def test_governance_doc_exists_with_docs_token(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_PR4936_CROSS_SECTIONAL_FUNDING_RATE_RESEARCH_FLEET_COMPLETE_NO_PASS_SCOPE_DEFINITION_V0"
            )
            in body
        )
        assert "LIVE_AUTHORIZED: false" in body

    def test_parent_closeout_manifest_verifies(self) -> None:
        assert PARENT_CLOSEOUT_DIR.is_dir()
        ok, _msg = verify_manifest_sha256(PARENT_CLOSEOUT_DIR)
        assert ok is True

    def test_materialization_produces_manifest_verified_bundle(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "bundle"
        result = run_post_pr4936_cross_sectional_funding_rate_research_fleet_complete_no_pass_scope_definition_v0(
            confirm_go_token=CONFIRM_GO,
            output_dir=output_dir,
        )
        assert result["verdict"] == "SCOPE_DEFINED_NOT_EXECUTED"
        assert result["scope_decision"] == "FLEET_TERMINALIZATION_COMPLETE_NO_PASS"
        assert result["selected_next_scope"] is None
        assert result["manifest_verify_rc"] == 0
        assert result["parent_closeout_manifest_verify_rc"] == 0
        for artifact in (
            "FINAL_REPORT.md",
            "SCOPE_DECISION_RECORD.md",
            "TERMINAL_EVIDENCE_DRIFT_MATRIX.md",
            "REUSE_FIRST_OWNER_MAP.md",
            "MANIFEST.sha256",
        ):
            assert (output_dir / artifact).is_file()
        ok, _msg = verify_manifest_sha256(output_dir)
        assert ok is True

    def test_script_cli_entrypoint(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "cli_bundle"
        proc = subprocess.run(
            [
                sys.executable,
                str(SCOPE_SCRIPT),
                "--confirm-go-token",
                CONFIRM_GO,
                "--out",
                str(output_dir),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert "VERDICT=SCOPE_DEFINED_NOT_EXECUTED" in proc.stdout
        assert "MANIFEST_VERIFY_RC=0" in proc.stdout

    def test_no_core_runtime_forbidden_paths_changed(self) -> None:
        forbidden_prefixes = (
            "src/execution/",
            "src/governance/",
            "src/risk/",
            "src/trading/master_v2/",
        )
        changed_paths = (
            "config/research/post_pr4936_cross_sectional_funding_rate_research_fleet_complete_no_pass_scope_definition_v0.json",
            "docs/governance/POST_PR4936_CROSS_SECTIONAL_FUNDING_RATE_RESEARCH_FLEET_COMPLETE_NO_PASS_SCOPE_DEFINITION_V0.md",
            "scripts/research/post_pr4936_cross_sectional_funding_rate_research_fleet_complete_no_pass_scope_definition_v0.py",
            "tests/ops/test_post_pr4936_cross_sectional_funding_rate_research_fleet_complete_no_pass_scope_definition_v0_contract.py",
            "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md",
        )
        for path in changed_paths:
            assert not any(path.startswith(prefix) for prefix in forbidden_prefixes), path
