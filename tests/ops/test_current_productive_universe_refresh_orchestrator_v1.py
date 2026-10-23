"""Offline contracts for the inactive universe-refresh skeleton and budget epoch."""

from __future__ import annotations

import ast
import socket
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

import src.ops.current_productive_universe_refresh_orchestrator_v1 as orchestrator
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    SCORE_COMPONENT_KEYS,
    SNAPSHOT_STATE_VALID,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
    RankedCandidateV1,
    authority_block,
)
from src.ops.current_productive_universe_refresh_orchestrator_v1 import (
    CAP21_TO_CAP23_BINDING_INVOCATION_ALLOWED,
    TOP20_SNAPSHOT_READ_ALLOWED,
    CAP21_TO_CAP23_COMPOSITION_MODULE,
    CAP21_TO_CAP23_COMPOSITION_SYMBOL,
    NATURAL_ENTER_ENTRY_MODULE,
    NATURAL_ENTER_ENTRY_SYMBOL,
    REFRESH_ACTIVATION_ALLOWED,
    UniverseRefreshBudgetEpochRequestV1,
    UniverseRefreshCap21BindingRequestV1,
    UniverseRefreshCap21BindingStatusV1,
    UniverseRefreshSelectionContinuityRequestV1,
    UniverseRefreshSelectionContinuityStatusV1,
    UniverseRefreshTop20SnapshotRequestV1,
    UniverseRefreshTop20SnapshotStatusV1,
    UniverseRefreshBudgetEpochStatusV1,
    DataCompletionEvidenceV1,
    DataCompletionStatusV1,
    UniverseRefreshEpochRequestV1,
    UniverseRefreshEpochResultV1,
    UniverseRefreshEpochStatusV1,
    UniverseRefreshReleasePreflightRequestV1,
    UniverseRefreshReleasePreflightStatusV1,
    UniverseRefreshSelectionHandoffRequestV1,
    UniverseRefreshSelectionHandoffStatusV1,
    UniverseRefreshNaturalEnterIsolationRequestV1,
    UniverseRefreshNaturalEnterIsolationStatusV1,
    assess_data_completion_slot_release_v1,
    bind_universe_refresh_natural_enter_isolation_v1,
    preflight_universe_refresh_release_v1,
    prepare_universe_refresh_selection_handoff_v1,
    bind_universe_refresh_selection_continuity_v1,
    bind_universe_refresh_to_cap21_to_cap23_v1,
    bind_universe_refresh_top20_snapshot_v1,
    run_universe_refresh_budget_epoch_v1,
    run_universe_refresh_epoch_v1,
)

_MODULE_PATH = Path("src/ops/current_productive_universe_refresh_orchestrator_v1.py")
_ALLOWED_IMPORT_MODULES = frozenset(
    {
        "__future__",
        "collections.abc",
        "dataclasses",
        "enum",
        "importlib.util",
        "pathlib",
        "sys",
        "types",
    }
)
_DENIED_IMPORT_PARTS = (
    "trading",
    "execution",
    "risk",
    "socket",
    "urllib",
    "http",
    "requests",
    "httpx",
    "aiohttp",
    "double_play",
    "natural_enter",
    "master_v2",
)
_FORBIDDEN_CALLS = frozenset(
    {
        "open",
        "urlopen",
        "request",
        "get",
        "post",
        "mkdir",
        "write_text",
        "write_bytes",
        "unlink",
        "remove",
        "system",
        "Popen",
        "Thread",
        "Process",
        "build_budgeted_economic_md_source_v1",
        "run_cap21_to_cap23_persist_productive_v1",
        "GovernedUniverseSingleWriterV1",
        "websocket",
        "WebSocket",
        "subscribe",
        "connect",
        "run_scheduler_tick_v1",
        "run_single_selected_future_policy_v1",
        "run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1",
        "run_governed_futures_universe_producer_v1",
        "apply_evaluation_completion_v1",
        "EvaluationCompletionWitnessV1",
    }
)
_NO_EFFECTS = {
    "refresh_activation_allowed": False,
    "producer_executed": False,
    "snapshot_published": False,
    "selection_mutated": False,
    "network_requested": False,
    "file_write_attempted": False,
    "ceiling_unchanged": True,
}


def _tree() -> ast.AST:
    return ast.parse(_MODULE_PATH.read_text(encoding="utf-8"))


def _imported_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            modules.add(node.module or "")
    return modules


def _called_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            names.add(func.id)
        elif isinstance(func, ast.Attribute):
            names.add(func.attr)
    return names


def _assert_no_effects(result: object) -> None:
    for name, expected in _NO_EFFECTS.items():
        assert getattr(result, name) is expected


def test_default_activation_is_disabled() -> None:
    assert REFRESH_ACTIVATION_ALLOWED is False


def test_call_without_authorization_is_refresh_not_authorized() -> None:
    result = run_universe_refresh_epoch_v1(UniverseRefreshEpochRequestV1(epoch_id="epoch-7"))

    assert result.status is UniverseRefreshEpochStatusV1.REFRESH_NOT_AUTHORIZED
    assert result.status.value == "REFRESH_NOT_AUTHORIZED"
    assert result.refresh_activation_allowed is False
    assert result.producer_executed is False
    assert result.snapshot_published is False
    assert result.selection_mutated is False
    assert result.network_requested is False
    assert result.file_write_attempted is False


def test_constant_rebind_does_not_authorize(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.ops.current_productive_universe_refresh_orchestrator_v1.REFRESH_ACTIVATION_ALLOWED",
        True,
    )

    refresh = run_universe_refresh_epoch_v1(UniverseRefreshEpochRequestV1(epoch_id="epoch-7"))
    budget = run_universe_refresh_budget_epoch_v1(
        UniverseRefreshBudgetEpochRequestV1(epoch_id="epoch-7")
    )

    assert refresh.status is UniverseRefreshEpochStatusV1.REFRESH_NOT_AUTHORIZED
    assert refresh.refresh_activation_allowed is False
    assert refresh.producer_executed is False
    assert budget.status is UniverseRefreshBudgetEpochStatusV1.BUDGET_NOT_AUTHORIZED
    _assert_no_effects(budget)


