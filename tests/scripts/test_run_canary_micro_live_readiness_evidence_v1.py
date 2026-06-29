"""CLI tests for canary_micro_live_readiness_v1 producers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_autonomous_non_live_orchestration_to_canary_readiness_input_v1 import (
    main as canary_input_main,
)
from scripts.run_canary_micro_live_readiness_evidence_v1 import main as readiness_main
from src.meta.learning_loop.canary_micro_live_readiness_v1 import (
    CANARY_INPUT_ARTIFACT_REL,
    READINESS_ARTIFACT_REL,
)
from tests.meta.autonomous_non_live_orchestration_plan_v1_fixtures import produce_plan_fixture
from tests.meta.canary_micro_live_readiness_v1_fixtures import produce_canary_input_fixture


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.canary_micro_live_readiness_v1.is_under_tmp",
        lambda _path: False,
    )


def _durable_output(tmp_path: Path, name: str) -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def test_cli_canary_input_default_fixture_mode(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "cli_canary_input_default")
    rc = canary_input_main(["--output-dir", str(out)])
    assert rc == 0
    payload = json.loads((out / CANARY_INPUT_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert payload["canary_input_status"] == "READY"


def test_cli_canary_input_from_plan_bundle(tmp_path: Path) -> None:
    source = produce_plan_fixture(tmp_path, "cli_plan_source")
    out = _durable_output(tmp_path, "cli_canary_input_from_plan")
    rc = canary_input_main(
        [
            "--source-plan-bundle-dir",
            str(source),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == 0


def test_cli_canary_input_rejects_existing_output(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "cli_canary_input_exists")
    out.mkdir()
    rc = canary_input_main(["--output-dir", str(out)])
    assert rc == 2


def test_cli_readiness_default_fixture_mode(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "cli_readiness_default")
    rc = readiness_main(["--output-dir", str(out)])
    assert rc == 0
    payload = json.loads((out / READINESS_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert payload["readiness_status"] == "READINESS_NOT_READY"


def test_cli_readiness_from_canary_input_bundle(tmp_path: Path) -> None:
    source = produce_canary_input_fixture(tmp_path, "cli_canary_input_source")
    out = _durable_output(tmp_path, "cli_readiness_from_canary_input")
    rc = readiness_main(
        [
            "--source-canary-input-bundle-dir",
            str(source),
            "--output-dir",
            str(out),
        ]
    )
    assert rc == 0


def test_cli_readiness_rejects_existing_output(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "cli_readiness_exists")
    out.mkdir()
    rc = readiness_main(["--output-dir", str(out)])
    assert rc == 2
