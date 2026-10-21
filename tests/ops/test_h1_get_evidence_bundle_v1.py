"""Offline bundle tests. Synthetic admission is not productive OKX truth."""

from __future__ import annotations

import ast
from pathlib import Path

from src.ops.h1_get_evidence_admission_v1.bundle_v1 import (
    OFFLINE_PAGE_BUDGET_V1,
    STATUS_CONTRADICTORY_PAGES,
    STATUS_PAGE_BUDGET_EXCEEDED,
    STATUS_REPEATED_CURSOR,
    STATUS_UNPROVEN,
    admit_offline_get_evidence_v1,
    assess_pagination_v1,
    collect_bounded_pagination_capture_v1,
    venue_timestamp_from_payload_v1,
)
from src.ops.h1_get_evidence_admission_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_FILLS,
    ENDPOINT_ORDERS_HISTORY,
    ENDPOINT_ORDERS_PENDING,
    EXTERNAL_EFFECT_AUTHORIZED,
    INVENTORY_ATTESTED_ZERO,
    INVENTORY_UNPROVEN,
    POST_ALLOWED,
    PRODUCTIVE_ACTIVATION,
    PRODUCTIVE_COMPLETENESS,
    REASON_ACCOUNT_IDENTITY_ABSENT,
    REASON_ACCOUNT_IDENTITY_MISMATCH,
    REASON_ACCOUNT_PARAMETER_ABSENT,
    REASON_DUPLICATE_FILL_CONFLICT,
    REASON_EMPTY_POSITIONS_WITHOUT_COMPLETENESS,
    REASON_INSTRUMENT_MISMATCH,
    REASON_LATE_FILL_OUTSIDE_WINDOW,
    REASON_PAGINATION_TERMINAL_ABSENT,
    REASON_STALE_EVIDENCE,
    REASON_VENUE_TIMESTAMP_ABSENT,
    STATUS_ADMITTED,
    STATUS_UNKNOWN_BLOCKED,
    WRITER_HANDOFF,
)
from src.ops.h1_get_evidence_admission_v1.validate_v1 import (
    AdmissionParametersV1,
    CapturedGetResponseV1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.rest_baseline_v1 import (
    admission_capture_record_v1,
    collect_optional_admission_capture_v1,
    collect_rest_baseline_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.runtime_orchestrator_v1 import (
    OkxEeaPrivateAccountStateRuntimeV1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.state_contracts_v1 import body_digest

NOW_MS = 1_700_000_000_000
FRESHNESS_MS = 1_000
ACCOUNT_UID = "10001"
OTHER_UID = "10002"
INSTRUMENT_ID = "ETH-USDT-SWAP"
OTHER_INSTRUMENT_ID = "BTC-USDT-SWAP"
WINDOW_ID = "admission-window-1"
PACKAGE = Path(__file__).resolve().parents[2] / "src/ops/h1_get_evidence_admission_v1"
ORCHESTRATOR = (
    Path(__file__).resolve().parents[2]
    / "src/ops/okx_eea_private_account_state_runtime_v1/runtime_orchestrator_v1.py"
)


def _params(**overrides: object) -> AdmissionParametersV1:
    values: dict[str, object] = {
        "bound_account_uid": ACCOUNT_UID,
        "bound_instrument_id": INSTRUMENT_ID,
        "freshness_window_ms": FRESHNESS_MS,
        "admission_time_ms": NOW_MS,
        "admission_window_id": WINDOW_ID,
        "admission_window_start_ms": NOW_MS - FRESHNESS_MS,
        "admission_window_end_ms": NOW_MS + FRESHNESS_MS,
    }
    values.update(overrides)
    return AdmissionParametersV1(**values)


def _body(rows: list[dict[str, object]]) -> dict[str, object]:
    return {"code": "0", "data": rows}


def _record(
    endpoint: str,
    rows: list[dict[str, object]],
    params: dict[str, str] | None = None,
    *,
    captured_at_ms: int | None = NOW_MS,
):
    return admission_capture_record_v1(
        endpoint,
        {} if params is None else params,
        _body(rows),
        captured_at_ms=captured_at_ms,
    )


def _eea_fixture(path: str, params: dict[str, str]) -> dict[str, object]:
    del params
    if path == ENDPOINT_ACCOUNT_CONFIG:
        return _body([{"acctLv": "2", "posMode": "net_mode"}])
    if path == ENDPOINT_ACCOUNT_BALANCE:
        return _body([{"totalEq": "100", "details": [{"ccy": "USDT", "availEq": "90"}]}])
    if path == ENDPOINT_ACCOUNT_POSITIONS:
        return _body([{"instId": INSTRUMENT_ID, "pos": "1", "posSide": "net", "avgPx": "100"}])
    if path in {ENDPOINT_ORDERS_PENDING, ENDPOINT_ORDERS_HISTORY}:
        return _body([{"instId": INSTRUMENT_ID, "ordId": "1", "clOrdId": "c1", "state": "live"}])
    if path == ENDPOINT_FILLS:
        return _body(
            [
                {
                    "instId": INSTRUMENT_ID,
                    "tradeId": "t1",
                    "ordId": "1",
                    "clOrdId": "c1",
                    "fillSz": "1",
                    "fillPx": "100",
                }
            ]
        )
    if path.endswith("leverage-info") or path.endswith("max-size"):
        return _body([{}])
    raise AssertionError(path)


def _synthetic(
    endpoint: str,
    rows: list[dict[str, object]],
    *,
    inst_id: str = INSTRUMENT_ID,
    terminal: bool | None = None,
    source: str | None = None,
    venue_timestamp_ms: int | None = NOW_MS,
    captured_at_ms: int | None = NOW_MS,
) -> CapturedGetResponseV1:
    payload = _body(rows)
    params = (
        {}
        if endpoint in {ENDPOINT_ACCOUNT_CONFIG, ENDPOINT_ACCOUNT_BALANCE}
        else {"instId": inst_id}
    )
    if endpoint not in {ENDPOINT_ACCOUNT_CONFIG, ENDPOINT_ACCOUNT_BALANCE}:
        if terminal is None:
            terminal = True
        if source is None and terminal is True:
            source = "synthetic_offline_marker"
    return CapturedGetResponseV1(
        endpoint=endpoint,
        request_params=params,
        payload=payload,
        body_digest=body_digest(payload),
        captured_at_ms=captured_at_ms,
        venue_timestamp_ms=venue_timestamp_ms,
        pagination_terminal=terminal,
        pagination_terminal_source=source,
        admission_window_id=WINDOW_ID,
    )


def _synthetic_set(
    *,
    position_rows: list[dict[str, object]] | None = None,
    fill_rows: list[dict[str, object]] | None = None,
) -> tuple[CapturedGetResponseV1, ...]:
    if position_rows is None:
        position_rows = [{"instId": INSTRUMENT_ID, "pos": "1"}]
    if fill_rows is None:
        fill_rows = [{"instId": INSTRUMENT_ID, "tradeId": "T1", "fillSz": "1", "fillPx": "2"}]
    return (
        _synthetic(ENDPOINT_ACCOUNT_CONFIG, [{"uid": ACCOUNT_UID, "acctLv": "2"}]),
        _synthetic(ENDPOINT_ACCOUNT_BALANCE, [{"uid": ACCOUNT_UID, "totalEq": "1"}]),
        _synthetic(ENDPOINT_ACCOUNT_POSITIONS, position_rows),
        _synthetic(ENDPOINT_ORDERS_PENDING, []),
        _synthetic(ENDPOINT_ORDERS_HISTORY, []),
        _synthetic(ENDPOINT_FILLS, fill_rows),
    )


def _scoped(endpoint: str, rows: list[dict[str, object]], inst_id: str = INSTRUMENT_ID):
    params = (
        {}
        if endpoint in {ENDPOINT_ACCOUNT_CONFIG, ENDPOINT_ACCOUNT_BALANCE}
        else {"instId": inst_id}
    )
    return _record(endpoint, rows, params)


def test_eea_fixture_capture_stays_unknown_blocked() -> None:
    records = collect_optional_admission_capture_v1(
        _eea_fixture,
        inst_id=INSTRUMENT_ID,
        inst_type="SWAP",
        captured_at_ms=NOW_MS,
    )
    result = admit_offline_get_evidence_v1(records, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_ACCOUNT_IDENTITY_ABSENT in result.reason_codes
    assert REASON_PAGINATION_TERMINAL_ABSENT in result.reason_codes
    assert result.position_inventory == INVENTORY_UNPROVEN
    assert result.productive_completeness is False


def test_synthetic_evidence_can_be_admitted_offline_without_productive_truth() -> None:
    result = admit_offline_get_evidence_v1(None, _params(), synthetic_responses=_synthetic_set())
    assert result.status == STATUS_ADMITTED
    assert result.productive_completeness is PRODUCTIVE_COMPLETENESS is False
    assert result.productive_activation is PRODUCTIVE_ACTIVATION is False
    assert result.authority_effect == AUTHORITY_EFFECT == "NONE"
    assert result.post_allowed is POST_ALLOWED is False
    assert result.external_effect_authorized is EXTERNAL_EFFECT_AUTHORIZED is False
    assert result.flat_emitted is False
    assert result.writer_handoff == WRITER_HANDOFF == "NONE"


def test_missing_config_uid_blocks() -> None:
    records = (
        _scoped(ENDPOINT_ACCOUNT_CONFIG, [{"acctLv": "2"}]),
        _scoped(ENDPOINT_ACCOUNT_BALANCE, [{"uid": ACCOUNT_UID, "totalEq": "1"}]),
    )
    result = admit_offline_get_evidence_v1(records, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_ACCOUNT_IDENTITY_ABSENT in result.reason_codes


def test_missing_balance_uid_blocks_without_projection() -> None:
    records = (
        _scoped(ENDPOINT_ACCOUNT_CONFIG, [{"uid": ACCOUNT_UID, "acctLv": "2"}]),
        _scoped(ENDPOINT_ACCOUNT_BALANCE, [{"totalEq": "1"}]),
    )
    result = admit_offline_get_evidence_v1(records, _params())
    balance = next(item for item in records if item.endpoint == ENDPOINT_ACCOUNT_BALANCE)
    assert "uid" not in balance.payload["data"][0]
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_ACCOUNT_IDENTITY_ABSENT in result.reason_codes


def test_uid_mismatch_blocks() -> None:
    records = (
        _scoped(ENDPOINT_ACCOUNT_CONFIG, [{"uid": ACCOUNT_UID}]),
        _scoped(ENDPOINT_ACCOUNT_BALANCE, [{"uid": OTHER_UID}]),
    )
    result = admit_offline_get_evidence_v1(records, _params())
    assert REASON_ACCOUNT_IDENTITY_MISMATCH in result.reason_codes
    assert result.status == STATUS_UNKNOWN_BLOCKED


def test_instrument_mismatch_blocks() -> None:
    records = (
        _scoped(
            ENDPOINT_ACCOUNT_POSITIONS,
            [{"instId": OTHER_INSTRUMENT_ID, "pos": "1"}],
            OTHER_INSTRUMENT_ID,
        ),
    )
    result = admit_offline_get_evidence_v1(records, _params())
    assert REASON_INSTRUMENT_MISMATCH in result.reason_codes
    assert result.status == STATUS_UNKNOWN_BLOCKED


def test_missing_venue_timestamp_blocks() -> None:
    result = admit_offline_get_evidence_v1(
        None,
        _params(),
        synthetic_responses=_synthetic_set(),
    )
    # Replace by a capture whose raw rows carry no venue time.
    records = collect_optional_admission_capture_v1(
        _eea_fixture,
        inst_id=INSTRUMENT_ID,
        inst_type="SWAP",
        captured_at_ms=NOW_MS,
    )
    blocked = admit_offline_get_evidence_v1(records, _params())
    assert result.status == STATUS_ADMITTED
    assert REASON_VENUE_TIMESTAMP_ABSENT in blocked.reason_codes
    assert blocked.status == STATUS_UNKNOWN_BLOCKED


def test_string_zero_timestamp_is_not_a_venue_time() -> None:
    payload = _body([{"uid": ACCOUNT_UID, "uTime": "0", "cTime": 0}])
    assert venue_timestamp_from_payload_v1(payload) is None
    record = admission_capture_record_v1(
        ENDPOINT_ACCOUNT_CONFIG, {}, payload, captured_at_ms=NOW_MS
    )
    result = admit_offline_get_evidence_v1((record,), _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_VENUE_TIMESTAMP_ABSENT in result.reason_codes


def test_stale_evidence_blocks() -> None:
    stale = tuple(
        CapturedGetResponseV1(
            endpoint=item.endpoint,
            request_params=item.request_params,
            payload=item.payload,
            body_digest=item.body_digest,
            captured_at_ms=NOW_MS,
            venue_timestamp_ms=NOW_MS + 50_000,
            pagination_terminal=item.pagination_terminal,
            pagination_terminal_source=item.pagination_terminal_source,
            admission_window_id=item.admission_window_id,
        )
        for item in _synthetic_set()
    )
    result = admit_offline_get_evidence_v1(None, _params(), synthetic_responses=stale)
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_STALE_EVIDENCE in result.reason_codes


def test_missing_pagination_terminal_blocks() -> None:
    records = (_scoped(ENDPOINT_ACCOUNT_POSITIONS, [{"instId": INSTRUMENT_ID, "pos": "1"}]),)
    assessment = assess_pagination_v1(ENDPOINT_ACCOUNT_POSITIONS, records)
    assert assessment.status == STATUS_UNPROVEN
    assert assessment.pagination_terminal is None
    result = admit_offline_get_evidence_v1(records, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_PAGINATION_TERMINAL_ABSENT in result.reason_codes


def test_repeated_cursor_blocks_without_merge() -> None:
    first = _record(
        ENDPOINT_FILLS,
        [{"instId": INSTRUMENT_ID, "tradeId": "T1", "fillSz": "1"}],
        {"instId": INSTRUMENT_ID, "after": "CUR"},
    )
    second = _record(
        ENDPOINT_FILLS,
        [{"instId": INSTRUMENT_ID, "tradeId": "T2", "fillSz": "1"}],
        {"instId": INSTRUMENT_ID, "after": "CUR"},
    )
    assessment = assess_pagination_v1(ENDPOINT_FILLS, (first, second))
    assert assessment.status == STATUS_REPEATED_CURSOR
    result = admit_offline_get_evidence_v1((first, second), _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert result.fill_fact_count == 0


def test_contradictory_pages_block() -> None:
    first = _record(
        ENDPOINT_ORDERS_PENDING,
        [{"instId": INSTRUMENT_ID, "ordId": "1", "state": "live"}],
        {"instId": INSTRUMENT_ID, "after": "A"},
    )
    second = _record(
        ENDPOINT_ORDERS_PENDING,
        [{"instId": INSTRUMENT_ID, "ordId": "1", "state": "filled"}],
        {"instId": INSTRUMENT_ID, "after": "B"},
    )
    assessment = assess_pagination_v1(ENDPOINT_ORDERS_PENDING, (first, second))
    assert assessment.status == STATUS_CONTRADICTORY_PAGES
    result = admit_offline_get_evidence_v1((first, second), _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED


def test_page_budget_blocks() -> None:
    pages = tuple(
        _record(
            ENDPOINT_ORDERS_HISTORY,
            [{"instId": INSTRUMENT_ID, "ordId": str(index), "state": "live"}],
            {"instId": INSTRUMENT_ID, "after": f"C{index}"},
        )
        for index in range(OFFLINE_PAGE_BUDGET_V1 + 1)
    )
    assessment = assess_pagination_v1(ENDPOINT_ORDERS_HISTORY, pages)
    assert assessment.status == STATUS_PAGE_BUDGET_EXCEEDED
    result = admit_offline_get_evidence_v1(pages, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED


def test_empty_positions_without_terminal_stay_unproven() -> None:
    records = (_scoped(ENDPOINT_ACCOUNT_POSITIONS, []),)
    result = admit_offline_get_evidence_v1(records, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert result.position_inventory == INVENTORY_UNPROVEN
    assert REASON_EMPTY_POSITIONS_WITHOUT_COMPLETENESS in result.reason_codes
    assert result.flat_emitted is False


def test_synthetic_zero_inventory_does_not_emit_flat() -> None:
    result = admit_offline_get_evidence_v1(
        None,
        _params(),
        synthetic_responses=_synthetic_set(position_rows=[]),
    )
    assert result.status == STATUS_ADMITTED
    assert result.position_inventory == INVENTORY_ATTESTED_ZERO
    assert result.flat_emitted is False
    assert result.writer_handoff == "NONE"


def test_duplicate_fill_conflict_blocks() -> None:
    fills = [
        {"instId": INSTRUMENT_ID, "tradeId": "T1", "fillSz": "1", "fillPx": "2"},
        {"instId": INSTRUMENT_ID, "tradeId": "T1", "fillSz": "2", "fillPx": "3"},
    ]
    result = admit_offline_get_evidence_v1(
        None,
        _params(),
        synthetic_responses=_synthetic_set(fill_rows=fills),
    )
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_DUPLICATE_FILL_CONFLICT in result.reason_codes


def test_late_fill_blocks() -> None:
    fills = [
        {
            "instId": INSTRUMENT_ID,
            "tradeId": "T1",
            "fillSz": "1",
            "fillPx": "2",
            "fillTime": NOW_MS + 50_000,
        }
    ]
    result = admit_offline_get_evidence_v1(
        None,
        _params(),
        synthetic_responses=_synthetic_set(fill_rows=fills),
    )
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_LATE_FILL_OUTSIDE_WINDOW in result.reason_codes


def test_admission_digest_is_deterministic() -> None:
    synthetic = _synthetic_set()
    first = admit_offline_get_evidence_v1(None, _params(), synthetic_responses=synthetic)
    second = admit_offline_get_evidence_v1(
        None,
        _params(),
        synthetic_responses=tuple(reversed(synthetic)),
    )
    assert first.admission_digest == second.admission_digest
    records = collect_optional_admission_capture_v1(
        _eea_fixture,
        inst_id=INSTRUMENT_ID,
        inst_type="SWAP",
        captured_at_ms=NOW_MS,
    )
    captured_a = admit_offline_get_evidence_v1(records, _params())
    captured_b = admit_offline_get_evidence_v1(tuple(reversed(records)), _params())
    assert captured_a.admission_digest == captured_b.admission_digest


def test_baseline_snapshot_and_orchestrator_get_count_stay_unchanged(tmp_path: Path) -> None:
    calls: list[str] = []

    def fetch(path: str, params: dict[str, str]) -> dict[str, object]:
        calls.append(path)
        return _eea_fixture(path, params)

    snap = collect_rest_baseline_v1(fetch, captured_at="t0", inst_id=INSTRUMENT_ID)
    assert snap.account_config is not None
    assert snap.account_config.acct_lv == "2"
    assert snap.account_config.pos_mode == "net_mode"
    assert snap.balance is not None
    assert snap.balance.total_eq == "100"
    assert snap.positions[0].pos == "1"
    baseline_calls = list(calls)
    calls.clear()
    runtime = OkxEeaPrivateAccountStateRuntimeV1(store_root=tmp_path, rest_fetch_json=fetch)
    runtime.run_rest_baseline_v1(captured_at="t0")
    assert calls == baseline_calls
    assert "collect_optional_admission_capture_v1" not in ORCHESTRATOR.read_text(encoding="utf-8")
    assert "collect_bounded_pagination_capture_v1" not in ORCHESTRATOR.read_text(encoding="utf-8")


def test_bounded_walker_does_not_invent_terminal_or_extra_pages() -> None:
    seen: list[dict[str, str]] = []

    def fetch(path: str, params: dict[str, str]) -> dict[str, object]:
        assert path == ENDPOINT_FILLS
        seen.append(dict(params))
        return _body([{"instId": INSTRUMENT_ID, "tradeId": "T1"}])

    pages = collect_bounded_pagination_capture_v1(
        fetch,
        endpoint=ENDPOINT_FILLS,
        request_params={"instType": "SWAP", "instId": INSTRUMENT_ID, "limit": "100"},
        captured_at_ms=NOW_MS,
    )
    assert len(seen) == 1
    assert pages[0].next_cursor is None
    assert pages[0].request_limit == 100
    assessment = assess_pagination_v1(ENDPOINT_FILLS, pages)
    assert assessment.status == STATUS_UNPROVEN
    assert assessment.pagination_terminal is None


def test_missing_owner_parameters_block() -> None:
    result = admit_offline_get_evidence_v1(
        None,
        _params(bound_account_uid=None, freshness_window_ms=None),
        synthetic_responses=_synthetic_set(),
    )
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_ACCOUNT_PARAMETER_ABSENT in result.reason_codes


def test_bundle_has_no_writer_network_or_portfolio_write() -> None:
    forbidden_prefixes = (
        "http",
        "requests",
        "socket",
        "urllib",
        "trading",
        "src.trading",
        "src.execution",
        "src.risk",
    )
    forbidden_calls = {"open", "urlopen", "socket", "request"}
    forbidden_attrs = {"write_text", "write_bytes", "unlink", "mkdir"}
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                names = []
            for name in names:
                assert not name.startswith(forbidden_prefixes)
                assert "writer" not in name
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_attrs


def test_productive_activation_stays_false() -> None:
    admitted = admit_offline_get_evidence_v1(None, _params(), synthetic_responses=_synthetic_set())
    blocked = admit_offline_get_evidence_v1(None, None)
    assert admitted.productive_activation is False
    assert blocked.productive_activation is False
    assert admitted.external_effect_authorized is False
    assert blocked.post_allowed is False
