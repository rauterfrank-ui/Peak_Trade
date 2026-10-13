"""Post-COMPLETED hook evidence — durable cycle-ledger supplement (observational only).

Cycle Host COMPLETED means PRE_EXTERNAL_EFFECT or valid HOLD terminal — not post-submit
reconciliation success. Atomic One-Shot remains authoritative for submission attempts.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from collections.abc import Mapping

CONTRACT_ID = "FULL_CORE_POST_COMPLETED_HOOK_EVIDENCE_V1"
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

ALLOWLISTED_CAPITAL_GUARD_CYCLE_CLAIM_KEYS: tuple[str, ...] = (
    "FULL_CORE_CAPITAL_GUARD_JOIN_MODE",
    "FULL_CORE_CAPITAL_GUARD_BLOCKED",
    "FULL_CORE_CAPITAL_GUARD_POST_COUNT",
    "FULL_CORE_CAPITAL_GUARD_BINDING_DIGEST",
    "FULL_CORE_CAPITAL_GUARD_REASONS",
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
    "CONTRACT_ID",
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
]
