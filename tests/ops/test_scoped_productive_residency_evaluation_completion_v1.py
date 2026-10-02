"""B06 scoped productive residency evaluation completion (GHV_B06 closure)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap21_to_cap23_productive_persistence_v1 import (
    run_cap21_to_cap23_persist_productive_v1,
)
from src.ops.peak_trade_economic_ranking_runtime_v1.synthesize_ready_features_v1 import (
    synthesize_ready_feature_production_snapshot_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import STATE_SELECTED_ACTIVE
from src.ops.single_selected_future_policy_v1.residency_eligibility_gate_v1 import (
    Cap23ResidencyEligibilityGateConfigV1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.constants_v1 import (
    EVENTS_FILENAME,
    STATE_COMPLETED,
    TOP20_EVALUATION_RESIDENCY_ENABLED,
)
from src.ops.top20_opportunity_evaluation_residency_v1.models_v1 import ResidencyRuntimeConfigV1
from src.ops.top20_opportunity_evaluation_residency_v1.persistence_v1 import load_store_v1
from src.ops.top20_opportunity_evaluation_residency_v1.scoped_productive_residency_evaluation_completion_v1 import (
    ScopedResidencyIntegratedEvaluationConfigV1,
    run_scoped_productive_residency_evaluation_completion_v1,
)
from tests.ops._productive_economic_md_inject_helpers_v1 import (
    injected_economic_md_source_for_venue_native_ids_v1,
)
from tests.ops.test_cap23_residency_eligibility_gate_v1 import (
    OBSERVED_UNIX,
    REPO_SHA,
    SOURCE_EVENT,
    _perp,
    _ranking,
)


@pytest.fixture
def residency_pin_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.ops.top20_opportunity_evaluation_residency_v1.constants_v1.TOP20_EVALUATION_RESIDENCY_ENABLED",
        True,
    )


def _acq(inst_id: str = "ETH-USDT-SWAP"):
    from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
        EeaUniverseAcquisitionResultV1,
    )

    row = _perp(inst_id)
    return EeaUniverseAcquisitionResultV1(
        ok=True,
        host="eea.okx.com",
        venue="okx_eea",
        source_kind="okx_eea_public_instruments",
        source_event_time=SOURCE_EVENT,
        instruments_payload={"code": "0", "msg": "", "data": [row]},
        mark_price_payload={
            "code": "0",
            "msg": "",
            "data": [{"instId": inst_id, "markPx": "100.5"}],
        },
        endpoints_used=("/api/v5/public/instruments",),
        methods_used=("GET",),
        post_count="0",
        request_count=2,
        venue_live_contact=False,
        failure_codes=(),
        provenance={"test": True},
    )


def test_productive_completion_produces_single_witness_in_canonical_store(
    tmp_path: Path, residency_pin_on: pytest.MonkeyPatch
) -> None:
    inst = "ETH-USDT-SWAP"
    ranking = _ranking(inst)
    res_root = tmp_path / "residency"
    cfg = ResidencyRuntimeConfigV1(enabled=True, max_pending=5, duration_seconds=600.0)
    from src.ops.top20_opportunity_evaluation_residency_v1.residency_engine_v1 import (
        observe_valid_cap22_ranking_snapshot_v1,
        run_scheduler_tick_v1,
    )

    observe_valid_cap22_ranking_snapshot_v1(
        state_root=res_root,
        ranking_snapshot=ranking,
        config=cfg,
        now_unix=OBSERVED_UNIX - 10.0,
    )
    run_scheduler_tick_v1(state_root=res_root, config=cfg, now_unix=OBSERVED_UNIX - 9.0)
    uni = {
        "instruments": [
            {
                "canonical_instrument_id": ranking["ranked_candidates"][0][
                    "canonical_instrument_id"
                ],
                "venue_native_inst_id": inst,
            }
        ]
    }

    def _stub_eval(_native: str, _iid: str, _cfg: object, _ws: Path) -> tuple[bool, str]:
        return True, "PRE_EXTERNAL_EFFECT"

    result = run_scoped_productive_residency_evaluation_completion_v1(
        residency_state_root=res_root,
        residency_config=cfg,
        universe_snapshot=uni,
        producer_observed_at_unix=OBSERVED_UNIX - 8.0,
        integrated_evaluation=ScopedResidencyIntegratedEvaluationConfigV1(
            dataset_root=tmp_path,
            repository_sha=REPO_SHA,
        ),
        evaluation_disposition_fn=_stub_eval,
        scheduler_tick_unix=OBSERVED_UNIX - 7.0,
    )
    assert result.witnesses_applied == 1
    store = load_store_v1(res_root)
    states = [r.state for r in store.records]
    assert any(s == STATE_COMPLETED for s in states), states
    assert result.ok is True
    events = (res_root / EVENTS_FILENAME).read_text(encoding="utf-8")
    assert "EVALUATION_OBSERVED" in events


def test_cap21_23_gate_fail_closed_without_integrated_evaluation(
    tmp_path: Path, residency_pin_on: pytest.MonkeyPatch
) -> None:
    inst = "ETH-USDT-SWAP"
    acq = _acq(inst)
    md = injected_economic_md_source_for_venue_native_ids_v1([inst])
    gate = Cap23ResidencyEligibilityGateConfigV1(
        enabled=True,
        scoped_productive_activation=True,
    )
    out = run_cap21_to_cap23_persist_productive_v1(
        acquisition=acq,
        store=tmp_path / "store",
        repository_sha=REPO_SHA,
        observed_unix=OBSERVED_UNIX,
        session_id_prefix="b06-fail",
        economic_md_public_source=md,
        residency_runtime_config=ResidencyRuntimeConfigV1(enabled=True),
        cap23_residency_eligibility_gate=gate,
        scoped_top20_evaluation_residency_v1=True,
        scoped_residency_integrated_evaluation=None,
    )
    assert out.ok is False
    assert "CAP22_RESIDENCY_EVALUATION_COMPLETION_FAIL_CLOSED" in out.status


def test_cap21_23_productive_path_with_stub_eval_selects_active(
    tmp_path: Path, residency_pin_on: pytest.MonkeyPatch, monkeypatch: pytest.MonkeyPatch
) -> None:
    inst = "ETH-USDT-SWAP"
    acq = _acq(inst)
    md = injected_economic_md_source_for_venue_native_ids_v1([inst])
    gate = Cap23ResidencyEligibilityGateConfigV1(
        enabled=True,
        scoped_productive_activation=True,
    )

    import src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap21_to_cap23_productive_persistence_v1 as cap21_mod
    from src.ops.top20_opportunity_evaluation_residency_v1.scoped_productive_residency_evaluation_completion_v1 import (
        run_scoped_productive_residency_evaluation_completion_v1 as real_completion,
    )

    def _completion_with_stub(**kwargs: object):
        kwargs = dict(kwargs)
        kwargs["evaluation_disposition_fn"] = lambda *_a: (True, "PRE_EXTERNAL_EFFECT")
        return real_completion(**kwargs)

    monkeypatch.setattr(
        cap21_mod, "run_scoped_productive_residency_evaluation_completion_v1", _completion_with_stub
    )

    out = run_cap21_to_cap23_persist_productive_v1(
        acquisition=acq,
        store=tmp_path / "store",
        repository_sha=REPO_SHA,
        observed_unix=OBSERVED_UNIX,
        session_id_prefix="b06-pass",
        economic_md_public_source=md,
        residency_runtime_config=ResidencyRuntimeConfigV1(enabled=True),
        cap23_residency_eligibility_gate=gate,
        scoped_top20_evaluation_residency_v1=True,
        scoped_residency_integrated_evaluation=ScopedResidencyIntegratedEvaluationConfigV1(
            dataset_root=tmp_path,
            repository_sha=REPO_SHA,
        ),
    )

    assert out.ok is True
    assert out.selection is not None
    assert out.selection.state == STATE_SELECTED_ACTIVE
    assert out.selection.venue_native_id == inst
