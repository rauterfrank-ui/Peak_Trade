"""M01 productive F1/M9 closure: per-cycle G17 bind on LANE_1 (INJ-001 regression lock)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ops.run_current_productive_policy_governed_live_c1_pre_external_convergence_v1 import (
    _build_f1_m9_evaluator,
)
from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
    STATUS_DENIED,
    STATUS_WIRED,
    evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1,
)
from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_g17_typed_vol_cmc_bind_v1 as g17_bind_mod,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops.test_current_productive_g17_typed_vol_mark_history_checkpoint_v1 import (
    _apply,
    _sixty_one_samples,
)

M01_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py"
)


def _bound_lane() -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id="BTC-USDT-SWAP-CANON",
        venue_native_id="BTC-USDT-SWAP",
        ranking_snapshot_id="rank-m01-f1m9",
        ranking_integrity_digest="rank-m01-f1m9-digest",
        universe_snapshot_id="uni-m01-f1m9",
        selection_id="sel-m01-f1m9",
        selection_integrity_digest="sel-m01-f1m9-digest",
        selection_state="SELECTED",
    )


def test_m01_f1_m9_build_path_does_not_use_test_volatility_fixtures() -> None:
    src = M01_SCRIPT.read_text(encoding="utf-8")
    assert "tests." not in src
    assert "_valid_estimate" not in src
    assert "_bound_context" not in src
    assert "apply_current_productive_g17_typed_vol_cmc_bind_v1" in src
    assert "evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1" in src


def test_m01_f1_m9_evaluator_wires_with_lane1_g17_producer(tmp_path: Path) -> None:
    created = _apply(tmp_path / "g17", samples=_sixty_one_samples())
    assert created.producer is not None
    evaluator = _build_f1_m9_evaluator(
        ledger_root=tmp_path / "f1_m9",
        g17_producers={"LANE_1": created.producer},
        bound=_bound_lane(),
    )
    result = evaluator(cycle_index=1)
    assert result.wiring_status == STATUS_WIRED
    assert result.presence_gate is not None
    assert result.presence_gate.typed_estimate_present is True


def test_m01_f1_m9_bind_uses_lane1_producer_before_consume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = _apply(tmp_path / "g17", samples=_sixty_one_samples())
    assert created.producer is not None
    lane_producer = created.producer
    real_apply = g17_bind_mod.apply_current_productive_g17_typed_vol_cmc_bind_v1
    real_eval = evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1
    call_order: list[str] = []
    seen_producers: list[object] = []

    def _apply_wrap(context, *, producer):
        call_order.append("g17_cmc_bind")
        seen_producers.append(producer)
        return real_apply(context, producer=producer)

    def _eval_wrap(**kwargs):
        call_order.append("f1_m9_evaluate")
        return real_eval(**kwargs)

    monkeypatch.setattr(
        g17_bind_mod, "apply_current_productive_g17_typed_vol_cmc_bind_v1", _apply_wrap
    )
    monkeypatch.setattr(
        "src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1."
        "evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1",
        _eval_wrap,
    )
    evaluator = _build_f1_m9_evaluator(
        ledger_root=tmp_path / "f1_m9",
        g17_producers={"LANE_1": lane_producer},
        bound=_bound_lane(),
    )
    result = evaluator(cycle_index=1)
    assert result.wiring_status == STATUS_WIRED
    assert call_order == ["g17_cmc_bind", "f1_m9_evaluate"]
    assert len(seen_producers) == 1
    assert seen_producers[0] is lane_producer


def test_m01_f1_m9_evaluator_none_lane_producer_denied_fail_closed(tmp_path: Path) -> None:
    evaluator = _build_f1_m9_evaluator(
        ledger_root=tmp_path / "f1_m9",
        g17_producers={"LANE_1": None},
        bound=_bound_lane(),
    )
    result = evaluator(cycle_index=0)
    assert result.wiring_status == STATUS_DENIED


def test_m01_f1_m9_evaluator_repeated_cycle_same_producer_handle_still_wires(
    tmp_path: Path,
) -> None:
    """CURRENT contract: one producer handle per run; no per-cycle re-ingest on F1 gate path."""
    created = _apply(tmp_path / "g17", samples=_sixty_one_samples())
    assert created.producer is not None
    producer = created.producer
    evaluator = _build_f1_m9_evaluator(
        ledger_root=tmp_path / "f1_m9",
        g17_producers={"LANE_1": producer},
        bound=_bound_lane(),
    )
    first = evaluator(cycle_index=1)
    second = evaluator(cycle_index=2)
    assert first.wiring_status == STATUS_WIRED
    assert second.wiring_status == STATUS_WIRED
    assert producer.output_port_v1().estimate is not None
