"""Contract tests for post-PR4908 offline terminal failure artifact materialization v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from scripts.research.post_pr4908_offline_terminal_failure_artifact_materialization_v0 import (
    ARTIFACT_CLASSES,
    CONFIRM_GO,
    EXECUTION_ID,
    EXECUTION_STATUS,
    GLOBAL_MISSING_FIELDS,
    NEXT_CANONICAL_STEP,
    PARENT_PR4908_MERGE_COMMIT,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    run_offline_terminal_failure_artifact_materialization_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTION_CONFIG = (
    REPO_ROOT
    / "config/research/post_pr4908_offline_terminal_failure_artifact_materialization_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_PR4908_OFFLINE_TERMINAL_FAILURE_ARTIFACT_MATERIALIZATION_V0.md"
)
BASELINE_HEAD = "968308ae63c7c3b19b8632fce4fc5d2398dc4a81"
PARENT_PR4905_OUTPUT_SUFFIX = (
    "post_pr4904_v4_fleet_robustness_failure_decomposition_v0_20260706T042551Z"
)
PARENT_PR4905_CLOSEOUT_SUFFIX = "pr4905_squash_merge_closeout_20260706T043541Z"
PARENT_PR4906_CLOSEOUT_SUFFIX = (
    "post_pr4905_terminal_fleet_failure_next_scope_definition_merge_closeout_20260706T044625Z"
)
PARENT_PR4907_EVIDENCE_SUFFIX = (
    "post_pr4906_offline_only_terminal_fleet_failure_evidence_execution_v0_20260706T045000Z"
)
PARENT_PR4907_CLOSEOUT_SUFFIX = (
    "post_pr4906_offline_only_terminal_fleet_failure_evidence_execution_merge_closeout_"
    "20260706T045620Z"
)
PARENT_PR4908_CLOSEOUT_SUFFIX = "pr4908_squash_merge_closeout_20260706T050858Z"
PARENT_EVALUATION_SUFFIX = (
    "post_v4_versioned_fleet_offline_economic_evaluation_execution_v0_20260706T040339Z"
)
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
PARENT_PR4905_OUTPUT_BUNDLE = ARCHIVE_ROOT / "implementation" / PARENT_PR4905_OUTPUT_SUFFIX
PARENT_PR4905_CLOSEOUT_DIR = ARCHIVE_ROOT / "implementation" / PARENT_PR4905_CLOSEOUT_SUFFIX
PARENT_PR4906_CLOSEOUT_DIR = ARCHIVE_ROOT / "implementation" / PARENT_PR4906_CLOSEOUT_SUFFIX
PARENT_PR4907_EVIDENCE_BUNDLE = ARCHIVE_ROOT / "implementation" / PARENT_PR4907_EVIDENCE_SUFFIX
PARENT_PR4907_CLOSEOUT_DIR = ARCHIVE_ROOT / "implementation" / PARENT_PR4907_CLOSEOUT_SUFFIX
PARENT_PR4908_CLOSEOUT_DIR = ARCHIVE_ROOT / "implementation" / PARENT_PR4908_CLOSEOUT_SUFFIX
PARENT_EVALUATION_BUNDLE = ARCHIVE_ROOT / "implementation" / PARENT_EVALUATION_SUFFIX
REQUIRED_ARTIFACTS = (
    "parent_manifest_verification.json",
    "ARTIFACT_MATERIALIZATION_REPORT.json",
    "TRADE_LEDGER_LONG_SHORT_DECOMPOSITION_OFFLINE_ARTIFACT_V0.json",
    "TURNOVER_COST_DRAG_DECOMPOSITION_OFFLINE_ARTIFACT_V0.json",
    "INSTRUMENT_CONCENTRATION_DECOMPOSITION_OFFLINE_ARTIFACT_V0.json",
    "ARTIFACT_MATERIALIZATION_SUMMARY.tsv",
    "execution_summary.json",
    "EXECUTION_SUMMARY.md",
    "MANIFEST.sha256",
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
    "Keine neue Economic Evaluation",
    "FLEET_ECONOMIC_VALIDITY_FAIL",
    "FAILED_EVIDENCE_IS_TERMINAL=true",
    "UNCHANGED_RETRY_ALLOWED=false",
    "POLICY_THRESHOLD_RESCUE_ALLOWED=false",
    "MISSING_SOURCE_EVIDENCE",
    "NO_ECONOMIC_EVALUATION_EXECUTION_SCOPE=true",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostPr4908OfflineTerminalFailureArtifactMaterializationV0Contract:
    def test_scope_config_core_fields(self) -> None:
        config = json.loads(EXECUTION_CONFIG.read_text(encoding="utf-8"))
        assert config["status"] == EXECUTION_STATUS
        assert config["evidence_class_id"] == EXECUTION_ID
        assert config["scope_id"] == SCOPE_ID
        assert config["execution_id"] == EXECUTION_ID
        assert config["selected_class"] == "I"
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["go_token"] == CONFIRM_GO
        assert config["baseline_head"] == BASELINE_HEAD
        assert config["parent_pr4907_aggregate_result"] == "FLEET_ECONOMIC_VALIDITY_FAIL"
        assert config["failed_evidence_is_terminal"] is True
        assert config["economic_validity_offline_gate_pass"] is False
        assert config["offline_evaluation_executed"] is False
        assert config["new_economic_evaluation_executed"] is False
        assert config["economic_evaluation_executed"] is False
        assert config["backtest_executed"] is False
        assert config["unchanged_retry_allowed"] is False
        assert config["policy_threshold_rescue_allowed"] is False
        assert config["runtime_rewire_admissible"] is False
        assert config["runtime_authority_created"] is False
        assert config["artifact_classes_targeted"] == list(ARTIFACT_CLASSES)

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_PR4908_OFFLINE_TERMINAL_FAILURE_ARTIFACT_MATERIALIZATION_V0"
            )
            in body
        )
        assert f"`GO_TOKEN` | `{CONFIRM_GO}`" in body
        assert "`FAILED_EVIDENCE_IS_TERMINAL` | `true`" in body
        assert "`OFFLINE_EVALUATION_EXECUTED` | `false`" in body
        assert "`NEW_ECONOMIC_EVALUATION_EXECUTED` | `false`" in body

    def test_governance_doc_boundary_phrases(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body

    def test_governance_doc_forbidden_runtime_actions(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for action in FORBIDDEN_RUNTIME_ACTIONS:
            assert action in body

    def test_governance_doc_next_scope_go(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert _field_value(body, "REQUIRED_NEXT_GO_FOR_SCOPE_DEFINITION") == NEXT_CANONICAL_STEP

    def test_parent_evidence_refs_present(self) -> None:
        config = json.loads(EXECUTION_CONFIG.read_text(encoding="utf-8"))
        assert PARENT_PR4908_CLOSEOUT_SUFFIX in config["parent_pr4908_closeout_dir"]
        assert PARENT_PR4907_EVIDENCE_SUFFIX in config["parent_pr4907_evidence_bundle"]
        assert PARENT_EVALUATION_SUFFIX in config["parent_evaluation_bundle_ref"]
        assert config["parent_pr4908_merge_commit"] == PARENT_PR4908_MERGE_COMMIT

    @pytest.mark.parametrize(
        "parent_path",
        [
            PARENT_PR4905_OUTPUT_BUNDLE,
            PARENT_PR4905_CLOSEOUT_DIR,
            PARENT_PR4906_CLOSEOUT_DIR,
            PARENT_PR4907_EVIDENCE_BUNDLE,
            PARENT_PR4907_CLOSEOUT_DIR,
            PARENT_PR4908_CLOSEOUT_DIR,
            PARENT_EVALUATION_BUNDLE,
        ],
    )
    def test_parent_manifests_verify(self, parent_path: Path) -> None:
        ok, _msg = verify_manifest_sha256(parent_path)
        assert ok, f"parent manifest invalid: {parent_path}"

    def test_runner_materializes_required_artifacts(self) -> None:
        result = run_offline_terminal_failure_artifact_materialization_v0(
            go_token=CONFIRM_GO,
            parent_pr4905_output_bundle=PARENT_PR4905_OUTPUT_BUNDLE,
            parent_pr4905_closeout_dir=PARENT_PR4905_CLOSEOUT_DIR,
            parent_pr4906_closeout_dir=PARENT_PR4906_CLOSEOUT_DIR,
            parent_pr4907_evidence_bundle=PARENT_PR4907_EVIDENCE_BUNDLE,
            parent_pr4907_closeout_dir=PARENT_PR4907_CLOSEOUT_DIR,
            parent_pr4908_closeout_dir=PARENT_PR4908_CLOSEOUT_DIR,
            parent_evaluation_bundle=PARENT_EVALUATION_BUNDLE,
        )
        output_dir = Path(result["durable_evidence_path"])
        assert result["verdict"] == EXECUTION_STATUS
        assert result["manifest_verify_rc"] == 0
        assert result["artifact_classes_materialized"] == list(ARTIFACT_CLASSES)
        assert result["missing_source_evidence"] == list(GLOBAL_MISSING_FIELDS)
        for artifact_name in REQUIRED_ARTIFACTS:
            assert (output_dir / artifact_name).is_file(), artifact_name
        ok, _msg = verify_manifest_sha256(output_dir)
        assert ok
        payload = json.loads(
            (
                output_dir / "TRADE_LEDGER_LONG_SHORT_DECOMPOSITION_OFFLINE_ARTIFACT_V0.json"
            ).read_text(encoding="utf-8")
        )
        assert payload["materialization_status"] == "PARTIAL_BOUND_FROM_PARENT_EVIDENCE"
        for candidate in ("trend_following", "bollinger_bands", "momentum_1h"):
            ledger = payload["per_candidate"][candidate]["trade_ledger_decomposition"]
            assert ledger["status"] == "MISSING_SOURCE_EVIDENCE"
