"""CLI tests for runtime observation feedback scripts."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.run_runtime_observation_bundle_v1 import EXIT_OK as OBSERVATION_EXIT_OK
from scripts.run_runtime_observation_bundle_v1 import (
    EXIT_USAGE_ERROR as OBSERVATION_USAGE_ERROR,
)
from scripts.run_runtime_observation_bundle_v1 import main as observation_main
from scripts.run_runtime_performance_comparison_input_v1 import EXIT_OK as COMPARISON_EXIT_OK
from scripts.run_runtime_performance_comparison_input_v1 import (
    EXIT_USAGE_ERROR as COMPARISON_USAGE_ERROR,
)
from scripts.run_runtime_performance_comparison_input_v1 import main as comparison_main
from scripts.run_runtime_to_learning_input_v1 import EXIT_OK as LEARNING_EXIT_OK
from scripts.run_runtime_to_learning_input_v1 import EXIT_USAGE_ERROR as LEARNING_USAGE_ERROR
from scripts.run_runtime_to_learning_input_v1 import main as learning_main
from src.meta.learning_loop.runtime_observation_feedback_v1 import (
    COMPARISON_INPUT_ARTIFACT_REL,
    LEARNING_INPUT_ARTIFACT_REL,
    OBSERVATION_ARTIFACT_REL,
)
from tests.meta.runtime_observation_feedback_v1_fixtures import (
    produce_learning_input_fixture,
    produce_observation_bundle_fixture,
    produce_source_evidence_bundle,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.runtime_observation_feedback_v1.is_under_tmp",
        lambda _path: False,
    )


def test_observation_cli_produces_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "cli_observation_out"
    rc = observation_main(["--output-dir", str(out)])
    assert rc == OBSERVATION_EXIT_OK
    assert (out / OBSERVATION_ARTIFACT_REL).is_file()
    assert "COMPLETE" in capsys.readouterr().out


def test_observation_cli_with_source_bundle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = produce_source_evidence_bundle(tmp_path)
    out = tmp_path / "cli_observation_source_out"
    rc = observation_main(["--source-evidence-bundle-dir", str(source), "--output-dir", str(out)])
    assert rc == OBSERVATION_EXIT_OK
    assert (out / OBSERVATION_ARTIFACT_REL).is_file()
    assert "COMPLETE" in capsys.readouterr().out


def test_observation_cli_rejects_existing_output(tmp_path: Path) -> None:
    out = tmp_path / "cli_observation_out"
    out.mkdir()
    rc = observation_main(["--output-dir", str(out)])
    assert rc == OBSERVATION_USAGE_ERROR


def test_learning_cli_produces_evidence(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    obs = produce_observation_bundle_fixture(tmp_path, "cli_obs_in")
    out = tmp_path / "cli_learning_out"
    rc = learning_main(["--runtime-observation-bundle-dir", str(obs), "--output-dir", str(out)])
    assert rc == LEARNING_EXIT_OK
    assert (out / LEARNING_INPUT_ARTIFACT_REL).is_file()
    assert "VALID" in capsys.readouterr().out


def test_learning_cli_rejects_missing_bundle(tmp_path: Path) -> None:
    out = tmp_path / "cli_learning_out"
    rc = learning_main(
        [
            "--runtime-observation-bundle-dir",
            str(tmp_path / "missing"),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == LEARNING_USAGE_ERROR


def test_comparison_cli_produces_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    learning = produce_learning_input_fixture(tmp_path, "cli_learning_in")
    out = tmp_path / "cli_comparison_out"
    rc = comparison_main(
        [
            "--runtime-learning-input-bundle-dir",
            str(learning),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == COMPARISON_EXIT_OK
    assert (out / COMPARISON_INPUT_ARTIFACT_REL).is_file()
    assert "READY" in capsys.readouterr().out


def test_comparison_cli_rejects_existing_output(tmp_path: Path) -> None:
    learning = produce_learning_input_fixture(tmp_path, "cli_learning_in2")
    out = tmp_path / "cli_comparison_out"
    out.mkdir()
    rc = comparison_main(
        [
            "--runtime-learning-input-bundle-dir",
            str(learning),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == COMPARISON_USAGE_ERROR
