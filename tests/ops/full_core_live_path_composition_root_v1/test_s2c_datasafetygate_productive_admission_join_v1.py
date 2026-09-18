"""S2C: DataSafetyGate join as Full-Core execution-admission conjunct.

Proves DataSafetyGate.check is a fail-closed conjunct of
evaluate_execution_admission_v1. Gate ALLOW is not admission.
Unbound/DENY/ERROR/missing deny. No ensure_allowed. No second owner.

AUTHORITY_EFFECT=NONE
DATASAFETYGATE_JOIN=CONJUNCT_NOT_OWNER
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
from pathlib import Path
from unittest.mock import patch

from src.data.safety import (
    DataSafetyContext,
    DataSafetyGate,
    DataSafetyResult,
    DataSourceKind,
    DataUsageContextKind,
)
from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    join_capital_admission_into_admission_inputs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    OWNER,
    OWNER_ONE_SHOT_PERMIT_TOKEN,
)
from src.ops.full_core_live_path_composition_root_v1.datasafety_context_bind_from_fresh_pretrade_get_transport_result_v1 import (
    DISPOSITION_BOUND,
    bind_full_core_datasafety_context_from_fresh_pretrade_get_transport_result_v1,
)
from src.ops.full_core_live_path_composition_root_v1.datasafety_gate_join_into_execution_admission_v1 import (
    DATASAFETYGATE_JOIN_CLASS,
    JOIN_SEAM_ID,
    aggregate_datasafety_admission_status_v1,
    evaluate_datasafety_admission_for_transport_result_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CapitalAdmissionStatusV1,
    DataSafetyAdmissionStatusV1,
    DurableKillSwitchEvidenceStatusV1,
    ExecutionAdmissionInputsV1,
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
    OwnerOneShotPermitStatusV1,
    PRETRADE_SOURCE_FRESH_GET,
    PretradeFreshnessStatusV1,
    evaluate_execution_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    METHOD_GET,
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
    FreshPretradeGetItemEvidenceV1,
    FreshPretradeGetTransportResultV1,
    FreshPretradeRuntimeGetEvidenceV1,
    collect_fresh_pretrade_runtime_get_v1,
    join_fresh_pretrade_runtime_get_into_admission_inputs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import gap_node_v1
from tests.ops.test_full_core_execution_admission_contract_v1 import _live_inputs
from tests.ops.test_full_core_live_enabled_standing_admission_seam_v1 import (
    _all_modelable_live_gates_true,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_COMPOSITION_ROOT = REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1"
_JOIN_RELPATH = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "datasafety_gate_join_into_execution_admission_v1.py"
)
_BIND_RELPATH = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "datasafety_context_bind_from_fresh_pretrade_get_transport_result_v1.py"
)
_SRC_TRANSPORT = _COMPOSITION_ROOT / "productive_read_only_get_transport_v1.py"
_SRC_FRESH = _COMPOSITION_ROOT / "fresh_pretrade_runtime_get_v1.py"
_SRC_BIND = (
    _COMPOSITION_ROOT / "datasafety_context_bind_from_fresh_pretrade_get_transport_result_v1.py"
)
_SRC_JOIN = _COMPOSITION_ROOT / "datasafety_gate_join_into_execution_admission_v1.py"
_SRC_LIVE_ACCOUNT = _COMPOSITION_ROOT / "live_account_bound_v1.py"
_SRC_CAPITAL = _COMPOSITION_ROOT / "capital_admission_v1.py"
_V5_SRC = (
    REPO_ROOT
    / "src/ops/governed_productive_account_equity_authority_producer_v1"
    / "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5.py"
)
_TRUSTED_PAYLOAD = {
    "code": "0",
    "data": [{"instId": "BTC-USDT-SWAP", "uid": "1", "tdMode": "cross", "mgnMode": "cross"}],
}


def _carrier(*, data_safety_source_kind: str | None) -> FreshPretradeGetTransportResultV1:
    return FreshPretradeGetTransportResultV1(
        get_performed=True,
        method=METHOD_GET,
        endpoint="/api/v5/public/instruments",
        http_status=200,
        payload=dict(_TRUSTED_PAYLOAD),
        auth_header_sent=False,
        transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
        venue_live_contact=True,
        historical_reuse=False,
        error_class="",
        data_safety_source_kind=data_safety_source_kind,
    )


class _RealStampedTransport:
    """Test double that carries the S1 REAL stamp. Not a productive REAL producer."""

    def get(self, *, endpoint: str, auth_required: bool, pretrade_decision_id: str):
        del pretrade_decision_id
        return FreshPretradeGetTransportResultV1(
            get_performed=True,
            method=METHOD_GET,
            endpoint=endpoint,
            http_status=200,
            payload=dict(_TRUSTED_PAYLOAD),
            auth_header_sent=bool(auth_required),
            transport_class=TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
            venue_live_contact=True,
            historical_reuse=False,
            error_class="",
            data_safety_source_kind=DataSourceKind.REAL.value,
        )


class _UnboundTransport:
    def get(self, *, endpoint: str, auth_required: bool, pretrade_decision_id: str):
        del pretrade_decision_id
        return FreshPretradeGetTransportResultV1(
            get_performed=True,
            method=METHOD_GET,
            endpoint=endpoint,
            http_status=200,
            payload=dict(_TRUSTED_PAYLOAD),
            auth_header_sent=bool(auth_required),
            transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
            venue_live_contact=False,
            historical_reuse=False,
            error_class="",
            data_safety_source_kind=None,
        )


def _complete_live_inputs(**overrides) -> ExecutionAdmissionInputsV1:
    payload = {
        "live_enabled": True,
        "live_armed": True,
        "wire_send_permitted": True,
        "pretrade_source_kind": PRETRADE_SOURCE_FRESH_GET,
        "pretrade_freshness_status": PretradeFreshnessStatusV1.LIVE_FRESH.value,
        "capital_risk_mode": CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
        "durable_kill_switch_evidence_status": (
            DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
        ),
        "durable_kill_switch_blocked": False,
        "fresh_pretrade_get_status": FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        "live_account_bound_status": LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
        "capital_admission_status": CapitalAdmissionStatusV1.TRUSTED_PRESENT.value,
        "capital_authority_class": CAPITAL_AUTHORITY_RISK_ADMISSIBLE,
        "step_29p_risk_admissible": True,
        "data_safety_admission_status": DataSafetyAdmissionStatusV1.SATISFIED.value,
    }
    payload.update(overrides)
    return _live_inputs(**payload)


def _precomputed_get_evidence(**overrides) -> FreshPretradeRuntimeGetEvidenceV1:
    payload = {
        "evidence_status": FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        "pretrade_source_kind": PRETRADE_SOURCE_FRESH_GET,
        "pretrade_freshness_status": PretradeFreshnessStatusV1.LIVE_FRESH.value,
        "pretrade_decision_id": "decision-1",
        "items": (),
        "reason_codes": (),
        "get_performed": True,
        "venue_live_contact": True,
        "live_enabled": True,
        "live_armed": True,
        "wire_send_permitted": True,
        "post_attempted": False,
    }
    payload.update(overrides)
    return FreshPretradeRuntimeGetEvidenceV1(**payload)


def test_new_status_vocabulary_is_dedicated_not_overloaded() -> None:
    assert {member.name for member in DataSafetyAdmissionStatusV1} == {
        "SATISFIED",
        "UNBOUND",
        "DENIED",
        "ERROR",
        "MISSING",
    }
    assert (
        DataSafetyAdmissionStatusV1.SATISFIED.value
        != FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    )
    assert "data_safety_admission_status" in {
        field.name for field in dataclasses.fields(ExecutionAdmissionInputsV1)
    }
    assert "data_safety_admission_status" in {
        field.name for field in dataclasses.fields(FreshPretradeRuntimeGetEvidenceV1)
    }
    omitted = ExecutionAdmissionInputsV1(
        plan_identity="p",
        venue_plan_identity="v",
        instrument_identity_ok=True,
        pretrade_admissible=True,
        pretrade_source_kind=PRETRADE_SOURCE_FRESH_GET,
        pretrade_freshness_status=PretradeFreshnessStatusV1.LIVE_FRESH.value,
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
        durable_kill_switch_evidence_status=DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value,
        durable_kill_switch_blocked=False,
        live_enabled=True,
        live_armed=True,
        wire_send_permitted=True,
        owner_authorization_present=True,
        owner_one_shot_permit_status=OwnerOneShotPermitStatusV1.TRUSTED_PRESENT.value,
        admission_context=ADMISSION_CONTEXT_LIVE,
    )
    assert omitted.data_safety_admission_status == DataSafetyAdmissionStatusV1.MISSING.value
    node = gap_node_v1("DATASAFETY_ADMISSION_JOIN")
    assert node.consumer == "evaluate_execution_admission_v1"
    assert node.implementation_status == "JOINED_TYPED_EVIDENCE_FAIL_CLOSED"
    assert DATASAFETYGATE_JOIN_CLASS == "CONJUNCT_NOT_OWNER"
    assert JOIN_SEAM_ID.endswith("_V1")
    assert OWNER == "ops.full_core_live_path_composition_root_v1"


def test_allow_is_not_admission_authority() -> None:
    decision = evaluate_execution_admission_v1(
        _live_inputs(data_safety_admission_status=DataSafetyAdmissionStatusV1.SATISFIED.value)
    )
    assert decision.admitted is False
    assert "DATA_SAFETY_ADMISSION_MISSING" not in decision.reason_codes
    assert "DATA_SAFETY_ADMISSION_UNBOUND" not in decision.reason_codes
    complete = evaluate_execution_admission_v1(_complete_live_inputs())
    assert complete.admitted is True
    assert complete.reason_codes == ()


def test_unbound_none_denies_and_does_not_call_gate() -> None:
    calls: list[object] = []

    def _wrapped_check(context: DataSafetyContext) -> DataSafetyResult:
        calls.append(context)
        return DataSafetyGate.check(context)

    unbound = _carrier(data_safety_source_kind=None)
    with patch(
        "src.ops.full_core_live_path_composition_root_v1"
        ".datasafety_gate_join_into_execution_admission_v1.DataSafetyGate.check",
        side_effect=_wrapped_check,
    ):
        status = evaluate_datasafety_admission_for_transport_result_v1(unbound)
    assert status == DataSafetyAdmissionStatusV1.UNBOUND.value
    assert calls == []
    decision = evaluate_execution_admission_v1(
        _complete_live_inputs(
            data_safety_admission_status=DataSafetyAdmissionStatusV1.UNBOUND.value
        )
    )
    assert decision.admitted is False
    assert "DATA_SAFETY_ADMISSION_UNBOUND" in decision.reason_codes


def test_gate_denied_is_fail_closed_conjunct() -> None:
    bound = _carrier(data_safety_source_kind=DataSourceKind.REAL.value)
    bind_result = bind_full_core_datasafety_context_from_fresh_pretrade_get_transport_result_v1(
        bound
    )
    assert bind_result.disposition == DISPOSITION_BOUND
    with patch(
        "src.ops.full_core_live_path_composition_root_v1"
        ".datasafety_gate_join_into_execution_admission_v1.DataSafetyGate.check",
        return_value=DataSafetyResult(allowed=False, reason="forced-deny"),
    ):
        status = evaluate_datasafety_admission_for_transport_result_v1(bound)
    assert status == DataSafetyAdmissionStatusV1.DENIED.value
    decision = evaluate_execution_admission_v1(
        _complete_live_inputs(data_safety_admission_status=DataSafetyAdmissionStatusV1.DENIED.value)
    )
    assert decision.admitted is False
    assert "DATA_SAFETY_ADMISSION_DENIED" in decision.reason_codes


def test_check_exception_is_typed_error_not_escaped() -> None:
    bound = _carrier(data_safety_source_kind=DataSourceKind.REAL.value)
    with patch(
        "src.ops.full_core_live_path_composition_root_v1"
        ".datasafety_gate_join_into_execution_admission_v1.DataSafetyGate.check",
        side_effect=RuntimeError("gate-boom"),
    ):
        status = evaluate_datasafety_admission_for_transport_result_v1(bound)
    assert status == DataSafetyAdmissionStatusV1.ERROR.value
    decision = evaluate_execution_admission_v1(
        _complete_live_inputs(data_safety_admission_status=DataSafetyAdmissionStatusV1.ERROR.value)
    )
    assert decision.admitted is False
    assert "DATA_SAFETY_ADMISSION_ERROR" in decision.reason_codes


def test_missing_default_denies() -> None:
    decision = evaluate_execution_admission_v1(_complete_live_inputs())
    assert decision.admitted is True
    missing = evaluate_execution_admission_v1(
        _complete_live_inputs(
            data_safety_admission_status=DataSafetyAdmissionStatusV1.MISSING.value
        )
    )
    assert missing.admitted is False
    assert "DATA_SAFETY_ADMISSION_MISSING" in missing.reason_codes
    defaulted = evaluate_execution_admission_v1(
        _all_modelable_live_gates_true(step_29p_risk_admissible=True)
    )
    assert defaulted.admitted is False
    assert "DATA_SAFETY_ADMISSION_MISSING" in defaulted.reason_codes


def test_prebuilt_admission_inputs_cannot_bypass() -> None:
    bypass = _complete_live_inputs()
    rebuilt = ExecutionAdmissionInputsV1(
        plan_identity=bypass.plan_identity,
        venue_plan_identity=bypass.venue_plan_identity,
        instrument_identity_ok=bypass.instrument_identity_ok,
        pretrade_admissible=bypass.pretrade_admissible,
        pretrade_source_kind=bypass.pretrade_source_kind,
        pretrade_freshness_status=bypass.pretrade_freshness_status,
        capital_risk_mode=bypass.capital_risk_mode,
        durable_kill_switch_evidence_status=bypass.durable_kill_switch_evidence_status,
        durable_kill_switch_blocked=bypass.durable_kill_switch_blocked,
        live_enabled=bypass.live_enabled,
        live_armed=bypass.live_armed,
        wire_send_permitted=bypass.wire_send_permitted,
        owner_authorization_present=bypass.owner_authorization_present,
        owner_one_shot_permit_status=bypass.owner_one_shot_permit_status,
        admission_context=bypass.admission_context,
        fresh_pretrade_get_status=bypass.fresh_pretrade_get_status,
        live_account_bound_status=bypass.live_account_bound_status,
        capital_admission_status=bypass.capital_admission_status,
        capital_authority_class=bypass.capital_authority_class,
        step_29p_risk_admissible=bypass.step_29p_risk_admissible,
    )
    assert rebuilt.data_safety_admission_status == DataSafetyAdmissionStatusV1.MISSING.value
    decision = evaluate_execution_admission_v1(rebuilt)
    assert decision.admitted is False
    assert "DATA_SAFETY_ADMISSION_MISSING" in decision.reason_codes


def test_precomputed_get_evidence_cannot_bypass() -> None:
    evidence = _precomputed_get_evidence()
    assert evidence.data_safety_admission_status == DataSafetyAdmissionStatusV1.MISSING.value
    inputs = join_fresh_pretrade_runtime_get_into_admission_inputs_v1(
        plan_identity="plan-1",
        venue_plan_identity="venue-1",
        instrument_identity_ok=True,
        pretrade_admissible=True,
        pretrade_source_kind=PRETRADE_SOURCE_FRESH_GET,
        pretrade_freshness_status=PretradeFreshnessStatusV1.LIVE_FRESH.value,
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
        owner_go=OWNER_ONE_SHOT_PERMIT_TOKEN,
        admission_context=ADMISSION_CONTEXT_LIVE,
        precomputed_evidence=evidence,
    )
    assert inputs.data_safety_admission_status == DataSafetyAdmissionStatusV1.MISSING.value
    decision = evaluate_execution_admission_v1(
        _complete_live_inputs(
            data_safety_admission_status=inputs.data_safety_admission_status,
        )
    )
    assert decision.admitted is False
    assert "DATA_SAFETY_ADMISSION_MISSING" in decision.reason_codes


def test_collect_real_stamped_aggregate_is_satisfied_unbound_injected_is_not() -> None:
    satisfied = collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id="s2c-real",
        instrument_id="BTC-USDT-SWAP",
        td_mode="cross",
        transport=_RealStampedTransport(),
        require_collection=True,
    )
    assert satisfied.data_safety_admission_status == DataSafetyAdmissionStatusV1.SATISFIED.value
    unbound = collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id="s2c-unbound",
        instrument_id="BTC-USDT-SWAP",
        td_mode="cross",
        transport=_UnboundTransport(),
        require_collection=True,
    )
    assert unbound.data_safety_admission_status == DataSafetyAdmissionStatusV1.UNBOUND.value
    assert aggregate_datasafety_admission_status_v1(()) == DataSafetyAdmissionStatusV1.MISSING.value
    mixed = aggregate_datasafety_admission_status_v1(
        (
            DataSafetyAdmissionStatusV1.SATISFIED.value,
            DataSafetyAdmissionStatusV1.UNBOUND.value,
        )
    )
    assert mixed == DataSafetyAdmissionStatusV1.UNBOUND.value


def test_aggregate_survives_later_input_reconstructions() -> None:
    evidence = collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id="s2c-recon",
        instrument_id="BTC-USDT-SWAP",
        td_mode="cross",
        transport=_RealStampedTransport(),
        require_collection=True,
    )
    assert evidence.data_safety_admission_status == DataSafetyAdmissionStatusV1.SATISFIED.value
    fresh_inputs = join_fresh_pretrade_runtime_get_into_admission_inputs_v1(
        plan_identity="plan-1",
        venue_plan_identity="venue-1",
        instrument_identity_ok=True,
        pretrade_admissible=True,
        pretrade_source_kind=PRETRADE_SOURCE_FRESH_GET,
        pretrade_freshness_status=PretradeFreshnessStatusV1.LIVE_FRESH.value,
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
        owner_go=OWNER_ONE_SHOT_PERMIT_TOKEN,
        admission_context=ADMISSION_CONTEXT_LIVE,
        precomputed_evidence=evidence,
    )
    assert fresh_inputs.data_safety_admission_status == DataSafetyAdmissionStatusV1.SATISFIED.value
    capital_inputs = join_capital_admission_into_admission_inputs_v1(
        plan_identity="plan-1",
        venue_plan_identity="venue-1",
        instrument_identity_ok=True,
        pretrade_admissible=True,
        pretrade_source_kind=PRETRADE_SOURCE_FRESH_GET,
        pretrade_freshness_status=PretradeFreshnessStatusV1.LIVE_FRESH.value,
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
        owner_go=OWNER_ONE_SHOT_PERMIT_TOKEN,
        admission_context=ADMISSION_CONTEXT_LIVE,
        transport=_RealStampedTransport(),
        pretrade_decision_id="s2c-recon-cap",
        instrument_id="BTC-USDT-SWAP",
        td_mode="cross",
    )
    assert (
        capital_inputs.data_safety_admission_status == DataSafetyAdmissionStatusV1.SATISFIED.value
    )
    live_src = _SRC_LIVE_ACCOUNT.read_text(encoding="utf-8")
    capital_src = _SRC_CAPITAL.read_text(encoding="utf-8")
    assert "data_safety_admission_status=inputs.data_safety_admission_status" in live_src
    assert "data_safety_admission_status=inputs.data_safety_admission_status" in capital_src


def test_no_ensure_allowed_on_full_core_path() -> None:
    for path in sorted(_COMPOSITION_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "ensure_allowed":
                raise AssertionError(f"ensure_allowed present in {path}")
            if isinstance(node, ast.Name) and node.id == "ensure_allowed":
                raise AssertionError(f"ensure_allowed name present in {path}")
    join_src = _SRC_JOIN.read_text(encoding="utf-8")
    assert "DataSafetyGate.check" in join_src
    assert "DataSafetyGate.ensure_allowed" not in join_src
    assert ".ensure_allowed(" not in join_src


def test_s1_and_s2b_semantics_unchanged() -> None:
    transport_src = _SRC_TRANSPORT.read_text(encoding="utf-8")
    fresh_src = _SRC_FRESH.read_text(encoding="utf-8")
    bind_src = _SRC_BIND.read_text(encoding="utf-8")
    assert transport_src.count("DataSourceKind.REAL.value") == 1
    assert "DataSourceKind.REAL.value if get_performed and venue_live_contact" in transport_src
    assert "VENUE_NATIVE_" not in transport_src
    assert "DataSourceKind.REAL" not in fresh_src
    assert "DataUsageContextKind.LIVE_TRADE" in bind_src
    assert "datasafetygate_join: bool = False" in bind_src
    assert "DataSafetyGate" not in bind_src
    authorized_bind = (REPO_ROOT / _BIND_RELPATH).resolve()
    authorized_join = (REPO_ROOT / _JOIN_RELPATH).resolve()
    for path in sorted(_COMPOSITION_ROOT.rglob("*.py")):
        if path.resolve() in {authorized_bind, authorized_join}:
            continue
        text = path.read_text(encoding="utf-8")
        assert "DataUsageContextKind.LIVE_TRADE" not in text
        assert "usage_context=DataUsageContextKind.LIVE_TRADE" not in text


def test_a1_a2_a3_remain_stamp_lossy() -> None:
    evidence = collect_fresh_pretrade_runtime_get_v1(
        pretrade_decision_id="s2c-a1",
        instrument_id="BTC-USDT-SWAP",
        td_mode="cross",
        transport=_RealStampedTransport(),
        require_collection=True,
    )
    assert evidence.items
    for item in evidence.items:
        assert "data_safety_source_kind" not in {f.name for f in dataclasses.fields(type(item))}
        assert getattr(item, "data_safety_source_kind", None) is None
    assert "data_safety_source_kind" not in {
        f.name for f in dataclasses.fields(FreshPretradeGetItemEvidenceV1)
    }
    v5_src = _V5_SRC.read_text(encoding="utf-8")
    assert 'return result.payload, ""' in v5_src or "return result.payload, ''" in v5_src
    transport_src = _SRC_TRANSPORT.read_text(encoding="utf-8")
    assert "self.payloads_by_path[path_only] = payload" in transport_src
    fresh_src = _SRC_FRESH.read_text(encoding="utf-8")
    ctor_idx = fresh_src.index("FreshPretradeGetItemEvidenceV1(")
    ctor_window = fresh_src[ctor_idx : ctor_idx + 900]
    assert "data_safety_source_kind" not in ctor_window


def test_existing_admission_owner_and_other_conjuncts_retain_authority() -> None:
    sig = inspect.signature(evaluate_execution_admission_v1)
    assert list(sig.parameters) == ["inputs"]
    ds_only = evaluate_execution_admission_v1(
        _live_inputs(data_safety_admission_status=DataSafetyAdmissionStatusV1.SATISFIED.value)
    )
    assert ds_only.admitted is False
    assert ds_only.fail_closed is True
    other = evaluate_execution_admission_v1(_complete_live_inputs(live_enabled=False))
    assert other.admitted is False
    assert "LIVE_ENABLED_FALSE" in other.reason_codes
    assert "DATA_SAFETY_ADMISSION_MISSING" not in other.reason_codes
    assert evaluate_execution_admission_v1.__doc__ is not None
    assert "Never a second execution owner" in evaluate_execution_admission_v1.__doc__
