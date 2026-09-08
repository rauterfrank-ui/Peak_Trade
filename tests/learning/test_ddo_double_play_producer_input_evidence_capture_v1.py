"""DDO Double-Play producer-input evidence capture v1.

Observation-only. Does not re-run evaluate_double_play_entry_exit_policy_v0
as a replay engine. Reconstructs the typed input object from immutable evidence
and compares it to the original decision-time object.
"""

from __future__ import annotations

import ast
import json
from dataclasses import fields, replace
from pathlib import Path
from typing import Any

from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    DdoCaptureBindingV0,
    SEAM_DOUBLE_PLAY_ENTRY_EXIT,
    bind_capture_session_v0,
    bind_host_cycle_capture_context_v0,
    observe_producer_result_v0,
    reset_capture_session_v0,
)
from src.learning.deterministic_decision_outcome_v0.contract_registry_v0 import (
    get_schema_contract_v0,
)
from src.learning.deterministic_decision_outcome_v0.double_play_input_evidence_v1 import (
    CAPTURE_TIMING_BEFORE_PRODUCER_CALL,
    DIGEST_RELATION_SUBSET_SCOPE,
    PRODUCER_INPUT_FIELD_KEYS,
    RUNTIME_EFFECT_OBSERVATION_ONLY,
    SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE,
    SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_V1,
    TRADING_AUTHORITY_NONE,
    TYPED_PROJECTION_STATUS,
    UNAVAILABLE_PROJECTION_STATUS,
    compute_producer_input_digest_from_canonical_payload_v1,
    project_double_play_entry_exit_policy_input_v1,
    reconstruct_typed_double_play_entry_exit_policy_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    DoublePlayEntryExitPolicyInputV0,
    DoublePlayEntryExitPolicyV0,
    EntryExitDirectionState,
    ExistingPositionSide,
    PolicyBlockedReason,
    PolicySignalV0,
    PositionState,
    ReconciliationState,
    SafetyMode,
    TradingGate,
    compute_entry_exit_policy_input_digest,
    evaluate_double_play_entry_exit_policy_v0,
    serialize_entry_exit_policy_input_canonical,
)
from tests.trading.master_v2.test_double_play_entry_exit_policy_v0 import (
    _long_selected_composition,
    _policy_input,
    _short_selected_composition,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src" / "learning" / "deterministic_decision_outcome_v0"
EVENT_TIME = "2026-09-08T12:00:00Z"
CORR_ID = "ddo.corr.dp.input.v1"
CYCLE_ID = "cycle:dp:input:0001"
EVENT_UNIX = 1_757_347_200.0

FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "src.live",
    "src.risk",
    "src.risk_layer",
    "src.governance.promotion",
    "src.ops",
)
SECRET_KEYS = frozenset(
    {
        "api_key",
        "secret",
        "authorization",
        "bearer",
        "signature",
        "session_credential",
        "confirm_token",
        "password",
        "private_key",
    }
)
HINDSIGHT_KEYS = frozenset(
    {
        "later_price",
        "later_prices",
        "fill",
        "fills",
        "pnl",
        "later_pnl",
        "outcome_record",
        "attribution",
        "counterfactual",
        "future_bars",
        "hindsight",
    }
)


def _project(
    inp: DoublePlayEntryExitPolicyInputV0,
    *,
    policy_version: str = "double_play_entry_exit_policy_v0",
) -> Any:
    return project_double_play_entry_exit_policy_input_v1(
        inp,
        record_id="ddo.dpi.input.0001",
        event_time_utc=EVENT_TIME,
        correlation_id=CORR_ID,
        cycle_id=CYCLE_ID,
        decision_event_ref="ddo.dec.input.0001",
        typed_output_observation_ref="ddo.dpo.input.0001",
        producer_call_policy_version=policy_version,
        capture_timing=CAPTURE_TIMING_BEFORE_PRODUCER_CALL,
    )


def _capture_with_decorator(
    inp: DoublePlayEntryExitPolicyInputV0,
    policy: DoublePlayEntryExitPolicyV0 | None = None,
) -> tuple[Any, DdoCaptureBindingV0]:
    policy = policy or DoublePlayEntryExitPolicyV0()
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=None)
    bind_host_cycle_capture_context_v0(
        binding,
        event_ts_unix=EVENT_UNIX,
        session_id="dp-input-evidence",
        cycle_index=1,
        repository_sha=UNKNOWN,
    )
    token = bind_capture_session_v0(binding)
    try:
        result = evaluate_double_play_entry_exit_policy_v0(inp, policy)
    finally:
        reset_capture_session_v0(token)
    return result, binding


