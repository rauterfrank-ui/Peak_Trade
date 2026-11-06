"""Synthetic tests for generic evaluation-runner lifecycle observability v1.

No real research evaluation. No holdout access. Deterministic fixtures only.
"""

from __future__ import annotations

import json
import signal
import time
from pathlib import Path

from src.research.evaluation_runner_lifecycle_observability_v1 import (
    EvaluationRunnerLifecycleObservabilityV1,
    classify_incomplete_run_v1,
    normalize_process_exit_v1,
    run_supervised_python_worker_v1,
)
from src.research.evaluation_runner_lifecycle_observability_v1.classification_v1 import (
    DEATH_CLASS_NO_RESULT_EOF,
    DEATH_CLASS_NONZERO_EXIT,
    DEATH_CLASS_PERSISTENCE_FAILURE,
    DEATH_CLASS_SIGNAL,
    DEATH_CLASS_TIMEOUT_OR_MISSING_HEARTBEAT,
    DEATH_CLASS_WORKER_EXCEPTION,
)
from src.research.evaluation_runner_lifecycle_observability_v1.constants_v1 import (
    HEARTBEAT_FILENAME,
    PROGRESS_FILENAME,
    RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE,
    TERMINAL_DIAGNOSTICS_FILENAME,
)
from src.research.evaluation_runner_lifecycle_observability_v1.supervised_process_v1 import (
    portable_terminating_signal_v1,
)


def test_normalize_clean_and_nonzero_and_signal() -> None:
    clean = normalize_process_exit_v1(returncode=0)
    assert clean["death_class"] == "CLEAN_EXIT"
    assert clean["process_completed"] is True
    nonzero = normalize_process_exit_v1(returncode=7)
    assert nonzero["death_class"] == DEATH_CLASS_NONZERO_EXIT
    assert nonzero["exit_code"] == 7
    signaled = normalize_process_exit_v1(returncode=-signal.SIGTERM)
    assert signaled["death_class"] == DEATH_CLASS_SIGNAL
    assert signaled["signal_name"] == "SIGTERM"


def test_classify_incomplete_is_fail_closed_no_rerun() -> None:
    payload = classify_incomplete_run_v1(
        death_class=DEATH_CLASS_TIMEOUT_OR_MISSING_HEARTBEAT,
        last_confirmed_phase="baseline",
        last_confirmed_member_index=2,
        last_confirmed_member_id="SYNTH-A",
        members_total=46,
    )
    assert payload["result_class"] == RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE
    assert payload["economic_verdict"] == "NOT_EVALUATED"
    assert payload["rerun_allowed"] is False
    assert payload["resume_allowed"] is False
    assert payload["auto_rerun_executed"] is False
    assert payload["fail_closed"] is True
    assert payload["last_confirmed_member_index"] == 2


def test_member_progress_and_heartbeat_atomic(tmp_path: Path) -> None:
    life = EvaluationRunnerLifecycleObservabilityV1(tmp_path, run_id="synthetic-run")
    life.record_member_progress(
        phase="baseline",
        member_index=2,
        members_total=46,
        member_id="ADA-USDT-SWAP",
        extra={"trades": 3},
    )
    progress = json.loads((tmp_path / PROGRESS_FILENAME).read_text(encoding="utf-8"))
    heartbeat = json.loads((tmp_path / HEARTBEAT_FILENAME).read_text(encoding="utf-8"))
    assert progress["member_index"] == 2
    assert progress["member_id"] == "ADA-USDT-SWAP"
    assert progress["trades"] == 3
    assert heartbeat["heartbeat"] is True
    assert heartbeat["last_confirmed_member_index"] == 2


def test_worker_exception_mode(tmp_path: Path) -> None:
    result = run_supervised_python_worker_v1(
        code=(
            "import sys\n"
            "print('WORKER_EXCEPTION=RuntimeError', flush=True)\n"
            "raise RuntimeError('synthetic_worker_boom')\n"
        ),
        timeout_seconds=5.0,
    )
    assert result.worker_exception_observed is True
    assert result.death_class == DEATH_CLASS_WORKER_EXCEPTION
    assert result.process_completed is False
    life = EvaluationRunnerLifecycleObservabilityV1(tmp_path, run_id="exc-run")
    life.record_member_progress(phase="baseline", member_index=1, members_total=3, member_id="M1")
    terminal = life.record_exception(RuntimeError("synthetic_worker_boom"))
    assert terminal["result_class"] == RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE
    assert terminal["death_class"] == DEATH_CLASS_WORKER_EXCEPTION
    assert terminal["exception_type"] == "RuntimeError"
    assert terminal["last_confirmed_member_index"] == 1


