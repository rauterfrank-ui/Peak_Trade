import pytest

from src.ops.p98 import P98OpsLoopContextV1, run_ops_loop_orchestrator_v1
from src.ops.p98.ops_loop_orchestrator_v1 import (
    _MAX_STEP_FAILURE_OUT_SNIPPET_CHARS,
    _truncate_for_step_failure,
)


def test_truncate_for_step_failure_short_unchanged() -> None:
    assert _truncate_for_step_failure("hello\n") == "hello"
    assert _truncate_for_step_failure("") == ""


def test_truncate_for_step_failure_exact_max_len_no_ellipsis() -> None:
    s = "a" * _MAX_STEP_FAILURE_OUT_SNIPPET_CHARS
    assert _truncate_for_step_failure(s) == s


def test_truncate_for_step_failure_long_gets_ellipsis() -> None:
    s = "b" * (_MAX_STEP_FAILURE_OUT_SNIPPET_CHARS + 10)
    out = _truncate_for_step_failure(s)
    assert len(out) == _MAX_STEP_FAILURE_OUT_SNIPPET_CHARS
    assert out.endswith("…")


def test_step_failure_runtime_error_includes_truncated_repr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    long_out = "E" * 800

    def fake_sh(cmd, env=None, cwd=None):
        return 1, long_out

    monkeypatch.setattr("src.ops.p98.ops_loop_orchestrator_v1._sh", fake_sh)
    with pytest.raises(RuntimeError, match="p95_meta_gate") as ei:
        run_ops_loop_orchestrator_v1(P98OpsLoopContextV1())
    msg = str(ei.value)
    assert "rc=1" in msg
    assert "out_snippet=" in msg
    expected = _truncate_for_step_failure(long_out)
    assert repr(expected) in msg


def test_step_failure_empty_out_snippet(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_sh(cmd, env=None, cwd=None):
        return 1, "   \n  "

    monkeypatch.setattr("src.ops.p98.ops_loop_orchestrator_v1._sh", fake_sh)
    with pytest.raises(RuntimeError) as ei:
        run_ops_loop_orchestrator_v1(P98OpsLoopContextV1())
    assert "out_snippet=''" in str(ei.value)
