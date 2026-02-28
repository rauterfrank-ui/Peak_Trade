"""Smoke: portfolio_psychology symbols exist."""


def test_portfolio_psychology_symbols_exist() -> None:
    m = __import__(
        "src.reporting.portfolio_psychology",
        fromlist=["derive_portfolio_psychology", "PsychologyAnnotation"],
    )
    assert hasattr(m, "derive_portfolio_psychology") or hasattr(m, "PsychologyAnnotation")
