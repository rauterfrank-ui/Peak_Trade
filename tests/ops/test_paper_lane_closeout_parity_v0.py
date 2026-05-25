"""Contract tests for paper-lane bounded observation closeout parity v0."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Mapping, Sequence

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PAPER_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_paper_only_bounded_observation_adapter_v0.py"
REGISTRY_SCRIPT = REPO_ROOT / "scripts" / "ops" / "build_generic_evidence_run_registry_v1.py"
APPROVAL_FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "ops" / "paper_only_adapter_stage3_approval_sample.md"
)
RUN_ID = "paper_lane_closeout_parity_fixture_v0"


def _load_paper_adapter():
    spec = importlib.util.spec_from_file_location(
        "run_paper_only_bounded_observation_adapter_v0_parity",
        PAPER_ADAPTER,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_registry():
    spec = importlib.util.spec_from_file_location(
        "build_generic_evidence_run_registry_v1_parity",
        REGISTRY_SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _staging(tmp_path: Path) -> Path:
    return Path("/tmp") / f"peak_trade_paper_closeout_parity_{tmp_path.name}"


def _durable_archive(tmp_path: Path) -> Path:
    path = REPO_ROOT / "tests" / ".pytest_archive_roots" / tmp_path.name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_minimal_paper_runtime_bundle(staging: Path) -> None:
    runtime_out = staging / "runtime_out"
    runtime_out.mkdir(parents=True, exist_ok=True)
    (runtime_out / "account.json").write_text("{}\n", encoding="utf-8")
    (runtime_out / "fills.json").write_text("[]\n", encoding="utf-8")
    (runtime_out / "evidence_manifest.json").write_text(
        json.dumps({"schema": "paper_runtime_evidence.v0"}) + "\n",
        encoding="utf-8",
    )
    logs = staging / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "scheduler_stdout.log").write_text("stdout\n", encoding="utf-8")
    (logs / "scheduler_stderr.log").write_text("stderr\n", encoding="utf-8")


@pytest.fixture(autouse=True)
def _cleanup_durable_archive_dirs():
    yield
    archive_roots = REPO_ROOT / "tests" / ".pytest_archive_roots"
    if archive_roots.is_dir():
        shutil.rmtree(archive_roots, ignore_errors=True)


def test_paper_adapter_exposes_write_closeout_artifacts() -> None:
    text = PAPER_ADAPTER.read_text(encoding="utf-8")
    assert "_write_closeout_artifacts" in text
    assert "RUN_METADATA.json" in text
    assert "CLOSEOUT.md" in text


def test_execute_emits_closeout_artifacts_with_non_authority_markers(tmp_path: Path) -> None:
    mod = _load_paper_adapter()
    staging = _staging(tmp_path)
    archive = _durable_archive(tmp_path)

    def _runner(
        argv: Sequence[str],
        _cwd,
        _stdout,
        _stderr,
        *,
        extra_env: Mapping[str, str] | None = None,
    ) -> int:
        if "run_with_timeout.py" in " ".join(argv):
            _write_minimal_paper_runtime_bundle(staging)
            return mod.TIMEOUT_EXIT
        if "review_scheduler_paper_runtime_evidence.py" in " ".join(argv):
            review_dir = staging / "review"
            review_dir.mkdir(parents=True, exist_ok=True)
            (review_dir / "REVIEW_RESULT.json").write_text(
                json.dumps({"verdict": "PASS", "metrics": {}, "issues": []}),
                encoding="utf-8",
            )
            return 0
        return 0

    rc = mod.main(
        [
            "--staging-root",
            str(staging),
            "--archive-root",
            str(archive),
            "--repo-root",
            str(REPO_ROOT),
            "--run-id",
            RUN_ID,
            "--execute",
            "--approval-record",
            str(APPROVAL_FIXTURE),
            "--no-strict-repo-clean",
        ],
        subprocess_runner=_runner,
        repo_clean_checker=lambda _root: (True, ""),
    )
    assert rc == 0

    archive_dest = archive / "runs" / "paper" / RUN_ID
    for rel in (
        "CLOSEOUT.md",
        "RUN_METADATA.json",
        "POSTRUN_ANALYSIS.md",
        "review/REVIEW_RESULT.json",
        "MANIFEST.sha256",
    ):
        assert (archive_dest / rel).is_file(), rel

    metadata = json.loads((archive_dest / "RUN_METADATA.json").read_text(encoding="utf-8"))
    assert metadata["live_authority"] is False
    assert metadata["testnet_authority"] is False
    assert metadata["broker_authority"] is False

    closeout = (archive_dest / "CLOSEOUT.md").read_text(encoding="utf-8")
    assert "live_authority=false" in closeout
    assert "testnet_authority=false" in closeout
    assert "broker_authority=false" in closeout
    assert "LIVE_ALLOWED=false" in closeout


def test_validate_durable_primary_evidence_root_passes_for_paper_fixture(tmp_path: Path) -> None:
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import (
        PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
        validate_durable_primary_evidence_root,
        write_manifest_sha256,
    )

    durable = _durable_archive(tmp_path) / "runs" / "paper" / RUN_ID
    _write_minimal_paper_runtime_bundle(durable)
    review_dir = durable / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "REVIEW_RESULT.json").write_text(
        json.dumps({"verdict": "PASS", "issues": []}) + "\n",
        encoding="utf-8",
    )
    (durable / "RUN_METADATA.json").write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "live_authority": False,
                "testnet_authority": False,
                "broker_authority": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (durable / "CLOSEOUT.md").write_text(
        "live_authority=false\ntestnet_authority=false\nbroker_authority=false\n",
        encoding="utf-8",
    )
    write_manifest_sha256(durable)

    ok, reason, detail = validate_durable_primary_evidence_root(
        durable,
        required_rel_paths=PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
    )
    assert ok is True, reason
    assert detail["checks"]["durable_review_verdict_pass"] is True
    assert detail["checks"]["manifest_sha256_verify"] is True


def test_registry_v1_indexes_paper_lane_not_new_lane_id(tmp_path: Path) -> None:
    archive = _durable_archive(tmp_path)
    run_dir = archive / "runs" / "paper" / RUN_ID
    _write_minimal_paper_runtime_bundle(run_dir)
    review_dir = run_dir / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "REVIEW_RESULT.json").write_text(
        json.dumps({"verdict": "PASS", "issues": []}) + "\n",
        encoding="utf-8",
    )
    (run_dir / "RUN_METADATA.json").write_text('{"run_id": "' + RUN_ID + '"}\n', encoding="utf-8")
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    write_manifest_sha256(run_dir)

    mod = _load_registry()
    registry = mod.build_registry(mod.BuildContext(archive_root=archive, repo_root=REPO_ROOT))
    lane_ids = {row["lane_id"] for row in registry["runs"]}
    assert lane_ids == {"paper"}
    assert registry["runs"][0]["lane_id"] == "paper"
    assert "daemon_paper_24h" not in lane_ids
    assert "remote_runtime" not in lane_ids
