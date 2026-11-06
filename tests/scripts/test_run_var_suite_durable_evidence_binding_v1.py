"""CLI tests for Package K offline VAR_SUITE durable evidence binding v1."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.run_var_suite_durable_evidence_binding_v1 import (
    EXIT_BINDING_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)
from src.governance.promotion_loop.var_suite_lineage_ref_producer_v1 import (
    produce_var_suite_lineage_ref_v1,
    write_var_suite_lineage_ref_v1_atomic,
)
from src.meta.learning_loop.var_suite_durable_evidence_binding_v1 import INDEX_ARTIFACT_REL

REPORT_DIR_NAME = "suite-cli-k-001"
SUITE_REPORT_JSON = "suite_report.json"


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.var_suite_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    sources = tmp_path / "sources"
    sources.mkdir()
    report_dir = sources / REPORT_DIR_NAME
    report_dir.mkdir()
    (report_dir / SUITE_REPORT_JSON).write_text(
        json.dumps({"overall_result": "PASS"}, indent=2),
        encoding="utf-8",
    )
    ref_path = sources / "var_suite_ref.json"
    result = produce_var_suite_lineage_ref_v1(report_dir=report_dir)
    write_var_suite_lineage_ref_v1_atomic(result.ref, ref_path)
    out_root = tmp_path / "evidence_root"
    out_root.mkdir()
    return report_dir, ref_path, out_root


def test_cli_successful_run(tmp_path: Path) -> None:
    report_dir, ref_path, out_root = _write_inputs(tmp_path)
    out = out_root / "bundle_out"
    rc = main(
        [
            "--report-dir",
            str(report_dir),
            "--var-suite-lineage-ref",
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


def test_cli_missing_report_dir_usage_error(tmp_path: Path) -> None:
    _, ref_path, out_root = _write_inputs(tmp_path)
    rc = main(
        [
            "--report-dir",
            str(tmp_path / "missing"),
            "--var-suite-lineage-ref",
            str(ref_path),
            "--output-dir",
            str(out_root / "out"),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_missing_lineage_ref_usage_error(tmp_path: Path) -> None:
    report_dir, _, out_root = _write_inputs(tmp_path)
    rc = main(
        [
            "--report-dir",
            str(report_dir),
            "--var-suite-lineage-ref",
            str(tmp_path / "missing.json"),
            "--output-dir",
            str(out_root / "out"),
        ]
    )
    assert rc == EXIT_USAGE_ERROR


def test_cli_digest_mismatch_binding_error(tmp_path: Path) -> None:
    report_dir, ref_path, out_root = _write_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["digest"] = "0" * 64
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    rc = main(
        [
            "--report-dir",
            str(report_dir),
            "--var-suite-lineage-ref",
            str(ref_path),
            "--output-dir",
            str(out_root / "out"),
        ]
    )
    assert rc == EXIT_BINDING_ERROR


def test_cli_existing_output_binding_error(tmp_path: Path) -> None:
    report_dir, ref_path, out_root = _write_inputs(tmp_path)
    out = out_root / "exists"
    out.mkdir()
    rc = main(
        [
            "--report-dir",
            str(report_dir),
            "--var-suite-lineage-ref",
            str(ref_path),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == EXIT_BINDING_ERROR


def test_cli_stderr_has_no_report_payload_dump(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    report_dir, ref_path, out_root = _write_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["digest"] = "0" * 64
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    rc = main(
        [
            "--report-dir",
            str(report_dir),
            "--var-suite-lineage-ref",
            str(ref_path),
            "--output-dir",
            str(out_root / "out"),
        ]
    )
    assert rc == EXIT_BINDING_ERROR
    err = capsys.readouterr().err
    assert "overall_result" not in err
    assert len(err) < 500


def test_cli_no_network_side_effects(tmp_path: Path) -> None:
    report_dir, ref_path, out_root = _write_inputs(tmp_path)
    out = out_root / "bundle"
    with patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")):
        rc = main(
            [
                "--report-dir",
                str(report_dir),
                "--var-suite-lineage-ref",
                str(ref_path),
                "--output-dir",
                str(out),
            ]
        )
    assert rc == EXIT_OK


def test_cli_deterministic_output(tmp_path: Path) -> None:
    report_dir, ref_path, out_root = _write_inputs(tmp_path)
    out1 = out_root / "bundle1"
    out2 = out_root / "bundle2"
    assert (
        main(
            [
                "--report-dir",
                str(report_dir),
                "--var-suite-lineage-ref",
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
                "--report-dir",
                str(report_dir),
                "--var-suite-lineage-ref",
                str(ref_path),
                "--output-dir",
                str(out2),
            ]
        )
        == EXIT_OK
    )
    assert (out1 / INDEX_ARTIFACT_REL).read_bytes() == (out2 / INDEX_ARTIFACT_REL).read_bytes()
