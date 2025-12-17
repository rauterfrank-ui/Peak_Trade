import pytest

from src.strategies.armstrong.armstrong_cycle_strategy import (
    ArmstrongCycleStrategy,
)
from src.strategies.el_karoui.el_karoui_vol_model_strategy import (
    ElKarouiVolModelStrategy,
)


@pytest.mark.parametrize(
    "strategy_cls",
    [
        ArmstrongCycleStrategy,
        ElKarouiVolModelStrategy,
    ],
)
def test_r_and_d_safety_flags(strategy_cls) -> None:
    """
    Diese Tests stellen sicher, dass die beiden Strategien sauber im
    R&D-Track verankert bleiben und nicht versehentlich live-fähig werden.
    """
    assert strategy_cls.IS_LIVE_READY is False
    assert strategy_cls.TIER == "r_and_d"
    assert strategy_cls.ALLOWED_ENVIRONMENTS == [
        "offline_backtest",
        "research",
    ]


@pytest.mark.parametrize(
    "strategy_cls_name",
    [
        "ArmstrongCycleStrategy",
        "ElKarouiVolModelStrategy",
    ],
)
def test_r_and_d_strategies_have_required_class_level_attributes(strategy_cls_name: str) -> None:
    """
    Defensive Test: Stellt sicher, dass die wichtigsten Meta-Attribute
    auf Klassenebene existieren. So schlagen Tests früh fehl, falls
    beim Refactoring etwas entfernt oder umbenannt wird.
    """
    mapping = {
        "ArmstrongCycleStrategy": ArmstrongCycleStrategy,
        "ElKarouiVolModelStrategy": ElKarouiVolModelStrategy,
    }
    strategy_cls = mapping[strategy_cls_name]

    for attr in ("IS_LIVE_READY", "ALLOWED_ENVIRONMENTS", "TIER"):
        assert hasattr(
            strategy_cls,
            attr,
        ), f"{strategy_cls_name} muss Attribut {attr} besitzen"


@pytest.mark.parametrize(
    "strategy_cls",
    [
        ArmstrongCycleStrategy,
        ElKarouiVolModelStrategy,
    ],
)
def test_r_and_d_strategies_document_research_only_intent(strategy_cls) -> None:
    """
    Optionaler Meta-Test: Dokumentiert explizit, dass diese Strategien
    nur für Research gedacht sind – der Test selbst ist simpel, aber
    die Message ist wichtig.
    """
    # Dieser Test ist vor allem ein dokumentierter Guardrail:
    # Falls jemand IS_LIVE_READY oder TIER ändert, gibt es hier
    # eine zweite Stelle, die Alarm schlägt.
    assert strategy_cls.IS_LIVE_READY is False
    assert strategy_cls.TIER == "r_and_d"
