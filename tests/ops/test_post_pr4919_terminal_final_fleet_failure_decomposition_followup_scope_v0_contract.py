"""Contract tests for post-PR4919 terminal final fleet failure decomposition follow-up scope v0."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from scripts.ops.validate_docs_token_policy import DocsTokenPolicyValidator
from scripts.research.post_pr4919_terminal_final_fleet_failure_decomposition_followup_scope_v0 import (
    GO_TOKEN,
    NEXT_STEP,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    run_post_pr4919_terminal_final_fleet_failure_decomposition_followup_scope_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_pr4919_terminal_final_fleet_failure_decomposition_followup_scope_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_PR4919_TERMINAL_FINAL_FLEET_FAILURE_DECOMPOSITION_FOLLOWUP_SCOPE_V0.md"
)
SCOPE_SCRIPT = (
    REPO_ROOT
    / "scripts/research/post_pr4919_terminal_final_fleet_failure_decomposition_followup_scope_v0.py"
)
EVIDENCE_CLASS_ID = "POST_PR4919_TERMINAL_FINAL_FLEET_FAILURE_DECOMPOSITION_FOLLOWUP_SCOPE_V0"
SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
BASE_HEAD = "6c11561db1a26893d5b318394bd78335659991e3"
PRE_MERGE_HEAD = "e5eafea28a96dcfdbb46593bea03b8769d5c3a4e"
PR_HEAD = "fe9967de033db0171a0b2f874bb36eb2cfe225fd"
POST_MERGE_HEAD = "6c11561db1a26893d5b318394bd78335659991e3"
PARENT_CLOSEOUT_SUFFIX = (
    "pr4919_terminal_final_fleet_failure_decomposition_next_scope_merge_closeout_20260706T075014Z"
)
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
PARENT_CLOSEOUT_DIR = ARCHIVE_ROOT / "implementation" / PARENT_CLOSEOUT_SUFFIX
FLEET_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
FOLLOWUP_TAXONOMY_CLASS_IDS = (
    "EVIDENCE_ADEQUACY_GAPS",
    "FEATURE_EDGE_FAILURE_CLASS",
    "TURNOVER_COST_DRAG_CLASS",
    "DRAWDOWN_TAIL_RISK_CLASS",
    "REGIME_INSTABILITY_CLASS",
    "WALK_FORWARD_OOS_INSTABILITY_CLASS",
    "MONTE_CARLO_STRESS_WEAKNESS_CLASS",
    "PORTFOLIO_CONTRIBUTION_WEAKNESS_CLASS",
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
BOUNDARY_PHRASES = (
    "Scope-Definition ≠ Evidence-Execution",
    "Keine Economic Evaluation",
    "FLEET_ECONOMIC_VALIDITY_FAIL",
    "retry_unchanged_binding_allowed",
    "operator_override_allowed",
    "governance_wording_override_allowed",
    "FAILED_EVIDENCE_IS_TERMINAL=true",
    "PROMOTION_ADMISSIBLE",
    "RUNTIME_REWIRE_ADMISSIBLE",
    "POLICY_CHANGE_TO_RECLASSIFY_NEGATIVE_EVIDENCE",
    "NEW_CANDIDATE_RATIFIED",
    "nicht Rerun",
)
REQUIRED_BUNDLE_ARTIFACTS = (
    "FOLLOWUP_SCOPE_SUMMARY.json",
    "AUTHORITY_BOUNDARY.json",
    "FAILURE_TAXONOMY.json",
    "MANIFEST.sha256",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostPr4919TerminalFinalFleetFailureDecompositionFollowupScopeV0Contract:
    def test_scope_config_exists_and_parses(self) -> None:
        assert SCOPE_CONFIG.is_file()
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert isinstance(config, dict)
        assert config["schema_version"] == (
            "post_pr4919_terminal_final_fleet_failure_decomposition_followup_scope.v0"
        )

    def test_scope_config_core_fields(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["status"] == SCOPE_STATUS
        assert config["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert config["scope_id"] == SCOPE_ID
        assert config["scope_version"] == "v0"
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["go_token"] == GO_TOKEN
        assert config["base_head"] == BASE_HEAD
        assert config["parent_pr"] == 4919
        assert config["pre_merge_head"] == PRE_MERGE_HEAD
        assert config["pr_head"] == PR_HEAD
        assert config["post_merge_head"] == POST_MERGE_HEAD
        assert config["fleet_verdict"] == "FLEET_ECONOMIC_VALIDITY_FAIL"
        assert config["economic_validity_offline_gate_pass"] is False
        assert config["promotion_admissible"] is False
        assert config["runtime_rewire_admissible"] is False
        assert config["operator_go_required_for_next_scope"] is True
        assert config["next_step"] == NEXT_STEP

    def test_required_machine_readable_sections(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert isinstance(config["allowed_actions"], list) and config["allowed_actions"]
        assert isinstance(config["forbidden_actions"], list) and config["forbidden_actions"]
        assert isinstance(config["terminal_failure_inputs"], dict)
        assert isinstance(config["followup_taxonomy"], list)
        assert isinstance(config["required_final_report_fields"], list)
        assert "VERDICT" in config["required_final_report_fields"]
        assert "NEXT_STEP" in config["required_final_report_fields"]

    def test_followup_taxonomy_classes(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        class_ids = [entry["class_id"] for entry in config["followup_taxonomy"]]
        assert class_ids == list(FOLLOWUP_TAXONOMY_CLASS_IDS)
        for entry in config["followup_taxonomy"]:
            assert entry["admissible_followup_question"]
            assert entry["explicitly_non_admissible_automatic_action"]
            assert entry["fleet_level_diagnosis"]

    def test_failed_bindings_no_unchanged_retry(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["retry_unchanged_binding_allowed"] is False
        assert config["same_binding_retry_allowed"] is False
        assert config["unchanged_retry_allowed"] is False
        assert config["failed_bindings_retry_allowed"] is False
        for binding in config["failed_bindings"]:
            assert binding["retry_unchanged_binding_allowed"] is False
            assert binding["promotion_admissible"] is False

    def test_no_new_candidate_ratified(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["new_candidate_ratified"] is False
        assert config["new_candidates_ratified"] is False

    def test_no_evaluation_or_runtime_authority(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["economic_evaluation_authorized"] is False
        assert config["runtime_authority_created"] is False
        assert config["runtime_authority"] == "NONE"
        assert config["no_evaluation_authority"] is True
        assert config["no_runtime_authority"] is True

    def test_forbidden_actions_present(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        forbidden = set(config["forbidden_actions"])
        for action in (
            "ECONOMIC_EVALUATION_EXECUTION",
            "NEW_CANDIDATE_RATIFICATION",
            "SAME_BINDING_RETRY",
            "PARAMETER_OPTIMIZATION",
            "THRESHOLD_LOWERING",
            "POLICY_THRESHOLD_RESCUE",
            "RUNTIME_REWIRE",
            *FORBIDDEN_RUNTIME_ACTIONS,
        ):
            assert action in forbidden

    def test_failed_bindings_candidate_summaries(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        by_id = {b["canonical_candidate_identifier"]: b for b in config["failed_bindings"]}
        assert by_id["trend_following/v1"]["net_return"] == -0.002398
        assert by_id["trend_following/v1"]["profit_factor"] == 0.951
        assert by_id["trend_following/v1"]["max_drawdown"] == -0.009945
        assert by_id["trend_following/v1"]["classified_verdict"] == "ROBUSTNESS_FAILED"
        assert by_id["bollinger_bands/v1"]["raw_evidence_status"] == "RESEARCH_ONLY"
        assert by_id["bollinger_bands/v1"]["classified_verdict"] == "ROBUSTNESS_FAILED"
        assert by_id["momentum_1h/v1"]["net_return"] == -0.001889
        assert by_id["momentum_1h/v1"]["profit_factor"] == 0.285
        assert by_id["momentum_1h/v1"]["max_drawdown"] == -0.002638

    def test_parent_closeout_ref_present(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert PARENT_CLOSEOUT_SUFFIX in config["parent_closeout_dir"]
        assert config["parent_closeout_manifest_verify_rc"] == 0

    def test_final_research_fleet(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["final_research_fleet"] == list(FLEET_CANDIDATES)
        assert config["strategy_version"] == "v1"

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_PR4919_TERMINAL_FINAL_FLEET_FAILURE_DECOMPOSITION_FOLLOWUP_SCOPE_V0"
            )
            in body
        )
        assert "LIVE_AUTHORIZED: false" in body
        assert "`FLEET_VERDICT` | `FLEET_ECONOMIC_VALIDITY_FAIL`" in body
        assert "`ECONOMIC_EVALUATION_AUTHORIZED` | `false`" in body
        assert "`RUNTIME_AUTHORITY_CREATED` | `false`" in body
        assert "`NEW_CANDIDATE_RATIFIED` | `false`" in body
        assert "`PROMOTION_ADMISSIBLE` | `false`" in body
        assert "`RUNTIME_REWIRE_ADMISSIBLE` | `false`" in body
        assert PRE_MERGE_HEAD in body
        assert PR_HEAD in body
        assert POST_MERGE_HEAD in body
        assert PARENT_CLOSEOUT_SUFFIX in body

    def test_governance_doc_boundary_phrases(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body

    def test_governance_doc_forbidden_runtime_actions(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for action in FORBIDDEN_RUNTIME_ACTIONS:
            assert action in body

    def test_governance_doc_next_step(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert _field_value(body, "NEXT_STEP") == NEXT_STEP
        assert _field_value(body, "OPERATOR_GO_REQUIRED_FOR_NEXT_SCOPE") == "true"

    def test_scope_is_definition_only_not_execution(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["non_authorizing"] is True
        assert config["offline_only"] is True
        assert config["repo_mutation_scope"] == "GOVERNANCE_ONLY"
        assert config["evidence_execution_executed"] is False

    def test_terminality_flags(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["failed_evidence_is_terminal"] is True
        assert config["operator_override_allowed"] is False
        assert config["governance_wording_override_allowed"] is False
        assert config["policy_threshold_rescue_allowed"] is False

    def test_authority_flags_explicitly_false(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["shadow_authorized"] is False
        assert config["paper_authorized"] is False
        assert config["testnet_authorized"] is False
        assert config["live_authorized"] is False
        assert config["promotion_authority"] is False
        assert config["orders_allowed"] is False

    def test_mutation_flags_all_false(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["core_system_mutation_allowed"] is False
        assert config["double_play_mutation_allowed"] is False
        assert config["risk_sizing_mutation_allowed"] is False
        assert config["safety_runtime_mutation_allowed"] is False

    def test_script_has_no_forbidden_imports(self) -> None:
        body = SCOPE_SCRIPT.read_text(encoding="utf-8")
        forbidden_import_re = re.compile(
            r"^\s*(from|import)\s+"
            r"src\.(execution|live|scheduler|adapters|broker|exchange|order|shadow|paper|testnet|credentials)"
        )
        for line in body.splitlines():
            assert not forbidden_import_re.match(line), line

    def test_docs_token_policy_passes_for_governance_doc(self) -> None:
        validator = DocsTokenPolicyValidator(REPO_ROOT)
        result = validator.scan_file(GOVERNANCE_DOC)
        assert result.passed, [(v.line, v.token, v.message) for v in result.violations]

    def test_docs_reference_targets_for_governance_doc(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for match in re.finditer(r"`((?:config|docs)/[^`]+)`", body):
            target = REPO_ROOT / match.group(1)
            assert target.is_file(), match.group(1)

    @pytest.mark.parametrize("parent_path", [PARENT_CLOSEOUT_DIR])
    def test_parent_closeout_manifest_verifies(self, parent_path: Path) -> None:
        if not parent_path.is_dir():
            pytest.skip(f"parent closeout dir unavailable: {parent_path}")
        ok, _msg = verify_manifest_sha256(parent_path)
        assert ok, f"parent manifest invalid: {parent_path}"

    def test_runner_materializes_required_artifacts(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "bundle_a"
        result = run_post_pr4919_terminal_final_fleet_failure_decomposition_followup_scope_v0(
            output_dir=output_dir,
        )
        assert result["verdict"] == SCOPE_STATUS
        assert result["manifest_verify_rc"] == 0
        for artifact_name in REQUIRED_BUNDLE_ARTIFACTS:
            assert (output_dir / artifact_name).is_file(), artifact_name
        ok, _msg = verify_manifest_sha256(output_dir)
        assert ok

        authority = json.loads((output_dir / "AUTHORITY_BOUNDARY.json").read_text(encoding="utf-8"))
        assert authority["economic_evaluation_authorized"] is False
        assert authority["new_candidate_ratified"] is False
        assert authority["runtime_authority_created"] is False
        assert authority["operator_go_required_for_next_scope"] is True

        taxonomy = json.loads((output_dir / "FAILURE_TAXONOMY.json").read_text(encoding="utf-8"))
        assert taxonomy["not_a_new_candidate"] is True
        assert taxonomy["not_a_rerun"] is True
        assert taxonomy["next_step"] == NEXT_STEP

    def test_runner_output_is_deterministic(self, tmp_path: Path) -> None:
        output_a = tmp_path / "bundle_a"
        output_b = tmp_path / "bundle_b"
        run_post_pr4919_terminal_final_fleet_failure_decomposition_followup_scope_v0(
            output_dir=output_a,
        )
        run_post_pr4919_terminal_final_fleet_failure_decomposition_followup_scope_v0(
            output_dir=output_b,
        )
        for artifact in (
            "FOLLOWUP_SCOPE_SUMMARY.json",
            "AUTHORITY_BOUNDARY.json",
            "FAILURE_TAXONOMY.json",
        ):
            assert (output_a / artifact).read_bytes() == (output_b / artifact).read_bytes()

    def test_cli_entrypoint(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "cli_bundle"
        proc = subprocess.run(
            [
                sys.executable,
                str(SCOPE_SCRIPT),
                "--config",
                str(SCOPE_CONFIG),
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
        assert (output_dir / "MANIFEST.sha256").is_file()
