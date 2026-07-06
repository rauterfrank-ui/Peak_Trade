"""Contract tests for post-PR4904 v4 fleet robustness failure decomposition v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from scripts.research.post_pr4904_v4_fleet_robustness_failure_decomposition_v0 import (
    CONFIRM_GO,
    EXECUTION_ID,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    run_failure_decomposition_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DECOMPOSITION_CONFIG = (
    REPO_ROOT / "config/research/post_pr4904_v4_fleet_robustness_failure_decomposition_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/POST_PR4904_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_V0.md"
)
RUNNER_SCRIPT = (
    REPO_ROOT / "scripts/research/post_pr4904_v4_fleet_robustness_failure_decomposition_v0.py"
)
BASELINE_HEAD = "442c05688cfd1dcc28ebfcfdb13fd853dc16f8aa"
PARENT_EVALUATION_SUFFIX = (
    "post_v4_versioned_fleet_offline_economic_evaluation_execution_v0_20260706T040339Z"
)
PARENT_CLOSEOUT_SUFFIX = "pr4904_squash_merge_closeout_20260706T041915Z"
FAILED_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
DECOMPOSITION_AXES = (
    "net_edge_after_costs",
    "profit_factor",
    "max_drawdown_tail_loss",
    "walk_forward_stability",
    "monte_carlo_robustness",
    "stress_robustness",
    "parameter_sensitivity",
    "trade_count_sample_adequacy",
    "long_short_contribution",
    "regime_breakdown",
    "fee_slippage_funding_drag",
    "dominance_concentration",
    "evidence_admissibility",
    "fleet_contribution_failure",
)
NEXT_STEP = (
    "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_V0"
)
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
PARENT_EVALUATION_BUNDLE = ARCHIVE_ROOT / "implementation" / PARENT_EVALUATION_SUFFIX
PARENT_CLOSEOUT_BUNDLE = ARCHIVE_ROOT / "implementation" / PARENT_CLOSEOUT_SUFFIX


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostPr4904V4FleetRobustnessFailureDecompositionV0Contract:
    def test_decomposition_config_core_fields(self) -> None:
        config = json.loads(DECOMPOSITION_CONFIG.read_text(encoding="utf-8"))
        assert config["status"] == "FAILURE_DECOMPOSITION_EXECUTION_COMPLETE_V0"
        assert config["evidence_class_id"] == EXECUTION_ID
        assert config["execution_id"] == EXECUTION_ID
        assert config["scope_id"] == SCOPE_ID
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["selected_class"] == "E"
        assert config["go_token"] == CONFIRM_GO
        assert config["baseline_head"] == BASELINE_HEAD
        assert config["fleet_verdict"] == "FLEET_ECONOMIC_VALIDITY_FAIL"
        assert config["economic_validity_offline_gate_pass"] is False
        assert config["same_binding_retry_allowed"] is False
        assert config["immutable_binding_retry_allowed"] is False
        assert config["new_candidates_ratified"] is False
        assert config["strategy_version"] == "post_v4_hypothesis_v0"
        assert config["decomposition_axes"] == list(DECOMPOSITION_AXES)
        assert config["failed_candidates"] == list(FAILED_CANDIDATES)

    def test_decomposition_config_parent_refs(self) -> None:
        config = json.loads(DECOMPOSITION_CONFIG.read_text(encoding="utf-8"))
        assert PARENT_EVALUATION_SUFFIX in config["parent_evaluation_evidence_ref"]
        assert PARENT_CLOSEOUT_SUFFIX in config["parent_closeout_evidence_ref"]
        assert config["parent_evaluation_manifest_verify_rc"] == 0
        assert config["parent_closeout_manifest_verify_rc"] == 0

    def test_decomposition_config_blocked_actions(self) -> None:
        config = json.loads(DECOMPOSITION_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_actions"])
        for action in (
            "ECONOMIC_EVALUATION_EXECUTION",
            "BACKTEST_RERUN",
            "SAME_BINDING_RETRY",
            "FAILED_BINDING_RETRY",
            "WALK_FORWARD_EXECUTION",
            "MONTE_CARLO_EXECUTION",
            "STRESS_EXECUTION",
            "NEW_CANDIDATE_RATIFICATION",
            "LIVE",
            "ORDERS",
        ):
            assert action in blocked

    def test_parent_manifest_verification_required(self) -> None:
        assert PARENT_EVALUATION_BUNDLE.is_dir()
        assert PARENT_CLOSEOUT_BUNDLE.is_dir()
        ok_eval, _ = verify_manifest_sha256(PARENT_EVALUATION_BUNDLE)
        ok_closeout, _ = verify_manifest_sha256(PARENT_CLOSEOUT_BUNDLE)
        assert ok_eval is True
        assert ok_closeout is True

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_PR4904_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_V0"
            )
            in body
        )
        assert f"`GO_TOKEN` | `{CONFIRM_GO}`" in body
        assert "`GO_TOKEN_CONSUMED` | `true`" in body
        assert "`FLEET_VERDICT` | `FLEET_ECONOMIC_VALIDITY_FAIL`" in body
        assert "`AGGREGATE_STATUS` | `FLEET_ECONOMIC_VALIDITY_FAIL`" in body
        assert "`FAILED_BINDINGS_RETRY_ALLOWED` | `false`" in body

    def test_governance_doc_failed_candidates(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for candidate in FAILED_CANDIDATES:
            assert f"`{candidate}`" in body
            assert "ROBUSTNESS_FAILED" in body

    def test_governance_doc_no_execution_flags(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "`economic_evaluation_executed` | `false`" in body
        assert "`backtest_executed` | `false`" in body
        assert "`walk_forward_run_executed` | `false`" in body
        assert "`monte_carlo_run_executed` | `false`" in body
        assert "`stress_run_executed` | `false`" in body
        assert "`RUNTIME_AUTHORITY` | `NONE`" in body
        assert "`RUNTIME_AUTHORITY_CREATED` | `false`" in body
        assert "`LIVE_AUTHORIZED` | `false`" in body
        assert "`SHADOW_AUTHORIZED` | `false`" in body
        assert "`PAPER_AUTHORIZED` | `false`" in body
        assert "`TESTNET_AUTHORIZED` | `false`" in body
        assert "`ORDERS_ALLOWED` | `false`" in body

    def test_governance_doc_next_step(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert NEXT_STEP in body
        assert _field_value(body, "SAME_BINDING_RETRY_ALLOWED") == "false"
        assert _field_value(body, "NEW_CANDIDATES_RATIFIED") == "false"

    def test_collector_script_exists(self) -> None:
        assert RUNNER_SCRIPT.is_file()
        body = RUNNER_SCRIPT.read_text(encoding="utf-8")
        assert CONFIRM_GO in body
        assert "FAILURE_DECOMPOSITION_SUMMARY.md" in body
        assert "FAILURE_DECOMPOSITION.json" in body
        assert "CANDIDATE_FAILURE_MATRIX.tsv" in body
        assert "AGGREGATE_FAILURE_MATRIX.tsv" in body
        assert "INPUT_POINTERS.json" in body
        assert "CANDIDATE_RESULT_" in body
        assert "parent_closeout_manifest_verify.log" in body

    @pytest.mark.integration
    def test_run_failure_decomposition_output_manifest_verifies(self, tmp_path: Path) -> None:
        if not PARENT_EVALUATION_BUNDLE.is_dir() or not PARENT_CLOSEOUT_BUNDLE.is_dir():
            pytest.skip("parent evidence bundles unavailable")
        report = run_failure_decomposition_v0(
            go_token=CONFIRM_GO,
            parent_evaluation_bundle=PARENT_EVALUATION_BUNDLE,
            parent_closeout_bundle=PARENT_CLOSEOUT_BUNDLE,
            durable_archive_root=tmp_path,
        )
        assert report["aggregate_status"] == "FLEET_ECONOMIC_VALIDITY_FAIL"
        assert report["failed_candidates"] == list(FAILED_CANDIDATES)
        assert report["manifest_verify_rc"] == 0
        assert report["authority_boundary"]["runtime_authority_created"] is False
        assert report["authority_boundary"]["live_authorized"] is False
        assert report["authority_boundary"]["orders_allowed"] is False
        assert report["same_binding_retry_allowed"] is False
        assert report["new_candidates_ratified"] is False
        for candidate in FAILED_CANDIDATES:
            assert report["failed_candidate_verdicts"][candidate] == "ROBUSTNESS_FAILED"
        output_dir = Path(report["durable_evidence_path"])
        for artifact in (
            "FAILURE_DECOMPOSITION_SUMMARY.md",
            "FAILURE_DECOMPOSITION.json",
            "CANDIDATE_FAILURE_MATRIX.tsv",
            "AGGREGATE_FAILURE_MATRIX.tsv",
            "INPUT_POINTERS.json",
            "MANIFEST.sha256",
        ):
            assert (output_dir / artifact).is_file()
        ok, _ = verify_manifest_sha256(output_dir)
        assert ok is True
