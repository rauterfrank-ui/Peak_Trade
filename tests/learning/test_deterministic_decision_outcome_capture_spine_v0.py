"""WP-FA-04 non-semantic decision-spine capture tests.

These tests prove observation-only capture. They do not claim FA/IC IDs PASS
in runbook or status documents. Mapping is test-local only.
"""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingInputV1,
    InstrumentQuantityConstraintsV1,
    evaluate_capital_risk_sizing_v1,
)
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY,
    CAPTURE_ADAPTER_PRESENT,
    LEARNING_PRODUCTIVE_AUTHORITY,
    PRODUCTIVE_CAPTURE_ADAPTERS,
    PRODUCTIVE_RUNTIME_WIRING,
    PROMOTION_AUTHORITY_ACTIVATION,
    RUNTIME_EFFECT,
    SECOND_EXECUTION_AUTHORITY_CREATED,
    SECOND_PROMOTION_AUTHORITY_CREATED,
    SECOND_TRADING_AUTHORITY_CREATED,
    WORKPACKAGE_ID,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    BLOCKED_CAPTURE_SEAMS_V0,
    HOST_DECORATOR_SPINE_COMPLETE_V0,
    IMPLEMENTED_CAPTURE_SEAMS_V0,
    PROVEN_HOST_DECORATOR_BINDINGS_V0,
    SEAM_BULL_BEAR,
    SEAM_DYNAMIC_SCOPE,
    SEAM_KILLSWITCH_FLAG,
    SEAM_SELECTION_UNIVERSE,
    SEAM_STEP_29P_RISK_SIZING,
    DdoCaptureBindingV0,
    bind_capture_session_v0,
    observe_producer_result_v0,
    record_productive_cycle_capture_v0,
    reset_capture_session_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.reason_codes_v0 import (
    EXISTING_OPAQUE_TAXONOMY_ID,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.intended_action_mapper_v1 import (
    map_replay_result_to_intended_analytical_action_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationCandidateV1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src" / "learning" / "deterministic_decision_outcome_v0"
CAPTURE_PATH = PACKAGE_DIR / "capture_v0.py"
EVENT_UNIX = 1_700_000_100.0
REPO_SHA = "02a1c65a1fe9c3c806fb846da949dfd6d864be94"

FORBIDDEN_IMPORT_PREFIXES = (
    "src.trading",
    "src.execution",
    "src.live",
    "src.risk",
    "src.risk_layer",
    "src.ops",
    "urllib",
    "requests",
    "httpx",
    "aiohttp",
    "socket",
    "http.client",
)


def _session(tmp_path: Path | None = None) -> DdoCaptureBindingV0:
    ledger_path = None if tmp_path is None else tmp_path / "ddo_capture.jsonl"
    return DdoCaptureBindingV0(enabled=True, ledger_path=ledger_path)


def test_fa_01_producer_output_identical_with_and_without_capture() -> None:
    """FA-01: producer output identical with and without capture."""
    kwargs = {
        "source_payload": None,
        "repository_sha": REPO_SHA,
        "producer_observed_at_unix": EVENT_UNIX,
        "snapshot_id": "gfu_fixed_capture_eq_01",
    }
    without = produce_governed_futures_universe_v1(**kwargs)
    binding = _session()
    session_handle = bind_capture_session_v0(binding)
    try:
        with_capture = produce_governed_futures_universe_v1(**kwargs)
    finally:
        reset_capture_session_v0(session_handle)
    assert with_capture == without
    assert with_capture.failure_codes == without.failure_codes
    assert with_capture.ok is without.ok
    assert with_capture.hard_stop is without.hard_stop
    assert binding.captured_records
    assert all(item["decision_result"] == "NO_ACTION" for item in binding.captured_records)


def test_fa_02_producer_reason_codes_preserved_verbatim() -> None:
    """FA-02: producer reason codes preserved verbatim, semantically uninterpreted."""
    kwargs = {
        "source_payload": None,
        "repository_sha": REPO_SHA,
        "producer_observed_at_unix": EVENT_UNIX,
        "snapshot_id": "gfu_fixed_capture_eq_01",
    }
    produced = produce_governed_futures_universe_v1(**kwargs)
    binding = _session()
    session_handle = bind_capture_session_v0(binding)
    try:
        captured_prod = produce_governed_futures_universe_v1(**kwargs)
    finally:
        reset_capture_session_v0(session_handle)
    assert captured_prod.failure_codes == produced.failure_codes
    record = binding.captured_records[0]
    captured_codes = tuple(item["code"] for item in record["reason_codes"])
    for code in produced.failure_codes:
        assert code in captured_codes
    assert all(
        item["taxonomy_id"] == EXISTING_OPAQUE_TAXONOMY_ID for item in record["reason_codes"]
    )
    assert all(
        item["source_taxonomy_ref"]
        == "src/ops/governed_futures_universe_producer_v1/reason_codes_v1.py"
        for item in record["reason_codes"]
    )


def test_fa_04_capture_occurs_after_authoritative_producer_decision() -> None:
    """FA-04: capture observes the already-returned producer result."""
    order: list[str] = []

    def producer(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        order.append("producer")
        return {
            "ok": False,
            "hard_stop": True,
            "failure_codes": ("OKX_SOURCE_UNAVAILABLE",),
        }

    from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
        observe_after_producer_v0,
    )

    wrapped = observe_after_producer_v0(seam_id=SEAM_SELECTION_UNIVERSE)(producer)
    binding = _session()
    session_handle = bind_capture_session_v0(binding)

    orig_observe = observe_producer_result_v0

    def _observe(*args: Any, **kwargs: Any) -> dict[str, Any]:
        order.append("capture")
        return orig_observe(*args, **kwargs)

    import src.learning.deterministic_decision_outcome_v0.capture_v0 as capture_mod

    capture_mod.observe_producer_result_v0 = _observe  # type: ignore[method-assign]
    try:
        result = wrapped(producer_observed_at_unix=EVENT_UNIX)
    finally:
        capture_mod.observe_producer_result_v0 = orig_observe
        reset_capture_session_v0(session_handle)
    assert result["failure_codes"] == ("OKX_SOURCE_UNAVAILABLE",)
    assert order == ["producer", "capture"]


def test_fa_05_capture_exception_does_not_change_productive_result(monkeypatch: Any) -> None:
    """FA-05: capture exception does not change the productive result."""

    def boom(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("CAPTURE_INJECTED_FAILURE")

    monkeypatch.setattr(
        "src.learning.deterministic_decision_outcome_v0.capture_v0._persist",
        boom,
    )
    kwargs = {
        "source_payload": None,
        "repository_sha": REPO_SHA,
        "producer_observed_at_unix": EVENT_UNIX,
        "snapshot_id": "gfu_fixed_capture_eq_01",
    }
    baseline = produce_governed_futures_universe_v1(**kwargs)
    binding = _session()
    session_handle = bind_capture_session_v0(binding)
    try:
        result = produce_governed_futures_universe_v1(**kwargs)
    finally:
        reset_capture_session_v0(session_handle)
    assert result == baseline
    assert binding.last_error is not None
    assert "CAPTURE_INJECTED_FAILURE" in binding.last_error


def test_fa_15_no_reverse_authority_dependency_from_core_to_learning() -> None:
    """FA-15: capture package must not import productive core/ops/trading surfaces."""
    hits: list[str] = []
    tree = ast.parse(CAPTURE_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
        for name in names:
            if any(
                name == prefix or name.startswith(prefix + ".")
                for prefix in FORBIDDEN_IMPORT_PREFIXES
            ):
                hits.append(name)
    assert hits == []
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert SECOND_TRADING_AUTHORITY_CREATED is False
    assert SECOND_EXECUTION_AUTHORITY_CREATED is False
    assert PROMOTION_AUTHORITY_ACTIVATION is False
    assert AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY is False
    assert RUNTIME_EFFECT == "NONE"


def test_ic_01_unknown_remains_unknown() -> None:
    """IC-01: UNKNOWN remains UNKNOWN; no silent normalization or stale inference."""
    binding = _session()
    record = observe_producer_result_v0(
        binding,
        seam_id=SEAM_BULL_BEAR,
        result={
            "previous_direction_state": "long_armed",
            "next_direction_state": "long_armed",
            "reason_codes": (),
        },
        event_time_utc="2026-09-01T12:00:00Z",
        correlation_id="ddo.corr.unknown1",
    )
    stored = next(
        item for item in binding.captured_records if item["record_id"] == record["record_id"]
    )
    assert stored["decision_type"] == UNKNOWN
    assert stored["decision_result"] == "NO_ACTION"
    assert stored["reason_codes"][0]["code"] == UNKNOWN
    incident = observe_producer_result_v0(
        binding,
        seam_id=SEAM_KILLSWITCH_FLAG,
        result={"killswitch_blocked": True},
        event_time_utc="2026-09-01T12:00:01Z",
        correlation_id="ddo.corr.unknown1",
    )
    inc = next(
        item for item in binding.captured_records if item["record_id"] == incident["incident_id"]
    )
    assert inc["stale_root_cause"] == UNKNOWN


def test_ic_02_one_authoritative_producer_per_domain() -> None:
    """IC-02: one authoritative producer per capture domain; no second trading authority."""
    assert CAPTURE_ADAPTER_PRESENT is True
    assert PRODUCTIVE_CAPTURE_ADAPTERS is True
    assert PRODUCTIVE_RUNTIME_WIRING is True
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert len(IMPLEMENTED_CAPTURE_SEAMS_V0) == 21
    assert len(BLOCKED_CAPTURE_SEAMS_V0) == 8
    assert "independent_killswitch_layer" in BLOCKED_CAPTURE_SEAMS_V0


def test_ic_16_append_only_ledger_semantics(tmp_path: Path) -> None:
    """IC-16: captured records persist append-only."""
    binding = _session(tmp_path)
    first = observe_producer_result_v0(
        binding,
        seam_id=SEAM_SELECTION_UNIVERSE,
        result={"ok": False, "hard_stop": True, "failure_codes": ("OKX_SOURCE_UNAVAILABLE",)},
        event_time_utc="2026-09-01T12:00:00Z",
        correlation_id="ddo.corr.ledger1",
    )
    second = observe_producer_result_v0(
        binding,
        seam_id=SEAM_SELECTION_UNIVERSE,
        result={"ok": False, "hard_stop": True, "failure_codes": ("EMPTY_ELIGIBLE_UNIVERSE",)},
        event_time_utc="2026-09-01T12:00:01Z",
        correlation_id="ddo.corr.ledger1",
    )
    assert first["record_id"] != second["record_id"]
    ledger = AppendOnlyDdoLedgerV0(binding.ledger_path)
    loaded = ledger.read_all()
    assert len(loaded) == 2
    assert loaded[0]["record_id"] == first["record_id"]
    assert loaded[1]["record_id"] == second["record_id"]
    text = Path(binding.ledger_path).read_text(encoding="utf-8")
    assert text.count("\n") == 2


def test_identical_inputs_produce_stable_ddo_serialization_and_hash() -> None:
    binding = _session()
    payload = {
        "ok": False,
        "hard_stop": True,
        "failure_codes": ("RANKING_SNAPSHOT_STALE",),
    }
    first = observe_producer_result_v0(
        binding,
        seam_id=SEAM_SELECTION_UNIVERSE,
        result=payload,
        event_time_utc="2026-09-01T12:00:00Z",
        correlation_id="ddo.corr.stable1",
        cycle_id="cycle:stable:0001",
        repository_sha=REPO_SHA,
    )
    second = observe_producer_result_v0(
        binding,
        seam_id=SEAM_SELECTION_UNIVERSE,
        result=dict(payload),
        event_time_utc="2026-09-01T12:00:00Z",
        correlation_id="ddo.corr.stable1",
        cycle_id="cycle:stable:0001",
        repository_sha=REPO_SHA,
    )
    assert first["record_id"] == second["record_id"]
    assert first["content_hash"] == second["content_hash"]


def test_no_action_and_non_transition_are_first_class_evidence() -> None:
    binding = _session()
    no_action = observe_producer_result_v0(
        binding,
        seam_id=SEAM_SELECTION_UNIVERSE,
        result={"ok": True, "hard_stop": False, "failure_codes": ()},
        event_time_utc="2026-09-01T12:00:00Z",
        correlation_id="ddo.corr.firstclass",
    )
    non_transition = observe_producer_result_v0(
        binding,
        seam_id=SEAM_DYNAMIC_SCOPE,
        result={"last_scope_advanced": False, "event_type": "noop"},
        event_time_utc="2026-09-01T12:00:00Z",
        correlation_id="ddo.corr.firstclass",
    )
    bull_hold = observe_producer_result_v0(
        binding,
        seam_id=SEAM_BULL_BEAR,
        result={"previous_direction_state": "long_active", "next_direction_state": "long_active"},
        event_time_utc="2026-09-01T12:00:00Z",
        correlation_id="ddo.corr.firstclass",
    )
    stored = {item["record_id"]: item for item in binding.captured_records}
    assert stored[no_action["record_id"]]["decision_result"] == "NO_ACTION"
    assert stored[non_transition["record_id"]]["decision_type"] == "DYNAMIC_SCOPE_NON_TRANSITION"
    assert stored[bull_hold["record_id"]]["decision_type"] == UNKNOWN
    assert stored[bull_hold["record_id"]]["decision_result"] == "NO_ACTION"


def test_hard_block_reasons_preserved_without_reinterpretation() -> None:
    binding = _session()
    observe_producer_result_v0(
        binding,
        seam_id=SEAM_STEP_29P_RISK_SIZING,
        result={"outcome": "BLOCKED", "hard_stop": True, "reason_codes": ("CAPITAL_LIMIT",)},
        event_time_utc="2026-09-01T12:00:00Z",
        correlation_id="ddo.corr.hardblock",
    )
    decision = next(
        item for item in binding.captured_records if item["schema_name"] == "decision_event"
    )
    assert decision["decision_type"] == "RISK_BLOCK"
    assert decision["hard_block_reasons"][0]["code"] == "CAPITAL_LIMIT"
    assert decision["hard_block_reasons"][0]["taxonomy_id"] == EXISTING_OPAQUE_TAXONOMY_ID
    incident = next(
        item for item in binding.captured_records if item["schema_name"] == "incident_record"
    )
    assert incident["incident_class"] == "RISK"
    assert incident["stale_root_cause"] == UNKNOWN
    assert incident["hard_block_reasons"][0]["code"] == "CAPITAL_LIMIT"


def test_cycle_capture_failure_does_not_change_host_result(monkeypatch: Any) -> None:
    def boom(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("CYCLE_CAPTURE_INJECTED_FAILURE")

    monkeypatch.setattr(
        "src.learning.deterministic_decision_outcome_v0.capture_v0.observe_producer_result_v0",
        boom,
    )
    binding = _session()
    summary = record_productive_cycle_capture_v0(
        binding,
        repository_sha=REPO_SHA,
        session_id="cycle-iso",
        cycle_index=1,
        event_ts_unix=EVENT_UNIX,
        observation_acceptance_result={"reason_code": "observation_accepted_distinct"},
        features={"regime_id": "unknown", "volatility_estimate": 0.1, "blockers": ()},
    )
    assert summary["ok"] is False
    assert summary["decision_unchanged"] is True
    assert "CYCLE_CAPTURE_INJECTED_FAILURE" in str(summary["error"])


def test_execution_authorized_remains_false_and_no_second_authority() -> None:
    binding = _session()
    observe_producer_result_v0(
        binding,
        seam_id=SEAM_SELECTION_UNIVERSE,
        result={"ok": True, "hard_stop": False, "failure_codes": (), "execution_eligible": False},
        event_time_utc="2026-09-01T12:00:00Z",
        correlation_id="ddo.corr.execfalse",
    )
    record = binding.captured_records[0]
    assert record["decision_result"] == "NO_ACTION"
    assert "TRADE" not in str(record)
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert SECOND_EXECUTION_AUTHORITY_CREATED is False


def _decorator_seam_ids(node: ast.AST) -> set[str]:
    found: set[str] = set()
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return found
    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        func = dec.func
        name = ""
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        if name != "observe_after_producer_v0":
            continue
        for kw in dec.keywords:
            if kw.arg == "seam_id" and isinstance(kw.value, ast.Constant):
                if isinstance(kw.value.value, str):
                    found.add(kw.value.value)
    return found


def test_wp_fs_b1_all_implemented_seams_have_proven_host_decorator() -> None:
    assert HOST_DECORATOR_SPINE_COMPLETE_V0 is True
    assert len(IMPLEMENTED_CAPTURE_SEAMS_V0) == 21
    bound = {item.seam_id: item for item in PROVEN_HOST_DECORATOR_BINDINGS_V0}
    assert set(bound) == set(IMPLEMENTED_CAPTURE_SEAMS_V0)
    for seam_id in IMPLEMENTED_CAPTURE_SEAMS_V0:
        item = bound[seam_id]
        path = REPO_ROOT / item.source_path
        assert path.is_file(), item.source_path
        tree = ast.parse(path.read_text(encoding="utf-8"))
        seam_ids: set[str] = set()
        for node in ast.walk(tree):
            seam_ids.update(_decorator_seam_ids(node))
        assert seam_id in seam_ids, f"{seam_id} missing host decorator in {item.source_path}"


def test_wp_fs_b1_blocked_seams_have_no_host_decorator() -> None:
    src_root = REPO_ROOT / "src"
    blocked_hits: list[str] = []
    for path in src_root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            for seam_id in _decorator_seam_ids(node) & set(BLOCKED_CAPTURE_SEAMS_V0):
                rel = path.relative_to(REPO_ROOT).as_posix()
                blocked_hits.append(f"{rel}:{getattr(node, 'name', '?')}:{seam_id}")
    assert blocked_hits == []


def test_wp_fs_b1_c1_host_is_acceptor_not_host_wrapper() -> None:
    host_path = (
        REPO_ROOT / "src/ops/stateful_confirmation_and_c1_productive_binding_v1/host_binding_v1.py"
    )
    tree = ast.parse(host_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "evaluate_host_observation_acceptance_v1"
        ):
            assert "c1.observation_acceptance" not in _decorator_seam_ids(node)


def _c1_candidate() -> ObservationCandidateV1:
    return ObservationCandidateV1(
        venue="okx_eea",
        canonical_instrument_id="ETH-USD-SWAP-CANON",
        venue_instrument_id="ETH-USD-SWAP",
        venue_event_time=EVENT_UNIX,
        mark_price=3500.25,
        transport=None,
    )


def test_wp_fs_b1_c1_output_identical_with_and_without_capture() -> None:
    key = InstrumentObservationKeyV1(
        venue="okx_eea",
        canonical_instrument_id="ETH-USD-SWAP-CANON",
        venue_instrument_id="ETH-USD-SWAP",
    )
    state = initial_observation_acceptance_state_v1(bound_instrument_key=key)
    candidate = _c1_candidate()
    without = evaluate_distinct_market_observation_v1(state, candidate)
    binding = _session()
    session_handle = bind_capture_session_v0(binding)
    try:
        with_capture = evaluate_distinct_market_observation_v1(state, candidate)
    finally:
        reset_capture_session_v0(session_handle)
    assert with_capture == without
    assert binding.captured_records
    assert all(item["decision_result"] == "NO_ACTION" for item in binding.captured_records)


def test_wp_fs_b1_mapper_output_identical_with_and_without_capture() -> None:
    replay = SimpleNamespace(
        replay_pass=True,
        evidence=SimpleNamespace(
            decision_outcome="no_action",
            selected_side="",
            reason_codes=(),
        ),
        intermediate=None,
        as_of_event_time="2024-01-15T12:00:00Z",
    )
    without = map_replay_result_to_intended_analytical_action_v1(
        replay,  # type: ignore[arg-type]
        instrument_id="ETH-USD-SWAP",
    )
    binding = _session()
    session_handle = bind_capture_session_v0(binding)
    try:
        with_capture = map_replay_result_to_intended_analytical_action_v1(
            replay,  # type: ignore[arg-type]
            instrument_id="ETH-USD-SWAP",
        )
    finally:
        reset_capture_session_v0(session_handle)
    assert with_capture == without
    assert binding.captured_records


def test_wp_fs_b1_step_29p_output_identical_with_and_without_capture() -> None:
    inp = CapitalRiskSizingInputV1(
        decision_id="decision-b1",
        instrument_id="ETH-USD-PERP",
        selected_side="LONG",
        reference_price=Decimal("2000"),
        protective_stop_price=Decimal("1900"),
        stop_distance=None,
        account_equity=Decimal("500"),
        scope_capital_limit=Decimal("25"),
        per_trade_risk_limit=Decimal("25"),
        total_capital_limit=Decimal("500"),
        daily_loss_remaining_budget=Decimal("25"),
        current_reconciled_exposure=Decimal("0"),
        maximum_positions=1,
        current_open_positions_count=0,
        current_open_side=None,
        configured_quantity_cap=None,
        leverage_ceiling=Decimal("5"),
        reconciliation_status="RECONCILED",
        policy_version="capital_risk_sizing_policy_v1",
        config_digest="b" * 64,
        input_digest="a" * 64,
        instrument=InstrumentQuantityConstraintsV1(
            instrument_id="ETH-USD-PERP",
            market_type="futures",
            contract_kind="LINEAR",
            contract_multiplier=Decimal("1"),
            lot_size=Decimal("0.01"),
            minimum_quantity=Decimal("0.01"),
            maximum_quantity=Decimal("100"),
            minimum_notional=Decimal("5"),
            tick_size=Decimal("0.01"),
            instrument_metadata_version="futures_metadata_v1_test",
        ),
        decision_outcome="enter_long",
    )
    without = evaluate_capital_risk_sizing_v1(inp)
    binding = _session()
    session_handle = bind_capture_session_v0(binding)
    try:
        with_capture = evaluate_capital_risk_sizing_v1(inp)
    finally:
        reset_capture_session_v0(session_handle)
    assert with_capture == without


def test_wp_fs_b1_capture_exception_does_not_change_c1_result(monkeypatch: Any) -> None:
    def boom(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("CAPTURE_INJECTED_FAILURE")

    monkeypatch.setattr(
        "src.learning.deterministic_decision_outcome_v0.capture_v0._persist",
        boom,
    )
    key = InstrumentObservationKeyV1(
        venue="okx_eea",
        canonical_instrument_id="ETH-USD-SWAP-CANON",
        venue_instrument_id="ETH-USD-SWAP",
    )
    state = initial_observation_acceptance_state_v1(bound_instrument_key=key)
    candidate = _c1_candidate()
    baseline = evaluate_distinct_market_observation_v1(state, candidate)
    binding = _session()
    session_handle = bind_capture_session_v0(binding)
    try:
        result = evaluate_distinct_market_observation_v1(state, candidate)
    finally:
        reset_capture_session_v0(session_handle)
    assert result == baseline
    assert binding.last_error is not None
    assert "CAPTURE_INJECTED_FAILURE" in binding.last_error


def test_wp_fs_b1_does_not_create_second_authority_or_reach_supervisor() -> None:
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert SECOND_TRADING_AUTHORITY_CREATED is False
    assert SECOND_EXECUTION_AUTHORITY_CREATED is False
    assert SECOND_PROMOTION_AUTHORITY_CREATED is False
    assert PROMOTION_AUTHORITY_ACTIVATION is False
    assert AUTONOMY_SUPERVISOR_RUNTIME_REACHABILITY is False
    assert WORKPACKAGE_ID != "WP_FA_08"
    assert "WP_FA_08" not in WORKPACKAGE_ID
