"""Clean-checkout F1/M9 durable bootstrap (no pre-existing runtime/governance)."""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    build_provenance_from_governed_synthetic_close_mark_and_index_v1,
)


from pathlib import Path

import pytest

from src.governance.f1_m9_productive_apply_durable_ledger_paths_v1 import (
    resolve_canonical_f1_m9_productive_apply_ledger_paths_v1,
    resolve_canonical_f1_m9_threshold_value_authorization_ledger_paths_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_f1_m9_canonical_durable_bootstrap_v1 import (
    ensure_canonical_f1_m9_runtime_applied_seam_materialized_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
    prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from tests.ops.test_current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
    CAPTURE_TS,
    _bound,
    _mark_payload,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_GOVERNANCE = REPO_ROOT / "runtime" / "governance" / "f1_m9_scoped_owner_productive_apply_v1"


@pytest.fixture
def isolated_canonical_f1_m9_ledgers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect canonical ledger paths to tmp (simulates clean checkout)."""
    ledger_root = tmp_path / "f1_m9_scoped_owner_productive_apply_v1"
    ledger_root.mkdir(parents=True)
    apply_path = ledger_root / "apply_ledger.jsonl"
    rev_path = ledger_root / "revocation_ledger.jsonl"
    threshold_path = ledger_root / "threshold_value_authorization_ledger.jsonl"
    threshold_rev_path = ledger_root / "threshold_value_authorization_revocation_ledger.jsonl"

    from src.governance.f1_m9_productive_apply_ledger_v1 import F1M9ProductiveApplyLedgerPathsV1
    from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
        F1M9ThresholdValueAuthorizationLedgerPathsV1,
    )

    apply_paths = F1M9ProductiveApplyLedgerPathsV1(
        apply_ledger_path=apply_path,
        revocation_ledger_path=rev_path,
    )
    threshold_paths = F1M9ThresholdValueAuthorizationLedgerPathsV1(
        threshold_ledger_path=threshold_path,
        threshold_revocation_ledger_path=threshold_rev_path,
    )

    def _apply_resolve(*, repo_root: Path | None = None):
        _ = repo_root
        return apply_paths

    def _threshold_resolve(*, repo_root: Path | None = None):
        _ = repo_root
        return threshold_paths

    monkeypatch.setattr(
        "src.governance.f1_m9_productive_apply_durable_ledger_paths_v1."
        "resolve_canonical_f1_m9_productive_apply_ledger_paths_v1",
        _apply_resolve,
    )
    monkeypatch.setattr(
        "src.governance.f1_m9_productive_apply_durable_ledger_paths_v1."
        "resolve_canonical_f1_m9_threshold_value_authorization_ledger_paths_v1",
        _threshold_resolve,
    )
    return apply_paths, threshold_paths


def test_clean_checkout_bootstrap_materializes_seam_and_idempotent_restart(
    tmp_path: Path,
    isolated_canonical_f1_m9_ledgers: tuple[object, object],
) -> None:
    apply_paths, threshold_paths = isolated_canonical_f1_m9_ledgers
    assert not apply_paths.apply_ledger_path.exists()

    bootstrap = ensure_canonical_f1_m9_runtime_applied_seam_materialized_v1(
        repo_root=REPO_ROOT,
        apply_ledger_paths=apply_paths,
        threshold_ledger_paths=threshold_paths,
    )
    assert bootstrap.status == "BOOTSTRAP_COMPLETE"
    assert apply_paths.apply_ledger_path.is_file()

    bootstrap_again = ensure_canonical_f1_m9_runtime_applied_seam_materialized_v1(
        repo_root=REPO_ROOT,
        apply_ledger_paths=apply_paths,
        threshold_ledger_paths=threshold_paths,
    )
    assert bootstrap_again.status == "ALREADY_MATERIALIZED"

    g17 = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
        evidence_store_root=tmp_path / "g17",
        bound_instrument=_bound(),
        mark_candles_payload=_mark_payload(),
        receive_or_capture_timestamp=CAPTURE_TS,
    )
    closes = tuple(100.0 + i * 0.01 for i in range(80))
    last = float(closes[-1])
    index_px = last * 0.995
    bound = _bound()
    ledger_kw = {
        "f1_m9_productive_apply_ledger_paths": apply_paths,
        "f1_m9_threshold_ledger_paths": threshold_paths,
    }
    cold = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id="clean-checkout-cold",
        observed_unix=1_700_000_100.0,
        mark_px=last,
        index_px=index_px,
        bid_px=last - 0.5,
        ask_px=last + 0.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=1_700_000_000.0,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        g17_typed_vol_producer=g17.producer,
        **ledger_kw,
        canonical_price_provenance=build_provenance_from_governed_synthetic_close_mark_and_index_v1(
            venue_native_id=str(bound.venue_native_id or bound.instrument_id),
            mark_px=float(last),
            index_px=float(index_px),
        ),
    )
    assert cold.input_blocker == ""
    assert cold.outgoing_cursor is not None

    warm = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id="clean-checkout-restart",
        observed_unix=1_700_000_160.0,
        mark_px=last,
        index_px=index_px,
        bid_px=last - 0.5,
        ask_px=last + 0.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=1_700_000_060.0,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        incoming_cursor=cold.outgoing_cursor,
        g17_typed_vol_producer=g17.producer,
        **ledger_kw,
        canonical_price_provenance=build_provenance_from_governed_synthetic_close_mark_and_index_v1(
            venue_native_id=str(bound.venue_native_id or bound.instrument_id),
            mark_px=float(last),
            index_px=float(index_px),
        ),
    )
    assert warm.cursor_restore_status == "restored"
    assert warm.outgoing_cursor is not None
    assert warm.outgoing_cursor.trading_epoch == cold.outgoing_cursor.trading_epoch + 1


def test_canonical_paths_resolve_without_local_runtime_artifacts() -> None:
    if RUNTIME_GOVERNANCE.is_dir():
        pytest.skip("Local runtime/governance present; path resolution only.")
    paths = resolve_canonical_f1_m9_productive_apply_ledger_paths_v1(repo_root=REPO_ROOT)
    assert not paths.apply_ledger_path.exists()
