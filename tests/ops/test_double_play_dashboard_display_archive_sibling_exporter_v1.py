"""Tests for productive Double Play display archive sibling export from replay commit."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.ops.double_play_archive_sibling_exporter_v1.constants_v1 import (
    CAPABILITY_ID,
    ERROR_REPLAY_COMMIT_INCOMPLETE,
    ERROR_RESULTV1_SHORTCUT_FORBIDDEN,
    TARGET_RELATIVE_PATH,
)
from src.ops.double_play_archive_sibling_exporter_v1.exporter_v1 import (
    export_double_play_display_to_archive_sibling_from_replay_commit_v1,
)
from src.ops.double_play_archive_sibling_exporter_v1.replay_commit_source_v1 import (
    build_double_play_dashboard_display_sibling_payload_from_replay_commit_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.family_export_adapter_v1 import (
    export_families_after_runtime_commit_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.models_v1 import (
    ArchiveBindingV1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.state_root_layout_v1 import (
    materialize_state_root_layout_v1,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.constants_v1 import (
    CAPABILITY_ID as PS_CAPABILITY_ID,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.models_v1 import (
    PureStackDisplayDecisionBundleV1,
)
from trading.master_v2.double_play_capital_slot import (
    CapitalSlotRatchetDecision,
    CapitalSlotReleaseDecision,
    CapitalSlotStatus,
)
from trading.master_v2.double_play_composition import (
    DoublePlayCompositionDecision,
    DoublePlayCompositionStatus,
)
from trading.master_v2.double_play_futures_input import (
    FuturesInputReadinessDecision,
    FuturesReadinessStatus,
)
from trading.master_v2.double_play_state import TransitionDecision
from trading.master_v2.double_play_suitability import (
    SideCompatibility,
    StrategyMetadata,
    StrategySuitabilityProjection,
    SuitabilityClass,
    SuitabilityProjectionDecision,
)
from trading.master_v2.double_play_survival import (
    SurvivalEnvelopeDecision,
    SurvivalEnvelopeStatus,
)
from src.webui.market_dashboard_landscape_producer_binding_v2 import bind_market_universe_slots
from src.webui.market_dashboard_landscape_v2.availability import Availability
from src.webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_materializer_v1 import (
    SOURCE_DISPLAY_RELATIVE_PATH,
)
from src.webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_v1 import (
    STORAGE_RELATIVE_PATH,
    try_load_double_play_presentation_projection_v1,
)

REPO = Path(__file__).resolve().parents[2]
EXPORTER_DIR = REPO / "src/ops/double_play_archive_sibling_exporter_v1"


def _complete_bundle() -> PureStackDisplayDecisionBundleV1:
    transition = TransitionDecision(True, "NOOP", False)
    survival = SurvivalEnvelopeDecision(
        status=SurvivalEnvelopeStatus.BLOCKED,
        pre_authorization_eligible=False,
        block_reasons=(),
        live_authorization=False,
    )
    meta = StrategyMetadata(
        strategy_id="binding-test",
        strategy_family="double_play",
        declared_side=SideCompatibility.BOTH,
        explicit_side_evidence=True,
    )
    projection = StrategySuitabilityProjection(
        strategy_id=meta.strategy_id,
        strategy_family=meta.strategy_family,
        suitability_class=SuitabilityClass.UNKNOWN_SUITABILITY,
        side_compatibility=SideCompatibility.BOTH,
        eligible_for_long_bull_pool=False,
        eligible_for_short_bear_pool=False,
        eligible_for_neutral_pool=False,
        block_reasons=(),
        missing_inputs=(),
        reason="blocked",
    )
    suitability = SuitabilityProjectionDecision(
        projection=projection,
        can_enter_any_candidate_pool=False,
        can_enter_long_bull_pool=False,
        can_enter_short_bear_pool=False,
        can_enter_neutral_pool=False,
        live_authorization=False,
    )
    futures = FuturesInputReadinessDecision(
        status=FuturesReadinessStatus.BLOCKED,
        ready_for_downstream_model_use=False,
        ready_for_dynamic_scope=False,
        ready_for_capital_slot=False,
        ready_for_suitability=False,
        ready_for_survival_envelope=False,
        block_reasons=(),
        missing_inputs=("instrument",),
    )
    ratchet = CapitalSlotRatchetDecision(
        status=CapitalSlotStatus.ACTIVE,
        ratchet_target=0.0,
        can_ratchet=False,
        block_reasons=(),
        reason="t",
        live_authorization=False,
    )
    release = CapitalSlotReleaseDecision(
        status=CapitalSlotStatus.ACTIVE,
        released=False,
        release_reason=None,
        block_reasons=(),
        reason="t",
        live_authorization=False,
        authorizes_new_future_selection=False,
        authorizes_new_trade=False,
    )
    composition = DoublePlayCompositionDecision(
        status=DoublePlayCompositionStatus.OBSERVE_ONLY,
        block_reasons=(),
        reason="t",
        live_authorization=False,
    )
    return PureStackDisplayDecisionBundleV1(
        schema_version="productive_pure_stack_display_decision_bundle.v1",
        capability_id=PS_CAPABILITY_ID,
        owner="test",
        cycle_id="c",
        cycle_index=0,
        instrument_id="SATS-USDT-SWAP",
        trading_epoch=1,
        created_at="2026-08-05T00:00:00Z",
        status="PURE_STACK_DISPLAY_DECISION_BUNDLE_READY",
        futures_input=futures,
        transition=transition,
        survival=survival,
        suitability=suitability,
        capital_slot_ratchet=ratchet,
        capital_slot_release=release,
        composition=composition,
    )


def _intermediate_with_bundle() -> object:
    bundle = _complete_bundle()

    class _Inter:
        display_decision_bundle = bundle

    return _Inter()


def test_capability_id_stable() -> None:
    assert CAPABILITY_ID == "CAPABILITY_DOUBLE_PLAY_ARCHIVE_SIBLING_EXPORTER_V1"
    assert TARGET_RELATIVE_PATH == SOURCE_DISPLAY_RELATIVE_PATH


def test_build_sibling_from_replay_commit_bundle() -> None:
    payload, errors = build_double_play_dashboard_display_sibling_payload_from_replay_commit_v1(
        replay_intermediate=_intermediate_with_bundle(),
    )
    assert errors == ()
    assert payload is not None
    assert payload.get("overall_status")
    assert payload.get("panel_summaries")


def test_resultv1_shortcut_forbidden() -> None:
    class _BadInter:
        transition_decision = TransitionDecision(True, "NOOP", False)
        composition_result = object()

    payload, errors = build_double_play_dashboard_display_sibling_payload_from_replay_commit_v1(
        replay_intermediate=_BadInter(),
    )
    assert payload is None
    assert ERROR_RESULTV1_SHORTCUT_FORBIDDEN in errors


def test_export_and_materialize_e2e(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    out = export_double_play_display_to_archive_sibling_from_replay_commit_v1(
        archive_root=archive_root,
        replay_intermediate=_intermediate_with_bundle(),
    )
    assert out.exported is True
    assert (archive_root / TARGET_RELATIVE_PATH).is_file()

    from src.webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_materializer_v1 import (
        materialize_double_play_presentation_projection_v1,
    )

    mat = materialize_double_play_presentation_projection_v1(
        archive_root,
        generated_at="2026-09-21T12:00:00Z",
        effective_at="2026-09-21T12:00:00Z",
    )
    assert mat.written is True
    loaded = try_load_double_play_presentation_projection_v1(archive_root)
    assert loaded.loaded is True


def test_family_export_double_play_with_bundle(tmp_path: Path) -> None:
    state_roots = materialize_state_root_layout_v1(runtime_root=tmp_path / "runtime")
    archive_root = tmp_path / "archive"
    readmodels = archive_root / "readmodels"
    readmodels.mkdir(parents=True)
    archive = ArchiveBindingV1(
        archive_root=str(archive_root.resolve()),
        resolution_precedence="test",
        readmodels_dir=str(readmodels.resolve()),
        dynamic_scope_sibling_path=str((readmodels / "dynamic_scope_state_v1.json").resolve()),
        canonical_decision_sibling_path=str(
            (readmodels / "canonical_trading_decision_evidence.v1.json").resolve()
        ),
        double_play_sibling_path=str(
            (readmodels / "double_play_dashboard_display.v1.json").resolve()
        ),
        regime_bull_bear_switch_sibling_path=str(
            (readmodels / "regime_bull_bear_switch.v1.json").resolve()
        ),
        writable=True,
    )

    families = export_families_after_runtime_commit_v1(
        state_roots=state_roots,
        archive=archive,
        cycle_id="cycle-dp-1",
        cycle_index=0,
        dynamic_scope_persisted=False,
        evidence_payload=None,
        replay_intermediate=_intermediate_with_bundle(),
        generated_at="2026-09-21T12:00:00Z",
    )
    dp = families["double_play"]
    assert dp.exported is True
    assert dp.materialized is True
    assert dp.loader_ok is True
    assert (archive_root / STORAGE_RELATIVE_PATH).is_file()


def test_partial_intermediate_fail_closed(tmp_path: Path) -> None:
    class _Partial:
        transition_decision = TransitionDecision(True, "NOOP", False)

    out = export_double_play_display_to_archive_sibling_from_replay_commit_v1(
        archive_root=tmp_path,
        replay_intermediate=_Partial(),
    )
    assert out.exported is False
    assert out.error_code == ERROR_REPLAY_COMMIT_INCOMPLETE


def test_dashboard_autobind_after_export(tmp_path: Path) -> None:
    from datetime import datetime, timezone

    archive_root = tmp_path / "archive"
    export_double_play_display_to_archive_sibling_from_replay_commit_v1(
        archive_root=archive_root,
        replay_intermediate=_intermediate_with_bundle(),
    )
    from src.webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_materializer_v1 import (
        materialize_double_play_presentation_projection_v1,
    )

    ts_iso = "2026-09-21T12:00:00Z"
    ts = datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc)
    materialize_double_play_presentation_projection_v1(
        archive_root,
        generated_at=ts_iso,
        effective_at=ts_iso,
    )
    slots = bind_market_universe_slots(
        archive_root=archive_root,
        generated_at=ts,
    )
    dp_slot = slots["double_play"]
    assert dp_slot.availability in (Availability.AVAILABLE, Availability.STALE)


def test_exporter_replay_commit_module_no_compose_import() -> None:
    forbidden = (
        "double_play_composition_matrix",
        "double_play_state",
        "compose_double_play_decision",
    )
    path = EXPORTER_DIR / "replay_commit_source_v1.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for token in forbidden:
                assert token not in node.module
