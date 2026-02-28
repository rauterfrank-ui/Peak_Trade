"""Smoke: ai_execution_gate.assert_ai_may_execute exists and is callable."""


def test_ai_execution_gate_assert_exists_and_safe_for_paper() -> None:
    """assert_ai_may_execute(mode) exists; paper mode passes with default config."""
    m = __import__("src.ops.ai_execution_gate", fromlist=["assert_ai_may_execute"])
    fn = getattr(m, "assert_ai_may_execute", None)
    assert fn is not None
    # Default config allows paper/shadow; should not raise
    fn("paper")
