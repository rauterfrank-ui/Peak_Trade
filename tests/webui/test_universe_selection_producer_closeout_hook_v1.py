"""Tests for env-gated closeout adapter hooks (Slice 2b — no runtime runs)."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import uuid
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from scripts.ops.primary_evidence_retention_v0 import is_under_tmp, verify_manifest_sha256
from src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1 import (
    ENV_PRODUCER_V1_ENABLED,
    READMODEL_FILENAME,
    READMODELS_DIRNAME,
    CloseoutHookResult,
    emit_universe_selection_closeout_machine_lines,
    maybe_write_missing_truth_after_bounded_closeout,
)

SCRATCH_ROOT = project_root / "tests" / "_durable_archive_scratch"

ADAPTER_SCRIPTS = (
    project_root / "scripts" / "ops" / "run_paper_only_bounded_observation_adapter_v0.py",
    project_root / "scripts" / "ops" / "run_shadow_bounded_observation_adapter_v0.py",
    project_root / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py",
)


@pytest.fixture
def archive_root(tmp_path: Path) -> Path:
    candidate = tmp_path / "archive_root"
    candidate.mkdir(parents=True, exist_ok=True)
    if not is_under_tmp(candidate):
        return candidate
    SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
    durable = SCRATCH_ROOT / str(uuid.uuid4())
    durable.mkdir(parents=True, exist_ok=True)
    return durable


@pytest.fixture(autouse=True)
def _clear_producer_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_PRODUCER_V1_ENABLED, raising=False)


def test_gate_off_skips_write_no_file(archive_root: Path) -> None:
    run_bundle = archive_root / "runs" / "paper" / "p1_test"
    run_bundle.mkdir(parents=True)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_test",
        source_stage="paper",
    )

    readmodel_path = archive_root / READMODELS_DIRNAME / READMODEL_FILENAME
    assert result.enabled is False
    assert result.skipped is True
    assert result.written is False
    assert result.reason == "DISABLED"
    assert not readmodel_path.exists()


def test_gate_on_writes_missing_truth_readmodel(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    run_bundle = archive_root / "runs" / "paper" / "p1_test"
    run_bundle.mkdir(parents=True)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="p1_test",
        source_stage="paper",
    )

    readmodels_dir = archive_root / READMODELS_DIRNAME
    readmodel_path = readmodels_dir / READMODEL_FILENAME
    manifest_path = readmodels_dir / "MANIFEST.sha256"

    assert result.enabled is True
    assert result.skipped is False
    assert result.written is True
    assert result.manifest_verify_rc == 0
    assert readmodel_path.is_file()
    assert manifest_path.is_file()
    ok, _ = verify_manifest_sha256(readmodels_dir)
    assert ok

    payload = json.loads(readmodel_path.read_text(encoding="utf-8"))
    assert payload["source_run_id"] == "p1_test"
    assert payload["source_stage"] == "paper"
    assert payload["selected_future"] == {"truth_status": "NOT_PERSISTED"}
    assert str(run_bundle) in payload["evidence"]["links"]
    assert "BTC/USD" not in readmodel_path.read_text(encoding="utf-8")


@pytest.mark.parametrize("stage", ["paper", "shadow", "testnet"])
def test_gate_on_accepts_bounded_stages(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    run_id = f"{stage}_run_test"
    run_bundle = archive_root / "runs" / stage / run_id
    run_bundle.mkdir(parents=True)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id=run_id,
        source_stage=stage,
    )

    assert result.written is True
    payload = json.loads(
        (archive_root / READMODELS_DIRNAME / READMODEL_FILENAME).read_text(encoding="utf-8")
    )
    assert payload["source_stage"] == stage


def test_live_stage_rejected_no_write(archive_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    run_bundle = archive_root / "runs" / "live" / "l1_test"
    run_bundle.mkdir(parents=True)

    result = maybe_write_missing_truth_after_bounded_closeout(
        archive_root=archive_root,
        run_bundle_path=run_bundle,
        source_run_id="l1_test",
        source_stage="live",
    )

    assert result.enabled is True
    assert result.skipped is True
    assert result.written is False
    assert result.reason == "INVALID_STAGE"
    assert not (archive_root / READMODELS_DIRNAME / READMODEL_FILENAME).exists()


def test_write_failure_non_blocking_no_exception(
    archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_PRODUCER_V1_ENABLED, "1")
    run_bundle = archive_root / "runs" / "paper" / "p1_fail"
    run_bundle.mkdir(parents=True)

    with patch(
        "src.webui.workflow_dashboard_readmodel_v1.universe_selection_producer_v1.write_missing_truth_universe_selection_readmodel",
        side_effect=OSError("simulated write failure"),
    ):
        result = maybe_write_missing_truth_after_bounded_closeout(
            archive_root=archive_root,
            run_bundle_path=run_bundle,
            source_run_id="p1_fail",
            source_stage="paper",
        )

    assert result.written is False
    assert result.reason == "ERROR"
    assert result.error == "simulated write failure"


def test_emit_machine_lines_gate_off() -> None:
    result = CloseoutHookResult(
        enabled=False,
        skipped=True,
        written=False,
        reason="DISABLED",
        archive_root="/tmp/archive",
        readmodel_path=None,
        manifest_verify_rc=None,
        error=None,
    )
    buf = io.StringIO()
    with redirect_stdout(buf):
        emit_universe_selection_closeout_machine_lines(result)
    out = buf.getvalue()
    assert "UNIVERSE_SELECTION_PRODUCER_V1_ENABLED=false" in out
    assert "UNIVERSE_SELECTION_READMODEL_WRITTEN=false" in out
    assert "UNIVERSE_SELECTION_READMODEL_PATH=NOT_WRITTEN" in out
    assert "UNIVERSE_SELECTION_READMODEL_MANIFEST_VERIFY_RC=NOT_RUN" in out
    assert "UNIVERSE_SELECTION_READMODEL_ERROR=" in out


def test_emit_machine_lines_gate_on_success() -> None:
    result = CloseoutHookResult(
        enabled=True,
        skipped=False,
        written=True,
        reason="OK",
        archive_root="/tmp/archive",
        readmodel_path="/tmp/archive/readmodels/universe_selection_readmodel.v1.json",
        manifest_verify_rc=0,
        error=None,
    )
    buf = io.StringIO()
    with redirect_stdout(buf):
        emit_universe_selection_closeout_machine_lines(result)
    out = buf.getvalue()
    assert "UNIVERSE_SELECTION_PRODUCER_V1_ENABLED=true" in out
    assert "UNIVERSE_SELECTION_READMODEL_WRITTEN=true" in out
    assert "UNIVERSE_SELECTION_READMODEL_MANIFEST_VERIFY_RC=0" in out


def test_adapters_reference_closeout_hook_helpers() -> None:
    for script in ADAPTER_SCRIPTS:
        text = script.read_text(encoding="utf-8")
        assert "maybe_write_missing_truth_after_bounded_closeout" in text
        assert "emit_universe_selection_closeout_machine_lines" in text
