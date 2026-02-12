"""P29 smoke tests."""


def test_imports_smoke() -> None:
    from src.backtest.p29 import (  # noqa: F401
        AccountingErrorV2,
        PositionCashStateV2,
        apply_fills_v2,
    )