def test_nonzero_exit_mode() -> None:
    result = run_supervised_python_worker_v1(
        code="import sys; print('no_result'); sys.exit(9)",
        timeout_seconds=5.0,
    )
    assert result.exit_code == 9
    assert result.death_class in {DEATH_CLASS_NONZERO_EXIT, DEATH_CLASS_NO_RESULT_EOF}
    assert result.process_completed is False


def test_signal_death_mode_portable() -> None:
    sig = portable_terminating_signal_v1()
    result = run_supervised_python_worker_v1(
        code="import time; time.sleep(30)",
        timeout_seconds=5.0,
        send_signal=sig,
        signal_after_seconds=0.1,
    )
    assert result.process_completed is False
    assert result.death_class == DEATH_CLASS_SIGNAL
    assert result.signal_name == "SIGTERM"
    assert result.exit_code is not None
    assert result.exit_code < 0 or result.returncode not in (0, None)


def test_abrupt_eof_no_result_mode() -> None:
    result = run_supervised_python_worker_v1(
        code="import sys; sys.exit(1)",
        timeout_seconds=5.0,
    )
    assert result.abrupt_eof is True
    assert result.death_class == DEATH_CLASS_NO_RESULT_EOF
    assert result.process_completed is False


def test_timeout_or_missing_heartbeat_mode(tmp_path: Path) -> None:
    result = run_supervised_python_worker_v1(
        code="import time; time.sleep(30)",
        timeout_seconds=0.2,
    )
    assert result.timed_out is True
    assert result.death_class == DEATH_CLASS_TIMEOUT_OR_MISSING_HEARTBEAT
    life = EvaluationRunnerLifecycleObservabilityV1(tmp_path, run_id="hb-run")
    life.record_member_progress(phase="baseline", member_index=2, members_total=46, member_id="M2")
    # Simulate parent observing stale heartbeat without new progress.
    time.sleep(0.01)
    stale = json.loads((tmp_path / HEARTBEAT_FILENAME).read_text(encoding="utf-8"))
    assert stale["last_confirmed_member_index"] == 2
    terminal = life.write_terminal_infrastructure_failure(
        death_class=DEATH_CLASS_TIMEOUT_OR_MISSING_HEARTBEAT,
        exception_type=None,
        exception_message_truncated=None,
        exit_code=None,
        signal_name=None,
    )
    assert terminal["result_class"] == RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE
    assert terminal["last_confirmed_member_index"] == 2
    assert (tmp_path / TERMINAL_DIAGNOSTICS_FILENAME).is_file()


def test_persistence_failure_after_successful_member(tmp_path: Path) -> None:
    life = EvaluationRunnerLifecycleObservabilityV1(tmp_path, run_id="persist-run")
    life.record_member_progress(
        phase="baseline",
        member_index=2,
        members_total=46,
        member_id="SYNTH-OK",
    )
    terminal = life.record_persistence_failure(OSError("synthetic_disk_full"))
    assert terminal["death_class"] == DEATH_CLASS_PERSISTENCE_FAILURE
    assert terminal["result_class"] == RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE
    assert terminal["last_confirmed_member_index"] == 2
    assert terminal["exception_type"] == "OSError"
    assert terminal["rerun_allowed"] is False


def test_cli_source_has_lifecycle_hooks_without_rerun() -> None:
    repo = Path(__file__).resolve().parents[2]
    cli = (
        repo
        / "scripts/research/run_evaluate_bollinger_mr_midband_exit_efficiency_development_v1.py"
    ).read_text(encoding="utf-8")
    assert "EvaluationRunnerLifecycleObservabilityV1" in cli
    assert "install_signal_handlers" in cli
    assert "EVALUATION_RUN_SLOT_ALREADY_CONSUMED" in cli
    assert "AUTO_RERUN_EXECUTED=false" in cli
    panel = (
        repo / "src/research/bollinger_mr_midband_exit_efficiency_development_evaluation_v1/"
        "panel_runner_v1.py"
    ).read_text(encoding="utf-8")
    assert "record_member_progress" in panel
    assert "record_persist_phase" in panel
    assert "mark_complete" in panel
