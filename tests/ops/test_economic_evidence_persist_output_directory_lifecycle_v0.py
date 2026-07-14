"""Focused regression tests for economic evidence output directory lifecycle v0."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.backtest import economic_viability_evidence_v1 as ev
from tests.ops.test_run_economic_viability_evidence_evaluation_v1 import (
    RUNNER_SCRIPT,
    _argv,
    _load_runner,
    _stage_run_inputs,
)


@pytest.fixture
def runner():
    return _load_runner()


def test_persist_fresh_parent_final_target_absent(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    rc = runner.main(_argv(paths))
    assert rc == 0
    assert paths["output_dir"].is_dir()
    assert (paths["output_dir"] / ev.ARTIFACT_FILENAME).is_file()
    ok, _msg = verify_manifest_sha256(paths["output_dir"])
    assert ok is True


def test_persist_existing_parent_final_target_absent(runner, tmp_path: Path) -> None:
    workspace = tmp_path / "evidence_workspace"
    workspace.mkdir()
    (workspace / "preflight.txt").write_text("parent workspace marker\n", encoding="utf-8")
    paths = _stage_run_inputs(tmp_path)
    paths["output_dir"] = workspace / "runner_output"
    rc = runner.main(_argv(paths, allow_existing_output=True))
    assert rc == 0
    assert paths["output_dir"].is_dir()
    assert (paths["output_dir"] / ev.ARTIFACT_FILENAME).is_file()


def test_precreated_empty_final_target_fail_closed(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    paths["output_dir"].mkdir()
    rc = runner.main(_argv(paths, allow_existing_output=True))
    assert rc != 0
    assert not (paths["output_dir"] / ev.ARTIFACT_FILENAME).exists()


def test_precreated_nonempty_final_target_fail_closed(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)
    paths["output_dir"].mkdir()
    (paths["output_dir"] / "stale.txt").write_text("stale", encoding="utf-8")
    rc = runner.main(_argv(paths, allow_existing_output=True))
    assert rc != 0
    assert (paths["output_dir"] / "stale.txt").read_text(encoding="utf-8") == "stale"


def test_allow_existing_output_does_not_authorize_final_target_reuse(
    runner, tmp_path: Path
) -> None:
    paths = _stage_run_inputs(tmp_path)
    paths["output_dir"].mkdir()
    existing = paths["output_dir"] / ev.ARTIFACT_FILENAME
    existing.write_text('{"status":"STALE"}\n', encoding="utf-8")
    rc = runner.main(_argv(paths, allow_existing_output=True))
    assert rc != 0
    assert json.loads(existing.read_text(encoding="utf-8"))["status"] == "STALE"


def test_runner_persist_integration_real_path_no_mock(runner, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    paths = _stage_run_inputs(tmp_path)
    paths["output_dir"] = workspace / "economic_bundle"
    rc = runner.main(_argv(paths, allow_existing_output=True))
    assert rc == 0
    assert (paths["output_dir"] / "run_summary.env").is_file()
    assert (paths["output_dir"] / "MANIFEST.sha256").is_file()


def test_partial_persist_failure_does_not_report_complete(runner, tmp_path: Path) -> None:
    paths = _stage_run_inputs(tmp_path)

    def _fail_persist(output_dir, **kwargs):
        raise ev.EconomicViabilityEvidenceError("persist_failed:simulated")

    with patch.object(
        ev,
        "build_and_persist_economic_viability_evidence_bundle_v1",
        _fail_persist,
    ):
        rc = runner.main(_argv(paths))
    assert rc != 0
    assert not paths["output_dir"].exists()


def test_deterministic_fixture_two_fresh_targets(runner, tmp_path: Path) -> None:
    paths_a = _stage_run_inputs(tmp_path / "a")
    paths_b = _stage_run_inputs(tmp_path / "b")
    assert runner.main(_argv(paths_a)) == 0
    assert runner.main(_argv(paths_b)) == 0
    for name in (
        "economic_viability_evidence_v1.json",
        "dataset_admissibility_result_v1.json",
        "economic_validity_evaluation_v1.json",
    ):
        a = json.loads((paths_a["output_dir"] / name).read_text(encoding="utf-8"))
        b = json.loads((paths_b["output_dir"] / name).read_text(encoding="utf-8"))
        assert a == b


def test_validate_output_dir_contract_helper(runner, tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    parent.mkdir()
    final_target = parent / "bundle"
    runner._resolve_persist_output_dir(final_target, allow_existing_parent=True)
    with pytest.raises(runner.RunnerError, match="output_dir_exists"):
        final_target.mkdir()
        runner._resolve_persist_output_dir(final_target, allow_existing_parent=True)


def test_runner_source_documents_persist_alignment() -> None:
    source = RUNNER_SCRIPT.read_text(encoding="utf-8")
    assert "persist_economic_viability_evidence_bundle_v1" in source
    assert "allow_existing_parent" in source
    assert "must not already exist" in source
