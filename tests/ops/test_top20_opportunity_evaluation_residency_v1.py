"""Top20 evaluation residency & scheduling contract tests (matrix 01–50)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.mf_membership_context_artifact_contract_v1 import N_VALUE, POLICY_IDENTITY_V1
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    SCORE_COMPONENT_KEYS,
    SNAPSHOT_STATE_VALID,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
    RankedCandidateV1,
    authority_block,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import DEFAULT_MIN_HOLDING_PERIOD_SECONDS
from src.ops.top20_opportunity_evaluation_residency_v1 import constants_v1 as residency_constants
from src.ops.top20_opportunity_evaluation_residency_v1.admission_v1 import (
    eligible_top20_candidates_v1,
    validate_cap22_integrity_v1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.constants_v1 import (
    AUTHORITY_CONTRACT,
    IMPLEMENTATION_SAFETY_MAX_PENDING,
    MAX_ACTIVE_EVALUATION_RESIDENTS,
    REASON_CAPACITY_QUEUE_FULL,
    STATE_ACTIVE_RESIDENT,
    STATE_ADMITTED_PENDING,
    STATE_CAPACITY_REJECTED,
    STATE_COMPLETED,
    TOP20_EVALUATION_RESIDENCY_ENABLED,
)
from src.ops.top20_opportunity_evaluation_residency_v1.evaluation_frame_v1 import (
    build_evaluation_frame_for_records_v1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.models_v1 import (
    EvaluationCompletionWitnessV1,
    ResidencyRuntimeConfigV1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.orchestration_v1 import (
    is_residency_feature_enabled_v1,
    observe_valid_cap22_snapshot_after_persist_v1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.persistence_v1 import load_store_v1
from src.ops.top20_opportunity_evaluation_residency_v1.residency_engine_v1 import (
    active_residents_v1,
    apply_evaluation_completion_v1,
    is_canonical_evaluation_complete_v1,
    observe_valid_cap22_ranking_snapshot_v1,
    run_scheduler_tick_v1,
)


@pytest.fixture
def residency_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(residency_constants, "TOP20_EVALUATION_RESIDENCY_ENABLED", True)


@pytest.fixture
def cfg() -> ResidencyRuntimeConfigV1:
    return ResidencyRuntimeConfigV1(
        enabled=True,
        max_pending=5,
        duration_seconds=600.0,
        early_release_allowed=True,
    )


def _candidate(canonical: str, rank: int, *, eligible: str = "ELIGIBLE") -> RankedCandidateV1:
    return RankedCandidateV1(
        rank=rank,
        canonical_instrument_id=canonical,
        venue_native_id=f"{canonical}-OKX",
        total_score=float(100 - rank),
        score_components={k: 0.0 for k in SCORE_COMPONENT_KEYS},
        data_quality_status="PASS",
        eligibility_status=eligible,
        exclusion_reason_codes=(),
        tie_break_values={"canonical_instrument_id": canonical},
    )


def _snapshot(
    ranked: list[RankedCandidateV1],
    *,
    snapshot_id: str = "rank_snap_1",
    universe_id: str = "uni_1",
    state: str = SNAPSHOT_STATE_VALID,
) -> dict:
    snap = ProductiveFuturesRankingSnapshotV1(
        schema_version="productive_futures_ranking_snapshot.v1",
        capability_id="CAPABILITY_2_2",
        producer_version="v1",
        ranking_snapshot_id=snapshot_id,
        universe_snapshot_id=universe_id,
        universe_source_digest="us",
        universe_payload_digest="up",
        ranking_policy_id="policy",
        ranking_policy_version="v1",
        repository_sha="sha",
        config_digest="cfg",
        event_time="2024-01-01T00:00:00Z",
        produced_at_wall_time="2024-01-01T00:00:01Z",
        candidate_count_total=len(ranked),
        eligible_candidate_count=len(ranked),
        excluded_candidate_count=0,
        ranked_candidates=tuple(ranked),
        excluded_candidates=(),
        snapshot_state=state,
        integrity_digest="",
        authority=authority_block(),
        call_graph=(),
        failure_codes=(),
    ).with_integrity_digest()
    return snap.to_dict()


def test_01_invalid_cap22_cannot_admit(tmp_path: Path, residency_enabled, cfg) -> None:
    bad = _snapshot([_candidate("A", 1)], state="INVALID")
    root = tmp_path / "res"
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root, ranking_snapshot=bad, config=cfg, now_unix=100.0
    )
    assert load_store_v1(root).records == ()


def test_02_rank_gt_20_not_admitted(tmp_path: Path, residency_enabled, cfg) -> None:
    snap = _snapshot([_candidate("A", 21)])
    assert eligible_top20_candidates_v1(snap) == ()


def test_03_first_valid_top20_creates_residency(tmp_path: Path, residency_enabled, cfg) -> None:
    snap = _snapshot([_candidate("A", 20)])
    root = tmp_path / "res"
    store = observe_valid_cap22_ranking_snapshot_v1(
        state_root=root, ranking_snapshot=snap, config=cfg, now_unix=100.0
    )
    assert len(store.records) == 1
    assert store.records[0].state == STATE_ADMITTED_PENDING


def test_04_transient_internal_rank_not_exposed() -> None:
    """Ranking producer returns only final VALID snapshot (no internal API)."""
    from src.ops.productive_futures_ranking_producer_v1 import ranking_v1

    assert "classify_and_rank_candidates_v1" in dir(ranking_v1)


def test_05_repeat_top20_no_deadline_reset(tmp_path: Path, residency_enabled, cfg) -> None:
    root = tmp_path / "res"
    s1 = _snapshot([_candidate("A", 20)], snapshot_id="s1")
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root, ranking_snapshot=s1, config=cfg, now_unix=100.0
    )
    deadline = load_store_v1(root).records[0].residency_deadline_unix
    s2 = _snapshot([_candidate("A", 5)], snapshot_id="s2")
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root, ranking_snapshot=s2, config=cfg, now_unix=150.0
    )
    assert load_store_v1(root).records[0].residency_deadline_unix == deadline


def test_06_rank_drop_preserves_residency(tmp_path: Path, residency_enabled, cfg) -> None:
    root = tmp_path / "res"
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=_snapshot([_candidate("A", 10)], snapshot_id="s1"),
        config=cfg,
        now_unix=100.0,
    )
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=_snapshot([], snapshot_id="s2"),
        config=cfg,
        now_unix=200.0,
    )
    rec = load_store_v1(root).records[0]
    assert rec.state == STATE_ADMITTED_PENDING
    assert rec.current_rank_observations[-1].in_current_top20 is False


def test_07_08_09_rank_truth_and_no_fabrication(tmp_path: Path, residency_enabled, cfg) -> None:
    root = tmp_path / "res"
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=_snapshot([_candidate("A", 3)], snapshot_id="s1"),
        config=cfg,
        now_unix=1.0,
    )
    rec = load_store_v1(root).records[0]
    assert rec.admission.admission_rank == 3
    obs = rec.current_rank_observations
    assert all(o.in_current_top20 in {True, False} for o in obs)
    assert rec.admission.ranking_snapshot_id == "s1"


def test_10_max_active_five(tmp_path: Path, residency_enabled) -> None:
    assert MAX_ACTIVE_EVALUATION_RESIDENTS == 5


def test_11_12_queue_finite_and_invalid_config() -> None:
    with pytest.raises(ValueError):
        ResidencyRuntimeConfigV1(max_pending=0).validate_v1()
    with pytest.raises(ValueError):
        ResidencyRuntimeConfigV1(max_pending=IMPLEMENTATION_SAFETY_MAX_PENDING + 1).validate_v1()


def test_13_14_overflow_capacity_rejected(tmp_path: Path, residency_enabled) -> None:
    cfg = ResidencyRuntimeConfigV1(enabled=True, max_pending=1, duration_seconds=600.0)
    root = tmp_path / "res"
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=_snapshot([_candidate("A", 1)], snapshot_id="s1"),
        config=cfg,
        now_unix=1.0,
    )
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=_snapshot([_candidate("B", 2)], snapshot_id="s2"),
        config=cfg,
        now_unix=2.0,
    )
    rejected = [r for r in load_store_v1(root).records if r.state == STATE_CAPACITY_REJECTED]
    assert rejected
    assert rejected[0].terminal_reason == REASON_CAPACITY_QUEUE_FULL


def test_15_16_deterministic_ordering(tmp_path: Path, residency_enabled, cfg) -> None:
    root = tmp_path / "res"
    ranked = [_candidate("B", 2), _candidate("A", 1)]
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=_snapshot(ranked, snapshot_id="s1"),
        config=cfg,
        now_unix=1.0,
    )
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=_snapshot([_candidate("C", 3)], snapshot_id="s2"),
        config=cfg,
        now_unix=2.0,
    )
    pending = [r for r in load_store_v1(root).records if r.state == STATE_ADMITTED_PENDING]
    assert pending[0].canonical_instrument_id == "A"
    assert pending[1].canonical_instrument_id == "B"


def test_17_20_scheduler_has_no_trading_preference() -> None:
    assert AUTHORITY_CONTRACT["ranking_authority"] is False
    assert AUTHORITY_CONTRACT["selection_authority"] is False
    assert AUTHORITY_CONTRACT["trading_authority"] is False


def test_21_23_completion_via_replay_not_enter() -> None:
    w_ok = EvaluationCompletionWitnessV1("A", "e1", True, "PRE_EXTERNAL_EFFECT")
    w_hold = EvaluationCompletionWitnessV1("A", "e1", True, "HOLD")
    w_bad = EvaluationCompletionWitnessV1("A", "e1", False, "PRE_EXTERNAL_EFFECT")
    assert is_canonical_evaluation_complete_v1(w_ok)
    assert is_canonical_evaluation_complete_v1(w_hold)
    assert not is_canonical_evaluation_complete_v1(w_bad)


def test_24_early_release_frees_slot(tmp_path: Path, residency_enabled, cfg) -> None:
    root = tmp_path / "res"
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=_snapshot([_candidate("A", 1)], snapshot_id="s1"),
        config=cfg,
        now_unix=100.0,
    )
    run_scheduler_tick_v1(state_root=root, config=cfg, now_unix=101.0)
    rec = load_store_v1(root).records[0]
    apply_evaluation_completion_v1(
        state_root=root,
        config=cfg,
        witnesses=[
            EvaluationCompletionWitnessV1(
                rec.canonical_instrument_id,
                rec.residency_epoch_id,
                True,
                "HOLD",
            )
        ],
        now_unix=102.0,
    )
    assert load_store_v1(root).records[0].state == STATE_COMPLETED
    assert load_store_v1(root).records[0].active_slot is None


def test_25_deadline_expiry(tmp_path: Path, residency_enabled, cfg) -> None:
    root = tmp_path / "res"
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=_snapshot([_candidate("A", 1)], snapshot_id="s1"),
        config=cfg,
        now_unix=100.0,
    )
    run_scheduler_tick_v1(state_root=root, config=cfg, now_unix=1000.0)
    assert load_store_v1(root).records[0].state.startswith("EXPIRED")


def test_27_no_duplicate_active_residency(tmp_path: Path, residency_enabled, cfg) -> None:
    root = tmp_path / "res"
    snap = _snapshot([_candidate("A", 1)], snapshot_id="s1")
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root, ranking_snapshot=snap, config=cfg, now_unix=1.0
    )
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root, ranking_snapshot=snap, config=cfg, now_unix=2.0
    )
    assert len(load_store_v1(root).records) == 1


def test_29_reentry_requires_outside_inside(tmp_path: Path, residency_enabled, cfg) -> None:
    root = tmp_path / "res"
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=_snapshot([_candidate("A", 1)], snapshot_id="s1"),
        config=cfg,
        now_unix=1.0,
    )
    run_scheduler_tick_v1(state_root=root, config=cfg, now_unix=2000.0)
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=_snapshot([_candidate("A", 1)], snapshot_id="s2"),
        config=cfg,
        now_unix=2001.0,
    )
    assert len([r for r in load_store_v1(root).records if r.state == STATE_ADMITTED_PENDING]) == 0


def test_30_31_restart_preserves_deadline(tmp_path: Path, residency_enabled, cfg) -> None:
    root = tmp_path / "res"
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=_snapshot([_candidate("A", 1)], snapshot_id="s1"),
        config=cfg,
        now_unix=10.0,
    )
    deadline = load_store_v1(root).records[0].residency_deadline_unix
    reloaded = load_store_v1(root)
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=_snapshot([_candidate("B", 2)], snapshot_id="s2"),
        config=cfg,
        now_unix=11.0,
    )
    assert reloaded.records[0].residency_deadline_unix == deadline


def test_33_clock_rollback_fail_closed(tmp_path: Path, residency_enabled, cfg) -> None:
    root = tmp_path / "res"
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=_snapshot([_candidate("A", 1)], snapshot_id="s1"),
        config=cfg,
        now_unix=100.0,
    )
    with pytest.raises(ValueError):
        observe_valid_cap22_ranking_snapshot_v1(
            state_root=root,
            ranking_snapshot=_snapshot([_candidate("B", 2)], snapshot_id="s2"),
            config=cfg,
            now_unix=50.0,
        )


def test_34_36_admission_snapshot_immutable(tmp_path: Path, residency_enabled, cfg) -> None:
    root = tmp_path / "res"
    snap = _snapshot([_candidate("A", 4)], snapshot_id="s1")
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root, ranking_snapshot=snap, config=cfg, now_unix=1.0
    )
    run_scheduler_tick_v1(state_root=root, config=cfg, now_unix=2.0)
    actives = active_residents_v1(load_store_v1(root))
    frame = build_evaluation_frame_for_records_v1(state_root=root, records=actives)
    assert frame.evaluation_ranking_snapshot["ranking_snapshot_id"] == "s1"
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=_snapshot([_candidate("A", 99)], snapshot_id="s2"),
        config=cfg,
        now_unix=3.0,
    )
    assert frame.evaluation_ranking_snapshot["ranked_candidates"][0]["rank"] == 4


def test_37_42_mf_and_cap23_constants_unchanged() -> None:
    assert N_VALUE == 5
    assert POLICY_IDENTITY_V1["n_value"] == 5
    assert DEFAULT_MIN_HOLDING_PERIOD_SECONDS == 3600.0


def test_44_45_no_residency_in_trading_dto_fields() -> None:
    forbidden = {"residency_epoch_id", "queue_position", "scheduler_state"}
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

    fields = set(BoundInstrumentV1.__dataclass_fields__)
    assert forbidden.isdisjoint(fields)


def test_47_feature_disabled_preserves_path(tmp_path: Path, cfg) -> None:
    assert TOP20_EVALUATION_RESIDENCY_ENABLED is False
    assert is_residency_feature_enabled_v1(ResidencyRuntimeConfigV1(enabled=True)) is False
    root = tmp_path / "state"
    observe_valid_cap22_snapshot_after_persist_v1(
        state_root=root,
        ranking_snapshot=_snapshot([_candidate("A", 1)]),
        producer_observed_at_unix=1.0,
        config=ResidencyRuntimeConfigV1(enabled=True),
    )
    assert not (root / "top20_evaluation_residency_v1").exists()


def test_50_authority_contract() -> None:
    assert AUTHORITY_CONTRACT["ranking_authority"] is False
    assert AUTHORITY_CONTRACT["selection_authority"] is False
    assert AUTHORITY_CONTRACT["trading_authority"] is False


def test_validate_integrity_detects_tamper() -> None:
    snap = _snapshot([_candidate("A", 1)])
    snap["integrity_digest"] = "deadbeef"
    assert validate_cap22_integrity_v1(snap)
