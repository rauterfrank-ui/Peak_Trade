"""Contract tests for post-PR4906 offline-only terminal fleet failure evidence execution v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from scripts.research.post_pr4906_offline_only_terminal_fleet_failure_evidence_execution_v0 import (
    CONFIRM_GO,
    EXECUTION_ID,
    NEXT_CANONICAL_STEP,
    PARENT_PR4905_MERGE_COMMIT,
    PARENT_PR4906_MERGE_COMMIT,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    run_offline_terminal_failure_evidence_execution_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTION_CONFIG = (
    REPO_ROOT
    / "config/research/post_pr4906_offline_only_terminal_fleet_failure_evidence_execution_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_PR4906_OFFLINE_ONLY_TERMINAL_FLEET_FAILURE_EVIDENCE_EXECUTION_V0.md"
)
RUNNER_SCRIPT = (
    REPO_ROOT
    / "scripts/research/post_pr4906_offline_only_terminal_fleet_failure_evidence_execution_v0.py"
)
BASELINE_HEAD = "4505030938f6a70391973f761fffb183443e9336"
PARENT_PR4905_OUTPUT_SUFFIX = (
    "post_pr4904_v4_fleet_robustness_failure_decomposition_v0_20260706T042551Z"
)
PARENT_PR4905_CLOSEOUT_SUFFIX = "pr4905_squash_merge_closeout_20260706T043541Z"
PARENT_PR4906_CLOSEOUT_SUFFIX = (
    "post_pr4905_terminal_fleet_failure_next_scope_definition_merge_closeout_20260706T044625Z"
)
PARENT_EVALUATION_SUFFIX = (
    "post_v4_versioned_fleet_offline_economic_evaluation_execution_v0_20260706T040339Z"
)
FAILED_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
MISSING_AXES = (
    "long_short_contribution",
    "fee_slippage_funding_drag",
    "turnover_cost_drag_decomposition",
    "regime_bucket_stability_beyond_wf_windows",
    "instrument_concentration_contribution_beyond_rotation_metadata",
)
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
PARENT_PR4905_OUTPUT_BUNDLE = ARCHIVE_ROOT / "implementation" / PARENT_PR4905_OUTPUT_SUFFIX
PARENT_PR4905_CLOSEOUT_DIR = ARCHIVE_ROOT / "implementation" / PARENT_PR4905_CLOSEOUT_SUFFIX
PARENT_PR4906_CLOSEOUT_DIR = ARCHIVE_ROOT / "implementation" / PARENT_PR4906_CLOSEOUT_SUFFIX
PARENT_EVALUATION_BUNDLE = ARCHIVE_ROOT / "implementation" / PARENT_EVALUATION_SUFFIX
REQUIRED_ARTIFACTS = (
    "parent_manifest_verification.json",
    "bound_parent_scope_summary.json",
    "terminal_failure_classification.json",
    "candidate_failure_matrix.json",
    "non_retry_guard_matrix.json",
    "admissible_next_scope_matrix.json",
    "execution_summary.json",
    "MANIFEST.sha256",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostPr4906OfflineOnlyTerminalFleetFailureEvidenceExecutionV0Contract:
    def test_execution_config_core_fields(self) -> None:
        config = json.loads(EXECUTION_CONFIG.read_text(encoding="utf-8"))
        assert config["status"] == "OFFLINE_TERMINAL_FAILURE_EVIDENCE_EXECUTION_COMPLETE_V0"
        assert config["evidence_class_id"] == EXECUTION_ID
        assert config["execution_id"] == EXECUTION_ID
        assert config["scope_id"] == SCOPE_ID
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["selected_class"] == "F"
        assert config["go_token"] == CONFIRM_GO
        assert config["baseline_head"] == BASELINE_HEAD
        assert config["fleet_verdict"] == "FLEET_ECONOMIC_VALIDITY_FAIL"
        assert config["aggregate_result"] == "FLEET_ECONOMIC_VALIDITY_FAIL"
        assert config["economic_validity_offline_gate_pass"] is False
        assert config["same_binding_retry_allowed"] is False
        assert config["failed_bindings_retry_allowed"] is False
        assert config["parameter_rescue_allowed"] is False
        assert config["threshold_lowering_allowed"] is False
        assert config["runtime_rewire_admissible"] is False
        assert config["new_candidates_ratified"] is False
        assert config["economic_evaluation_executed"] is False
        assert config["backtest_executed"] is False
        assert config["runtime_authority"] == "NONE"
        assert config["runtime_authority_created"] is False
        assert config["strategy_version"] == "post_v4_hypothesis_v0"
        assert config["missing_axes_targeted"] == list(MISSING_AXES)

    def test_execution_config_parent_bindings(self) -> None:
        config = json.loads(EXECUTION_CONFIG.read_text(encoding="utf-8"))
        assert PARENT_PR4905_OUTPUT_SUFFIX in config["parent_pr4905_output_bundle"]
        assert PARENT_PR4905_CLOSEOUT_SUFFIX in config["parent_pr4905_closeout_dir"]
        assert PARENT_PR4906_CLOSEOUT_SUFFIX in config["parent_pr4906_closeout_dir"]
        assert config["parent_pr4905_merge_commit"] == PARENT_PR4905_MERGE_COMMIT
        assert config["parent_pr4906_merge_commit"] == PARENT_PR4906_MERGE_COMMIT
        assert config["parent_pr4905_output_manifest_verify_rc"] == 0
        assert config["parent_pr4905_closeout_manifest_verify_rc"] == 0
        assert config["parent_pr4906_closeout_manifest_verify_rc"] == 0

    def test_execution_config_blocked_actions(self) -> None:
        config = json.loads(EXECUTION_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_actions"])
        for action in (
            "ECONOMIC_EVALUATION_EXECUTION",
            "BACKTEST_RERUN",
            "SAME_BINDING_RETRY",
            "FAILED_BINDING_RETRY",
            "PARAMETER_RESCUE",
            "THRESHOLD_LOWERING",
            "POLICY_CHANGE_TO_RECLASSIFY_NEGATIVE_EVIDENCE",
            "UNCHANGED_FAILED_BINDING_EVALUATION",
            "LIVE",
            "ORDERS",
        ):
            assert action in blocked

    def test_parent_manifest_verification_required(self) -> None:
        for bundle in (
            PARENT_PR4905_OUTPUT_BUNDLE,
            PARENT_PR4905_CLOSEOUT_DIR,
            PARENT_PR4906_CLOSEOUT_DIR,
            PARENT_EVALUATION_BUNDLE,
        ):
            assert bundle.is_dir()
            ok, _ = verify_manifest_sha256(bundle)
            assert ok is True

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_PR4906_OFFLINE_ONLY_TERMINAL_FLEET_FAILURE_EVIDENCE_EXECUTION_V0"
            )
            in body
        )
        assert f"`GO_TOKEN` | `{CONFIRM_GO}`" in body
        assert "`GO_TOKEN_CONSUMED` | `true`" in body
        assert "`FLEET_VERDICT` | `FLEET_ECONOMIC_VALIDITY_FAIL`" in body
        assert "`AGGREGATE_RESULT` | `FLEET_ECONOMIC_VALIDITY_FAIL`" in body
        assert "`FAILED_BINDINGS_RETRY_ALLOWED` | `false`" in body

    def test_governance_doc_no_execution_flags(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "`ECONOMIC_EVALUATION_EXECUTED` | `false`" in body
        assert "`BACKTEST_EXECUTED` | `false`" in body
        assert "`WALK_FORWARD_RUN_EXECUTED` | `false`" in body
        assert "`MONTE_CARLO_RUN_EXECUTED` | `false`" in body
        assert "`STRESS_RUN_EXECUTED` | `false`" in body
        assert "`RUNTIME_AUTHORITY` | `NONE`" in body
        assert "`RUNTIME_AUTHORITY_CREATED` | `false`" in body
        assert "`LIVE_AUTHORIZED` | `false`" in body
        assert "`SHADOW_AUTHORIZED` | `false`" in body
        assert "`PAPER_AUTHORIZED` | `false`" in body
        assert "`TESTNET_AUTHORIZED` | `false`" in body
        assert "`ORDERS_ALLOWED` | `false`" in body

    def test_governance_doc_next_step(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert NEXT_CANONICAL_STEP in body
        assert _field_value(body, "SAME_BINDING_RETRY_ALLOWED") == "false"
        assert _field_value(body, "PARAMETER_RESCUE_ALLOWED") == "false"
        assert _field_value(body, "THRESHOLD_LOWERING_ALLOWED") == "false"

    def test_collector_script_exists(self) -> None:
        assert RUNNER_SCRIPT.is_file()
        body = RUNNER_SCRIPT.read_text(encoding="utf-8")
        assert CONFIRM_GO in body
        assert "parent_manifest_verification.json" in body
        assert "terminal_failure_classification.json" in body
        assert "non_retry_guard_matrix.json" in body
        assert "admissible_next_scope_matrix.json" in body
        assert 'f"{key}_manifest_verify.log"' in body

    @pytest.mark.integration
    def test_run_offline_evidence_execution_output_manifest_verifies(self, tmp_path: Path) -> None:
        if not all(
            bundle.is_dir()
            for bundle in (
                PARENT_PR4905_OUTPUT_BUNDLE,
                PARENT_PR4905_CLOSEOUT_DIR,
                PARENT_PR4906_CLOSEOUT_DIR,
                PARENT_EVALUATION_BUNDLE,
            )
        ):
            pytest.skip("parent evidence bundles unavailable")
        report = run_offline_terminal_failure_evidence_execution_v0(
            go_token=CONFIRM_GO,
            parent_pr4905_output_bundle=PARENT_PR4905_OUTPUT_BUNDLE,
            parent_pr4905_closeout_dir=PARENT_PR4905_CLOSEOUT_DIR,
            parent_pr4906_closeout_dir=PARENT_PR4906_CLOSEOUT_DIR,
            parent_evaluation_bundle=PARENT_EVALUATION_BUNDLE,
            durable_archive_root=tmp_path,
        )
        assert report["aggregate_result"] == "FLEET_ECONOMIC_VALIDITY_FAIL"
        assert report["failed_candidates"] == list(FAILED_CANDIDATES)
        assert report["manifest_verify_rc"] == 0
        assert report["authority_boundary"]["runtime_authority_created"] is False
        assert report["authority_boundary"]["live_authorized"] is False
        assert report["authority_boundary"]["orders_allowed"] is False
        assert report["same_binding_retry_allowed"] is False
        assert report["new_candidates_ratified"] is False
        assert report["economic_validity_offline_gate_pass"] is False
        for candidate in FAILED_CANDIDATES:
            assert (
                report["candidate_failure_matrix"]["failed_candidate_verdicts"][candidate]
                == "ROBUSTNESS_FAILED"
            )
        output_dir = Path(report["durable_evidence_path"])
        for artifact in REQUIRED_ARTIFACTS:
            assert (output_dir / artifact).is_file()
        ok, _ = verify_manifest_sha256(output_dir)
        assert ok is True

        guards = json.loads(
            (output_dir / "non_retry_guard_matrix.json").read_text(encoding="utf-8")
        )
        assert guards["all_guards_active"] is True

        admissible = json.loads(
            (output_dir / "admissible_next_scope_matrix.json").read_text(encoding="utf-8")
        )
        assert admissible["runtime_promotion_allowed"] is False
        assert admissible["required_next_go_for_scope_definition"] == NEXT_CANONICAL_STEP

        parent_manifest = json.loads(
            (output_dir / "parent_manifest_verification.json").read_text(encoding="utf-8")
        )
        assert parent_manifest["parent_pr4905_merge_commit"] == PARENT_PR4905_MERGE_COMMIT
        assert parent_manifest["parent_pr4906_merge_commit"] == PARENT_PR4906_MERGE_COMMIT
