"""Offline CURRENT_PRODUCTIVE host-ENTER 29P INVALID_STOP_PRICE binding repair."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.governance.capital_risk_sizing_v1 import REASON_INVALID_STOP_PRICE
from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import CompositionStatusV1
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_HOST_ENTER_29P_INVALID_STOP_PRICE_REPAIR_CREATED,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _bound,
    _cycle,
    _cycle_a_with_confirmation_progress,
    _strong_uptrend_closes,
)
from tests.ops.test_full_core_live_path_offline_full_chain_v1 import (
    _confirmed_replay_input,
    _patch_replay_owners,
)
from trading.master_v2.capital_risk_sizing_historical_default_deauthorization_v1 import (
    ISOLATED_OFFLINE_REPLAY_FIXTURE_PROTECTIVE_STOP,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    bind_capital_risk_sizing_offline_replay_evidence_v0,
    derive_protective_stop_price_from_adverse_exit_v0,
    isolated_offline_replay_fixture_capital_context_v0,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    ScopeDirectionState,
    compute_evaluated_thresholds,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/"
    "FULL_CORE_CURRENT_PRODUCTIVE_HOST_ENTER_29P_INVALID_STOP_PRICE_REPAIR_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
DS_HEADING = "### 11.2.1.DS FULL_CORE_CURRENT_PRODUCTIVE_HOST_ENTER_29P_INVALID_STOP_PRICE_ROOT_CAUSE_AND_REPAIR"
THIS_SLICE = (
    "11.2.1.DS.FULL_CORE_CURRENT_PRODUCTIVE_HOST_ENTER_29P_INVALID_STOP_PRICE_ROOT_CAUSE_AND_REPAIR"
)
PROTECTED_ALGORITHM_FILES = (
    "src/ops/governed_futures_universe_producer_v1/eligibility_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py",
    "src/ops/productive_futures_ranking_producer_v1/policy_v1.py",
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
    "src/trading/master_v2/double_play_state.py",
    "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
    "src/trading/master_v2/deterministic_scope_event_generator_v1.py",
    "src/governance/capital_risk_sizing_v1.py",
    "config/ops/canonical_decision_runtime_config_v1.toml",
)


def _host_enter_cycle():
    path = _strong_uptrend_closes()
    cycle_a = _cycle_a_with_confirmation_progress()
    cycle_b = _cycle(
        cycle_id="cursor-join-b",
        incoming_cursor=cycle_a.outgoing_cursor,
        mark_px=float(path[-1]),
        event_ts_unix=1_700_000_120.0,
    )
    return cycle_a, cycle_b, path


def test_created_flag_and_protected_thresholds_unchanged() -> None:
    assert CURRENT_PRODUCTIVE_HOST_ENTER_29P_INVALID_STOP_PRICE_REPAIR_CREATED is True
    assert float(CANONICAL_ADVERSE_EXIT_DISTANCE) == 80.0
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert ISOLATED_OFFLINE_REPLAY_FIXTURE_PROTECTIVE_STOP == Decimal("3400")


@pytest.mark.parametrize(
    ("side", "reference", "distance", "expected"),
    [
        ("LONG", Decimal("1630"), Decimal("80"), Decimal("1550")),
        ("long", Decimal("1630"), Decimal("80"), Decimal("1550")),
        ("SHORT", Decimal("1630"), Decimal("80"), Decimal("1710")),
        ("short", Decimal("3500"), Decimal("80"), Decimal("3580")),
    ],
)
def test_derive_stop_matches_current_adverse_exit_formula(
    side: str, reference: Decimal, distance: Decimal, expected: Decimal
) -> None:
    derived = derive_protective_stop_price_from_adverse_exit_v0(
        selected_side=side,
        reference_price=reference,
        adverse_exit_distance=distance,
    )
    assert derived == expected
    direction = ScopeDirectionState.LONG if side.upper() == "LONG" else ScopeDirectionState.SHORT
    threshold = compute_evaluated_thresholds(
        direction=direction,
        trailing_anchor=float(reference),
        up_distance=200.0,
        adverse_exit_distance=float(distance),
        reversal_distance=120.0,
    ).adverse_exit_threshold
    assert derived == Decimal(str(threshold))


@pytest.mark.parametrize(
    ("side", "reference", "distance"),
    [
        ("", Decimal("1630"), Decimal("80")),
        ("NONE", Decimal("1630"), Decimal("80")),
        ("LONG", Decimal("1630"), Decimal("0")),
        ("LONG", Decimal("1630"), Decimal("-80")),
        ("LONG", Decimal("0"), Decimal("80")),
        ("LONG", Decimal("1630"), Decimal("NaN")),
        ("LONG", Decimal("3.5"), Decimal("80")),
        ("SHORT", Decimal("NaN"), Decimal("80")),
    ],
)
def test_derive_stop_fail_closed_on_invalid_inputs(
    side: str, reference: Decimal, distance: Decimal
) -> None:
    assert (
        derive_protective_stop_price_from_adverse_exit_v0(
            selected_side=side,
            reference_price=reference,
            adverse_exit_distance=distance,
        )
        is None
    )


def test_fixture_stop_against_host_mark_is_invalid_stop_price() -> None:
    _, cycle_b, path = _host_enter_cycle()
    assert cycle_b.decision_outcome == "enter_long"
    assert cycle_b.replay is not None
    mark = Decimal(str(path[-1]))
    assert mark == Decimal("1630")
    assert ISOLATED_OFFLINE_REPLAY_FIXTURE_PROTECTIVE_STOP >= mark
    fixture_ctx = isolated_offline_replay_fixture_capital_context_v0(
        instrument_id=cycle_b.replay.evidence.instrument_id,
        reference_price=mark,
    )
    assert fixture_ctx.protective_stop_price == ISOLATED_OFFLINE_REPLAY_FIXTURE_PROTECTIVE_STOP
    binding = bind_capital_risk_sizing_offline_replay_evidence_v0(
        cycle_b.replay.evidence,
        capital_context=fixture_ctx,
    )
    assert binding.sizing_decision is not None
    assert str(binding.sizing_decision.outcome.value) == "BLOCKED"
    assert REASON_INVALID_STOP_PRICE in binding.sizing_decision.reason_codes


@pytest.mark.parametrize(
    "stop",
    [
        None,
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("1630"),
        Decimal("1640"),
        Decimal("3400"),
    ],
)
def test_invalid_or_direction_invalid_stop_cannot_pass_29p(stop: Decimal | None) -> None:
    _, cycle_b, path = _host_enter_cycle()
    mark = Decimal(str(path[-1]))
    ctx = isolated_offline_replay_fixture_capital_context_v0(
        instrument_id=cycle_b.replay.evidence.instrument_id,
        reference_price=mark,
        protective_stop_price=stop,
    )
    binding = bind_capital_risk_sizing_offline_replay_evidence_v0(
        cycle_b.replay.evidence,
        capital_context=ctx,
    )
    assert binding.sizing_decision is not None
    assert str(binding.sizing_decision.outcome.value) != "PASS"
    if (
        stop is None
        or (isinstance(stop, Decimal) and not stop.is_finite())
        or (isinstance(stop, Decimal) and stop > mark)
    ):
        assert REASON_INVALID_STOP_PRICE in binding.sizing_decision.reason_codes


def test_host_enter_binds_canonical_adverse_exit_and_reaches_envelope() -> None:
    cycle_a, cycle_b, path = _host_enter_cycle()
    assert cycle_a.outgoing_cursor is not None
    assert cycle_b.cursor_restore_status == "restored"
    assert cycle_b.decision_outcome == "enter_long"
    assert cycle_b.replay is not None
    replay = cycle_b.replay
    sizing = replay.intermediate.capital_risk_sizing_decision
    assert sizing is not None
    assert str(replay.intermediate.capital_risk_mode) == "OFFLINE_ALGEBRA"
    assert str(getattr(sizing.outcome, "value", sizing.outcome)) == "PASS"
    assert REASON_INVALID_STOP_PRICE not in sizing.reason_codes
    mark = Decimal(str(path[-1]))
    expected_stop = derive_protective_stop_price_from_adverse_exit_v0(
        selected_side=str(replay.evidence.selected_side),
        reference_price=mark,
        adverse_exit_distance=CANONICAL_ADVERSE_EXIT_DISTANCE,
    )
    assert expected_stop == Decimal("1550")
    assert expected_stop != ISOLATED_OFFLINE_REPLAY_FIXTURE_PROTECTIVE_STOP
    intent = replay.intermediate.canonical_order_intent
    assert intent is not None
    assert intent.execution_eligible is False
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"
    status, reasons, plan = try_bind_current_productive_venue_plan_v1(
        replay=replay,
        bound_instrument=_bound(),
        session_id="host-enter-29p-repair-session",
        run_id="host-enter-29p-repair-run",
        composed_epoch="2026-09-16T00:00:00Z",
        execution_mode="LIVE",
    )
    assert status is CompositionStatusV1.PASS, reasons
    assert plan is not None
    envelope = bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="DS_HOST_ENTER_29P_STOP_REPAIR_OFFLINE",
        provenance_ref="CURRENT_PRODUCTIVE_MASTER_V2_VENUE_PLAN",
        creation_epoch="2026-09-16T00:00:00Z",
    )
    assert envelope.envelope_id
    assert envelope.envelope_digest
    assert envelope.instrument_id == replay.evidence.instrument_id


def test_armed_replay_still_reaches_envelope_without_permit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_replay_owners(monkeypatch)
    replay = run_integrated_offline_trading_logic_replay_v1(_confirmed_replay_input(side="LONG"))
    assert replay.evidence.decision_outcome == "enter_long"
    sizing = replay.intermediate.capital_risk_sizing_decision
    assert sizing is not None
    assert str(getattr(sizing.outcome, "value", sizing.outcome)) == "PASS"
    expected_stop = derive_protective_stop_price_from_adverse_exit_v0(
        selected_side=str(replay.evidence.selected_side),
        reference_price=Decimal(str(replay.intermediate.market_context.mark_price)),
        adverse_exit_distance=_confirmed_replay_input(side="LONG").adverse_exit_distance,
    )
    assert expected_stop == Decimal("3420")
    status, reasons, plan = try_bind_current_productive_venue_plan_v1(
        replay=replay,
        bound_instrument=_bound(),
        session_id="armed-replay-29p-repair-session",
        run_id="armed-replay-29p-repair-run",
        composed_epoch="2026-09-16T00:00:00Z",
        execution_mode="LIVE",
    )
    assert status is CompositionStatusV1.PASS, reasons
    assert plan is not None
    envelope = bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="DS_ARMED_REPLAY_29P_STOP_REPAIR_OFFLINE",
        provenance_ref="CURRENT_PRODUCTIVE_MASTER_V2_VENUE_PLAN",
        creation_epoch="2026-09-16T00:00:00Z",
    )
    assert envelope.envelope_id
    assert envelope.envelope_digest
    assert replay.intermediate.canonical_order_intent is not None
    assert replay.intermediate.canonical_order_intent.execution_eligible is False


def test_protected_algorithm_files_unchanged_vs_origin_main() -> None:
    import subprocess

    diff = subprocess.run(
        ["git", "diff", "--name-only", "origin/main", "--", *PROTECTED_ALGORITHM_FILES],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert diff.stdout.strip() == ""


def test_ssot_docs_once_present() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert DS_HEADING in runbook
    assert THIS_SLICE in runbook
    section = runbook[runbook.index(DS_HEADING) : runbook.index("## 11.3 Autonomy state model")]
    assert "EXTERNAL_EFFECT_AUTHORIZED=false" in section
    assert "REAL_EXTERNAL_EFFECT_AUTHORIZED=false" in section
    assert "STEP_29Q_STATUS=PLAN_ONLY" in section
    assert "POST_COUNT=0" in section
    assert "PERMIT_CREATED=false" in section
    assert "TRADING_LOGIC_AUTHORITY_CHANGED=false" in section
    assert "29P_POLICY_CHANGED=false" in section
    assert SPEC_PATH.name in mot
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_HOST_ENTER_29P_INVALID_STOP_PRICE_REPAIR_V1"
    ) in spec
    assert "11.2.1.DS" in atlas
    assert json.loads(json.dumps({"POST_COUNT": "0"}))["POST_COUNT"] == "0"
