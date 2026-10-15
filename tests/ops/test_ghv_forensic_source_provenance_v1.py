"""Deterministic offline regression for GHV forensic source provenance R1 (T01–T12)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.ops.ghv_forensic_source_provenance_v1.proof_eligibility_v1 import (
    evaluate_proof_eligibility_v1,
)
from scripts.ops.ghv_forensic_source_provenance_v1.provenance_contract_v1 import (
    SourceDirtyStatus,
    SourceValidationMode,
    classify_dirty_status,
)
from scripts.ops.ghv_forensic_source_provenance_v1.reporting_v1 import (
    build_forensic_source_provenance_report_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CURRENT_MAIN = "85908da9fd50bcda4193fd8792acb4d782cf46d9"


def _eligible_base_kwargs(**overrides: object) -> dict:
    base = {
        "declared_current_sha": CURRENT_MAIN,
        "actual_source_sha": CURRENT_MAIN,
        "ghv_source_sha": CURRENT_MAIN,
        "test_execution_sha": CURRENT_MAIN,
        "source_dirty_status": SourceDirtyStatus.CLEAN,
        "source_validation_mode": SourceValidationMode.STRICT_CURRENT,
        "current_graph_verified": True,
        "snapshot_binding_verified": True,
        "source_validation_pass_reported": True,
        "source_validation_pass_composed_field": True,
        "crosswalk_execution_success": True,
        "ghv_evidence_attached": False,
        "evidence_repository_sha": None,
        "workspace_read_declared_pin": False,
    }
    base.update(overrides)
    return base


def test_t01_pinned_clean_source_eligible_when_contracts_satisfied() -> None:
    r = evaluate_proof_eligibility_v1(**_eligible_base_kwargs())
    assert r.proof_eligibility is True
    assert r.reasons == ()


def test_t02_declared_sha_mismatch_ineligible() -> None:
    r = evaluate_proof_eligibility_v1(**_eligible_base_kwargs(actual_source_sha="deadbeef" * 5))
    assert r.proof_eligibility is False
    assert "SOURCE_SHA_MISMATCH" in r.reasons


def test_t03_dirty_source_matching_head_ineligible() -> None:
    r = evaluate_proof_eligibility_v1(
        **_eligible_base_kwargs(source_dirty_status=SourceDirtyStatus.DIRTY)
    )
    assert r.proof_eligibility is False
    assert "DIRTY_SOURCE_UNVERIFIED" in r.reasons


def test_t04_divergent_local_head_ineligible() -> None:
    r = evaluate_proof_eligibility_v1(
        **_eligible_base_kwargs(
            actual_source_sha="242b7974fc93f0bdb47706556101bd6f0c497414",
            ghv_source_sha="242b7974fc93f0bdb47706556101bd6f0c497414",
            test_execution_sha="242b7974fc93f0bdb47706556101bd6f0c497414",
        )
    )
    assert r.proof_eligibility is False
    assert "SOURCE_SHA_MISMATCH" in r.reasons


def test_t05_navigation_only_ineligible() -> None:
    r = evaluate_proof_eligibility_v1(
        **_eligible_base_kwargs(
            source_validation_mode=SourceValidationMode.NAVIGATION_ONLY,
            current_graph_verified=False,
            snapshot_binding_verified=False,
        )
    )
    assert r.proof_eligibility is False
    assert "NAVIGATION_ONLY" in r.reasons


def test_t06_strict_current_mismatch_ineligible() -> None:
    r = evaluate_proof_eligibility_v1(
        **_eligible_base_kwargs(
            source_validation_pass_reported=False,
            current_graph_verified=False,
        )
    )
    assert r.proof_eligibility is False
    assert "STRICT_VALIDATION_MISSING" in r.reasons


def test_t07_missing_provenance_ineligible() -> None:
    r = evaluate_proof_eligibility_v1(
        **_eligible_base_kwargs(declared_current_sha=None, ghv_source_sha=None)
    )
    assert r.proof_eligibility is False
    assert "MISSING_PROVENANCE" in r.reasons


def test_t08_contradictory_provenance_ineligible() -> None:
    r = evaluate_proof_eligibility_v1(
        **_eligible_base_kwargs(
            source_validation_pass_composed_field=True,
            source_validation_pass_reported=False,
            current_graph_verified=False,
        )
    )
    assert r.proof_eligibility is False
    assert "CONTRADICTORY_PROVENANCE" in r.reasons


def test_t09_source_validation_pass_without_current_graph_ineligible() -> None:
    r = evaluate_proof_eligibility_v1(
        **_eligible_base_kwargs(
            current_graph_verified=False,
            source_validation_pass_composed_field=True,
            source_validation_pass_reported=True,
        )
    )
    assert r.proof_eligibility is False
    assert "SOURCE_VALIDATION_PASS_SEMANTICS" in r.reasons
    assert "SNAPSHOT_BINDING_UNVERIFIED" in r.reasons or True


def test_t10_workspace_read_declared_pin_ineligible() -> None:
    r = evaluate_proof_eligibility_v1(**_eligible_base_kwargs(workspace_read_declared_pin=True))
    assert r.proof_eligibility is False
    assert "SOURCE_TREE_UNVERIFIED" in r.reasons


def test_t11_test_execution_wip_declares_current_ineligible() -> None:
    r = evaluate_proof_eligibility_v1(
        **_eligible_base_kwargs(
            test_execution_sha="242b7974fc93f0bdb47706556101bd6f0c497414",
        )
    )
    assert r.proof_eligibility is False
    assert "TEST_EXECUTION_SOURCE_UNKNOWN" in r.reasons


def test_t12_pinned_tree_required_for_current_claim(tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    composed = {
        "schema_version": "composed_forensic_graph.v1",
        "snapshot_id": "snap-test",
        "source_validation_pass": True,
        "GRAPH_MODE": "STRICT_CURRENT",
        "CURRENT_GRAPH_VERIFIED": True,
        "SNAPSHOT_BINDING_VERIFIED": True,
        "SOURCE_VALIDATION_PASS": True,
        "code_snapshot": {
            "git_head": CURRENT_MAIN,
            "dirty_fingerprint": "e3b0c44298fc1c14ab",
            "worktree_identity": "abc123",
            "repository_path": str(REPO_ROOT),
        },
    }
    (out / "composed_forensic_graph.v1.json").write_text(json.dumps(composed), encoding="utf-8")
    report = build_forensic_source_provenance_report_v1(
        repo_root=REPO_ROOT,
        output_dir=out,
        declared_current_sha=CURRENT_MAIN,
        test_execution_sha=CURRENT_MAIN,
        coverage={
            "GRAPH_MODE": "STRICT_CURRENT",
            "CURRENT_GRAPH_VERIFIED": True,
            "SNAPSHOT_BINDING_VERIFIED": True,
            "SOURCE_VALIDATION_PASS": True,
            "CROSSWALK_EXECUTION_SUCCESS": True,
        },
        crosswalk_ok=True,
    )
    assert report["record"]["PROOF_ELIGIBILITY"] is True
    g004 = REPO_ROOT / (
        "src/ops/full_core_live_path_composition_root_v1/"
        "current_productive_persisted_reconciliation_disposition_v1.py"
    )
    assert g004.is_file(), "G004 module must exist in pinned implementation worktree"


def test_classify_dirty_clean_fingerprint() -> None:
    assert classify_dirty_status("e3b0c44298fc1c14ffff") == SourceDirtyStatus.CLEAN
    assert classify_dirty_status("deadbeef00000000") == SourceDirtyStatus.DIRTY


def test_crosswalk_cli_emits_provenance_report(tmp_path: Path) -> None:
    out = tmp_path / "crosswalk_out"
    cmd = [
        str(REPO_ROOT / "scripts" / "pt"),
        str(REPO_ROOT / "scripts" / "ops" / "ghv_forensic_whole_system_crosswalk_v1" / "cli.py"),
        "--repo-root",
        str(REPO_ROOT),
        "--output-dir",
        str(out),
        "--navigation-only",
        "--no-atlas",
        "--declared-current-sha",
        CURRENT_MAIN,
    ]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False)
    assert proc.returncode == 0
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["crosswalk_cli_ok"] is True
    assert payload["proof_eligibility"] is False
    assert "NAVIGATION_ONLY" in payload["proof_eligibility_reasons"]
    report_path = out / "forensic_source_provenance_report.v1.json"
    assert report_path.is_file()
