"""Adversarial offline reproof for archive / instrument seam (A–N subset)."""

from __future__ import annotations

import json
import multiprocessing
import subprocess
from pathlib import Path

import pytest

from src.ops.productive_decision_host_active_archive_three_family_binding_v1.archive_binding_v1 import (
    bind_active_archive_v1,
    resolve_selected_instrument_from_archive_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.archive_session_pin_v1 import (
    assert_archive_universe_session_pin_unchanged_v1,
    establish_archive_universe_session_pin_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.authorization_v1 import (
    ProductiveHostAuthorizationError,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.cycle_session_v1 import (
    run_productive_host_smoke_session_v1,
)
from src.ops.archive_sibling_export_contract_v1.manifest_finalize_v1 import (
    finalize_readmodels_manifest_after_write_v1,
)
from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256


def _current_repo_sha() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        text=True,
    ).strip()


REPO_SHA = _current_repo_sha()


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
        "ranking": [{"row_id": f"r-c-{symbol}", "symbol": symbol, "rank": 1, "notes": "test"}],
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


def _seed_verified_archive(tmp_path: Path, symbol: str = "SATS-USDT-SWAP") -> Path:
    archive = tmp_path / "archive"
    readmodels = archive / "readmodels"
    readmodels.mkdir(parents=True)
    (readmodels / "universe_selection_readmodel.v1.json").write_text(
        json.dumps(_universe_payload(symbol), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256(readmodels)
    return archive


def test_a_json_without_manifest_fail_closed(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    readmodels = archive / "readmodels"
    readmodels.mkdir(parents=True)
    (readmodels / "universe_selection_readmodel.v1.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ProductiveHostAuthorizationError, match="ARCHIVE_UNIVERSE_VERIFY_FAILED"):
        resolve_selected_instrument_from_archive_v1(
            archive_root=archive,
            expected_symbol="SATS-USDT-SWAP",
            require_instrument_pin=True,
        )


def test_b_invalid_manifest_fail_closed(tmp_path: Path) -> None:
    archive = _seed_verified_archive(tmp_path)
    readmodels = archive / "readmodels"
    (readmodels / "MANIFEST.sha256").write_text("deadbeef  universe_selection_readmodel.v1.json\n")
    with pytest.raises(ProductiveHostAuthorizationError, match="MANIFEST_VERIFY_FAILED"):
        resolve_selected_instrument_from_archive_v1(archive_root=archive)


def test_c_valid_producer_archive_accepted(tmp_path: Path) -> None:
    archive = _seed_verified_archive(tmp_path)
    symbol, _ = resolve_selected_instrument_from_archive_v1(
        archive_root=archive,
        expected_symbol="SATS-USDT-SWAP",
        require_instrument_pin=True,
    )
    assert symbol == "SATS-USDT-SWAP"


def test_d_wrong_instrument_mismatch_fail_closed(tmp_path: Path) -> None:
    archive = _seed_verified_archive(tmp_path, symbol="ETH-USDT-SWAP")
    with pytest.raises(ProductiveHostAuthorizationError, match="SELECTED_INSTRUMENT_MISMATCH"):
        resolve_selected_instrument_from_archive_v1(
            archive_root=archive,
            expected_symbol="SATS-USDT-SWAP",
            require_instrument_pin=True,
        )


def test_e_missing_expected_symbol_pin_fail_closed(tmp_path: Path) -> None:
    archive = _seed_verified_archive(tmp_path)
    with pytest.raises(ProductiveHostAuthorizationError, match="INSTRUMENT_PIN_REQUIRED"):
        resolve_selected_instrument_from_archive_v1(
            archive_root=archive,
            require_instrument_pin=True,
        )


def test_f_missing_archive_root_no_discovery_fail_closed() -> None:
    with pytest.raises(ProductiveHostAuthorizationError, match="ARCHIVE_ROOT_REQUIRED"):
        bind_active_archive_v1(archive_root=None, allow_resolver_fallback=False)


def test_g_refresh_during_smoke_pin_drift_fail_closed(tmp_path: Path) -> None:
    archive = _seed_verified_archive(tmp_path)
    pin = establish_archive_universe_session_pin_v1(archive_root=archive)
    readmodels = archive / "readmodels"
    payload = json.loads((readmodels / "universe_selection_readmodel.v1.json").read_text())
    payload = dict(payload)
    payload["selected_future"] = dict(payload["selected_future"])
    payload["selected_future"]["symbol"] = "ETH-USDT-SWAP"
    (readmodels / "universe_selection_readmodel.v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256(readmodels)
    with pytest.raises(ProductiveHostAuthorizationError, match="ARCHIVE_SESSION_PIN_DRIFT"):
        assert_archive_universe_session_pin_unchanged_v1(pin)


def test_h_crash_between_write_and_manifest_detected(tmp_path: Path) -> None:
    archive = _seed_verified_archive(tmp_path)
    readmodels = archive / "readmodels"
    payload = json.loads((readmodels / "universe_selection_readmodel.v1.json").read_text())
    payload = dict(payload)
    payload["generated_at"] = "2026-08-01T00:00:00Z"
    (readmodels / "universe_selection_readmodel.v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ProductiveHostAuthorizationError, match="MANIFEST_VERIFY_FAILED"):
        resolve_selected_instrument_from_archive_v1(archive_root=archive)


def test_i_manifest_finalize_restores_coherence(tmp_path: Path) -> None:
    archive = _seed_verified_archive(tmp_path)
    readmodels = archive / "readmodels"
    payload = json.loads((readmodels / "universe_selection_readmodel.v1.json").read_text())
    payload = dict(payload)
    payload["generated_at"] = "2026-08-01T00:00:00Z"
    (readmodels / "universe_selection_readmodel.v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    ok, _ = finalize_readmodels_manifest_after_write_v1(readmodels)
    assert ok is True
    symbol, _ = resolve_selected_instrument_from_archive_v1(archive_root=archive)
    assert symbol == "SATS-USDT-SWAP"


def test_j_smoke_missing_instrument_pin_fail_closed(tmp_path: Path) -> None:
    archive = _seed_verified_archive(tmp_path)
    result = run_productive_host_smoke_session_v1(
        owner_go=True,
        expected_repository_sha=REPO_SHA,
        archive_root=archive,
        runtime_root=tmp_path / "runtime",
        runtime_session_id="no-pin",
        mid_prices=[0.00035],
        max_cycles=1,
        min_cycle_interval_seconds=0.0,
    )
    assert result.ok is False
    assert any("INSTRUMENT_PIN_REQUIRED" in e for e in result.errors)


def test_n_false_reject_valid_archive_after_manifest(tmp_path: Path) -> None:
    archive = _seed_verified_archive(tmp_path)
    result = run_productive_host_smoke_session_v1(
        owner_go=True,
        expected_repository_sha=REPO_SHA,
        archive_root=archive,
        runtime_root=tmp_path / "runtime",
        runtime_session_id="false-reject-guard",
        mid_prices=[0.00035 + i * 0.000001 for i in range(4)],
        expected_instrument="SATS-USDT-SWAP",
        max_cycles=4,
        min_cycle_interval_seconds=0.0,
    )
    assert not any("ARCHIVE_UNIVERSE_VERIFY_FAILED" in e for e in result.errors)
    assert not any("INSTRUMENT_PIN_REQUIRED" in e for e in result.errors)


def _mutate_universe_worker(archive_str: str) -> None:
    archive = Path(archive_str)
    readmodels = archive / "readmodels"
    payload = json.loads((readmodels / "universe_selection_readmodel.v1.json").read_text())
    payload = dict(payload)
    payload["source_run_id"] = "concurrent_writer"
    (readmodels / "universe_selection_readmodel.v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256(readmodels)


def test_k_sibling_export_extends_manifest_without_pin_drift(tmp_path: Path) -> None:
    archive = _seed_verified_archive(tmp_path)
    pin = establish_archive_universe_session_pin_v1(archive_root=archive)
    readmodels = archive / "readmodels"
    (readmodels / "dynamic_scope_state_v1.json").write_text(
        json.dumps({"schema_name": "dynamic_scope_state_v1", "non_authorizing": True}) + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256(readmodels)
    assert_archive_universe_session_pin_unchanged_v1(pin)


def test_l_restart_smoke_same_expected_after_instrument_swap_fail_closed(
    tmp_path: Path,
) -> None:
    archive = _seed_verified_archive(tmp_path, symbol="SATS-USDT-SWAP")
    first = run_productive_host_smoke_session_v1(
        owner_go=True,
        expected_repository_sha=REPO_SHA,
        archive_root=archive,
        runtime_root=tmp_path / "runtime_a",
        runtime_session_id="restart-a",
        mid_prices=[0.00035],
        expected_instrument="SATS-USDT-SWAP",
        max_cycles=1,
        min_cycle_interval_seconds=0.0,
    )
    assert not any("SELECTED_INSTRUMENT_MISMATCH" in e for e in first.errors)
    readmodels = archive / "readmodels"
    payload = json.loads((readmodels / "universe_selection_readmodel.v1.json").read_text())
    payload = dict(_universe_payload(symbol="ETH-USDT-SWAP"))
    (readmodels / "universe_selection_readmodel.v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256(readmodels)
    second = run_productive_host_smoke_session_v1(
        owner_go=True,
        expected_repository_sha=REPO_SHA,
        archive_root=archive,
        runtime_root=tmp_path / "runtime_b",
        runtime_session_id="restart-b",
        mid_prices=[0.00035],
        expected_instrument="SATS-USDT-SWAP",
        max_cycles=1,
        min_cycle_interval_seconds=0.0,
    )
    assert second.ok is False
    assert any(
        "SELECTED_INSTRUMENT_MISMATCH" in e or "ARCHIVE_UNIVERSE_VERIFY_FAILED" in e
        for e in second.errors
    )


def test_m_verify_to_use_race_pin_assert_before_resolve(tmp_path: Path) -> None:
    archive = _seed_verified_archive(tmp_path)
    pin = establish_archive_universe_session_pin_v1(archive_root=archive)
    readmodels = archive / "readmodels"
    payload = json.loads((readmodels / "universe_selection_readmodel.v1.json").read_text())
    payload = dict(payload)
    payload["selected_future"] = dict(payload["selected_future"])
    payload["selected_future"]["symbol"] = "ETH-USDT-SWAP"
    (readmodels / "universe_selection_readmodel.v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256(readmodels)
    assert pin.selected_symbol == "SATS-USDT-SWAP"
    with pytest.raises(ProductiveHostAuthorizationError, match="ARCHIVE_SESSION_PIN_DRIFT"):
        assert_archive_universe_session_pin_unchanged_v1(pin)


def test_o_false_accept_blocked_by_manifest_verify(tmp_path: Path) -> None:
    archive = _seed_verified_archive(tmp_path)
    readmodels = archive / "readmodels"
    payload = json.loads((readmodels / "universe_selection_readmodel.v1.json").read_text())
    payload = dict(payload)
    payload["selected_future"] = dict(payload["selected_future"])
    payload["selected_future"]["symbol"] = "ETH-USDT-SWAP"
    (readmodels / "universe_selection_readmodel.v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ProductiveHostAuthorizationError, match="MANIFEST_VERIFY_FAILED"):
        resolve_selected_instrument_from_archive_v1(archive_root=archive)


def test_materializer_chain_smoke_exports_without_verify_regression(tmp_path: Path) -> None:
    archive = _seed_verified_archive(tmp_path)
    result = run_productive_host_smoke_session_v1(
        owner_go=True,
        expected_repository_sha=REPO_SHA,
        archive_root=archive,
        runtime_root=tmp_path / "runtime_mat",
        runtime_session_id="materializer-chain",
        mid_prices=[0.00035 + i * 0.000001 for i in range(6)],
        expected_instrument="SATS-USDT-SWAP",
        max_cycles=6,
        min_cycle_interval_seconds=0.0,
    )
    assert not any("ARCHIVE_SESSION_PIN_DRIFT" in e for e in result.errors)
    if result.canonical_decision is not None:
        assert (
            result.canonical_decision.exported
            or result.canonical_decision.materialized
            or result.canonical_decision.skipped_reason
            or result.canonical_decision.error_code
        )


def test_multiprocess_concurrent_manifest_refresh_pin_observable(tmp_path: Path) -> None:
    archive = _seed_verified_archive(tmp_path)
    pin = establish_archive_universe_session_pin_v1(archive_root=archive)
    proc = multiprocessing.Process(
        target=_mutate_universe_worker,
        args=(str(archive),),
    )
    proc.start()
    proc.join(timeout=5)
    assert proc.exitcode == 0
    with pytest.raises(ProductiveHostAuthorizationError, match="ARCHIVE_SESSION_PIN_DRIFT"):
        assert_archive_universe_session_pin_unchanged_v1(pin)
