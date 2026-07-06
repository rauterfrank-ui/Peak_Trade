"""Contract tests for post-PR4921 versioned research bindings no eval v0."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from scripts.ops.validate_docs_token_policy import DocsTokenPolicyValidator
from scripts.research.post_pr4921_versioned_research_bindings_no_eval_v0 import (
    CONFIRM_GO,
    NEXT_STEP,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    VERDICT,
    run_post_pr4921_versioned_research_bindings_no_eval_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BINDING_CONFIG = (
    REPO_ROOT / "config/research/post_pr4921_versioned_research_bindings_no_eval_v0.json"
)
GOVERNANCE_DOC = REPO_ROOT / "docs/governance/POST_PR4921_VERSIONED_RESEARCH_BINDINGS_NO_EVAL_V0.md"
BINDING_SCRIPT = (
    REPO_ROOT / "scripts/research/post_pr4921_versioned_research_bindings_no_eval_v0.py"
)
PARENT_SCOPE_CONFIG = (
    REPO_ROOT / "config/research/post_pr4920_new_versioned_research_scope_definition_v0.json"
)
BASE_HEAD = "dc6229ed32a57af4b9f3cd1f3d969cf499b6ebc5"
PARENT_CLOSEOUT_SUFFIX = (
    "post_pr4920_new_versioned_research_scope_definition_merge_closeout_20260706T081927Z"
)
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
PARENT_CLOSEOUT_DIR = ARCHIVE_ROOT / "implementation" / PARENT_CLOSEOUT_SUFFIX
EXCLUDED_V1 = ("trend_following/v1", "bollinger_bands/v1", "momentum_1h/v1")
FLEET_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
ARCHETYPES = (
    "TREND_CONTINUATION_V2",
    "MEAN_REVERSION_BANDS_V2",
    "MOMENTUM_HORIZON_V2",
)
PROVENANCE_FIELDS = (
    "parameter_binding",
    "dataset_binding",
    "period_binding",
    "instrument_binding",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "implementation_digest_source",
    "config_digest_source",
    "data_digest_source",
)
REQUIRED_CONTRACT_ASSERTIONS = (
    ("binding_materialization_only", True),
    ("economic_evaluation_authorized", False),
    ("backtest_execution_authorized", False),
    ("walk_forward_execution_authorized", False),
    ("monte_carlo_execution_authorized", False),
    ("stress_execution_authorized", False),
    ("retry_authorized", False),
    ("parameter_optimization_authorized", False),
    ("threshold_lowering_authorized", False),
    ("promotion_admissible", False),
    ("runtime_rewire_admissible", False),
    ("orders_allowed", False),
    ("live_authorized", False),
    ("failed_v1_bindings_excluded", True),
)
REQUIRED_BUNDLE_ARTIFACTS = (
    "BINDING_SUMMARY.md",
    "VERSIONED_BINDINGS.json",
    "AUTHORITY_BOUNDARY.json",
    "SOURCE_EVIDENCE_INDEX.json",
    "MANIFEST.sha256",
    "MANIFEST.verify.txt",
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
    "Binding-Materialisierung ≠ Evaluation-Autorisierung",
    "FAILED_V1_BINDINGS_EXCLUDED",
    "Keine Offline-Economic-Evaluation",
    "SEPARATE_OPERATOR_GO_REQUIRED_FOR_OFFLINE_ECONOMIC_EVALUATION_EXECUTION",
    "MATERIALIZED_NOT_EVALUATED",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostPr4921VersionedResearchBindingsNoEvalV0Contract:
    def test_binding_config_exists_and_parses(self) -> None:
        assert BINDING_CONFIG.is_file()
        config = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert config["schema_version"] == "post_pr4921_versioned_research_bindings_no_eval.v0"

    def test_required_contract_assertions(self) -> None:
        config = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        for field, expected in REQUIRED_CONTRACT_ASSERTIONS:
            assert config[field] is expected, f"contract assertion failed: {field}"
        assert config["next_step"] == NEXT_STEP

    def test_binding_config_core_fields(self) -> None:
        config = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert config["verdict"] == VERDICT
        assert config["scope_id"] == SCOPE_ID
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["go_token"] == CONFIRM_GO
        assert config["base_head"] == BASE_HEAD
        assert config["baseline_pr"] == 4921
        assert config["parent_scope_id"] == "POST_PR4920_NEW_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0"

    def test_versioned_bindings_structure(self) -> None:
        config = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        bindings = config["versioned_bindings"]
        assert len(bindings) == 3
        by_id = {b["candidate_id"]: b for b in bindings}
        for sid in FLEET_CANDIDATES:
            assert sid in by_id
        archetypes = [b["strategy_archetype"] for b in bindings]
        assert archetypes == list(ARCHETYPES)
        for binding in bindings:
            assert binding["candidate_version"] == "v2"
            assert binding["binding_status"] == "MATERIALIZED_NOT_EVALUATED"
            for field in PROVENANCE_FIELDS:
                assert field in binding, f"missing {field} in {binding['candidate_id']}"
            assert binding["evaluation_authorized"] is False
            assert binding["retry_authorized"] is False
            assert binding["promotion_admissible"] is False
            assert binding["runtime_rewire_admissible"] is False

    def test_failed_v1_bindings_excluded(self) -> None:
        config = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert set(config["excluded_failed_v1_bindings"]) == set(EXCLUDED_V1)
        for binding in config["versioned_bindings"]:
            assert binding["excluded_failed_v1_binding"] in EXCLUDED_V1
            assert binding["replaces_failed_binding"] == binding["excluded_failed_v1_binding"]

    def test_blocked_execution_classes(self) -> None:
        config = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_execution_classes"])
        for action in (
            "BACKTEST",
            "WALK_FORWARD",
            "MONTE_CARLO",
            "STRESS",
            "ECONOMIC_EVALUATION",
            "PROMOTION",
            "LIVE",
        ):
            assert action in blocked

    def test_parent_closeout_ref_present(self) -> None:
        config = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert PARENT_CLOSEOUT_SUFFIX in config["parent_closeout_dir"]
        assert config["parent_closeout_manifest_verify_rc"] == 0

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker("DOCS_TOKEN_POST_PR4921_VERSIONED_RESEARCH_BINDINGS_NO_EVAL_V0")
            in body
        )
        assert "`BINDING_MATERIALIZATION_ONLY` | `true`" in body
        assert "`FAILED_V1_BINDINGS_EXCLUDED` | `true`" in body
        assert "`ECONOMIC_EVALUATION_AUTHORIZED` | `false`" in body
        assert "`RETRY_AUTHORIZED` | `false`" in body
        assert "`ORDERS_ALLOWED` | `false`" in body
        assert "`LIVE_AUTHORIZED` | `false`" in body

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

    def test_implementation_digest_sources_exist(self) -> None:
        config = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        for binding in config["versioned_bindings"]:
            impl_path = REPO_ROOT / binding["implementation_digest_source"]
            assert impl_path.is_file(), binding["implementation_digest_source"]

    def test_script_has_no_forbidden_imports(self) -> None:
        body = BINDING_SCRIPT.read_text(encoding="utf-8")
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

    def test_runner_materializes_required_artifacts(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "bundle"
        result = run_post_pr4921_versioned_research_bindings_no_eval_v0(output_dir=output_dir)
        assert result["verdict"] == VERDICT
        assert result["manifest_verify_rc"] == 0
        for artifact_name in REQUIRED_BUNDLE_ARTIFACTS:
            assert (output_dir / artifact_name).is_file(), artifact_name
        ok, _msg = verify_manifest_sha256(output_dir)
        assert ok

        authority = json.loads((output_dir / "AUTHORITY_BOUNDARY.json").read_text(encoding="utf-8"))
        assert authority["binding_materialization_only"] is True
        assert authority["economic_evaluation_authorized"] is False
        assert authority["failed_v1_bindings_excluded"] is True
        assert authority["next_step"] == NEXT_STEP

        bindings = json.loads((output_dir / "VERSIONED_BINDINGS.json").read_text(encoding="utf-8"))
        assert bindings["binding_count"] == 3
        assert set(bindings["excluded_failed_v1_bindings"]) == set(EXCLUDED_V1)

    def test_cli_entrypoint(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "cli_bundle"
        proc = subprocess.run(
            [
                sys.executable,
                str(BINDING_SCRIPT),
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
        assert (output_dir / "MANIFEST.sha256").is_file()

    def test_parent_scope_config_referenced(self) -> None:
        assert PARENT_SCOPE_CONFIG.is_file()
        parent = json.loads(PARENT_SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert parent["scope_id"] == "POST_PR4920_NEW_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0"
        assert parent["failed_bindings_excluded"] is True
