"""P27 smoke tests."""


def test_imports_smoke() -> None:
    from src.backtest.p27 import execution_integration  # noqa: F401
    from src.backtest.p27.execution_integration import (
        P27ExecutionWiringConfig,
        build_p26_adapter,
        execute_bar_via_p26,
    )

    _ = P27ExecutionWiringConfig
    _ = build_p26_adapter
    _ = execute_bar_via_p26
