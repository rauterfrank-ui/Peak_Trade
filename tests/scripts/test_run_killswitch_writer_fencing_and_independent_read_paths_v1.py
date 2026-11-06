"""CLI tests for run_killswitch_writer_fencing_and_independent_read_paths_v1."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.run_killswitch_writer_fencing_and_independent_read_paths_v1 import (
    EXIT_OK,
    EXIT_USAGE_ERROR,
    main,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1.is_under_tmp",
        lambda _path: False,
    )


def test_script_happy_path(tmp_path: Path, capsys) -> None:
    out = tmp_path / "evidence_root" / "script_killswitch_writer_fencing"
    rc = main(["--output-dir", str(out)])
    assert rc == EXIT_OK
    captured = capsys.readouterr()
    assert '"decision": "PASS"' in captured.out
    assert out.is_dir()


def test_script_existing_output_returns_usage_error(tmp_path: Path) -> None:
    out = tmp_path / "evidence_root" / "existing"
    out.mkdir(parents=True)
    rc = main(["--output-dir", str(out)])
    assert rc == EXIT_USAGE_ERROR