def _input_records(binding: DdoCaptureBindingV0) -> list[dict[str, Any]]:
    return [
        item
        for item in binding.captured_records
        if item["schema_name"] == SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE
    ]


def _enter_input() -> DoublePlayEntryExitPolicyInputV0:
    return _policy_input(
        composition_result=_long_selected_composition(),
        direction_state=EntryExitDirectionState.LONG_ARMED,
    )


def _exit_input() -> DoublePlayEntryExitPolicyInputV0:
    return _policy_input(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        profit_protection_signal=PolicySignalV0(triggered=True, reason_code="profit_lock"),
    )


def _hold_input() -> DoublePlayEntryExitPolicyInputV0:
    return _policy_input(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        composition_result=_long_selected_composition(),
    )


def _reversal_input() -> DoublePlayEntryExitPolicyInputV0:
    return _policy_input(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        composition_result=_short_selected_composition(),
        direction_state=EntryExitDirectionState.SHORT_ARMED,
    )


def _unknown_recon_input() -> DoublePlayEntryExitPolicyInputV0:
    return _policy_input(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        reconciliation_state=ReconciliationState.UNKNOWN,
    )


def test_producer_input_field_count_is_complete() -> None:
    names = tuple(item.name for item in fields(DoublePlayEntryExitPolicyInputV0))
    assert names == PRODUCER_INPUT_FIELD_KEYS
    assert len(PRODUCER_INPUT_FIELD_KEYS) == 25


def test_enter_input_capture_and_roundtrip() -> None:
    inp = _enter_input()
    result, binding = _capture_with_decorator(inp)
    assert result.decision_outcome is DecisionOutcome.ENTER_LONG
    evidence = _input_records(binding)[0]
    assert evidence["projection_status"] == TYPED_PROJECTION_STATUS
    assert evidence["capture_timing"] == CAPTURE_TIMING_BEFORE_PRODUCER_CALL
    reconstructed = reconstruct_typed_double_play_entry_exit_policy_input_v1(evidence)
    assert reconstructed == inp
    assert reconstructed is not inp


def test_exit_input_capture_preserves_signal_reason_code() -> None:
    inp = _exit_input()
    _result, binding = _capture_with_decorator(inp)
    evidence = _input_records(binding)[0]
    fields_payload = dict(evidence["producer_input_fields"])
    assert fields_payload["profit_protection_signal"]["triggered"] is True
    assert fields_payload["profit_protection_signal"]["reason_code"] == "profit_lock"
    reconstructed = reconstruct_typed_double_play_entry_exit_policy_input_v1(evidence)
    assert reconstructed.profit_protection_signal == inp.profit_protection_signal
    assert reconstructed == inp


def test_hold_and_no_action_inputs_are_distinct() -> None:
    hold = _hold_input()
    hold_evidence = _project(hold)
    no_action_inp = _policy_input(
        trading_gate=TradingGate.BLOCKED,
        safety_mode=SafetyMode.BLOCKED,
        input_complete=True,
    )
    no_action_evidence = _project(no_action_inp)
    hold_fields = dict(hold_evidence["producer_input_fields"])
    no_action_fields = dict(no_action_evidence["producer_input_fields"])
    assert hold_fields["position_state"] == "open_full"
    assert hold_fields["existing_position_side"] == "long"
    assert no_action_fields["trading_gate"] == "blocked"
    assert (
        hold_evidence["input_evidence_payload_hash"]
        != no_action_evidence["input_evidence_payload_hash"]
    )
    assert reconstruct_typed_double_play_entry_exit_policy_input_v1(hold_evidence) == hold


