"""Bounded Safety Authority archive sibling exporter V1 — focused contract tests."""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.ops.safety_authority_archive_sibling_exporter_v1.constants_v1 import (
    CAPABILITY_ID,
    ERROR_DECISION_EVIDENCE_ABSENT,
    ERROR_TYPED_REPLAY_SAFETY_ABSENT,
    TARGET_RELATIVE_PATH,
)
from src.ops.safety_authority_archive_sibling_exporter_v1.exporter_v1 import (
    export_safety_authority_to_archive_sibling_from_replay_commit_v1,
)
from src.ops.safety_authority_archive_sibling_exporter_v1.replay_commit_source_v1 import (
    build_safety_authority_sibling_payload_from_replay_commit_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.safety_authority_presentation_projection_materializer_v1 import (
    materialize_safety_authority_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.safety_authority_presentation_projection_v1 import (
    SOURCE_FIELDS_RELATIVE_PATH,
    try_load_safety_authority_presentation_projection_v1,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run
from trading.master_v2.double_play_entry_exit_policy_v0 import EntryExitDirectionState
from trading.master_v2.double_play_state import SideState
from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE,
)
from trading.master_v2.replay_execution_safety_contract_v1 import (
    derive_replay_execution_safety_v1,
)

EXPORTER_PKG = Path("src/ops/safety_authority_archive_sibling_exporter_v1")
FORBIDDEN_IMPORT_PREFIXES = (
    "src.webui",
    "webui",
    "src.webui.",
)


def test_capability_id_is_stable() -> None:
    assert CAPABILITY_ID == "CAPABILITY_SAFETY_AUTHORITY_ARCHIVE_SIBLING_EXPORTER_V1"


def test_exporter_module_has_no_top_level_webui_imports() -> None:
    tree = ast.parse((EXPORTER_PKG / "exporter_v1.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not any(node.module.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES)


def test_integrated_replay_export_materialize_loader_e2e(tmp_path: Path) -> None:
    integrated = _run(
        side_state=SideState.LONG_ARMED,
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    assert integrated.replay_execution_safety is not None
    assert (
        integrated.evidence.killswitch_boundary_effect == KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE
    )

    archive = tmp_path / "archive"
    out = export_safety_authority_to_archive_sibling_from_replay_commit_v1(
        archive_root=archive,
        replay_execution_safety=integrated.replay_execution_safety,
        decision_evidence=integrated.evidence,
        source_label="test_replay_commit",
    )
    assert out.exported is True
    assert (archive / SOURCE_FIELDS_RELATIVE_PATH).is_file()

    payload, errors = build_safety_authority_sibling_payload_from_replay_commit_v1(
        replay_execution_safety=integrated.replay_execution_safety,
        decision_evidence=integrated.evidence,
    )
    assert errors == ()
    assert payload is not None
    assert payload["kill_switch_state"] == "ACTIVE"
    assert payload["veto_active"] is False

    ts_iso = "2026-09-21T12:00:00Z"
    mat = materialize_safety_authority_presentation_projection_v1(
        archive,
        generated_at=ts_iso,
        effective_at=ts_iso,
        saved_at=ts_iso,
    )
    assert mat.written is True
    loaded = try_load_safety_authority_presentation_projection_v1(archive)
    assert loaded.loaded is True
    assert loaded.kill_switch_state == "ACTIVE"
    assert loaded.veto_active is False


def test_dashboard_autobind_after_export(tmp_path: Path) -> None:
    from src.webui.market_dashboard_landscape_producer_binding_v2 import bind_market_universe_slots
    from src.webui.market_dashboard_landscape_v2.availability import Availability

    integrated = _run(
        side_state=SideState.LONG_ARMED,
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    assert integrated.replay_execution_safety is not None

    archive = tmp_path / "archive"
    export_safety_authority_to_archive_sibling_from_replay_commit_v1(
        archive_root=archive,
        replay_execution_safety=integrated.replay_execution_safety,
        decision_evidence=integrated.evidence,
    )
    ts_iso = "2026-09-21T12:00:00Z"
    ts = datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc)
    materialize_safety_authority_presentation_projection_v1(
        archive,
        generated_at=ts_iso,
        effective_at=ts_iso,
        saved_at=ts_iso,
    )
    slots = bind_market_universe_slots(archive_root=archive, generated_at=ts)
    safety = slots["safety_authority"]
    assert safety.availability in (Availability.AVAILABLE, Availability.STALE)
    assert safety.kill_switch_state == "ACTIVE"
    assert safety.veto_active is False


def test_veto_active_when_emergency_boundary_active(tmp_path: Path) -> None:
    from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
        KillSwitchBoundaryMode,
        KillSwitchBoundaryOfflineReplayContextV0,
        evaluate_offline_killswitch_boundary_v0,
    )

    boundary = evaluate_offline_killswitch_boundary_v0(
        KillSwitchBoundaryOfflineReplayContextV0(
            boundary_mode=KillSwitchBoundaryMode.BLOCK_NEW,
            killswitch_active=True,
        ),
        decision_outcome="enter_long",
    )
    typed = derive_replay_execution_safety_v1(killswitch_boundary=boundary)
    evidence = {
        "killswitch_boundary_effect": KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE,
        "killswitch_boundary_ref": boundary.semantic_digest,
    }
    payload, errors = build_safety_authority_sibling_payload_from_replay_commit_v1(
        replay_execution_safety=typed,
        decision_evidence=evidence,
    )
    assert errors == ()
    assert payload is not None
    assert payload["veto_active"] is True
    assert payload["kill_switch_state"] == "KILLED"


def test_missing_typed_safety_fail_closed(tmp_path: Path) -> None:
    out = export_safety_authority_to_archive_sibling_from_replay_commit_v1(
        archive_root=tmp_path,
        replay_execution_safety=None,
        decision_evidence={"killswitch_boundary_effect": "BOUND_OFFLINE"},
    )
    assert out.exported is False
    assert out.error_code == ERROR_TYPED_REPLAY_SAFETY_ABSENT


def test_missing_decision_evidence_fail_closed(tmp_path: Path) -> None:
    integrated = _run()
    out = export_safety_authority_to_archive_sibling_from_replay_commit_v1(
        archive_root=tmp_path,
        replay_execution_safety=integrated.replay_execution_safety,
        decision_evidence=None,
    )
    assert out.exported is False
    assert out.error_code == ERROR_DECISION_EVIDENCE_ABSENT


def test_target_relative_path_matches_presentation_contract() -> None:
    assert TARGET_RELATIVE_PATH == SOURCE_FIELDS_RELATIVE_PATH


def test_d4_4_witness_tree_present() -> None:
    matches = list(Path("docs/ops/market_dashboard").glob("d4_4_*"))
    assert matches, "D4.4 witness tree expected after this slice"
