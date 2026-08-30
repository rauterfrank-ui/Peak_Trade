"""Offline contract tests for MASTER_V2_MINIMAL_SELECTOR_V1.

OWNER_POLICY_VERSION=V1
HISTORICAL_CLAIM=false
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

from src.ops.master_v2_minimal_selector_v1.constants_v1 import (
    CAP22_ROLE,
    CAP22_SELECTION_AUTHORITY,
    CAP22_SELECTION_AUTHORITY_ALLOWED,
    D1_HISTORICAL_CLAIM,
    D1_INSTRUMENT_CLASS,
    D2_BTC_OR_BASE_EXCLUSION,
    D2_HISTORICAL_CLAIM,
    D3_MULTI_ELIGIBLE_RESOLUTION,
    D4_SELECTION_REFRESH_MODE,
    HISTORICAL_CLAIM,
    LIVE_AUTHORIZED,
    NO_HOT_PATH_RESCAN,
    NO_IMPLICIT_FALLBACK_INSTRUMENT,
    ORDERS_AUTHORIZED,
    OWNER_SELECTOR_POLICY_VERSION,
    RANKING_POLICY_REQUIRED_NOW,
    REASON_NO_SELECTION_INCOMPLETE_SOURCE,
    REASON_NO_SELECTION_MULTIPLE_ELIGIBLE,
    REASON_NO_SELECTION_STALE_OR_INVALID_SOURCE,
    REASON_NO_SELECTION_ZERO_ELIGIBLE,
    REASON_SELECTED_EXACTLY_ONE,
    RUNTIME_ACTIVATION_ALLOWED,
    SELECTOR_HAS_DOUBLE_PLAY_SIDE_AUTHORITY,
    SELECTOR_HAS_LEVERAGE_AUTHORITY,
    SELECTOR_HAS_POSITION_SIZING_AUTHORITY,
    SELECTOR_HAS_TRADING_AUTHORITY,
    STATUS_NO_SELECTION,
    STATUS_SELECTED,
    VENUE,
)
from src.ops.master_v2_minimal_selector_v1.models_v1 import compute_policy_digest_v1
from src.ops.master_v2_minimal_selector_v1.persistence_v1 import (
    load_and_validate_selection_decision_v1,
    persist_selection_decision_atomic_v1,
)
from src.ops.master_v2_minimal_selector_v1.runtime_binding_adapter_v1 import (
    adapt_master_v2_selection_to_runtime_binding_v1,
)
from src.ops.master_v2_minimal_selector_v1.selection_v1 import (
    decide_master_v2_minimal_selection_v1,
    trigger_master_v2_minimal_selection_v1,
)

PACKAGE_DIR = Path(__file__).resolve().parents[2] / "src" / "ops" / "master_v2_minimal_selector_v1"
SOURCE_EVENT = "1700000000000"


def _perp(
    inst_id: str = "ETH-USDT-SWAP",
    *,
    state: str = "live",
    tick: str = "0.01",
    lot: str = "1",
    min_sz: str = "1",
    ct_val: str = "0.01",
    ct_val_ccy: str | None = None,
    base: str | None = None,
    quote: str = "USDT",
    settle: str = "USDT",
    ct_type: str = "linear",
    inst_type: str = "SWAP",
    exp: str = "",
    **extra: object,
) -> dict:
    token = inst_id.split("-")[0]
    row = {
        "instId": inst_id,
        "instType": inst_type,
        "state": state,
        "baseCcy": base if base is not None else token,
        "quoteCcy": quote,
        "settleCcy": settle,
        "ctType": ct_type,
        "ctVal": ct_val,
        "ctValCcy": ct_val_ccy if ct_val_ccy is not None else token,
        "tickSz": tick,
        "lotSz": lot,
        "minSz": min_sz,
        "uly": f"{base if base is not None else token}-{quote}",
        "expTime": exp,
    }
    row.update(extra)
    return row


def _payload(rows: list[dict]) -> dict:
    return {"code": "0", "msg": "", "data": rows}


def _marks(*inst_ids: str) -> dict:
    return {
        "code": "0",
        "msg": "",
        "data": [{"instId": i, "markPx": "100.5"} for i in inst_ids],
    }


def _decide(
    rows: list[dict],
    marks: tuple[str, ...] | None = None,
    **kwargs: object,
):
    ids = marks if marks is not None else tuple(r["instId"] for r in rows if r.get("instId"))
    return decide_master_v2_minimal_selection_v1(
        source_payload=_payload(rows),
        mark_price_payload=_marks(*ids),
        source_event_time=SOURCE_EVENT,
        venue=VENUE,
        **kwargs,
    )


def test_owner_policy_version_and_historical_claim() -> None:
    assert OWNER_SELECTOR_POLICY_VERSION == "V1"
    assert HISTORICAL_CLAIM is False
    assert D1_HISTORICAL_CLAIM is False
    assert D2_HISTORICAL_CLAIM is False
    assert D1_INSTRUMENT_CLASS == "PERP_SWAP_ONLY"
    assert D2_BTC_OR_BASE_EXCLUSION == "NO_ASSET_EXCLUDE"
    assert D3_MULTI_ELIGIBLE_RESOLUTION == "FAIL_CLOSED_UNLESS_EXACTLY_ONE"
    assert D4_SELECTION_REFRESH_MODE == "EXPLICIT_CONTROL_PLANE_TRIGGER_ONLY"
    assert compute_policy_digest_v1() == compute_policy_digest_v1()


def test_t1_zero_eligible() -> None:
    decision = _decide([])
    assert decision.decision_status == STATUS_NO_SELECTION
    assert decision.selected_native_instrument_id is None
    assert decision.eligible_count == 0
    assert decision.decision_reason == REASON_NO_SELECTION_ZERO_ELIGIBLE


def test_t2_one_eligible_perp() -> None:
    decision = _decide([_perp("ETH-USDT-SWAP")])
    assert decision.decision_status == STATUS_SELECTED
    assert decision.selected_native_instrument_id == "ETH-USDT-SWAP"
    assert decision.eligible_count == 1
    assert decision.decision_reason == REASON_SELECTED_EXACTLY_ONE
    inverse = _decide([_perp("SOL-USDT-SWAP", ct_type="inverse")])
    assert inverse.selected_native_instrument_id == "SOL-USDT-SWAP"


def test_t3_two_eligible_perps() -> None:
    decision = _decide([_perp("ETH-USDT-SWAP"), _perp("SOL-USDT-SWAP")])
    assert decision.decision_status == STATUS_NO_SELECTION
    assert decision.selected_native_instrument_id is None
    assert decision.eligible_count == 2
    assert decision.decision_reason == REASON_NO_SELECTION_MULTIPLE_ELIGIBLE


def test_t4_btc_perp_sole_eligible_no_asset_exclude() -> None:
    decision = _decide([_perp("BTC-USDT-SWAP", base="BTC", ct_val_ccy="BTC")])
    assert decision.decision_status == STATUS_SELECTED
    assert decision.selected_native_instrument_id == "BTC-USDT-SWAP"
    assert decision.decision_reason == REASON_SELECTED_EXACTLY_ONE
    xbt = _decide([_perp("XBT-USDT-SWAP", base="XBT", ct_val_ccy="XBT")])
    assert xbt.selected_native_instrument_id == "XBT-USDT-SWAP"


def test_t5_dated_future_only() -> None:
    decision = _decide(
        [
            _perp(
                "ETH-USDT-250328",
                inst_type="FUTURES",
                exp="1743120000000",
                base="ETH",
                ct_val_ccy="ETH",
            )
        ]
    )
    assert decision.decision_status == STATUS_NO_SELECTION
    assert decision.selected_native_instrument_id is None
    assert decision.decision_reason == REASON_NO_SELECTION_ZERO_ELIGIBLE


def test_t6_spot_only() -> None:
    decision = _decide([_perp("ETH-USDT", inst_type="SPOT", base="ETH", ct_val_ccy="ETH")])
    assert decision.decision_status == STATUS_NO_SELECTION
    assert decision.selected_native_instrument_id is None
    assert decision.decision_reason == REASON_NO_SELECTION_ZERO_ELIGIBLE


def test_t7_stale_or_incomplete_source() -> None:
    missing = decide_master_v2_minimal_selection_v1(source_payload=None)
    assert missing.decision_status == STATUS_NO_SELECTION
    assert missing.decision_reason == REASON_NO_SELECTION_INCOMPLETE_SOURCE

    malformed = decide_master_v2_minimal_selection_v1(source_payload={"code": "0", "data": "bad"})
    assert malformed.decision_status == STATUS_NO_SELECTION
    assert malformed.decision_reason == REASON_NO_SELECTION_STALE_OR_INVALID_SOURCE

    no_event = decide_master_v2_minimal_selection_v1(
        source_payload=_payload([_perp("ETH-USDT-SWAP")]),
        mark_price_payload=_marks("ETH-USDT-SWAP"),
        source_event_time="",
    )
    assert no_event.decision_status == STATUS_NO_SELECTION
    assert no_event.decision_reason == REASON_NO_SELECTION_INCOMPLETE_SOURCE

    duplicate = _decide(
        [_perp("ETH-USDT-SWAP"), _perp("ETH-USDT-SWAP", tick="0.02")],
        marks=("ETH-USDT-SWAP",),
    )
    assert duplicate.decision_status == STATUS_NO_SELECTION
    assert duplicate.decision_reason == REASON_NO_SELECTION_STALE_OR_INVALID_SOURCE


def test_t8_ranking_input_cannot_change_selection() -> None:
    rows = [_perp("ETH-USDT-SWAP")]
    base = _decide(rows, ranking_snapshot=None)
    ranking_a = {"ranked": [{"id": "SOL-USDT-SWAP", "rank": 1}], "top20": ["SOL-USDT-SWAP"]}
    ranking_b = {"ranked": [{"id": "BTC-USDT-SWAP", "rank": 99}], "top50": ["BTC-USDT-SWAP"]}
    with_a = _decide(rows, ranking_snapshot=ranking_a)
    with_b = _decide(rows, ranking_snapshot=ranking_b)
    assert base.identity_digest == with_a.identity_digest == with_b.identity_digest
    assert base.selected_native_instrument_id == "ETH-USDT-SWAP"
    assert with_a.ranking_input_ignored is True
    assert RANKING_POLICY_REQUIRED_NOW is False
    assert CAP22_SELECTION_AUTHORITY is False
    assert CAP22_SELECTION_AUTHORITY_ALLOWED is False
    assert CAP22_ROLE == "CONTEXT_ONLY_OR_UNUSED"


def test_t9_no_fallback() -> None:
    empty = decide_master_v2_minimal_selection_v1(
        source_payload=_payload([]),
        mark_price_payload=_marks(),
        source_event_time=SOURCE_EVENT,
        default_instrument="ETH-USDT-SWAP",
        fallback_instrument="BTC-USDT-SWAP",
    )
    assert empty.selected_native_instrument_id is None
    assert empty.decision_reason == REASON_NO_SELECTION_ZERO_ELIGIBLE
    assert NO_IMPLICIT_FALLBACK_INSTRUMENT is True
    override = decide_master_v2_minimal_selection_v1(
        source_payload=_payload([_perp("ETH-USDT-SWAP")]),
        mark_price_payload=_marks("ETH-USDT-SWAP"),
        source_event_time=SOURCE_EVENT,
        manual_override_payload={"instrument": "BTC-USDT-SWAP"},
    )
    assert override.selected_native_instrument_id is None
    assert override.decision_status == STATUS_NO_SELECTION


def test_t10_no_automatic_cadence() -> None:
    assert NO_HOT_PATH_RESCAN is True
    assert D4_SELECTION_REFRESH_MODE == "EXPLICIT_CONTROL_PLANE_TRIGGER_ONLY"
    forbidden = (
        "refresh_cadence",
        "periodic",
        "background_refresh",
        "threading.Timer",
        "sched.",
        "while True",
        "sleep(",
    )
    for path in PACKAGE_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for token in forbidden:
            assert token.lower() not in lowered, f"{path.name} contains {token}"
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                raise AssertionError(f"while-loop in {path.name}")
    first = trigger_master_v2_minimal_selection_v1(
        source_payload=_payload([_perp("ETH-USDT-SWAP")]),
        mark_price_payload=_marks("ETH-USDT-SWAP"),
        source_event_time=SOURCE_EVENT,
    )
    second = trigger_master_v2_minimal_selection_v1(
        source_payload=_payload([_perp("ETH-USDT-SWAP")]),
        mark_price_payload=_marks("ETH-USDT-SWAP"),
        source_event_time=SOURCE_EVENT,
    )
    assert first.identity_digest == second.identity_digest
    assert "time." not in inspect.getsource(decide_master_v2_minimal_selection_v1)


def test_t11_reproducible_snapshot(tmp_path: Path) -> None:
    rows = [_perp("ETH-USDT-SWAP")]
    a = _decide(rows)
    b = _decide(rows)
    assert a.identity_digest == b.identity_digest
    assert a.to_dict()["identity_digest"] == b.to_dict()["identity_digest"]
    assert a.policy_digest == b.policy_digest
    persist_selection_decision_atomic_v1(state_root=tmp_path, decision=a)
    loaded = load_and_validate_selection_decision_v1(tmp_path)
    assert loaded.ok is True
    assert loaded.decision is not None
    assert loaded.decision.identity_digest == a.identity_digest


def test_t12_native_identity_preserved() -> None:
    native = "BTC-USDT-SWAP"
    decision = _decide([_perp(native, base="BTC", ct_val_ccy="BTC")])
    assert decision.selected_native_instrument_id == native
    assert decision.selected_native_instrument_id == "BTC-USDT-SWAP"


def test_t13_no_authority_escalation() -> None:
    decision = _decide([_perp("ETH-USDT-SWAP")])
    assert SELECTOR_HAS_TRADING_AUTHORITY is False
    assert SELECTOR_HAS_POSITION_SIZING_AUTHORITY is False
    assert SELECTOR_HAS_LEVERAGE_AUTHORITY is False
    assert SELECTOR_HAS_DOUBLE_PLAY_SIDE_AUTHORITY is False
    assert LIVE_AUTHORIZED is False
    assert ORDERS_AUTHORIZED is False
    assert RUNTIME_ACTIVATION_ALLOWED is False
    auth = decision.authority
    assert auth["SELECTOR_HAS_TRADING_AUTHORITY"] is False
    assert auth["SELECTOR_HAS_POSITION_SIZING_AUTHORITY"] is False
    assert auth["SELECTOR_HAS_LEVERAGE_AUTHORITY"] is False
    assert auth["SELECTOR_HAS_DOUBLE_PLAY_SIDE_AUTHORITY"] is False
    bound = adapt_master_v2_selection_to_runtime_binding_v1(
        decision,
        source_payload=_payload([_perp("ETH-USDT-SWAP")]),
        mark_price_payload=_marks("ETH-USDT-SWAP"),
        source_event_time=SOURCE_EVENT,
    )
    assert bound.ok is True
    assert bound.activation_allowed is False
    assert bound.live_authorized is False
    assert bound.orders_authorized is False
    assert bound.ranking_required is False
    assert bound.valid_until_required is False
    none = adapt_master_v2_selection_to_runtime_binding_v1(_decide([]))
    assert none.ok is False
    assert "NO_SELECTION" in none.failure_codes
    rejected = adapt_master_v2_selection_to_runtime_binding_v1(
        decision,
        direct_instrument_override="SOL-USDT-SWAP",
    )
    assert rejected.ok is False


def test_t14_candidate_order_independence() -> None:
    a = _decide([_perp("ETH-USDT-SWAP"), _perp("SOL-USDT-SWAP")])
    b = _decide([_perp("SOL-USDT-SWAP"), _perp("ETH-USDT-SWAP")])
    assert a.decision_status == STATUS_NO_SELECTION
    assert b.decision_status == STATUS_NO_SELECTION
    assert a.decision_reason == REASON_NO_SELECTION_MULTIPLE_ELIGIBLE
    assert a.identity_digest == b.identity_digest
    assert set(a.eligible_native_instrument_ids) == {"ETH-USDT-SWAP", "SOL-USDT-SWAP"}


def test_t15_swap_with_expiry() -> None:
    decision = _decide([_perp("ETH-USDT-SWAP", exp="1743120000000")])
    assert decision.decision_status == STATUS_NO_SELECTION
    assert decision.selected_native_instrument_id is None
    assert decision.decision_reason == REASON_NO_SELECTION_ZERO_ELIGIBLE


def test_package_has_no_asset_exclusion_or_ranking_authority() -> None:
    banned = (
        "FORBIDDEN_BASE_ASSETS",
        "FORBIDDEN_INSTRUMENT_TOKENS",
        "BTC_EXCLUDED",
        "LINEAR_ONLY",
        "SUPPORTED_CT_TYPES",
        "refresh_cadence_seconds",
        "hysteresis",
        "min_holding",
    )
    for path in PACKAGE_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text, f"{path.name} contains banned token {token}"
        assert "from src.ops.productive_futures_ranking_producer_v1" not in text
        assert "from src.ops.governed_futures_universe_producer_v1.eligibility_v1" not in text
        assert "from src.ops.single_selected_future_policy_v1.selection_v1" not in text
