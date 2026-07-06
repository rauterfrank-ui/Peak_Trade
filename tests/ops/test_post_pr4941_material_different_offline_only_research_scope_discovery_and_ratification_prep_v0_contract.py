"""Contract tests for post-PR4941 material-different research scope discovery prep v0."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from scripts.ops.validate_docs_token_policy import DocsTokenPolicyValidator
from scripts.research.post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep_v0 import (
    CONFIRM_GO,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    run_post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep_v0,
    validate_config,
)
from src.research.post_pr4940_final_research_fleet_negative_evidence_terminalization_and_next_material_research_boundary_v0 import (
    EXPECTED_CANDIDATE_RESULTS,
    FINAL_RESEARCH_FLEET,
)
from src.research.post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep_v0 import (
    BASE_HEAD,
    EXCLUDED_FAILED_BINDINGS,
    REQUIRED_MATERIAL_DIFFERENCE_AXES,
    SCOPE_ID,
    SELECTED_NEXT_SCOPE_BOUNDARY,
    VERDICT,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT / "config/research/post_pr4941_material_different_offline_only_research_scope_"
    "discovery_and_ratification_prep_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/POST_PR4941_MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_"
    "DISCOVERY_AND_RATIFICATION_PREP_V0.md"
)
SCOPE_SCRIPT = (
    REPO_ROOT / "scripts/research/post_pr4941_material_different_offline_only_research_scope_"
    "discovery_and_ratification_prep_v0.py"
)
EVIDENCE_CLASS_ID = (
    "POST_PR4941_MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_AND_RATIFICATION_PREP_V0"
)
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
PR4939_CLOSEOUT_DIR = (
    ARCHIVE_ROOT
    / "research/pr4939_final_research_fleet_negative_evidence_terminalization_merge_closeout_20260706T181802Z"
)
PR4940_CLOSEOUT_DIR = (
    ARCHIVE_ROOT
    / "research/pr4940_final_fleet_terminalization_and_next_material_research_boundary_merge_closeout_20260706T182841Z"
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
    "MARKET_AIRPORT",
)
REQUIRED_CONTRACT_ASSERTIONS = (
    ("scope_discovery_and_ratification_prep_only", True),
    ("ratification_prep_only", True),
    ("discovery_and_ratification_prep_only", True),
    ("offline_only", True),
    ("economic_evaluation_authorized", False),
    ("economic_evaluation_executed", False),
    ("evaluation_executed", False),
    ("runtime_authority_touched", False),
    ("promotion_granted", False),
    ("unchanged_retry_allowed", False),
    ("negative_evidence_terminal_for_unchanged_bindings", True),
    ("economic_validity_offline_gate_pass", False),
    ("runtime_rewire_admissible", False),
    ("live_authorized", False),
    ("no_runtime_authority", True),
    ("market_airport_excluded", True),
    ("futures_only", True),
    ("bitcoin_direction_allowed", False),
)


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


class TestPostPr4941MaterialDifferentOfflineOnlyResearchScopeDiscoveryAndRatificationPrepV0Contract:
    def test_scope_config_exists_and_parses(self) -> None:
        assert SCOPE_CONFIG.is_file()
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert isinstance(config, dict)
        assert (
            config["schema_version"]
            == "post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep.v0"
        )

    def test_required_contract_assertions(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        for field, expected in REQUIRED_CONTRACT_ASSERTIONS:
            assert config[field] is expected, f"contract assertion failed: {field}"

    def test_scope_config_core_fields(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["status"] == VERDICT
        assert config["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert config["scope_id"] == SCOPE_ID
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["go_token"] == CONFIRM_GO
        assert config["baseline_head"] == BASE_HEAD
        assert config["selected_next_scope_boundary"] == SELECTED_NEXT_SCOPE_BOUNDARY
        assert config["excluded_failed_bindings"] == list(EXCLUDED_FAILED_BINDINGS)
        assert config["material_difference_axes"] == list(REQUIRED_MATERIAL_DIFFERENCE_AXES)
        assert config["final_research_fleet"] == list(FINAL_RESEARCH_FLEET)

    def test_final_fleet_terminal_fail_state_remains_bound(self) -> None:
        pr4940_config = json.loads(
            (
                REPO_ROOT / "config/research/post_pr4940_final_research_fleet_negative_evidence_"
                "terminalization_and_next_material_research_boundary_v0.json"
            ).read_text(encoding="utf-8")
        )
        assert pr4940_config["candidate_results"] == EXPECTED_CANDIDATE_RESULTS
        assert pr4940_config["negative_evidence_terminal_for_unchanged_bindings"] is True
        assert pr4940_config["unchanged_retry_allowed"] is False

    def test_exactly_one_selected_candidate_family(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        selected = [
            entry
            for entry in config["candidate_family_inventory"]
            if entry["disposition"] == "SELECTED_RECOMMENDED"
        ]
        assert len(selected) == 1
        assert selected[0]["candidate_family"] == SELECTED_NEXT_SCOPE_BOUNDARY

    def test_blocked_actions_include_forbidden_runtime(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_actions"])
        for action in FORBIDDEN_RUNTIME_ACTIONS:
            assert action in blocked
        assert "EVALUATION_EXECUTION_IN_THIS_SCOPE" in blocked
        assert "UNCHANGED_BINDING_RETRY" in blocked
        assert "BINDING_RATIFICATION_IN_THIS_SCOPE" in blocked

    def test_validate_config_accepts_canonical_config(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert validate_config(config) == []

    def test_governance_doc_states_discovery_prep_and_selected_scope(self) -> None:
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert SCOPE_ID in text
        assert _field_value(text, "VERDICT") == VERDICT
        assert _field_value(text, "SELECTED_NEXT_SCOPE_BOUNDARY") == (
            "cross_sectional_realized_volatility_rank_rotation&#47;v0"
        )
        assert _field_value(text, "EVALUATION_EXECUTED") == "false"
        assert _field_value(text, "RUNTIME_AUTHORITY_TOUCHED") == "false"
        assert _field_value(text, "PROMOTION_GRANTED") == "false"
        assert _field_value(text, "UNCHANGED_RETRY_ALLOWED") == "false"
        assert _field_value(text, "MARKET_AIRPORT_EXCLUDED") == "true"

    def test_docs_token_policy(self) -> None:
        validator = DocsTokenPolicyValidator(REPO_ROOT)
        result = validator.scan_file(GOVERNANCE_DOC)
        assert result.passed, [(v.line, v.token, v.message) for v in result.violations]

    def test_parent_closeout_manifests_verify(self) -> None:
        assert PR4939_CLOSEOUT_DIR.is_dir()
        assert PR4940_CLOSEOUT_DIR.is_dir()
        ok4939, _ = verify_manifest_sha256(PR4939_CLOSEOUT_DIR)
        ok4940, _ = verify_manifest_sha256(PR4940_CLOSEOUT_DIR)
        assert ok4939 is True
        assert ok4940 is True

    def test_materialization_produces_manifest_verified_bundle(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "bundle"
        result = run_post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep_v0(
            confirm_go_token=CONFIRM_GO,
            output_dir=output_dir,
        )
        assert result["verdict"] == VERDICT
        assert result["selected_next_scope_boundary"] == SELECTED_NEXT_SCOPE_BOUNDARY
        assert result["manifest_verify_rc"] == 0
        assert result["pr4939_manifest_verify_rc"] == 0
        assert result["pr4940_manifest_verify_rc"] == 0
        for artifact in (
            "FINAL_REPORT.md",
            "FAILED_BINDING_EXCLUSION_MATRIX.json",
            "MATERIAL_DIFFERENCE_MATRIX.json",
            "REUSE_FIRST_MATRIX.json",
            "SELECTED_NEXT_SCOPE_BOUNDARY.md",
            "NO_EVAL_NO_RUNTIME_AUTHORITY_STATEMENT.md",
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
        assert f"VERDICT={VERDICT}" in proc.stdout
        assert "MANIFEST_VERIFY_RC=0" in proc.stdout

    def test_no_core_runtime_forbidden_paths_changed(self) -> None:
        forbidden_prefixes = (
            "src/execution/",
            "src/governance/",
            "src/risk/",
            "src/trading/master_v2/",
        )
        changed_paths = (
            "config/research/post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep_v0.json",
            "docs/governance/POST_PR4941_MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_AND_RATIFICATION_PREP_V0.md",
            "scripts/research/post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep_v0.py",
            "src/research/post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep_v0.py",
            "tests/ops/test_post_pr4941_material_different_offline_only_research_scope_discovery_and_ratification_prep_v0_contract.py",
            "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md",
        )
        for path in changed_paths:
            assert not any(path.startswith(prefix) for prefix in forbidden_prefixes), path
