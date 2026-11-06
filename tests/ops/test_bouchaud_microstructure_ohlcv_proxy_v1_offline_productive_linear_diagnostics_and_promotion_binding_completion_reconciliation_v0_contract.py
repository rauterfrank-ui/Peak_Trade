"""Contract tests for Bouchaud offline linear diagnostics promotion binding reconciliation v0."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.governance.bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_and_promotion_binding_completion_reconciliation_v0 import (
    AUTHORITATIVE_TRUTH,
    GO_TOKEN,
    PR5191_IMPLEMENTATION_DIR,
    PR5192_IMPLEMENTATION_DIR,
    PR5189_CLOSEOUT_DIR,
    PR5190_CLOSEOUT_DIR,
    PR5190_IMPLEMENTATION_DIR,
    PR5191_CLOSEOUT_DIR,
    PR5192_CLOSEOUT_DIR,
    PR5193_CLOSEOUT_DIR,
    PR_CHAIN,
    SCOPE,
    build_closeout_binding_map_v0,
    build_pr_chain_json_v0,
    build_reuse_decision_v0,
    deterministic_materialization_digest,
    reject_contradictory_pass_when_gate_false,
    reject_invalid_manifest_status,
    reject_missing_closeout_reference,
    validate_authoritative_truth_fields,
    validate_pr_chain_order,
    verify_source_derivation_manifest,
)
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_execution_and_support_evidence_v0 import (
    CANONICAL_FEATURE_DIGEST,
)
from src.research.linear_evidence.offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0 import (
    BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT,
)
from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

REPO_ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER = REPO_ROOT / (
    "scripts/ops/"
    "materialize_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "and_promotion_binding_completion_reconciliation_v0.py"
)
PROMOTION_MATERIALIZER = REPO_ROOT / (
    "scripts/ops/"
    "materialize_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "promotion_economic_gate_consumer_binding_v0.py"
)


def _archive_available() -> bool:
    return all(
        path.is_dir()
        for path in (
            PR5189_CLOSEOUT_DIR,
            PR5190_CLOSEOUT_DIR,
            PR5190_IMPLEMENTATION_DIR,
            PR5191_CLOSEOUT_DIR,
            PR5192_CLOSEOUT_DIR,
            PR5193_CLOSEOUT_DIR,
            PR5191_IMPLEMENTATION_DIR,
            PR5192_IMPLEMENTATION_DIR,
        )
    )


def _load_promotion_bind_fn():
    spec = importlib.util.spec_from_file_location(
        "bouchaud_promotion_materializer_v0",
        PROMOTION_MATERIALIZER,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.bind_bouchaud_promotion_economic_gate_consumer_v0


@pytest.fixture(scope="module")
def closeout_records():
    if not _archive_available():
        pytest.skip("PR5189-5193 closeout archives unavailable")
    records = build_closeout_binding_map_v0(verify_manifest_sha256)
    validate_pr_chain_order(records)
    return records


class TestScopeIdentity:
    def test_scope_and_go_token(self) -> None:
        assert SCOPE.startswith("BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1")
        assert GO_TOKEN.startswith("GO_BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1")

    def test_reuse_decision_matches_pr5188_pattern(self) -> None:
        reuse = build_reuse_decision_v0()
        assert reuse["decision"] == "REUSE_WITH_NARROW_ADAPTER"
        assert reuse["reuse_source_pattern"] == "PR5188"
        assert reuse["runbook_mutation"] == "FORBIDDEN_BY_OPERATOR_SCOPE"


class TestPrChainBinding:
    def test_pr5190_closeout_log_drift_uses_implementation_ssot(self, closeout_records) -> None:
        record = next(item for item in closeout_records if item.pr == "5190")
        assert record.closeout_manifest_log_drift is True
        assert record.manifest_verify_rc == 0
        assert record.evidence_binding_dir.name.startswith(
            "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
            "feature_matrix_binding_v0_"
        )
        chain = build_pr_chain_json_v0(closeout_records)
        assert [item["pr"] for item in chain["chain"]] == [
            "5189",
            "5190",
            "5191",
            "5192",
            "5193",
        ]
        for expected, actual in zip(PR_CHAIN, chain["chain"]):
            assert actual["merge_commit"] == expected["merge_commit"]
            assert actual["manifest_verify_rc"] == 0

    def test_bouchaud_promotion_consumer_remains_blocked(self, closeout_records) -> None:
        bind_fn = _load_promotion_bind_fn()
        _, _, promotion_result = bind_fn(
            pr5191_implementation_dir=PR5191_IMPLEMENTATION_DIR,
            pr5192_implementation_dir=PR5192_IMPLEMENTATION_DIR,
            expected_feature_digest=CANONICAL_FEATURE_DIGEST,
            verify_fn=verify_manifest_sha256,
        )
        payload = promotion_result.to_dict()
        assert payload["promotion_economic_gate_status"] == "BLOCKED"
        assert BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT in payload["blocking_reason"]
        assert payload["economic_evaluation_executed"] is False
        assert payload["promotion_pass_created"] is False
        assert payload["promotion_candidate_eligible"] is False

    def test_authoritative_truth_validated(self, closeout_records) -> None:
        bind_fn = _load_promotion_bind_fn()
        _, _, promotion_result = bind_fn(
            pr5191_implementation_dir=PR5191_IMPLEMENTATION_DIR,
            pr5192_implementation_dir=PR5192_IMPLEMENTATION_DIR,
            expected_feature_digest=CANONICAL_FEATURE_DIGEST,
            verify_fn=verify_manifest_sha256,
        )
        payload = promotion_result.to_dict()
        observed = validate_authoritative_truth_fields(
            promotion_economic_gate_status=payload["promotion_economic_gate_status"],
            blocking_reason=payload["blocking_reason"],
            feature_digest=CANONICAL_FEATURE_DIGEST,
        )
        assert observed == AUTHORITATIVE_TRUTH


class TestDeterministicMaterialization:
    def test_repeated_digest_identical(self, closeout_records) -> None:
        payload = build_pr_chain_json_v0(closeout_records)
        assert deterministic_materialization_digest(
            payload
        ) == deterministic_materialization_digest(payload)

    def test_materializer_produces_manifest_verified_bundle(self, tmp_path: Path) -> None:
        if not _archive_available():
            pytest.skip("PR5189-5193 closeout archives unavailable")
        out_dir = tmp_path / "evidence"
        proc = subprocess.run(
            [sys.executable, str(MATERIALIZER), "--out", str(out_dir), "--skip-focused-tests"],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            env={"PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}"},
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        ok, _msg = verify_manifest_sha256(out_dir)
        assert ok is True


class TestFailClosedGuards:
    def test_missing_closeout_reference_rejected(self) -> None:
        with pytest.raises(Exception):
            reject_missing_closeout_reference(None)

    def test_invalid_manifest_status_rejected(self) -> None:
        with pytest.raises(Exception):
            reject_invalid_manifest_status(1)

    def test_contradictory_pass_with_gate_false_rejected(self) -> None:
        with pytest.raises(Exception):
            reject_contradictory_pass_when_gate_false(False, "PASS")

    def test_source_derivation_manifest_verifies(self) -> None:
        if not _archive_available():
            pytest.skip("PR5189-5193 closeout archives unavailable")
        assert verify_source_derivation_manifest(verify_fn=verify_manifest_sha256) == 0


class TestPolicyBlocksPreserved:
    def test_no_implementation_gap_and_policy_block_only(self) -> None:
        assert AUTHORITATIVE_TRUTH["NO_IMPLEMENTATION_GAP"] == "true"
        assert AUTHORITATIVE_TRUTH["REMAINING_BLOCK_CLASS"] == "POLICY_BLOCK_ONLY"
        assert AUTHORITATIVE_TRUTH["UNCHANGED_RETRY_BLOCKED"] == "true"
        assert AUTHORITATIVE_TRUTH["POLICY_RESCUE_ALLOWED"] == "false"
        assert AUTHORITATIVE_TRUTH["ECONOMIC_VALIDITY_OFFLINE_GATE_PASS"] == "false"

    def test_closeout_binding_map_json_roundtrip(self, closeout_records) -> None:
        payload = build_pr_chain_json_v0(closeout_records)
        roundtrip = json.loads(json.dumps(payload, sort_keys=True))
        assert roundtrip == payload
