"""Offline Core→Live composition root: unit, isolation, and negative gates."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from src.governance.capital_risk_sizing_v1 import CapitalRiskSizingOutcome
from src.ops.full_core_live_path_composition_root_v1.canary_isolation_v1 import (
    refuse_canary_plan_as_full_core_e2e_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_DEFAULT_INSTRUMENT_ID,
    CANARY_DEFAULT_SIDE,
    CURRENT_LIVE_CORE_PATH_PROVEN,
    FULL_CORE_RESTART_TEST_AUTHORIZED,
    FULL_CORE_SYSTEM_E2E_PROVEN,
    LIVE_ARMED,
    LIVE_ENABLED,
    MODE_TEST,
    PATH_KIND,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import (
    FrozenPretradeEvidenceV1,
    FullCoreLivePathInputV1,
)
from src.ops.full_core_live_path_composition_root_v1.overclaim_guards_v1 import (
    prove_package_does_not_import_wire_surfaces_v1,
    restart_gate_v1,
)
from src.ops.full_core_live_path_composition_root_v1.path_v1 import (
    run_full_core_live_path_offline_v1,
)
from src.ops.full_core_live_path_composition_root_v1.venue_translation_v1 import (
    translate_core_live_intent_to_venue_plan_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_SIDE,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
    _patch_replay_owners,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _INSTRUMENT,
    _replay_input,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_LIVE_PATH_COMPOSITION_ROOT_V1.md"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"


def _binding(*, instrument_id: str = _INSTRUMENT, selection_id: str = "sel-1") -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id=instrument_id,
        venue_native_id=instrument_id,
        ranking_snapshot_id="rank-1",
        ranking_integrity_digest="rank-digest",
        universe_snapshot_id="uni-1",
        selection_id=selection_id,
        selection_integrity_digest="sel-digest",
        selection_state="SELECTED",
    )


def _pretrade(
    *, max_available: str = "10", max_size: str = "10", **kwargs
) -> FrozenPretradeEvidenceV1:
    payload = {
        "max_available": Decimal(max_available),
        "max_size": Decimal(max_size),
        "available_margin_ok": True,
        "price_band_ok": True,
        "instrument_state_ok": True,
        "account_mode_ok": True,
        "pos_mode_ok": True,
        "margin_mode_ok": True,
        "leverage_ok": True,
    }
    payload.update(kwargs)
    return FrozenPretradeEvidenceV1(**payload)


def _run(monkeypatch, replay_input, **kwargs):
    _patch_replay_owners(
        monkeypatch, force_safety_hard_block=kwargs.pop("force_safety_hard_block", False)
    )
    replay = run_integrated_offline_trading_logic_replay_v1(replay_input)
    payload = FullCoreLivePathInputV1(
        replay=replay,
        bound_instrument=kwargs.pop("bound", _binding()),
        frozen_pretrade=kwargs.pop("frozen", _pretrade()),
        mode=kwargs.pop("mode", MODE_TEST),
        composed_epoch=kwargs.pop("composed_epoch", "1"),
        seen_semantic_digests=kwargs.pop("seen_semantic_digests", frozenset()),
        expected_trading_epoch=kwargs.pop("expected_trading_epoch", None),
        owner_go=kwargs.pop("owner_go", "OWNER_GO_FULL_CORE_LIVE_PATH_OFFLINE_V1"),
    )
    return run_full_core_live_path_offline_v1(payload, **kwargs), replay


def _path_from_replay(replay, **kwargs):
    payload = FullCoreLivePathInputV1(
        replay=replay,
        bound_instrument=kwargs.pop("bound", _binding()),
        frozen_pretrade=kwargs.pop("frozen", _pretrade()),
        mode=kwargs.pop("mode", MODE_TEST),
        composed_epoch=kwargs.pop("composed_epoch", "1"),
        seen_semantic_digests=kwargs.pop("seen_semantic_digests", frozenset()),
        expected_trading_epoch=kwargs.pop("expected_trading_epoch", None),
        owner_go=kwargs.pop("owner_go", "OWNER_GO_FULL_CORE_LIVE_PATH_OFFLINE_V1"),
    )
    return run_full_core_live_path_offline_v1(payload, **kwargs)


def test_standing_gates_remain_false() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert CURRENT_LIVE_CORE_PATH_PROVEN is False
    assert FULL_CORE_SYSTEM_E2E_PROVEN is False
    assert FULL_CORE_RESTART_TEST_AUTHORIZED is False


def test_package_does_not_import_canary_http_or_live_port_send() -> None:
    proof = prove_package_does_not_import_wire_surfaces_v1()
    assert proof["ok"] is True
    assert proof["WIRE_SEND_OCCURRED"] is False
    blob = "".join(
        p.read_text(encoding="utf-8")
        for p in PACKAGE_DIR.glob("*.py")
        if p.name not in {"constants_v1.py", "overclaim_guards_v1.py"}
    )
    assert "LiveCanaryHttpClientV1" not in blob
    assert "post_entry_order" not in blob
    assert "build_minimum_valid_canary_order_plan_v1" not in blob


def test_canary_plan_cannot_satisfy_full_core_e2e() -> None:
    verdict = refuse_canary_plan_as_full_core_e2e_v1(
        {
            "instrument_id": DEFAULT_INSTRUMENT_ID,
            "side": DEFAULT_SIDE,
            "quantity_source": "minSz",
        },
        quantity_source="minSz",
    )
    assert verdict["admissible_as_full_core_e2e"] is False
    assert verdict["CANARY_PATH_DISTINCT_FROM_FULL_CORE_LIVE_PATH"] is True
    assert DEFAULT_INSTRUMENT_ID == CANARY_DEFAULT_INSTRUMENT_ID
    assert DEFAULT_SIDE == CANARY_DEFAULT_SIDE


def test_restart_gate_stays_false_even_if_offline_chain_passes() -> None:
    assert restart_gate_v1(full_core_live_path_bound=True, offline_full_chain_proven=True) is False


def test_no_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        bound=_binding(selection_id=""),
    )
    assert result.status.value == "DENY"
    assert "NO_SELECTION" in result.reason_codes
    assert result.wire_send_occurred is False


def test_binding_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        bound=_binding(instrument_id=CANARY_DEFAULT_INSTRUMENT_ID),
    )
    assert "BINDING_MISMATCH" in result.reason_codes
    assert result.wire_send_occurred is False


def test_hardcoded_instrument_injection(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        injected_instrument_id=CANARY_DEFAULT_INSTRUMENT_ID,
    )
    assert "HARDCODED_INSTRUMENT_INJECTION_FORBIDDEN" in result.reason_codes


def test_hardcoded_side_injection(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        injected_side=CANARY_DEFAULT_SIDE,
    )
    assert "HARDCODED_SIDE_INJECTION_FORBIDDEN" in result.reason_codes


def test_hold(monkeypatch: pytest.MonkeyPatch) -> None:
    result, replay = _run(monkeypatch, _replay_input())
    assert replay.evidence.decision_outcome in {
        DecisionOutcome.HOLD.value,
        DecisionOutcome.NO_ACTION.value,
        DecisionOutcome.OBSERVE.value,
        DecisionOutcome.RECONCILE_ONLY.value,
    }
    assert "HOLD" in result.reason_codes
    assert result.wire_send_occurred is False


def test_missing_double_play_result(monkeypatch: pytest.MonkeyPatch) -> None:
    _, replay = _run(monkeypatch, _confirmed_replay_input(side="LONG"))
    mutated = replace(
        replay,
        intermediate=replace(
            replay.intermediate,
            composition_result=None,
            entry_exit_decision=None,
        ),
    )
    denied = _path_from_replay(mutated)
    assert "MISSING_DOUBLE_PLAY_RESULT" in denied.reason_codes
    assert denied.wire_send_occurred is False


def test_blocked_enter(monkeypatch: pytest.MonkeyPatch) -> None:
    _, replay = _run(monkeypatch, _confirmed_replay_input(side="LONG"))
    blocked = replace(
        replay,
        evidence=replace(replay.evidence, decision_outcome=DecisionOutcome.BLOCKED.value),
    )
    result = _path_from_replay(blocked)
    assert "BLOCKED_ENTER" in result.reason_codes
    assert result.wire_send_occurred is False


def test_missing_29p(monkeypatch: pytest.MonkeyPatch) -> None:
    _, replay = _run(monkeypatch, _confirmed_replay_input(side="LONG"))
    mutated = replace(
        replay,
        intermediate=replace(replay.intermediate, capital_risk_sizing_decision=None),
    )
    result = _path_from_replay(mutated)
    assert "MISSING_29P" in result.reason_codes


def test_29p_deny(monkeypatch: pytest.MonkeyPatch) -> None:
    _, replay = _run(monkeypatch, _confirmed_replay_input(side="LONG"))
    sizing = replay.intermediate.capital_risk_sizing_decision
    mutated = replace(
        replay,
        intermediate=replace(
            replay.intermediate,
            capital_risk_sizing_decision=replace(sizing, outcome=CapitalRiskSizingOutcome.BLOCKED),
        ),
    )
    result = _path_from_replay(mutated)
    assert "29P_DENY" in result.reason_codes


def test_missing_29q(monkeypatch: pytest.MonkeyPatch) -> None:
    _, replay = _run(monkeypatch, _confirmed_replay_input(side="LONG"))
    mutated = replace(
        replay,
        intermediate=replace(replay.intermediate, canonical_order_intent=None),
    )
    result = _path_from_replay(mutated)
    assert "MISSING_29Q" in result.reason_codes or "REPLAY_SAFETY_DENY" in result.reason_codes


def test_zero_qty(monkeypatch: pytest.MonkeyPatch) -> None:
    _, replay = _run(monkeypatch, _confirmed_replay_input(side="LONG"))
    intent = replace(replay.intermediate.canonical_order_intent, quantity=Decimal("0"))
    mutated = replace(
        replay,
        intermediate=replace(replay.intermediate, canonical_order_intent=intent),
    )
    result = _path_from_replay(mutated)
    assert "ZERO_QTY" in result.reason_codes


def test_invalid_sizing(monkeypatch: pytest.MonkeyPatch) -> None:
    _, replay = _run(monkeypatch, _confirmed_replay_input(side="LONG"))
    intent = replace(replay.intermediate.canonical_order_intent, quantity_provenance="")
    mutated = replace(
        replay,
        intermediate=replace(replay.intermediate, canonical_order_intent=intent),
    )
    result = _path_from_replay(mutated)
    assert "INVALID_SIZING" in result.reason_codes


def test_wrong_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    _, replay = _run(monkeypatch, _confirmed_replay_input(side="LONG"))
    intent = replace(replay.intermediate.canonical_order_intent, semantic_digest="")
    mutated = replace(
        replay,
        intermediate=replace(replay.intermediate, canonical_order_intent=intent),
    )
    result = _path_from_replay(mutated)
    assert "WRONG_IDENTITY" in result.reason_codes


def test_replay_safety_deny(monkeypatch: pytest.MonkeyPatch) -> None:
    result, replay = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        force_safety_hard_block=True,
    )
    assert replay.intermediate.canonical_order_intent is None
    assert "REPLAY_SAFETY_DENY" in result.reason_codes or "MISSING_29Q" in result.reason_codes


def test_duplicate_intent(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_replay_owners(monkeypatch)
    replay = run_integrated_offline_trading_logic_replay_v1(_confirmed_replay_input(side="LONG"))
    digest = replay.intermediate.canonical_order_intent.semantic_digest
    dup = _path_from_replay(replay, seen_semantic_digests=frozenset({digest}))
    assert "DUPLICATE_INTENT" in dup.reason_codes
    assert dup.wire_send_occurred is False


def test_stale_intent(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        expected_trading_epoch="9999",
    )
    assert "STALE_CANONICAL_ORDER_INTENT" in result.reason_codes


def test_pretrade_max_available_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        frozen=_pretrade(max_available="0"),
    )
    assert "MAX_AVAILABLE_ZERO" in result.reason_codes
    assert result.wire_send_occurred is False


def test_pretrade_max_size_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        frozen=_pretrade(max_size="0"),
    )
    assert "MAX_SIZE_ZERO" in result.reason_codes
    assert result.wire_send_occurred is False


def test_price_band_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        frozen=_pretrade(price_band_ok=False),
    )
    assert "PRICE_BAND_FAIL" in result.reason_codes


def test_unavailable_margin(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        frozen=_pretrade(available_margin_ok=False),
    )
    assert "UNAVAILABLE_MARGIN" in result.reason_codes


def test_venue_translation_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    result, replay = _run(monkeypatch, _confirmed_replay_input(side="LONG"))
    assert result.intent is not None

    def _mismatch(**kwargs):
        body = {
            "instId": "WRONG-INSTRUMENT",
            "side": kwargs.get("side"),
            "sz": kwargs.get("quantity"),
            "ordType": kwargs.get("order_type"),
            "tdMode": kwargs.get("td_mode"),
        }
        return body

    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1.venue_translation_v1.build_venue_native_order_body_v1",
        _mismatch,
    )
    status, reasons, plan = translate_core_live_intent_to_venue_plan_v1(
        result.intent,
        session_id="offline-full-core",
        run_id="offline-full-core-run",
    )
    assert plan is None
    assert any(code.startswith("VENUE_TRANSLATION_MISMATCH") for code in reasons)
    assert status.value == "DENY"


def test_execution_disabled_and_unarmed_on_halt(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _ = _run(monkeypatch, _confirmed_replay_input(side="LONG"))
    assert result.boundary is not None
    assert "EXECUTION_DISABLED" in result.reason_codes
    assert "EXECUTION_UNARMED" in result.reason_codes
    assert "WIRE_SEND_NOT_PERMITTED" in result.reason_codes
    assert result.wire_send_occurred is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False


def test_missing_owner_go_halts_before_wire(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        owner_go=None,
    )
    assert result.boundary is not None
    assert result.wire_send_occurred is False
    assert "MISSING_OWNER_GO" in result.reason_codes or "MISSING_OWNER_GO" in (
        result.pretrade.reason_codes if result.pretrade else ()
    )


def test_attempted_wire_send_still_false(monkeypatch: pytest.MonkeyPatch) -> None:
    result, _ = _run(
        monkeypatch,
        _confirmed_replay_input(side="LONG"),
        attempt_wire_send=True,
        attempt_construct_live_port=True,
    )
    assert result.wire_send_occurred is False
    assert result.boundary is not None
    assert result.boundary.wire_send_occurred is False
    assert result.boundary.live_execution_port_constructed is False
    assert result.boundary.canary_http_invoked is False
    assert "WIRE_SEND_FORBIDDEN_IN_OFFLINE_FULL_CORE_PATH" in result.reason_codes
    assert "LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN" in result.reason_codes
    assert "EXECUTION_DISABLED" in result.reason_codes
    assert "EXECUTION_UNARMED" in result.reason_codes


def test_spec_and_runbook_isolation_language() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert "CANARY_VENUE_PROOF_PATH != FULL_CORE_LIVE_PATH" in spec
    assert "HARD STOP BEFORE WIRE" in spec
    assert "FULL_CORE_LIVE_PATH_COMPOSITION_ROOT" in runbook
    assert PATH_KIND in spec
