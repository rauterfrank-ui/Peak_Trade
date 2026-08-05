"""Focused tests for productive decision-host ↔ active-archive three-family binding."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.canonical_local_launcher_and_process_supervision_v1.constants_v1 import (
    AUTHORIZED_MODES,
    MODE_DASHBOARD_ONLY,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.archive_binding_v1 import (
    bind_active_archive_v1,
    resolve_selected_instrument_from_archive_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.authorization_v1 import (
    ProductiveHostAuthorizationError,
    prove_network_and_order_boundary_v1,
    require_owner_go_v1,
    require_repository_sha_match_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH,
    O2_AUTHORIZED_MODES_REQUIRED,
    PRODUCTIVE_HOST_SYMBOL,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.cycle_session_v1 import (
    run_productive_host_smoke_session_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.double_play_input_gate_v1 import (
    classify_double_play_canonical_inputs_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.state_root_layout_v1 import (
    ProductiveHostSingleWriterV1,
    materialize_state_root_layout_v1,
)


REPO_SHA = "1989e7e4dc0697d049a25c4b3d84baf27016ecf5"


def _universe_payload(symbol: str = "SATS-USDT-SWAP") -> dict[str, object]:
    return {
        "schema_name": "universe_selection_readmodel.v1",
        "schema_version": 1,
        "generated_at": "2026-07-24T21:48:23Z",
        "source_run_id": "okx_governed_test_fixture",
        "source_stage": "paper",
        "fixture_marked": False,
        "non_authorizing": True,
        "evidence": {},
        "market_snapshot": {},
        "missing_truth": {
            "future_detail": "AVAILABLE",
            "orders_fills_pnl": "NOT_PERSISTED",
            "ranking": "PERSISTED",
            "selected_future": "PERSISTED",
            "universe": "PERSISTED",
        },
        "ranking": [
            {
                "row_id": f"r-c-{symbol}",
                "symbol": symbol,
                "rank": 1,
                "notes": "test",
            }
        ],
        "universe": [
            {
                "row_id": f"c-{symbol}",
                "symbol": symbol,
                "rank": 1,
                "exchange": "okx",
                "notes": "test",
            }
        ],
        "selected_future": {
            "truth_status": "PERSISTED",
            "symbol": symbol,
            "row_id": f"s-c-{symbol}",
            "rank": 1,
            "selection_reason": "upstream_explicit_selection",
            "notes": "test",
        },
    }


def _seed_archive(tmp_path: Path, symbol: str = "SATS-USDT-SWAP") -> Path:
    archive = tmp_path / "archive"
    readmodels = archive / "readmodels"
    readmodels.mkdir(parents=True)
    (readmodels / "universe_selection_readmodel.v1.json").write_text(
        json.dumps(_universe_payload(symbol), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return archive


def test_capability_and_host_symbol_stable() -> None:
    assert CAPABILITY_ID.endswith("THREE_FAMILY_BINDING_V1")
    assert PRODUCTIVE_HOST_SYMBOL == "run_bridge_cycle_v1"
    assert HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH is True


def test_owner_go_missing_fail_closed() -> None:
    with pytest.raises(ProductiveHostAuthorizationError, match="OWNER_GO_REQUIRED"):
        require_owner_go_v1(owner_go=False, environ={})


def test_wrong_repository_sha_fail_closed() -> None:
    with pytest.raises(ProductiveHostAuthorizationError, match="REPOSITORY_SHA_MISMATCH"):
        require_repository_sha_match_v1(actual_sha="a" * 40, expected_sha="b" * 40)


def test_o2_remains_dashboard_only() -> None:
    assert set(AUTHORIZED_MODES) == set(O2_AUTHORIZED_MODES_REQUIRED)
    assert MODE_DASHBOARD_ONLY in AUTHORIZED_MODES
    proof = prove_network_and_order_boundary_v1()
    assert proof.ok is True
    assert proof.order_submit_reachable is False
    assert proof.credential_path_reachable is False
    assert proof.private_endpoints_reachable is False


def test_archive_root_required_and_writable(tmp_path: Path) -> None:
    with pytest.raises(ProductiveHostAuthorizationError, match="ARCHIVE_ROOT"):
        bind_active_archive_v1(archive_root=None, allow_resolver_fallback=False)
    missing = tmp_path / "missing"
    with pytest.raises(ProductiveHostAuthorizationError, match="ARCHIVE_ROOT_MISSING"):
        bind_active_archive_v1(archive_root=missing, allow_resolver_fallback=False)
    archive = _seed_archive(tmp_path)
    bound = bind_active_archive_v1(archive_root=archive, allow_resolver_fallback=False)
    assert bound.writable is True
    assert Path(bound.archive_root) == archive.resolve()


def test_selected_instrument_from_archive_not_hardcoded(tmp_path: Path) -> None:
    archive = _seed_archive(tmp_path, symbol="SATS-USDT-SWAP")
    symbol, source = resolve_selected_instrument_from_archive_v1(archive_root=archive)
    assert symbol == "SATS-USDT-SWAP"
    assert "universe_selection_readmodel" in source
    with pytest.raises(ProductiveHostAuthorizationError, match="SELECTED_INSTRUMENT_MISMATCH"):
        resolve_selected_instrument_from_archive_v1(
            archive_root=archive,
            expected_symbol="ETH-USDT-SWAP",
        )


def test_second_writer_fail_closed(tmp_path: Path) -> None:
    layout = materialize_state_root_layout_v1(runtime_root=tmp_path / "runtime")
    w1 = ProductiveHostSingleWriterV1(
        lock_path=Path(layout.writer_lock_path),
        session_id="session-a",
    )
    w1.acquire()
    w2 = ProductiveHostSingleWriterV1(
        lock_path=Path(layout.writer_lock_path),
        session_id="session-b",
    )
    with pytest.raises(ProductiveHostAuthorizationError, match="SECOND_WRITER_REJECTED"):
        w2.acquire(timeout_seconds=0.2)
    w1.release()


def test_double_play_missing_inputs_fail_closed() -> None:
    out = classify_double_play_canonical_inputs_v1(None)
    assert out.exportable is False
    assert out.error_code == "HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH"


def test_smoke_without_owner_go_fails(tmp_path: Path) -> None:
    archive = _seed_archive(tmp_path)
    result = run_productive_host_smoke_session_v1(
        owner_go=False,
        expected_repository_sha=REPO_SHA,
        archive_root=archive,
        runtime_root=tmp_path / "runtime",
        runtime_session_id="test-no-go",
        mid_prices=[0.00035, 0.000351],
        max_cycles=2,
        min_cycle_interval_seconds=0.0,
    )
    assert result.ok is False
    assert any("OWNER_GO_REQUIRED" in e for e in result.errors)


def test_smoke_wrong_sha_fails(tmp_path: Path) -> None:
    archive = _seed_archive(tmp_path)
    result = run_productive_host_smoke_session_v1(
        owner_go=True,
        expected_repository_sha="0" * 40,
        archive_root=archive,
        runtime_root=tmp_path / "runtime",
        runtime_session_id="test-bad-sha",
        mid_prices=[0.00035],
        max_cycles=1,
        min_cycle_interval_seconds=0.0,
    )
    assert result.ok is False
    assert any("REPOSITORY_SHA_MISMATCH" in e for e in result.errors)


def test_productive_smoke_commits_and_exports_ds_cd(tmp_path: Path) -> None:
    archive = _seed_archive(tmp_path)
    result = run_productive_host_smoke_session_v1(
        owner_go=True,
        expected_repository_sha=REPO_SHA,
        archive_root=archive,
        runtime_root=tmp_path / "runtime",
        runtime_session_id="test-smoke-ok",
        mid_prices=[0.00035 + i * 0.000001 for i in range(8)],
        expected_instrument="SATS-USDT-SWAP",
        enable_activation=True,
        require_selection_binding=False,
        max_cycles=8,
        min_cycle_interval_seconds=0.0,
    )
    assert result.host_started is True
    assert result.archive_bound is True
    assert result.order_path_reachable is False
    assert result.credential_path_reachable is False
    assert result.long_running_phase_9_2_proven is False
    assert result.hard_stop_double_play is True
    assert result.double_play is not None
    assert result.double_play.exportable is False
    # At least one analytical cycle should commit under Cap 7.2 + warm-up path.
    assert result.cycles_attempted >= 1
    if result.ok:
        assert result.canonical_cycle_committed is True
        assert result.canonical_decision is not None
        # Evidence export may succeed even when scope has not advanced yet.
        assert (
            result.canonical_decision.exported
            or result.canonical_decision.error_code
            or result.canonical_decision.skipped_reason
        )
    else:
        # Fail-closed activation/runtime blockers must be explicit (not silent).
        assert result.errors
        # Surface errors in assertion message for forensics.
        raise AssertionError(f"smoke_not_ok:{result.errors}")
