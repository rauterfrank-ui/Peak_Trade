"""Focused tests for productive Pure-Stack display Decision host binding."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.ops.productive_decision_host_active_archive_three_family_binding_v1.double_play_input_gate_v1 import (
    classify_double_play_canonical_inputs_v1,
    try_extract_double_play_decision_inputs_from_replay_intermediate_v1,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.authority_inventory_v1 import (
    missing_input_authorities_v1,
    probe_pure_stack_display_input_authorities_v1,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    FIXTURE_FALLBACK_AUTHORIZED,
    RESULTV1_MAPPING_AUTHORIZED,
    STATUS_BLOCKED_CANONICAL_INPUT_AUTHORITY_ABSENT,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.host_cycle_v1 import (
    extract_transition_from_replay_intermediate_v1,
    run_pure_stack_display_decision_host_cycle_v1,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.input_builders_v1 import (
    CanonicalInputAuthorityAbsentError,
    assert_no_unauthorized_fallback_flags_v1,
    build_productive_capital_slot_config_v1,
    build_productive_capital_slot_state_v1,
    build_productive_futures_input_snapshot_v1,
    build_productive_suitability_projection_input_v1,
    build_productive_survival_envelope_v1,
    extract_transition_decision_passthrough_v1,
    reject_resultv1_mapping_attempt_v1,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.models_v1 import (
    PureStackDisplayDecisionBundleV1,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.persistence_v1 import (
    load_pure_stack_display_decision_bundle_payload_v1,
    persist_pure_stack_display_decision_bundle_atomic_v1,
)
from src.ops.productive_pure_stack_display_decision_host_binding_v1.producers_binding_v1 import (
    assert_transition_identity_v1,
    produce_capital_slot_ratchet_v1,
    produce_capital_slot_release_v1,
    produce_composition_decision_v1,
    produce_futures_input_readiness_v1,
    produce_suitability_projection_decision_v1,
    produce_survival_envelope_decision_v1,
)
from trading.master_v2.double_play_capital_slot import (
    CapitalSlotRatchetDecision,
    CapitalSlotReleaseDecision,
    CapitalSlotStatus,
)
from trading.master_v2.double_play_composition import (
    DoublePlayCompositionDecision,
    DoublePlayCompositionStatus,
    RequestedSide,
)
from trading.master_v2.double_play_futures_input import (
    FuturesInputReadinessDecision,
    FuturesReadinessStatus,
)
from trading.master_v2.double_play_state import SideState, TransitionDecision
from trading.master_v2.double_play_suitability import (
    SideCompatibility,
    StrategyMetadata,
    SuitabilityClass,
    SuitabilityProjectionDecision,
    StrategySuitabilityProjection,
)
from trading.master_v2.double_play_survival import SurvivalEnvelopeDecision, SurvivalEnvelopeStatus


REPO_ROOT = Path(__file__).resolve().parents[2]
PKG = REPO_ROOT / "src/ops/productive_pure_stack_display_decision_host_binding_v1"
BRIDGE = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "decision_economics_cycle_bridge_v1.py"
)
CYCLE_SESSION = (
    REPO_ROOT
    / "src/ops/productive_decision_host_active_archive_three_family_binding_v1"
    / "cycle_session_v1.py"
)
INTEGRATED = REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"


def test_capability_constants_stable() -> None:
    assert CAPABILITY_ID.endswith("HOST_BINDING_V1")
    assert RESULTV1_MAPPING_AUTHORIZED is False
    assert FIXTURE_FALLBACK_AUTHORIZED is False
    assert_no_unauthorized_fallback_flags_v1()


def test_authority_inventory_marks_five_inputs_absent() -> None:
    missing = missing_input_authorities_v1()
    assert "FuturesInputSnapshot" in missing
    assert "DoublePlaySurvivalEnvelope" in missing
    assert "SuitabilityProjectionInput" in missing
    assert "CapitalSlotConfig" in missing
    assert "CapitalSlotState" in missing
    assert "TransitionDecision" not in missing
    probes = probe_pure_stack_display_input_authorities_v1()
    assert any(p.input_name == "TransitionDecision" and p.authority_present for p in probes)


@pytest.mark.parametrize(
    "builder",
    [
        build_productive_futures_input_snapshot_v1,
        build_productive_survival_envelope_v1,
        build_productive_suitability_projection_input_v1,
        build_productive_capital_slot_config_v1,
        build_productive_capital_slot_state_v1,
    ],
)
def test_input_builders_fail_closed_without_authority(builder) -> None:
    with pytest.raises(CanonicalInputAuthorityAbsentError) as exc:
        builder()
    assert STATUS_BLOCKED_CANONICAL_INPUT_AUTHORITY_ABSENT in str(exc.value)


def test_transition_passthrough_identity() -> None:
    original = TransitionDecision(True, "SHORT_ARMED", False)

    class _Inter:
        transition_decision = original

    extracted = extract_transition_from_replay_intermediate_v1(_Inter())
    assert extracted is original
    passed = extract_transition_decision_passthrough_v1(transition_decision=extracted)
    assert passed is original
    assert assert_transition_identity_v1(
        from_transition_state=original,
        from_bundle_or_intermediate=passed,
    )


def test_reject_resultv1_mapping_attempt() -> None:
    class FakeSurvivalResultV1:
        pass

    with pytest.raises(CanonicalInputAuthorityAbsentError, match="RESULTV1_MAPPING_FORBIDDEN"):
        reject_resultv1_mapping_attempt_v1(FakeSurvivalResultV1())


def test_host_cycle_blocked_no_runtime_mutation(tmp_path: Path) -> None:
    original = TransitionDecision(False, "COOLDOWN_BLOCK", False)

    class _Inter:
        transition_decision = original

    result = run_pure_stack_display_decision_host_cycle_v1(
        replay_intermediate=_Inter(),
        cycle_id="c1",
        cycle_index=0,
        instrument_id="SATS-USDT-SWAP",
        trading_epoch=1,
        state_root=tmp_path,
        allow_runtime_mutation=True,
    )
    assert result.ok is False
    assert result.status == STATUS_BLOCKED_CANONICAL_INPUT_AUTHORITY_ABSENT
    assert result.runtime_mutated is False
    assert result.archive_mutated is False
    assert result.persisted is False
    assert result.capital_slot_state_persisted is False
    assert result.transition_passthrough is original
    assert result.transition_identity_proven is True
    assert not list(tmp_path.iterdir())


def test_partial_extract_fail_closed_even_with_transition_passthrough() -> None:
    class _Inter:
        transition_decision = TransitionDecision(True, "NOOP", False)

    assert try_extract_double_play_decision_inputs_from_replay_intermediate_v1(_Inter()) is None
    out = classify_double_play_canonical_inputs_v1(None)
    assert out.exportable is False
    assert "HARD_STOP_DOUBLE_PLAY" in (out.error_code or "")


def test_bundle_extract_requires_all_seven() -> None:
    transition = TransitionDecision(True, "NOOP", False)
    survival = SurvivalEnvelopeDecision(
        status=SurvivalEnvelopeStatus.OK,
        pre_authorization_eligible=True,
        block_reasons=(),
        live_authorization=False,
    )
    projection = StrategySuitabilityProjection(
        strategy_id="s",
        strategy_family="f",
        suitability_class=SuitabilityClass.UNKNOWN_SUITABILITY,
        side_compatibility=SideCompatibility.UNKNOWN,
        eligible_for_long_bull_pool=False,
        eligible_for_short_bear_pool=False,
        eligible_for_neutral_pool=False,
        block_reasons=(),
        missing_inputs=(),
        reason="test",
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
        status=FuturesReadinessStatus.DATA_READY,
        ready_for_downstream_model_use=True,
        ready_for_dynamic_scope=True,
        ready_for_capital_slot=True,
        ready_for_suitability=True,
        ready_for_survival_envelope=True,
        block_reasons=(),
        missing_inputs=(),
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
    bundle = PureStackDisplayDecisionBundleV1(
        schema_version="productive_pure_stack_display_decision_bundle.v1",
        capability_id=CAPABILITY_ID,
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

    class _Inter:
        display_decision_bundle = bundle

    extracted = try_extract_double_play_decision_inputs_from_replay_intermediate_v1(_Inter())
    assert extracted is not None
    assert extracted["transition"] is transition
    classified = classify_double_play_canonical_inputs_v1(extracted)
    assert classified.exportable is True


def test_atomic_bundle_persist_and_restart_load(tmp_path: Path) -> None:
    # Persistence helper is only used when a complete bundle exists (Owner path).
    # Here we prove atomic write/load mechanics with a synthetic complete bundle.
    transition = TransitionDecision(True, "NOOP", False)
    survival = SurvivalEnvelopeDecision(
        status=SurvivalEnvelopeStatus.BLOCKED,
        pre_authorization_eligible=False,
        block_reasons=(),
        live_authorization=False,
    )
    projection = StrategySuitabilityProjection(
        strategy_id="s",
        strategy_family=None,
        suitability_class=SuitabilityClass.UNKNOWN_SUITABILITY,
        side_compatibility=SideCompatibility.UNKNOWN,
        eligible_for_long_bull_pool=False,
        eligible_for_short_bear_pool=False,
        eligible_for_neutral_pool=False,
        block_reasons=(),
        missing_inputs=("x",),
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
        ratchet_target=1.0,
        can_ratchet=False,
        block_reasons=(),
        reason="n",
        live_authorization=False,
    )
    release = CapitalSlotReleaseDecision(
        status=CapitalSlotStatus.ACTIVE,
        released=False,
        release_reason=None,
        block_reasons=(),
        reason="n",
        live_authorization=False,
        authorizes_new_future_selection=False,
        authorizes_new_trade=False,
    )
    composition = DoublePlayCompositionDecision(
        status=DoublePlayCompositionStatus.BLOCKED,
        block_reasons=(),
        reason="n",
        live_authorization=False,
    )
    bundle = PureStackDisplayDecisionBundleV1(
        schema_version="productive_pure_stack_display_decision_bundle.v1",
        capability_id=CAPABILITY_ID,
        owner="test",
        cycle_id="cycle-1",
        cycle_index=1,
        instrument_id="SATS-USDT-SWAP",
        trading_epoch=2,
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
    path, digest = persist_pure_stack_display_decision_bundle_atomic_v1(
        state_root=tmp_path, bundle=bundle
    )
    assert path.is_file()
    loaded = load_pure_stack_display_decision_bundle_payload_v1(tmp_path)
    assert loaded["bundle_digest"] == digest
    assert loaded["cycle_id"] == "cycle-1"
    assert "decisions" in loaded
    # Restart: reload yields same digest
    loaded2 = load_pure_stack_display_decision_bundle_payload_v1(tmp_path)
    assert loaded2["bundle_digest"] == digest


def test_no_resultv1_mapping_or_fixture_imports_in_package() -> None:
    forbidden_tokens = (
        "build_offline_replay_futures_input_snapshot",
        "def _survival_envelope",
        "def _suitability_input",
        "def _capital_config",
        "evaluate_survival_assessment_v1",
        "evaluate_suitability_binding_v1",
        "evaluate_double_play_composition_matrix_v1",
        "from trading.master_v2.offline_double_play_scenario_replay_v0",
        "from src.webui.double_play_dashboard_display_json_route_v0",
    )
    for path in PKG.glob("*.py"):
        src = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in src, f"{path.name} contains forbidden token {token}"


def test_integrated_replay_assigns_transition_decision_passthrough() -> None:
    src = INTEGRATED.read_text(encoding="utf-8")
    assert "transition_decision: Optional[TransitionDecision] = None" in src
    assert "transition_decision=transition," in src
    # Must not rebuild from state_switch fields for the Decision object.
    tree = ast.parse(src)
    assign_texts = []
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "transition_decision":
            assign_texts.append(ast.unparse(node.value))
    assert "transition" in assign_texts
    assert not any("StateSwitchEvidence" in t for t in assign_texts)


def test_bridge_retains_intermediate_and_cycle_session_exports_it() -> None:
    bridge_src = BRIDGE.read_text(encoding="utf-8")
    assert "last_replay_intermediate" in bridge_src
    assert "state.last_replay_intermediate = replay.intermediate" in bridge_src
    assert "run_pure_stack_display_decision_host_cycle_v1" in bridge_src
    cycle_src = CYCLE_SESSION.read_text(encoding="utf-8")
    assert "replay_intermediate=None" not in cycle_src
    assert 'getattr(state, "last_replay_intermediate", None)' in cycle_src


def test_producer_symbols_are_pure_stack_only() -> None:
    # Binding module must call only the seven Pure-Stack producers.
    src = (PKG / "producers_binding_v1.py").read_text(encoding="utf-8")
    assert "evaluate_futures_input_snapshot" in src
    assert "evaluate_survival_envelope" in src
    assert "project_strategy_suitability" in src
    assert "evaluate_capital_slot_ratchet" in src
    assert "evaluate_capital_slot_release" in src
    assert "compose_double_play_decision" in src
    assert "evaluate_survival_assessment_v1" not in src
    assert "SurvivalResultV1" not in src


def test_dashboard_consumer_gate_still_hard_stop_without_bundle() -> None:
    out = classify_double_play_canonical_inputs_v1({})
    assert out.exportable is False
    assert out.error_code == "HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH"


def test_producer_bindings_invoke_all_seven_pure_stack_producers() -> None:
    """Unit binding proof: wrappers call Pure-Stack producers (test-local inputs only)."""
    from tests.trading.master_v2.test_double_play_pure_stack_contract import (
        _cs_cfg_ok,
        _cs_state_ok,
        _env_ok,
        _fi_snapshot,
        _ii_all,
        _suit_in,
    )

    fi = produce_futures_input_readiness_v1(_fi_snapshot())
    assert isinstance(fi, FuturesInputReadinessDecision)

    transition = TransitionDecision(True, "NOOP", False)
    survival = produce_survival_envelope_decision_v1(_env_ok())
    assert isinstance(survival, SurvivalEnvelopeDecision)

    meta = StrategyMetadata(
        strategy_id="binding-test",
        strategy_family="double_play",
        declared_side=SideCompatibility.BOTH,
        explicit_side_evidence=True,
    )
    suit = produce_suitability_projection_decision_v1(
        _suit_in(meta, bool(survival.pre_authorization_eligible))
    )
    assert isinstance(suit, SuitabilityProjectionDecision)
    assert _ii_all() is not None

    ratchet = produce_capital_slot_ratchet_v1(_cs_cfg_ok(), _cs_state_ok())
    release = produce_capital_slot_release_v1(_cs_cfg_ok(), _cs_state_ok())
    assert isinstance(ratchet, CapitalSlotRatchetDecision)
    assert isinstance(release, CapitalSlotReleaseDecision)

    composition = produce_composition_decision_v1(
        transition=transition,
        resulting_side_state=SideState.NEUTRAL_OBSERVE,
        survival=survival,
        suitability=suit,
        requested_side=RequestedSide.NEUTRAL_OBSERVE,
        capital_slot_ratchet=ratchet,
        capital_slot_release=release,
    )
    assert isinstance(composition, DoublePlayCompositionDecision)


def test_export_accepts_non_none_replay_intermediate_and_keeps_dp_hard_stop(
    tmp_path: Path,
) -> None:
    from src.ops.productive_decision_host_active_archive_three_family_binding_v1.family_export_adapter_v1 import (
        export_families_after_runtime_commit_v1,
    )
    from src.ops.productive_decision_host_active_archive_three_family_binding_v1.models_v1 import (
        ArchiveBindingV1,
    )
    from src.ops.productive_decision_host_active_archive_three_family_binding_v1.state_root_layout_v1 import (
        materialize_state_root_layout_v1,
    )

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
        writable=True,
    )

    class _Inter:
        transition_decision = TransitionDecision(True, "NOOP", False)

    families = export_families_after_runtime_commit_v1(
        state_roots=state_roots,
        archive=archive,
        cycle_id="export-cycle-1",
        cycle_index=0,
        dynamic_scope_persisted=False,
        evidence_payload=None,
        replay_intermediate=_Inter(),
    )
    assert "double_play" in families
    dp = families["double_play"]
    assert dp.exportable is False
    assert dp.error_code == "HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH"
    assert not Path(archive.double_play_sibling_path).is_file()