def test_reversal_and_risk_gate_signal_fields() -> None:
    reversal = _reversal_input()
    risk = _policy_input(
        position_state=PositionState.OPEN_FULL,
        existing_position_side=ExistingPositionSide.LONG,
        hard_risk_reduction_signal=PolicySignalV0(triggered=True, reason_code="hard_risk"),
        safety_exit_signal=PolicySignalV0(triggered=False, reason_code=""),
        trading_gate=TradingGate.EXIT_ONLY,
    )
    reversal_evidence = _project(reversal)
    risk_evidence = _project(risk)
    reversal_fields = dict(reversal_evidence["producer_input_fields"])
    risk_fields = dict(risk_evidence["producer_input_fields"])
    assert reversal_fields["existing_position_side"] == "long"
    assert reversal_fields["composition_result"]["selected_side"] == "short"
    assert risk_fields["hard_risk_reduction_signal"]["triggered"] is True
    assert risk_fields["hard_risk_reduction_signal"]["reason_code"] == "hard_risk"
    assert risk_fields["trading_gate"] == "exit_only"
    assert reconstruct_typed_double_play_entry_exit_policy_input_v1(reversal_evidence) == reversal
    assert reconstruct_typed_double_play_entry_exit_policy_input_v1(risk_evidence) == risk


def test_position_state_and_enum_semantics_preserved() -> None:
    inp = _policy_input(
        position_state=PositionState.REDUCING_PARTIAL,
        existing_position_side=ExistingPositionSide.SHORT,
        direction_state=EntryExitDirectionState.SHORT_ACTIVE,
    )
    evidence = _project(inp)
    payload = dict(evidence["producer_input_fields"])
    assert payload["position_state"] == "reducing_partial"
    assert payload["existing_position_side"] == "short"
    assert payload["direction_state"] == "short_active"
    reconstructed = reconstruct_typed_double_play_entry_exit_policy_input_v1(evidence)
    assert reconstructed.position_state is PositionState.REDUCING_PARTIAL
    assert reconstructed.direction_state is EntryExitDirectionState.SHORT_ACTIVE


def test_unknown_reconciliation_preserved_not_normalized() -> None:
    inp = _unknown_recon_input()
    evidence = _project(inp)
    payload = dict(evidence["producer_input_fields"])
    assert payload["reconciliation_state"] == "unknown"
    assert payload["reconciliation_state"] != UNKNOWN
    reconstructed = reconstruct_typed_double_play_entry_exit_policy_input_v1(evidence)
    assert reconstructed.reconciliation_state is ReconciliationState.UNKNOWN
    assert reconstructed == inp


def test_unavailable_projection_when_input_missing() -> None:
    evidence = project_double_play_entry_exit_policy_input_v1(
        None,
        record_id="ddo.dpi.unavail.0001",
        event_time_utc=EVENT_TIME,
        correlation_id=CORR_ID,
        cycle_id=None,
        decision_event_ref="ddo.dec.unavail.0001",
        typed_output_observation_ref=None,
        producer_call_policy_version=UNKNOWN,
        capture_timing="UNAVAILABLE",
    )
    assert evidence["projection_status"] == UNAVAILABLE_PROJECTION_STATUS
    assert evidence["producer_input_fields"] is None
    assert evidence["producer_input_digest"] is None
    assert evidence["producer_digest_canonical_payload"] is None
    assert evidence["cycle_id"] is None
    assert evidence["typed_output_observation_ref"] is None


def test_canonical_serialization_and_identical_input_hash() -> None:
    inp = _enter_input()
    first = _project(inp)
    second = _project(inp)
    assert first["content_hash"] == second["content_hash"]
    assert first["input_evidence_payload_hash"] == second["input_evidence_payload_hash"]
    assert first["producer_input_digest"] == second["producer_input_digest"]


def test_material_field_change_changes_hash() -> None:
    inp = _enter_input()
    changed = replace(inp, cooldown_pass=False)
    changed = replace(changed, input_digest=compute_entry_exit_policy_input_digest(changed))
    first = _project(inp)
    second = _project(changed)
    assert first["input_evidence_payload_hash"] != second["input_evidence_payload_hash"]
    assert first["producer_input_digest"] != second["producer_input_digest"]
    assert first["content_hash"] != second["content_hash"]


def test_producer_input_digest_relation_subset_not_equal_to_evidence_hash() -> None:
    inp = _enter_input()
    evidence = _project(inp)
    producer_digest = compute_entry_exit_policy_input_digest(inp)
    canonical = json.loads(serialize_entry_exit_policy_input_canonical(inp))
    reproduced = compute_producer_input_digest_from_canonical_payload_v1(canonical)
    assert evidence["producer_input_digest"] == producer_digest
    assert reproduced == producer_digest
    assert dict(evidence["producer_digest_canonical_payload"]) == canonical
    assert evidence["digest_relation"] == DIGEST_RELATION_SUBSET_SCOPE
    assert evidence["content_hash"] != producer_digest
    assert evidence["input_evidence_payload_hash"] != producer_digest
    digest_payload = dict(evidence["producer_digest_canonical_payload"])
    assert "reason_code" not in json.dumps(digest_payload)
    fields_payload = dict(evidence["producer_input_fields"])
    assert fields_payload["profit_protection_signal"]["reason_code"] == ""
    assert "composition_result" in fields_payload
    assert "composition_result" not in digest_payload


