"""CLI tests for run_runtime_eligibility_v1."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.run_runtime_eligibility_v1 import EXIT_OK, EXIT_USAGE_ERROR, main
from src.meta.learning_loop.runtime_eligibility_v1 import ARTIFACT_REL


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.runtime_eligibility_v1.is_under_tmp",
        lambda _path: False,
    )


def test_cli_produces_evidence(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "cli_out"
    rc = main(["--output-dir", str(out)])
    assert rc == EXIT_OK
    assert (out / ARTIFACT_REL).is_file()
    captured = capsys.readouterr()
    assert "ELIGIBLE" in captured.out


def test_cli_rejects_existing_output(tmp_path: Path) -> None:
    out = tmp_path / "cli_out"
    out.mkdir()
    rc = main(["--output-dir", str(out)])
    assert rc == EXIT_USAGE_ERROR
