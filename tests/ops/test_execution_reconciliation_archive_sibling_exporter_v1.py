"""Bounded Execution/Reconciliation archive sibling exporter V1 — focused contract tests."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.ops.execution_reconciliation_archive_sibling_exporter_v1.constants_v1 import (
    CAPABILITY_ID,
    ERROR_DECISION_EVIDENCE_ABSENT,
    TARGET_RELATIVE_PATH,
)
from src.ops.execution_reconciliation_archive_sibling_exporter_v1.exporter_v1 import (
    export_execution_reconciliation_to_archive_sibling_from_replay_commit_v1,
)
from src.ops.execution_reconciliation_archive_sibling_exporter_v1.replay_commit_source_v1 import (
    build_execution_reconciliation_sibling_payload_from_replay_commit_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.execution_reconciliation_presentation_projection_materializer_v1 import (
    SOURCE_FIELDS_RELATIVE_PATH,
    materialize_execution_reconciliation_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.execution_reconciliation_presentation_projection_v1 import (
    try_load_execution_reconciliation_presentation_projection_v1,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _run
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    ORDER_INTENT_EFFECT_BOUND_OFFLINE,
    bind_canonical_order_intent_offline_replay_evidence_v0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    bind_capital_risk_sizing_offline_replay_evidence_v0,
    build_scenario_tick_decision_evidence_v0,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryExitDirectionState,
)
from trading.master_v2.double_play_state import SideState

EXPORTER_PKG = Path("src/ops/execution_reconciliation_archive_sibling_exporter_v1")
FORBIDDEN_IMPORT_PREFIXES = (
    "src.webui",
    "webui",
    "src.webui.",
)


def test_capability_id_is_stable() -> None:
    assert CAPABILITY_ID == "CAPABILITY_EXECUTION_RECONCILIATION_ARCHIVE_SIBLING_EXPORTER_V1"


def test_exporter_module_has_no_top_level_webui_imports() -> None:
    tree = ast.parse((EXPORTER_PKG / "exporter_v1.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(alias.name.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES)
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not any(node.module.startswith(p) for p in FORBIDDEN_IMPORT_PREFIXES)


def _bound_offline_replay_commit() -> tuple[object, object]:
    evidence = build_scenario_tick_decision_evidence_v0(
        decision_id="decision-er-export",
        replay_id="replay-er-export",
        instrument_id="ETH-USDT-SWAP",
        trading_epoch=48,
        composition_result_id="composition-er",
        entry_exit_policy_ref="policy-er",
        selected_side="long",
        decision_outcome=DecisionOutcome.ENTER_LONG.value,
        reason_codes=("ENTER_LONG",),
        decision_precedence_trace=("enter",),
        config_digest="c" * 64,
        implementation_digest="i" * 64,
    )
    sizing_binding = bind_capital_risk_sizing_offline_replay_evidence_v0(evidence)
    intent_binding = bind_canonical_order_intent_offline_replay_evidence_v0(
        sizing_binding.evidence,
        sizing_decision=sizing_binding.sizing_decision,
    )
    assert intent_binding.order_intent_effect == ORDER_INTENT_EFFECT_BOUND_OFFLINE
    assert intent_binding.canonical_intent is not None
    intermediate = SimpleNamespace(canonical_order_intent=intent_binding.canonical_intent)
    return intent_binding.evidence, intermediate


def test_bound_offline_replay_commit_export_materialize_loader(tmp_path: Path) -> None:
    evidence, intermediate = _bound_offline_replay_commit()
    archive = tmp_path / "archive"
    out = export_execution_reconciliation_to_archive_sibling_from_replay_commit_v1(
        archive_root=archive,
        replay_intermediate=intermediate,
        decision_evidence=evidence,
        source_label="test_bound_offline",
    )
    assert out.exported is True
    assert (archive / SOURCE_FIELDS_RELATIVE_PATH).is_file()

    payload, errors = build_execution_reconciliation_sibling_payload_from_replay_commit_v1(
        replay_intermediate=intermediate,
        decision_evidence=evidence,
    )
    assert errors == ()
    assert payload is not None
    assert payload["execution_status"] == ORDER_INTENT_EFFECT_BOUND_OFFLINE

    mat = materialize_execution_reconciliation_presentation_projection_v1(
        archive,
        execution_reconciliation=None,
        generated_at="2026-09-21T12:00:00Z",
        effective_at="2026-09-21T12:00:00Z",
    )
    assert mat.written is True
    loaded = try_load_execution_reconciliation_presentation_projection_v1(archive)
    assert loaded.loaded is True


def test_dashboard_autobind_after_bound_offline_export(tmp_path: Path) -> None:
    from datetime import datetime, timezone

    from src.webui.market_dashboard_landscape_producer_binding_v2 import bind_market_universe_slots
    from src.webui.market_dashboard_landscape_v2.availability import Availability

    evidence, intermediate = _bound_offline_replay_commit()
    archive = tmp_path / "archive"
    export_execution_reconciliation_to_archive_sibling_from_replay_commit_v1(
        archive_root=archive,
        replay_intermediate=intermediate,
        decision_evidence=evidence,
    )
    ts_iso = "2026-09-21T12:00:00Z"
    ts = datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc)
    materialize_execution_reconciliation_presentation_projection_v1(
        archive,
        generated_at=ts_iso,
        effective_at=ts_iso,
    )
    slots = bind_market_universe_slots(archive_root=archive, generated_at=ts)
    er_slot = slots["execution_reconciliation"]
    assert er_slot.availability in (Availability.AVAILABLE, Availability.STALE)
    assert er_slot.execution_status == ORDER_INTENT_EFFECT_BOUND_OFFLINE


def test_unbound_integrated_replay_exports_none_status(tmp_path: Path) -> None:
    integrated = _run(
        side_state=SideState.LONG_ARMED,
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )
    if integrated.intermediate is None:
        pytest.skip("integrated replay intermediate unavailable")
    archive = tmp_path / "archive"
    out = export_execution_reconciliation_to_archive_sibling_from_replay_commit_v1(
        archive_root=archive,
        replay_intermediate=integrated.intermediate,
        decision_evidence=integrated.evidence,
    )
    assert out.exported is True
    payload = json.loads((archive / SOURCE_FIELDS_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert payload["execution_status"] == "NONE"


def test_missing_decision_evidence_fail_closed(tmp_path: Path) -> None:
    out = export_execution_reconciliation_to_archive_sibling_from_replay_commit_v1(
        archive_root=tmp_path,
        replay_intermediate=object(),
        decision_evidence=None,
    )
    assert out.exported is False
    assert out.error_code == ERROR_DECISION_EVIDENCE_ABSENT


def test_target_relative_path_matches_presentation_contract() -> None:
    assert TARGET_RELATIVE_PATH == SOURCE_FIELDS_RELATIVE_PATH
