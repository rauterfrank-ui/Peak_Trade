"""Cross-file binding contract tests for GHOSV execution offline consistency guard."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    LEDGER_FILENAME,
)
from src.ops.ghosv_bounded_context_v1.execution_offline_consistency_guard_v1 import (
    ENTRY_STATE_SNAPSHOT_FILENAME,
    PRE_EXTERNAL_REPORT_FILENAME,
    S5_CYCLE_AUTHORIZATION_FILENAME,
    discover_repository_root_from_paths_v1,
    resolve_persisted_evidence_root_v1,
    run_consistency_guard_v1,
    verify_cross_file_bindings_v1,
)


def _init_repo_root(base: Path) -> Path:
    repo = base / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    (repo / ".git").mkdir()
    return repo


def _write_witnessed_run_bundle(
    repo: Path,
    *,
    run_slug: str = "runs/run-a",
    run_id: str = "e0ac0f0955d15a0b",
    native_id: str = "BTC-USDT-SWAP",
    cycle_hash: str = "48cf857337ef5f1f8249146ff607c24787afe0ec2124b406b6cb4321801c4cd5",
    cycle_index: int = 7,
    binding_digest: str = "digest-a",
    evidence_root_in_pre: str | None = None,
) -> tuple[Path, Path, Path]:
    repo.mkdir(parents=True, exist_ok=True)
    rel = Path(run_slug)
    run_dir = repo / rel
    cycle_instance = run_dir / "cycles" / cycle_hash
    s5_dir = cycle_instance / "s5"
    s5_dir.mkdir(parents=True)

    evidence_root_value = evidence_root_in_pre if evidence_root_in_pre is not None else str(rel)

    pre_payload = {
        "NATIVE_ID": native_id,
        "RUN_ID": run_id,
        "EVIDENCE_ROOT": evidence_root_value,
        "REPORTING_S5_CYCLE_INDEX": str(cycle_index),
    }
    pre_path = run_dir / PRE_EXTERNAL_REPORT_FILENAME
    pre_path.write_text(json.dumps(pre_payload, indent=2), encoding="utf-8")

    snapshot = {
        "run_id": run_id,
        "continuous_run_id": run_id,
        "schema_version": "continuous_run_entry_state_snapshot.v1",
    }
    (run_dir / ENTRY_STATE_SNAPSHOT_FILENAME).write_text(
        json.dumps(snapshot, indent=2), encoding="utf-8"
    )

    auth = {
        "consume_instance_id": cycle_hash,
        "cycle_instance_id": cycle_hash,
        "cycle_index": cycle_index,
        "evidence_root": str(rel / "cycles" / cycle_hash),
    }
    (cycle_instance / S5_CYCLE_AUTHORIZATION_FILENAME).write_text(
        json.dumps(auth, indent=2), encoding="utf-8"
    )

    ledger = {
        "state": "COMPLETED",
        "binding_digest": binding_digest,
        "native_id": native_id,
        "POST_COUNT": "0",
    }
    (s5_dir / LEDGER_FILENAME).write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    return run_dir, pre_path, s5_dir


def test_relative_evidence_root_independent_of_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repo = _init_repo_root(tmp_path)
    _, pre_path, s5_dir = _write_witnessed_run_bundle(repo)
    foreign = tmp_path / "foreign_cwd"
    foreign.mkdir()
    monkeypatch.chdir(foreign)

    guard = run_consistency_guard_v1(
        recon_dir=None,
        pre_external_report=pre_path,
        final_order_envelope=None,
        governed_cycle_evidence_dir=s5_dir,
        g004_post_attempt_store_root=None,
        repository_root=repo,
        operator_trade_id="e0ac0f0955d15a0b",
    )
    assert guard.cross_file.consistency == "PASS"
    assert guard.cross_file.reason_codes == ("CROSS_FILE_CHECKS_OK",)
    assert "RUN_ID_PATH_WEAK_BINDING" not in guard.cross_file.reason_codes


def test_relative_evidence_root_without_repository_anchor_unknown(tmp_path: Path):
    """Without git-discoverable repository root, relative EVIDENCE_ROOT stays unanchored."""
    repo = tmp_path / "not_a_git_repo"
    _, pre_path, s5_dir = _write_witnessed_run_bundle(repo)
    guard = verify_cross_file_bindings_v1(
        pre_external_report=pre_path,
        governed_cycle_evidence_dir=s5_dir,
        g004_store_root=None,
        repository_root=None,
    )
    assert "EVIDENCE_ROOT_REPOSITORY_ANCHOR_REQUIRED" in guard.reason_codes


def test_absolute_evidence_root_valid(tmp_path: Path):
    repo = _init_repo_root(tmp_path)
    run_dir, pre_path, s5_dir = _write_witnessed_run_bundle(
        repo, evidence_root_in_pre=str((repo / "runs/run-a").resolve())
    )
    guard = verify_cross_file_bindings_v1(
        pre_external_report=pre_path,
        governed_cycle_evidence_dir=s5_dir,
        g004_store_root=None,
        repository_root=repo,
    )
    assert guard.consistency == "PASS"
    assert run_dir in pre_path.parents


def test_evidence_root_prefix_trap_still_fails(tmp_path: Path):
    repo = _init_repo_root(tmp_path)
    evidence_root = repo / "runs" / "abc"
    evidence_root.mkdir(parents=True)
    wrong_cycle = repo / "runs" / "abcdef" / "cyclehash" / "s5"
    wrong_cycle.mkdir(parents=True)
    (wrong_cycle / LEDGER_FILENAME).write_text(
        json.dumps({"native_id": "BTC-USDT-SWAP", "binding_digest": "d"}), encoding="utf-8"
    )
    pre = evidence_root / PRE_EXTERNAL_REPORT_FILENAME
    pre.write_text(
        json.dumps(
            {
                "NATIVE_ID": "BTC-USDT-SWAP",
                "RUN_ID": "run-1",
                "EVIDENCE_ROOT": str(evidence_root),
            }
        ),
        encoding="utf-8",
    )
    guard = verify_cross_file_bindings_v1(
        pre_external_report=pre,
        governed_cycle_evidence_dir=wrong_cycle,
        g004_store_root=None,
        repository_root=repo,
    )
    assert "RUN_CYCLE_PATH_NOT_UNDER_EVIDENCE_ROOT" in guard.reason_codes


def test_evidence_root_traversal_rejected(tmp_path: Path):
    repo = _init_repo_root(tmp_path)
    resolved, reasons = resolve_persisted_evidence_root_v1(
        evidence_root_raw="../outside",
        repository_root=repo,
    )
    assert resolved is None
    assert "EVIDENCE_ROOT_TRAVERSAL_REJECTED" in reasons


def test_symlink_escape_outside_run_root_fails(tmp_path: Path):
    repo = _init_repo_root(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    s5_outside = outside / "s5"
    s5_outside.mkdir()
    (s5_outside / LEDGER_FILENAME).write_text(
        json.dumps({"native_id": "BTC-USDT-SWAP", "binding_digest": "d"}), encoding="utf-8"
    )

    run_dir, pre_path, _ = _write_witnessed_run_bundle(repo)
    link_parent = run_dir / "cycles" / "linkcycle"
    link_parent.mkdir()
    symlink_s5 = link_parent / "s5"
    symlink_s5.symlink_to(s5_outside, target_is_directory=True)

    guard = verify_cross_file_bindings_v1(
        pre_external_report=pre_path,
        governed_cycle_evidence_dir=symlink_s5,
        g004_store_root=None,
        repository_root=repo,
    )
    assert "RUN_CYCLE_PATH_NOT_UNDER_EVIDENCE_ROOT" in guard.reason_codes


def test_valid_run_without_run_id_in_path(tmp_path: Path):
    repo = _init_repo_root(tmp_path)
    _, pre_path, s5_dir = _write_witnessed_run_bundle(
        repo, run_id="deadbeefdeadbeef", cycle_hash="a" * 64
    )
    guard = verify_cross_file_bindings_v1(
        pre_external_report=pre_path,
        governed_cycle_evidence_dir=s5_dir,
        g004_store_root=None,
        repository_root=repo,
    )
    assert guard.consistency == "PASS"
    assert "RUN_ID_PATH_WEAK_BINDING" not in guard.reason_codes


def test_run_id_snapshot_mismatch_fails(tmp_path: Path):
    repo = _init_repo_root(tmp_path)
    _, pre_path, s5_dir = _write_witnessed_run_bundle(repo, run_id="aaa")
    snap_path = pre_path.parent / ENTRY_STATE_SNAPSHOT_FILENAME
    snap = json.loads(snap_path.read_text(encoding="utf-8"))
    snap["run_id"] = "bbb"
    snap_path.write_text(json.dumps(snap), encoding="utf-8")
    guard = verify_cross_file_bindings_v1(
        pre_external_report=pre_path,
        governed_cycle_evidence_dir=s5_dir,
        g004_store_root=None,
        repository_root=repo,
    )
    assert "RUN_ID_SNAPSHOT_PRE_EXTERNAL_MISMATCH" in guard.reason_codes
    assert guard.consistency == "FAIL"


def test_cycle_instance_id_path_mismatch_fails(tmp_path: Path):
    repo = _init_repo_root(tmp_path)
    _, pre_path, s5_dir = _write_witnessed_run_bundle(repo)
    auth_path = s5_dir.parent / S5_CYCLE_AUTHORIZATION_FILENAME
    auth = json.loads(auth_path.read_text(encoding="utf-8"))
    auth["consume_instance_id"] = "b" * 64
    auth_path.write_text(json.dumps(auth), encoding="utf-8")
    guard = verify_cross_file_bindings_v1(
        pre_external_report=pre_path,
        governed_cycle_evidence_dir=s5_dir,
        g004_store_root=None,
        repository_root=repo,
    )
    assert "CYCLE_INSTANCE_ID_PATH_MISMATCH" in guard.reason_codes


def test_cycle_index_mismatch_fails(tmp_path: Path):
    repo = _init_repo_root(tmp_path)
    _, pre_path, s5_dir = _write_witnessed_run_bundle(repo, cycle_index=7)
    pre_payload = json.loads(pre_path.read_text(encoding="utf-8"))
    pre_payload["REPORTING_S5_CYCLE_INDEX"] = "3"
    pre_path.write_text(json.dumps(pre_payload, indent=2), encoding="utf-8")
    guard = verify_cross_file_bindings_v1(
        pre_external_report=pre_path,
        governed_cycle_evidence_dir=s5_dir,
        g004_store_root=None,
        repository_root=repo,
    )
    assert "CYCLE_INDEX_CROSS_FILE_MISMATCH" in guard.reason_codes


def test_operator_trade_id_run_id_mismatch_fails(tmp_path: Path):
    repo = _init_repo_root(tmp_path)
    _, pre_path, s5_dir = _write_witnessed_run_bundle(repo)
    guard = verify_cross_file_bindings_v1(
        pre_external_report=pre_path,
        governed_cycle_evidence_dir=s5_dir,
        g004_store_root=None,
        repository_root=repo,
        operator_trade_id="not-the-run-id",
    )
    assert "OPERATOR_TRADE_ID_RUN_ID_MISMATCH" in guard.reason_codes


def test_discover_repository_root_from_pre_external(tmp_path: Path):
    repo = _init_repo_root(tmp_path)
    _, pre_path, _ = _write_witnessed_run_bundle(repo)
    discovered = discover_repository_root_from_paths_v1(pre_path)
    assert discovered == repo.resolve()


def test_cross_run_cycle_mixture_fails(tmp_path: Path):
    repo = _init_repo_root(tmp_path)
    _, pre_path, s5_dir = _write_witnessed_run_bundle(repo, run_slug="runs/run-a")
    _, _, other_s5 = _write_witnessed_run_bundle(
        repo,
        run_slug="runs/run-b",
        cycle_hash="b" * 64,
        run_id="cccccccccccccccc",
    )
    guard = verify_cross_file_bindings_v1(
        pre_external_report=pre_path,
        governed_cycle_evidence_dir=other_s5,
        g004_store_root=None,
        repository_root=repo,
    )
    assert guard.consistency == "FAIL"
    assert (
        "RUN_CYCLE_PATH_NOT_UNDER_EVIDENCE_ROOT" in guard.reason_codes
        or "PRE_EXTERNAL_EVIDENCE_ROOT_LOCATION_MISMATCH" in guard.reason_codes
    )


def test_missing_run_entry_snapshot_unknown(tmp_path: Path):
    repo = _init_repo_root(tmp_path)
    run_dir, pre_path, s5_dir = _write_witnessed_run_bundle(repo)
    (run_dir / ENTRY_STATE_SNAPSHOT_FILENAME).unlink()
    guard = verify_cross_file_bindings_v1(
        pre_external_report=pre_path,
        governed_cycle_evidence_dir=s5_dir,
        g004_store_root=None,
        repository_root=repo,
    )
    assert "RUN_ENTRY_STATE_SNAPSHOT_MISSING" in guard.reason_codes
    assert guard.consistency == "UNKNOWN"