def test_reason_code_is_outside_existing_digest_scope() -> None:
    left = _policy_input(
        profit_protection_signal=PolicySignalV0(triggered=True, reason_code="alpha"),
    )
    right = _policy_input(
        profit_protection_signal=PolicySignalV0(triggered=True, reason_code="beta"),
    )
    assert compute_entry_exit_policy_input_digest(left) == compute_entry_exit_policy_input_digest(
        right
    )
    left_evidence = _project(left)
    right_evidence = _project(right)
    assert left_evidence["producer_input_digest"] == right_evidence["producer_input_digest"]
    assert (
        left_evidence["input_evidence_payload_hash"]
        != right_evidence["input_evidence_payload_hash"]
    )
    reconstructed_left = reconstruct_typed_double_play_entry_exit_policy_input_v1(left_evidence)
    reconstructed_right = reconstruct_typed_double_play_entry_exit_policy_input_v1(right_evidence)
    assert reconstructed_left.profit_protection_signal.reason_code == "alpha"
    assert reconstructed_right.profit_protection_signal.reason_code == "beta"


def test_roundtrip_does_not_call_producer_function() -> None:
    inp = _enter_input()
    evidence = _project(inp)
    reconstructed = reconstruct_typed_double_play_entry_exit_policy_input_v1(evidence)
    assert reconstructed == inp
    assert compute_entry_exit_policy_input_digest(reconstructed) == inp.input_digest


def test_no_hindsight_or_secret_keys() -> None:
    inp = _exit_input()
    evidence = _project(inp)
    blob = json.dumps(dict(evidence["producer_input_fields"]))
    for key in SECRET_KEYS | HINDSIGHT_KEYS:
        assert f'"{key}"' not in blob
    names = {item.name for item in fields(DoublePlayEntryExitPolicyInputV0)}
    assert names.isdisjoint(SECRET_KEYS)
    assert names.isdisjoint(HINDSIGHT_KEYS)


def test_hindsight_field_rejected() -> None:
    inp = _enter_input()
    evidence = dict(_project(inp))
    mutated = dict(evidence["producer_input_fields"])
    evidence.pop("content_hash", None)
    from src.learning.deterministic_decision_outcome_v0.double_play_input_evidence_v1 import (
        build_double_play_entry_exit_policy_input_evidence_v1,
    )
    from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
        canonical_json_dumps_v0,
        sha256_hex_v0,
    )

    nested = dict(mutated["composition_result"])
    nested["later_pnl"] = "1"
    mutated["composition_result"] = nested
    evidence["producer_input_fields"] = mutated
    evidence["input_evidence_payload_hash"] = sha256_hex_v0(canonical_json_dumps_v0(mutated))
    try:
        build_double_play_entry_exit_policy_input_evidence_v1(evidence)
    except DdoValidationError as exc:
        assert "HINDSIGHT_FIELD_FORBIDDEN" in str(exc)
    else:
        raise AssertionError("expected hindsight rejection")


def test_capture_failure_isolation_and_producer_object_unchanged() -> None:
    inp = _enter_input()
    policy = DoublePlayEntryExitPolicyV0()
    before_id = id(inp)
    without = evaluate_double_play_entry_exit_policy_v0(inp, policy)
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=None)
    bind_host_cycle_capture_context_v0(
        binding,
        event_ts_unix=EVENT_UNIX,
        session_id="dp-input-fail",
        cycle_index=1,
        repository_sha=UNKNOWN,
    )
    token = bind_capture_session_v0(binding)
    import src.learning.deterministic_decision_outcome_v0.capture_v0 as capture_mod

    original = capture_mod.observe_producer_result_v0

    def _boom(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("forced-input-evidence-failure")

    try:
        capture_mod.observe_producer_result_v0 = _boom  # type: ignore[method-assign]
        with_capture = evaluate_double_play_entry_exit_policy_v0(inp, policy)
    finally:
        capture_mod.observe_producer_result_v0 = original
        reset_capture_session_v0(token)
    assert with_capture == without
    assert id(inp) == before_id
    assert inp.direction_state is EntryExitDirectionState.LONG_ARMED
    assert binding.last_error is not None


def test_producer_exception_semantics_unchanged() -> None:
    policy = DoublePlayEntryExitPolicyV0()
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=None)
    bind_host_cycle_capture_context_v0(
        binding,
        event_ts_unix=EVENT_UNIX,
        session_id="dp-input-exc",
        cycle_index=1,
        repository_sha=UNKNOWN,
    )
    token = bind_capture_session_v0(binding)
    try:
        raised = False
        try:
            evaluate_double_play_entry_exit_policy_v0("not-an-input", policy)  # type: ignore[arg-type]
        except Exception:
            raised = True
        assert raised is True
    finally:
        reset_capture_session_v0(token)


