# tests/trading/master_v2/test_double_play_dashboard_display.py
from __future__ import annotations

import ast
import json
from dataclasses import replace
from datetime import datetime
from enum import Enum
from pathlib import Path

from trading.master_v2.double_play_capital_slot import (
    CapitalSlotConfig,
    CapitalSlotState,
    evaluate_capital_slot_ratchet,
    evaluate_capital_slot_release,
)
from trading.master_v2.double_play_composition import (
    DoublePlayCompositionInput,
    RequestedSide,
    compose_double_play_decision,
)
from trading.master_v2.double_play_dashboard_display import (
    DISPLAY_JSON_LAYER_VERSION,
    DOUBLE_PLAY_DASHBOARD_DISPLAY_LAYER_VERSION,
    DashboardDisplayStatus,
    build_dashboard_display_snapshot,
    snapshot_to_jsonable,
)
from trading.master_v2.double_play_futures_input import evaluate_futures_input_snapshot
from trading.master_v2.double_play_state import ScopeEvent, SideState
from trading.master_v2.double_play_suitability import (
    SideCompatibility,
    StrategyMetadata,
)
from trading.master_v2.double_play_survival import (
    SurvivalEnvelopeDecision,
    SurvivalEnvelopeStatus,
)

from tests.trading.master_v2.test_double_play_futures_input import _snapshot as _fi_snapshot
from tests.trading.master_v2.test_double_play_pure_stack_contract import (
    _env_ok,
    _suit_in,
    _suit_allows_from_envelope,
    evaluate_survival_envelope,
    project_strategy_suitability,
)
from trading.master_v2.double_play_state import RuntimeScopeState, transition_state
from trading.master_v2.double_play_state import DynamicScopeRules, RuntimeEnvelope, StaticHardLimits

GOOD = StaticHardLimits(
    max_notional=1.0,
    max_leverage=1.0,
    max_switches_per_window=100,
    min_band_width=1.0,
    max_band_width=100.0,
)
GOOD_ENVELOPE = RuntimeEnvelope(static=GOOD, live_authorization=False)
GOOD_RULES = DynamicScopeRules(
    min_band_width=1.0,
    max_band_width=50.0,
    min_switch_cooldown_ticks=0,
    max_switches_per_window=1_000_000,
    volatility_estimate=0.1,
)
EMPTY_ST = RuntimeScopeState()


def _ts(side: SideState, event: ScopeEvent, st: RuntimeScopeState, now: int = 0):
    return transition_state(
        side_state=side,
        event=event,
        scope_state=st,
        rules=GOOD_RULES,
        envelope=GOOD_ENVELOPE,
        now_tick=now,
    )


def _full_stack_decisions():
    s1, st1, _ = _ts(SideState.NEUTRAL_OBSERVE, ScopeEvent.UPSCOPE_CONFIRMED, EMPTY_ST, 0)
    s2, st2, t2 = _ts(s1, ScopeEvent.UPSCOPE_CONFIRMED, st1, 1)
    surv = evaluate_survival_envelope(_env_ok())
    meta = StrategyMetadata(
        strategy_id="c1",
        strategy_family="m",
        declared_side=SideCompatibility.LONG_BULL,
        explicit_side_evidence=True,
    )
    suit = project_strategy_suitability(_suit_in(meta, _suit_allows_from_envelope(surv)))
    cfg = CapitalSlotConfig(
        profit_step_pct=0.10,
        cashflow_lock_fraction=0.30,
        reinvest_fraction=0.70,
        allow_auto_top_up=False,
        live_authorization=False,
        min_realized_volatility=0.05,
        min_atr_or_range=0.05,
        max_time_without_cashflow_step=10_000,
        min_opportunity_score=0.2,
    )
    cs_st = CapitalSlotState(
        selected_future="BTC-USD-PERP",
        initial_slot_base=300.0,
        active_slot_base=300.0,
        realized_or_settled_slot_equity=340.0,
        unrealized_pnl=0.0,
        locked_cashflow=0.0,
        time_without_cashflow_step=0,
        realized_volatility=0.5,
        atr_or_range=0.5,
        opportunity_score=0.8,
        survival_allows_slot=True,
    )
    rat = evaluate_capital_slot_ratchet(cfg, cs_st)
    rel = evaluate_capital_slot_release(cfg, cs_st)
    comp = compose_double_play_decision(
        DoublePlayCompositionInput(
            transition=t2,
            resulting_side_state=s2,
            survival=surv,
            suitability=suit,
            requested_side=RequestedSide.LONG_BULL,
            capital_slot_ratchet_decision=rat,
            capital_slot_release_decision=rel,
        )
    )
    fi = evaluate_futures_input_snapshot(_fi_snapshot())
    return fi, t2, surv, suit, rat, rel, comp


