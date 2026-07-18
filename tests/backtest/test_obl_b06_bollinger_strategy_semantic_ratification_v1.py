"""OBL_B06 Bollinger strategy-semantic ratification — fail-closed blocker locks.

No productive entry_side activation. Documents that LONG/SHORT Strategy Intent
remains unratified while EXIT on -1 and ENTRY event-kind on +1 stay confirmed.
"""

from __future__ import annotations

from pathlib import Path

import src.backtest.strategy_signal_suitability_agreement_adapter_v1 as adapter_mod
from src.backtest.strategy_signal_suitability_agreement_adapter_v1 import (
    normalize_strategy_signal_to_suitability_agreement_material_v1,
    resolve_strategy_signal_encoding_class_v1,
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
EVIDENCE = REPO_ROOT / "docs" / "evidence" / "obl_b06_bollinger_strategy_semantic_ratification_v1"
BOLLINGER_SRC = REPO_ROOT / "src" / "strategies" / "bollinger.py"
ENGINE_SRC = REPO_ROOT / "src" / "backtest" / "engine.py"
B05_SSOT = REPO_ROOT / "config" / "governance" / "obl_b05_bollinger_long_semantic_decision_v1.json"


def _bollinger_provenance():
    return _provenance(
        configured_strategy_id="bollinger_bands",
        executed_strategy_id="bollinger_bands",
        strategy_owner="strategies.bollinger",
    )


def test_evidence_bundle_present_and_blocker_named() -> None:
    assert EVIDENCE.is_dir()
    for name in (
        "README.md",
        "repo_state.txt",
        "search_inventory.txt",
        "semantic_authority_map.md",
        "signal_truth_table.md",
        "classic_vs_integrated_interpretation.md",
        "verdict.txt",
    ):
        assert (EVIDENCE / name).is_file(), name
    verdict = (EVIDENCE / "verdict.txt").read_text(encoding="utf-8")
    assert "BOLLINGER_SEMANTICS_CONFIRMED=false" in verdict
    assert "SIGNAL_PLUS_ONE_MEANS=AMBIGUOUS" in verdict
    assert "SIGNAL_MINUS_ONE_MEANS=EXIT" in verdict
    assert "SIGNAL_ZERO_MEANS=FLAT" in verdict
    assert "ENTRY_SIDE_AUTHORITY=NONE" in verdict
    assert "RATIFICATION_BLOCKER=BOLLINGER_STRATEGY_INTENT_LONG_SHORT_AUTHORITY_MISSING" in verdict
    assert "GENERIC_SIGN_HEURISTIC_INTRODUCED=false" in verdict
    assert "LIVE_AUTHORIZED=false" in verdict


def test_b05_ssot_still_ambiguous_and_side_inactive() -> None:
    body = B05_SSOT.read_text(encoding="utf-8")
    assert '"BOLLINGER_DECISION": "CONTRACT_REMAINS_AMBIGUOUS"' in body
    assert '"BOLLINGER_SIDE_ACTIVATED": false' in body


def test_producer_geometry_entry_exit_no_short() -> None:
    src = BOLLINGER_SRC.read_text(encoding="utf-8")
    assert "signals[cross_entry] = 1" in src
    assert "signals[cross_exit] = -1" in src
    assert "1=entry" in src
    assert "-1 (exit)" in src or "1=entry, -1=exit" in src
    # CP02 remains: class doc still says long while method says entry
    assert "1 (long)" in src
    assert "short_entry" not in src.lower()
    assert "upper" in src  # bands computed
    # No upper-band short assignment
    assert "signals[cross_entry] = -1" not in src


def test_encoding_class_entry_exit_and_adapter_side_none_for_all_events() -> None:
    assert (
        resolve_strategy_signal_encoding_class_v1("bollinger_bands")
        is StrategySignalEncodingClassV1.ENTRY_EXIT_EVENT_V1
    )
    prov = _bollinger_provenance()
    instrument = "okx:linear_perpetual:1INCH:USDT:USDT:perp"

    mat_entry = normalize_strategy_signal_to_suitability_agreement_material_v1(
        _binding([0, 1, 0], provenance=prov),
        instrument_id=instrument,
        trading_epoch=1,
    )
    assert mat_entry.event_kind is StrategyAgreementEventKindV1.ENTRY
    assert mat_entry.entry_side is StrategyEntrySideCarrierV1.NONE
    assert mat_entry.cycle_signal_value == 1

    mat_exit = normalize_strategy_signal_to_suitability_agreement_material_v1(
        _binding([0, -1, 0], provenance=prov),
        instrument_id=instrument,
        trading_epoch=1,
    )
    assert mat_exit.event_kind is StrategyAgreementEventKindV1.EXIT
    assert mat_exit.entry_side is StrategyEntrySideCarrierV1.NONE
    assert mat_exit.cycle_signal_value == -1

    mat_flat = normalize_strategy_signal_to_suitability_agreement_material_v1(
        _binding([0, 0, 0], provenance=prov),
        instrument_id=instrument,
        trading_epoch=1,
    )
    assert mat_flat.event_kind is StrategyAgreementEventKindV1.NONE
    assert mat_flat.entry_side is StrategyEntrySideCarrierV1.NONE

    assert adapter_mod._TREND_FOLLOWING_ENTRY_SIDE_RATIFIED_OWNER == "trend_following"
    assert "bollinger" not in adapter_mod._TREND_FOLLOWING_ENTRY_SIDE_RATIFIED_OWNER


def test_classic_engine_long_reinterpretation_exists_but_is_not_mv2_side_authority() -> None:
    engine = ENGINE_SRC.read_text(encoding="utf-8")
    assert "LONG ENTRY" in engine
    assert "elif signal == -1 and current_trade is not None:" in engine
    # Path split: classic buy language must not imply Integrated entry_side ratification
    assert "1=Buy, -1=Sell, 0=Hold" in engine
    adapter = (
        REPO_ROOT / "src" / "backtest" / "strategy_signal_suitability_agreement_adapter_v1.py"
    ).read_text(encoding="utf-8")
    assert "Other ENTRY_EXIT\n    owners remain ``NONE``" in adapter or (
        "executed_strategy_id != _TREND_FOLLOWING_ENTRY_SIDE_RATIFIED_OWNER" in adapter
    )
