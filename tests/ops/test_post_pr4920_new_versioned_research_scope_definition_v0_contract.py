"""Contract tests for post-PR4920 new versioned research scope definition v0."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from scripts.ops.validate_docs_token_policy import DocsTokenPolicyValidator
from scripts.research.post_pr4920_new_versioned_research_scope_definition_v0 import (
    CONFIRM_GO,
    NEXT_STEP,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    run_post_pr4920_new_versioned_research_scope_definition_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT / "config/research/post_pr4920_new_versioned_research_scope_definition_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/POST_PR4920_NEW_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0.md"
)
SCOPE_SCRIPT = (
    REPO_ROOT / "scripts/research/post_pr4920_new_versioned_research_scope_definition_v0.py"
)
EVIDENCE_CLASS_ID = "POST_PR4920_NEW_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0"
SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
BASE_HEAD = "aa53ee580257b8d937a19c5172e98b7d16544221"
PARENT_DECOMPOSITION_SUFFIX = (
    "post_pr4920_failure_decomposition_followup_execution_offline_only_20260706T080836Z"
)
PARENT_CLOSEOUT_SUFFIX = "pr4920_post_pr4919_terminal_final_fleet_failure_decomposition_followup_scope_merge_closeout_20260706T080500Z"
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
PARENT_DECOMPOSITION_DIR = ARCHIVE_ROOT / "implementation" / PARENT_DECOMPOSITION_SUFFIX
PARENT_CLOSEOUT_DIR = ARCHIVE_ROOT / "implementation" / PARENT_CLOSEOUT_SUFFIX
EXCLUDED_BINDINGS = ("trend_following/v1", "bollinger_bands/v1", "momentum_1h/v1")
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
    "Scope-Definition ≠ Binding-Ratifikation",
    "Keine Economic Evaluation",
    "FLEET_ECONOMIC_VALIDITY_FAIL",
    "FAILED_BINDINGS_EXCLUDED",
    "NO_ORDER_AUTHORITY",
    "retry_unchanged_binding_allowed",
    "SEPARATE_OPERATOR_GO_REQUIRED_FOR_VERSIONED_BINDINGS_OR_OFFLINE_EVALUATION",
    "nicht retry-fähig",
)
REQUIRED_BUNDLE_ARTIFACTS = (
    "SCOPE_DEFINITION_SUMMARY.json",
    "AUTHORITY_BOUNDARY.json",
    "FAILURE_TAXONOMY.json",
    "MANIFEST.sha256",
)
REQUIRED_CONTRACT_ASSERTIONS = (
    ("scope_definition_only", True),
    ("economic_evaluation_authorized", False),
    ("retry_authorized", False),
    ("runtime_rewire_admissible", False),
    ("promotion_admissible", False),
    ("failed_bindings_excluded", True),
    ("core_system_mutation_allowed", False),
    ("canonical_trading_logic_mutation_allowed", False),
    ("master_v2_mutation_allowed", False),
    ("double_play_mutation_allowed", False),
    ("safety_runtime_mutation_allowed", False),
    ("no_order_authority", True),
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostPr4920NewVersionedResearchScopeDefinitionV0Contract:
    def test_scope_config_exists_and_parses(self) -> None:
        assert SCOPE_CONFIG.is_file()
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert isinstance(config, dict)
        assert config["schema_version"] == "post_pr4920_new_versioned_research_scope_definition.v0"

    def test_required_contract_assertions(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        for field, expected in REQUIRED_CONTRACT_ASSERTIONS:
            assert config[field] is expected, f"contract assertion failed: {field}"
        assert config["next_step"] == NEXT_STEP

    def test_scope_config_core_fields(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["status"] == SCOPE_STATUS
        assert config["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert config["scope_id"] == SCOPE_ID
        assert config["scope_version"] == "v0"
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["go_token"] == CONFIRM_GO
        assert config["base_head"] == BASE_HEAD
        assert config["baseline_pr"] == 4920
        assert config["fleet_verdict"] == "FLEET_ECONOMIC_VALIDITY_FAIL"
        assert config["economic_validity_offline_gate_pass"] is False
        assert config["operator_go_required_for_next_scope"] is True

    def test_excluded_failed_bindings(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["failed_bindings_excluded"] is True
        assert set(config["excluded_failed_bindings"]) == set(EXCLUDED_BINDINGS)
        for binding in config["failed_bindings"]:
            identifier = binding["canonical_candidate_identifier"]
            assert identifier in EXCLUDED_BINDINGS
            assert binding["retry_unchanged_binding_allowed"] is False

    def test_followup_taxonomy_classes(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        class_ids = [entry["class_id"] for entry in config["followup_taxonomy"]]
        assert class_ids == list(FOLLOWUP_TAXONOMY_CLASS_IDS)

    def test_candidate_archetype_requirements(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        archetypes = config["candidate_archetype_requirements"]
        assert len(archetypes) == 3
        replaces = {entry["replaces_binding"] for entry in archetypes}
        assert replaces == set(EXCLUDED_BINDINGS)

    def test_forbidden_actions_present(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        forbidden = set(config["forbidden_actions"])
        for action in (
            "ECONOMIC_EVALUATION_EXECUTION",
            "SAME_BINDING_RETRY",
            "PARAMETER_OPTIMIZATION",
            "THRESHOLD_LOWERING",
            "RUNTIME_REWIRE",
            *FORBIDDEN_RUNTIME_ACTIONS,
        ):
            assert action in forbidden

    def test_blocked_scope_classes(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_scope_classes"])
        assert "A_UNMODIFIED_V1_BINDING_REEXECUTION" in blocked
        assert "G_RUNTIME_REWIRE" in blocked

    def test_parent_evidence_refs_present(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert PARENT_DECOMPOSITION_SUFFIX in config["parent_decomposition_evidence_ref"]
        assert PARENT_CLOSEOUT_SUFFIX in config["parent_closeout_dir"]
        assert config["parent_decomposition_manifest_verify_rc"] == 0
        assert config["parent_closeout_manifest_verify_rc"] == 0

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker("DOCS_TOKEN_POST_PR4920_NEW_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0")
            in body
        )
        assert "LIVE_AUTHORIZED: false" in body
        assert "`FLEET_VERDICT` | `FLEET_ECONOMIC_VALIDITY_FAIL`" in body
        assert "`SCOPE_DEFINITION_ONLY` | `true`" in body
        assert "`FAILED_BINDINGS_EXCLUDED` | `true`" in body
        assert "`NO_ORDER_AUTHORITY` | `true`" in body
        assert "`ECONOMIC_EVALUATION_AUTHORIZED` | `false`" in body
        assert "`RETRY_AUTHORIZED` | `false`" in body

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

    def test_scope_is_definition_only_not_execution(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["non_authorizing"] is True
        assert config["offline_only"] is True
        assert config["repo_mutation_scope"] == "GOVERNANCE_ONLY"
        assert config["economic_evaluation_executed"] is False

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

    @pytest.mark.parametrize("parent_path", [PARENT_DECOMPOSITION_DIR, PARENT_CLOSEOUT_DIR])
    def test_parent_manifest_verifies(self, parent_path: Path) -> None:
        if not parent_path.is_dir():
            pytest.skip(f"parent bundle unavailable: {parent_path}")
        ok, _msg = verify_manifest_sha256(parent_path)
        assert ok, f"parent manifest invalid: {parent_path}"

    def test_runner_materializes_required_artifacts(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "bundle_a"
        result = run_post_pr4920_new_versioned_research_scope_definition_v0(
            output_dir=output_dir,
        )
        assert result["verdict"] == SCOPE_STATUS
        assert result["manifest_verify_rc"] == 0
        for artifact_name in REQUIRED_BUNDLE_ARTIFACTS:
            assert (output_dir / artifact_name).is_file(), artifact_name
        ok, _msg = verify_manifest_sha256(output_dir)
        assert ok

        authority = json.loads((output_dir / "AUTHORITY_BOUNDARY.json").read_text(encoding="utf-8"))
        assert authority["scope_definition_only"] is True
        assert authority["failed_bindings_excluded"] is True
        assert authority["no_order_authority"] is True
        assert authority["retry_authorized"] is False
        assert authority["promotion_admissible"] is False

        taxonomy = json.loads((output_dir / "FAILURE_TAXONOMY.json").read_text(encoding="utf-8"))
        assert taxonomy["not_a_new_candidate"] is True
        assert taxonomy["not_a_rerun"] is True
        assert taxonomy["next_step"] == NEXT_STEP
        assert set(taxonomy["excluded_failed_bindings"]) == set(EXCLUDED_BINDINGS)

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