def test_layer_version_is_v0() -> None:
    assert DOUBLE_PLAY_DASHBOARD_DISPLAY_LAYER_VERSION == "v0"


def test_builds_snapshot_from_all_pure_decisions() -> None:
    fi, t2, surv, suit, rat, rel, comp = _full_stack_decisions()
    snap = build_dashboard_display_snapshot(
        futures_input=fi,
        transition=t2,
        survival=surv,
        suitability=suit,
        capital_slot_ratchet=rat,
        capital_slot_release=rel,
        composition=comp,
    )
    assert len(snap.panels) == 7
    names = [p.name for p in snap.panels]
    assert names == [
        "futures_input",
        "state_transition",
        "survival_envelope",
        "strategy_suitability",
        "capital_slot_ratchet",
        "capital_slot_release",
        "composition",
    ]
    assert snap.overall_status is DashboardDisplayStatus.DISPLAY_READY
    assert snap.no_live_banner_visible
    assert snap.display_only
    assert not snap.trading_ready
    assert not snap.testnet_ready
    assert not snap.live_ready
    assert not snap.live_authorization
    comp_panel = snap.panels[-1]
    assert "ELIGIBLE_MODEL_ONLY" in comp_panel.summary
    assert (
        "not trading" in comp_panel.summary.lower() or "trading-ready" in comp_panel.summary.lower()
    )


def test_missing_optional_panel_is_warning_level() -> None:
    fi, t2, surv, suit, rat, rel, comp = _full_stack_decisions()
    snap = build_dashboard_display_snapshot(
        futures_input=fi,
        transition=t2,
        survival=surv,
        suitability=suit,
        capital_slot_ratchet=rat,
        capital_slot_release=rel,
        composition=None,
    )
    assert snap.panels[-1].status is DashboardDisplayStatus.DISPLAY_MISSING
    assert snap.overall_status is DashboardDisplayStatus.DISPLAY_WARNING


def test_blocked_survival_maps_to_blocked_panel() -> None:
    fi, t2, _, suit, rat, rel, comp = _full_stack_decisions()
    bad_surv = SurvivalEnvelopeDecision(
        status=SurvivalEnvelopeStatus.BLOCKED,
        pre_authorization_eligible=False,
        block_reasons=(),
    )
    snap = build_dashboard_display_snapshot(
        futures_input=fi,
        transition=t2,
        survival=bad_surv,
        suitability=suit,
        capital_slot_ratchet=rat,
        capital_slot_release=rel,
        composition=comp,
    )
    p = snap.panels[2]
    assert p.name == "survival_envelope"
    assert p.status is DashboardDisplayStatus.DISPLAY_BLOCKED
    assert snap.overall_status is DashboardDisplayStatus.DISPLAY_BLOCKED


def test_eligible_composition_not_trading_ready_on_snapshot() -> None:
    _, _, _, _, _, _, comp = _full_stack_decisions()
    snap = build_dashboard_display_snapshot(composition=comp)
    assert snap.panels[-1].status is DashboardDisplayStatus.DISPLAY_READY
    assert not snap.trading_ready
    assert snap.display_only


def test_no_live_banner_always_visible() -> None:
    snap = build_dashboard_display_snapshot()
    assert snap.no_live_banner_visible


def test_live_authorization_false_despite_malformed_projection_flag() -> None:
    _, _, _, suit, _, _, _ = _full_stack_decisions()
    bad_proj = replace(suit.projection, live_authorization=True)
    bad_suit = replace(suit, projection=bad_proj)
    snap = build_dashboard_display_snapshot(suitability=bad_suit)
    assert not snap.live_authorization
    p = snap.panels[3]
    assert p.status is DashboardDisplayStatus.DISPLAY_ERROR
    assert any("suitability.projection" in w for w in snap.warnings)


def test_dto_values_are_display_safe_no_callables() -> None:
    fi, t2, surv, suit, rat, rel, comp = _full_stack_decisions()
    snap = build_dashboard_display_snapshot(
        futures_input=fi,
        transition=t2,
        survival=surv,
        suitability=suit,
        capital_slot_ratchet=rat,
        capital_slot_release=rel,
        composition=comp,
    )
    assert _is_display_safe(snap)


