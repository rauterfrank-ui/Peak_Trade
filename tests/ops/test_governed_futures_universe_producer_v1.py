"""Capability 2.1 — Governed Futures Universe Producer tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.governed_futures_universe_producer_v1.constants_v1 import (
    ALPHA_ALLOWED_DEFAULT,
    CALL_GRAPH,
    CAPABILITY_ID,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PACKAGE_MARKER,
    PRODUCER_VERSION,
    RANKING_AUTHORITY_ADDED,
    SCHEMA_VERSION,
    SELECTION_AUTHORITY_ADDED,
    SNAPSHOT_FILENAME,
    UNIVERSE_STATUS_EMPTY,
    UNIVERSE_STATUS_ELIGIBLE,
    VENUE,
    VOLATILITY_NUMERIC_MAX_AGE_ENFORCING,
)
from src.ops.governed_futures_universe_producer_v1.models_v1 import (
    GovernedFuturesUniverseSnapshotV1,
    compute_config_digest_v1,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    load_and_validate_universe_snapshot_v1,
    verify_manifest,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
    prove_restart_load_v1,
    run_governed_futures_universe_producer_v1,
)
from src.ops.governed_futures_universe_producer_v1.reason_codes_v1 import (
    ALL_FAILURE_CODES,
    UniverseFailureCodeV1,
)
from src.ops.governed_futures_universe_producer_v1.single_writer_v1 import (
    DuplicateUniverseWriterError,
    GovernedUniverseSingleWriterV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    CALL_GRAPH_STEP as RECON_CALL_GRAPH_STEP,
)

REPO_SHA = "02a1c65a1fe9c3c806fb846da949dfd6d864be94"
OBSERVED_UNIX = 1_700_000_100.0
SOURCE_EVENT = "1700000000000"  # ms


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


def _dated(
    inst_id: str = "ETH-USDT-250328",
    *,
    exp: str = "1743120000000",
    **kwargs: object,
) -> dict:
    return _perp(
        inst_id,
        inst_type="FUTURES",
        exp=exp,
        **kwargs,
    )


def _payload(rows: list[dict]) -> dict:
    return {"code": "0", "msg": "", "data": rows}


def _marks(*inst_ids: str) -> dict:
    return {
        "code": "0",
        "msg": "",
        "data": [{"instId": i, "markPx": "100.5"} for i in inst_ids],
    }


def _produce(rows: list[dict], marks: list[str] | None = None, **kwargs):
    mark_ids = marks if marks is not None else [r["instId"] for r in rows if r.get("instId")]
    return produce_governed_futures_universe_v1(
        source_payload=_payload(rows),
        mark_price_payload=_marks(*mark_ids),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
        **kwargs,
    )


def test_constants_and_authority_bounds() -> None:
    assert CAPABILITY_ID == "CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1"
    assert PACKAGE_MARKER == "GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1=true"
    assert SCHEMA_VERSION == "governed_futures_universe_snapshot.v1"
    assert PRODUCER_VERSION == "governed_futures_universe_producer.v1"
    assert VENUE == "okx_eea"
    assert ALPHA_ALLOWED_DEFAULT is False
    assert RANKING_AUTHORITY_ADDED is False
    assert SELECTION_AUTHORITY_ADDED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert VOLATILITY_NUMERIC_MAX_AGE_ENFORCING is False
    assert FORBIDDEN_CALL_GRAPH_TARGETS.isdisjoint(set(CALL_GRAPH))
    assert RECON_CALL_GRAPH_STEP not in CALL_GRAPH


def test_valid_eligible_perpetual_future() -> None:
    result = _produce([_perp()])
    assert result.ok is True
    assert result.snapshot.universe_status == UNIVERSE_STATUS_ELIGIBLE
    assert result.snapshot.eligible_instrument_count == 1
    assert result.snapshot.alpha_allowed is False
    row = result.snapshot.instruments[0]
    assert row.venue == "okx_eea"
    assert row.venue_native_inst_id == "ETH-USDT-SWAP"
    assert row.eligibility is True
    assert row.tick_size == "0.01"
    assert row.lot_size == "1"
    assert row.contract_value == "0.01"
    assert row.perpetual_or_expiry_semantics == "perpetual"
    assert row.mark_price_supported is True
    assert row.canonical_instrument_id.startswith("okx_eea:linear_perpetual:ETH:USDT:USDT:")


def test_valid_dated_future() -> None:
    result = _produce([_dated()])
    assert result.ok is True
    row = result.snapshot.instruments[0]
    assert row.perpetual_or_expiry_semantics == "expiry"
    assert row.expiry_time
    assert row.contract_type == "linear_dated_future"


def test_spot_exclusion() -> None:
    result = _produce([_perp(inst_type="SPOT", inst_id="ETH-USDT")])
    assert result.snapshot.eligible_instrument_count == 0
    assert (
        UniverseFailureCodeV1.SPOT_INSTRUMENT.value
        in result.excluded_instruments[0].exclusion_reason_codes
    )


def test_btc_exclusion() -> None:
    result = _produce([_perp(inst_id="BTC-USDT-SWAP", base="BTC", ct_val_ccy="BTC")])
    assert result.snapshot.eligible_instrument_count == 0
    assert (
        UniverseFailureCodeV1.BTC_INSTRUMENT.value
        in result.excluded_instruments[0].exclusion_reason_codes
    )


def test_inactive_suspended_exclusion() -> None:
    result = _produce([_perp(state="suspend")])
    codes = result.excluded_instruments[0].exclusion_reason_codes
    assert UniverseFailureCodeV1.INACTIVE_OR_SUSPENDED.value in codes


def test_missing_and_invalid_metadata_exclusions() -> None:
    cases = [
        (_perp(tick=""), UniverseFailureCodeV1.MISSING_TICK_SIZE.value),
        (_perp(tick="-1"), UniverseFailureCodeV1.INVALID_TICK_SIZE.value),
        (_perp(lot=""), UniverseFailureCodeV1.MISSING_LOT_SIZE.value),
        (_perp(lot="0"), UniverseFailureCodeV1.INVALID_LOT_SIZE.value),
        (_perp(ct_val=""), UniverseFailureCodeV1.MISSING_CONTRACT_VALUE.value),
        (_perp(ct_val="-2"), UniverseFailureCodeV1.INVALID_CONTRACT_VALUE.value),
        (_perp(state=""), UniverseFailureCodeV1.UNKNOWN_TRADING_STATUS.value),
        (_perp(ct_val_ccy=""), UniverseFailureCodeV1.MISSING_CONTRACT_VALUE_CURRENCY.value),
    ]
    for row, code in cases:
        result = _produce([row])
        assert code in result.excluded_instruments[0].exclusion_reason_codes


def test_mark_price_unsupported() -> None:
    result = produce_governed_futures_universe_v1(
        source_payload=_payload([_perp()]),
        mark_price_payload=_marks(),  # empty marks
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    )
    assert UniverseFailureCodeV1.MARK_PRICE_UNSUPPORTED.value in (
        result.excluded_instruments[0].exclusion_reason_codes
    )


def test_stale_source_event_time() -> None:
    result = produce_governed_futures_universe_v1(
        source_payload=_payload([_perp()]),
        mark_price_payload=_marks("ETH-USDT-SWAP"),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time="1000",
        max_source_age_seconds=60.0,
    )
    assert UniverseFailureCodeV1.STALE_SOURCE_EVENT_TIME.value in (
        result.excluded_instruments[0].exclusion_reason_codes
    )


def test_missing_native_inst_id_and_malformed_and_unavailable() -> None:
    r1 = _produce([_perp(inst_id="")])
    assert UniverseFailureCodeV1.MISSING_NATIVE_INST_ID.value in (
        r1.excluded_instruments[0].exclusion_reason_codes
    )
    r2 = produce_governed_futures_universe_v1(
        source_payload={"code": "0", "data": "not-a-list"},
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    )
    assert UniverseFailureCodeV1.MALFORMED_SOURCE_PAYLOAD.value in r2.failure_codes
    r3 = produce_governed_futures_universe_v1(
        source_payload=None,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert UniverseFailureCodeV1.OKX_SOURCE_UNAVAILABLE.value in r3.failure_codes


def test_unsupported_instrument_type() -> None:
    result = _produce([_perp(inst_type="OPTION", inst_id="ETH-USD-OPTION")])
    assert UniverseFailureCodeV1.UNSUPPORTED_INSTRUMENT_TYPE.value in (
        result.excluded_instruments[0].exclusion_reason_codes
    )


def test_deterministic_ordering_and_digest() -> None:
    rows = [_perp("SOL-USDT-SWAP", base="SOL", ct_val_ccy="SOL"), _perp("ETH-USDT-SWAP")]
    first = _produce(rows)
    second = _produce(list(reversed(rows)))
    assert [r.canonical_instrument_id for r in first.snapshot.instruments] == [
        r.canonical_instrument_id for r in second.snapshot.instruments
    ]
    assert first.snapshot.payload_digest == second.snapshot.payload_digest
    assert first.snapshot.source_digest == second.snapshot.source_digest


def test_duplicate_and_conflicting_ids() -> None:
    dup = _produce([_perp(), _perp()])
    assert dup.snapshot.eligible_instrument_count == 0
    assert any(
        UniverseFailureCodeV1.DUPLICATE_INSTRUMENT.value in r.exclusion_reason_codes
        for r in dup.excluded_instruments
    )


def test_empty_eligible_universe_fail_closed() -> None:
    result = _produce([_perp(inst_id="BTC-USDT-SWAP", base="BTC", ct_val_ccy="BTC")])
    assert result.snapshot.universe_status == UNIVERSE_STATUS_EMPTY
    assert result.snapshot.alpha_allowed is False
    assert UniverseFailureCodeV1.EMPTY_ELIGIBLE_UNIVERSE.value in result.failure_codes


def test_atomic_persistence_restart_and_replay(tmp_path: Path) -> None:
    out = run_governed_futures_universe_producer_v1(
        state_root=tmp_path,
        source_payload=_payload([_perp(), _dated()]),
        mark_price_payload=_marks("ETH-USDT-SWAP", "ETH-USDT-250328"),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
        session_id="sess-1",
    )
    assert out["ok"] is True
    assert out["alpha_allowed"] is False
    assert out["restart"]["identical_canonical_truth"] is True
    assert out["restart"]["alpha_allowed_after_restart"] is False
    assert out["evidence"]["deterministic_replay_verification"]["ok"] is True
    verify_manifest(tmp_path)
    loaded = load_and_validate_universe_snapshot_v1(
        tmp_path,
        expected_repository_sha=REPO_SHA,
        expected_config_digest=out["snapshot"]["config_digest"],
    )
    assert loaded.ok is True
    assert loaded.snapshot is not None
    assert loaded.snapshot.payload_digest == out["snapshot"]["payload_digest"]


def test_corruption_schema_sha_config_mismatch(tmp_path: Path) -> None:
    run_governed_futures_universe_producer_v1(
        state_root=tmp_path,
        source_payload=_payload([_perp()]),
        mark_price_payload=_marks("ETH-USDT-SWAP"),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
        session_id="sess-ok",
    )
    path = tmp_path / SNAPSHOT_FILENAME
    payload = json.loads(path.read_text(encoding="utf-8"))

    # Corrupt digest
    payload["payload_digest"] = "0" * 64
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    corrupt = load_and_validate_universe_snapshot_v1(tmp_path, require_manifest=False)
    assert UniverseFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value in corrupt.failure_codes

    # Schema mismatch
    payload["payload_digest"] = GovernedFuturesUniverseSnapshotV1.from_dict(
        {**payload, "payload_digest": ""}
    ).compute_payload_digest()  # may still fail schema
    payload["schema_version"] = "wrong.v0"
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    schema = load_and_validate_universe_snapshot_v1(tmp_path, require_manifest=False)
    assert UniverseFailureCodeV1.SCHEMA_MISMATCH.value in schema.failure_codes

    # Rewrite good snapshot then validate with wrong expected sha / config digest.
    good = produce_governed_futures_universe_v1(
        source_payload=_payload([_perp()]),
        mark_price_payload=_marks("ETH-USDT-SWAP"),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    ).snapshot
    path.write_text(json.dumps(good.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    sha_check = load_and_validate_universe_snapshot_v1(
        tmp_path,
        expected_repository_sha="deadbeef",
        require_manifest=False,
    )
    assert UniverseFailureCodeV1.REPOSITORY_SHA_MISMATCH.value in sha_check.failure_codes

    cfg = compute_config_digest_v1(repository_sha=REPO_SHA, max_source_age_seconds=1.0)
    cfg_check = load_and_validate_universe_snapshot_v1(
        tmp_path,
        expected_config_digest=cfg,
        require_manifest=False,
    )
    assert UniverseFailureCodeV1.CONFIG_DIGEST_MISMATCH.value in cfg_check.failure_codes


def test_duplicate_writer_rejection(tmp_path: Path) -> None:
    first = GovernedUniverseSingleWriterV1(state_root=tmp_path, session_id="a")
    first.acquire(now_unix=OBSERVED_UNIX)
    second = GovernedUniverseSingleWriterV1(state_root=tmp_path, session_id="b")
    with pytest.raises(DuplicateUniverseWriterError):
        second.acquire(now_unix=OBSERVED_UNIX)
    out = run_governed_futures_universe_producer_v1(
        state_root=tmp_path,
        source_payload=_payload([_perp()]),
        mark_price_payload=_marks("ETH-USDT-SWAP"),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
        session_id="c",
    )
    assert out["ok"] is False
    assert UniverseFailureCodeV1.DUPLICATE_PRODUCER_WRITER.value in out["failure_codes"]
    first.release()


def test_persistence_write_failure_and_partial(tmp_path: Path) -> None:
    fail = run_governed_futures_universe_producer_v1(
        state_root=tmp_path / "fail",
        source_payload=_payload([_perp()]),
        mark_price_payload=_marks("ETH-USDT-SWAP"),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
        session_id="wf",
        simulate_write_failure=True,
    )
    assert UniverseFailureCodeV1.PERSISTENCE_WRITE_FAILURE.value in fail["failure_codes"]

    partial = run_governed_futures_universe_producer_v1(
        state_root=tmp_path / "partial",
        source_payload=_payload([_perp()]),
        mark_price_payload=_marks("ETH-USDT-SWAP"),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
        session_id="pw",
        simulate_partial_write=True,
    )
    assert UniverseFailureCodeV1.PARTIAL_WRITE.value in partial["failure_codes"]


def test_dashboard_independence_and_no_ranking_selection_authority() -> None:
    result = produce_governed_futures_universe_v1(
        source_payload={
            "code": "0",
            "data": [_perp()],
            "universe_selection_readmodel": {"selected": "ETH"},
        },
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
        source_kind="dashboard_readmodel",
    )
    assert UniverseFailureCodeV1.DASHBOARD_INPUT_FORBIDDEN.value in result.failure_codes
    good = _produce([_perp()])
    auth = good.snapshot.authority
    assert auth["DASHBOARD_AUTHORITY"] is False
    assert auth["RANKING_AUTHORITY_ADDED"] is False
    assert auth["SELECTION_AUTHORITY_ADDED"] is False
    assert auth["ALPHA_AUTHORITY_ADDED"] is False
    assert auth["EXECUTION_AUTHORITY_ADDED"] is False
    assert auth["LEGACY_PARALLEL_AUTHORITY_ABSENT"] is True
    assert auth["UNIVERSE_AUTHORITY_OWNER_SINGLE"] is True


def test_no_core_logic_mutation_surface() -> None:
    # Capability package must not import Master V2 / Double Play trading path.
    import src.ops.governed_futures_universe_producer_v1.producer_v1 as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "master_v2" not in src.lower()
    assert "double_play" not in src.lower()
    assert "ranking" not in CALL_GRAPH
    assert "selected_future" not in CALL_GRAPH


def test_failure_semantics_catalog_complete() -> None:
    required = {
        "OKX_SOURCE_UNAVAILABLE",
        "MALFORMED_SOURCE_PAYLOAD",
        "MISSING_NATIVE_INST_ID",
        "UNSUPPORTED_INSTRUMENT_TYPE",
        "SPOT_INSTRUMENT",
        "BTC_INSTRUMENT",
        "MISSING_TICK_SIZE",
        "INVALID_TICK_SIZE",
        "MISSING_LOT_SIZE",
        "INVALID_LOT_SIZE",
        "MISSING_CONTRACT_VALUE",
        "INVALID_CONTRACT_VALUE",
        "UNKNOWN_TRADING_STATUS",
        "MARK_PRICE_UNSUPPORTED",
        "STALE_SOURCE_EVENT_TIME",
        "DUPLICATE_INSTRUMENT",
        "CONFLICTING_NATIVE_IDS",
        "CONFLICTING_CANONICAL_IDS",
        "EMPTY_ELIGIBLE_UNIVERSE",
        "PERSISTENCE_WRITE_FAILURE",
        "PARTIAL_WRITE",
        "CORRUPT_PERSISTED_SNAPSHOT",
        "SCHEMA_MISMATCH",
        "REPOSITORY_SHA_MISMATCH",
        "CONFIG_DIGEST_MISMATCH",
        "DUPLICATE_PRODUCER_WRITER",
    }
    assert required.issubset(ALL_FAILURE_CODES)


def test_restart_helper_identical(tmp_path: Path) -> None:
    produced = _produce([_perp()])
    writer = GovernedUniverseSingleWriterV1(state_root=tmp_path, session_id="r")
    writer.acquire(now_unix=OBSERVED_UNIX)
    from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
        persist_universe_bundle_atomic_v1,
    )

    persist_universe_bundle_atomic_v1(
        state_root=tmp_path,
        writer=writer,
        snapshot=produced.snapshot,
        evidence={"capability_id": CAPABILITY_ID},
    )
    writer.release()
    proof = prove_restart_load_v1(state_root=tmp_path, expected_snapshot=produced.snapshot)
    assert proof["ok"] is True
    assert proof["alpha_allowed_after_restart"] is False


def test_venue_not_okx_eea() -> None:
    result = produce_governed_futures_universe_v1(
        source_payload=_payload([_perp()]),
        mark_price_payload=_marks("ETH-USDT-SWAP"),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
        venue="binance",
    )
    assert UniverseFailureCodeV1.VENUE_NOT_OKX_EEA.value in result.failure_codes
