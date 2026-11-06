"""CLI tests for offline COMPARISON LineageRef producer."""

from __future__ import annotations

import json
import os
import shutil
import stat
import uuid
from pathlib import Path
from typing import Callable
from unittest.mock import patch

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from scripts.run_comparison_lineage_ref_producer_v1 import (
    EXIT_OK,
    EXIT_PRODUCER_ERROR,
    main,
)
from src.governance.promotion_loop.comparison_lineage_ref_producer_v1 import (
    ComparisonLineageRefProducerError,
)
from src.meta.learning_loop.comparison_ssot_v1.constants import RESULT_ARTIFACT_FILENAME
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from tests.meta.comparison_ssot_v1_fixtures import produce_comparison_pair

REPO_ROOT = Path(__file__).resolve().parents[2]
_DURABLE_OUTPUT_ROOT = REPO_ROOT / ".comparison_lineage_ref_cli_pytest_outputs"


@pytest.fixture
def lineage_ref_cli_durable_output_dir() -> Callable[[], Path]:
    _DURABLE_OUTPUT_ROOT.mkdir(exist_ok=True)
    created: list[Path] = []

    def _make() -> Path:
        path = _DURABLE_OUTPUT_ROOT / uuid.uuid4().hex
        created.append(path)
        return path

    yield _make

    for path in created:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)


def _result_manifest_dir(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> tuple[Path, dict[str, object]]:
    _, result_path, _definition_id = produce_comparison_pair(tmp_path, ssot_durable_output_dir)
    manifest = read_manifest(result_path)
    return result_path.parent, manifest


def test_cli_successful_run(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    output_path = tmp_path / "ref.json"
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_OK
    assert output_path.is_file()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ref_id"] == manifest["comparison_definition_id"]
    assert payload["ref_type"] == "comparison"
    assert payload["relation"] == "derives_from_result_manifest"
    assert payload["owner_domain"] == "meta/learning_loop/comparison_ssot_v1"


def test_cli_deterministic_output(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    output_a = tmp_path / "a.json"
    output_b = tmp_path / "b.json"
    assert main(["--manifest-dir", str(manifest_dir), "--output", str(output_a)]) == EXIT_OK
    assert main(["--manifest-dir", str(manifest_dir), "--output", str(output_b)]) == EXIT_OK
    assert output_a.read_text(encoding="utf-8") == output_b.read_text(encoding="utf-8")


def test_cli_requires_explicit_manifest_dir_and_output(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    with pytest.raises(SystemExit):
        main(["--output", str(tmp_path / "out.json")])
    with pytest.raises(SystemExit):
        main(["--manifest-dir", str(manifest_dir)])


def test_cli_invalid_input_is_producer_error(tmp_path: Path, capsys) -> None:
    manifest_dir = tmp_path / "empty-dir"
    manifest_dir.mkdir()
    output_path = tmp_path / "out.json"
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()
    assert "ERROR:" in capsys.readouterr().err


def test_cli_missing_result_manifest_fail_closed(tmp_path: Path, capsys) -> None:
    manifest_dir = tmp_path / "missing-manifest"
    manifest_dir.mkdir()
    output_path = tmp_path / "out.json"
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()
    assert RESULT_ARTIFACT_FILENAME in capsys.readouterr().err


def test_cli_existing_output_fail_closed(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
    capsys,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    output_path = tmp_path / "out.json"
    output_path.write_text('{"stale": true}', encoding="utf-8")
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert output_path.read_text(encoding="utf-8") == '{"stale": true}'
    assert "already exists" in capsys.readouterr().err


def test_cli_non_writable_output_parent(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    output_path = readonly_dir / "out.json"
    os.chmod(readonly_dir, stat.S_IRUSR | stat.S_IXUSR)
    try:
        rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    finally:
        os.chmod(readonly_dir, stat.S_IRWXU)
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()


def test_cli_no_partial_output_on_producer_error(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    tampered = dict(manifest)
    tampered["winner"] = "forbidden"
    (manifest_dir / RESULT_ARTIFACT_FILENAME).write_text(json.dumps(tampered), encoding="utf-8")
    output_path = tmp_path / "out.json"
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert not output_path.exists()
    assert not output_path.with_name(output_path.name + ".tmp").exists()


def test_cli_producer_error_reports_on_stderr(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
    capsys,
    monkeypatch,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    output_path = tmp_path / "out.json"

    def _raise(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise ComparisonLineageRefProducerError("forced producer failure")

    monkeypatch.setattr(
        "scripts.run_comparison_lineage_ref_producer_v1.produce_comparison_lineage_ref_v1_to_path",
        _raise,
    )
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_PRODUCER_ERROR
    assert "forced producer failure" in capsys.readouterr().err


def test_cli_no_comparison_offline_or_registry_calls(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
    monkeypatch,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    output_path = tmp_path / "out.json"

    def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("forbidden side-effect invocation")

    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_ssot_v1.producer.produce_comparison_offline_v1",
        _forbidden,
    )
    with patch("urllib.request.urlopen", side_effect=_forbidden):
        rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_OK


def test_cli_durable_output_path(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
    lineage_ref_cli_durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    output_path = lineage_ref_cli_durable_output_dir() / "ref.json"
    rc = main(["--manifest-dir", str(manifest_dir), "--output", str(output_path)])
    assert rc == EXIT_OK
    assert output_path.is_file()