def _is_display_safe(obj: object, *, depth: int = 0) -> bool:
    if depth > 12:
        return False
    if obj is None:
        return True
    if isinstance(obj, (str, int, float, bool)):
        return True
    if callable(obj):
        return False
    if isinstance(obj, tuple):
        return all(_is_display_safe(x, depth=depth + 1) for x in obj)
    if isinstance(obj, Enum):
        return True
    if hasattr(obj, "__dataclass_fields__"):
        for name in obj.__dataclass_fields__:
            if not _is_display_safe(getattr(obj, name), depth=depth + 1):
                return False
        return True
    return False


def test_no_forbidden_imports_in_module() -> None:
    root = Path(__file__).resolve().parent.parent.parent.parent / "src" / "trading" / "master_v2"
    path = root / "double_play_dashboard_display.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bad = {"fastapi", "uvicorn", "requests", "urllib3", "ccxt", "httpx", "aiohttp", "socket"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                assert n.name.split(".")[0].lower() not in bad
        if isinstance(node, ast.ImportFrom) and node.module:
            mod0 = node.module.split(".")[0].lower()
            assert mod0 not in bad
            if mod0 == "trading":
                assert node.module.startswith("trading.master_v2")


def test_module_has_no_fastapi_strings() -> None:
    path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "trading"
        / "master_v2"
        / "double_play_dashboard_display.py"
    )
    text = path.read_text(encoding="utf-8").lower()
    assert "fastapi" not in text
    assert "apirouter" not in text


def test_snapshot_invariants_always() -> None:
    snap = build_dashboard_display_snapshot()
    assert snap.display_only
    assert not snap.trading_ready
    assert not snap.testnet_ready
    assert not snap.live_ready
    assert not snap.live_authorization
    assert snap.no_live_banner_visible


# --- snapshot_to_jsonable (canonical mapper in trading.master_v2; aligned with WebUI route) ---
# Keep key surfaces aligned with tests/webui/test_double_play_dashboard_display_json_route.py

_EXPECTED_JSON_TOP_LEVEL_KEYS = frozenset(
    {
        "display_layer_version",
        "display_snapshot_meta",
        "panels",
        "overall_status",
        "no_live_banner_visible",
        "display_only",
        "trading_ready",
        "testnet_ready",
        "live_ready",
        "live_authorization",
        "warnings",
    }
)

_EXPECTED_JSON_DISPLAY_SNAPSHOT_META_KEYS = frozenset(
    {"source_kind", "source_id", "assembled_at_iso"}
)

_EXPECTED_JSON_PANEL_KEYS = frozenset(
    {
        "name",
        "status",
        "summary",
        "blockers",
        "missing_inputs",
        "live_authorization",
        "is_authority",
        "is_signal",
        "ordinal",
        "panel_group",
        "severity_rank",
    }
)

# Dict keys anywhere in the serialized tree must not include these (control / runtime / secrets).
# `live_authorization` is an explicit safety flag: forbid as *unexpected* key elsewhere only via
# disjoint check — it is allowed on top-level and panels and must be false (asserted separately).
_FORBIDDEN_JSON_KEYS = frozenset(
    {
        "start",
        "stop",
        "arm",
        "enable",
        "allocate",
        "release",
        "trade",
        "fetch",
        "scan",
        "select",
        "promote",
        "approve",
        "sign_off",
        "live",
        "order",
        "orders",
        "execute",
        "execution",
        "action",
        "action_url",
        "control",
        "control_url",
        "live_enable",
        "live_enabled",
        "live_armed",
        "confirm_token",
        "api_key",
        "secret",
        "exchange",
        "provider",
        "scanner",
        "runtime_handle",
        "producer",
        "session_id",
        "testnet_authorization",
    }
)