def test_authority_markers_remain_none() -> None:
    evidence = _project(_enter_input())
    assert evidence["trading_authority"] == TRADING_AUTHORITY_NONE
    assert evidence["authority_owner"] == "NONE"
    assert evidence["runtime_effect"] == RUNTIME_EFFECT_OBSERVATION_ONLY
    contract = get_schema_contract_v0(
        SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE,
        SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_V1,
    )
    assert (
        contract["current_version"]
        == SCHEMA_VERSION_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE_V1
    )


def test_output_only_observe_does_not_invent_input_evidence() -> None:
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=None)
    result = evaluate_double_play_entry_exit_policy_v0(
        _enter_input(), DoublePlayEntryExitPolicyV0()
    )
    observe_producer_result_v0(
        binding,
        seam_id=SEAM_DOUBLE_PLAY_ENTRY_EXIT,
        result=result,
        event_time_utc=EVENT_TIME,
        correlation_id=CORR_ID,
        cycle_id=CYCLE_ID,
    )
    assert _input_records(binding) == []


def test_ledger_persists_input_evidence_when_args_present(tmp_path: Path) -> None:
    path = tmp_path / "ddo_ledger_v0.jsonl"
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=path)
    inp = _enter_input()
    policy = DoublePlayEntryExitPolicyV0()
    result = evaluate_double_play_entry_exit_policy_v0(inp, policy)
    summary = observe_producer_result_v0(
        binding,
        seam_id=SEAM_DOUBLE_PLAY_ENTRY_EXIT,
        result=result,
        args=(inp, policy),
        event_time_utc=EVENT_TIME,
        correlation_id=CORR_ID,
        cycle_id=CYCLE_ID,
    )
    assert summary["durable_ok"] is True
    loaded = AppendOnlyDdoLedgerV0(path).read_all()
    schemas = [row["schema_name"] for row in loaded]
    assert SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE in schemas
    assert "double_play_entry_exit_observation" in schemas
    input_rows = [
        row
        for row in loaded
        if row["schema_name"] == SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE
    ]
    assert input_rows[0]["projection_status"] == TYPED_PROJECTION_STATUS
    reconstructed = reconstruct_typed_double_play_entry_exit_policy_input_v1(input_rows[0])
    assert reconstructed == inp


def test_blocked_explicit_reasons_roundtrip() -> None:
    inp = _policy_input(
        explicit_blocked_reasons=(
            PolicyBlockedReason.EXPLICIT_BLOCKED,
            PolicyBlockedReason.INPUT_INCOMPLETE,
        )
    )
    evidence = _project(inp)
    reconstructed = reconstruct_typed_double_play_entry_exit_policy_input_v1(evidence)
    assert reconstructed.explicit_blocked_reasons == inp.explicit_blocked_reasons
    digest_payload = dict(evidence["producer_digest_canonical_payload"])
    assert digest_payload["explicit_blocked_reasons"] == sorted(
        item.value for item in inp.explicit_blocked_reasons
    )


def test_no_execution_or_a1_wal_imports() -> None:
    hits: list[str] = []
    for path in (
        PACKAGE_DIR / "capture_v0.py",
        PACKAGE_DIR / "double_play_input_evidence_v1.py",
        PACKAGE_DIR / "double_play_observation_projection_v1.py",
        PACKAGE_DIR / "ledger_v0.py",
    ):
        tree = ast.parse(path.read_text(encoding="utf-8"))
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
                    hits.append(f"{path.name}:{name}")
                lowered = name.lower()
                if "mutation_critical_control_state" in lowered or "a1_wal" in lowered:
                    hits.append(f"{path.name}:{name}")
    assert hits == []
