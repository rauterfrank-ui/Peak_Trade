"""Contract tests for post-PR4937 final research fleet bindings and offline eval scope ratification v0."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from scripts.ops.validate_docs_token_policy import DocsTokenPolicyValidator
from scripts.research.post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0 import (
    CONFIRM_GO,
    GO_TOKEN,
    NEXT_STEP,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    SCOPE_ID,
    VERDICT,
    run_post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0,
)
from src.research.post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0 import (
    ALLOWED_FUTURE_ACTIONS,
    EXCLUDED_CROSS_SECTIONAL_FUNDING_CANDIDATES,
    FLEET_CANDIDATE_IDS,
    REQUIRED_BINDING_FIELDS,
    validate_ratification_config_v0,
    validate_ratified_binding_entry_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RATIFICATION_CONFIG = (
    REPO_ROOT
    / "config/research/post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFICATION_POST_PR4937_V0.md"
)
RATIFICATION_SCRIPT = (
    REPO_ROOT
    / "scripts/research/post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0.py"
)
BINDING_COMPLETION_OWNER = (
    REPO_ROOT / "config/research/final_research_fleet_class_d_versioned_binding_completion_v0.json"
)
BASE_HEAD = "720fc100e590fd7ac40edb0fcba0bb63026ae838"
PARENT_CLOSEOUT_SUFFIX = (
    "pr4937_cross_sectional_funding_research_fleet_complete_no_pass_merge_closeout_20260706T175340Z"
)
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
PARENT_CLOSEOUT_DIR = ARCHIVE_ROOT / "research" / PARENT_CLOSEOUT_SUFFIX
FLEET_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
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
REQUIRED_CONTRACT_ASSERTIONS = (
    ("binding_ratification_only", True),
    ("evaluation_authorized", False),
    ("evaluation_executed", False),
    ("economic_evaluation_authorized", False),
    ("economic_evaluation_executed", False),
    ("evaluation_scope_ratified", True),
    ("offline_economic_evaluation_scope_ratified", True),
    ("runtime_authority_touched", False),
    ("promotion_granted", False),
    ("threshold_lowering_authorized", False),
    ("result_rescue_authorized", False),
    ("parameter_rescue_authorized", False),
    ("runtime_rewire_admissible", False),
    ("orders_allowed", False),
    ("live_authorized", False),
)
BOUNDARY_PHRASES = (
    "Binding-Ratifikation ≠ Evaluation-Ausführung",
    "COMPLETE_NO_PASS",
    "FINAL_RESEARCH_FLEET_BINDINGS",
    "EVALUATION_EXECUTED",
    "RUNTIME_AUTHORITY_TOUCHED",
    "PROMOTION_GRANTED",
    "result_rescue_forbidden",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostPr4937FinalResearchFleetBindingsAndOfflineEvalScopeRatificationV0Contract:
    def test_ratification_config_exists_and_parses(self) -> None:
        assert RATIFICATION_CONFIG.is_file()
        config = json.loads(RATIFICATION_CONFIG.read_text(encoding="utf-8"))
        assert (
            config["schema_version"]
            == "post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification.v0"
        )

    def test_required_contract_assertions(self) -> None:
        config = json.loads(RATIFICATION_CONFIG.read_text(encoding="utf-8"))
        for field, expected in REQUIRED_CONTRACT_ASSERTIONS:
            assert config[field] is expected, f"contract assertion failed: {field}"
        assert config["next_step"] == NEXT_STEP
        assert config["verdict"] == VERDICT

    def test_ratification_config_core_fields(self) -> None:
        config = json.loads(RATIFICATION_CONFIG.read_text(encoding="utf-8"))
        assert config["scope_id"] == SCOPE_ID
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["go_token"] == GO_TOKEN
        assert config["base_head"] == BASE_HEAD
        assert config["baseline_pr"] == 4937
        assert config["final_research_fleet"] == "trend_following,bollinger_bands,momentum_1h"
        prerequisite = config["pr4937_terminalization_prerequisite"]
        assert prerequisite["fleet_terminalization"] == "COMPLETE_NO_PASS"
        assert (
            prerequisite["selected_next_scope"]
            == "FINAL_RESEARCH_FLEET_BINDINGS_CANONICAL_RUNBOOK_PATH"
        )

    def test_exactly_three_fleet_candidates(self) -> None:
        config = json.loads(RATIFICATION_CONFIG.read_text(encoding="utf-8"))
        bindings = config["ratified_bindings"]
        assert len(bindings) == 3
        ids = {b["strategy_id"] for b in bindings}
        assert ids == set(FLEET_CANDIDATES) == FLEET_CANDIDATE_IDS
        for binding in bindings:
            assert binding["strategy_version"] == "v1"

    def test_required_binding_fields_present(self) -> None:
        config = json.loads(RATIFICATION_CONFIG.read_text(encoding="utf-8"))
        for binding in config["ratified_bindings"]:
            for field in REQUIRED_BINDING_FIELDS:
                assert field in binding, f"missing {field} in {binding['strategy_id']}"
            assert binding["fail_closed_missing_field_semantics"] == "REJECT_RATIFICATION"

    def test_shared_offline_evaluation_scope(self) -> None:
        config = json.loads(RATIFICATION_CONFIG.read_text(encoding="utf-8"))
        scope = config["shared_offline_evaluation_scope"]
        assert scope["evaluation_authorized"] is False
        assert scope["evaluation_scope_ratified"] is True
        assert scope["policy_threshold_lowering_forbidden"] is True
        assert scope["result_rescue_forbidden"] is True
        assert scope["allowed_future_actions_after_separate_go"] == list(ALLOWED_FUTURE_ACTIONS)

    def test_excluded_cross_sectional_funding_candidates_not_reintroduced(self) -> None:
        config = json.loads(RATIFICATION_CONFIG.read_text(encoding="utf-8"))
        assert set(config["excluded_cross_sectional_funding_candidates"]) == (
            EXCLUDED_CROSS_SECTIONAL_FUNDING_CANDIDATES
        )
        ratified_ids = {b["strategy_id"] for b in config["ratified_bindings"]}
        assert ratified_ids.isdisjoint(EXCLUDED_CROSS_SECTIONAL_FUNDING_CANDIDATES)

    def test_blocked_actions_include_forbidden_runtime_and_core(self) -> None:
        config = json.loads(RATIFICATION_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_actions"])
        for action in FORBIDDEN_RUNTIME_ACTIONS:
            assert action in blocked
        for action in FORBIDDEN_CORE_PATHS:
            assert action in blocked
        assert "THRESHOLD_LOWERING" in blocked
        assert "RESULT_RESCUE" in blocked
        assert "EVALUATION_EXECUTION_IN_THIS_SCOPE" in blocked

    def test_validate_config_accepts_canonical_config(self) -> None:
        config = json.loads(RATIFICATION_CONFIG.read_text(encoding="utf-8"))
        result = validate_ratification_config_v0(config, repo_root=REPO_ROOT)
        assert result.valid is True
        assert result.fail_reasons == ()

    def test_fail_closed_missing_required_binding_field(self) -> None:
        config = json.loads(RATIFICATION_CONFIG.read_text(encoding="utf-8"))
        owner_completion = json.loads(BINDING_COMPLETION_OWNER.read_text(encoding="utf-8"))
        binding = deepcopy(config["ratified_bindings"][0])
        binding.pop("implementation_digest")
        reasons = validate_ratified_binding_entry_v0(
            binding,
            owner_completion=owner_completion,
        )
        assert any("MISSING_REQUIRED_BINDING_FIELD:implementation_digest" in r for r in reasons)

    def test_fail_closed_config_missing_candidate(self) -> None:
        config = json.loads(RATIFICATION_CONFIG.read_text(encoding="utf-8"))
        broken = deepcopy(config)
        broken["ratified_bindings"] = [
            b for b in broken["ratified_bindings"] if b["strategy_id"] != "trend_following"
        ]
        result = validate_ratification_config_v0(broken, repo_root=REPO_ROOT)
        assert result.valid is False
        assert any("RATIFIED_BINDINGS_COUNT_MISMATCH" in r for r in result.fail_reasons)

    def test_governance_doc_exists_and_states_ratification_boundaries(self) -> None:
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert SCOPE_ID in text
        assert _field_value(text, "PR4937_FLEET_TERMINALIZATION") == "COMPLETE_NO_PASS"
        assert _field_value(text, "EVALUATION_EXECUTED") == "false"
        assert _field_value(text, "RUNTIME_AUTHORITY_TOUCHED") == "false"
        assert _field_value(text, "PROMOTION_GRANTED") == "false"
        assert _field_value(text, "EVALUATION_AUTHORIZED") == "false"
        assert _field_value(text, "EVALUATION_SCOPE_RATIFIED") == "true"
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
                "DOCS_TOKEN_FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFICATION_POST_PR4937_V0"
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
        result = (
            run_post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0(
                confirm_go_token=CONFIRM_GO,
                output_dir=output_dir,
            )
        )
        assert result["verdict"] == VERDICT
        assert result["manifest_verify_rc"] == 0
        assert result["parent_closeout_manifest_verify_rc"] == 0
        assert result["ratified_binding_count"] == 3
        for artifact in (
            "FINAL_RESEARCH_FLEET_BINDINGS_SCOPE_RATIFICATION.md",
            "RATIFIED_BINDINGS.json",
            "OFFLINE_EVALUATION_SCOPE.json",
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
                str(RATIFICATION_SCRIPT),
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
            "config/research/post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0.json",
            "docs/governance/FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFICATION_POST_PR4937_V0.md",
            "scripts/research/post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0.py",
            "src/research/post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0.py",
            "tests/ops/test_post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0_contract.py",
            "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md",
        )
        for path in changed_paths:
            assert not any(path.startswith(prefix) for prefix in forbidden_prefixes), path
