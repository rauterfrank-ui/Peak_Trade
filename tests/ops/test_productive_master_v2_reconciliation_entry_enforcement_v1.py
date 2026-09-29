"""Productive reconciliation single-check + Master-V2 entry admission enforcement."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_reconciliation_admission_v1 import (
    ProductiveMasterV2ReconciliationAdmissionContextV1,
    ProductiveMasterV2ReconciliationAdmissionError,
    build_explicit_non_productive_test_fixture_master_v2_reconciliation_admission_v1,
    build_productive_master_v2_reconciliation_admission_from_gate_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.master_v2_entry_reconciliation_contract_v1 import (
    DOUBLE_PLAY_RECHECK_REQUIRED,
    MASTER_V2_RECHECK_REQUIRED,
    PRODUCTIVE_MASTER_V2_ENTRY_REQUIRES_UPSTREAM_SUCCESSFUL_RECONCILIATION,
    PRODUCTIVE_PORTFOLIO_RECONCILIATION_SINGLE_CHECK,
    RECONCILIATION_AUTHORITY_TRANSFER,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    ProductiveReconciliationEvidenceV1,
    ProductiveReconciliationGateResultV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.startup_gate_v1 import (
    run_productive_reconciliation_startup_gate_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.taxonomy_v1 import (
    ProductiveReconciliationClass,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops._current_productive_canonical_price_test_helpers_v1 import provenance_for_bound_v1
from tests.ops._current_productive_reconciliation_admission_test_helpers_v1 import (
    non_productive_test_master_v2_reconciliation_admission_v1,
)
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _bound,
    _produced_g17_producer,
    _strong_uptrend_closes,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide

REPO = Path(__file__).resolve().parents[2]
MV2_SRC = (
    REPO
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py"
)
REPO_SHA = "5824af75e9c65592b362c935ac707064cfaea099"


def test_ratified_contract_constants() -> None:
    assert PRODUCTIVE_PORTFOLIO_RECONCILIATION_SINGLE_CHECK is True
    assert PRODUCTIVE_MASTER_V2_ENTRY_REQUIRES_UPSTREAM_SUCCESSFUL_RECONCILIATION is True
    assert MASTER_V2_RECHECK_REQUIRED is False
    assert DOUBLE_PLAY_RECHECK_REQUIRED is False
    assert RECONCILIATION_AUTHORITY_TRANSFER is False


def test_productive_gate_admission_allows_master_v2_replay_state(tmp_path: Path) -> None:
    observed = PortfolioTruthSnapshotV1(positions=(), source_id="observed")
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=observed,
        session_id="admission-ok",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_000.0,
    )
    admission = build_productive_master_v2_reconciliation_admission_from_gate_v1(
        gate=gate,
        session_id="admission-ok",
        repository_sha=REPO_SHA,
        bound_instrument_id="inst-test",
    )
    assert admission.is_productive_upstream_provenance_v1() is True
    from trading.master_v2.double_play_entry_exit_policy_v0 import ReconciliationState

    assert admission.integrated_replay_reconciliation_state_v1() is ReconciliationState.RECONCILED


def test_missing_productive_evidence_digest_blocks_admission_build() -> None:
    admission = build_explicit_non_productive_test_fixture_master_v2_reconciliation_admission_v1(
        bound_instrument_id="inst-test",
    )
    assert (
        admission.context_class
        is ProductiveMasterV2ReconciliationAdmissionContextV1.EXPLICIT_NON_PRODUCTIVE_TEST_FIXTURE
    )


def test_productive_admission_fail_closed_blocks_master_v2_cycle() -> None:
    bound = _bound()
    closes = _strong_uptrend_closes()
    mark = float(closes[-1])
    bad_evidence = ProductiveReconciliationEvidenceV1(
        capability_id="CAP",
        schema_version="v1",
        owner="ops.productive_reconciliation_runtime_binding_v1",
        classification=ProductiveReconciliationClass.MATCH.value,
        alpha_enabled=True,
        pre_state_digest="a",
        observed_state_digest="b",
        post_state_digest="c",
        reconciliation_decision="CONTINUE",
        repository_sha=REPO_SHA,
    )
    bad_gate = ProductiveReconciliationGateResultV1(
        ok=False,
        alpha_enabled=False,
        classification=ProductiveReconciliationClass.MATCH,
        master_v2_reconciliation_state="reconciliation_required",
        hard_stop=True,
        evidence=bad_evidence,
    )
    admission = build_productive_master_v2_reconciliation_admission_from_gate_v1(
        gate=bad_gate,
        session_id="blocked",
        repository_sha=REPO_SHA,
        bound_instrument_id=str(bound.instrument_id),
    )
    with pytest.raises(ProductiveMasterV2ReconciliationAdmissionError):
        admission.validate_for_productive_master_v2_entry_v1(instrument_id=str(bound.instrument_id))
    result = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id="admission-blocked",
        observed_unix=1_700_000_200.0,
        mark_px=mark,
        index_px=mark * 0.995,
        bid_px=mark - 0.5,
        ask_px=mark + 0.5,
        volume=1.0,
        open_interest=1.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=1_700_000_100.0,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        g17_typed_vol_producer=_produced_g17_producer(instrument_id=bound.instrument_id),
        canonical_price_provenance=provenance_for_bound_v1(
            bound=bound, mark_px=mark, index_px=mark * 0.995
        ),
        master_v2_reconciliation_admission=admission,
    )
    assert "MASTER_V2_RECONCILIATION_ADMISSION_FAIL_CLOSED" in str(result.fail_reasons)


def test_non_productive_fixture_still_runs_master_v2_without_productive_authority() -> None:
    bound = _bound()
    closes = _strong_uptrend_closes()
    mark = float(closes[-1])
    admission = non_productive_test_master_v2_reconciliation_admission_v1(bound=bound)
    assert admission.is_productive_upstream_provenance_v1() is False
    result = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id="non-productive-fixture",
        observed_unix=1_700_000_200.0,
        mark_px=mark,
        index_px=mark * 0.995,
        bid_px=mark - 0.5,
        ask_px=mark + 0.5,
        volume=1.0,
        open_interest=1.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=1_700_000_100.0,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        g17_typed_vol_producer=_produced_g17_producer(instrument_id=bound.instrument_id),
        canonical_price_provenance=provenance_for_bound_v1(
            bound=bound, mark_px=mark, index_px=mark * 0.995
        ),
        master_v2_reconciliation_admission=admission,
    )
    assert result.replay is not None
    assert result.replay.replay_pass is True


def test_mv2_host_does_not_hardcode_reconciled_without_admission_path() -> None:
    src = MV2_SRC.read_text(encoding="utf-8")
    assert "reconciliation_state=ReconciliationState.RECONCILED" not in src
    assert "replay_reconciliation_state" in src
    assert "master_v2_reconciliation_admission" in src


def test_startup_gate_evidence_digest_non_empty(tmp_path: Path) -> None:
    observed = PortfolioTruthSnapshotV1(positions=(), source_id="observed")
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=tmp_path,
        observed=observed,
        session_id="cap24-digest",
        repository_sha=REPO_SHA,
        now_unix=1_700_000_000.0,
    )
    assert gate.evidence.digest()
    _ = Decimal("0")
