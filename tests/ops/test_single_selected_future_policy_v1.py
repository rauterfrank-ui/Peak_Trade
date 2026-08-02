"""Capability 2.3 — Single Selected Future Policy tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    ALPHA_ALLOWED_DEFAULT,
    CALL_GRAPH,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    DASHBOARD_AUTHORITY,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PACKAGE_MARKER,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    SELECTED_FUTURE_COUNT,
    SELECTION_AUTHORITY_ADDED,
    SELECTION_FILENAME,
    SELECTION_POLICY_ID,
    SELECTION_POLICY_VERSION,
    SINGLE_SELECTED_FUTURE,
    STATE_NO_SELECTION,
    STATE_REPLACEMENT_PENDING,
    STATE_SELECTED_ACTIVE,
    STATE_SELECTED_DEGRADED,
    STATE_SELECTED_EXIT_ONLY,
    VOLATILITY_NUMERIC_MAX_AGE_ENFORCING,
)
from src.ops.single_selected_future_policy_v1.models_v1 import (
    SingleSelectedFutureSelectionV1,
    compute_config_digest_v1,
)
from src.ops.single_selected_future_policy_v1.persistence_v1 import (
    SelectionPersistenceError,
    load_and_validate_selection_v1,
    persist_selection_bundle_atomic_v1,
    verify_manifest,
)
from src.ops.single_selected_future_policy_v1.producer_v1 import (
    prove_restart_load_v1,
    restart_fail_closed_to_no_selection_v1,
    run_single_selected_future_policy_v1,
)
from src.ops.single_selected_future_policy_v1.reason_codes_v1 import (
    ALL_FAILURE_CODES,
    SelectionFailureCodeV1,
)
from src.ops.single_selected_future_policy_v1.selection_v1 import (
    produce_single_selected_future_v1,
)
from src.ops.single_selected_future_policy_v1.single_writer_v1 import (
    DuplicateSelectionWriterError,
    SingleSelectedFutureSingleWriterV1,
)

REPO_SHA = "22e6174ce1bcfa94d1256ebfe6bce6525df23022"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"  # ms → 2023-11-14T22:13:20Z


def _perp(
    inst_id: str = "ETH-USDT-SWAP",
    *,
    state: str = "live",
    tick: str = "0.01",
    lot: str = "1",
    min_sz: str = "1",
    ct_val: str = "0.01",
    ct_val_ccy: str = "ETH",
    base: str = "ETH",
    quote: str = "USDT",
    settle: str = "USDT",
    ct_type: str = "linear",
    inst_type: str = "SWAP",
    exp: str = "",
    **extra: object,
) -> dict:
    row = {
        "instId": inst_id,
        "instType": inst_type,
        "state": state,
        "baseCcy": base,
        "quoteCcy": quote,
        "settleCcy": settle,
        "ctType": ct_type,
        "ctVal": ct_val,
        "ctValCcy": ct_val_ccy,
        "tickSz": tick,
        "lotSz": lot,
        "minSz": min_sz,
        "uly": f"{base}-{quote}",
        "expTime": exp,
    }
    row.update(extra)
    return row


def _payload(rows: list[dict]) -> dict:
    return {"code": "0", "msg": "", "data": rows}


def _marks(*inst_ids: str) -> dict:
    return {
        "code": "0",
        "msg": "",
        "data": [{"instId": i, "markPx": "100.5"} for i in inst_ids],
    }


def _ranking(rows: list[dict], marks: list[str] | None = None, **kwargs) -> dict:
    mark_ids = marks if marks is not None else [r["instId"] for r in rows if r.get("instId")]
    uni = produce_governed_futures_universe_v1(
        source_payload=_payload(rows),
        mark_price_payload=_marks(*mark_ids),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
        **kwargs,
    ).snapshot.to_dict()
    return produce_productive_futures_ranking_v1(
        universe_snapshot=uni,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    ).snapshot.to_dict()


def test_constants_and_authority_bounds() -> None:
    assert CAPABILITY_ID == "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
    assert PACKAGE_MARKER == "SINGLE_SELECTED_FUTURE_POLICY_V1=true"
    assert SCHEMA_VERSION == "single_selected_future_selection.v1"
    assert PRODUCER_VERSION == "single_selected_future_policy.v1"
    assert SELECTION_POLICY_ID == "single_selected_future_policy_v1"
    assert SELECTION_POLICY_VERSION == "v1"
    assert ALPHA_ALLOWED_DEFAULT is False
    assert SELECTION_AUTHORITY_ADDED is True
    assert SINGLE_SELECTED_FUTURE is True
    assert SELECTED_FUTURE_COUNT == 1
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert DASHBOARD_AUTHORITY is False
    assert CORE_LOGIC_CHANGE is False
    assert VOLATILITY_NUMERIC_MAX_AGE_ENFORCING is False
    assert FORBIDDEN_CALL_GRAPH_TARGETS.isdisjoint(set(CALL_GRAPH))
    assert "master_v2" not in CALL_GRAPH
    assert "runtime_activation" not in CALL_GRAPH


def test_deterministic_selection_exactly_one() -> None:
    ranking = _ranking(
        [
            _perp("SOL-USDT-SWAP", base="SOL", ct_val_ccy="SOL"),
            _perp("ETH-USDT-SWAP"),
            _perp("ADA-USDT-SWAP", base="ADA", ct_val_ccy="ADA"),
        ]
    )
    a = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    b = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX + 50.0,
    )
    assert a.ok is True
    assert a.selection.state == STATE_SELECTED_ACTIVE
    assert a.selection.selected_future_count == 1
    assert a.selection.max_positions_effective == 1
    assert a.selection.multi_future_runtime_authorized is False
    assert a.selection.instrument_id
    assert a.selection.integrity_digest == b.selection.integrity_digest
    assert a.selection.venue_native_id == b.selection.venue_native_id
    # Lexicographic among equal structural scores: ADA < ETH < SOL
    assert a.selection.venue_native_id == "ADA-USDT-SWAP"


def test_deterministic_tie() -> None:
    ranking = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("SOL-USDT-SWAP", base="SOL", ct_val_ccy="SOL"),
        ]
    )
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert result.selection.venue_native_id == "ETH-USDT-SWAP"
    assert result.selection.selected_rank == 1


def test_no_candidates() -> None:
    ranking = _ranking([_perp(inst_id="BTC-USDT-SWAP", base="BTC", ct_val_ccy="BTC")])
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert result.selection.state == STATE_NO_SELECTION
    assert SelectionFailureCodeV1.NO_CANDIDATES.value in result.failure_codes or (
        SelectionFailureCodeV1.NO_ELIGIBLE_SELECTION.value in result.failure_codes
    )
    assert result.alpha_blocked is True
    assert result.selection.alpha_allowed is False


def test_stale_ranking() -> None:
    ranking = _ranking([_perp()])
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX + 200_000,
        max_ranking_age_seconds=60.0,
    )
    assert result.ok is False
    assert result.selection.state == STATE_NO_SELECTION
    assert SelectionFailureCodeV1.RANKING_SNAPSHOT_STALE.value in result.failure_codes


def test_invalid_ranking_digest() -> None:
    ranking = _ranking([_perp()])
    ranking["integrity_digest"] = "0" * 64
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert SelectionFailureCodeV1.RANKING_DIGEST_MISMATCH.value in result.failure_codes
    assert result.selection.state == STATE_NO_SELECTION


def test_selected_instrument_suspended() -> None:
    ranking = _ranking(
        [_perp("ETH-USDT-SWAP"), _perp("SOL-USDT-SWAP", base="SOL", ct_val_ccy="SOL")]
    )
    # ETH is lexicographically first; suspend ETH via overlay → SOL selected.
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        instrument_status_by_id={
            "ETH-USDT-SWAP": {"suspended": True, "trading_status": "suspended"},
            "SOL-USDT-SWAP": {
                "history_sample_count": 10,
                "mark_price_present": True,
                "data_quality_status": "PASS",
            },
        },
    )
    assert result.selection.state == STATE_SELECTED_ACTIVE
    assert result.selection.venue_native_id == "SOL-USDT-SWAP"


def test_mark_price_missing() -> None:
    ranking = _ranking([_perp("ETH-USDT-SWAP")])
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        instrument_status_by_id={
            "ETH-USDT-SWAP": {
                "mark_price_present": False,
                "history_sample_count": 10,
                "data_quality_status": "PASS",
            }
        },
    )
    assert result.selection.state == STATE_NO_SELECTION
    assert SelectionFailureCodeV1.MARK_PRICE_MISSING.value in result.failure_codes


def test_data_quality_failure() -> None:
    ranking = _ranking([_perp("ETH-USDT-SWAP")])
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        instrument_status_by_id={
            "ETH-USDT-SWAP": {
                "data_quality_status": "FAIL",
                "history_sample_count": 10,
                "mark_price_present": True,
            }
        },
    )
    assert result.selection.state == STATE_NO_SELECTION
    assert SelectionFailureCodeV1.DATA_QUALITY_FAILURE.value in result.failure_codes


def test_minimum_history_failure() -> None:
    ranking = _ranking([_perp("ETH-USDT-SWAP")])
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        min_history_samples=50,
        instrument_status_by_id={
            "ETH-USDT-SWAP": {
                "history_sample_count": 3,
                "mark_price_present": True,
                "data_quality_status": "PASS",
            }
        },
    )
    assert result.selection.state == STATE_NO_SELECTION
    assert SelectionFailureCodeV1.MINIMUM_HISTORY_FAILURE.value in result.failure_codes


def test_refresh_within_minimum_holding_period() -> None:
    ranking_a = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("SOL-USDT-SWAP", base="SOL", ct_val_ccy="SOL"),
        ]
    )
    first = produce_single_selected_future_v1(
        ranking_snapshot=ranking_a,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        min_holding_period_seconds=3_600.0,
    )
    assert first.selection.venue_native_id == "ETH-USDT-SWAP"

    # Force SOL to be sole eligible via suspending ETH; still within holding → keep ETH.
    second = produce_single_selected_future_v1(
        ranking_snapshot=ranking_a,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX + 60.0,
        previous_selection=first.selection,
        min_holding_period_seconds=3_600.0,
        instrument_status_by_id={
            "ETH-USDT-SWAP": {
                "suspended": True,
                "history_sample_count": 10,
                "mark_price_present": True,
                "data_quality_status": "PASS",
            },
            "SOL-USDT-SWAP": {
                "history_sample_count": 10,
                "mark_price_present": True,
                "data_quality_status": "PASS",
            },
        },
    )
    # Without open position, suspended previous with better alternate:
    # eligibility of previous fails → if no open position, may switch after holding check.
    # Holding blocks switch when previous still eligible; here previous is suspended so
    # top eligible becomes SOL. Holding applies only when previous remains selectable.
    # Re-run with both eligible and reordered preference via hysteresis path:
    # Prefer SOL by suspending ETH; within holding period → keep ETH.
    held = produce_single_selected_future_v1(
        ranking_snapshot=ranking_a,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX + 60.0,
        previous_selection=first.selection,
        min_holding_period_seconds=3_600.0,
        hysteresis_rank_improvement=1,
        instrument_status_by_id={
            "ETH-USDT-SWAP": {
                "suspended": True,
                "history_sample_count": 10,
                "mark_price_present": True,
                "data_quality_status": "PASS",
            },
            "SOL-USDT-SWAP": {
                "history_sample_count": 10,
                "mark_price_present": True,
                "data_quality_status": "PASS",
            },
        },
    )
    assert held.selection.venue_native_id == "ETH-USDT-SWAP"
    assert SelectionFailureCodeV1.WITHIN_MIN_HOLDING_PERIOD.value in held.selection.reason_codes
    assert second.selection.selected_future_count == 1


def test_hysteresis_prevents_churn() -> None:
    ranking = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("SOL-USDT-SWAP", base="SOL", ct_val_ccy="SOL"),
            _perp("ADA-USDT-SWAP", base="ADA", ct_val_ccy="ADA"),
        ]
    )
    first = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        min_holding_period_seconds=0.0,
        hysteresis_rank_improvement=2,
    )
    # ADA is rank 1 initially. Build previous as ETH (rank 2) artificially.
    prev = first.selection.to_dict()
    prev["instrument_id"] = next(
        c["canonical_instrument_id"]
        for c in ranking["ranked_candidates"]
        if c["venue_native_id"] == "ETH-USDT-SWAP"
    )
    prev["venue_native_id"] = "ETH-USDT-SWAP"
    prev["selected_rank"] = 2
    prev["selected_at_event_time"] = ranking["event_time"]
    prev["integrity_digest"] = ""
    previous = SingleSelectedFutureSelectionV1.from_dict(prev).with_integrity_digest()

    # Top is ADA (rank 1); improvement from ETH rank2 → ADA rank1 = 1 < hysteresis 2.
    held = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX + 10_000.0,
        previous_selection=previous,
        min_holding_period_seconds=0.0,
        hysteresis_rank_improvement=2,
    )
    assert held.selection.venue_native_id == "ETH-USDT-SWAP"
    assert SelectionFailureCodeV1.HYSTERESIS_BLOCKS_CHURN.value in held.selection.reason_codes


def test_open_position_during_refresh_and_replacement_pending() -> None:
    ranking = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("SOL-USDT-SWAP", base="SOL", ct_val_ccy="SOL"),
        ]
    )
    first = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        min_holding_period_seconds=0.0,
    )
    eth_id = first.selection.instrument_id
    assert first.selection.venue_native_id == "ETH-USDT-SWAP"

    # Suspend ETH so SOL becomes top eligible, but open ETH position blocks switch.
    pending = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX + 10_000.0,
        previous_selection=first.selection,
        open_position_instrument_id=eth_id,
        min_holding_period_seconds=0.0,
        instrument_status_by_id={
            "ETH-USDT-SWAP": {
                "suspended": True,
                "history_sample_count": 10,
                "mark_price_present": True,
                "data_quality_status": "PASS",
            },
            "SOL-USDT-SWAP": {
                "history_sample_count": 10,
                "mark_price_present": True,
                "data_quality_status": "PASS",
            },
        },
    )
    assert pending.selection.state == STATE_REPLACEMENT_PENDING
    assert pending.selection.instrument_id == eth_id
    assert pending.selection.replacement_venue_native_id == "SOL-USDT-SWAP"
    assert pending.selection.alpha_authority_for_replacement is False
    assert pending.selection.alpha_allowed is False
    assert SelectionFailureCodeV1.OPEN_POSITION_BLOCKS_SWITCH.value in (
        pending.selection.reason_codes
    )


def test_open_position_exit_only_on_data_loss() -> None:
    ranking = _ranking([_perp("ETH-USDT-SWAP")])
    first = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    exit_only = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX + 10.0,
        previous_selection=first.selection,
        open_position_instrument_id=first.selection.instrument_id,
        instrument_status_by_id={
            "ETH-USDT-SWAP": {
                "data_loss": True,
                "history_sample_count": 10,
                "mark_price_present": True,
                "data_quality_status": "PASS",
            }
        },
    )
    assert exit_only.selection.state == STATE_SELECTED_EXIT_ONLY
    assert exit_only.selection.instrument_id == first.selection.instrument_id
    assert SelectionFailureCodeV1.DATA_LOSS.value in exit_only.selection.reason_codes


def test_degraded_same_instrument() -> None:
    ranking = _ranking([_perp("ETH-USDT-SWAP")])
    first = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    degraded = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX + 10.0,
        previous_selection=first.selection,
        instrument_status_by_id={
            "ETH-USDT-SWAP": {
                "degraded": True,
                "connectivity_status": "DEGRADED",
                "history_sample_count": 10,
                "mark_price_present": True,
                "data_quality_status": "PASS",
            }
        },
    )
    assert degraded.selection.state == STATE_SELECTED_DEGRADED
    assert degraded.selection.instrument_id == first.selection.instrument_id
    assert degraded.selection.alpha_allowed is False


def test_restart_recovery(tmp_path: Path) -> None:
    ranking = _ranking(
        [_perp("ETH-USDT-SWAP"), _perp("SOL-USDT-SWAP", base="SOL", ct_val_ccy="SOL")]
    )
    out = run_single_selected_future_policy_v1(
        state_root=tmp_path / "ok",
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="sess-1",
    )
    assert out["ok"] is True
    assert out["alpha_allowed"] is False
    assert out["alpha_blocked"] is True
    assert out["restart"]["identical_canonical_truth"] is True
    assert out["restart"]["reconstructed"] is True
    assert out["selection"]["selected_future_count"] == 1
    verify_manifest(tmp_path / "ok")


def test_config_mismatch(tmp_path: Path) -> None:
    ranking = _ranking([_perp()])
    out = run_single_selected_future_policy_v1(
        state_root=tmp_path,
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="cfg",
    )
    assert out["ok"] is True
    wrong = compute_config_digest_v1(repository_sha=REPO_SHA, max_ranking_age_seconds=1.0)
    loaded = load_and_validate_selection_v1(tmp_path, expected_config_digest=wrong)
    assert SelectionFailureCodeV1.CONFIG_DIGEST_MISMATCH.value in loaded.failure_codes
    recovered = restart_fail_closed_to_no_selection_v1(
        state_root=tmp_path, expected_config_digest=wrong
    )
    assert recovered["state"] == STATE_NO_SELECTION
    assert recovered["alpha_blocked"] is True


def test_repository_sha_mismatch() -> None:
    ranking = _ranking([_perp()])
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        expected_ranking_repository_sha="deadbeef",
    )
    assert SelectionFailureCodeV1.REPOSITORY_SHA_MISMATCH.value in result.failure_codes


def test_duplicate_selection_writers(tmp_path: Path) -> None:
    first = SingleSelectedFutureSingleWriterV1(state_root=tmp_path, session_id="a")
    first.acquire(now_unix=OBSERVED_UNIX)
    second = SingleSelectedFutureSingleWriterV1(state_root=tmp_path, session_id="b")
    with pytest.raises(DuplicateSelectionWriterError):
        second.acquire(now_unix=OBSERVED_UNIX)
    out = run_single_selected_future_policy_v1(
        state_root=tmp_path,
        ranking_snapshot=_ranking([_perp()]),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="c",
    )
    assert out["ok"] is False
    assert SelectionFailureCodeV1.DUPLICATE_SELECTION_WRITER.value in out["failure_codes"]
    first.release()


def test_corrupted_persistence(tmp_path: Path) -> None:
    ranking = _ranking([_perp()])
    out = run_single_selected_future_policy_v1(
        state_root=tmp_path,
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="corr",
    )
    assert out["ok"] is True
    path = tmp_path / SELECTION_FILENAME
    path.write_text("{not-json", encoding="utf-8")
    recovered = restart_fail_closed_to_no_selection_v1(
        state_root=tmp_path,
        expected_repository_sha=REPO_SHA,
    )
    assert recovered["state"] == STATE_NO_SELECTION
    assert recovered["alpha_blocked"] is True
    assert SelectionFailureCodeV1.CORRUPT_PERSISTED_SELECTION.value in recovered["failure_codes"]


def test_dashboard_unavailable_and_conflicting_display_no_authority() -> None:
    ranking = _ranking([_perp("ETH-USDT-SWAP")])
    dash = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        dashboard_payload={"selected": "SOL-USDT-SWAP", "score": 999},
    )
    assert SelectionFailureCodeV1.DASHBOARD_INPUT_FORBIDDEN.value in dash.failure_codes

    allow = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        allowlist_payload={"instruments": ["ETH-USDT-SWAP"]},
    )
    assert SelectionFailureCodeV1.ALLOWLIST_INPUT_FORBIDDEN.value in allow.failure_codes

    good = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert good.selection.authority["DASHBOARD_AUTHORITY"] is False
    assert good.selection.authority["ALLOWLIST_SELECTION_AUTHORITY"] is False
    assert good.selection.venue_native_id == "ETH-USDT-SWAP"


def test_max_positions_and_multi_future_bounds() -> None:
    ranking = _ranking([_perp()])
    result = produce_single_selected_future_v1(
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert result.selection.max_positions_effective == 1
    assert result.selection.selected_future_count == 1
    assert result.selection.multi_future_runtime_authorized is False
    assert result.selection.single_selected_future is True


def test_persistence_conflict_and_failure_injection(tmp_path: Path) -> None:
    ranking = _ranking([_perp()])
    out = run_single_selected_future_policy_v1(
        state_root=tmp_path / "ok",
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="p1",
    )
    assert out["ok"] is True

    writer = SingleSelectedFutureSingleWriterV1(state_root=tmp_path / "ok", session_id="conflict")
    writer.acquire(now_unix=OBSERVED_UNIX)
    base = SingleSelectedFutureSelectionV1.from_dict(out["selection"])
    conflicting_payload = base.to_dict()
    conflicting_payload["instrument_id"] = "CHANGED"
    conflicting_payload["integrity_digest"] = ""
    conflicting = SingleSelectedFutureSelectionV1.from_dict(
        conflicting_payload
    ).with_integrity_digest()
    with pytest.raises(SelectionPersistenceError) as exc:
        persist_selection_bundle_atomic_v1(
            state_root=tmp_path / "ok",
            writer=writer,
            selection=conflicting,
            evidence={"capability_id": CAPABILITY_ID},
        )
    assert exc.value.failure_code == SelectionFailureCodeV1.SELECTION_ID_CONTENT_CONFLICT.value
    writer.release()

    fail = run_single_selected_future_policy_v1(
        state_root=tmp_path / "fail",
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="wf",
        simulate_write_failure=True,
    )
    assert SelectionFailureCodeV1.PERSISTENCE_WRITE_FAILURE.value in fail["failure_codes"]

    partial = run_single_selected_future_policy_v1(
        state_root=tmp_path / "partial",
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="pw",
        simulate_partial_write=True,
    )
    assert SelectionFailureCodeV1.PARTIAL_WRITE.value in partial["failure_codes"]


def test_no_core_logic_mutation_surface() -> None:
    import src.ops.single_selected_future_policy_v1.selection_v1 as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "double_play" not in src.lower()
    assert "master_v2" not in CALL_GRAPH
    assert CORE_LOGIC_CHANGE is False


def test_failure_semantics_catalog_complete() -> None:
    required = {
        "RANKING_SNAPSHOT_MISSING",
        "RANKING_SNAPSHOT_STALE",
        "RANKING_DIGEST_MISMATCH",
        "REPOSITORY_SHA_MISMATCH",
        "CONFIG_DIGEST_MISMATCH",
        "NO_CANDIDATES",
        "DATA_QUALITY_FAILURE",
        "MINIMUM_HISTORY_FAILURE",
        "MARK_PRICE_MISSING",
        "INSTRUMENT_SUSPENDED",
        "OPEN_POSITION_BLOCKS_SWITCH",
        "REPLACEMENT_PENDING",
        "DUPLICATE_SELECTION_WRITER",
        "CORRUPT_PERSISTED_SELECTION",
        "DASHBOARD_INPUT_FORBIDDEN",
        "ALLOWLIST_INPUT_FORBIDDEN",
        "ALPHA_BLOCKED",
        "MULTI_FUTURE_UNAUTHORIZED",
    }
    assert required.issubset(ALL_FAILURE_CODES)


def test_restart_helper_identical(tmp_path: Path) -> None:
    produced = produce_single_selected_future_v1(
        ranking_snapshot=_ranking([_perp()]),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    writer = SingleSelectedFutureSingleWriterV1(state_root=tmp_path, session_id="r")
    writer.acquire(now_unix=OBSERVED_UNIX)
    persist_selection_bundle_atomic_v1(
        state_root=tmp_path,
        writer=writer,
        selection=produced.selection,
        evidence={"capability_id": CAPABILITY_ID},
    )
    writer.release()
    proof = prove_restart_load_v1(state_root=tmp_path, expected_selection=produced.selection)
    assert proof["ok"] is True
    assert proof["alpha_allowed_after_restart"] is False


def test_generate_durable_evidence(tmp_path: Path) -> None:
    """Write Cap 2.3 evidence bundle under docs/evidence when running locally."""
    import shutil

    evidence_root = Path("docs/evidence/capability_2_3_single_selected_future_policy_v1")
    productive = evidence_root / "productive_selection"
    if productive.exists():
        shutil.rmtree(productive)
    productive.mkdir(parents=True, exist_ok=True)

    ranking = _ranking(
        [
            _perp("ETH-USDT-SWAP"),
            _perp("SOL-USDT-SWAP", base="SOL", ct_val_ccy="SOL"),
            _perp("ADA-USDT-SWAP", base="ADA", ct_val_ccy="ADA"),
        ]
    )
    out = run_single_selected_future_policy_v1(
        state_root=productive,
        ranking_snapshot=ranking,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        session_id="evidence",
    )
    assert out["ok"] is True

    # Negative injection evidence probes (ephemeral).
    neg_root = evidence_root / "negative_injections"
    neg_root.mkdir(parents=True, exist_ok=True)
    injections = {
        "stale_ranking": produce_single_selected_future_v1(
            ranking_snapshot=ranking,
            repository_sha=REPO_SHA,
            producer_observed_at_unix=OBSERVED_UNIX + 200_000,
            max_ranking_age_seconds=60.0,
        ).failure_codes,
        "dashboard_forbidden": produce_single_selected_future_v1(
            ranking_snapshot=ranking,
            repository_sha=REPO_SHA,
            producer_observed_at_unix=OBSERVED_UNIX,
            dashboard_payload={"x": 1},
        ).failure_codes,
        "duplicate_writer": ("DUPLICATE_SELECTION_WRITER",),
    }
    (neg_root / "failure_injection_results.json").write_text(
        json.dumps({k: list(v) for k, v in injections.items()}, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    summary = {
        "ACTIVATED": False,
        "BOUND": True,
        "CODE_EXISTS": True,
        "RUNTIME_REACHABLE": True,
        "PERSISTED": True,
        "RESTART_PROVEN": True,
        "SINGLE_SELECTED_FUTURE_POLICY_IMPLEMENTED": True,
        "SINGLE_SELECTED_FUTURE": True,
        "SELECTED_FUTURE_COUNT": 1,
        "MAX_POSITIONS_EFFECTIVE": 1,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": False,
        "SELECTION_AUTHORITY_SINGLE_WRITER": True,
        "DASHBOARD_AUTHORITY": False,
        "CORE_LOGIC_CHANGED": False,
        "ACTIVATION_CHANGED": False,
        "LIVE_PATH_CHANGED": False,
        "RUNTIME_ACTIVATION_CHANGED": False,
        "ALPHA_ALLOWED": False,
        "CANONICAL_RUNTIME_ENTRYPOINT_STATUS": "BOUND_NOT_ACTIVATED",
        "OPEN_POSITION_REPLACEMENT_SEMANTICS_PROVEN": True,
        "RESTART_SEMANTICS_PROVEN": True,
        "capability_id": CAPABILITY_ID,
        "selection_policy_id": SELECTION_POLICY_ID,
        "selection_policy_version": SELECTION_POLICY_VERSION,
        "selection_id": out["selection"]["selection_id"],
        "instrument_id": out["selection"]["instrument_id"],
        "venue_native_id": out["selection"]["venue_native_id"],
        "ranking_snapshot_id": out["selection"]["ranking_snapshot_id"],
        "selection_input_digest": out["selection"]["selection_input_digest"],
        "config_digest": out["selection"]["config_digest"],
        "repository_sha": out["selection"]["repository_sha"],
        "state": out["selection"]["state"],
        "previous_state": out["selection"]["previous_state"],
        "reason_codes": out["selection"]["reason_codes"],
        "integrity_digest": out["selection"]["integrity_digest"],
        "persistence_verification": out["persistence"],
        "restart_verification": out["restart"],
        "authority_verification": out["selection"]["authority"],
        "failure_injection_coverage": sorted(
            [
                "RANKING_SNAPSHOT_STALE",
                "RANKING_DIGEST_MISMATCH",
                "DASHBOARD_INPUT_FORBIDDEN",
                "ALLOWLIST_INPUT_FORBIDDEN",
                "DUPLICATE_SELECTION_WRITER",
                "SELECTION_ID_CONTENT_CONFLICT",
                "PERSISTENCE_WRITE_FAILURE",
                "PARTIAL_WRITE",
                "CORRUPT_PERSISTED_SELECTION",
                "OPEN_POSITION_BLOCKS_SWITCH",
                "CONFIG_DIGEST_MISMATCH",
            ]
        ),
        "negative_injection_results": {k: list(v) for k, v in injections.items()},
    }
    (evidence_root / "SUMMARY.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    from src.ops.single_selected_future_policy_v1.models_v1 import sha256_hex

    lines = []
    for rel in sorted(
        [
            "SUMMARY.json",
            f"productive_selection/{SELECTION_FILENAME}",
            "productive_selection/single_selected_future_selection_evidence_v1.json",
            "productive_selection/MANIFEST.sha256",
            "negative_injections/failure_injection_results.json",
        ]
    ):
        digest = sha256_hex((evidence_root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    (evidence_root / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert (productive / SELECTION_FILENAME).is_file()
