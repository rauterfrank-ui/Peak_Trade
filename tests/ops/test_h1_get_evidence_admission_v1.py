"""Offline tests for isolated GET-evidence admission. Synthetic evidence only."""

from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
from dataclasses import MISSING, fields, replace
from pathlib import Path

import pytest

from src.ops.h1_get_evidence_admission_v1.constants_v1 import (
    ACCOUNT_ENDPOINTS,
    AUTHORITY_EFFECT,
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_FILLS,
    ENDPOINT_ORDERS_HISTORY,
    ENDPOINT_ORDERS_PENDING,
    EXTERNAL_EFFECT_AUTHORIZED,
    INVENTORY_ATTESTED_ROWS,
    INVENTORY_ATTESTED_ZERO,
    INVENTORY_UNPROVEN,
    PAGINATED_ENDPOINTS,
    POSITIVE_REASON_CODES,
    POST_ALLOWED,
    PRODUCTIVE_ACTIVATION,
    PRODUCTIVE_COMPLETENESS,
    REASON_ACCOUNT_IDENTITY_ABSENT,
    REASON_ACCOUNT_IDENTITY_MALFORMED,
    REASON_ACCOUNT_IDENTITY_MISMATCH,
    REASON_ACCOUNT_PARAMETER_ABSENT,
    REASON_ADMISSION_TIME_ABSENT,
    REASON_ADMISSION_WINDOW_ABSENT,
    REASON_CAPTURED_AT_ABSENT,
    REASON_DIGEST_MISMATCH,
    REASON_DUPLICATE_FILL_CONFLICT,
    REASON_EMPTY_POSITIONS_WITHOUT_COMPLETENESS,
    REASON_FRESHNESS_WINDOW_ABSENT,
    REASON_INPUT_ABSENT,
    REASON_INPUT_MALFORMED,
    REASON_INSTRUMENT_ABSENT,
    REASON_INSTRUMENT_MISMATCH,
    REASON_INSTRUMENT_PARAMETER_ABSENT,
    REASON_LATE_FILL_OUTSIDE_WINDOW,
    REASON_PAGINATION_TERMINAL_ABSENT,
    REASON_PAGINATION_TERMINAL_SOURCE_ABSENT,
    REASON_STALE_EVIDENCE,
    REASON_TEMPORAL_INCONSISTENCY,
    REASON_VENUE_TIMESTAMP_ABSENT,
    STATUS_ADMITTED,
    STATUS_UNKNOWN_BLOCKED,
    WRITER_HANDOFF,
)
from src.ops.h1_get_evidence_admission_v1.validate_v1 import (
    AdmissionParametersV1,
    CapturedGetResponseV1,
    validate_get_evidence_admission_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.state_contracts_v1 import body_digest

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "src/ops/h1_get_evidence_admission_v1"
NOW_MS = 1_700_000_000_000
FRESHNESS_MS = 1_000
WINDOW_START_MS = NOW_MS - FRESHNESS_MS
WINDOW_END_MS = NOW_MS + FRESHNESS_MS
ACCOUNT_UID = "10001"
OTHER_UID = "10002"
INSTRUMENT_ID = "ETH-USDT-SWAP"
OTHER_INSTRUMENT_ID = "BTC-USDT-SWAP"
WINDOW_ID = "admission-window-1"
TERMINAL_SOURCE = "synthetic_owner_terminal_marker"

CHANGED_PATHS = [
    "config/governance/current_law_impact_map_v1/impact_adjudication_v1.json",
    "config/governance/current_law_impact_map_v1/impact_candidates_v1.json",
    "config/governance/current_system_interaction_authority_map_v1/impact_adjudication_v1.json",
    "src/ops/h1_get_evidence_admission_v1/__init__.py",
    "src/ops/h1_get_evidence_admission_v1/bundle_v1.py",
    "src/ops/okx_eea_private_account_state_runtime_v1/rest_baseline_v1.py",
    "tests/ops/test_h1_get_evidence_admission_v1.py",
    "tests/ops/test_h1_get_evidence_bundle_v1.py",
    "tests/ops/test_okx_eea_private_account_state_runtime_v1.py",
]

INTERACTION_CANDIDATE_PATHS = [
    "config/governance/current_law_impact_map_v1/impact_adjudication_v1.json",
    "config/governance/current_law_impact_map_v1/impact_candidates_v1.json",
    "src/ops/h1_get_evidence_admission_v1/__init__.py",
    "src/ops/h1_get_evidence_admission_v1/bundle_v1.py",
    "src/ops/okx_eea_private_account_state_runtime_v1/rest_baseline_v1.py",
    "tests/ops/test_h1_get_evidence_admission_v1.py",
    "tests/ops/test_h1_get_evidence_bundle_v1.py",
    "tests/ops/test_okx_eea_private_account_state_runtime_v1.py",
]

LAW_CANDIDATE_PATHS = [
    "config/governance/current_system_interaction_authority_map_v1/impact_adjudication_v1.json",
    "src/ops/h1_get_evidence_admission_v1/__init__.py",
    "src/ops/h1_get_evidence_admission_v1/bundle_v1.py",
    "src/ops/okx_eea_private_account_state_runtime_v1/rest_baseline_v1.py",
    "tests/ops/test_h1_get_evidence_admission_v1.py",
    "tests/ops/test_h1_get_evidence_bundle_v1.py",
    "tests/ops/test_okx_eea_private_account_state_runtime_v1.py",
]

FORBIDDEN_IMPORT_PREFIXES = (
    "http",
    "requests",
    "socket",
    "src.ops.full_core_live_path_composition_root_v1",
    "src.ops.productive_futures_accounting_runtime_binding_v1",
    "src.ops.productive_reconciliation_runtime_binding_v1",
    "src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1",
    "trading",
    "urllib",
)


def _params(**overrides: object) -> AdmissionParametersV1:
    values: dict[str, object] = {
        "bound_account_uid": ACCOUNT_UID,
        "bound_instrument_id": INSTRUMENT_ID,
        "freshness_window_ms": FRESHNESS_MS,
        "admission_time_ms": NOW_MS,
        "admission_window_id": WINDOW_ID,
        "admission_window_start_ms": WINDOW_START_MS,
        "admission_window_end_ms": WINDOW_END_MS,
    }
    values.update(overrides)
    return AdmissionParametersV1(**values)


def _response(
    endpoint: str,
    rows: list[dict[str, object]],
    *,
    inst_id: str = INSTRUMENT_ID,
    terminal: bool | None = None,
    source: str | None = None,
    venue_timestamp_ms: int | None = NOW_MS,
    captured_at_ms: int | None = NOW_MS,
    admission_window_id: str | None = WINDOW_ID,
    request_params: dict[str, str] | None = None,
) -> CapturedGetResponseV1:
    payload = {"code": "0", "data": rows}
    if request_params is None:
        request_params = {} if endpoint in ACCOUNT_ENDPOINTS else {"instId": inst_id}
    if endpoint in PAGINATED_ENDPOINTS:
        if terminal is None:
            terminal = True
        if source is None and terminal is True:
            source = TERMINAL_SOURCE
    return CapturedGetResponseV1(
        endpoint=endpoint,
        request_params=request_params,
        payload=payload,
        body_digest=body_digest(payload),
        captured_at_ms=captured_at_ms,
        venue_timestamp_ms=venue_timestamp_ms,
        pagination_terminal=terminal,
        pagination_terminal_source=source,
        admission_window_id=admission_window_id,
    )


def _valid_responses(
    *,
    position_rows: list[dict[str, object]] | None = None,
    fill_rows: list[dict[str, object]] | None = None,
) -> tuple[CapturedGetResponseV1, ...]:
    if position_rows is None:
        position_rows = [{"instId": INSTRUMENT_ID, "pos": "1"}]
    if fill_rows is None:
        fill_rows = [{"instId": INSTRUMENT_ID, "tradeId": "T1", "fillSz": "1", "fillPx": "2"}]
    return (
        _response(ENDPOINT_ACCOUNT_CONFIG, [{"uid": ACCOUNT_UID, "acctLv": "2"}]),
        _response(ENDPOINT_ACCOUNT_BALANCE, [{"uid": ACCOUNT_UID, "totalEq": "1"}]),
        _response(ENDPOINT_ACCOUNT_POSITIONS, position_rows),
        _response(ENDPOINT_ORDERS_PENDING, []),
        _response(ENDPOINT_ORDERS_HISTORY, []),
        _response(ENDPOINT_FILLS, fill_rows),
    )


def _replace_endpoint(
    responses: tuple[CapturedGetResponseV1, ...],
    endpoint: str,
    response: CapturedGetResponseV1,
) -> tuple[CapturedGetResponseV1, ...]:
    return tuple(response if item.endpoint == endpoint else item for item in responses)


def _load_script(name: str):
    path = REPO / "scripts/ops" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_valid_evidence_is_admitted_without_trading_authority() -> None:
    result = validate_get_evidence_admission_v1(_valid_responses(), _params())
    assert result.status == STATUS_ADMITTED
    assert result.reason_codes == POSITIVE_REASON_CODES
    assert result.position_inventory == INVENTORY_ATTESTED_ROWS
    assert result.fill_fact_count == 1
    assert result.writer_handoff == WRITER_HANDOFF
    assert result.flat_emitted is False
    assert result.authority_effect == AUTHORITY_EFFECT == "NONE"
    assert result.post_allowed is POST_ALLOWED is False
    assert result.external_effect_authorized is EXTERNAL_EFFECT_AUTHORIZED is False
    assert result.productive_completeness is PRODUCTIVE_COMPLETENESS is False
    assert result.productive_activation is PRODUCTIVE_ACTIVATION is False


def test_missing_account_identity_blocks() -> None:
    responses = _replace_endpoint(
        _valid_responses(),
        ENDPOINT_ACCOUNT_CONFIG,
        _response(ENDPOINT_ACCOUNT_CONFIG, [{"acctLv": "2"}]),
    )
    result = validate_get_evidence_admission_v1(responses, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_ACCOUNT_IDENTITY_ABSENT in result.reason_codes
    assert result.flat_emitted is False


def test_instrument_mismatch_blocks() -> None:
    responses = _replace_endpoint(
        _valid_responses(),
        ENDPOINT_ACCOUNT_POSITIONS,
        _response(
            ENDPOINT_ACCOUNT_POSITIONS,
            [{"instId": OTHER_INSTRUMENT_ID, "pos": "1"}],
            inst_id=OTHER_INSTRUMENT_ID,
        ),
    )
    result = validate_get_evidence_admission_v1(responses, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_INSTRUMENT_MISMATCH in result.reason_codes


def test_stale_evidence_blocks() -> None:
    stale_at = NOW_MS - 5_000
    responses = tuple(
        replace(
            item,
            captured_at_ms=stale_at,
            venue_timestamp_ms=stale_at,
        )
        for item in _valid_responses()
    )
    parameters = _params(
        freshness_window_ms=FRESHNESS_MS,
        admission_window_start_ms=NOW_MS - 10_000,
        admission_window_end_ms=NOW_MS + 10_000,
    )
    result = validate_get_evidence_admission_v1(responses, parameters)
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_STALE_EVIDENCE in result.reason_codes
    assert REASON_TEMPORAL_INCONSISTENCY not in result.reason_codes


def test_missing_pagination_terminal_blocks() -> None:
    current = next(
        item for item in _valid_responses() if item.endpoint == ENDPOINT_ACCOUNT_POSITIONS
    )
    responses = _replace_endpoint(
        _valid_responses(),
        ENDPOINT_ACCOUNT_POSITIONS,
        replace(current, pagination_terminal=None, pagination_terminal_source=None),
    )
    result = validate_get_evidence_admission_v1(responses, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_PAGINATION_TERMINAL_ABSENT in result.reason_codes


def test_contradictory_admission_window_blocks() -> None:
    current = next(item for item in _valid_responses() if item.endpoint == ENDPOINT_FILLS)
    responses = _replace_endpoint(
        _valid_responses(),
        ENDPOINT_FILLS,
        replace(current, admission_window_id="other-window"),
    )
    result = validate_get_evidence_admission_v1(responses, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_TEMPORAL_INCONSISTENCY in result.reason_codes


def test_digest_mismatch_blocks() -> None:
    current = next(item for item in _valid_responses() if item.endpoint == ENDPOINT_FILLS)
    responses = _replace_endpoint(
        _valid_responses(),
        ENDPOINT_FILLS,
        replace(current, body_digest="0" * 64),
    )
    result = validate_get_evidence_admission_v1(responses, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_DIGEST_MISMATCH in result.reason_codes


def test_empty_positions_without_completeness_block() -> None:
    responses = _replace_endpoint(
        _valid_responses(position_rows=[]),
        ENDPOINT_ACCOUNT_POSITIONS,
        _response(ENDPOINT_ACCOUNT_POSITIONS, [], terminal=False, source=None),
    )
    result = validate_get_evidence_admission_v1(responses, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_EMPTY_POSITIONS_WITHOUT_COMPLETENESS in result.reason_codes
    assert result.position_inventory == INVENTORY_UNPROVEN
    assert result.flat_emitted is False


def test_fully_proven_empty_positions_are_attested_zero_not_flat() -> None:
    result = validate_get_evidence_admission_v1(
        _valid_responses(position_rows=[], fill_rows=[]),
        _params(),
    )
    assert result.status == STATUS_ADMITTED
    assert result.position_inventory == INVENTORY_ATTESTED_ZERO
    assert result.writer_handoff == "NONE"
    assert result.flat_emitted is False
    assert result.productive_activation is False


def test_duplicate_fill_conflict_blocks() -> None:
    fills = [
        {"instId": INSTRUMENT_ID, "tradeId": "T1", "fillSz": "1", "fillPx": "2"},
        {"instId": INSTRUMENT_ID, "tradeId": "T1", "fillSz": "3", "fillPx": "2"},
    ]
    result = validate_get_evidence_admission_v1(_valid_responses(fill_rows=fills), _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_DUPLICATE_FILL_CONFLICT in result.reason_codes
    assert result.fill_fact_count == 0


def test_identical_duplicate_fill_is_one_fact() -> None:
    row = {"instId": INSTRUMENT_ID, "tradeId": "T1", "fillSz": "1", "fillPx": "2"}
    result = validate_get_evidence_admission_v1(
        _valid_responses(fill_rows=[row, dict(row)]),
        _params(),
    )
    assert result.status == STATUS_ADMITTED
    assert result.fill_fact_count == 1


def test_late_fill_outside_admission_window_blocks() -> None:
    fills = [
        {
            "instId": INSTRUMENT_ID,
            "tradeId": "T1",
            "fillSz": "1",
            "fillPx": "2",
            "fillTime": WINDOW_END_MS + 1,
        }
    ]
    result = validate_get_evidence_admission_v1(_valid_responses(fill_rows=fills), _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_LATE_FILL_OUTSIDE_WINDOW in result.reason_codes


@pytest.mark.parametrize(
    ("field", "code"),
    [
        ("bound_account_uid", REASON_ACCOUNT_PARAMETER_ABSENT),
        ("bound_instrument_id", REASON_INSTRUMENT_PARAMETER_ABSENT),
        ("freshness_window_ms", REASON_FRESHNESS_WINDOW_ABSENT),
        ("admission_time_ms", REASON_ADMISSION_TIME_ABSENT),
        ("admission_window_id", REASON_ADMISSION_WINDOW_ABSENT),
        ("admission_window_start_ms", REASON_ADMISSION_WINDOW_ABSENT),
        ("admission_window_end_ms", REASON_ADMISSION_WINDOW_ABSENT),
    ],
)
def test_each_missing_owner_parameter_blocks(field: str, code: str) -> None:
    result = validate_get_evidence_admission_v1(_valid_responses(), _params(**{field: None}))
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert code in result.reason_codes
    assert result.flat_emitted is False


def test_dataclasses_have_no_implicit_defaults() -> None:
    for model in (CapturedGetResponseV1, AdmissionParametersV1):
        for field in fields(model):
            assert field.default is MISSING
            assert field.default_factory is MISSING
    package_text = "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE.glob("*.py"))
    assert "POSITION_OBSERVATION_FRESHNESS" not in package_text
    result = validate_get_evidence_admission_v1(
        _valid_responses(),
        _params(freshness_window_ms=None),
    )
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_FRESHNESS_WINDOW_ABSENT in result.reason_codes


def test_contradictory_uid_blocks() -> None:
    responses = _replace_endpoint(
        _valid_responses(),
        ENDPOINT_ACCOUNT_BALANCE,
        _response(ENDPOINT_ACCOUNT_BALANCE, [{"uid": OTHER_UID, "totalEq": "1"}]),
    )
    result = validate_get_evidence_admission_v1(responses, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_ACCOUNT_IDENTITY_MISMATCH in result.reason_codes


def test_bool_uid_is_malformed_and_blocks() -> None:
    responses = _replace_endpoint(
        _valid_responses(),
        ENDPOINT_ACCOUNT_CONFIG,
        _response(ENDPOINT_ACCOUNT_CONFIG, [{"uid": True, "acctLv": "2"}]),
    )
    result = validate_get_evidence_admission_v1(responses, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_ACCOUNT_IDENTITY_MALFORMED in result.reason_codes


def test_missing_inst_id_blocks() -> None:
    responses = _replace_endpoint(
        _valid_responses(),
        ENDPOINT_ACCOUNT_POSITIONS,
        _response(
            ENDPOINT_ACCOUNT_POSITIONS,
            [{"instId": INSTRUMENT_ID, "pos": "1"}],
            request_params={},
        ),
    )
    result = validate_get_evidence_admission_v1(responses, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_INSTRUMENT_ABSENT in result.reason_codes


def test_missing_venue_timestamp_blocks() -> None:
    current = next(item for item in _valid_responses() if item.endpoint == ENDPOINT_FILLS)
    responses = _replace_endpoint(
        _valid_responses(),
        ENDPOINT_FILLS,
        replace(current, venue_timestamp_ms=None),
    )
    result = validate_get_evidence_admission_v1(responses, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_VENUE_TIMESTAMP_ABSENT in result.reason_codes


def test_missing_captured_at_blocks() -> None:
    current = next(item for item in _valid_responses() if item.endpoint == ENDPOINT_FILLS)
    responses = _replace_endpoint(
        _valid_responses(),
        ENDPOINT_FILLS,
        replace(current, captured_at_ms=None),
    )
    result = validate_get_evidence_admission_v1(responses, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_CAPTURED_AT_ABSENT in result.reason_codes


def test_pagination_terminal_without_source_is_not_productive_completeness() -> None:
    current = next(
        item for item in _valid_responses() if item.endpoint == ENDPOINT_ACCOUNT_POSITIONS
    )
    responses = _replace_endpoint(
        _valid_responses(),
        ENDPOINT_ACCOUNT_POSITIONS,
        replace(current, pagination_terminal=True, pagination_terminal_source=None),
    )
    result = validate_get_evidence_admission_v1(responses, _params())
    assert result.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_PAGINATION_TERMINAL_SOURCE_ABSENT in result.reason_codes
    assert "PAGINATION_COMPLETENESS" not in result.reason_codes
    assert result.productive_completeness is False


def test_admission_digest_is_deterministic() -> None:
    responses = _valid_responses()
    parameters = _params()
    first = validate_get_evidence_admission_v1(responses, parameters)
    second = validate_get_evidence_admission_v1(responses, parameters)
    assert first.admission_digest == second.admission_digest
    assert len(first.admission_digest) == 64
    shifted = tuple(
        replace(item, captured_at_ms=NOW_MS - 1, venue_timestamp_ms=NOW_MS - 1)
        for item in responses
    )
    changed = validate_get_evidence_admission_v1(shifted, parameters)
    assert changed.status == STATUS_ADMITTED
    assert changed.admission_digest != first.admission_digest


def test_zero_position_string_is_not_attested_zero_or_flat() -> None:
    result = validate_get_evidence_admission_v1(
        _valid_responses(position_rows=[{"instId": INSTRUMENT_ID, "pos": "0"}]),
        _params(),
    )
    assert result.status == STATUS_ADMITTED
    assert result.position_inventory == INVENTORY_ATTESTED_ROWS
    assert result.flat_emitted is False
    assert result.writer_handoff == "NONE"


def test_missing_input_blocks_without_defaulting() -> None:
    assert validate_get_evidence_admission_v1(None, _params()).status == STATUS_UNKNOWN_BLOCKED
    assert REASON_INPUT_ABSENT in validate_get_evidence_admission_v1(None, _params()).reason_codes
    listed = validate_get_evidence_admission_v1(list(_valid_responses()), _params())
    assert listed.status == STATUS_UNKNOWN_BLOCKED
    assert REASON_INPUT_MALFORMED in listed.reason_codes


def test_package_has_no_writer_network_or_state_write_surface() -> None:
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
                assert not name.startswith(FORBIDDEN_IMPORT_PREFIXES)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_attrs


def test_working_tree_map_currency_is_non_authorizing() -> None:
    interaction = _load_script("current_system_interaction_authority_map_v1.py")
    law = _load_script("current_law_impact_map_v1.py")
    interaction_declaration = json.loads(
        (
            REPO
            / "config/governance/current_system_interaction_authority_map_v1"
            / "impact_adjudication_v1.json"
        ).read_text(encoding="utf-8")
    )
    law_declaration = json.loads(
        (
            REPO / "config/governance/current_law_impact_map_v1" / "impact_adjudication_v1.json"
        ).read_text(encoding="utf-8")
    )
    interaction_surfaces = json.loads(
        (
            REPO
            / "config/governance/current_system_interaction_authority_map_v1"
            / "impact_candidates_v1.json"
        ).read_text(encoding="utf-8")
    )
    law_surfaces = json.loads(
        (
            REPO / "config/governance/current_law_impact_map_v1" / "impact_candidates_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert interaction_surfaces["exhaustive"] is False
    assert law_surfaces["exhaustive"] is False
    assert interaction_surfaces["authority_effect"] == "NONE"
    assert law_surfaces["authority_effect"] == "NONE"
    assert "src/ops/h1_get_evidence_admission_v1/" in interaction_surfaces["surfaces"]
    assert "src/ops/h1_get_evidence_admission_v1/" in law_surfaces["surfaces"]
    interaction_errors = interaction.evaluate_impact(
        CHANGED_PATHS,
        interaction_declaration,
        surfaces=list(interaction_surfaces["surfaces"]),
        surfaces_exhaustive=bool(interaction_surfaces["exhaustive"]),
        source_changed=False,
        derived_clean=interaction.derived_drift(
            interaction._load_json(interaction.SOURCE_PATH), REPO
        )
        == [],
    )
    law_errors = law.evaluate_impact(
        CHANGED_PATHS,
        law_declaration,
        surfaces=list(law_surfaces["surfaces"]),
        source_changed=False,
        derived_clean=law.derived_drift(law._load_json(law.SOURCE_PATH), REPO) == [],
    )
    assert interaction_errors == []
    assert law_errors == []
    assert interaction_declaration["verdict"] == "NO_MAP_IMPACT"
    assert law_declaration["verdict"] == "NO_LAW_IMPACT"
    assert interaction_declaration["covered_candidate_paths"] == INTERACTION_CANDIDATE_PATHS
    assert law_declaration["covered_candidate_paths"] == LAW_CANDIDATE_PATHS
    assert interaction_declaration["authority_effect"] == "NONE"
    assert law_declaration["authority_effect"] == "NONE"
    source_diff = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "HEAD",
            "--",
            "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            "config/governance/current_law_impact_map_v1/source_v1.json",
            "src/trading/master_v2",
            "src/execution",
        ],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    assert source_diff.stdout.strip() == ""
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    )
    dirty = sorted(line[3:] for line in status.stdout.splitlines() if line.strip())
    assert dirty == CHANGED_PATHS
