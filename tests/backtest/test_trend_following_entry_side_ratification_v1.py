"""OBL_B05 trend_following entry_side ratification v1 — focused contracts."""

from __future__ import annotations

import json
from pathlib import Path

import src.backtest.strategy_signal_suitability_agreement_adapter_v1 as adapter_mod
from src.backtest.mv2_research_wiring_v1 import (
    resolve_agreement_bound_directional_cycle_v1,
)
from src.backtest.strategy_signal_suitability_agreement_adapter_v1 import (
    normalize_strategy_signal_to_suitability_agreement_material_v1,
)
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
    StrategySignalEncodingClassV1,
    deserialize_strategy_suitability_agreement_material_v1,
    serialize_strategy_suitability_agreement_material_v1,
)
from tests.backtest.test_strategy_signal_suitability_agreement_adapter_v1 import (
    _binding,
    _provenance,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = (
    REPO_ROOT / "config" / "governance" / "obl_b05_trend_following_entry_side_ratification_v1.json"
)
GOV_DOC = (
    REPO_ROOT / "docs" / "governance" / "OBL_B05_TREND_FOLLOWING_ENTRY_SIDE_RATIFICATION_V1.md"
)
ADAPTER_SRC = REPO_ROOT / "src" / "backtest" / "strategy_signal_suitability_agreement_adapter_v1.py"
TREND_SRC = REPO_ROOT / "src" / "strategies" / "trend_following.py"

_ENTRY_EXIT_OTHERS = frozenset(
    {
        "bollinger_bands",
        "ecm_cycle",
        "macd",
        "mean_reversion",
        "momentum_1h",
        "my_strategy",
    }
)


def _ssot() -> dict:
    return json.loads(SSOT_PATH.read_text(encoding="utf-8"))


def _normalize(strategy_id: str, values: list[int], epoch: int):
    return normalize_strategy_signal_to_suitability_agreement_material_v1(
        _binding(
            values,
            provenance=_provenance(
                configured_strategy_id=strategy_id,
                executed_strategy_id=strategy_id,
            ),
        ),
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=epoch,
    )


def test_ssot_and_governance_markers() -> None:
    assert SSOT_PATH.is_file()
    assert GOV_DOC.is_file()
    data = _ssot()
    body = GOV_DOC.read_text(encoding="utf-8")
    assert data["slice_id"] == "OBL_B05_TREND_FOLLOWING_ENTRY_SIDE_RATIFICATION_V1"
    assert data["TREND_FOLLOWING_SIDE_RATIFIED"] is True
    assert data["PRODUCTIVE_TREND_FOLLOWING_SIDE_EMISSION_CHANGED"] is True
    assert data["OTHER_PRODUCER_SIDE_EMISSION_CHANGED"] is False
    assert data["BOLLINGER_SIDE_ACTIVATED"] is False
    assert data["MACD_SIDE_ACTIVATED"] is False
    assert data["LIVE_AUTHORIZED"] is False
    assert data["ORDERS_ENABLED"] is False
    assert data["short_entry_condition_present"] is False
    assert data["short_side_emitted"] is False
    assert data["exit_never_mapped_to_short"] is True
    assert data["producer_id"] == "trend_following"
    assert "DOCS_TOKEN_OBL_B05_TREND_FOLLOWING_ENTRY_SIDE_RATIFICATION_V1" in body
    assert "TREND_FOLLOWING_SIDE_RATIFIED: true" in body


def test_productive_trend_following_contract_long_entry_exit_not_short() -> None:
    source = TREND_SRC.read_text(encoding="utf-8")
    assert "- 1 (long):" in source
    assert "- -1 (exit):" in source
    assert "Long-Entry:" in source
    assert "signals[entry_trigger] = 1" in source
    assert "signals[exit_trigger] = -1" in source
    # Productive generator never assigns a short-entry polarity.
    assert "signals[entry_trigger] = -1" not in source
    assert "short_entry" not in source.lower()


def test_trend_following_long_entry_emits_long() -> None:
    material = _normalize("trend_following", [1, 0, -1], 0)
    assert material.encoding_class is StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1
    assert material.event_kind is StrategyAgreementEventKindV1.ENTRY
    assert material.cycle_signal_value == 1
    assert material.entry_side is StrategyEntrySideCarrierV1.LONG
    assert resolve_agreement_bound_directional_cycle_v1(material) == 1


def test_trend_following_exit_and_flat_emit_none_not_short() -> None:
    exit_mat = _normalize("trend_following", [1, 0, -1], 2)
    flat_mat = _normalize("trend_following", [1, 0, -1], 1)
    assert exit_mat.event_kind is StrategyAgreementEventKindV1.EXIT
    assert exit_mat.cycle_signal_value == -1
    assert exit_mat.entry_side is StrategyEntrySideCarrierV1.NONE
    assert resolve_agreement_bound_directional_cycle_v1(exit_mat) is None
    assert flat_mat.event_kind is StrategyAgreementEventKindV1.NONE
    assert flat_mat.cycle_signal_value == 0
    assert flat_mat.entry_side is StrategyEntrySideCarrierV1.NONE
    assert resolve_agreement_bound_directional_cycle_v1(flat_mat) is None


def test_bollinger_and_macd_remain_none() -> None:
    for strategy_id in ("bollinger_bands", "macd"):
        material = _normalize(strategy_id, [1, 0, -1], 0)
        assert material.event_kind is StrategyAgreementEventKindV1.ENTRY
        assert material.entry_side is StrategyEntrySideCarrierV1.NONE
        assert resolve_agreement_bound_directional_cycle_v1(material) is None


def test_all_other_entry_exit_producers_remain_none() -> None:
    for strategy_id in sorted(_ENTRY_EXIT_OTHERS):
        for epoch, expected_event in (
            (0, StrategyAgreementEventKindV1.ENTRY),
            (1, StrategyAgreementEventKindV1.NONE),
            (2, StrategyAgreementEventKindV1.EXIT),
        ):
            material = _normalize(strategy_id, [1, 0, -1], epoch)
            assert material.event_kind is expected_event
            assert material.entry_side is StrategyEntrySideCarrierV1.NONE
            assert resolve_agreement_bound_directional_cycle_v1(material) is None


def test_missing_serialized_entry_side_remains_backward_compatible_none() -> None:
    material = _normalize("trend_following", [1, 0, -1], 0)
    assert material.entry_side is StrategyEntrySideCarrierV1.LONG
    payload = serialize_strategy_suitability_agreement_material_v1(material)
    del payload["entry_side"]
    restored = deserialize_strategy_suitability_agreement_material_v1(payload)
    assert restored.entry_side is StrategyEntrySideCarrierV1.NONE
    assert resolve_agreement_bound_directional_cycle_v1(restored) is None


def test_directional_cycle_only_via_explicit_long_short_carrier() -> None:
    long_mat = _normalize("trend_following", [1], 0)
    none_mat = _normalize("bollinger_bands", [1], 0)
    assert resolve_agreement_bound_directional_cycle_v1(long_mat) == 1
    assert resolve_agreement_bound_directional_cycle_v1(none_mat) is None


def test_legacy_adapter_path_outside_trend_following_unchanged() -> None:
    """Positional families remain entry_side=NONE; resolve still uses cycle."""
    rsi = _normalize("rsi_reversion", [1, 0, -1], 0)
    assert rsi.encoding_class is StrategySignalEncodingClassV1.POSITIONAL_LS_STATE_V1
    assert rsi.entry_side is StrategyEntrySideCarrierV1.NONE
    assert resolve_agreement_bound_directional_cycle_v1(rsi) == 1
    rsi_short = _normalize("rsi_reversion", [1, 0, -1], 2)
    assert rsi_short.entry_side is StrategyEntrySideCarrierV1.NONE
    assert resolve_agreement_bound_directional_cycle_v1(rsi_short) == -1


def test_adapter_source_scopes_long_emission_to_trend_following_only() -> None:
    source = ADAPTER_SRC.read_text(encoding="utf-8")
    assert "_TREND_FOLLOWING_ENTRY_SIDE_RATIFIED_OWNER" in source
    assert "_resolve_entry_side_carrier_v1" in source
    assert "executed_strategy_id != _TREND_FOLLOWING_ENTRY_SIDE_RATIFIED_OWNER" in source
    assert "StrategyEntrySideCarrierV1.LONG" in source
    # SHORT must not be emitted by the productive resolver path.
    assert "StrategyEntrySideCarrierV1.SHORT" not in source
    assert adapter_mod._TREND_FOLLOWING_ENTRY_SIDE_RATIFIED_OWNER == "trend_following"


def test_closed_owner_set_unchanged_seven_entry_exit_owners() -> None:
    assert frozenset(adapter_mod._ENTRY_EXIT_EVENT_OWNERS) == (
        _ENTRY_EXIT_OTHERS | {"trend_following"}
    )
    assert len(adapter_mod._ENTRY_EXIT_EVENT_OWNERS) == 7
