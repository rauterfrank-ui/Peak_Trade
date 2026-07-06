"""Contract tests for post-PR4938 final research fleet offline economic evaluation execution v0."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.research.post_pr4938_final_research_fleet_offline_economic_evaluation_execution_v0 import (
    CONFIRM_GO,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    PR4938_CLOSEOUT_SUFFIX,
    PR4938_MERGE_COMMIT,
    PROCESS_CLASSIFICATION,
    SCOPE_CLASSIFICATION,
    verify_binding_integrity_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_SCRIPT = (
    REPO_ROOT
    / "scripts/research/execute_post_pr4938_final_research_fleet_offline_economic_evaluation_v0.py"
)
EXECUTION_MODULE = (
    REPO_ROOT
    / "src/research/post_pr4938_final_research_fleet_offline_economic_evaluation_execution_v0.py"
)
PR4938_CLOSEOUT_DIR = DEFAULT_DURABLE_ARCHIVE_ROOT / "research" / PR4938_CLOSEOUT_SUFFIX


class TestPostPr4938FinalResearchFleetOfflineEconomicEvaluationExecutionV0Contract:
    def test_go_token_and_scope_classification(self) -> None:
        assert (
            CONFIRM_GO
            == "GO_EXECUTE_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_ONLY_NO_RUNTIME_AUTHORITY_V0"
        )
        assert (
            SCOPE_CLASSIFICATION
            == "FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_AFTER_PR4938_NO_RUNTIME_AUTHORITY_V0"
        )
        assert (
            PROCESS_CLASSIFICATION
            == "BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_ONLY"
        )
        assert PR4938_MERGE_COMMIT == "cd33cd097f5cae512024b9cbf15a9396ef8a1b5e"

    def test_runner_and_module_exist(self) -> None:
        assert RUNNER_SCRIPT.is_file()
        assert EXECUTION_MODULE.is_file()

    def test_pr4938_closeout_manifest_verifies(self) -> None:
        if not PR4938_CLOSEOUT_DIR.is_dir():
            pytest.skip("PR4938 closeout evidence not present locally")
        ok, _msg = verify_manifest_sha256(PR4938_CLOSEOUT_DIR)
        assert ok

    def test_binding_integrity_passes_on_main(self) -> None:
        ok, status, _ratification, _binding = verify_binding_integrity_v0(repo_root=REPO_ROOT)
        assert ok, status
        assert status == "BINDING_INTEGRITY_PASS"

    def test_invalid_go_token_rejected(self) -> None:
        from src.research.post_pr4938_final_research_fleet_offline_economic_evaluation_execution_v0 import (
            run_bounded_scope_v0,
        )

        with pytest.raises(ValueError, match="GO_TOKEN_INVALID"):
            run_bounded_scope_v0(
                confirm="INVALID_GO",
                repo_root=REPO_ROOT,
                durable_evidence_root=DEFAULT_DURABLE_ARCHIVE_ROOT,
            )
