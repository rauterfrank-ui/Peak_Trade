"""Static contract: Stage-2 Shadow Campaign Input Authority Owner Ratification v1."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = REPO_ROOT / "docs" / "ops"
RATIFICATION = (
    DOCS / "PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_OWNER_RATIFICATION_V1.md"
)
PLAN = (
    DOCS / "PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_IMPLEMENTATION_PLAN_V1.md"
)
DECISIONS = DOCS / "PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_DECISIONS_V1.json"

REQUIRED_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=OWNER_AUTHORITY_RATIFICATION",
    "STATUS=OWNER_RATIFIED_BOUNDED_IMPLEMENTATION_AUTHORIZED",
    "BASELINE_ORIGIN_MAIN_SHA=55922609182a3166320c0a66a3a0b7cda5c13090",
    "AUTHORITY_SURFACE=B",
    "O4_UNCHANGED=true",
    "OHLCV_SOURCE=VENUE_NATIVE_FINALIZED_CANDLES",
    "MARK_PRICE=REQUIRED_SEPARATE_FIELD",
    "CANDLE_MARK_TRADE_EQUIVALENCE=FORBIDDEN",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "PRODUCTIVE_NUMERIC_VALUES_SET=0",
    "SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "OPEN_TIP_BARS=FORBIDDEN",
    "SILENT_REWRITES=FORBIDDEN",
    "RANDOM_BAR_SPLITTING=FORBIDDEN",
    "IID_RESAMPLING=FORBIDDEN_BY_DEFAULT",
    "MULTI_INSTRUMENT_POOLING=FORBIDDEN",
)

FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "PRODUCTIVE_NUMERIC_VALUES_SET=1",
    "O4_UNCHANGED=false",
    "RESULTV1_MAPPING_AUTHORIZED=true",
    "CANDLE_MARK_TRADE_EQUIVALENCE=ALLOWED",
    "AUTHORITY_SURFACE=A",
    "LIVE_ORDERS=true",
)


def test_ratification_artifacts_exist_v1() -> None:
    assert RATIFICATION.is_file()
    assert PLAN.is_file()
    assert DECISIONS.is_file()


def test_ratification_markers_v1() -> None:
    text = RATIFICATION.read_text(encoding="utf-8")
    for marker in REQUIRED_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_CLAIMS:
        assert claim not in text, claim


def test_decisions_json_matches_owner_go_v1() -> None:
    data = json.loads(DECISIONS.read_text(encoding="utf-8"))
    assert data["authority_surface"] == "B"
    assert data["o4_unchanged"] is True
    assert data["input_authority"] is False
    assert data["runtime_implemented"] is False
    assert data["productive_numeric_values_set"] == 0
    assert data["baseline_origin_main_sha"] == ("55922609182a3166320c0a66a3a0b7cda5c13090")
    assert data["decisions"]["PRICE_SEMANTICS"]["ohlcv_source"] == (
        "VENUE_NATIVE_FINALIZED_CANDLES"
    )
    assert data["decisions"]["PRICE_SEMANTICS"]["mark_price"] == ("REQUIRED_SEPARATE_FIELD")
    assert data["decisions"]["PRICE_SEMANTICS"]["candle_mark_trade_equivalence"] == ("FORBIDDEN")
    assert data["decisions"]["INSTRUMENT_BINDING"]["multi_instrument_pooling"] is False
    assert data["decisions"]["PARTITION_PROTOCOL"]["random_bar_splitting"] is False
    assert data["decisions"]["PARTITION_PROTOCOL"]["purge_embargo_numeric_magnitudes"] is None
    assert data["decisions"]["WALK_FORWARD_PROTOCOL"]["fold_sizes_and_cadence_numbers"] is None
    assert data["decisions"]["BOOTSTRAP_PROTOCOL"]["block_length"] is None
    assert data["decisions"]["BOOTSTRAP_PROTOCOL"]["path_count"] is None
    assert data["decisions"]["STRESS_PROTOCOL"]["numeric_magnitudes_ratified"] is False
    families = data["decisions"]["STRESS_PROTOCOL"]["structural_families"]
    assert "gaps_missing_bars" in families
    assert "sequence_path_disruption" in families
    assert len(families) == 10


def test_implementation_plan_boundary_v1() -> None:
    text = PLAN.read_text(encoding="utf-8")
    assert "AUTHORITY_SURFACE=B" in text
    assert "O4_UNCHANGED=true" in text
    assert "INPUT_AUTHORITY=false" in text
    assert "No productive calibration run" in text
    assert "OWNER_MERGE_GO" in text
