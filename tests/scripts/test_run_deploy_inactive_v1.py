"""CLI tests for deployment candidate and verification scripts."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.run_deployed_inactive_verification_v1 import EXIT_OK as VERIFICATION_EXIT_OK
from scripts.run_deployed_inactive_verification_v1 import (
    EXIT_USAGE_ERROR as VERIFICATION_USAGE_ERROR,
)
from scripts.run_deployed_inactive_verification_v1 import main as verification_main
from scripts.run_deployment_candidate_v1 import EXIT_OK as CANDIDATE_EXIT_OK
from scripts.run_deployment_candidate_v1 import EXIT_USAGE_ERROR as CANDIDATE_USAGE_ERROR
from scripts.run_deployment_candidate_v1 import main as candidate_main
from src.meta.learning_loop.deploy_inactive_v1 import (
    DEPLOYMENT_CANDIDATE_ARTIFACT_REL,
    VERIFICATION_ARTIFACT_REL,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.deploy_inactive_v1.is_under_tmp",
        lambda _path: False,
    )


def test_deployment_candidate_cli_produces_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "cli_candidate_out"
    rc = candidate_main(["--output-dir", str(out)])
    assert rc == CANDIDATE_EXIT_OK
    assert (out / DEPLOYMENT_CANDIDATE_ARTIFACT_REL).is_file()
    assert "DEPLOYABLE" in capsys.readouterr().out


def test_deployment_candidate_cli_rejects_existing_output(tmp_path: Path) -> None:
    out = tmp_path / "cli_candidate_out"
    out.mkdir()
    rc = candidate_main(["--output-dir", str(out)])
    assert rc == CANDIDATE_USAGE_ERROR


def test_verification_cli_produces_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "cli_verification_out"
    rc = verification_main(["--output-dir", str(out)])
    assert rc == VERIFICATION_EXIT_OK
    assert (out / VERIFICATION_ARTIFACT_REL).is_file()
    assert "VERIFIED_INACTIVE_PROJECTION" in capsys.readouterr().out


def test_verification_cli_rejects_existing_output(tmp_path: Path) -> None:
    out = tmp_path / "cli_verification_out"
    out.mkdir()
    rc = verification_main(["--output-dir", str(out)])
    assert rc == VERIFICATION_USAGE_ERROR
