"""Cap2.3 read-only residency eligibility gate (IMPLEMENT_COHERENT_TARGET_WIRING_V1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.peak_trade_economic_ranking_runtime_v1.synthesize_ready_features_v1 import (
    synthesize_ready_feature_production_snapshot_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    STATE_NO_SELECTION,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    run_single_selected_future_policy_v1,
)
from src.ops.single_selected_future_policy_v1.reason_codes_v1 import SelectionFailureCodeV1
from src.ops.single_selected_future_policy_v1.residency_eligibility_gate_v1 import (
    Cap23ResidencyEligibilityGateConfigV1,
    apply_cap23_residency_eligibility_gate_v1,
    verify_cap23_residency_eligibility_v1,
)
from src.ops.single_selected_future_policy_v1.selection_v1 import produce_single_selected_future_v1
from src.ops.top20_opportunity_evaluation_residency_v1.constants_v1 import (
    STATE_COMPLETED,
    TOP20_EVALUATION_RESIDENCY_ENABLED,
)
from src.ops.top20_opportunity_evaluation_residency_v1.models_v1 import (
    EvaluationCompletionWitnessV1,
    ResidencyRuntimeConfigV1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.persistence_v1 import load_store_v1
from src.ops.top20_opportunity_evaluation_residency_v1.residency_engine_v1 import (
    apply_evaluation_completion_v1,
    observe_valid_cap22_ranking_snapshot_v1,
    run_scheduler_tick_v1,
)


REPO_SHA = "d62eb64ca83e1562b9f8bf7d1506cf65535f51d3"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"


def _perp(inst_id: str = "ETH-USDT-SWAP") -> dict:
    base, quote = inst_id.split("-")[0], "USDT"
    return {
        "instId": inst_id,
        "instType": "SWAP",
        "state": "live",
        "baseCcy": base,
        "quoteCcy": quote,
        "settleCcy": quote,
        "ctType": "linear",
        "ctVal": "0.01",
        "ctValCcy": base,
        "tickSz": "0.01",
        "lotSz": "1",
        "minSz": "1",
        "uly": f"{base}-{quote}",
        "expTime": "",
    }


def _ranking(inst_id: str = "ETH-USDT-SWAP") -> dict:
    uni = produce_governed_futures_universe_v1(
        source_payload={"code": "0", "msg": "", "data": [_perp(inst_id)]},
        mark_price_payload={
            "code": "0",
            "msg": "",
            "data": [{"instId": inst_id, "markPx": "100.5"}],
        },
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    ).snapshot.to_dict()
    return produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        feature_production_snapshot=synthesize_ready_feature_production_snapshot_v1(uni),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    ).snapshot.to_dict()


@pytest.fixture
def residency_pin_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.ops.top20_opportunity_evaluation_residency_v1.constants_v1.TOP20_EVALUATION_RESIDENCY_ENABLED",
        True,
    )


def _seed_completed_residency(
    root: Path,
    *,
    ranking: dict,
) -> EvaluationCompletionWitnessV1:
    cfg = ResidencyRuntimeConfigV1(enabled=True, max_pending=5, duration_seconds=600.0)
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=root,
        ranking_snapshot=ranking,
        config=cfg,
        now_unix=OBSERVED_UNIX - 10.0,
    )
    run_scheduler_tick_v1(state_root=root, config=cfg, now_unix=OBSERVED_UNIX - 9.0)
    rec = load_store_v1(root).records[0]
    witness = EvaluationCompletionWitnessV1(
        rec.canonical_instrument_id,
        rec.residency_epoch_id,
        True,
        "PRE_EXTERNAL_EFFECT",
    )
    apply_evaluation_completion_v1(
        state_root=root,
        config=cfg,
        witnesses=[witness],
        now_unix=OBSERVED_UNIX - 8.0,
    )
    assert load_store_v1(root).records[0].state == STATE_COMPLETED
    return witness


def _produce_active_selection(ranking: dict) -> tuple:
    produced = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        previous_selection=None,
    )
    assert produced.selection.state == STATE_SELECTED_ACTIVE
    return produced


def test_valid_witness_allows_eligibility(tmp_path: Path, residency_pin_on) -> None:
    res_root = tmp_path / "residency"
    ranking = _ranking()
    _seed_completed_residency(res_root, ranking=ranking)
    produced = _produce_active_selection(ranking)
    gate = Cap23ResidencyEligibilityGateConfigV1(
        enabled=True,
        residency_state_root=res_root,
        scoped_productive_activation=True,
    )
    ok, codes, ref = verify_cap23_residency_eligibility_v1(
        selection=produced.selection,
        ranking_snapshot=ranking,
        gate=gate,
        producer_observed_at_unix=OBSERVED_UNIX,
        residency_config=ResidencyRuntimeConfigV1(enabled=True),
    )
    assert ok is True
    assert codes == ()
    assert ref is not None
    assert ref.residency_completion_state == STATE_COMPLETED


def test_missing_witness_fail_closed(tmp_path: Path, residency_pin_on) -> None:
    res_root = tmp_path / "residency"
    ranking = _ranking()
    produced = _produce_active_selection(ranking)
    gate = Cap23ResidencyEligibilityGateConfigV1(
        enabled=True,
        residency_state_root=res_root,
        scoped_productive_activation=True,
    )
    ok, codes, _ = verify_cap23_residency_eligibility_v1(
        selection=produced.selection,
        ranking_snapshot=ranking,
        gate=gate,
        producer_observed_at_unix=OBSERVED_UNIX,
        residency_config=ResidencyRuntimeConfigV1(enabled=True),
    )
    assert ok is False
    assert SelectionFailureCodeV1.RESIDENCY_ELIGIBILITY_RESIDENCY_INCOMPLETE.value in codes


def test_non_terminal_residency_fail_closed(tmp_path: Path, residency_pin_on) -> None:
    res_root = tmp_path / "residency"
    ranking = _ranking()
    cfg = ResidencyRuntimeConfigV1(enabled=True, max_pending=5, duration_seconds=600.0)
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=res_root,
        ranking_snapshot=ranking,
        config=cfg,
        now_unix=OBSERVED_UNIX - 10.0,
    )
    run_scheduler_tick_v1(state_root=res_root, config=cfg, now_unix=OBSERVED_UNIX - 9.0)
    produced = _produce_active_selection(ranking)
    gate = Cap23ResidencyEligibilityGateConfigV1(
        enabled=True,
        residency_state_root=res_root,
        scoped_productive_activation=True,
    )
    ok, codes, _ = verify_cap23_residency_eligibility_v1(
        selection=produced.selection,
        ranking_snapshot=ranking,
        gate=gate,
        producer_observed_at_unix=OBSERVED_UNIX,
        residency_config=cfg,
    )
    assert ok is False
    assert SelectionFailureCodeV1.RESIDENCY_ELIGIBILITY_RESIDENCY_INCOMPLETE.value in codes


def test_stale_witness_fail_closed(tmp_path: Path, residency_pin_on) -> None:
    res_root = tmp_path / "residency"
    ranking = _ranking()
    _seed_completed_residency(res_root, ranking=ranking)
    produced = _produce_active_selection(ranking)
    gate = Cap23ResidencyEligibilityGateConfigV1(
        enabled=True,
        residency_state_root=res_root,
        max_witness_age_seconds=1.0,
        scoped_productive_activation=True,
    )
    ok, codes, _ = verify_cap23_residency_eligibility_v1(
        selection=produced.selection,
        ranking_snapshot=ranking,
        gate=gate,
        producer_observed_at_unix=10_000.0,
        residency_config=ResidencyRuntimeConfigV1(enabled=True),
    )
    assert ok is False
    assert SelectionFailureCodeV1.RESIDENCY_ELIGIBILITY_WITNESS_STALE.value in codes


def test_identity_mismatch_fail_closed(tmp_path: Path, residency_pin_on) -> None:
    res_root = tmp_path / "residency"
    ranking = _ranking("ETH-USDT-SWAP")
    produced = _produce_active_selection(ranking)
    gate = Cap23ResidencyEligibilityGateConfigV1(
        enabled=True,
        residency_state_root=res_root,
        scoped_productive_activation=True,
    )
    ok, codes, _ = verify_cap23_residency_eligibility_v1(
        selection=produced.selection,
        ranking_snapshot=ranking,
        gate=gate,
        producer_observed_at_unix=OBSERVED_UNIX,
        residency_config=ResidencyRuntimeConfigV1(enabled=True),
    )
    assert ok is False
    assert SelectionFailureCodeV1.RESIDENCY_ELIGIBILITY_RESIDENCY_INCOMPLETE.value in codes


def test_gate_fail_closed_blocks_persisted_active_selection(
    tmp_path: Path, residency_pin_on
) -> None:
    sel_root = tmp_path / "selection"
    sel_root.mkdir()
    ranking = _ranking()
    res_root = tmp_path / "top20_evaluation_residency_v1"
    out = run_single_selected_future_policy_v1(
        state_root=sel_root,
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        load_previous_from_state=False,
        residency_eligibility_gate=Cap23ResidencyEligibilityGateConfigV1(
            enabled=True,
            residency_state_root=res_root,
            scoped_productive_activation=True,
        ),
        residency_runtime_config=ResidencyRuntimeConfigV1(enabled=True),
    )
    assert out["ok"] is False
    assert out["state"] == STATE_NO_SELECTION
    assert (
        SelectionFailureCodeV1.RESIDENCY_ELIGIBILITY_RESIDENCY_INCOMPLETE.value
        in out["failure_codes"]
    )


def test_gate_pass_persists_residency_completion_ref(tmp_path: Path, residency_pin_on) -> None:
    sel_root = tmp_path / "selection"
    sel_root.mkdir()
    ranking = _ranking()
    res_root = tmp_path / "top20_evaluation_residency_v1"
    _seed_completed_residency(res_root, ranking=ranking)
    out = run_single_selected_future_policy_v1(
        state_root=sel_root,
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        load_previous_from_state=False,
        residency_eligibility_gate=Cap23ResidencyEligibilityGateConfigV1(
            enabled=True,
            residency_state_root=res_root,
            scoped_productive_activation=True,
        ),
        residency_runtime_config=ResidencyRuntimeConfigV1(enabled=True),
    )
    assert out["ok"] is True
    assert out["state"] == STATE_SELECTED_ACTIVE
    evidence = json.loads(
        (sel_root / "single_selected_future_selection_evidence_v1.json").read_text()
    )
    assert evidence.get("residency_completion_ref") is not None


def test_witness_does_not_write_selection_itself(tmp_path: Path, residency_pin_on) -> None:
    produced = _produce_active_selection(_ranking())
    gated, ref = apply_cap23_residency_eligibility_gate_v1(
        produced=produced,
        ranking_snapshot=_ranking(),
        gate=Cap23ResidencyEligibilityGateConfigV1(enabled=False),
        residency_config=ResidencyRuntimeConfigV1(enabled=False),
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert gated.selection.selection_id == produced.selection.selection_id
    assert ref is None


def test_post_and_external_effect_pins_false() -> None:
    assert POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False


def test_residency_package_has_no_mv2_import() -> None:
    text = Path(
        "src/ops/top20_opportunity_evaluation_residency_v1/residency_engine_v1.py"
    ).read_text()
    assert "master_v2" not in text
    assert "double_play" not in text


def test_default_pin_unchanged() -> None:
    assert TOP20_EVALUATION_RESIDENCY_ENABLED is False
