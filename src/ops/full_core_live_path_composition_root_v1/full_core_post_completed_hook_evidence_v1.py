"""Post-COMPLETED hook evidence — durable cycle-ledger supplement (observational only).

Cycle Host COMPLETED means PRE_EXTERNAL_EFFECT or valid HOLD terminal — not post-submit
reconciliation success. Atomic One-Shot remains authoritative for submission attempts.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

CONTRACT_ID = "FULL_CORE_POST_COMPLETED_HOOK_EVIDENCE_V1"
RECOVERY_OBSERVATION_CONTRACT_ID = "FULL_CORE_S5_RECOVERY_OBSERVATION_V1"
POST_COMPLETED_HOOK_EVIDENCE_LEDGER_PHASE = "POST_COMPLETED_HOOK_EVIDENCE_V1"

LIFECYCLE_OBSERVATION_NOT_INVOKED = "NOT_INVOKED"
LIFECYCLE_OBSERVATION_DISABLED_IN_CONTEXT = "DISABLED_IN_CONTEXT"
LIFECYCLE_OBSERVATION_INCOMPLETE = "OBSERVATION_INCOMPLETE"

POST_SUBMIT_RECONCILIATION_SUCCEEDED = "POST_SUBMIT_RECONCILIATION_SUCCEEDED"
POST_SUBMIT_RECONCILIATION_SUCCEEDED_VALUE = "false"
POST_SUBMIT_RECONCILIATION_UNPROVEN_VALUE = "unproven"

POST_COMPLETED_HOOK_EVIDENCE_STATUS = "POST_COMPLETED_HOOK_EVIDENCE_STATUS"
POST_COMPLETED_HOOK_EVIDENCE_STATUS_PENDING = "PENDING"
POST_COMPLETED_HOOK_EVIDENCE_STATUS_RECORDED = "RECORDED"

RECONCILIATION_OBSERVATION_NOT_APPLICABLE = "NOT_APPLICABLE"
RECONCILIATION_OBSERVATION_INCOMPLETE = "OBSERVATION_INCOMPLETE"
RECONCILIATION_SUCCESS_NOT_CLAIMED = "RECONCILIATION_SUCCESS_NOT_CLAIMED"
LIFECYCLE_FAIL_CLOSED_NOT_RECONCILIATION_SUCCESS = "LIFECYCLE_FAIL_CLOSED"

CYCLE_LEDGER_SUPPLEMENT_PERSISTENCE = "CYCLE_LEDGER_SUPPLEMENT_PERSISTENCE"
CYCLE_LEDGER_SUPPLEMENT_PERSISTENCE_PASS = "PASS"
CYCLE_LEDGER_SUPPLEMENT_PERSISTENCE_FAIL_CLOSED = "FAIL_CLOSED"
CYCLE_LEDGER_SUPPLEMENT_PERSISTENCE_ERROR = "CYCLE_LEDGER_SUPPLEMENT_PERSISTENCE_ERROR"

ALLOWLISTED_LIFECYCLE_CYCLE_CLAIM_KEYS: tuple[str, ...] = (
    "FULL_CORE_CYCLE_LIFECYCLE_WIRING",
    "FULL_CORE_CYCLE_LIFECYCLE_WIRING_MODE",
    "FULL_CORE_CYCLE_LIFECYCLE_WIRING_SKIP",
    "FULL_CORE_CYCLE_LIFECYCLE_WIRING_REASON",
    "FULL_CORE_CYCLE_LIFECYCLE_WIRING_UNEXPECTED",
    "FULL_CORE_CYCLE_LIFECYCLE_WIRING_EXCEPTION_TYPE",
    "FULL_CORE_CYCLE_LIFECYCLE_WIRING_EXCEPTION_MESSAGE",
    "FULL_CORE_CYCLE_LIFECYCLE_GHV_FORWARD",
    "FULL_CORE_CYCLE_LIFECYCLE_GHV_REVERSE",
    "FULL_CORE_CYCLE_LIFECYCLE_RECON_OUTCOME",
    POST_COMPLETED_HOOK_EVIDENCE_LEDGER_PHASE,
    POST_COMPLETED_HOOK_EVIDENCE_STATUS,
    POST_SUBMIT_RECONCILIATION_SUCCEEDED,
    CYCLE_LEDGER_SUPPLEMENT_PERSISTENCE,
    CYCLE_LEDGER_SUPPLEMENT_PERSISTENCE_ERROR,
)

FULL_CORE_ATOMIC_CONSUMPTION_KEY = "FULL_CORE_ATOMIC_CONSUMPTION_KEY"

ALLOWLISTED_CAPITAL_GUARD_CYCLE_CLAIM_KEYS: tuple[str, ...] = (
    "FULL_CORE_CAPITAL_GUARD_JOIN_MODE",
    "FULL_CORE_CAPITAL_GUARD_BLOCKED",
    "FULL_CORE_CAPITAL_GUARD_POST_COUNT",
    "FULL_CORE_CAPITAL_GUARD_BINDING_DIGEST",
    "FULL_CORE_CAPITAL_GUARD_REASONS",
    FULL_CORE_ATOMIC_CONSUMPTION_KEY,
)

ATOMIC_OBSERVATION_BOUND = "BOUND"
ATOMIC_OBSERVATION_NOT_BOUND_FAIL_CLOSED = "NOT_BOUND_FAIL_CLOSED"
ATOMIC_OBSERVATION_CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
ATOMIC_OBSERVATION_ATOMIC_UNKNOWN = "ATOMIC_UNKNOWN"
ATOMIC_OBSERVATION_LOAD_ERROR = "LOAD_ERROR"
ATOMIC_OBSERVATION_CYCLE_IDENTITY_INCOMPLETE = "CYCLE_IDENTITY_INCOMPLETE"

ATOMIC_SCOPE_IDENTITY_NOT_PRESENT = "NOT_PRESENT"
ATOMIC_SCOPE_IDENTITY_PRESENT = "PRESENT"

CYCLE_IDENTITY_NOT_APPLICABLE = "NOT_APPLICABLE"
CYCLE_IDENTITY_INCOMPLETE = "IDENTITY_INCOMPLETE"
CYCLE_IDENTITY_BOUND = "CYCLE_BOUND"
CYCLE_IDENTITY_CONFLICT = "CYCLE_IDENTITY_CONFLICT"

RECOVERY_LEDGER_IDENTITY_MATCH = "MATCH"
RECOVERY_LEDGER_IDENTITY_MISMATCH = "MISMATCH"
RECOVERY_LEDGER_IDENTITY_NOT_APPLICABLE = "NOT_APPLICABLE"


def _ledger_string_claims_v1(ledger: Mapping[str, object]) -> dict[str, str]:
    return {str(key): str(value) for key, value in ledger.items() if isinstance(value, str)}


def _resolve_recovery_atomic_state_dir_v1() -> Path:
    from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
        default_full_core_atomic_state_dir_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_pre_post_capital_guard_join_v1 import (
        ATOMIC_STATE_DIR_ENV_VAR,
    )

    raw = str(os.environ.get(ATOMIC_STATE_DIR_ENV_VAR) or "").strip()
    if raw:
        return Path(raw)
    return default_full_core_atomic_state_dir_v1()


@dataclass(frozen=True)
class FullCoreS5RecoveryObservationV1:
    contract_id: str
    ledger_state: str
    ledger_binding_digest: str
    authorization_binding_digest: str
    ledger_identity_status: str
    post_submit_reconciliation_classification: str
    atomic_observation: str
    atomic_durable_state: str
    recovery_evidence_status: str
    atomic_scope_identity: str
    cycle_identity_status: str

    def to_extra_fields_v1(self) -> dict[str, str]:
        return {
            "FULL_CORE_S5_RECOVERY_OBSERVATION_V1": "V1",
            "FULL_CORE_S5_RECOVERY_LEDGER_STATE": self.ledger_state,
            "FULL_CORE_S5_RECOVERY_LEDGER_BINDING_DIGEST": self.ledger_binding_digest,
            "FULL_CORE_S5_RECOVERY_AUTHORIZATION_BINDING_DIGEST": self.authorization_binding_digest,
            "FULL_CORE_S5_RECOVERY_LEDGER_IDENTITY_STATUS": self.ledger_identity_status,
            "FULL_CORE_S5_RECOVERY_POST_SUBMIT_RECON_CLASS": (
                self.post_submit_reconciliation_classification
            ),
            "ATOMIC_OBSERVATION": self.atomic_observation,
            "FULL_CORE_S5_RECOVERY_ATOMIC_DURABLE_STATE": self.atomic_durable_state,
            "FULL_CORE_S5_RECOVERY_EVIDENCE_STATUS": self.recovery_evidence_status,
            "FULL_CORE_S5_RECOVERY_ATOMIC_SCOPE_IDENTITY": self.atomic_scope_identity,
            "FULL_CORE_S5_RECOVERY_CYCLE_IDENTITY_STATUS": self.cycle_identity_status,
        }


def observe_full_core_s5_recovery_entry_v1(
    *,
    ledger: Mapping[str, object],
    authorization_binding_digest: str,
    atomic_state_dir: Path | None = None,
) -> FullCoreS5RecoveryObservationV1:
    """Read-only S5 restart recovery observation — non-authoritative, no mutation."""

    ledger_state = str(ledger.get("state") or "")
    ledger_binding_digest = str(ledger.get("binding_digest") or "")
    auth_digest = str(authorization_binding_digest or "")
    string_claims = _ledger_string_claims_v1(ledger)
    recon_class = classify_post_submit_reconciliation_observation_v1(string_claims)

    identity_status = RECOVERY_LEDGER_IDENTITY_NOT_APPLICABLE
    if ledger_binding_digest and auth_digest:
        identity_status = (
            RECOVERY_LEDGER_IDENTITY_MATCH
            if ledger_binding_digest == auth_digest
            else RECOVERY_LEDGER_IDENTITY_MISMATCH
        )
    elif ledger_binding_digest and not auth_digest:
        identity_status = RECOVERY_LEDGER_IDENTITY_MISMATCH

    atomic_observation = ATOMIC_OBSERVATION_NOT_BOUND_FAIL_CLOSED
    atomic_durable_state = ""
    evidence_status = "PASS"
    atomic_scope_identity = ATOMIC_SCOPE_IDENTITY_NOT_PRESENT
    cycle_identity_status = CYCLE_IDENTITY_NOT_APPLICABLE

    consumption_key = str(string_claims.get(FULL_CORE_ATOMIC_CONSUMPTION_KEY) or "").strip()
    guard_digest = str(string_claims.get("FULL_CORE_CAPITAL_GUARD_BINDING_DIGEST") or "").strip()
    if consumption_key:
        atomic_scope_identity = ATOMIC_SCOPE_IDENTITY_PRESENT

    if identity_status == RECOVERY_LEDGER_IDENTITY_MISMATCH and ledger_state == "COMPLETED":
        atomic_observation = ATOMIC_OBSERVATION_CONFLICTING_EVIDENCE
        cycle_identity_status = CYCLE_IDENTITY_CONFLICT
        evidence_status = "FAIL_CLOSED"
    elif not consumption_key:
        atomic_observation = ATOMIC_OBSERVATION_NOT_BOUND_FAIL_CLOSED
        if ledger_state == "COMPLETED":
            evidence_status = "FAIL_CLOSED"
    elif not guard_digest:
        atomic_observation = ATOMIC_OBSERVATION_CYCLE_IDENTITY_INCOMPLETE
        cycle_identity_status = CYCLE_IDENTITY_INCOMPLETE
        evidence_status = "FAIL_CLOSED"
    else:
        state_dir = (
            atomic_state_dir
            if atomic_state_dir is not None
            else _resolve_recovery_atomic_state_dir_v1()
        )
        from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
            full_core_durable_entry_state_for_guard_v1,
            load_full_core_atomic_authorization_state_v1,
        )
        from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_atomic_one_shot_v1 import (
            CanaryAtomicOneShotError,
        )

        try:
            loaded = load_full_core_atomic_authorization_state_v1(
                state_dir=Path(state_dir),
                consumption_key=consumption_key,
            )
            durable = full_core_durable_entry_state_for_guard_v1(
                state_dir=Path(state_dir),
                consumption_key=consumption_key,
            )
        except (OSError, CanaryAtomicOneShotError) as exc:
            atomic_observation = ATOMIC_OBSERVATION_LOAD_ERROR
            atomic_durable_state = str(exc)
            cycle_identity_status = CYCLE_IDENTITY_INCOMPLETE
            evidence_status = "FAIL_CLOSED"
        else:
            if loaded is None and not durable:
                atomic_observation = ATOMIC_OBSERVATION_ATOMIC_UNKNOWN
                cycle_identity_status = CYCLE_IDENTITY_INCOMPLETE
                evidence_status = "FAIL_CLOSED"
            elif loaded is None:
                atomic_observation = ATOMIC_OBSERVATION_ATOMIC_UNKNOWN
                atomic_durable_state = durable
                cycle_identity_status = CYCLE_IDENTITY_INCOMPLETE
                evidence_status = "FAIL_CLOSED"
            else:
                atomic_durable_state = str(loaded.state or durable or "")
                plan_digest = str(loaded.binding.get("plan_digest") or "")
                if plan_digest != guard_digest:
                    atomic_observation = ATOMIC_OBSERVATION_CONFLICTING_EVIDENCE
                    cycle_identity_status = CYCLE_IDENTITY_CONFLICT
                    evidence_status = "FAIL_CLOSED"
                else:
                    atomic_observation = ATOMIC_OBSERVATION_BOUND
                    cycle_identity_status = CYCLE_IDENTITY_BOUND

    if recon_class == "FABRICATED_RECONCILIATION_SUCCESS":
        evidence_status = "FAIL_CLOSED"

    return FullCoreS5RecoveryObservationV1(
        contract_id=RECOVERY_OBSERVATION_CONTRACT_ID,
        ledger_state=ledger_state,
        ledger_binding_digest=ledger_binding_digest,
        authorization_binding_digest=auth_digest,
        ledger_identity_status=identity_status,
        post_submit_reconciliation_classification=recon_class,
        atomic_observation=atomic_observation,
        atomic_durable_state=atomic_durable_state,
        recovery_evidence_status=evidence_status,
        atomic_scope_identity=atomic_scope_identity,
        cycle_identity_status=cycle_identity_status,
    )


def lifecycle_hook_observation_fields_v1(
    hook_fields: Mapping[str, str],
    *,
    invocation_bound: bool,
    wiring_explicitly_disabled: bool,
) -> dict[str, str]:
    """Normalize lifecycle hook outcome for durable ledger supplement (non-authoritative)."""

    if not invocation_bound:
        return {"FULL_CORE_CYCLE_LIFECYCLE_WIRING": LIFECYCLE_OBSERVATION_NOT_INVOKED}
    if wiring_explicitly_disabled:
        return {"FULL_CORE_CYCLE_LIFECYCLE_WIRING": LIFECYCLE_OBSERVATION_DISABLED_IN_CONTEXT}
    if not hook_fields:
        return {"FULL_CORE_CYCLE_LIFECYCLE_WIRING": LIFECYCLE_OBSERVATION_INCOMPLETE}
    return {str(k): str(v) for k, v in hook_fields.items()}


def build_post_completed_hook_ledger_supplement_v1(
    *,
    lifecycle_hook_fields: Mapping[str, str],
    invocation_bound: bool,
    wiring_explicitly_disabled: bool,
    capital_guard_fields: Mapping[str, str],
) -> dict[str, str]:
    lifecycle_obs = lifecycle_hook_observation_fields_v1(
        lifecycle_hook_fields,
        invocation_bound=invocation_bound,
        wiring_explicitly_disabled=wiring_explicitly_disabled,
    )
    supplement: dict[str, str] = {
        POST_COMPLETED_HOOK_EVIDENCE_LEDGER_PHASE: "V1",
        POST_COMPLETED_HOOK_EVIDENCE_STATUS: POST_COMPLETED_HOOK_EVIDENCE_STATUS_RECORDED,
        POST_SUBMIT_RECONCILIATION_SUCCEEDED: POST_SUBMIT_RECONCILIATION_SUCCEEDED_VALUE,
    }
    for key in ALLOWLISTED_CAPITAL_GUARD_CYCLE_CLAIM_KEYS:
        if key in capital_guard_fields:
            supplement[key] = str(capital_guard_fields[key])
    supplement.update(lifecycle_obs)
    return supplement


def merge_supplement_persistence_outcome_v1(
    supplement: Mapping[str, str],
    *,
    persistence_status: str,
    persistence_error: str = "",
) -> dict[str, str]:
    merged = {str(k): str(v) for k, v in supplement.items()}
    merged[CYCLE_LEDGER_SUPPLEMENT_PERSISTENCE] = persistence_status
    if persistence_error:
        merged[CYCLE_LEDGER_SUPPLEMENT_PERSISTENCE_ERROR] = persistence_error
    return merged


def pre_external_completed_ledger_pending_marker_v1() -> dict[str, str]:
    """First COMPLETED write for PRE_EXTERNAL — supplement may not have run yet."""

    return {
        POST_COMPLETED_HOOK_EVIDENCE_STATUS: POST_COMPLETED_HOOK_EVIDENCE_STATUS_PENDING,
        POST_SUBMIT_RECONCILIATION_SUCCEEDED: POST_SUBMIT_RECONCILIATION_UNPROVEN_VALUE,
    }


def classify_post_submit_reconciliation_observation_v1(ledger: Mapping[str, str]) -> str:
    """Fail-closed read model — never infer reconciliation success from COMPLETED alone."""

    if str(ledger.get(POST_SUBMIT_RECONCILIATION_SUCCEEDED) or "").lower() == "true":
        return "FABRICATED_RECONCILIATION_SUCCESS"
    terminal = str(ledger.get("terminal_class") or "")
    if terminal != "PRE_EXTERNAL_EFFECT":
        return RECONCILIATION_OBSERVATION_NOT_APPLICABLE
    if str(ledger.get("FULL_CORE_CYCLE_LIFECYCLE_WIRING") or "") == "FAIL_CLOSED":
        return LIFECYCLE_FAIL_CLOSED_NOT_RECONCILIATION_SUCCESS
    status = str(ledger.get(POST_COMPLETED_HOOK_EVIDENCE_STATUS) or "")
    if status == POST_COMPLETED_HOOK_EVIDENCE_STATUS_PENDING:
        return RECONCILIATION_OBSERVATION_INCOMPLETE
    if POST_COMPLETED_HOOK_EVIDENCE_LEDGER_PHASE not in ledger:
        return RECONCILIATION_OBSERVATION_INCOMPLETE
    if str(ledger.get(POST_SUBMIT_RECONCILIATION_SUCCEEDED) or "") == (
        POST_SUBMIT_RECONCILIATION_SUCCEEDED_VALUE
    ):
        return RECONCILIATION_SUCCESS_NOT_CLAIMED
    return RECONCILIATION_OBSERVATION_INCOMPLETE


def merge_allowlisted_post_completed_hook_claims_v1(
    claims: dict[str, object],
    cycle_extra: Mapping[str, str],
) -> None:
    for join_claim_key in ALLOWLISTED_CAPITAL_GUARD_CYCLE_CLAIM_KEYS:
        if join_claim_key in cycle_extra:
            claims[join_claim_key] = str(cycle_extra[join_claim_key])
    claims.update(extract_allowlisted_lifecycle_claims_v1(cycle_extra))


def extract_allowlisted_lifecycle_claims_v1(cycle_extra: Mapping[str, str]) -> dict[str, str]:
    return {
        str(key): str(cycle_extra[key])
        for key in ALLOWLISTED_LIFECYCLE_CYCLE_CLAIM_KEYS
        if key in cycle_extra
    }


__all__ = [
    "ALLOWLISTED_CAPITAL_GUARD_CYCLE_CLAIM_KEYS",
    "ALLOWLISTED_LIFECYCLE_CYCLE_CLAIM_KEYS",
    "ATOMIC_OBSERVATION_ATOMIC_UNKNOWN",
    "ATOMIC_OBSERVATION_BOUND",
    "ATOMIC_OBSERVATION_CONFLICTING_EVIDENCE",
    "ATOMIC_OBSERVATION_LOAD_ERROR",
    "ATOMIC_OBSERVATION_CYCLE_IDENTITY_INCOMPLETE",
    "ATOMIC_OBSERVATION_NOT_BOUND_FAIL_CLOSED",
    "ATOMIC_SCOPE_IDENTITY_NOT_PRESENT",
    "ATOMIC_SCOPE_IDENTITY_PRESENT",
    "CONTRACT_ID",
    "CYCLE_IDENTITY_BOUND",
    "CYCLE_IDENTITY_CONFLICT",
    "CYCLE_IDENTITY_INCOMPLETE",
    "CYCLE_IDENTITY_NOT_APPLICABLE",
    "FULL_CORE_ATOMIC_CONSUMPTION_KEY",
    "FullCoreS5RecoveryObservationV1",
    "RECOVERY_OBSERVATION_CONTRACT_ID",
    "observe_full_core_s5_recovery_entry_v1",
    "CYCLE_LEDGER_SUPPLEMENT_PERSISTENCE",
    "CYCLE_LEDGER_SUPPLEMENT_PERSISTENCE_ERROR",
    "CYCLE_LEDGER_SUPPLEMENT_PERSISTENCE_FAIL_CLOSED",
    "CYCLE_LEDGER_SUPPLEMENT_PERSISTENCE_PASS",
    "LIFECYCLE_OBSERVATION_DISABLED_IN_CONTEXT",
    "LIFECYCLE_OBSERVATION_INCOMPLETE",
    "LIFECYCLE_OBSERVATION_NOT_INVOKED",
    "POST_COMPLETED_HOOK_EVIDENCE_LEDGER_PHASE",
    "POST_SUBMIT_RECONCILIATION_SUCCEEDED",
    "POST_SUBMIT_RECONCILIATION_SUCCEEDED_VALUE",
    "LIFECYCLE_FAIL_CLOSED_NOT_RECONCILIATION_SUCCESS",
    "POST_COMPLETED_HOOK_EVIDENCE_STATUS",
    "POST_COMPLETED_HOOK_EVIDENCE_STATUS_PENDING",
    "POST_COMPLETED_HOOK_EVIDENCE_STATUS_RECORDED",
    "POST_SUBMIT_RECONCILIATION_UNPROVEN_VALUE",
    "RECONCILIATION_OBSERVATION_INCOMPLETE",
    "RECONCILIATION_OBSERVATION_NOT_APPLICABLE",
    "RECONCILIATION_SUCCESS_NOT_CLAIMED",
    "build_post_completed_hook_ledger_supplement_v1",
    "classify_post_submit_reconciliation_observation_v1",
    "extract_allowlisted_lifecycle_claims_v1",
    "lifecycle_hook_observation_fields_v1",
    "merge_allowlisted_post_completed_hook_claims_v1",
    "merge_supplement_persistence_outcome_v1",
    "pre_external_completed_ledger_pending_marker_v1",
    "RECOVERY_LEDGER_IDENTITY_MATCH",
    "RECOVERY_LEDGER_IDENTITY_MISMATCH",
    "RECOVERY_LEDGER_IDENTITY_NOT_APPLICABLE",
]
