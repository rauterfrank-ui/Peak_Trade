"""CLI tests for autonomous_non_live_orchestration_plan_v1 producers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_autonomous_non_live_orchestration_plan_v1 import main as plan_main
from scripts.run_runtime_observation_to_orchestration_input_v1 import (
    main as orchestration_input_main,
)
from src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1 import (
    ORCHESTRATION_INPUT_ARTIFACT_REL,
    PLAN_ARTIFACT_REL,
)
from tests.meta.autonomous_non_live_orchestration_plan_v1_fixtures import (
    produce_learning_input_fixture,
    produce_observation_bundle_fixture,
    produce_orchestration_input_fixture,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1.is_under_tmp",
        lambda _path: False,
    )


def _durable_output(tmp_path: Path, name: str) -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def test_cli_orchestration_input_default_fixture_mode(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "cli_orch_default")
    rc = orchestration_input_main(["--output-dir", str(out)])
    assert rc == 0
    payload = json.loads((out / ORCHESTRATION_INPUT_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert payload["orchestration_input_status"] == "READY"


def test_cli_orchestration_input_from_observation_bundle(tmp_path: Path) -> None:
    source = produce_observation_bundle_fixture(tmp_path, "cli_obs_source")
    out = _durable_output(tmp_path, "cli_orch_from_obs")
    rc = orchestration_input_main(
        [
            "--source-observation-bundle-dir",
            str(source),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == 0


def test_cli_orchestration_input_from_learning_bundle(tmp_path: Path) -> None:
    source = produce_learning_input_fixture(tmp_path, "cli_learning_source")
    out = _durable_output(tmp_path, "cli_orch_from_learning")
    rc = orchestration_input_main(
        [
            "--source-learning-input-bundle-dir",
            str(source),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == 0


def test_cli_orchestration_input_rejects_existing_output(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "cli_orch_exists")
    out.mkdir()
    rc = orchestration_input_main(["--output-dir", str(out)])
    assert rc == 2


def test_cli_plan_default_fixture_mode(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "cli_plan_default")
    rc = plan_main(["--output-dir", str(out)])
    assert rc == 0
    payload = json.loads((out / PLAN_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert payload["plan_status"] == "PLAN_READY"
    assert payload["stage_sequence"] == [
        "REPLAY_ONLY",
        "SHADOW_ONLY",
        "PAPER_ONLY",
        "TESTNET_ONLY",
    ]


def test_cli_plan_from_orchestration_input_bundle(tmp_path: Path) -> None:
    source = produce_orchestration_input_fixture(tmp_path, "cli_orch_source")
    out = _durable_output(tmp_path, "cli_plan_from_orch")
    rc = plan_main(
        [
            "--source-orchestration-input-bundle-dir",
            str(source),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == 0


def test_cli_plan_rejects_missing_source_bundle(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "cli_plan_missing_source")
    rc = plan_main(
        [
            "--source-orchestration-input-bundle-dir",
            str(tmp_path / "missing"),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == 2
