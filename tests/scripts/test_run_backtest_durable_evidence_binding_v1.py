"""CLI tests for Package L offline BACKTEST durable evidence binding v1."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.run_backtest_durable_evidence_binding_v1 import (
    EXIT_BINDING_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from src.governance.promotion_loop.backtest_lineage_ref_producer_v1 import (
    RUN_SUMMARY_REL_PATH,
    produce_backtest_lineage_ref_v1,
    write_backtest_lineage_ref_v1_atomic,
)
from src.meta.learning_loop.backtest_durable_evidence_binding_v1 import INDEX_ARTIFACT_REL

RUN_ID = "test-run-cli-l-001"
FIXED_STARTED = "2025-01-15T10:00:00+00:00"
FIXED_FINISHED = "2025-01-15T10:05:00+00:00"


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.backtest_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    sources = tmp_path / "sources"
    sources.mkdir()
    run_dir = sources / "completed-run"
    run_dir.mkdir()
    (run_dir / RUN_SUMMARY_REL_PATH).write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "started_at_utc": FIXED_STARTED,
                "finished_at_utc": FIXED_FINISHED,
                "status": "FINISHED",
                "tracking_backend": "null",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    ref_path = sources / "backtest_ref.json"
    result = produce_backtest_lineage_ref_v1(run_dir=run_dir)
    write_backtest_lineage_ref_v1_atomic(result.ref, ref_path)
    out_root = tmp_path / "evidence_root"
    out_root.mkdir()
    return run_dir, ref_path, out_root


def test_cli_successful_run(tmp_path: Path) -> None:
    run_dir, ref_path, out_root = _write_inputs(tmp_path)
    out = out_root / "bundle_out"
    rc = main(
        [
            "--run-dir",
            str(run_dir),
            "--backtest-lineage-ref",
            str(ref_path),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_OK
    assert (out / INDEX_ARTIFACT_REL).is_file()


def test_cli_requires_all_paths() -> None:
    with pytest.raises(SystemExit):
        main([])


def test_cli_missing_run_dir_usage_error(tmp_path: Path) -> None:
    _, ref_path, out_root = _write_inputs(tmp_path)
    rc = main(
        [
            "--run-dir",
            str(tmp_path / "missing"),
            "--backtest-lineage-ref",
            str(ref_path),
            "--output-dir",
            str(out_root / "out"),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_missing_lineage_ref_usage_error(tmp_path: Path) -> None:
    run_dir, _, out_root = _write_inputs(tmp_path)
    rc = main(
        [
            "--run-dir",
            str(run_dir),
            "--backtest-lineage-ref",
            str(tmp_path / "missing.json"),
            "--output-dir",
            str(out_root / "out"),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_digest_mismatch_binding_error(tmp_path: Path) -> None:
    run_dir, ref_path, out_root = _write_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["digest"] = "0" * 64
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    rc = main(
        [
            "--run-dir",
            str(run_dir),
            "--backtest-lineage-ref",
            str(ref_path),
            "--output-dir",
            str(out_root / "out"),
        ]
    )
    assert rc == EXIT_BINDING_ERROR


def test_cli_existing_output_binding_error(tmp_path: Path) -> None:
    run_dir, ref_path, out_root = _write_inputs(tmp_path)
    out = out_root / "exists"
    out.mkdir()
    rc = main(
        [
            "--run-dir",
            str(run_dir),
            "--backtest-lineage-ref",
            str(ref_path),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_BINDING_ERROR


def test_cli_stderr_has_no_run_payload_dump(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_dir, ref_path, out_root = _write_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["digest"] = "0" * 64
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    rc = main(
        [
            "--run-dir",
            str(run_dir),
            "--backtest-lineage-ref",
            str(ref_path),
            "--output-dir",
            str(out_root / "out"),
        ]
    )
    assert rc == EXIT_BINDING_ERROR
    err = capsys.readouterr().err
    assert "sharpe" not in err
    assert "params" not in err
    assert len(err) < 500


def test_cli_no_network_side_effects(tmp_path: Path) -> None:
    run_dir, ref_path, out_root = _write_inputs(tmp_path)
    out = out_root / "bundle"
    with patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")):
        rc = main(
            [
                "--run-dir",
                str(run_dir),
                "--backtest-lineage-ref",
                str(ref_path),
                "--output-dir",
                str(out),
            ]
        )
    assert rc == EXIT_OK


def test_cli_deterministic_output(tmp_path: Path) -> None:
    run_dir, ref_path, out_root = _write_inputs(tmp_path)
    out1 = out_root / "bundle1"
    out2 = out_root / "bundle2"
    assert (
        main(
            [
                "--run-dir",
                str(run_dir),
                "--backtest-lineage-ref",
                str(ref_path),
                "--output-dir",
                str(out1),
            ]
        )
        == EXIT_OK
    )
    assert (
        main(
            [
                "--run-dir",
                str(run_dir),
                "--backtest-lineage-ref",
                str(ref_path),
                "--output-dir",
                str(out2),
            ]
        )
        == EXIT_OK
    )
    assert (out1 / INDEX_ARTIFACT_REL).read_bytes() == (out2 / INDEX_ARTIFACT_REL).read_bytes()
