"""Isolated closure checks for the three Master-V2 conflicts. No network. No POST."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
    admit_forensic_overlay_to_productive_consumers_v1,
)
from src.ops.dynamic_scope_persistence_binding_v1.constants_v1 import (
    RUNTIME_ACTIVATED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_OWNER,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
    LEDGER_FILENAME,
    bind_synthetic_enter_forensic_session_v1,
    build_synthetic_enter_forensic_session_v1,
    maybe_apply_synthetic_enter_forensic_overlay_v1,
    reset_synthetic_enter_forensic_session_v1,
)

REPO = Path(__file__).resolve().parents[2]
IAM = REPO / "config/governance/current_system_interaction_authority_map_v1/source_v1.json"
CENSUS = REPO / "config/governance/current_system_census_graph_v1/source_v1.json"
JOIN = (
    REPO
    / "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py"
)
CYCLE = (
    REPO
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py"
)
CURSOR = (
    REPO
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_sidestate_confirmation_cursor_v1.py"
)

_ALLOWED_PREFIXES = (
    "config/governance/current_system_interaction_authority_map_v1/",
    "config/governance/current_system_census_graph_v1/source_v1.json",
    "docs/governance/current_system_interaction_authority_map_v1/generated/",
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py",
    "tests/ops/test_master_v2_three_conflict_closure_v1.py",
)
_FORBIDDEN_FRAGMENTS = (
    "src/trading/master_v2/double_play_state.py",
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
    "src/trading/master_v2/capital_risk_sizing",
    "src/ops/dynamic_scope_persistence_binding_v1/",
)


def _iam() -> dict:
    return json.loads(IAM.read_text(encoding="utf-8"))


def _domain(domain_id: str) -> dict:
    return next(item for item in _iam()["domains"] if item["id"] == domain_id)


def _binder() -> dict:
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    return next(
        item
        for item in census["census_objects"]
        if item["object_id"] == "SO-OPS-PKG:dynamic_scope_persistence_binding_v1"
    )


def _overlay(*, applied: bool, outcome: str, record: dict | None, replay: object):
    return SimpleNamespace(
        applied=applied,
        replay=replay,
        record=record,
        natural_outcome_before="observe",
        synthetic_side=outcome,
    )


def test_iam_decision_owner_and_cycle_entry_are_split() -> None:
    domain = _domain("mv2_double_play")
    assert _iam()["authority_effect"] == "NONE"
    assert domain["canonical_owner_ref"] == "run_integrated_offline_trading_logic_replay_v1"
    assert "DECISION_OWNER=run_integrated_offline_trading_logic_replay_v1" in domain["role"]
    assert (
        "PRODUCTIVE_CYCLE_ENTRY=run_current_productive_master_v2_runtime_cycle_v1" in domain["role"]
    )
    assert (
        "HISTORICAL_CANONICAL_OWNER_REF=run_current_productive_master_v2_runtime_cycle_v1"
        in (domain["role"])
    )


def test_dynamic_scope_state_owner_cursor_and_inactive_binder() -> None:
    domain = _domain("dynamic_scope")
    assert domain["canonical_owner_ref"] == (
        "trading.master_v2.double_play_state.RuntimeScopeState"
    )
    assert "STATE_OWNER=trading.master_v2.double_play_state.RuntimeScopeState" in domain["role"]
    assert (
        "PRODUCTIVE_RESTART_CARRIER=current_productive_sidestate_confirmation_cursor_v1"
        in domain["role"]
    )
    assert "BINDER_ROLE=SERIALIZATION_CODEC_ADAPTER" in domain["role"]
    assert "BINDER_RUNTIME_ACTIVATED=false" in domain["role"]
    assert "REPRESENTATION=SUBDOMAIN" in domain["role"]
    assert "parent_domain=mv2_double_play" in domain["role"]
    binder = _binder()
    assert binder["runtime_role"] != "PRODUCTIVE_HOT_PATH"
    assert binder["runtime_role"] == "SUPPORT"
    assert binder["persistence_role"] == "SERIALIZATION_CODEC_ADAPTER"
    assert "BINDER_RUNTIME_ACTIVATED=false" in binder["purpose"]
    assert RUNTIME_ACTIVATED is False


def test_cursor_restart_semantics_remain_the_productive_carrier() -> None:
    cycle = CYCLE.read_text(encoding="utf-8")
    cursor = CURSOR.read_text(encoding="utf-8")
    assert "runtime_scope_state = None if restored is None else restored.runtime_scope_state" in (
        cycle
    )
    assert "def persist_current_productive_sidestate_confirmation_cursor_v1" in cursor
    assert CURSOR_OWNER.endswith("current_productive_sidestate_confirmation_cursor_v1")
    assert "commit_host_dynamic_scope_after_replay_v1" not in cycle


def test_missing_synthetic_session_keeps_the_natural_replay() -> None:
    natural = SimpleNamespace(evidence=SimpleNamespace(decision_outcome="hold"))
    overlay = _overlay(applied=False, outcome="", record=None, replay=natural)
    admission = admit_forensic_overlay_to_productive_consumers_v1(natural, overlay)
    assert admission.productive_replay is natural
    assert admission.admits_synthetic_to_29p is False


def test_bound_synthetic_replay_is_not_a_productive_consumer() -> None:
    natural = SimpleNamespace(evidence=SimpleNamespace(decision_outcome="observe"))
    synthetic = SimpleNamespace(evidence=SimpleNamespace(decision_outcome="enter_long"))
    overlay = _overlay(
        applied=True,
        outcome="enter_long",
        record={"kept": True},
        replay=synthetic,
    )
    admission = admit_forensic_overlay_to_productive_consumers_v1(natural, overlay)
    seen: dict[str, object] = {}

    def _fake_29p(*, replay: object, **_kwargs: object) -> SimpleNamespace:
        seen["replay"] = replay
        outcome = str(getattr(getattr(replay, "evidence", None), "decision_outcome", ""))
        seen["capital_or_sizing"] = outcome in {"enter_long", "enter_short"}
        return SimpleNamespace(replay=replay, venue_plan=False, execution=False)

    result = _fake_29p(replay=admission.productive_replay)
    assert seen["replay"] is natural
    assert seen["capital_or_sizing"] is False
    assert result.venue_plan is False
    assert result.execution is False
    assert admission.admits_synthetic_to_29p is False
    assert admission.admits_synthetic_to_capital is False
    assert admission.admits_synthetic_to_sizing is False
    assert admission.admits_synthetic_to_venue_plan is False
    assert admission.admits_synthetic_to_execution is False
    assert admission.retains_forensic_record is True


def test_synthetic_enter_long_and_short_do_not_admit_sizing() -> None:
    natural = SimpleNamespace(evidence=SimpleNamespace(decision_outcome="hold"))
    for outcome in ("enter_long", "enter_short"):
        synthetic = SimpleNamespace(evidence=SimpleNamespace(decision_outcome=outcome))
        admission = admit_forensic_overlay_to_productive_consumers_v1(
            natural,
            _overlay(applied=True, outcome=outcome, record={"side": outcome}, replay=synthetic),
        )
        assert admission.productive_replay is natural
        assert admission.admits_synthetic_to_sizing is False
        assert admission.admits_synthetic_to_venue_plan is False
        assert admission.admits_synthetic_to_execution is False


def test_real_overlay_ledger_survives_and_productive_replay_stays_natural(tmp_path: Path) -> None:
    from tests.ops.test_current_productive_synthetic_enter_forensic_v1 import (
        _observe_replay_from_enter_fixture,
    )

    natural = _observe_replay_from_enter_fixture()
    natural_outcome = str(natural.evidence.decision_outcome)
    session = build_synthetic_enter_forensic_session_v1(
        enabled=True,
        synthetic_side="enter_short",
        inject_cycle_index=1,
        product_evidence_root=tmp_path,
        continuous_run_id="three-conflict-closure",
    )
    token = bind_synthetic_enter_forensic_session_v1(session)
    try:
        overlay = maybe_apply_synthetic_enter_forensic_overlay_v1(natural, cycle_index=1)
    finally:
        reset_synthetic_enter_forensic_session_v1(token)
    admission = admit_forensic_overlay_to_productive_consumers_v1(natural, overlay)
    assert overlay.applied is True
    assert str(natural.evidence.decision_outcome) == natural_outcome
    assert admission.productive_replay is natural
    assert str(admission.productive_replay.evidence.decision_outcome) == natural_outcome
    assert (tmp_path / LEDGER_FILENAME).is_file()
    assert admission.admits_synthetic_to_29p is False
    assert admission.admits_synthetic_to_sizing is False
    assert admission.admits_synthetic_to_venue_plan is False
    assert admission.admits_synthetic_to_execution is False


def test_natural_enter_exit_and_hold_remain_the_productive_replay() -> None:
    for outcome in ("enter_long", "exit_long", "hold"):
        natural = SimpleNamespace(evidence=SimpleNamespace(decision_outcome=outcome))
        admission = admit_forensic_overlay_to_productive_consumers_v1(
            natural,
            _overlay(applied=False, outcome="", record=None, replay=natural),
        )
        assert admission.productive_replay is natural
        assert admission.productive_replay.evidence.decision_outcome == outcome
        assert admission.admits_synthetic_to_29p is False


def test_join_wires_productive_replay_and_adds_no_post_path() -> None:
    text = JOIN.read_text(encoding="utf-8")
    call = "join_current_productive_enter_live_29p_before_venue_plan_v1(\n            replay=productive_replay,"
    assert call in text
    assert "replay=overlay.replay," not in text.split(call, 1)[1]
    assert "FORENSIC_SYNTHETIC_DECISION_NOT_PRODUCTIVE" in text
    assert "try_bind_current_productive_venue_plan_v1" in text
    assert 'post_count="0"' in text
    assert "submit_order" not in text
    assert "trade/order" not in text


def test_changeset_does_not_touch_protected_trading_logic() -> None:
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=REPO,
        text=True,
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=REPO,
        text=True,
    ).splitlines()
    changed = [line.strip() for line in [*tracked, *untracked] if line.strip()]
    assert changed
    for path in changed:
        assert path.startswith(_ALLOWED_PREFIXES), path
        assert not any(fragment in path for fragment in _FORBIDDEN_FRAGMENTS)