def test_no_side_effects(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    def _forbid_open(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("file open is forbidden")

    monkeypatch.setattr("builtins.open", _forbid_open)
    before = set(tmp_path.iterdir())

    result = run_universe_refresh_epoch_v1(UniverseRefreshEpochRequestV1(epoch_id="epoch-7"))

    assert result.file_write_attempted is False
    assert result.network_requested is False
    assert result.selection_mutated is False
    assert set(tmp_path.iterdir()) == before


def test_result_is_deterministic() -> None:
    request = UniverseRefreshEpochRequestV1(epoch_id="epoch-7")

    first = run_universe_refresh_epoch_v1(request)
    second = run_universe_refresh_epoch_v1(request)

    assert first == second
    assert first == UniverseRefreshEpochResultV1(
        epoch_id="epoch-7",
        status=UniverseRefreshEpochStatusV1.REFRESH_NOT_AUTHORIZED,
        refresh_activation_allowed=False,
        producer_executed=False,
        snapshot_published=False,
        selection_mutated=False,
        network_requested=False,
        file_write_attempted=False,
    )


def test_import_boundary_excludes_trading_and_network() -> None:
    imported = _imported_modules(_tree())

    assert imported == set(_ALLOWED_IMPORT_MODULES)
    assert _called_names(_tree()).isdisjoint(_FORBIDDEN_CALLS)
    for module_name in imported:
        assert all(part not in module_name for part in _DENIED_IMPORT_PARTS)


def test_blank_epoch_identity_stays_unauthorized() -> None:
    result = run_universe_refresh_epoch_v1(UniverseRefreshEpochRequestV1(epoch_id=""))

    assert result.epoch_id == ""
    assert result.status is UniverseRefreshEpochStatusV1.REFRESH_NOT_AUTHORIZED
    assert result.producer_executed is False


def test_missing_budget_authority_is_not_authorized() -> None:
    result = run_universe_refresh_budget_epoch_v1(
        UniverseRefreshBudgetEpochRequestV1(epoch_id="epoch-7", eligible_count=5)
    )

    assert result.status is UniverseRefreshBudgetEpochStatusV1.BUDGET_NOT_AUTHORIZED
    assert result.attempts_accounted == 0
    assert result.max_total_attempts is None
    _assert_no_effects(result)


@pytest.mark.parametrize("ceiling", [0, -1, True, 1.5])
def test_invalid_ceiling_is_rejected(ceiling: object) -> None:
    result = run_universe_refresh_budget_epoch_v1(
        UniverseRefreshBudgetEpochRequestV1(
            epoch_id="epoch-7",
            max_total_attempts=ceiling,
            eligible_count=1,
        )
    )

    assert result.status is UniverseRefreshBudgetEpochStatusV1.BUDGET_CEILING_INVALID
    assert result.max_total_attempts == ceiling
    assert result.attempts_accounted == 0
    _assert_no_effects(result)


@pytest.mark.parametrize(
    ("eligible_count", "ceiling", "attempts"),
    [(0, 4, 4), (1, 6, 6), (5, 14, 14), (20, 44, 44)],
)
def test_eligible_counts_account_inventory_then_economic_md(
    eligible_count: int,
    ceiling: int,
    attempts: int,
) -> None:
    result = run_universe_refresh_budget_epoch_v1(
        UniverseRefreshBudgetEpochRequestV1(
            epoch_id="epoch-7",
            max_total_attempts=ceiling,
            eligible_count=eligible_count,
        )
    )

    assert result.status is UniverseRefreshBudgetEpochStatusV1.BUDGET_ACCOUNTED
    assert result.max_total_attempts == ceiling
    assert result.attempts_accounted == attempts
    _assert_no_effects(result)
    assert (
        run_universe_refresh_epoch_v1(UniverseRefreshEpochRequestV1(epoch_id="epoch-7")).status
        is UniverseRefreshEpochStatusV1.REFRESH_NOT_AUTHORIZED
    )


def test_insufficient_remainder_does_not_publish_a_snapshot() -> None:
    result = run_universe_refresh_budget_epoch_v1(
        UniverseRefreshBudgetEpochRequestV1(
            epoch_id="epoch-7",
            max_total_attempts=13,
            eligible_count=5,
        )
    )

    assert result.status is UniverseRefreshBudgetEpochStatusV1.BUDGET_INSUFFICIENT
    assert result.max_total_attempts == 13
    assert result.attempts_accounted == 4
    _assert_no_effects(result)


def test_exhausted_ceiling_is_not_raised_or_renewed() -> None:
    request = UniverseRefreshBudgetEpochRequestV1(
        epoch_id="epoch-7",
        max_total_attempts=14,
        eligible_count=5,
    )
    blocked = UniverseRefreshBudgetEpochRequestV1(
        epoch_id="epoch-7",
        max_total_attempts=4,
        eligible_count=1,
    )

    first = run_universe_refresh_budget_epoch_v1(request)
    second = run_universe_refresh_budget_epoch_v1(request)
    remainder = run_universe_refresh_budget_epoch_v1(blocked)

    assert first == second
    assert first.status is UniverseRefreshBudgetEpochStatusV1.BUDGET_ACCOUNTED
    assert first.attempts_accounted == 14
    assert first.max_total_attempts == 14
    assert remainder.status is UniverseRefreshBudgetEpochStatusV1.BUDGET_INSUFFICIENT
    assert remainder.max_total_attempts == 4
    assert remainder.attempts_accounted == 4
    _assert_no_effects(first)
    _assert_no_effects(remainder)


@pytest.mark.parametrize("eligible_count", [-1, True, None, "5"])
def test_invalid_eligible_count_does_not_publish_a_snapshot(eligible_count: object) -> None:
    result = run_universe_refresh_budget_epoch_v1(
        UniverseRefreshBudgetEpochRequestV1(
            epoch_id="epoch-7",
            max_total_attempts=44,
            eligible_count=eligible_count,
        )
    )

    assert result.status is UniverseRefreshBudgetEpochStatusV1.INVALID_ELIGIBLE_COUNT
    assert result.max_total_attempts == 44
    assert result.attempts_accounted == 4
    _assert_no_effects(result)


def test_budget_epoch_does_not_open_files_or_sockets(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    def _forbid_open(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("file open is forbidden")

    def _forbid_socket(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("socket open is forbidden")

    monkeypatch.setattr("builtins.open", _forbid_open)
    monkeypatch.setattr(socket, "socket", _forbid_socket)
    before = set(tmp_path.iterdir())

    result = run_universe_refresh_budget_epoch_v1(
        UniverseRefreshBudgetEpochRequestV1(
            epoch_id="epoch-7",
            max_total_attempts=6,
            eligible_count=1,
        )
    )

    assert result.status is UniverseRefreshBudgetEpochStatusV1.BUDGET_ACCOUNTED
    assert set(tmp_path.iterdir()) == before
    _assert_no_effects(result)
    loaded = sys.modules[orchestrator.CANONICAL_SELECTION_BUDGET_MODULE]
    assert (
        loaded.SelectionNetworkBudgetV1.__module__ == orchestrator.CANONICAL_SELECTION_BUDGET_MODULE
    )
    assert loaded.__file__.endswith("current_productive_selection_network_budget_v1.py")


def test_cap21_binding_stays_uninvoked_and_closed() -> None:
    assert CAP21_TO_CAP23_BINDING_INVOCATION_ALLOWED is False
    request = UniverseRefreshCap21BindingRequestV1(epoch_id="epoch-7")

    first = bind_universe_refresh_to_cap21_to_cap23_v1(request)
    second = bind_universe_refresh_to_cap21_to_cap23_v1(request)

    assert first == second
    assert first.status is UniverseRefreshCap21BindingStatusV1.CAP21_TO_CAP23_BINDING_NOT_INVOKED
    assert first.composition_symbol == CAP21_TO_CAP23_COMPOSITION_SYMBOL
    assert first.composition_symbol == "run_cap21_to_cap23_persist_productive_v1"
    assert first.composition_module == CAP21_TO_CAP23_COMPOSITION_MODULE
    assert first.state_roots == (
        "runtime_state/universe",
        "runtime_state/ranking",
        "runtime_state/selection",
    )
    assert first.invocation_performed is False
    assert first.producer_executed is False
    assert first.snapshot_published is False
    assert first.selection_mutated is False
    assert first.network_requested is False
    assert first.http_get_performed is False
    assert first.public_websocket_connected is False
    assert first.private_websocket_connected is False
    assert first.public_websocket_equated_with_http_get is False
    assert first.binding_owns_state is False
    assert first.second_writer_claimed is False
    assert first.existing_universe_writer_symbol == "GovernedUniverseSingleWriterV1"
    assert first.ranking_volatility_owner == "population_sigma_log_returns_v1"
    assert first.g17_volatility_owner == "CanonicalVolatilityTypedRuntimeProducerScaffoldV1"
    assert first.ranking_volatility_owner != first.g17_volatility_owner
    assert first.shared_volatility_epoch_enforced is False
    assert first.market_data_redirected is False
    assert first.hold_semantics_changed is False
    assert first.file_write_attempted is False
    assert (
        run_universe_refresh_epoch_v1(UniverseRefreshEpochRequestV1(epoch_id="epoch-7")).status
        is UniverseRefreshEpochStatusV1.REFRESH_NOT_AUTHORIZED
    )


def test_binding_constant_rebind_does_not_invoke(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "src.ops.current_productive_universe_refresh_orchestrator_v1."
        "CAP21_TO_CAP23_BINDING_INVOCATION_ALLOWED",
        True,
    )
    monkeypatch.chdir(tmp_path)

    def _forbid_open(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("file open is forbidden")

    def _forbid_socket(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("socket open is forbidden")

    monkeypatch.setattr("builtins.open", _forbid_open)
    monkeypatch.setattr(socket, "socket", _forbid_socket)
    before = set(tmp_path.iterdir())

    result = bind_universe_refresh_to_cap21_to_cap23_v1(
        UniverseRefreshCap21BindingRequestV1(epoch_id="epoch-7")
    )

    assert result.invocation_performed is False
    assert result.producer_executed is False
    assert result.http_get_performed is False
    assert result.public_websocket_connected is False
    assert result.private_websocket_connected is False
    assert set(tmp_path.iterdir()) == before


def test_binding_source_keeps_ws_budget_and_hold_boundaries() -> None:
    source = _MODULE_PATH.read_text(encoding="utf-8")

    assert "wss://" not in source
    assert "import websocket" not in source.lower()
    assert "private_ws" not in source.lower()
    assert "EEA_PRIVATE_WS" not in source
    assert "EEA_PUBLIC_WS" not in source
    assert "3600" not in source
    assert "run_single_selected_future_policy_v1(" not in source
    assert "run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1(" not in source
    assert "run_cap21_to_cap23_persist_productive_v1(" not in source
    assert "run_governed_futures_universe_producer_v1(" not in source
    assert "apply_evaluation_completion_v1(" not in source
    assert "EvaluationCompletionWitnessV1(" not in source
    assert "from trading" not in source
    assert "population_sigma_log_returns_v1" in source
    assert "CanonicalVolatilityTypedRuntimeProducerScaffoldV1" in source
    assert "run_scheduler_tick_v1(" not in source


def _ranked(canonical: str, rank: int) -> RankedCandidateV1:
    return RankedCandidateV1(
        rank=rank,
        canonical_instrument_id=canonical,
        venue_native_id=f"{canonical}-OKX",
        total_score=float(100 - rank),
        score_components={key: 0.0 for key in SCORE_COMPONENT_KEYS},
        data_quality_status="PASS",
        eligibility_status="ELIGIBLE",
        exclusion_reason_codes=(),
        tie_break_values={"canonical_instrument_id": canonical},
    )


def _committed_snapshot(
    ranked: list[RankedCandidateV1],
    *,
    snapshot_id: str = "rank_snap_1",
    state: str = SNAPSHOT_STATE_VALID,
) -> dict[str, object]:
    snap = ProductiveFuturesRankingSnapshotV1(
        schema_version="productive_futures_ranking_snapshot.v1",
        capability_id="CAPABILITY_2_2",
        producer_version="v1",
        ranking_snapshot_id=snapshot_id,
        universe_snapshot_id="uni_1",
        universe_source_digest="us",
        universe_payload_digest="up",
        ranking_policy_id="policy",
        ranking_policy_version="v1",
        repository_sha="sha",
        config_digest="cfg",
        event_time="2024-01-01T00:00:00Z",
        produced_at_wall_time="2024-01-01T00:00:01Z",
        candidate_count_total=len(ranked),
        eligible_candidate_count=len(ranked),
        excluded_candidate_count=0,
        ranked_candidates=tuple(ranked),
        excluded_candidates=(),
        snapshot_state=state,
        integrity_digest="",
        authority=authority_block(),
        call_graph=(),
        failure_codes=(),
    ).with_integrity_digest()
    return snap.to_dict()


def _assert_top20_closed(result: object) -> None:
    assert result.orchestrator_owns_ranking_state is False
    assert result.orchestrator_owns_residency_state is False
    assert result.residency_write_performed is False
    assert result.scheduler_tick_performed is False
    assert result.admission_mutated is False
    assert result.productive_admission is False
    assert result.selection_mutated is False
    assert result.producer_executed is False
    assert result.snapshot_published is False
    assert result.network_requested is False
    assert result.http_get_performed is False
    assert result.public_websocket_connected is False
    assert result.private_websocket_connected is False
    assert result.file_write_attempted is False
    assert result.second_writer_claimed is False
    assert result.ranking_snapshot_owner == "ops.productive_futures_ranking_producer_v1"
    assert result.top20_role == "reader"


def test_missing_or_uncommitted_snapshot_is_not_ready() -> None:
    assert TOP20_SNAPSHOT_READ_ALLOWED is False
    missing = bind_universe_refresh_top20_snapshot_v1(
        UniverseRefreshTop20SnapshotRequestV1(epoch_id="epoch-7")
    )
    uncommitted = bind_universe_refresh_top20_snapshot_v1(
        UniverseRefreshTop20SnapshotRequestV1(
            epoch_id="epoch-7",
            snapshot=_committed_snapshot([_ranked("AAA", 1)]),
            snapshot_committed=False,
        )
    )

    assert missing.status is UniverseRefreshTop20SnapshotStatusV1.TOP20_SNAPSHOT_NOT_READY
    assert uncommitted.status is UniverseRefreshTop20SnapshotStatusV1.TOP20_SNAPSHOT_NOT_READY
    assert missing.hypothetical_new == ()
    _assert_top20_closed(missing)
    _assert_top20_closed(uncommitted)


def test_invalid_snapshot_is_not_ready() -> None:
    result = bind_universe_refresh_top20_snapshot_v1(
        UniverseRefreshTop20SnapshotRequestV1(
            epoch_id="epoch-7",
            snapshot=_committed_snapshot([_ranked("AAA", 1)], state="INVALID"),
            snapshot_committed=True,
        )
    )

    assert result.status is UniverseRefreshTop20SnapshotStatusV1.TOP20_SNAPSHOT_NOT_READY
    assert result.hypothetical_new == ()
    _assert_top20_closed(result)


def test_staging_snapshot_is_not_read(monkeypatch: pytest.MonkeyPatch) -> None:
    def _forbid_reader(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("staging snapshot was read")

    monkeypatch.setattr(
        orchestrator._TOP20_ADMISSION,
        "eligible_top20_candidates_v1",
        _forbid_reader,
    )
    snapshot = _committed_snapshot(
        [_ranked("AAA", 1)],
        snapshot_id=".productive_futures_ranking_staging_rank",
    )

    result = bind_universe_refresh_top20_snapshot_v1(
        UniverseRefreshTop20SnapshotRequestV1(
            epoch_id="epoch-7",
            snapshot=snapshot,
            snapshot_committed=True,
        )
    )

    assert result.status is UniverseRefreshTop20SnapshotStatusV1.TOP20_SNAPSHOT_NOT_READY
    _assert_top20_closed(result)


def test_committed_snapshot_classifies_hypothetical_candidates(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        "src.ops.current_productive_universe_refresh_orchestrator_v1.TOP20_SNAPSHOT_READ_ALLOWED",
        True,
    )
    monkeypatch.chdir(tmp_path)

    def _forbid_open(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("file open is forbidden")

    def _forbid_socket(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("socket open is forbidden")

    monkeypatch.setattr("builtins.open", _forbid_open)
    monkeypatch.setattr(socket, "socket", _forbid_socket)
    before = set(tmp_path.iterdir())
    snapshot = _committed_snapshot([_ranked("AAA", 1), _ranked("CCC", 2)])

    result = bind_universe_refresh_top20_snapshot_v1(
        UniverseRefreshTop20SnapshotRequestV1(
            epoch_id="epoch-7",
            snapshot=snapshot,
            snapshot_committed=True,
            prior_canonical_ids=("AAA", "BBB"),
            observed_at_unix=100.0,
        )
    )

    assert result.status is UniverseRefreshTop20SnapshotStatusV1.TOP20_HYPOTHETICAL_ADMISSION
    assert result.hypothetical_new == ("CCC",)
    assert result.hypothetical_unchanged == ("AAA",)
    assert result.hypothetical_departed == ("BBB",)
    assert result.rank_observations[0].canonical_instrument_id == "CCC"
    assert result.rank_observations[0].rank == 2
    assert result.rank_observations[0].in_top20 is True
    assert result.rank_observations[1].rank == 1
    assert result.rank_observations[2].rank is None
    assert result.rank_observations[2].in_top20 is False
    _assert_top20_closed(result)
    assert set(tmp_path.iterdir()) == before
    assert orchestrator._TOP20_ADMISSION.__name__ == orchestrator._WP_P4_TOP20_ADMISSION
    assert str(orchestrator._TOP20_ADMISSION.__file__).endswith("admission_v1.py")


def _previous_selection(instrument_id: str = "BTC-USDT-SWAP") -> dict[str, str]:
    return {
        "selection_id": "sel-1",
        "instrument_id": instrument_id,
        "state": "SELECTED_ACTIVE",
        "integrity_digest": "digest-1",
    }


def _continuity(
    **overrides: object,
) -> object:
    payload = {
        "epoch_id": "epoch-7",
        "previous_selection": _previous_selection(),
        "state_provenance_proven": True,
        "position_truth": "FLAT",
        "holding_elapsed_seconds": 3600.0,
        "ranking_favorite_id": "BTC-USDT-SWAP",
    }
    payload.update(overrides)
    return bind_universe_refresh_selection_continuity_v1(
        UniverseRefreshSelectionContinuityRequestV1(**payload)
    )


def _assert_continuity_closed(result: object) -> None:
    assert result.previous_selection_forced_none is False
    assert result.unknown_position_treated_as_flat is False
    assert result.switch_authorized is False
    assert result.new_selection_created is False
    assert result.selection_policy_invoked is False
    assert result.selection_mutated is False
    assert result.state_write_attempted is False
    assert result.second_selection_authority is False
    assert result.natural_enter_started is False
    assert result.trading_epoch_created is False
    assert result.master_v2_invoked is False
    assert result.double_play_invoked is False
    assert result.network_requested is False
    assert result.http_get_performed is False
    assert result.public_websocket_connected is False
    assert result.private_websocket_connected is False
    assert result.min_holding_period_seconds == 3600.0
    assert result.selection_owner == "ops.single_selected_future_policy_v1"


def test_valid_previous_selection_is_held() -> None:
    result = _continuity()

    assert result.status is UniverseRefreshSelectionContinuityStatusV1.SELECTION_CONTINUITY_HELD
    assert result.retained_instrument_id == "BTC-USDT-SWAP"
    assert result.previous_selection_supplied is True
    assert result.load_previous_from_state is True
    assert result.ranking_favorite_changed is False
    _assert_continuity_closed(result)


def test_missing_invalid_or_unproven_selection_stays_unproven() -> None:
    missing = _continuity(previous_selection=None, state_provenance_proven=False)
    invalid = _continuity(previous_selection={"state": "NO_SELECTION"})
    unproven_origin = _continuity(state_provenance_proven=False)

    assert missing.status is (
        UniverseRefreshSelectionContinuityStatusV1.SELECTION_CONTINUITY_UNPROVEN
    )
    assert missing.retained_instrument_id == ""
    assert missing.load_previous_from_state is False
    assert invalid.status is (
        UniverseRefreshSelectionContinuityStatusV1.SELECTION_CONTINUITY_UNPROVEN
    )
    assert unproven_origin.status is (
        UniverseRefreshSelectionContinuityStatusV1.SELECTION_CONTINUITY_UNPROVEN
    )
    assert unproven_origin.retained_instrument_id == "BTC-USDT-SWAP"
    _assert_continuity_closed(missing)
    _assert_continuity_closed(invalid)
    _assert_continuity_closed(unproven_origin)


def test_unknown_position_is_not_flat_and_open_position_blocks_switch() -> None:
    unknown = _continuity(position_truth="UNKNOWN")
    opened = _continuity(
        position_truth="OPEN",
        open_position_instrument_id="BTC-USDT-SWAP",
        ranking_favorite_id="ETH-USDT-SWAP",
        holding_elapsed_seconds=10.0,
    )

    assert unknown.status is (
        UniverseRefreshSelectionContinuityStatusV1.SELECTION_CONTINUITY_UNPROVEN
    )
    assert unknown.position_truth == "UNKNOWN"
    assert unknown.open_position_present is False
    assert opened.status is UniverseRefreshSelectionContinuityStatusV1.SELECTION_CONTINUITY_HELD
    assert opened.retained_instrument_id == "BTC-USDT-SWAP"
    assert opened.ranking_favorite_changed is True
    assert opened.holding_period_active is True
    assert opened.open_position_present is True
    assert opened.open_position_blocks_switch is True
    _assert_continuity_closed(unknown)
    _assert_continuity_closed(opened)


def test_continuity_does_not_write_or_open_transport(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    def _forbid_open(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("file open is forbidden")

    def _forbid_socket(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("socket open is forbidden")

    monkeypatch.setattr("builtins.open", _forbid_open)
    monkeypatch.setattr(socket, "socket", _forbid_socket)
    before = set(tmp_path.iterdir())

    result = _continuity(ranking_favorite_id="ETH-USDT-SWAP")

    assert result.ranking_favorite_changed is True
    assert result.retained_instrument_id == "BTC-USDT-SWAP"
    _assert_continuity_closed(result)
    assert set(tmp_path.iterdir()) == before


def _isolation(**overrides: object) -> object:
    payload = {
        "epoch_id": "epoch-7",
        "natural_enter_binding": "INACTIVE",
        "selection_continuity_status": "SELECTION_CONTINUITY_HELD",
    }
    payload.update(overrides)
    return bind_universe_refresh_natural_enter_isolation_v1(
        UniverseRefreshNaturalEnterIsolationRequestV1(**payload)
    )


def _assert_isolation_closed(result: object) -> None:
    assert result.entry_symbol == NATURAL_ENTER_ENTRY_SYMBOL
    assert result.entry_module == NATURAL_ENTER_ENTRY_MODULE
    assert result.isolation_describes_only is True
    assert result.runtime_control_performed is False
    assert result.natural_enter_invoked is False
    assert result.natural_enter_restarted is False
    assert result.natural_enter_interrupted is False
    assert result.natural_enter_reset is False
    assert result.instrument_rebound is False
    assert result.trading_epoch_created is False
    assert result.trading_epoch_reset is False
    assert result.position_closed is False
    assert result.direction_switch_authorized is False
    assert result.master_v2_invoked is False
    assert result.double_play_invoked is False
    assert result.selection_mutated is False
    assert result.snapshot_write_attempted is False
    assert result.state_write_attempted is False
    assert result.network_requested is False
    assert result.http_get_performed is False
    assert result.http_post_performed is False
    assert result.public_websocket_connected is False
    assert result.private_websocket_connected is False
    assert result.subscription_opened is False


def test_inactive_natural_enter_stays_isolated() -> None:
    result = _isolation()

    assert result.status is (
        UniverseRefreshNaturalEnterIsolationStatusV1.NATURAL_ENTER_ISOLATION_HELD
    )
    assert result.natural_enter_binding == "INACTIVE"
    assert result.bound_instrument_id == ""
    assert result.trading_epoch_id == ""
    _assert_isolation_closed(result)


def test_bound_natural_enter_keeps_instrument_and_trading_epoch() -> None:
    result = _isolation(
        natural_enter_binding="BOUND",
        bound_instrument_id="BTC-USDT-SWAP",
        trading_epoch_id="trade-epoch-1",
        ranking_favorite_id="BTC-USDT-SWAP",
    )

    assert result.status is (
        UniverseRefreshNaturalEnterIsolationStatusV1.NATURAL_ENTER_ISOLATION_HELD
    )
    assert result.bound_instrument_id == "BTC-USDT-SWAP"
    assert result.trading_epoch_id == "trade-epoch-1"
    assert result.ranking_favorite_changed is False
    _assert_isolation_closed(result)


def test_unknown_binding_instrument_or_epoch_is_unproven() -> None:
    unknown = _isolation(natural_enter_binding="UNKNOWN")
    missing_instrument = _isolation(
        natural_enter_binding="BOUND",
        trading_epoch_id="trade-epoch-1",
    )
    missing_epoch = _isolation(
        natural_enter_binding="BOUND",
        bound_instrument_id="BTC-USDT-SWAP",
    )

    assert unknown.status is (
        UniverseRefreshNaturalEnterIsolationStatusV1.NATURAL_ENTER_ISOLATION_UNPROVEN
    )
    assert missing_instrument.status is (
        UniverseRefreshNaturalEnterIsolationStatusV1.NATURAL_ENTER_ISOLATION_UNPROVEN
    )
    assert missing_instrument.bound_instrument_id == ""
    assert missing_epoch.status is (
        UniverseRefreshNaturalEnterIsolationStatusV1.NATURAL_ENTER_ISOLATION_UNPROVEN
    )
    assert missing_epoch.trading_epoch_id == ""
    _assert_isolation_closed(unknown)
    _assert_isolation_closed(missing_instrument)
    _assert_isolation_closed(missing_epoch)


def test_ranking_change_and_unproven_continuity_do_not_rebind() -> None:
    changed = _isolation(
        natural_enter_binding="BOUND",
        bound_instrument_id="BTC-USDT-SWAP",
        trading_epoch_id="trade-epoch-1",
        ranking_favorite_id="ETH-USDT-SWAP",
    )
    unproven = _isolation(
        natural_enter_binding="BOUND",
        bound_instrument_id="BTC-USDT-SWAP",
        trading_epoch_id="trade-epoch-1",
        ranking_favorite_id="ETH-USDT-SWAP",
        selection_continuity_status="SELECTION_CONTINUITY_UNPROVEN",
    )

    assert changed.status is (
        UniverseRefreshNaturalEnterIsolationStatusV1.NATURAL_ENTER_ISOLATION_HELD
    )
    assert changed.ranking_favorite_changed is True
    assert changed.bound_instrument_id == "BTC-USDT-SWAP"
    assert changed.trading_epoch_id == "trade-epoch-1"
    assert unproven.status is (
        UniverseRefreshNaturalEnterIsolationStatusV1.NATURAL_ENTER_ISOLATION_UNPROVEN
    )
    assert unproven.selection_continuity_proven is False
    assert unproven.bound_instrument_id == "BTC-USDT-SWAP"
    assert unproven.trading_epoch_id == "trade-epoch-1"
    _assert_isolation_closed(changed)
    _assert_isolation_closed(unproven)


def test_isolation_constant_rebind_does_not_invoke(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(orchestrator, "NATURAL_ENTER_ISOLATION_INVOCATION_ALLOWED", True)

    result = _isolation()

    assert orchestrator.NATURAL_ENTER_ISOLATION_INVOCATION_ALLOWED is True
    assert result.natural_enter_invoked is False
    assert result.runtime_control_performed is False


def test_isolation_is_deterministic_and_does_not_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    def _forbid_open(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("file open is forbidden")

    def _forbid_socket(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("socket open is forbidden")

    monkeypatch.setattr("builtins.open", _forbid_open)
    monkeypatch.setattr(socket, "socket", _forbid_socket)
    before = set(tmp_path.iterdir())
    first = _isolation(
        natural_enter_binding="BOUND",
        bound_instrument_id="BTC-USDT-SWAP",
        trading_epoch_id="trade-epoch-1",
        ranking_favorite_id="ETH-USDT-SWAP",
    )
    second = _isolation(
        natural_enter_binding="BOUND",
        bound_instrument_id="BTC-USDT-SWAP",
        trading_epoch_id="trade-epoch-1",
        ranking_favorite_id="ETH-USDT-SWAP",
    )

    assert first == second
    _assert_isolation_closed(first)
    assert set(tmp_path.iterdir()) == before


def test_p1_to_p6_offline_sequence_does_not_execute_the_productive_chain(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    imported = _imported_modules(_tree())
    assert imported == set(_ALLOWED_IMPORT_MODULES)
    for module_name in imported:
        assert all(part not in module_name for part in _DENIED_IMPORT_PARTS)
    monkeypatch.chdir(tmp_path)

    def _forbid_open(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("file open is forbidden")

    def _forbid_socket(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("socket open is forbidden")

    monkeypatch.setattr("builtins.open", _forbid_open)
    monkeypatch.setattr(socket, "socket", _forbid_socket)

    refresh = run_universe_refresh_epoch_v1(UniverseRefreshEpochRequestV1(epoch_id="epoch-7"))
    budget = run_universe_refresh_budget_epoch_v1(
        UniverseRefreshBudgetEpochRequestV1(
            epoch_id="epoch-7",
            max_total_attempts=6,
            eligible_count=1,
        )
    )
    blocked_budget = run_universe_refresh_budget_epoch_v1(
        UniverseRefreshBudgetEpochRequestV1(
            epoch_id="epoch-7",
            max_total_attempts=4,
            eligible_count=1,
        )
    )
    binding = bind_universe_refresh_to_cap21_to_cap23_v1(
        UniverseRefreshCap21BindingRequestV1(epoch_id="epoch-7")
    )
    top20 = bind_universe_refresh_top20_snapshot_v1(
        UniverseRefreshTop20SnapshotRequestV1(
            epoch_id="epoch-7",
            snapshot=_committed_snapshot([_ranked("AAA", 1), _ranked("CCC", 2)]),
            snapshot_committed=True,
            prior_canonical_ids=("AAA",),
        )
    )
    continuity = _continuity(ranking_favorite_id="ETH-USDT-SWAP")
    isolation = _isolation(
        natural_enter_binding="BOUND",
        bound_instrument_id="BTC-USDT-SWAP",
        trading_epoch_id="trade-epoch-1",
        ranking_favorite_id="ETH-USDT-SWAP",
        selection_continuity_status=continuity.status.value,
    )
    blocked_isolation = _isolation(
        natural_enter_binding="BOUND",
        bound_instrument_id="BTC-USDT-SWAP",
        trading_epoch_id="trade-epoch-1",
        selection_continuity_status="SELECTION_CONTINUITY_UNPROVEN",
    )

    assert refresh.status is UniverseRefreshEpochStatusV1.REFRESH_NOT_AUTHORIZED
    assert budget.status is UniverseRefreshBudgetEpochStatusV1.BUDGET_ACCOUNTED
    assert budget.attempts_accounted == 6
    assert blocked_budget.status is UniverseRefreshBudgetEpochStatusV1.BUDGET_INSUFFICIENT
    assert blocked_budget.snapshot_published is False
    assert binding.status is (
        UniverseRefreshCap21BindingStatusV1.CAP21_TO_CAP23_BINDING_NOT_INVOKED
    )
    assert binding.invocation_performed is False
    assert binding.second_writer_claimed is False
    assert binding.hold_semantics_changed is False
    assert top20.status is UniverseRefreshTop20SnapshotStatusV1.TOP20_HYPOTHETICAL_ADMISSION
    assert top20.hypothetical_new == ("CCC",)
    assert top20.hypothetical_unchanged == ("AAA",)
    assert continuity.status is (
        UniverseRefreshSelectionContinuityStatusV1.SELECTION_CONTINUITY_HELD
    )
    assert continuity.ranking_favorite_changed is True
    assert isolation.status is (
        UniverseRefreshNaturalEnterIsolationStatusV1.NATURAL_ENTER_ISOLATION_HELD
    )
    assert isolation.bound_instrument_id == "BTC-USDT-SWAP"
    assert isolation.trading_epoch_id == "trade-epoch-1"
    assert blocked_isolation.status is (
        UniverseRefreshNaturalEnterIsolationStatusV1.NATURAL_ENTER_ISOLATION_UNPROVEN
    )
    assert refresh.producer_executed is False
    assert refresh.file_write_attempted is False
    _assert_no_effects(budget)
    _assert_top20_closed(top20)
    _assert_continuity_closed(continuity)
    _assert_isolation_closed(isolation)
    _assert_isolation_closed(blocked_isolation)
    assert not (tmp_path / "runtime_state").exists()
    assert set(tmp_path.iterdir()) == set()


def _canonical_budget() -> object:
    budget_type = orchestrator._SELECTION_NETWORK_BUDGET_V1.SelectionNetworkBudgetV1
    return budget_type(max_total_attempts=4)


def _foreign_budget() -> object:
    path = Path(
        "src/ops/governed_productive_account_equity_authority_producer_v1/"
        "current_productive_selection_network_budget_v1.py"
    )
    spec = spec_from_file_location("_wp_p8_noncanonical_budget", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("foreign budget module unavailable")
    module = module_from_spec(spec)
    sys.modules["_wp_p8_noncanonical_budget"] = module
    spec.loader.exec_module(module)
    return module.SelectionNetworkBudgetV1(max_total_attempts=4)


def _assert_preflight_closed(result: object) -> None:
    assert result.previous_selection_passed_as_none is False
    assert result.release_performed is False
    assert result.producer_executed is False
    assert result.cap21_invoked is False
    assert result.selection_mutated is False
    assert result.state_write_attempted is False
    assert result.network_requested is False
    assert result.http_get_performed is False
    assert result.http_post_performed is False
    assert result.public_websocket_connected is False
    assert result.private_websocket_connected is False
    assert result.master_v2_invoked is False
    assert result.double_play_invoked is False
    assert result.natural_enter_invoked is False


def test_orchestrator_import_keeps_one_canonical_budget_class() -> None:
    script = """
import sys
from importlib.util import module_from_spec, spec_from_file_location
name = (
    "src.ops.governed_productive_account_equity_authority_producer_v1."
    "current_productive_selection_network_budget_v1"
)
path = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_selection_network_budget_v1.py"
)
before = set(sys.modules)
spec = spec_from_file_location(name, path)
module = module_from_spec(spec)
sys.modules[name] = module
spec.loader.exec_module(module)
delta = set(sys.modules) - before
pkg = "src.ops.governed_productive_account_equity_authority_producer_v1"
banned = ("urllib", "http", "socket", "websocket", "trading", "double_play", "natural_enter")
bad = sorted(item for item in delta if any(part in item for part in banned))
assert pkg not in sys.modules
assert bad == [], bad
import src.ops.current_productive_universe_refresh_orchestrator_v1 as orch
assert orch.CANONICAL_SELECTION_BUDGET_MODULE == name
assert orch._SELECTION_NETWORK_BUDGET_V1.SelectionNetworkBudgetV1 is module.SelectionNetworkBudgetV1
assert pkg not in sys.modules
"""
    completed = subprocess.run(
        ["./scripts/pt", "-c", script],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_selection_network_budget_v1 import (
        SelectionNetworkBudgetV1,
    )

    loaded = orchestrator._SELECTION_NETWORK_BUDGET_V1.SelectionNetworkBudgetV1
    assert loaded is SelectionNetworkBudgetV1
    assert loaded.__module__ == orchestrator.CANONICAL_SELECTION_BUDGET_MODULE


def test_preflight_rejects_noncanonical_budget_before_any_producer() -> None:
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_selection_network_budget_v1 import (
        SelectionNetworkBudgetError,
        build_budgeted_economic_md_source_v1,
    )

    foreign = _foreign_budget()
    cap21 = Path(
        "src/ops/governed_productive_account_equity_authority_producer_v1/"
        "current_productive_cap21_to_cap23_productive_persistence_v1.py"
    ).read_text(encoding="utf-8")
    producer_at = cap21.index("run_governed_futures_universe_producer_v1(")
    guard_at = cap21.index('status="SELECTION_BUDGET_TYPE_INVALID"')
    result = preflight_universe_refresh_release_v1(
        UniverseRefreshReleasePreflightRequestV1(
            epoch_id="epoch-7",
            budget=foreign,
            continuity=_continuity(),
        )
    )

    assert producer_at < guard_at
    assert result.status is UniverseRefreshReleasePreflightStatusV1.PREFLIGHT_BUDGET_REJECTED
    assert result.budget_identity_canonical is False
    assert result.selection_handoff_supported is False
    _assert_preflight_closed(result)
    with pytest.raises(SelectionNetworkBudgetError, match="SELECTION_BUDGET_REQUIRED"):
        build_budgeted_economic_md_source_v1(
            budget=foreign,
            capture_timestamp="2024-01-01T00:00:00Z",
        )


def test_preflight_blocks_release_without_continuity_or_handoff() -> None:
    budget = _canonical_budget()
    unknown_continuity = _continuity(position_truth="UNKNOWN")
    unknown = preflight_universe_refresh_release_v1(
        UniverseRefreshReleasePreflightRequestV1(
            epoch_id="epoch-7",
            budget=budget,
            continuity=unknown_continuity,
        )
    )
    missing = preflight_universe_refresh_release_v1(
        UniverseRefreshReleasePreflightRequestV1(
            epoch_id="epoch-7",
            budget=budget,
            continuity=_continuity(previous_selection=None, state_provenance_proven=False),
        )
    )
    held = _continuity()
    blocked = preflight_universe_refresh_release_v1(
        UniverseRefreshReleasePreflightRequestV1(
            epoch_id="epoch-7",
            budget=budget,
            continuity=held,
        )
    )

    assert unknown_continuity.position_truth == "UNKNOWN"
    assert unknown_continuity.unknown_position_treated_as_flat is False
    assert unknown.status is (UniverseRefreshReleasePreflightStatusV1.PREFLIGHT_CONTINUITY_UNPROVEN)
    assert unknown.selection_handoff_supported is False
    assert held.min_holding_period_seconds == 3600.0
    assert missing.status is (UniverseRefreshReleasePreflightStatusV1.PREFLIGHT_CONTINUITY_UNPROVEN)
    assert blocked.status is (
        UniverseRefreshReleasePreflightStatusV1.PREFLIGHT_HANDOFF_PREPARED_NOT_INVOKED
    )
    assert blocked.selection_handoff_supported is True
    assert blocked.continuity_proven is True
    _assert_preflight_closed(unknown)
    _assert_preflight_closed(missing)
    _assert_preflight_closed(blocked)


def _cap21_function() -> ast.FunctionDef:
    path = Path(
        "src/ops/governed_productive_account_equity_authority_producer_v1/"
        "current_productive_cap21_to_cap23_productive_persistence_v1.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "run_cap21_to_cap23_persist_productive_v1"
    )
    return function


def _constant(node: ast.AST) -> object:
    assert isinstance(node, ast.Constant)
    return node.value


def test_existing_cap21_callers_keep_previous_selection_defaults() -> None:
    function = _cap21_function()
    defaults = {
        arg.arg: default
        for arg, default in zip(function.args.kwonlyargs, function.args.kw_defaults, strict=True)
    }
    policy_calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_single_selected_future_policy_v1"
    ]
    keywords = {keyword.arg: keyword.value for keyword in policy_calls[0].keywords}
    producer_call = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_governed_futures_universe_producer_v1"
    )
    budget_guard = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Constant) and node.value == "SELECTION_BUDGET_TYPE_INVALID"
    )

    assert _constant(defaults["previous_selection"]) is None
    assert _constant(defaults["load_previous_from_state"]) is False
    assert _constant(defaults["open_position_instrument_id"]) is None
    assert isinstance(keywords["previous_selection"], ast.Name)
    assert keywords["previous_selection"].id == "previous_selection"
    assert isinstance(keywords["load_previous_from_state"], ast.Name)
    assert keywords["load_previous_from_state"].id == "load_previous_from_state"
    assert isinstance(keywords["open_position_instrument_id"], ast.Name)
    assert keywords["open_position_instrument_id"].id == "open_position_instrument_id"
    assert "min_holding_period_seconds" not in keywords
    assert producer_call.lineno < budget_guard.lineno


def _handoff(**overrides: object) -> object:
    payload = {
        "epoch_id": "epoch-7",
        "budget": _canonical_budget(),
        "continuity": _continuity(),
        "previous_selection": _previous_selection(),
    }
    payload.update(overrides)
    return prepare_universe_refresh_selection_handoff_v1(
        UniverseRefreshSelectionHandoffRequestV1(**payload)
    )


def _assert_handoff_closed(result: object) -> None:
    assert result.load_previous_from_state is False
    assert result.holding_argument_supplied is False
    assert result.unknown_position_treated_as_flat is False
    assert result.invocation_performed is False
    assert result.producer_executed is False
    assert result.cap21_invoked is False
    assert result.selection_policy_invoked is False
    assert result.selection_mutated is False
    assert result.state_write_attempted is False
    assert result.network_requested is False
    assert result.http_get_performed is False
    assert result.http_post_performed is False
    assert result.public_websocket_connected is False
    assert result.private_websocket_connected is False
    assert result.master_v2_invoked is False
    assert result.double_play_invoked is False
    assert result.natural_enter_invoked is False


def test_refresh_handoff_prepares_explicit_previous_selection() -> None:
    previous = _previous_selection()
    held = _handoff(previous_selection=previous)
    opened_continuity = _continuity(
        position_truth="OPEN",
        open_position_instrument_id="BTC-USDT-SWAP",
        holding_elapsed_seconds=10.0,
        ranking_favorite_id="ETH-USDT-SWAP",
    )
    opened = _handoff(
        continuity=opened_continuity,
        open_position_instrument_id="BTC-USDT-SWAP",
    )

    assert held.status is UniverseRefreshSelectionHandoffStatusV1.HANDOFF_PREPARED_NOT_INVOKED
    assert held.previous_selection == previous
    assert held.open_position_instrument_id is None
    assert held.position_truth == "FLAT"
    assert opened.status is UniverseRefreshSelectionHandoffStatusV1.HANDOFF_PREPARED_NOT_INVOKED
    assert opened.open_position_instrument_id == "BTC-USDT-SWAP"
    assert opened.holding_period_active is True
    assert opened_continuity.min_holding_period_seconds == 3600.0
    _assert_handoff_closed(held)
    _assert_handoff_closed(opened)


def test_refresh_handoff_rejects_unproven_continuity_and_invalid_budget() -> None:
    missing = _handoff(
        previous_selection=None,
        continuity=_continuity(previous_selection=None, state_provenance_proven=False),
    )
    unproven_origin = _handoff(continuity=_continuity(state_provenance_proven=False))
    unknown = _handoff(continuity=_continuity(position_truth="UNKNOWN"))
    rejected = _handoff(budget=_foreign_budget())

    assert missing.status is (UniverseRefreshSelectionHandoffStatusV1.HANDOFF_CONTINUITY_UNPROVEN)
    assert missing.previous_selection is None
    assert unproven_origin.status is (
        UniverseRefreshSelectionHandoffStatusV1.HANDOFF_CONTINUITY_UNPROVEN
    )
    assert unknown.status is UniverseRefreshSelectionHandoffStatusV1.HANDOFF_CONTINUITY_UNPROVEN
    assert unknown.position_truth == "UNKNOWN"
    assert rejected.status is UniverseRefreshSelectionHandoffStatusV1.HANDOFF_BUDGET_REJECTED
    assert rejected.budget_rejected_before_producer is True
    assert rejected.previous_selection is None
    _assert_handoff_closed(missing)
    _assert_handoff_closed(unproven_origin)
    _assert_handoff_closed(unknown)
    _assert_handoff_closed(rejected)


def _required_mark_count() -> int:
    feature = sys.modules[orchestrator._WP_P12_FEATURE_CONSTANTS]
    economic = sys.modules[orchestrator._WP_P12_ECONOMIC_MD_CONSTANTS]
    assert feature.MARK_COUNT == economic.MINIMUM_FINALIZED_PT1M_MARKS
    return int(feature.MARK_COUNT)


def _completion_evidence(**overrides: object) -> DataCompletionEvidenceV1:
    marks = _required_mark_count()
    payload = {
        "instrument_id": "BTC-USDT-SWAP",
        "economic_md_ok": True,
        "economic_input_snapshot_id": "econ-1",
        "economic_instrument_id": "BTC-USDT-SWAP",
        "economic_raw_input_eligible": True,
        "economic_raw_input_digest": "digest-econ",
        "economic_mark_count": marks,
        "feature_production_snapshot_id": "feat-1",
        "feature_production_digest": "digest-feat",
        "feature_instrument_id": "BTC-USDT-SWAP",
        "feature_production_ready": True,
        "feature_mark_count": marks,
        "feature_economic_md_raw_input_digest": "digest-econ",
        "ranking_snapshot_id": "rank-1",
        "ranking_snapshot_state": "VALID",
        "ranking_instrument_id": "BTC-USDT-SWAP",
        "ranking_feature_production_snapshot_id": "feat-1",
        "ranking_feature_production_digest": "digest-feat",
        "residency_epoch_id": "res-epoch-1",
        "bound_residency_epoch_id": "res-epoch-1",
    }
    payload.update(overrides)
    return DataCompletionEvidenceV1(**payload)


def _assert_completion_closed(result: object) -> None:
    assert result.slot_release_performed is False
    assert result.admission_performed is False
    assert result.residency_write_attempted is False
    assert result.scheduler_tick_performed is False
    assert result.replay_witness_created is False
    assert result.timeout_completion is False
    assert result.positive_negative_evaluation is False
    assert result.ranking_authority is False
    assert result.selection_authority is False
    assert result.trading_authority is False
    assert result.network_requested is False
    assert result.http_get_performed is False
    assert result.http_post_performed is False
    assert result.public_websocket_connected is False
    assert result.private_websocket_connected is False


def test_complete_data_prepares_hypothetical_slot_release(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    def _forbid_open(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("file open is forbidden")

    def _forbid_socket(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("socket open is forbidden")

    monkeypatch.setattr("builtins.open", _forbid_open)
    monkeypatch.setattr(socket, "socket", _forbid_socket)
    before = set(tmp_path.iterdir())
    released = assess_data_completion_slot_release_v1(
        _completion_evidence(slot_already_released=True)
    )
    result = assess_data_completion_slot_release_v1(_completion_evidence())

    assert result.status is DataCompletionStatusV1.DATA_COMPLETION_PROVEN
    assert result.hypothetical_slot_release is True
    assert result.residency_epoch_id == "res-epoch-1"
    assert released.status is DataCompletionStatusV1.DATA_COMPLETION_PROVEN
    assert released.hypothetical_slot_release is False
    assert released.slot_already_released is True
    _assert_completion_closed(result)
    _assert_completion_closed(released)
    assert set(tmp_path.iterdir()) == before


def test_incomplete_or_mismatched_data_stays_unproven() -> None:
    cases = (
        _completion_evidence(economic_md_ok=False),
        _completion_evidence(feature_mark_count=_required_mark_count() - 1),
        _completion_evidence(feature_production_ready=False),
        _completion_evidence(ranking_snapshot_state="INVALID"),
        _completion_evidence(ranking_instrument_id="ETH-USDT-SWAP"),
        _completion_evidence(bound_residency_epoch_id="res-epoch-2"),
        _completion_evidence(ranking_snapshot_id=".productive_futures_ranking_staging_rank"),
    )

    for evidence in cases:
        result = assess_data_completion_slot_release_v1(evidence)
        assert result.status is DataCompletionStatusV1.DATA_COMPLETION_UNPROVEN
        assert result.hypothetical_slot_release is False
        _assert_completion_closed(result)
