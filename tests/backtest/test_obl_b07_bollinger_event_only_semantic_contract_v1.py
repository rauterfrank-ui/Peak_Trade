"""OBL_B07 Bollinger EVENT_ONLY semantic contract — focused ratification tests."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

import src.backtest.strategy_signal_suitability_agreement_adapter_v1 as adapter_mod
from src.backtest.mv2_research_wiring_v1 import (
    resolve_agreement_bound_directional_cycle_v1,
)
from src.backtest.strategy_signal_suitability_agreement_adapter_v1 import (
    normalize_strategy_signal_to_suitability_agreement_material_v1,
)
from src.strategies.bollinger_event_semantic_contract_v1 import (
    BOLLINGER_STRATEGY_ID,
    BollingerSignalEventV1,
    classify_bollinger_raw_signal_event_v1,
    resolve_bollinger_event_semantic_v1,
)
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategyEntrySideCarrierV1,
    StrategySignalEncodingClassV1,
)
from tests.backtest.test_strategy_signal_suitability_agreement_adapter_v1 import (
    _binding,
    _provenance,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = (
    REPO_ROOT / "config" / "governance" / "obl_b07_bollinger_event_only_semantic_contract_v1.json"
)
GOV_DOC = REPO_ROOT / "docs" / "governance" / "OBL_B07_BOLLINGER_EVENT_ONLY_SEMANTIC_CONTRACT_V1.md"
CONTRACT_SRC = REPO_ROOT / "src" / "strategies" / "bollinger_event_semantic_contract_v1.py"
ENGINE_SRC = REPO_ROOT / "src" / "backtest" / "engine.py"
EVIDENCE = REPO_ROOT / "docs" / "evidence" / "obl_b07_bollinger_event_only_semantic_contract_v1"


def _ssot() -> dict:
    return json.loads(SSOT_PATH.read_text(encoding="utf-8"))


def _normalize_bollinger(values: list[int], epoch: int):
    return normalize_strategy_signal_to_suitability_agreement_material_v1(
        _binding(
            values,
            provenance=_provenance(
                configured_strategy_id=BOLLINGER_STRATEGY_ID,
                executed_strategy_id=BOLLINGER_STRATEGY_ID,
                strategy_owner="strategies.bollinger",
            ),
        ),
        instrument_id="okx:linear_perpetual:1INCH:USDT:USDT:perp",
        trading_epoch=epoch,
    )


def test_ssot_and_governance_markers() -> None:
    assert SSOT_PATH.is_file()
    assert GOV_DOC.is_file()
    assert CONTRACT_SRC.is_file()
    data = _ssot()
    body = GOV_DOC.read_text(encoding="utf-8")
    assert data["OPERATOR_OPTION"] == "OPTION_EVENT_ONLY"
    assert data["BOLLINGER_EVENT_ONLY_RATIFIED"] is True
    assert data["LONG_ONLY_AUTHORIZED"] is False
    assert data["SHORT_ENTRY_AUTHORIZED"] is False
    assert data["SYMMETRIC_SHORT_GEOMETRY_AUTHORIZED"] is False
    assert data["STRATEGY_DIRECTION"] == "NONE"
    assert data["ENTRY_SIDE"] == "NONE"
    assert data["CLASSIC_LONG_IS_CANONICAL"] is False
    assert data["CLASSIC_LONG_PROPAGATES_TO_INTEGRATED"] is False
    assert data["BOLLINGER_SIDE_ACTIVATED"] is False
    assert data["LIVE_AUTHORIZED"] is False
    assert data["ORDERS_ENABLED"] is False
    assert "DOCS_TOKEN_OBL_B07_BOLLINGER_EVENT_ONLY_SEMANTIC_CONTRACT_V1" in body
    assert "OPERATOR_OPTION: OPTION_EVENT_ONLY" in body


def test_contract_raw_mapping_and_direction_none() -> None:
    assert classify_bollinger_raw_signal_event_v1(1) is BollingerSignalEventV1.ENTRY_EVENT
    assert classify_bollinger_raw_signal_event_v1(-1) is BollingerSignalEventV1.EXIT_EVENT
    assert classify_bollinger_raw_signal_event_v1(0) is BollingerSignalEventV1.FLAT_NO_EVENT
    for raw in (1, -1, 0, 1.0, -1.0, 0.0):
        result = resolve_bollinger_event_semantic_v1(raw)
        assert result.direction == "NONE"
        assert result.entry_side == "NONE"


def test_contract_fail_closed_on_missing_nan_unsupported() -> None:
    for raw in (None, True, False, math.nan, 1.5, 2, -2, "long", object()):
        assert (
            classify_bollinger_raw_signal_event_v1(raw)
            is BollingerSignalEventV1.UNKNOWN_FAIL_CLOSED
        )
        result = resolve_bollinger_event_semantic_v1(raw)
        assert result.event is BollingerSignalEventV1.UNKNOWN_FAIL_CLOSED
        assert result.direction == "NONE"
        assert result.entry_side == "NONE"


def test_adapter_plus_one_entry_event_no_long_no_side() -> None:
    material = _normalize_bollinger([0, 1, 0], 1)
    assert material.encoding_class is StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1
    assert material.event_kind is StrategyAgreementEventKindV1.ENTRY
    assert material.cycle_signal_value == 1
    assert material.entry_side is StrategyEntrySideCarrierV1.NONE
    assert resolve_agreement_bound_directional_cycle_v1(material) is None


def test_adapter_minus_one_exit_event_no_short() -> None:
    material = _normalize_bollinger([0, -1, 0], 1)
    assert material.event_kind is StrategyAgreementEventKindV1.EXIT
    assert material.cycle_signal_value == -1
    assert material.entry_side is StrategyEntrySideCarrierV1.NONE
    assert resolve_agreement_bound_directional_cycle_v1(material) is None


def test_adapter_zero_flat_no_event() -> None:
    material = _normalize_bollinger([0, 0, 0], 1)
    assert material.event_kind is StrategyAgreementEventKindV1.NONE
    assert material.cycle_signal_value == 0
    assert material.entry_side is StrategyEntrySideCarrierV1.NONE
    assert resolve_agreement_bound_directional_cycle_v1(material) is None


def test_no_plus_one_long_and_no_minus_one_short_authority() -> None:
    entry = _normalize_bollinger([1], 0)
    exit_m = _normalize_bollinger([-1], 0)
    assert entry.entry_side is not StrategyEntrySideCarrierV1.LONG
    assert exit_m.entry_side is not StrategyEntrySideCarrierV1.SHORT
    assert adapter_mod._BOLLINGER_EVENT_ONLY_OWNER == BOLLINGER_STRATEGY_ID
    assert "bollinger" not in adapter_mod._TREND_FOLLOWING_ENTRY_SIDE_RATIFIED_OWNER


def test_classic_long_exists_but_is_not_integrated_authority() -> None:
    engine = ENGINE_SRC.read_text(encoding="utf-8")
    assert "LONG ENTRY" in engine
    assert "1=Buy, -1=Sell, 0=Hold" in engine
    # Integrated path: Bollinger ENTRY stays side-less.
    material = _normalize_bollinger([1], 0)
    assert material.entry_side is StrategyEntrySideCarrierV1.NONE
    assert resolve_agreement_bound_directional_cycle_v1(material) is None
    contract = CONTRACT_SRC.read_text(encoding="utf-8")
    assert "CLASSIC" in contract.upper() or "Classic" in contract or "classic" in contract
    assert "Never maps polarity to LONG/SHORT" in contract


def test_no_cycle_bull_bear_position_inference_in_contract() -> None:
    src = CONTRACT_SRC.read_text(encoding="utf-8")
    lowered = src.lower()
    assert "bull" not in lowered
    assert "bear" not in lowered
    assert "cycle_state" not in lowered
    assert "position_state" not in lowered
    assert "dynamic_scope" not in lowered
    # Function signature is raw-only.
    assert "def classify_bollinger_raw_signal_event_v1(raw:" in src


def test_evidence_bundle_markers() -> None:
    assert EVIDENCE.is_dir()
    verdict = (EVIDENCE / "verdict.txt").read_text(encoding="utf-8")
    assert "OPERATOR_OPTION=OPTION_EVENT_ONLY" in verdict
    assert "SIGNAL_PLUS_ONE_MEANS=ENTRY_EVENT" in verdict
    assert "ENTRY_SIDE=NONE" in verdict
    assert "LONG_ONLY_AUTHORIZED=false" in verdict
