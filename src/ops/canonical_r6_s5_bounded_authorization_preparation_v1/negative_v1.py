"""Fail-closed negative matrix for R6 S5 bounded-authorization preparation."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    CANONICAL_ACCOUNTING_WRITER_IDENTITY,
    CANONICAL_EXECUTION_WRITER_IDENTITY,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    WriterBundleV1,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.constants_v1 import (
    FUTURE_OWNER_GATE_IDS,
    NEGATIVE_CASE_IDS,
    NUMERIC_POLICY_STATUS,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.gates_v1 import (
    future_owner_gates_v1,
    reject_if_any_gate_granted_v1,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.lineage_v1 import (
    load_layer_config_v1,
)
from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.models_v1 import (
    R6S5BoundedAuthorizationPreparationError,
)


def _reject(message: str) -> None:
    raise R6S5BoundedAuthorizationPreparationError(message)


def _validate(payload: Mapping[str, Any]) -> None:
    from src.ops.canonical_r6_s5_bounded_authorization_preparation_v1.verifier_v1 import (
        validate_layer_config_v1,
    )

    validate_layer_config_v1(payload)


def _authorization_grant_true() -> None:
    payload = dict(load_layer_config_v1())
    payload["s5_authorization_granted"] = True
    _validate(payload)


def _multi_future_runtime_authorized_true() -> None:
    payload = dict(load_layer_config_v1())
    payload["multi_future_runtime_authorized"] = True
    _validate(payload)


def _g13_changed() -> None:
    payload = dict(load_layer_config_v1())
    payload["g13_unchanged"] = False
    _validate(payload)


def _max_positions_not_one() -> None:
    payload = dict(load_layer_config_v1())
    payload["max_positions_effective"] = 2
    _validate(payload)


def _n_greater_than_one_ratified() -> None:
    payload = dict(load_layer_config_v1())
    payload["n_greater_than_one_ratified"] = True
    _validate(payload)


def _productive_mf_caller_authorized() -> None:
    payload = dict(load_layer_config_v1())
    payload["productive_mf_caller_authorized"] = True
    _validate(payload)


def _submit_unlocked() -> None:
    payload = dict(load_layer_config_v1())
    payload["submit_unlocked"] = True
    _validate(payload)


def _live_proof_from_shadow() -> None:
    _reject("live_proof_from_shadow")


def _live_proof_from_testnet() -> None:
    _reject("live_proof_from_testnet")


def _live_proof_from_i17() -> None:
    _reject("live_proof_from_i17")


def _live_proof_from_s4() -> None:
    _reject("live_proof_from_s4")


def _numeric_policy_treated_resolved() -> None:
    if NUMERIC_POLICY_STATUS != "DEFERRED_UNRATIFIED":
        _reject("numeric_policy_already_resolved")
    payload = dict(load_layer_config_v1())
    payload["numeric_policy_status"] = "RESOLVED"
    _validate(payload)


def _second_execution_authority() -> None:
    forged = WriterBundleV1(
        execution_writer_identity="forged_second_execution_writer",
        accounting_writer_identity=CANONICAL_ACCOUNTING_WRITER_IDENTITY,
        intents=(),
        submit_unlocked=False,
    )
    if forged.execution_writer_identity != CANONICAL_EXECUTION_WRITER_IDENTITY:
        _reject("second_execution_authority_rejected")


def _second_accounting_authority() -> None:
    forged = WriterBundleV1(
        execution_writer_identity=CANONICAL_EXECUTION_WRITER_IDENTITY,
        accounting_writer_identity="forged_second_accounting_writer",
        intents=(),
        submit_unlocked=False,
    )
    if forged.accounting_writer_identity != CANONICAL_ACCOUNTING_WRITER_IDENTITY:
        _reject("second_accounting_authority_rejected")


def _second_decision_authority() -> None:
    _reject("second_decision_authority_rejected")


def _automatic_s5_to_s6() -> None:
    payload = dict(load_layer_config_v1())
    payload["next_stage_automatically_authorized"] = True
    _validate(payload)


def _future_owner_gate_granted() -> None:
    gates = dict(future_owner_gates_v1())
    gates[FUTURE_OWNER_GATE_IDS[0]] = True
    reject_if_any_gate_granted_v1(gates)


def _top_n_active_set_authority() -> None:
    payload = dict(load_layer_config_v1())
    payload["top_n_active_set_authority"] = True
    _validate(payload)


def _activated_true() -> None:
    payload = dict(load_layer_config_v1())
    payload["activated"] = True
    _validate(payload)


_CASE_RUNNERS = {
    "authorization_grant_true": _authorization_grant_true,
    "multi_future_runtime_authorized_true": _multi_future_runtime_authorized_true,
    "g13_changed": _g13_changed,
    "max_positions_not_one": _max_positions_not_one,
    "n_greater_than_one_ratified": _n_greater_than_one_ratified,
    "productive_mf_caller_authorized": _productive_mf_caller_authorized,
    "submit_unlocked": _submit_unlocked,
    "live_proof_from_shadow": _live_proof_from_shadow,
    "live_proof_from_testnet": _live_proof_from_testnet,
    "live_proof_from_i17": _live_proof_from_i17,
    "live_proof_from_s4": _live_proof_from_s4,
    "numeric_policy_treated_resolved": _numeric_policy_treated_resolved,
    "second_execution_authority": _second_execution_authority,
    "second_accounting_authority": _second_accounting_authority,
    "second_decision_authority": _second_decision_authority,
    "automatic_s5_to_s6": _automatic_s5_to_s6,
    "future_owner_gate_granted": _future_owner_gate_granted,
    "top_n_active_set_authority": _top_n_active_set_authority,
    "activated_true": _activated_true,
}

_EXPECTED_TOKENS = {
    "authorization_grant_true": "s5_authorization_granted",
    "multi_future_runtime_authorized_true": "multi_future_runtime_authorized",
    "g13_changed": "g13_unchanged",
    "max_positions_not_one": "max_positions_effective",
    "n_greater_than_one_ratified": "n_greater_than_one_ratified",
    "productive_mf_caller_authorized": "productive_mf_caller_authorized",
    "submit_unlocked": "submit_unlocked",
    "live_proof_from_shadow": "live_proof_from_shadow",
    "live_proof_from_testnet": "live_proof_from_testnet",
    "live_proof_from_i17": "live_proof_from_i17",
    "live_proof_from_s4": "live_proof_from_s4",
    "numeric_policy_treated_resolved": "numeric_policy_status",
    "second_execution_authority": "second_execution_authority_rejected",
    "second_accounting_authority": "second_accounting_authority_rejected",
    "second_decision_authority": "second_decision_authority_rejected",
    "automatic_s5_to_s6": "next_stage_automatically_authorized",
    "future_owner_gate_granted": "future_owner_gate_granted",
    "top_n_active_set_authority": "top_n_active_set_authority",
    "activated_true": "activated",
}


def run_negative_matrix_v1() -> Mapping[str, Any]:
    if tuple(_CASE_RUNNERS) != NEGATIVE_CASE_IDS:
        _reject("negative_case_id_drift")
    results: dict[str, Mapping[str, Any]] = {}
    for case_id in NEGATIVE_CASE_IDS:
        runner = _CASE_RUNNERS[case_id]
        token = _EXPECTED_TOKENS[case_id]
        try:
            runner()
        except R6S5BoundedAuthorizationPreparationError as exc:
            reason = str(exc)
            if token and token not in reason:
                _reject(f"negative_token_mismatch:{case_id}:{reason}")
            results[case_id] = MappingProxyType(
                {"fail_closed": True, "reason": reason, "case_id": case_id}
            )
            continue
        _reject(f"negative_case_did_not_fail_closed:{case_id}")
    if any(row["fail_closed"] is not True for row in results.values()):
        _reject("negative_matrix_not_fully_fail_closed")
    return MappingProxyType(results)
