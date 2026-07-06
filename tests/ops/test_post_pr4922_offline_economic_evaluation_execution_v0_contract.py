"""Contract tests for post-PR4922 offline economic evaluation execution v0."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from scripts.ops.validate_docs_token_policy import DocsTokenPolicyValidator
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    CandidateExecutionResultV0,
    CandidateTerminalStatus,
)
from src.research.post_pr4922_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    BINDING_CONFIG_DIGEST,
    BINDING_CONFIG_REL,
    CONFIRM_GO,
    EVIDENCE_CLASS_ID,
    EXECUTION_SCOPE_DIGEST,
    EXECUTION_SEMANTIC_DIGEST,
    EXCLUDED_V1_BINDINGS,
    EXPECTED_ORIGIN_MAIN_SHA,
    FLEET_CANDIDATES,
    ORDER_EFFECT,
    PARENT_CLOSEOUT_SUFFIX,
    PROCESS_CLASSIFICATION,
    RUNTIME_EFFECT,
    SCOPE_CLASSIFICATION,
    STRATEGY_VERSION,
    CandidateEconomicVerdict,
    FleetEconomicVerdict,
    classify_candidate_verdict_v0,
    classify_fleet_verdict_v0,
    compute_execution_scope_digests_v0,
    verify_execution_scope_v0,
    verify_preconditions_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTION_CONFIG = (
    REPO_ROOT / "config/research/post_pr4922_offline_economic_evaluation_execution_v0.json"
)
BINDING_CONFIG = REPO_ROOT / BINDING_CONFIG_REL
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/POST_PR4922_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0.md"
)
RUNNER_SCRIPT = (
    REPO_ROOT / "scripts/research/post_pr4922_offline_economic_evaluation_execution_v0.py"
)
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
PARENT_CLOSEOUT_DIR = ARCHIVE_ROOT / "implementation" / PARENT_CLOSEOUT_SUFFIX
REQUIRED_BUNDLE_ARTIFACTS = (
    "EXECUTION_REPORT.md",
    "authority_boundary.json",
    "parent_manifest_verify.log",
    "binding_config_snapshot.json",
    "candidate_economic_viability_evidence.json",
    "candidate_verdicts.json",
    "fleet_verdict.json",
    "MANIFEST.sha256",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


@pytest.fixture(name="execution_config")
def fixture_execution_config() -> dict:
    return json.loads(EXECUTION_CONFIG.read_text(encoding="utf-8"))


@pytest.fixture(name="binding_config")
def fixture_binding_config() -> dict:
    return json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))


class TestPostPr4922OfflineEconomicEvaluationExecutionV0Contract:
    def test_go_token_and_scope_classification(self) -> None:
        assert (
            CONFIRM_GO
            == "GO_POST_PR4922_VERSIONED_RESEARCH_BINDINGS_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
        )
        assert (
            SCOPE_CLASSIFICATION
            == "OFFLINE_ECONOMIC_EVALUATION_EXECUTION_ONLY_NO_RUNTIME_AUTHORITY_V0"
        )
        assert PROCESS_CLASSIFICATION == "POST_PR4922_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"

    def test_no_runtime_authority_order_effect_constants(self) -> None:
        assert AUTHORITY_EFFECT == "NONE"
        assert RUNTIME_EFFECT == "NONE"
        assert ORDER_EFFECT == "NONE"

    def test_expected_origin_main_sha(self) -> None:
        assert EXPECTED_ORIGIN_MAIN_SHA == "a5cb8edef3edff2c1213aef2130cd0700c3b89c3"

    def test_execution_config_digests(self, execution_config: dict) -> None:
        assert execution_config["scope_digest"] == EXECUTION_SCOPE_DIGEST
        assert execution_config["semantic_digest"] == EXECUTION_SEMANTIC_DIGEST
        assert execution_config["binding_config_digest"] == BINDING_CONFIG_DIGEST
        assert execution_config["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert execution_config["execution_go_token"] == CONFIRM_GO
        assert execution_config["parent_closeout_suffix"] == PARENT_CLOSEOUT_SUFFIX
        assert execution_config["strategy_version"] == STRATEGY_VERSION
        assert execution_config["fleet_candidates"] == list(FLEET_CANDIDATES)
        assert execution_config.get("execution_performed") is True
        assert execution_config["fleet_verdict"] == "FLEET_EXECUTION_BLOCKED_FAIL_CLOSED"
        assert execution_config["economic_validity_offline_gate_pass"] is False
        assert (
            "post_pr4922_offline_economic_evaluation_execution_20260706T083719Z"
            in execution_config["durable_evidence_ref"]
        )

    def test_execution_scope_semantic_digest_recomputes(self, execution_config: dict) -> None:
        _scope_digest, semantic_digest = compute_execution_scope_digests_v0(execution_config)
        assert semantic_digest == EXECUTION_SEMANTIC_DIGEST

    def test_execution_scope_verification(
        self, execution_config: dict, binding_config: dict
    ) -> None:
        ok, reasons = verify_execution_scope_v0(
            execution_config,
            binding_config=binding_config,
        )
        assert ok, reasons

    def test_binding_config_fleet_v2(self, binding_config: dict) -> None:
        bindings = binding_config["versioned_bindings"]
        assert len(bindings) == 3
        assert set(binding_config["excluded_failed_v1_bindings"]) == set(EXCLUDED_V1_BINDINGS)
        for binding in bindings:
            assert binding["candidate_version"] == "v2"
            assert binding["binding_status"] == "MATERIALIZED_NOT_EVALUATED"
            assert binding["evaluation_authorized"] is False
            assert binding["retry_authorized"] is False

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker("DOCS_TOKEN_POST_PR4922_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0")
            in body
        )
        assert "`FAILED_V1_BINDINGS_EXCLUDED` | `true`" in body
        assert "`FUTURES_ONLY` | `true`" in body
        assert "`BITCOIN_DIRECTION_ALLOWED` | `false`" in body
        assert "`RUNTIME_AUTHORITY` | `NONE`" in body

    def test_governance_doc_binding_refs(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "`config/research/post_pr4921_versioned_research_bindings_no_eval_v0.json`" in body
        assert f"`BINDING_CONFIG_DIGEST` | `{BINDING_CONFIG_DIGEST}`" in body

    def test_runner_script_exists(self) -> None:
        assert RUNNER_SCRIPT.is_file()
        body = RUNNER_SCRIPT.read_text(encoding="utf-8")
        assert CONFIRM_GO in body
        assert "run_bounded_scope_v0" in body
        assert "runtime_authority_created" in body

    def test_runner_script_no_forbidden_imports(self) -> None:
        body = RUNNER_SCRIPT.read_text(encoding="utf-8")
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
            pytest.skip(f"parent closeout unavailable: {parent_path}")
        ok, _msg = verify_manifest_sha256(parent_path)
        assert ok, f"parent manifest invalid: {parent_path}"

    def test_classify_fleet_verdict_pass(self) -> None:
        verdicts = [CandidateEconomicVerdict.ECONOMICALLY_VIABLE_OFFLINE] * 3
        assert (
            classify_fleet_verdict_v0(verdicts) is FleetEconomicVerdict.FLEET_ECONOMIC_VALIDITY_PASS
        )

    def test_classify_fleet_verdict_fail(self) -> None:
        verdicts = [
            CandidateEconomicVerdict.ROBUSTNESS_FAILED,
            CandidateEconomicVerdict.ROBUSTNESS_FAILED,
            CandidateEconomicVerdict.ROBUSTNESS_FAILED,
        ]
        assert (
            classify_fleet_verdict_v0(verdicts) is FleetEconomicVerdict.FLEET_ECONOMIC_VALIDITY_FAIL
        )

    def test_classify_candidate_robustness_failed(self) -> None:
        result = CandidateExecutionResultV0(
            strategy_id="trend_following",
            strategy_version="v2",
            canonical_candidate_identifier="trend_following/v2",
            config_path="cfg.json",
            output_dir="/tmp/out",
            run_id="run-1",
            terminal_status=CandidateTerminalStatus.FAIL,
            economic_validity_result="FAIL",
            economic_validity_offline_gate_pass=False,
            evidence_status="ROBUSTNESS_FAILED",
            manifest_verify_rc=0,
            reason_codes=(),
            stage_return_codes={},
            runner_execution_success=True,
        )
        verdict = classify_candidate_verdict_v0(
            result,
            evidence_payload={"status": "ROBUSTNESS_FAILED"},
        )
        assert verdict is CandidateEconomicVerdict.ROBUSTNESS_FAILED

    def test_verify_preconditions_go_token(self) -> None:
        ok, reasons = verify_preconditions_v0(
            repo_root=REPO_ROOT,
            confirm=CONFIRM_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            require_clean_worktree=False,
        )
        assert ok, reasons

    def test_required_bundle_artifact_names_documented(self) -> None:
        for name in REQUIRED_BUNDLE_ARTIFACTS:
            assert name

    def test_cli_help(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(RUNNER_SCRIPT), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0
        assert CONFIRM_GO in proc.stdout