def _collect_object_keys(obj: object, out: set[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                out.add(k)
            _collect_object_keys(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_object_keys(item, out)


def _assert_json_native_values(obj: object) -> None:
    """Reject handles / callables / opaque objects in the serialized tree."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return
    if isinstance(obj, list):
        for x in obj:
            _assert_json_native_values(x)
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert isinstance(k, str)
            _assert_json_native_values(v)
        return
    raise AssertionError(f"non-JSON-native value remains after snapshot_to_jsonable: {type(obj)!r}")


def _assert_serialized_dashboard_authority_invariants(data: dict) -> None:
    assert set(data.keys()) == _EXPECTED_JSON_TOP_LEVEL_KEYS
    assert data["display_layer_version"] == DISPLAY_JSON_LAYER_VERSION
    meta = data["display_snapshot_meta"]
    assert set(meta.keys()) == _EXPECTED_JSON_DISPLAY_SNAPSHOT_META_KEYS
    assert isinstance(meta["assembled_at_iso"], str)
    datetime.fromisoformat(meta["assembled_at_iso"].replace("Z", "+00:00"))
    assert meta["source_kind"] == "static_display_v0"
    assert meta["source_id"] == "webui_dashboard_display_static_v0"
    assert data["display_only"] is True
    assert data["no_live_banner_visible"] is True
    assert data["trading_ready"] is False
    assert data["testnet_ready"] is False
    assert data["live_ready"] is False
    assert data["live_authorization"] is False

    assert isinstance(data["panels"], list)
    for panel in data["panels"]:
        assert isinstance(panel, dict)
        assert set(panel.keys()) == _EXPECTED_JSON_PANEL_KEYS
        assert panel["live_authorization"] is False
        assert panel["is_authority"] is False
        assert panel["is_signal"] is False

    keys: set[str] = set()
    _collect_object_keys(data, keys)
    assert keys.isdisjoint(_FORBIDDEN_JSON_KEYS)

    _assert_json_native_values(data)
    json.dumps(data)


def test_display_json_layer_version_and_metadata_contract_v0() -> None:
    """Structured display JSON metadata aligns with ``DISPLAY_JSON_LAYER_VERSION`` (non-authority).

    Locks core constants vs ``snapshot_to_jsonable`` output without asserting ``assembled_at_iso`` value.
    """
    assert DISPLAY_JSON_LAYER_VERSION == "v2"
    payload = snapshot_to_jsonable(build_dashboard_display_snapshot())
    assert payload["display_layer_version"] == DISPLAY_JSON_LAYER_VERSION
    meta = payload["display_snapshot_meta"]
    assert set(meta.keys()) == _EXPECTED_JSON_DISPLAY_SNAPSHOT_META_KEYS
    assert meta["source_kind"] == "static_display_v0"
    assert meta["source_id"] == "webui_dashboard_display_static_v0"
    assert isinstance(meta["assembled_at_iso"], str)
    assert meta["assembled_at_iso"].strip() != ""


def test_snapshot_to_jsonable_full_stack_matches_route_contract() -> None:
    fi, t2, surv, suit, rat, rel, comp = _full_stack_decisions()
    snap = build_dashboard_display_snapshot(
        futures_input=fi,
        transition=t2,
        survival=surv,
        suitability=suit,
        capital_slot_ratchet=rat,
        capital_slot_release=rel,
        composition=comp,
    )
    data = snapshot_to_jsonable(snap)
    _assert_serialized_dashboard_authority_invariants(data)
    assert len(data["panels"]) == 7
    expected_rows = (
        ("futures_input", "input", 0, 0),
        ("state_transition", "state", 1, 0),
        ("survival_envelope", "scope", 2, 0),
        ("strategy_suitability", "strategy", 3, 0),
        ("capital_slot_ratchet", "capital", 4, 0),
        ("capital_slot_release", "capital", 5, 0),
        ("composition", "composition", 6, 0),
    )
    for row, panel in zip(expected_rows, data["panels"]):
        name, grp, ordinal, rank = row
        assert panel["name"] == name
        assert panel["panel_group"] == grp
        assert panel["ordinal"] == ordinal
        assert panel["severity_rank"] == rank


def test_snapshot_to_jsonable_blocked_survival_still_matches_contract() -> None:
    fi, t2, _, suit, rat, rel, comp = _full_stack_decisions()
    bad_surv = SurvivalEnvelopeDecision(
        status=SurvivalEnvelopeStatus.BLOCKED,
        pre_authorization_eligible=False,
        block_reasons=(),
    )
    snap = build_dashboard_display_snapshot(
        futures_input=fi,
        transition=t2,
        survival=bad_surv,
        suitability=suit,
        capital_slot_ratchet=rat,
        capital_slot_release=rel,
        composition=comp,
    )
    data = snapshot_to_jsonable(snap)
    _assert_serialized_dashboard_authority_invariants(data)
    survival_p = next(p for p in data["panels"] if p["name"] == "survival_envelope")
    assert survival_p["status"] == "display_blocked"
    assert survival_p["severity_rank"] == 30


def test_snapshot_to_jsonable_empty_snapshot_still_matches_contract() -> None:
    snap = build_dashboard_display_snapshot()
    data = snapshot_to_jsonable(snap)
    _assert_serialized_dashboard_authority_invariants(data)
    assert data["overall_status"] == "display_warning"
    for i, p in enumerate(data["panels"]):
        assert p["status"] == "display_missing"
        assert p["severity_rank"] == 20
        assert p["ordinal"] == i
