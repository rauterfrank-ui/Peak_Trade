"""Offline provenance boundaries. Synthetic rows are not exchange truth."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.h1_get_evidence_admission_v1.constants_v1 import (
    ACCOUNT_FLAT_UNPROVEN,
    CONTRACT_PAGINATION_TERMINAL_SOURCES,
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_FILLS,
    ENDPOINT_ORDERS_HISTORY,
    ENDPOINT_ORDERS_PENDING,
    EXCHANGE_TRUTH_UNPROVEN,
    PRIVATE_GET_FRESHNESS_SOURCE_TYPE,
    REASON_ACCOUNT_IDENTITY_ABSENT,
    REASON_ACCOUNT_IDENTITY_MISMATCH,
    REASON_DUPLICATE_FILL_CONFLICT,
    REASON_FRESHNESS_THRESHOLD_UNRATIFIED,
    REASON_PAGINATION_TERMINAL_ABSENT,
    REASON_REST_WS_CONSISTENCY_UNPROVEN,
    REASON_TEMPORAL_INCONSISTENCY,
    REASON_VENUE_TIMESTAMP_ABSENT,
    REASON_VENUE_TIMESTAMP_CONTRADICTION,
    REASON_VENUE_TIMESTAMP_NOT_PAYLOAD_WITNESS,
    REST_WS_CONSISTENCY_UNPROVEN,
    STATUS_ADMITTED,
    STATUS_UNKNOWN_BLOCKED,
)
from src.ops.h1_get_evidence_admission_v1.provenance_v1 import (
    account_wide_position_completeness_proven_v1,
    bind_venue_and_capture_clocks_v1,
    classify_fills_v1,
    private_get_freshness_ratified_v1,
    venue_timestamp_from_payload_v1,
)
from src.ops.h1_get_evidence_admission_v1.validate_v1 import (
    AdmissionParametersV1,
    CapturedGetResponseV1,
    validate_get_evidence_admission_v1,
)
from src.ops.okx_captured_at_freshness_policy_v1 import CONFIG_RELATIVE_PATH
from src.ops.okx_eea_private_account_state_runtime_v1.state_contracts_v1 import body_digest

REPO = Path(__file__).resolve().parents[2]
NOW_MS = 1_700_000_000_000
ACCOUNT_UID = "10001"
INSTRUMENT_ID = "ETH-USDT-SWAP"
WINDOW_ID = "admission-window-1"
PROVENANCE = REPO / "src/ops/h1_get_evidence_admission_v1/provenance_v1.py"


def _params(**overrides: object) -> AdmissionParametersV1:
    values: dict[str, object] = {
        "bound_account_uid": ACCOUNT_UID,
        "bound_instrument_id": INSTRUMENT_ID,
        "freshness_window_ms": 1_000,
        "admission_time_ms": NOW_MS,
        "admission_window_id": WINDOW_ID,
        "admission_window_start_ms": NOW_MS - 5_000,
        "admission_window_end_ms": NOW_MS + 5_000,
    }
    values.update(overrides)
    return AdmissionParametersV1(**values)


def _captured(
    endpoint: str,
    rows: list[dict[str, object]],
    *,
    params: dict[str, str] | None = None,
    venue_timestamp_ms: int | None = NOW_MS,
    captured_at_ms: int | None = NOW_MS + 10,
    extra: dict[str, object] | None = None,
) -> CapturedGetResponseV1:
    payload: dict[str, object] = {"code": "0", "data": rows}
    if extra:
        payload.update(extra)
    if params is None:
        params = (
            {}
            if endpoint in {ENDPOINT_ACCOUNT_CONFIG, ENDPOINT_ACCOUNT_BALANCE}
            else {"instId": INSTRUMENT_ID}
        )
    return CapturedGetResponseV1(
        endpoint=endpoint,
        request_params=params,
        payload=payload,
        body_digest=body_digest(payload),
        captured_at_ms=captured_at_ms,
        venue_timestamp_ms=venue_timestamp_ms,
        pagination_terminal=None,
        pagination_terminal_source=None,
        pagination_chain_status=None,
        admission_window_id=WINDOW_ID,
    )


def _payload_backed() -> tuple[CapturedGetResponseV1, ...]:
    row_time = {"uTime": str(NOW_MS)}
    return (
        _captured(
            ENDPOINT_ACCOUNT_CONFIG,
            [{"uid": ACCOUNT_UID, "mainUid": ACCOUNT_UID, "acctLv": "2", **row_time}],
        ),
        _captured(ENDPOINT_ACCOUNT_BALANCE, [{"totalEq": "1", **row_time}]),
        _captured(
            ENDPOINT_ACCOUNT_POSITIONS,
            [{"instId": INSTRUMENT_ID, "pos": "1", **row_time}],
        ),
        _captured(
            ENDPOINT_ORDERS_PENDING,
            [{"instId": INSTRUMENT_ID, "ordId": "1", **row_time}],
        ),
        _captured(
            ENDPOINT_ORDERS_HISTORY,
            [{"instId": INSTRUMENT_ID, "ordId": "2", "uTime": str(NOW_MS - 20)}],
            venue_timestamp_ms=NOW_MS - 20,
        ),
        _captured(
            ENDPOINT_FILLS,
            [{"instId": INSTRUMENT_ID, "tradeId": "T1", "fillSz": "1", **row_time}],
        ),
    )


def test_config_uid_is_the_only_account_provenance() -> None:
    pilot = (
        REPO
        / "src/ops/full_core_live_path_composition_root_v1"
        / "current_productive_pilot_capital_guard_post_bind_v1.py"
    ).read_text(encoding="utf-8")
    bound = (
        REPO / "src/ops/full_core_live_path_composition_root_v1/live_account_bound_v1.py"
    ).read_text(encoding="utf-8")
    assert 'uid = str(data[0].get("uid") or "").strip()' in pilot
    assert 'ACCOUNT_UID_ITEM_IDS: frozenset[str] = frozenset({"POS_MODE", "ACCOUNT_MODE"})' in bound
    mode_only = _payload_backed()
    replaced = tuple(
        _captured(
            ENDPOINT_ACCOUNT_CONFIG, [{"acctLv": "2", "posMode": "net_mode", "uTime": str(NOW_MS)}]
        )
        if item.endpoint == ENDPOINT_ACCOUNT_CONFIG
        else item
        for item in mode_only
    )
    result = validate_get_evidence_admission_v1(replaced, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_ACCOUNT_IDENTITY_ABSENT in result.reason_codes
    assert "ACCOUNT_IDENTITY" not in result.satisfied_proofs


def test_integer_config_uid_matches_and_main_uid_disagreement_blocks() -> None:
    responses = tuple(
        _captured(ENDPOINT_ACCOUNT_CONFIG, [{"uid": 10001, "uTime": str(NOW_MS)}])
        if item.endpoint == ENDPOINT_ACCOUNT_CONFIG
        else item
        for item in _payload_backed()
    )
    matched = validate_get_evidence_admission_v1(responses, _params())
    assert "ACCOUNT_IDENTITY" in matched.satisfied_proofs
    conflicted = tuple(
        _captured(
            ENDPOINT_ACCOUNT_CONFIG,
            [{"uid": ACCOUNT_UID, "mainUid": "99999", "uTime": str(NOW_MS)}],
        )
        if item.endpoint == ENDPOINT_ACCOUNT_CONFIG
        else item
        for item in _payload_backed()
    )
    result = validate_get_evidence_admission_v1(conflicted, _params())
    assert REASON_ACCOUNT_IDENTITY_MISMATCH in result.reason_codes
    assert result.status == STATUS_UNKNOWN_BLOCKED


def test_balance_uid_cannot_mint_identity_and_disagreement_blocks() -> None:
    missing_config = tuple(
        _captured(ENDPOINT_ACCOUNT_CONFIG, [{"acctLv": "2", "uTime": str(NOW_MS)}])
        if item.endpoint == ENDPOINT_ACCOUNT_CONFIG
        else _captured(
            ENDPOINT_ACCOUNT_BALANCE, [{"uid": ACCOUNT_UID, "totalEq": "1", "uTime": str(NOW_MS)}]
        )
        if item.endpoint == ENDPOINT_ACCOUNT_BALANCE
        else item
        for item in _payload_backed()
    )
    minted = validate_get_evidence_admission_v1(missing_config, _params())
    assert REASON_ACCOUNT_IDENTITY_ABSENT in minted.reason_codes
    assert REASON_ACCOUNT_IDENTITY_MISMATCH in minted.reason_codes
    foreign = tuple(
        _captured(
            ENDPOINT_ACCOUNT_BALANCE,
            [{"uid": "10002", "totalEq": "1", "uTime": str(NOW_MS)}],
        )
        if item.endpoint == ENDPOINT_ACCOUNT_BALANCE
        else item
        for item in _payload_backed()
    )
    result = validate_get_evidence_admission_v1(foreign, _params())
    assert REASON_ACCOUNT_IDENTITY_MISMATCH in result.reason_codes


def test_venue_time_comes_only_from_row_clocks_and_stays_separate_from_capture() -> None:
    payload = {"code": "0", "data": [{"uTime": str(NOW_MS), "cTime": NOW_MS}]}
    assert venue_timestamp_from_payload_v1(payload) == NOW_MS
    assert venue_timestamp_from_payload_v1({"code": "0", "ts": str(NOW_MS), "data": [{}]}) is None
    assert (
        venue_timestamp_from_payload_v1(
            {"code": "0", "data": [{"uTime": str(NOW_MS), "cTime": str(NOW_MS + 1)}]}
        )
        is None
    )
    derived, reasons = bind_venue_and_capture_clocks_v1({"code": "0", "data": [{}]}, NOW_MS)
    assert derived is None
    assert REASON_VENUE_TIMESTAMP_ABSENT in reasons
    assert REASON_VENUE_TIMESTAMP_NOT_PAYLOAD_WITNESS in reasons
    derived, reasons = bind_venue_and_capture_clocks_v1(payload, NOW_MS + 1)
    assert derived == NOW_MS
    assert REASON_VENUE_TIMESTAMP_CONTRADICTION in reasons
    text = PROVENANCE.read_text(encoding="utf-8")
    assert "datetime.now" not in text
    assert "utc_now" not in text


def test_private_get_freshness_threshold_is_not_ratified() -> None:
    policy = json.loads((REPO / CONFIG_RELATIVE_PATH).read_text(encoding="utf-8"))
    thresholds = policy["freshness_thresholds_seconds"]
    assert PRIVATE_GET_FRESHNESS_SOURCE_TYPE not in thresholds
    assert "instrument_metadata" in thresholds
    assert private_get_freshness_ratified_v1() is False
    assert account_wide_position_completeness_proven_v1() is False
    assert CONTRACT_PAGINATION_TERMINAL_SOURCES == frozenset()


def test_payload_backed_proofs_do_not_admit_or_flatten() -> None:
    result = validate_get_evidence_admission_v1(_payload_backed(), _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert result.status != STATUS_ADMITTED
    assert "ACCOUNT_IDENTITY" in result.satisfied_proofs
    assert "DIGEST_INTEGRITY" in result.satisfied_proofs
    assert "INSTRUMENT_IDENTITY" in result.satisfied_proofs
    assert "TEMPORAL_CONSISTENCY" in result.satisfied_proofs
    assert "FRESHNESS" not in result.satisfied_proofs
    assert "PAGINATION_COMPLETENESS" not in result.satisfied_proofs
    assert REASON_FRESHNESS_THRESHOLD_UNRATIFIED in result.reason_codes
    assert REASON_PAGINATION_TERMINAL_ABSENT in result.reason_codes
    assert REASON_TEMPORAL_INCONSISTENCY not in result.reason_codes
    assert result.flat_emitted is False
    assert result.account_flat == ACCOUNT_FLAT_UNPROVEN
    assert result.rest_ws_consistency == REST_WS_CONSISTENCY_UNPROVEN
    assert result.exchange_truth == EXCHANGE_TRUTH_UNPROVEN
    assert result.productive_completeness is False


def test_capture_outside_declared_window_is_temporal_not_a_freshness_threshold() -> None:
    responses = tuple(
        CapturedGetResponseV1(
            endpoint=item.endpoint,
            request_params=item.request_params,
            payload=item.payload,
            body_digest=item.body_digest,
            captured_at_ms=NOW_MS + 50_000,
            venue_timestamp_ms=item.venue_timestamp_ms,
            pagination_terminal=item.pagination_terminal,
            pagination_terminal_source=item.pagination_terminal_source,
            pagination_chain_status=item.pagination_chain_status,
            admission_window_id=item.admission_window_id,
        )
        for item in _payload_backed()
    )
    result = validate_get_evidence_admission_v1(responses, _params())
    assert REASON_TEMPORAL_INCONSISTENCY in result.reason_codes
    assert "FRESHNESS" not in result.satisfied_proofs
    assert result.status == STATUS_UNKNOWN_BLOCKED


def test_private_ws_envelope_is_not_rest_consistency() -> None:
    responses = tuple(
        _captured(
            ENDPOINT_ACCOUNT_BALANCE,
            [{"totalEq": "1", "uTime": str(NOW_MS)}],
            extra={"arg": {"channel": "account"}},
        )
        if item.endpoint == ENDPOINT_ACCOUNT_BALANCE
        else item
        for item in _payload_backed()
    )
    result = validate_get_evidence_admission_v1(responses, _params())
    assert REASON_REST_WS_CONSISTENCY_UNPROVEN in result.reason_codes
    assert result.rest_ws_consistency == REST_WS_CONSISTENCY_UNPROVEN
    assert result.status == STATUS_UNKNOWN_BLOCKED


def test_identical_fill_rows_are_one_fact_and_conflicts_block() -> None:
    row = {"instId": INSTRUMENT_ID, "tradeId": "T1", "fillSz": "1"}
    count, reasons = classify_fills_v1(
        [row, dict(row)], window_start_ms=0, window_end_ms=1, bounds_ok=False
    )
    assert count == 1
    assert reasons == set()
    count, reasons = classify_fills_v1(
        [row, {"instId": INSTRUMENT_ID, "tradeId": "T1", "fillSz": "2"}],
        window_start_ms=0,
        window_end_ms=1,
        bounds_ok=False,
    )
    assert REASON_DUPLICATE_FILL_CONFLICT in reasons
    assert count == 1


def test_empty_instrument_scope_is_not_account_flat() -> None:
    responses = tuple(
        _captured(ENDPOINT_ACCOUNT_POSITIONS, [])
        if item.endpoint == ENDPOINT_ACCOUNT_POSITIONS
        else item
        for item in _payload_backed()
    )
    result = validate_get_evidence_admission_v1(responses, _params())
    assert result.position_inventory == "UNPROVEN"
    assert result.flat_emitted is False
    assert result.account_flat == ACCOUNT_FLAT_UNPROVEN
    assert result.status == STATUS_UNKNOWN_BLOCKED
