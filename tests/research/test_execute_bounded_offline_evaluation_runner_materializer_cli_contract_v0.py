from __future__ import annotations

import subprocess
import sys
from pathlib import Path


RUNNER = Path(
    "scripts/research/execute_bounded_offline_economic_evaluation_from_ratified_scope_no_retry_v0.py"
)
MATERIALIZER = (
    "scripts/ops/materialize_final_research_fleet_offline_economic_evaluation_execution_v0.py"
)
GO_TOKEN = "GO_EXECUTE_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_V0"
BINDING_COMPLETION = "config/research/final_research_fleet_versioned_binding_completion_v0.json"


def test_runner_points_to_materializing_owner() -> None:
    text = RUNNER.read_text()
    assert MATERIALIZER in text
    assert (
        "src/research/final_research_fleet_offline_economic_evaluation_execution_v0.py" not in text
    )


def test_runner_binds_materializer_cli_contract() -> None:
    text = RUNNER.read_text()
    assert "--confirm-go-token" in text
    assert "--binding-completion-path" in text
    assert "--durable-evidence-root" in text
    assert GO_TOKEN in text
    assert BINDING_COMPLETION in text
    assert 'runpy.run_path(str(delegate_path), run_name="__main__")' in text


def test_print_delegate_only_returns_materializer() -> None:
    result = subprocess.run(
        [sys.executable, str(RUNNER), "--print-delegate-only"],
        check=True,
        text=True,
        capture_output=True,
    )
    assert MATERIALIZER in result.stdout
