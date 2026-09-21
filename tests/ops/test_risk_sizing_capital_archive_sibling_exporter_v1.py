"""Bounded Risk/Sizing/Capital archive sibling exporter V1 — focused contract tests."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.ops.risk_sizing_capital_archive_sibling_exporter_v1.constants_v1 import (
    CAPABILITY_ID,
    ERROR_SIZING_DECISION_ABSENT,
    TARGET_RELATIVE_PATH,
)
from src.ops.risk_sizing_capital_archive_sibling_exporter_v1.exporter_v1 import (
    export_risk_sizing_capital_to_archive_sibling_from_replay_commit_v1,
)
from src.ops.risk_sizing_capital_archive_sibling_exporter_v1.replay_commit_source_v1 import (
    build_risk_sizing_capital_sibling_payload_from_replay_commit_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.risk_sizing_capital_presentation_projection_materializer_v1 import (
    SOURCE_FIELDS_RELATIVE_PATH,
    materialize_risk_sizing_capital_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.risk_sizing_capital_presentation_projection_v1 import (
    try_load_risk_sizing_capital_presentation_projection_v1,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run
from trading.master_v2.double_play_entry_exit_policy_v0 import EntryExitDirectionState
from trading.master_v2.double_play_state import SideState

EXPORTER_PKG = Path("src/ops/risk_sizing_capital_archive_sibling_exporter_v1")
FORBIDDEN_IMPORT_PREFIXES = (
    "src.webui",
    "webui",
    "src.webui.",
)


def test_capability_id_is_stable() -> None:
    assert CAPABILITY_ID == "CAPABILITY_RISK_SIZING_CAPITAL_ARCHIVE_SIBLING_EXPORTER_V1"


def test_exporter_module_has_no_top_level_webui_imports() -> None:
    tree = ast.parse((EXPORTER_PKG / "exporter_v1.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not any(node.module.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES)


def test_replay_commit_export_and_materialize_e2e(tmp_path: Path) -> None:
    integrated = _run(
        side_state=SideState.LONG_ARMED,
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    if integrated.intermediate is None:
        pytest.skip("integrated replay intermediate unavailable for this fixture")
    if integrated.intermediate.capital_risk_sizing_decision is None:
        pytest.skip("sizing decision absent on replay intermediate")

    archive = tmp_path / "archive"
    out = export_risk_sizing_capital_to_archive_sibling_from_replay_commit_v1(
        archive_root=archive,
        replay_intermediate=integrated.intermediate,
        source_label="test_replay_commit",
    )
    assert out.exported is True
    assert (archive / SOURCE_FIELDS_RELATIVE_PATH).is_file()

    payload, errors = build_risk_sizing_capital_sibling_payload_from_replay_commit_v1(
        replay_intermediate=integrated.intermediate,
    )
    assert errors == ()
    assert payload is not None

    mat = materialize_risk_sizing_capital_presentation_projection_v1(
        archive,
        risk_sizing_capital=None,
        generated_at="2026-09-21T12:00:00Z",
        effective_at="2026-09-21T12:00:00Z",
    )
    assert mat.written is True
    loaded = try_load_risk_sizing_capital_presentation_projection_v1(archive)
    assert loaded.loaded is True


def test_dashboard_autobind_after_export(tmp_path: Path) -> None:
    from datetime import datetime, timezone

    from src.webui.market_dashboard_landscape_producer_binding_v2 import bind_market_universe_slots
    from src.webui.market_dashboard_landscape_v2.availability import Availability

    integrated = _run(
        side_state=SideState.LONG_ARMED,
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    if (
        integrated.intermediate is None
        or integrated.intermediate.capital_risk_sizing_decision is None
    ):
        pytest.skip("replay intermediate sizing unavailable")

    archive = tmp_path / "archive"
    export_risk_sizing_capital_to_archive_sibling_from_replay_commit_v1(
        archive_root=archive,
        replay_intermediate=integrated.intermediate,
    )
    ts_iso = "2026-09-21T12:00:00Z"
    ts = datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc)
    mat = materialize_risk_sizing_capital_presentation_projection_v1(
        archive,
        generated_at=ts_iso,
        effective_at=ts_iso,
    )
    assert mat.written is True
    slots = bind_market_universe_slots(archive_root=archive, generated_at=ts)
    rs_slot = slots["risk_sizing_capital"]
    assert rs_slot.availability in (Availability.AVAILABLE, Availability.STALE)


def test_blocked_outcome_maps_sizing_status_block_without_post_sizing() -> None:
    from types import SimpleNamespace

    from src.governance.capital_risk_sizing_v1 import CapitalRiskSizingOutcome
    from src.ops.risk_sizing_capital_archive_sibling_exporter_v1.replay_commit_source_v1 import (
        _resolve_sizing_status,
    )

    decision = SimpleNamespace(
        post_sizing_risk=None,
        quantity_provenance=None,
        outcome=CapitalRiskSizingOutcome.BLOCKED,
    )
    assert _resolve_sizing_status(decision) == "BLOCK"  # type: ignore[arg-type]


def test_missing_sizing_decision_fail_closed(tmp_path: Path) -> None:
    out = export_risk_sizing_capital_to_archive_sibling_from_replay_commit_v1(
        archive_root=tmp_path,
        replay_intermediate=object(),
        source_label="empty_intermediate",
    )
    assert out.exported is False
    assert out.error_code == ERROR_SIZING_DECISION_ABSENT


def test_target_relative_path_matches_presentation_contract() -> None:
    assert TARGET_RELATIVE_PATH == SOURCE_FIELDS_RELATIVE_PATH
