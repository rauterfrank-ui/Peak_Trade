"""FAST_REFERENCE_REPLAY_V1 wrapper tests. AUTHORITY=NONE; non-authorizing."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO / "scripts/ops/fast_reference_replay_v1.py"


def _load():
    spec = importlib.util.spec_from_file_location("fast_reference_replay_v1", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


REPLAY = _load()


def test_v1_check_population_frozen() -> None:
    specs = REPLAY.build_v1_check_specs(REPO)
    assert len(specs) == 12
    assert [s.check_id for s in specs] == list(REPLAY.V1_CHECK_IDS)


def test_missing_check_in_builder_fails_closed() -> None:
    original = REPLAY.V1_CHECK_IDS
    try:
        REPLAY.V1_CHECK_IDS = ("runtime_check",)  # type: ignore[misc]
        with pytest.raises(RuntimeError, match="V1 check population drift"):
            REPLAY.build_v1_check_specs(REPO)
    finally:
        REPLAY.V1_CHECK_IDS = original  # type: ignore[misc]


def test_individual_failed_check_yields_overall_fail(tmp_path: Path) -> None:
    def runner(argv, cwd, timeout):  # noqa: ANN001
        if "runtime-check" in argv:
            return 1
        return 0

    _, overall, _ = REPLAY.run_fast_reference_replay_v1(tmp_path, runner=runner)
    assert overall == "FAIL"


def test_timed_out_check_yields_overall_fail(tmp_path: Path) -> None:
    def runner(argv, cwd, timeout):  # noqa: ANN001
        raise subprocess.TimeoutExpired(argv, timeout)

    results, overall, _ = REPLAY.run_fast_reference_replay_v1(tmp_path, runner=runner)
    assert overall == "FAIL"
    assert any(r.status == "TIMEOUT" for r in results)


def test_safety_invariant_drift_yields_fail(tmp_path: Path) -> None:
    def runner(argv, cwd, timeout):  # noqa: ANN001
        joined = " ".join(argv)
        if "SAFETY_INVARIANTS_OK" in joined or "section_11_13_5_live_canary" in joined:
            return 1
        return 0

    results, overall, _ = REPLAY.run_fast_reference_replay_v1(tmp_path, runner=runner)
    assert overall == "FAIL"
    safety = [r for r in results if r.check_id == "safety_standing_invariants"]
    assert len(safety) == 1
    assert safety[0].status == "FAIL"


def test_known_good_baseline_passes() -> None:
    results, overall, total = REPLAY.run_fast_reference_replay_v1(REPO)
    assert len(results) == 12
    assert overall == "PASS"
    assert total < 120


def test_cli_exit_code_matches_result() -> None:
    proc = subprocess.run(
        [str(REPO / "scripts/pt"), "scripts/ops/fast_reference_replay_v1.py"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert "FAST_REFERENCE_REPLAY_RESULT=PASS" in proc.stdout
    assert proc.returncode == 0
